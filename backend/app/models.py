"""SQLAlchemy ORM models for users, content, generated_posts."""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, DateTime
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    contents = relationship("Content", back_populates="user")


class Content(Base):
    """
    ORM model for content uploaded by users.
    
    Fields:
        id: Primary key.
        user_id: Foreign key to users.id, nullable.
        original_text: Original content text.
        title: Optional title.
        word_count: Number of words.
        source_url: Optional source URL.
        created_at: Timestamp.
    Relationships:
        user: Reference to the User who uploaded.
        generated_posts: Associated generated posts.
    """
    __tablename__ = "content"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    original_text = Column(Text, nullable=False)
    title = Column(String(255))
    word_count = Column(Integer)
    source_url = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="contents")
    generated_posts = relationship("GeneratedPost", back_populates="content")


class GeneratedPost(Base):
    """
    Represents a generated post for a specific platform, linked to content.

    Fields:
        id: Primary key.
        content_id: Foreign key to content.id (CASCADE on delete).
        platform: Platform name (e.g., linkedin, twitter).
        generated_text: The output text generated for the platform.
        post_metadata: Optional JSON (avoids SQLAlchemy reserved 'metadata').
        is_favorite: Boolean flag for user favorites.
        created_at: Timestamp of creation.
    Relationships:
        content: Reference to the original Content instance.
    """
    __tablename__ = "generated_posts"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, ForeignKey("content.id", ondelete="CASCADE"), nullable=False)
    platform = Column(String(50), nullable=False)
    generated_text = Column(Text, nullable=False)
    post_metadata = Column(JSON)
    is_favorite = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    content = relationship("Content", back_populates="generated_posts")
