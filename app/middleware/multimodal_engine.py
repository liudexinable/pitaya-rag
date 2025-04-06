from app.db.milvusdb import MilvusManager
from app.middleware.zhipu_embedding import ZhipuEmbedding
import logging

class MultimodalEngine:
    def __init__(self):
        self.milvus = MilvusManager()
        self.zhipu = ZhipuEmbedding()

    def store_in_milvus(self, items):
        """批量存储到Milvus"""
        embeddings = []
        entities = []

        for item in items:
            for c_item in item:
                if c_item["type"] == "text":
                    embedding = self.zhipu.embed_text(c_item["content"])
                    entities.append({
                        "content_type": "text",
                        "text_content": c_item["content"],
                        "page": c_item["page"],
                        "related_images": c_item.get("related_images", []),
                        "related_text": []
                    })
                else:
                    embedding = self.zhipu.embed_img(c_item["s3_path"])
                    entities.append({
                        "content_type": "image",
                        "image_path": c_item["s3_path"],
                        "page": c_item["page"],
                        "related_text": c_item.get("related_text", []),
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
        logging.info(f"向量后的数据:{insert_data}")
        # 批量插入
        #self.milvus.collection.insert(insert_data)
        #self.milvus.collection.flush()