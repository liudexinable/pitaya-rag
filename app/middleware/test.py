import os

import fitz
from dotenv import load_dotenv
from minio import Minio
from minio.error import S3Error
from pymilvus import (
    connections,
    FieldSchema, CollectionSchema, DataType,
    Collection, utility
)
from transformers import CLIPModel, CLIPProcessor

from app.middleware.multimodal_engine import MultimodalEngine
from app.middleware.pdf_extract import PDFProcessor

load_dotenv()
# 配置信息
MILVUS_HOST = os.getenv("MILVUS_HOST")
MILVUS_PORT = os.getenv("MILVUS_PORT")
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
MINIO_BUCKET = 'pitaya-uat'

# 1. 初始化Minio客户端
minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False
)


# 2. Milvus集合定义
class MilvusManager:
    def __init__(self, collection_name="multimodal_docs"):
        self.collection_name = collection_name
        connections.connect(host=MILVUS_HOST, port=MILVUS_PORT)

        if not utility.has_collection(collection_name):
            self._create_collection()

        self.collection = Collection(collection_name)

    def _create_collection(self):
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=512),
            FieldSchema(name="content_type", dtype=DataType.VARCHAR, max_length=20),
            FieldSchema(name="text_content", dtype=DataType.VARCHAR, max_length=4000),
            FieldSchema(name="image_path", dtype=DataType.VARCHAR, max_length=512),
            FieldSchema(name="page", dtype=DataType.INT64),
            FieldSchema(name="related_images", dtype=DataType.JSON),
            FieldSchema(name="related_text", dtype=DataType.JSON)
        ]
        schema = CollectionSchema(fields, description="Multimodal document collection")
        self.collection = Collection(self.collection_name, schema)

        # 创建索引
        index_params = {
            "index_type": "IVF_FLAT",
            "metric_type": "L2",
            "params": {"nlist": 1024}
        }
        self.collection.create_index("embedding", index_params)
        return self.collection


# 3. 改进的PDF处理模块
class PDFProcessor1:
    def __init__(self):
        self.milvus = MilvusManager()

    def upload_to_minio(self, file_path, object_name):
        try:
            minio_client.fput_object(
                MINIO_BUCKET,
                object_name,
                file_path
            )
            return f"s3://{MINIO_BUCKET}/{object_name}"
        except S3Error as e:
            print(f"Minio Error: {e}")
            return None

    def extract_elements(self, pdf_path):
        """提取并处理PDF元素"""
        doc = fitz.open(pdf_path)
        elements = []

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)

            # 处理文本块
            text_blocks = page.get_text("blocks")
            for block in text_blocks:
                x0, y0, x1, y1, text, _, _ = block
                if text.strip():
                    elements.append({
                        "type": "text",
                        "content": text,
                        "page": page_num,
                        "position": (x0, y0, x1, y1)
                    })

            # 处理图片
            image_list = page.get_images(full=True)
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]

                # 暂存图片并上传
                temp_path = f"/tmp/page{page_num}_img{img_index}.{image_ext}"
                with open(temp_path, "wb") as f:
                    f.write(image_bytes)

                s3_path = self.upload_to_minio(temp_path,
                                               f"pages/{os.path.basename(temp_path)}")
                os.remove(temp_path)

                elements.append({
                    "type": "image",
                    "s3_path": s3_path,
                    "page": page_num,
                    "position": page.get_image_rects(xref)[0]
                })

        return elements

    def group_elements(self, elements, vertical_threshold=20):
        """根据垂直位置进行元素分组"""
        sorted_elements = sorted(elements, key=lambda x: (x['page'], x['position'][1]))
        groups = []
        current_group = []
        prev_bottom = None

        for elem in sorted_elements:
            page = elem['page']
            y0 = elem['position'][1]
            y1 = elem['position'][3]

            if current_group and (
                    page != current_group[-1]['page'] or
                    (y0 - prev_bottom) > vertical_threshold
            ):
                groups.append(current_group)
                current_group = []

            current_group.append(elem)
            prev_bottom = y1

        if current_group:
            groups.append(current_group)
        return groups


# 4. 多模态处理模块
class MultimodalEngine1:
    def __init__(self):
        self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        self.milvus = MilvusManager()

    def encode(self, content, is_image=False):
        if is_image:
            image = Image.open(content)
            inputs = self.processor(images=image, return_tensors="pt")
            features = self.model.get_image_features(**inputs)
        else:
            inputs = self.processor(text=content, return_tensors="pt",
                                    padding=True, truncation=True, max_length=77)
            features = self.model.get_text_features(**inputs)
        return features.detach().numpy().squeeze()

    def store_in_milvus(self, items):
        """批量存储到Milvus"""
        embeddings = []
        entities = []

        for item in items:
            if item["type"] == "text":
                embedding = self.encode(item["content"])
                entities.append({
                    "content_type": "text",
                    "text_content": item["content"],
                    "page": item["page"],
                    "related_images": item.get("related_images", []),
                    "related_text": []
                })
            else:
                embedding = self.encode(item["s3_path"], is_image=True)
                entities.append({
                    "content_type": "image",
                    "image_path": item["s3_path"],
                    "page": item["page"],
                    "related_text": item.get("related_text", []),
                    "related_images": []
                })

            embeddings.append(embedding)

        # 转换为Milvus的插入格式
        insert_data = [
            embeddings,
            [e["content_type"] for e in entities],
            [e["text_content"] for e in entities],
            [e["image_path"] for e in entities],
            [e["page"] for e in entities],
            [e["related_images"] for e in entities],
            [e["related_text"] for e in entities]
        ]

        # 批量插入
        self.milvus.collection.insert(insert_data)
        self.milvus.collection.flush()


# 5. 混合搜索实现
class HybridSearcher:
    def __init__(self):
        self.milvus = MilvusManager()
        self.multimodal = MultimodalEngine()

    def search(self, query, top_k=5):
        # 判断查询类型
        if query.startswith("s3://"):
            query_vec = self.multimodal.encode(query, is_image=True)
        else:
            query_vec = self.multimodal.encode(query)

        # Milvus搜索参数
        search_params = {
            "metric_type": "L2",
            "params": {"nprobe": 10}
        }

        results = self.milvus.collection.search(
            data=[query_vec],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            output_fields=["content_type", "text_content", "image_path", "page"]
        )

        # 处理搜索结果
        formatted_results = []
        for hits in results:
            for hit in hits:
                result = {
                    "score": hit.score,
                    "type": hit.entity.get("content_type"),
                    "text": hit.entity.get("text_content"),
                    "image": hit.entity.get("image_path"),
                    "page": hit.entity.get("page")
                }
                formatted_results.append(result)

        return sorted(formatted_results, key=lambda x: x["score"])


# 使用示例
if __name__ == "__main__":
    # 处理PDF并存储
    processor = PDFProcessor()
    elements = processor.extract_elements("《2024年中国AI大模型产业发展报告》.pdf")
    groups = processor.group_elements(elements)

    # 多模态处理
    engine = MultimodalEngine()
    engine.store_in_milvus(groups)

    # 执行搜索
    searcher = HybridSearcher()
    print("文本搜索:")
    print(searcher.search("千亿级参数大模型通义千问 2.0"))

    print("\n图片搜索:")
    print(searcher.search("http://192.168.9.180:9001/pitaya-uat/pages/page37_img0.jpeg"))
