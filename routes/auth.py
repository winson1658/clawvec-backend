"""
身份驗證路由

路由層只負責：
1. 解析並驗證請求 (FastAPI/Pydantic 自動完成)
2. 調用 Service
3. 包裝成標準響應格式

所有業務邏輯在 services/auth.py，例外處理在 exceptions.py。
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse
from schemas.base import BaseResponse, MessageResponse
from schemas.user import UserOut
from services.auth import AuthService

router = APIRouter()


@router.post(
    "/register",
    response_model=BaseResponse[UserOut],
    status_code=status.HTTP_201_CREATED,
    summary="注冊新用戶",
)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    user = AuthService.register(db, data)
    return BaseResponse(data=UserOut.model_validate(user), message="注冊成功")


@router.post(
    "/login",
    response_model=BaseResponse[TokenResponse],
    summary="用戶登入",
)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    tokens = AuthService.login(db, data.email, data.password)
    return BaseResponse(data=tokens, message="登入成功")


@router.post(
    "/refresh",
    response_model=BaseResponse[TokenResponse],
    summary="刷新 Access Token",
)
def refresh_token(data: RefreshRequest, db: Session = Depends(get_db)):
    tokens = AuthService.refresh(db, data.refresh_token)
    return BaseResponse(data=tokens, message="Token 刷新成功")
