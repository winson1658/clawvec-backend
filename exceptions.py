"""
自定義例外層次結構與全局處理器

設計原則:
- 所有業務例外繼承自 ClawvecException
- 每個例外攜帶 HTTP 狀態碼、錯誤代碼、訊息
- 全局 handler 統一輸出格式: {error_code, message, detail, path}
"""

from typing import Any, Optional
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 基礎例外
# ---------------------------------------------------------------------------

class ClawvecException(Exception):
    """所有業務例外的基類"""

    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"
    message: str = "內部伺服器錯誤"

    def __init__(
        self,
        message: Optional[str] = None,
        detail: Optional[Any] = None,
        error_code: Optional[str] = None,
    ):
        self.message = message or self.__class__.message
        self.detail = detail
        self.error_code = error_code or self.__class__.error_code
        super().__init__(self.message)

    def to_dict(self, path: str = "") -> dict:
        payload: dict = {
            "error_code": self.error_code,
            "message": self.message,
        }
        if self.detail is not None:
            payload["detail"] = self.detail
        if path:
            payload["path"] = path
        return payload


# ---------------------------------------------------------------------------
# 4xx 例外
# ---------------------------------------------------------------------------

class BadRequestError(ClawvecException):
    status_code = 400
    error_code = "BAD_REQUEST"
    message = "請求格式錯誤"


class AuthenticationError(ClawvecException):
    status_code = 401
    error_code = "AUTHENTICATION_FAILED"
    message = "身份驗證失敗"


class InvalidTokenError(AuthenticationError):
    error_code = "INVALID_TOKEN"
    message = "無效或已過期的 Token"


class PermissionDeniedError(ClawvecException):
    status_code = 403
    error_code = "PERMISSION_DENIED"
    message = "沒有執行此操作的權限"


class NotFoundError(ClawvecException):
    status_code = 404
    error_code = "NOT_FOUND"
    message = "資源不存在"


class ConflictError(ClawvecException):
    status_code = 409
    error_code = "CONFLICT"
    message = "資源衝突"


class ValidationError(ClawvecException):
    status_code = 422
    error_code = "VALIDATION_ERROR"
    message = "資料驗證失敗"


class RateLimitError(ClawvecException):
    status_code = 429
    error_code = "RATE_LIMIT_EXCEEDED"
    message = "請求過於頻繁，請稍後再試"


# ---------------------------------------------------------------------------
# 業務域例外
# ---------------------------------------------------------------------------

class UserAlreadyExistsError(ConflictError):
    error_code = "USER_ALREADY_EXISTS"
    message = "該電子郵件已被註冊"


class UserNotFoundError(NotFoundError):
    error_code = "USER_NOT_FOUND"
    message = "用戶不存在"


class InvalidCredentialsError(AuthenticationError):
    error_code = "INVALID_CREDENTIALS"
    message = "電子郵件或密碼不正確"


class PhilosophyNotFoundError(NotFoundError):
    error_code = "PHILOSOPHY_NOT_FOUND"
    message = "理念不存在"


class PhilosophyConsistencyError(ClawvecException):
    status_code = 400
    error_code = "PHILOSOPHY_INCONSISTENCY"
    message = "請求行為與智能體聲明理念不一致"


# ---------------------------------------------------------------------------
# 全局例外處理器（在 main.py 中注冊）
# ---------------------------------------------------------------------------

def _error_response(status_code: int, payload: dict) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=payload)


async def clawvec_exception_handler(request: Request, exc: ClawvecException) -> JSONResponse:
    logger.warning(
        "業務例外 | %s | %s | path=%s",
        exc.error_code,
        exc.message,
        request.url.path,
    )
    return _error_response(exc.status_code, exc.to_dict(path=request.url.path))


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return _error_response(
        exc.status_code,
        {
            "error_code": f"HTTP_{exc.status_code}",
            "message": str(exc.detail),
            "path": request.url.path,
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = [
        {"field": ".".join(str(loc) for loc in e["loc"]), "message": e["msg"]}
        for e in exc.errors()
    ]
    return _error_response(
        422,
        {
            "error_code": "VALIDATION_ERROR",
            "message": "請求資料驗證失敗",
            "detail": errors,
            "path": request.url.path,
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("未處理的例外 | path=%s | %s", request.url.path, exc, exc_info=True)
    return _error_response(
        500,
        {
            "error_code": "INTERNAL_ERROR",
            "message": "內部伺服器錯誤，請聯繫管理員",
            "path": request.url.path,
        },
    )


def register_exception_handlers(app) -> None:
    """在 FastAPI app 上注冊所有全局例外處理器"""
    from fastapi.exceptions import RequestValidationError

    app.add_exception_handler(ClawvecException, clawvec_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)


__all__ = [
    # 基礎
    "ClawvecException",
    # 4xx
    "BadRequestError",
    "AuthenticationError",
    "InvalidTokenError",
    "PermissionDeniedError",
    "NotFoundError",
    "ConflictError",
    "ValidationError",
    "RateLimitError",
    # 業務域
    "UserAlreadyExistsError",
    "UserNotFoundError",
    "InvalidCredentialsError",
    "PhilosophyNotFoundError",
    "PhilosophyConsistencyError",
    # 注冊函數
    "register_exception_handlers",
]
