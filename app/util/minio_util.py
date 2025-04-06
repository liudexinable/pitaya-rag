from minio import Minio
import os
from dotenv import load_dotenv

load_dotenv()

def get_minio_client():
    """初始化 MinIO 客户端"""
    MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
    MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
    MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
    return Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False
    )


def upload_to_minio(file_path,object_name: str) -> str:
    """
    上传文件到 MinIO
    :param bucket_name: 存储桶名称
    :param object_name: 对象存储路径
    :param file_path: 本地文件路径
    """
    client = get_minio_client()
    bucket_name = os.getenv("MINIO_BUCKET")
    try:
        # 上传文件
        client.fput_object(
            bucket_name=bucket_name,
            object_name=object_name,
            file_path=file_path,
            content_type="image/jpeg"
        )
        print(f"文件 {file_path} 成功上传至 {bucket_name}/{object_name}")
        return f"http://td2.cat-kk.com.cn:9001/{bucket_name}/{object_name}"
       # return bucket_name + "/" + object_name
    except Exception as e:
        print(f"上传失败: {str(e)}")
