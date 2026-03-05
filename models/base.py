"""
SQLAlchemy 基礎 Mixin

所有模型繼承 TimestampMixin 可獲得 created_at / updated_at。
繼承 SoftDeleteMixin 可獲得軟刪除功能。

設計原則：
- 用 Mixin 而非繼承鏈，讓模型職責清晰
- created_at / updated_at 由資料庫自動維護
"""

from datetime import datetime
from sqlalchemy import Column, DateTime, Boolean
from sqlalchemy.sql import func


class TimestampMixin:
    """自動維護創建/更新時間戳"""

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SoftDeleteMixin:
    """
    軟刪除支援

    查詢時需手動過濾: .filter(Model.deleted_at.is_(None))
    或使用 services 層提供的工具函數。
    """

    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)

    def soft_delete(self) -> None:
        self.deleted_at = datetime.utcnow()
        self.is_deleted = True

    @property
    def is_active_record(self) -> bool:
        return not self.is_deleted
