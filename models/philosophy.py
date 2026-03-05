"""
理念聲明模型
"""

from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, Table
from sqlalchemy.orm import relationship
from database import Base
from models.base import TimestampMixin, SoftDeleteMixin

# 多對多中間表：理念聲明 <-> 標籤
philosophy_tag_association = Table(
    "philosophy_tag_association",
    Base.metadata,
    Column("declaration_id", Integer, ForeignKey("philosophy_declarations.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("philosophy_tags.id"), primary_key=True),
)


class PhilosophyTag(TimestampMixin, Base):
    __tablename__ = "philosophy_tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)

    declarations = relationship(
        "PhilosophyDeclaration",
        secondary=philosophy_tag_association,
        back_populates="tags",
    )

    def __repr__(self) -> str:
        return f"<PhilosophyTag name={self.name!r}>"


class PhilosophyDeclaration(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "philosophy_declarations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    consistency_score = Column(Float, nullable=True)  # 由系統計算

    # 關聯
    user = relationship("User", backref="philosophy_declarations")
    tags = relationship(
        "PhilosophyTag",
        secondary=philosophy_tag_association,
        back_populates="declarations",
    )

    def __repr__(self) -> str:
        return f"<PhilosophyDeclaration id={self.id} user_id={self.user_id}>"
