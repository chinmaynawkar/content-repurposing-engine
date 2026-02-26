"""Pydantic schemas for content and generated_posts."""

from datetime import datetime
from typing import Literal, Optional

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


class SeoMetaVariant(BaseModel):
    """A single generated SEO meta description variant."""

    id: int
    description: str
    character_count: int
    primary_keyword: str


class SeoMetaResponse(BaseModel):
    """API response: generated SEO meta descriptions for a given content_id."""

    content_id: int
    metas: list[SeoMetaVariant]


class SeoMetaGenerateRequest(BaseModel):
    """Request body to generate SEO meta descriptions for a content item."""

    primary_keyword: str
    search_intent: Literal[
        "informational",
        "transactional",
        "navigational",
        "commercial",
    ]
    tone: Optional[str] = None


class ImageSpec(BaseModel):
    """A generated image specification backed by Pollinations."""

    id: int
    type: Literal["image_cover", "image_instagram"]
    image_url: str
    width: int
    height: int
    style: str
    prompt: str


class ImageGenerateRequest(BaseModel):
    """Request body to generate an image for a content item."""

    style: str = "minimal_gradient"
    type: Literal["cover", "instagram"] = "cover"


class ImageGenerateResponse(BaseModel):
    """API response: generated image spec for a given content_id."""

    content_id: int
    image: ImageSpec
