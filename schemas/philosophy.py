"""理念相關 Schema"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class PhilosophyTagOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    model_config = {"from_attributes": True}


class PhilosophyCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=10)
    tag_ids: List[int] = Field(default_factory=list)


class PhilosophyUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    content: Optional[str] = Field(default=None, min_length=10)
    tag_ids: Optional[List[int]] = None


class PhilosophyOut(BaseModel):
    id: int
    user_id: int
    title: str
    content: str
    consistency_score: Optional[float] = None
    tags: List[PhilosophyTagOut] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
