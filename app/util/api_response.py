from datetime import datetime
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any, Union
from pydantic import BaseModel


class ApiResponse:
    """标准化API响应处理器（线程安全版本）"""

    def __init__(
            self,
            success: bool = True,
            code: int = 200,
            message: str = "Success",
            data: Optional[Union[Dict, BaseModel]] = None,
            meta: Optional[Dict] = None,
            errors: Optional[list] = None
    ):
        self.success = success
        self.code = code
        self.message = message
        self.data = data.dict() if isinstance(data, BaseModel) else (data or {})
        self.meta = meta or {}
        self.errors = errors or []

    @classmethod
    def success_response(
            cls,
            data: Optional[Union[Dict, BaseModel]] = None,
            message: str = "Success",
            code: int = 200,
            **meta
    ) -> 'ApiResponse':
        """创建成功响应（推荐入口方法）"""
        return cls(
            success=True,
            code=code,
            message=message,
            data=data,
            meta=meta
        )

    @classmethod
    def error_response(
            cls,
            message: str = "Error",
            code: int = 400,
            errors: Optional[list] = None,
            **meta
    ) -> 'ApiResponse':
        """创建错误响应（推荐入口方法）"""
        return cls(
            success=False,
            code=code,
            message=message,
            errors=errors or [],
            meta=meta
        )

    def to_dict(self) -> dict:
        """生成标准化响应字典"""
        return {
            "success": self.success,
            "code": self.code,
            "message": self.message,
            "data": self.data,
            "errors": self.errors,
            "meta": self.meta,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    def build(
            self,
            status_code: Optional[int] = None,
            headers: Optional[Dict] = None
    ) -> JSONResponse:
        """构建FastAPI响应对象"""
        return JSONResponse(
            content=self.to_dict(),
            status_code=status_code or self.code,
            headers=headers or {}
        )
