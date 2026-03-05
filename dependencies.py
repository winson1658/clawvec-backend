"""
共享 FastAPI 依賴函數

所有路由共用的依賴集中於此，避免分散重複。
使用方式：
    from dependencies import get_current_user, paginate

    @router.get("/items")
    async def list_items(
        page: PaginationParams = Depends(paginate),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ): ...
"""

from typing import Optional
from dataclasses import dataclass

from fastapi import Depends, Header, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from database import get_db
from config import settings
from exceptions import InvalidTokenError, PermissionDeniedError

# JWT 工具（避免循環導入，延遲導入 services）
from jose import JWTError, jwt

security = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# 分頁參數
# ---------------------------------------------------------------------------

@dataclass
class PaginationParams:
    page: int
    page_size: int

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


def paginate(
    page: int = Query(default=1, ge=1, description="頁碼（從 1 開始）"),
    page_size: int = Query(default=20, ge=1, le=100, description="每頁筆數（最大 100）"),
) -> PaginationParams:
    return PaginationParams(page=page, page_size=page_size)


# ---------------------------------------------------------------------------
# JWT / 身份驗證
# ---------------------------------------------------------------------------

def _decode_token(token: str) -> dict:
    """解碼並驗證 JWT，統一拋出 InvalidTokenError"""
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        return payload
    except JWTError as exc:
        raise InvalidTokenError(detail=str(exc)) from exc


def get_token_payload(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    """從 Authorization header 取得並驗證 token payload"""
    if not credentials:
        raise InvalidTokenError(message="缺少 Authorization 頭部")
    return _decode_token(credentials.credentials)


def get_current_user_id(payload: dict = Depends(get_token_payload)) -> int:
    """從 token payload 取得 user_id"""
    user_id = payload.get("sub")
    if user_id is None:
        raise InvalidTokenError(message="Token 中缺少 sub 字段")
    try:
        return int(user_id)
    except (ValueError, TypeError) as exc:
        raise InvalidTokenError(message="Token sub 字段格式無效") from exc


def get_current_user(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """取得當前登入用戶的 ORM 對象（惰性導入避免循環）"""
    from models.user import User

    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()  # noqa: E712
    if user is None:
        from exceptions import UserNotFoundError
        raise UserNotFoundError()
    return user


def require_admin(current_user=Depends(get_current_user)):
    """僅允許管理員角色"""
    if not getattr(current_user, "is_admin", False):
        raise PermissionDeniedError(message="此操作需要管理員權限")
    return current_user


# ---------------------------------------------------------------------------
# 可選身份驗證（公開端點允許匿名，但已登入時取得用戶）
# ---------------------------------------------------------------------------

def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
):
    """
    可選認證：有 token 時返回用戶，無 token 時返回 None
    適用於部分公開、部分需認證的端點
    """
    if not credentials:
        return None
    try:
        payload = _decode_token(credentials.credentials)
        user_id = int(payload.get("sub", 0))
        from models.user import User
        return db.query(User).filter(User.id == user_id, User.is_active == True).first()  # noqa: E712
    except Exception:
        return None


__all__ = [
    "PaginationParams",
    "paginate",
    "get_token_payload",
    "get_current_user_id",
    "get_current_user",
    "require_admin",
    "get_optional_user",
]
