"""理念聲明路由"""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from database import get_db
from dependencies import PaginationParams, get_current_user, get_optional_user, paginate
from schemas.base import BaseResponse, MessageResponse, PaginatedResponse
from schemas.philosophy import PhilosophyCreate, PhilosophyOut, PhilosophyUpdate
from services.philosophy import PhilosophyService

router = APIRouter()


@router.get(
    "/",
    response_model=PaginatedResponse[PhilosophyOut],
    summary="列出理念聲明（公開）",
)
def list_philosophy(
    user_id: int | None = Query(default=None, description="過濾特定用戶的聲明"),
    page: PaginationParams = Depends(paginate),
    db: Session = Depends(get_db),
):
    items, total = PhilosophyService.list(
        db, user_id=user_id, offset=page.offset, limit=page.limit
    )
    return PaginatedResponse.create(
        [PhilosophyOut.model_validate(i) for i in items],
        total=total,
        page=page.page,
        page_size=page.page_size,
    )


@router.post(
    "/",
    response_model=BaseResponse[PhilosophyOut],
    status_code=status.HTTP_201_CREATED,
    summary="創建理念聲明",
)
def create_philosophy(
    data: PhilosophyCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = PhilosophyService.create(db, current_user.id, data)
    return BaseResponse(data=PhilosophyOut.model_validate(item), message="理念聲明已創建")


@router.get("/{declaration_id}", response_model=BaseResponse[PhilosophyOut], summary="取得單一理念聲明")
def get_philosophy(declaration_id: int, db: Session = Depends(get_db)):
    item = PhilosophyService.get(db, declaration_id)
    return BaseResponse(data=PhilosophyOut.model_validate(item))


@router.patch("/{declaration_id}", response_model=BaseResponse[PhilosophyOut], summary="更新理念聲明")
def update_philosophy(
    declaration_id: int,
    data: PhilosophyUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = PhilosophyService.update(db, declaration_id, current_user.id, data)
    return BaseResponse(data=PhilosophyOut.model_validate(item), message="理念聲明已更新")


@router.delete("/{declaration_id}", response_model=MessageResponse, summary="刪除理念聲明（軟刪除）")
def delete_philosophy(
    declaration_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    PhilosophyService.delete(db, declaration_id, current_user.id)
    return MessageResponse(message="理念聲明已刪除")
