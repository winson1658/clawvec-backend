"""用戶路由"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user
from schemas.base import BaseResponse, MessageResponse
from schemas.user import UserOut, UserUpdate
from services.user import UserService

router = APIRouter()


@router.get("/me", response_model=BaseResponse[UserOut], summary="取得當前用戶資料")
def get_me(current_user=Depends(get_current_user)):
    return BaseResponse(data=UserOut.model_validate(current_user))


@router.patch("/me", response_model=BaseResponse[UserOut], summary="更新當前用戶資料")
def update_me(
    data: UserUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = UserService.update(db, current_user, data)
    return BaseResponse(data=UserOut.model_validate(user), message="資料更新成功")


@router.delete(
    "/me",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="停用當前用戶帳號",
)
def delete_me(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    UserService.deactivate(db, current_user)
    return MessageResponse(message="帳號已停用")


@router.get("/{user_id}", response_model=BaseResponse[UserOut], summary="取得公開用戶資料")
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = UserService.get_by_id(db, user_id)
    return BaseResponse(data=UserOut.model_validate(user))
