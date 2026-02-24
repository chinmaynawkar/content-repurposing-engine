from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.logging_config import get_logger
from app.models import Content, GeneratedPost
from app.schemas import LinkedInGenerateResponse, TwitterGenerateResponse
from app.services.gemini_service import generate_linkedin_posts_from_text
from app.services.groq_service import generate_twitter_threads_from_text


router = APIRouter(prefix="/api/generate", tags=["generate"])

log = get_logger(__name__)


@router.post(
    "/linkedin/{content_id}",
    response_model=LinkedInGenerateResponse,
    status_code=201,
)
async def generate_linkedin_posts(
    content_id: int,
    db: AsyncSession = Depends(get_db),
) -> LinkedInGenerateResponse:
    """
    Generate 3 LinkedIn posts from long-form content using the Gemini AI service.

    Args:
        content_id (int): The ID of the existing Content object to repurpose.
        db (AsyncSession): SQLAlchemy async session via dependency injection.

    Returns:
        LinkedInGenerateResponse: Pydantic schema containing the generated posts.

    Raises:
        404: If content_id is not found in the database.
        400: If content text is too short for generation.
        502: If the Gemini service call fails.
        500: If parsing fails or no valid posts are generated.
    """
    # 1) Fetch content by id from the DB; raise 404 if not found.
    result = await db.execute(select(Content).where(Content.id == content_id))
    content = result.scalar_one_or_none()
    if content is None:
        raise HTTPException(status_code=404, detail="Content not found")

    # 2) Basic validation on text length (must be >=20 chars); else 400.
    text = (content.original_text or "").strip()
    if len(text) < 20:
        raise HTTPException(status_code=400, detail="Content too short for generation")

    # 3) Call Gemini service to generate post variants from this text.
    try:
        generated = generate_linkedin_posts_from_text(text)
    except Exception as exc:  # pragma: no cover - mapped to 502
        log.warning(
            "gemini_generation_failed",
            content_id=content_id,
            error=str(exc),
        )
        raise HTTPException(status_code=502, detail="Gemini generation failed")

    # Raise 500 if the AI service returns nothing usable.
    if not generated:
        log.warning("gemini_returned_no_posts", content_id=content_id)
        raise HTTPException(status_code=500, detail="No posts generated")

    # 4) Persist each valid post as a GeneratedPost (skip empty bodies).
    post_rows: list[GeneratedPost] = []
    for item in generated:
        body = (item.get("body") or "").strip()
        if not body:
            continue  # Skip posts with empty body
        title = (item.get("title") or "").strip()
        row = GeneratedPost(
            content_id=content.id,
            platform="linkedin",
            generated_text=body,
            post_metadata={"title": title} if title else None,
        )
        db.add(row)
        post_rows.append(row)

    # Ensure at least one post is valid; otherwise fail fast.
    if not post_rows:
        log.warning("no_valid_posts_to_persist", content_id=content_id)
        raise HTTPException(status_code=500, detail="No posts generated")

    # Commit all inserted GeneratedPosts and refresh to get IDs/timestamps.
    await db.commit()
    for row in post_rows:
        await db.refresh(row)

    # Build response objects explicitly so schema fields (title/body) are clear.
    response_posts = []
    for row in post_rows:
        metadata = row.post_metadata or {}
        response_posts.append(
            {
                "id": row.id,
                "content_id": row.content_id,
                "title": metadata.get("title"),
                "body": row.generated_text,
                "created_at": row.created_at,
            }
        )

    # Return the response containing the persisted LinkedIn posts.
    return LinkedInGenerateResponse(content_id=content.id, posts=response_posts)


@router.post(
    "/twitter/{content_id}",
    response_model=TwitterGenerateResponse,
    status_code=201,
)
async def generate_twitter_threads(
    content_id: int,
    db: AsyncSession = Depends(get_db),
) -> TwitterGenerateResponse:
    """
    Generate Twitter/X threads from long-form content using the Groq service.

    Raises:
        404: If content_id is not found in the database.
        400: If content text is too short for generation.
        502: If the Groq service call fails.
        500: If parsing fails or no valid threads are generated.
    """
    # 1) Fetch content by id from the DB; raise 404 if not found.
    result = await db.execute(select(Content).where(Content.id == content_id))
    content = result.scalar_one_or_none()
    if content is None:
        raise HTTPException(status_code=404, detail="Content not found")

    # 2) Basic validation on text length (must be >=20 chars); else 400.
    text = (content.original_text or "").strip()
    if len(text) < 20:
        raise HTTPException(status_code=400, detail="Content too short for generation")

    # 3) Call Groq service to generate thread variants from this text.
    try:
        generated = generate_twitter_threads_from_text(text)
    except Exception as exc:  # pragma: no cover - mapped to 502
        log.warning(
            "groq_generation_failed",
            content_id=content_id,
            error=str(exc),
        )
        raise HTTPException(status_code=502, detail="Groq generation failed")

    # Raise 500 if the AI service returns nothing usable.
    if not generated:
        log.warning("groq_returned_no_threads", content_id=content_id)
        raise HTTPException(status_code=500, detail="No threads generated")

    # 4) Persist each valid thread as a GeneratedPost.
    thread_rows: list[GeneratedPost] = []
    for item in generated:
        tweets = [t for t in (item.get("tweets") or []) if isinstance(t, str) and t.strip()]
        if not tweets:
            continue
        title = (item.get("title") or "").strip()
        generated_text = "\n\n".join(tweets)
        row = GeneratedPost(
            content_id=content.id,
            platform="twitter",
            generated_text=generated_text,
            post_metadata={"title": title, "tweets": tweets},
        )
        db.add(row)
        thread_rows.append(row)

    # Ensure at least one thread is valid; otherwise fail fast.
    if not thread_rows:
        log.warning("no_valid_threads_to_persist", content_id=content_id)
        raise HTTPException(status_code=500, detail="No threads generated")

    # Commit all inserted GeneratedPosts and refresh to get IDs/timestamps.
    await db.commit()
    for row in thread_rows:
        await db.refresh(row)

    # Build response objects explicitly so schema fields (title/tweets) are clear.
    response_threads = []
    for row in thread_rows:
        metadata = row.post_metadata or {}
        response_threads.append(
            {
                "id": row.id,
                "content_id": row.content_id,
                "title": metadata.get("title"),
                "tweets": metadata.get("tweets") or [],
                "created_at": row.created_at,
            }
        )

    # Return the response containing the persisted Twitter threads.
    return TwitterGenerateResponse(content_id=content.id, threads=response_threads)
