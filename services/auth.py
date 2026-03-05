"""
身份驗證服務

職責：
- 密碼雜湊與驗證
- JWT 生成與驗證
- 注冊 / 登入 / 刷新 token 流程

路由層不做任何業務判斷，只調用此服務。
"""

from datetime import datetime, timedelta
from typing import Tuple

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from config import settings
from exceptions import (
    InvalidCredentialsError,
    InvalidTokenError,
    UserAlreadyExistsError,
)
from models.user import User
from schemas.auth import RegisterRequest, TokenResponse

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def _verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


def _create_token(subject: str, expires_delta: timedelta, token_type: str = "access") -> str:
    expire = datetime.utcnow() + expires_delta
    payload = {
        "sub": subject,
        "exp": expire,
        "type": token_type,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


class AuthService:
    """身份驗證業務邏輯"""

    @staticmethod
    def register(db: Session, data: RegisterRequest) -> User:
        if db.query(User).filter(User.email == data.email).first():
            raise UserAlreadyExistsError()

        user = User(
            email=data.email,
            hashed_password=_hash_password(data.password),
            display_name=data.display_name,
        )
        db.add(user)
        db.flush()  # 取得 id，但不提交（由 get_db 統一 commit）
        return user

    @staticmethod
    def login(db: Session, email: str, password: str) -> TokenResponse:
        user = db.query(User).filter(User.email == email, User.is_active == True).first()  # noqa: E712
        if not user or not _verify_password(password, user.hashed_password):
            raise InvalidCredentialsError()

        return AuthService._issue_tokens(user)

    @staticmethod
    def refresh(db: Session, refresh_token: str) -> TokenResponse:
        try:
            payload = jwt.decode(
                refresh_token,
                settings.secret_key,
                algorithms=[settings.algorithm],
            )
        except JWTError as exc:
            raise InvalidTokenError(detail=str(exc)) from exc

        if payload.get("type") != "refresh":
            raise InvalidTokenError(message="Token 類型錯誤，需要 refresh token")

        user_id = payload.get("sub")
        user = db.query(User).filter(User.id == int(user_id), User.is_active == True).first()  # noqa: E712
        if not user:
            raise InvalidTokenError(message="用戶不存在或已停用")

        return AuthService._issue_tokens(user)

    @staticmethod
    def _issue_tokens(user: User) -> TokenResponse:
        access_expires = timedelta(minutes=settings.access_token_expire_minutes)
        refresh_expires = timedelta(days=settings.jwt_refresh_token_expire_days)

        access_token = _create_token(str(user.id), access_expires, "access")
        refresh_token = _create_token(str(user.id), refresh_expires, "refresh")

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=int(access_expires.total_seconds()),
        )
