import logging
import os
import tempfile
from typing import Optional

from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException
from langchain import text_splitter
from langchain_community.document_loaders import PyPDFLoader

from app.util.api_response import ApiResponse
from app.util.file_handle import extract_images_from_pdf, ocr_image
from app.util.minio_util import get_minio_client, upload_to_minio

router = APIRouter(
    prefix="/knowledge_api",
    tags=["knowledge_api"]
)


@router.post('/update')
async def update(
    request: Request,
    files: list[UploadFile] = File(..., description="上传的知识文件"),
    application_model: str = Form(default="default", description="系统模块"),
    category: str = Form(default="default", description="知识分类"),
    priority: int = Form(default=1,ge=1, le=5, description="处理优先级"),
    description: Optional[str] = Form(None),
):
    logging.info("update-----")
    """
    知识库更新接口，支持：
    - 多文件上传
    - 分类参数
    - 优先级参数
    - 可选描述
    """

    print(application_model, category, priority, description)

    # 处理上传文件
    file_info = []
    for file in files:
        print(file.filename)
        # 获取文件扩展名
        file_ext = file.filename.split('.')[-1].lower()
        # 使用match-case处理不同类型
        match file_ext:
            case "pdf":
                await pdf_spilt(file)
            case "doc" | "docx":
                pass
            case "txt":
                pass
            case "csv":
                pass
            case _:
                pass


    return ApiResponse.success_response(
        data=None,
        cache=True
    ).build()

async def pdf_spilt(file :UploadFile):
    try:
        # 创建临时文件保存上传内容
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            content = await file.read()  # 异步读取文件内容
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        print(tmp_file_path)
        # 使用 PDF 加载器
        # 1. 处理文本内容
        loader = PyPDFLoader(tmp_file_path)
        pages = loader.load_and_split()

        # 2. 处理图片内容
        images = extract_images_from_pdf(tmp_file_path)
        image_texts = [ocr_image(img) for img in images]

        # 2. 处理图片内容
        images = extract_images_from_pdf(tmp_file_path)
        image_texts = []
        image_refs = []  # 存储图片引用

        for i, img in enumerate(images):
            # OCR识别图片文字
            text = ocr_image(img)
            image_texts.append(text)

            # 保存图片到存储系统并获取引用
            # 图片上传minio
            url = upload_to_minio(bucket_name="pitaya",
                              object_name=f"pdf/{file.filename}-{i}.jpg",
                              file_path=img)

            image_refs.append({
                "path": url,
                "text": text,
                "page": i + 1
            })

        # 3. 合并文本和图片OCR结果
        all_texts = [page.page_content for page in pages] + image_texts
        documents = text_splitter.create_documents(all_texts)

        # 4. 添加元数据
        for doc in documents:
            doc.metadata.update({
                "source": file.filename,
                "type": "pdf"
            })

        logging.info(f"PDF 分页数: {documents}")
        logging.info("PDF 分页处理完成")
    except Exception as e:
        logging.info(f"PDF 处理失败: {e}")
        # 清理可能残留的临时文件
        if 'tmp_file_path' in locals() and os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)
        raise HTTPException(
            status_code=500,
            detail=f"PDF 处理失败: {str(e)}"
        )
    finally:
        if os.path.exists(tmp_file_path):
            logging.info("PDF 处理完成，清理临时文件")
            os.unlink(tmp_file_path)
