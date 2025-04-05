import logging
from typing import Optional

from fastapi import APIRouter, Request, UploadFile, File, Form

from app.util.api_response import ApiResponse

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
                pass
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
