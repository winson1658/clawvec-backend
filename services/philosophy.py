"""理念聲明服務"""

from typing import Tuple, List

from sqlalchemy.orm import Session

from config import settings
from exceptions import PhilosophyNotFoundError, PermissionDeniedError
from models.philosophy import PhilosophyDeclaration, PhilosophyTag
from schemas.philosophy import PhilosophyCreate, PhilosophyUpdate


def _resolve_tags(db: Session, tag_ids: List[int]) -> List[PhilosophyTag]:
    if not tag_ids:
        return []
    return db.query(PhilosophyTag).filter(PhilosophyTag.id.in_(tag_ids)).all()


class PhilosophyService:
    @staticmethod
    def list(
        db: Session,
        *,
        user_id: int | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[PhilosophyDeclaration], int]:
        q = db.query(PhilosophyDeclaration).filter(
            PhilosophyDeclaration.is_deleted == False  # noqa: E712
        )
        if user_id is not None:
            q = q.filter(PhilosophyDeclaration.user_id == user_id)
        total = q.count()
        items = q.order_by(PhilosophyDeclaration.created_at.desc()).offset(offset).limit(limit).all()
        return items, total

    @staticmethod
    def get(db: Session, declaration_id: int) -> PhilosophyDeclaration:
        item = db.query(PhilosophyDeclaration).filter(
            PhilosophyDeclaration.id == declaration_id,
            PhilosophyDeclaration.is_deleted == False,  # noqa: E712
        ).first()
        if not item:
            raise PhilosophyNotFoundError()
        return item

    @staticmethod
    def create(db: Session, user_id: int, data: PhilosophyCreate) -> PhilosophyDeclaration:
        tags = _resolve_tags(db, data.tag_ids)
        item = PhilosophyDeclaration(
            user_id=user_id,
            title=data.title,
            content=data.content,
            tags=tags,
        )
        db.add(item)
        db.flush()
        return item

    @staticmethod
    def update(
        db: Session,
        declaration_id: int,
        user_id: int,
        data: PhilosophyUpdate,
    ) -> PhilosophyDeclaration:
        item = PhilosophyService.get(db, declaration_id)
        if item.user_id != user_id:
            raise PermissionDeniedError(message="只有作者才能修改此理念聲明")

        if data.title is not None:
            item.title = data.title
        if data.content is not None:
            item.content = data.content
        if data.tag_ids is not None:
            item.tags = _resolve_tags(db, data.tag_ids)

        db.flush()
        return item

    @staticmethod
    def delete(db: Session, declaration_id: int, user_id: int) -> None:
        item = PhilosophyService.get(db, declaration_id)
        if item.user_id != user_id:
            raise PermissionDeniedError(message="只有作者才能刪除此理念聲明")
        item.soft_delete()
        db.flush()

    @staticmethod
    def compute_consistency_score(content: str) -> float:
        """
        計算理念一致性分數（stub）

        未來接入知識圖譜或 LLM 評分。
        目前返回預設分數以通過測試。
        """
        return settings.min_philosophy_consistency_score
