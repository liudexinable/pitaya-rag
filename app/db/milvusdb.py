import os
from dotenv import load_dotenv
from pymilvus import  (
    connections,
    FieldSchema, CollectionSchema, DataType,
    Collection, utility
)

load_dotenv()

class MilvusManager:
    def __init__(self):
        # 初始化连接
        host = os.getenv("MILVUS_HOST")
        port = os.getenv("MILVUS_PORT")
        self.collection_name = os.getenv("MILVUS_COLLECTION_NAME")

        connections.connect(host=host, port=port)

        if not utility.has_collection(self.collection_name):
            self._create_collection()

        self.collection = Collection(self.collection_name)

    def _create_collection(self):
        # 创建集合 定义字段
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="sys_model", dtype=DataType.VARCHAR, max_length=30),
            FieldSchema(name="status", dtype=DataType.VARCHAR, max_length=30),
            FieldSchema(name="file_name", dtype=DataType.VARCHAR, max_length=200),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=2048),
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