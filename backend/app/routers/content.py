from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Content
from app.schemas import ContentCreate, ContentResponse

router = APIRouter(prefix="/api/content", tags=["content"])


@router.post("/", response_model=ContentResponse, status_code=201)
async def create_content(
    content_in: ContentCreate, 
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new Content item.

    Args:
        content_in (ContentCreate): Input data for the content.
        db (AsyncSession): Database session (dependency).

    Returns:
        Content: The created content record.
    """
    word_count = len(content_in.original_text.split())
    db_content = Content(
        original_text=content_in.original_text,
        title=content_in.title,
        source_url=content_in.source_url,
        word_count=word_count,
    )
    db.add(db_content)
    await db.commit()
    await db.refresh(db_content)
    return db_content



@router.get("/", response_model=list[ContentResponse])
async def get_contents(
    skip: int = 0, 
    limit: int = 10, 
    db: AsyncSession = Depends(get_db)
):
    """
    Get a list of content items, ordered by most recent.

    Args:
        skip (int): Number of items to skip for pagination.
        limit (int): Maximum number of items to return.
        db (AsyncSession): Database session (dependency).

    Returns:
        List[ContentResponse]: List of content records.
    """
    result = await db.execute(
        select(Content).order_by(Content.created_at.desc()).offset(skip).limit(limit)
    )
    return result.scalars().all()


@router.get("/{content_id}", response_model=ContentResponse)
async def get_content(
    content_id: int, 
    db: AsyncSession = Depends(get_db)
):
    """
    Get a single content item by its ID.

    Args:
        content_id (int): The ID of the content to retrieve.
        db (AsyncSession): Database session (dependency).

    Returns:
        ContentResponse: The found content record.

    Raises:
        HTTPException: If content item is not found (404).
    """
    result = await db.execute(select(Content).where(Content.id == content_id))
    content = result.scalar_one_or_none()
    if content is None:
        raise HTTPException(status_code=404, detail="Content not found")
    return content
