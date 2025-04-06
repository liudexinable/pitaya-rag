import tempfile

import requests
from pdf2image import convert_from_path
from pytesseract import pytesseract


def extract_images_from_pdf(pdf_path) -> list:
    """从PDF中提取所有图片"""
    images = []
    # 使用pdf2image或其他库提取图片
    # 这里需要安装pdf2image: pip install pdf2image
    pil_images = convert_from_path(pdf_path)
    return pil_images

def ocr_image(image) -> str:
    """使用OCR识别图片中的文字"""
    try:
        return pytesseract.image_to_string(image, lang='chi_sim+eng')
    except Exception:
        return ""

def download_file(url):
   response = requests.get(url)
   if response.status_code == 200:
       # 创建临时文件
       with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
           tmp_file.write(response.content)
           return tmp_file.name
   else:
       raise Exception(f"下载失败: HTTP {response.status_code}")