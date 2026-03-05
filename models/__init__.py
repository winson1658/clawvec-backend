"""
SQLAlchemy 模型包

在此集中導入所有模型，確保 Alembic 可以偵測所有表。
database.py 中的 `from . import models` 會觸發此 __init__.py，
從而完成所有模型的注冊。
"""

from models.base import TimestampMixin, SoftDeleteMixin
from models.user import User
from models.philosophy import PhilosophyDeclaration, PhilosophyTag

__all__ = [
    "TimestampMixin",
    "SoftDeleteMixin",
    "User",
    "PhilosophyDeclaration",
    "PhilosophyTag",
]
