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


class LinkedInPostOut(BaseModel):
    """A single generated LinkedIn post from long-form content."""

    id: int
    content_id: int
    title: Optional[str]
    body: str
    created_at: datetime

    model_config = {"from_attributes": True}


class LinkedInGenerateResponse(BaseModel):
    """API response: generated LinkedIn posts for a given content_id."""

    content_id: int
    posts: list[LinkedInPostOut]


class TwitterThreadOut(BaseModel):
    """A single generated Twitter/X thread from long-form content."""

    id: int
    content_id: int
    title: Optional[str]
    tweets: list[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class TwitterGenerateResponse(BaseModel):
    """API response: generated Twitter/X threads for a given content_id."""

    content_id: int
    threads: list[TwitterThreadOut]


class InstagramCaptionVariant(BaseModel):
    """A single generated Instagram caption variant."""

    id: int
    style: str
    text: str
    hashtags: list[str]
    character_count: int


class InstagramCaptionResponse(BaseModel):
    """API response: generated Instagram captions for a given content_id."""

    content_id: int
    captions: list[InstagramCaptionVariant]


class InstagramGenerateRequest(BaseModel):
    """Request body to generate Instagram captions for a content item."""

    audience: str
    tone: str
    goal: Optional[str] = None
