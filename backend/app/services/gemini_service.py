"""Gemini-backed generation service for platform-specific posts."""

import json
import re # built-in regular expression module, enabling advanced string searching, matching, splitting, substitution based on text pattern
from google import genai

from app.config import settings
from app.logging_config import get_logger

log = get_logger(__name__)

# Client uses API key from config only (Twelve-Factor).
client = genai.Client(api_key=settings.GEMINI_API_KEY)

# Free-tier friendly: highest RPD (1,000/day) and lowest cost. See ai.google.dev/gemini-api/docs/rate-limits
LINKEDIN_MODEL = "gemini-2.5-flash-lite"

LINKEDIN_SYSTEM_INSTRUCTIONS = """You are a professional content repurposer. Given long-form content, produce exactly 3 LinkedIn posts.

For each post:
- Professional tone, suitable for LinkedIn.
- Length: 150–300 words per post.
- Start with a strong hook.
- Include 3–5 relevant hashtags at the end.
- Each post should offer a distinct angle or takeaway from the source content.

Return ONLY valid JSON. No markdown, no code fences, no backticks. Use this exact schema:
{"posts": [{"title": "Short title for the post", "body": "Full post text including hashtags"}, ...]}

Content to repurpose:
"""


def _strip_json_fences(raw: str) -> str:
    """Remove markdown code fences (e.g. ```json ... ```) from string."""
    text = raw.strip()
    # Match optional ```json or ``` at start, optional ``` at end
    m = re.match(r"^```(?:json)?\s*\n?(.*?)\n?```\s*$", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return text


def _normalize_posts(parsed: dict) -> list[dict]:
    """Extract and normalize posts list to [{"title": str, "body": str}, ...]; skip empty body."""
    posts = parsed.get("posts")
    if not isinstance(posts, list):
        return []
    result = []
    for item in posts:
        if not isinstance(item, dict):
            continue
        body = item.get("body")
        if body is None:
            body = item.get("content", "")
        body = str(body).strip() if body else ""
        if not body:
            continue
        title = item.get("title")
        title = str(title).strip() if title is not None else ""
        result.append({"title": title, "body": body})
    return result


def generate_linkedin_posts_from_text(content_text: str) -> list[dict]:
    """
    Generate 1–3 LinkedIn post dicts from long-form text using Gemini.

    Returns list of dicts with keys "title" (str, may be empty) and "body" (str).
    On API or network failure, raises (caller should return 502).
    On parse failure or empty/invalid JSON, returns [] (caller should return 500).
    """
    if not content_text or not content_text.strip():
        return []

    prompt = LINKEDIN_SYSTEM_INSTRUCTIONS + content_text.strip()

    try:
        response = client.models.generate_content(
            model=LINKEDIN_MODEL,
            contents=prompt,
        )
    except Exception as e:
        log.warning("gemini_generate_failed", error=str(e))
        raise

    raw = getattr(response, "text", None)
    if not raw or not str(raw).strip():
        log.warning("gemini_empty_response", model=LINKEDIN_MODEL)
        return []

    text = str(raw).strip()

    # Parse JSON; retry after stripping code fences if needed.
    parsed = None
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        stripped = _strip_json_fences(text)
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError as e:
            log.warning("gemini_invalid_json", error=str(e))
            return []

    if not isinstance(parsed, dict):
        log.warning("gemini_unexpected_structure", type=type(parsed).__name__)
        return []

    return _normalize_posts(parsed)
