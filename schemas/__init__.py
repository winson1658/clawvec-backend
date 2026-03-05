"""Pydantic Schema 包"""

from schemas.base import (
    BaseResponse,
    PaginatedResponse,
    MessageResponse,
    ErrorResponse,
)
from schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    RefreshRequest,
)
from schemas.user import UserOut, UserUpdate
from schemas.philosophy import (
    PhilosophyCreate,
    PhilosophyUpdate,
    PhilosophyOut,
    PhilosophyTagOut,
)

__all__ = [
    "BaseResponse",
    "PaginatedResponse",
    "MessageResponse",
    "ErrorResponse",
    "RegisterRequest",
    "LoginRequest",
    "TokenResponse",
    "RefreshRequest",
    "UserOut",
    "UserUpdate",
    "PhilosophyCreate",
    "PhilosophyUpdate",
    "PhilosophyOut",
    "PhilosophyTagOut",
]
