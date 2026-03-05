"""用戶服務"""

from sqlalchemy.orm import Session

from exceptions import UserNotFoundError
from models.user import User
from schemas.user import UserUpdate


class UserService:
    @staticmethod
    def get_by_id(db: Session, user_id: int) -> User:
        user = db.query(User).filter(User.id == user_id, User.is_active == True).first()  # noqa: E712
        if not user:
            raise UserNotFoundError()
        return user

    @staticmethod
    def update(db: Session, user: User, data: UserUpdate) -> User:
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        db.flush()
        return user

    @staticmethod
    def deactivate(db: Session, user: User) -> None:
        user.is_active = False
        db.flush()
