"""Pollinations image generation helpers (prompt and URL builders).

This module does NOT call the Pollinations API directly. Instead, it builds
upstream image URLs that are fetched by a backend proxy route, backed by:

    https://gen.pollinations.ai/image/{prompt}

See:
- https://enter.pollinations.ai/api/docs
- https://raw.githubusercontent.com/pollinations/pollinations/master/APIDOCS.md
"""

from __future__ import annotations

import random
from typing import Literal
from urllib.parse import quote

from app.logging_config import get_logger
from app.models import Content

log = get_logger(__name__)


ImageType = Literal["image_cover", "image_instagram"]


def build_image_prompt(
    title: str | None,
    summary: str,
    platform: str,
    style: str,
) -> str:
    """Compose a concise visual description for Pollinations.

    The prompt intentionally avoids requesting overlaid text to prevent
    unwanted words in the generated image. Text for thumbnails remains
    a separate concern handled by text generators.
    """
    base_parts: list[str] = []

    if title:
        base_parts.append(f"Topic: {title.strip()}. ")

    base_parts.append(summary.strip())

    # Map style presets to descriptive modifiers.
    style_map = {
        "minimal_gradient": "minimalist flat illustration, soft gradients, high contrast, no text, clean UI style",
        "photo_realistic": "photo-realistic scene, natural lighting, cinematic, no text",
        "tech_dark": "futuristic user interface on dark background, neon accents, no text",
        "pastel_illustration": "pastel color palette, friendly illustration, soft shapes, no text",
    }
    style_description = style_map.get(
        style,
        "modern illustration, clear focal point, no text",
    )

    if platform == "instagram":
        platform_hint = (
            "instagram post, square composition, visually striking, centered subject. "
        )
    else:
        platform_hint = (
            "social media share image, 16:9 aspect ratio, suitable as a blog or "
            "LinkedIn cover. "
        )

    prompt = (
        f"{platform_hint}"
        f"{style_description}. "
        f"Do not include any words or letters in the image. "
        f"{' '.join(base_parts)}"
    )
    return prompt


def build_pollinations_image_url(
    prompt: str,
    *,
    width: int,
    height: int,
    model: str = "flux",
    seed: int | None = None,
) -> str:
    """Build a Pollinations image URL for the given prompt and dimensions.

    Uses the documented pattern:
        https://gen.pollinations.ai/image/{url_encoded_prompt}?width=...&height=...&model=flux&safe=true[&seed=...]
    """
    encoded_prompt = quote(prompt, safe="")
    base_url = f"https://gen.pollinations.ai/image/{encoded_prompt}"

    params = [
        f"width={width}",
        f"height={height}",
        f"model={model}",
        "safe=true",
    ]
    if seed is not None:
        params.append(f"seed={seed}")

    return f"{base_url}?{'&'.join(params)}"


def generate_image_spec_for_content(
    content: Content,
    *,
    style: str,
    requested_type: Literal["cover", "instagram"],
) -> dict:
    """Build the image spec dict for a piece of content.

    The resulting dict is suitable for storage in GeneratedPost.post_metadata.
    """
    # Choose dimensions and internal type based on requested type.
    if requested_type == "instagram":
        width, height = 1080, 1080
        image_type: ImageType = "image_instagram"
        platform = "instagram"
    else:
        width, height = 1200, 630
        image_type = "image_cover"
        platform = "thumbnail"

    # Use a short slice of original_text as a crude "summary" fallback.
    raw_text = (content.original_text or "").strip()
    summary = raw_text[:400] if len(raw_text) > 400 else raw_text

    full_prompt = build_image_prompt(
        title=content.title,
        summary=summary,
        platform=platform,
        style=style,
    )
    # Keep the upstream prompt shorter to avoid overly long URLs.
    prompt_short = full_prompt[:250]

    seed = random.randint(1, 999_999_999)
    upstream_url = build_pollinations_image_url(
        prompt=prompt_short,
        width=width,
        height=height,
        model="flux",
        seed=seed,
    )

    spec = {
        "type": image_type,
        "upstream_url": upstream_url,
        "width": width,
        "height": height,
        "style": style,
        "prompt": full_prompt,
        "prompt_short": prompt_short,
        "model": "flux",
        "seed": seed,
        "aspect_ratio": f"{width}:{height}",
    }

    log.info(
        "pollinations_image_spec_built",
        content_id=content.id,
        type=image_type,
        width=width,
        height=height,
        style=style,
    )

    return spec

