"""Pydantic schemas for content and generated_posts."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ContentBase(BaseModel):
    original_text: str = Field(..., min_length=10, max_length=10_000)
    title: Optional[str] = Field(None, max_length=255)
    source_url: Optional[str] = Field(None, max_length=500)


class ContentCreate(ContentBase):
    pass


class ContentResponse(ContentBase):
    id: int
    word_count: int
    created_at: datetime

    model_config = {"from_attributes": True}
