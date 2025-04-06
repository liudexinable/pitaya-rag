from zhipuai import ZhipuAI
import os
from dotenv import load_dotenv
from typing import List, Union
import base64

from app.util.file_handle import download_file

load_dotenv()
class ZhipuEmbedding:
    def __init__(self):
        api_key = os.getenv("ZHIPU_API_KEY")
        self.client = ZhipuAI(api_key=api_key)

    def embed_text(self, text: str) -> List[float]:
        """生成文本embedding"""
        response = self.client.embeddings.create(
            model="embedding-3",
            input=[text]
        )
        return response.data[0].embedding
    def embed_img(self, image_url: str) -> List[float]:
        """生成图片embedding"""
        image_path = download_file(image_url)
        with open(image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
        response = self.client.embeddings.create(
            model="embedding-3",
            input=[encoded_image]
        )
        return response.data[0].embedding

