"""
基礎 Pydantic Schema

統一 API 響應格式，所有端點使用這些基類，確保格式一致。

成功響應:  {"data": ..., "message": "ok"}
分頁響應:  {"data": [...], "total": n, "page": 1, "page_size": 20, "pages": 5}
錯誤響應:  {"error_code": "...", "message": "...", "detail": [...]}
"""

from typing import Generic, List, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class BaseResponse(BaseModel, Generic[T]):
    """單一資源成功響應"""
    data: T
    message: str = "ok"


class PaginatedResponse(BaseModel, Generic[T]):
    """分頁列表響應"""
    data: List[T]
    total: int
    page: int
    page_size: int
    pages: int

    @classmethod
    def create(cls, items: List[T], total: int, page: int, page_size: int) -> "PaginatedResponse[T]":
        pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return cls(data=items, total=total, page=page, page_size=page_size, pages=pages)


class MessageResponse(BaseModel):
    """純訊息響應（適用於刪除、狀態變更等操作）"""
    message: str


class ErrorResponse(BaseModel):
    """錯誤響應（與 exceptions.py 格式對應）"""
    error_code: str
    message: str
    detail: Optional[object] = None
    path: Optional[str] = None
