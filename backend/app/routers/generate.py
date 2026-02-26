import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.logging_config import get_logger
from app.models import Content, GeneratedPost
from app.schemas import (
    ImageGenerateRequest,
    ImageGenerateResponse,
    InstagramCaptionResponse,
    InstagramGenerateRequest,
    LinkedInGenerateResponse,
    SeoMetaGenerateRequest,
    SeoMetaResponse,
    TwitterGenerateResponse,
)
from app.services.gemini_service import (
    generate_instagram_captions_from_text,
    generate_linkedin_posts_from_text,
)
from app.services.groq_service import (
    generate_seo_meta_from_text,
    generate_twitter_threads_from_text,
)
from app.services.pollinations_service import (
    build_pollinations_image_url,
    generate_image_spec_for_content,
)


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


@router.post(
    "/image/{content_id}",
    response_model=ImageGenerateResponse,
    status_code=201,
)
async def generate_image(
    content_id: int,
    body: ImageGenerateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ImageGenerateResponse:
    """
    Generate a single image specification for a piece of content using Pollinations.

    The backend stores image generation metadata and returns a proxy URL.
    The browser hits our proxy route, which fetches the upstream image from
    gen.pollinations.ai with backend credentials.
    """
    result = await db.execute(select(Content).where(Content.id == content_id))
    content = result.scalar_one_or_none()
    if content is None:
        raise HTTPException(status_code=404, detail="Content not found")

    text = (content.original_text or "").strip()
    if len(text) < 20:
        raise HTTPException(status_code=400, detail="Content too short for generation")

    image_spec = generate_image_spec_for_content(
        content,
        style=body.style,
        requested_type=body.type,
    )

    platform = "instagram" if image_spec.get("type") == "image_instagram" else "thumbnail"

    row = GeneratedPost(
        content_id=content.id,
        platform=platform,
        generated_text=image_spec.get("prompt", ""),
        post_metadata=image_spec,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)

    meta = row.post_metadata or image_spec
    proxy_url = str(request.base_url).rstrip("/") + f"/api/generate/image/serve/{row.id}"

    return ImageGenerateResponse(
        content_id=content.id,
        image={
            "id": row.id,
            "type": meta.get("type"),
            "image_url": proxy_url,
            "width": meta.get("width"),
            "height": meta.get("height"),
            "style": meta.get("style"),
            "prompt": meta.get("prompt"),
        },
    )


@router.post(
    "/instagram/{content_id}",
    response_model=InstagramCaptionResponse,
    status_code=201,
)
async def generate_instagram_captions(
    content_id: int,
    body: InstagramGenerateRequest,
    db: AsyncSession = Depends(get_db),
) -> InstagramCaptionResponse:
    """
    Generate up to 3 Instagram caption variants from long-form content using Gemini.

    Requires request body: audience, tone, optional goal.
    """
    result = await db.execute(select(Content).where(Content.id == content_id))
    content = result.scalar_one_or_none()
    if content is None:
        raise HTTPException(status_code=404, detail="Content not found")

    text = (content.original_text or "").strip()
    if len(text) < 20:
        raise HTTPException(status_code=400, detail="Content too short for generation")

    try:
        generated = generate_instagram_captions_from_text(
            text,
            audience=body.audience,
            tone=body.tone,
            goal=body.goal,
            title=content.title,
        )
    except Exception as exc:
        log.warning(
            "gemini_instagram_generation_failed",
            content_id=content_id,
            error=str(exc),
        )
        raise HTTPException(status_code=502, detail="Instagram generation failed")

    if not generated:
        log.warning("gemini_returned_no_instagram_captions", content_id=content_id)
        raise HTTPException(status_code=500, detail="No captions generated")

    caption_rows: list[GeneratedPost] = []
    for item in generated:
        row = GeneratedPost(
            content_id=content.id,
            platform="instagram",
            generated_text=item.get("text") or "",
            post_metadata={
                "style": item.get("style", "default"),
                "text": item.get("text", ""),
                "hashtags": item.get("hashtags") or [],
                "character_count": item.get("character_count", 0),
            },
        )
        db.add(row)
        caption_rows.append(row)

    await db.commit()
    for row in caption_rows:
        await db.refresh(row)

    captions = []
    for row in caption_rows:
        meta = row.post_metadata or {}
        captions.append(
            {
                "id": row.id,
                "style": meta.get("style", "default"),
                "text": row.generated_text or meta.get("text", ""),
                "hashtags": meta.get("hashtags", []),
                "character_count": meta.get("character_count", len(row.generated_text or "")),
            }
        )

    return InstagramCaptionResponse(content_id=content.id, captions=captions)


@router.get("/image/serve/{generated_post_id}")
async def serve_generated_image(
    generated_post_id: int,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """
    Proxy a generated image via backend to avoid exposing Pollinations API keys.
    """
    result = await db.execute(
        select(GeneratedPost).where(GeneratedPost.id == generated_post_id)
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Generated image not found")

    metadata = row.post_metadata or {}
    if not isinstance(metadata, dict):
        raise HTTPException(status_code=404, detail="Generated image metadata missing")

    prompt = (metadata.get("prompt_short") or metadata.get("prompt") or "").strip()
    if not prompt:
        raise HTTPException(status_code=404, detail="Generated image metadata missing")

    if not settings.POLLINATIONS_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Image generation proxy is not configured. Set POLLINATIONS_API_KEY.",
        )

    width = int(metadata.get("width") or 1024)
    height = int(metadata.get("height") or 1024)
    model = str(metadata.get("model") or "flux")
    seed_value = metadata.get("seed")
    seed = int(seed_value) if seed_value is not None else None

    upstream_url = build_pollinations_image_url(
        prompt=prompt[:250],
        width=width,
        height=height,
        model=model,
        seed=seed,
    )

    headers = {"Authorization": f"Bearer {settings.POLLINATIONS_API_KEY}"}
    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            upstream_response = await client.get(upstream_url, headers=headers)
    except httpx.HTTPError as exc:
        log.warning("pollinations_proxy_request_failed", error=str(exc))
        raise HTTPException(status_code=502, detail="Pollinations upstream request failed")

    if upstream_response.status_code >= 400:
        log.warning(
            "pollinations_proxy_upstream_error",
            status_code=upstream_response.status_code,
            body=upstream_response.text[:300],
        )
        raise HTTPException(
            status_code=502,
            detail=f"Pollinations upstream error: {upstream_response.status_code}",
        )

    media_type = upstream_response.headers.get("content-type", "image/jpeg")
    return Response(content=upstream_response.content, media_type=media_type)


@router.post(
    "/seo/{content_id}",
    response_model=SeoMetaResponse,
    status_code=201,
)
async def generate_seo_meta(
    content_id: int,
    body: SeoMetaGenerateRequest,
    db: AsyncSession = Depends(get_db),
) -> SeoMetaResponse:
    """
    Generate up to 3 SEO meta description variants from long-form content using Groq.

    Requires request body: primary_keyword, search_intent, optional tone.
    """
    result = await db.execute(select(Content).where(Content.id == content_id))
    content = result.scalar_one_or_none()
    if content is None:
        raise HTTPException(status_code=404, detail="Content not found")

    text = (content.original_text or "").strip()
    if len(text) < 20:
        raise HTTPException(status_code=400, detail="Content too short for generation")

    try:
        generated = generate_seo_meta_from_text(
            text,
            title=content.title,
            primary_keyword=body.primary_keyword,
            search_intent=body.search_intent,
            tone=body.tone,
        )
    except Exception as exc:
        log.warning(
            "groq_seo_generation_failed",
            content_id=content_id,
            error=str(exc),
        )
        raise HTTPException(status_code=502, detail="SEO generation failed")

    if not generated:
        log.warning("groq_seo_returned_no_metas", content_id=content_id)
        raise HTTPException(status_code=500, detail="No meta descriptions generated")

    meta_rows: list[GeneratedPost] = []
    for item in generated:
        description = (item.get("description") or "").strip()
        if not description:
            continue
        row = GeneratedPost(
            content_id=content.id,
            platform="seo",
            generated_text=description,
            post_metadata={
                "primary_keyword": item.get("primary_keyword") or body.primary_keyword,
                "character_count": item.get("character_count", len(description)),
            },
        )
        db.add(row)
        meta_rows.append(row)

    if not meta_rows:
        log.warning("no_valid_seo_metas_to_persist", content_id=content_id)
        raise HTTPException(status_code=500, detail="No meta descriptions generated")

    await db.commit()
    for row in meta_rows:
        await db.refresh(row)

    metas = []
    for row in meta_rows:
        meta = row.post_metadata or {}
        description = row.generated_text or meta.get("description", "")
        metas.append(
            {
                "id": row.id,
                "description": description,
                "character_count": meta.get(
                    "character_count",
                    len(description),
                ),
                "primary_keyword": meta.get("primary_keyword", body.primary_keyword),
            }
        )

    return SeoMetaResponse(content_id=content.id, metas=metas)
