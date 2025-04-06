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
                logging.info("---->>>")
                embeddings.append(embedding)

        # 转换为Milvus的插入格式
        insert_data = [
            [e.get('sys_model', 'default_model') for e in entities],
            [e.get('status', 'active') for e in entities],
            [e.get('file_name', 'active') for e in entities],
            embeddings,
            [e.get("content_type","") for e in entities],
            [e.get("text_content","") for e in entities],
            [e.get("image_path","") for e in entities],
            [e.get("page","") for e in entities],
            [e.get("related_images","") for e in entities],
            [e.get("related_text","") for e in entities]
        ]
        logging.info(f"向量后的数据:{insert_data}")
        print(f"向量后的数据:{insert_data}")
        # 批量插入
        self.milvus.collection.insert(insert_data)
        self.milvus.collection.flush()