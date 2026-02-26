"""Groq-backed generation service for Twitter/X threads.

This module provides a single entrypoint:

    generate_twitter_threads_from_text(content_text: str) -> list[dict]

It calls the Groq chat completions API with a free-tier Llama 3 model to
turn long-form content into multiple Twitter threads.

Manual smoke test (from backend/):

    PYTHONPATH=. venv/bin/python -c \
      "from app.services.groq_service import generate_twitter_threads_from_text as g; \
       print(g('Sample long-form content about AI and productivity.'))"

This is a convenience sanity check only; proper behaviour is verified via
the FastAPI endpoint tests in Chunk C/D.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from groq import Groq

from app.config import settings
from app.logging_config import get_logger

log = get_logger(__name__)


# Client uses API key from config only (Twelve-Factor).
client = Groq(api_key=settings.GROQ_API_KEY)

# Free-tier friendly: see https://console.groq.com/docs/models and
# https://console.groq.com/docs/rate-limits for up-to-date limits.
# llama-3.3-70b-versatile has 1K RPD on free tier at time of writing.
TWITTER_MODEL = "llama-3.3-70b-versatile"


TWITTER_SYSTEM_PROMPT = """
You are an expert Twitter (X) content writer.

Given a long-form piece of content, you will turn it into multiple high-quality Twitter threads.

For each thread:
- 3 to 7 tweets per thread.
- The first tweet MUST be a strong hook that clearly states who the thread is for and why they should read it.
- Each tweet should have ONE main idea, be concise, and easy to read.
- Use simple language; avoid jargon and filler.
- You may use line breaks inside a tweet for bullet-style formatting.
- The last tweet in each thread MUST contain a clear call-to-action (reply, share, follow, or reflect).
- Hashtags: at most 2–3, and only in the first OR last tweet (not every tweet).
- Do NOT use clickbait or fake metrics.
"""


TWITTER_OUTPUT_INSTRUCTIONS = """
Return ONLY valid JSON in this exact schema:

{
  "threads": [
    {
      "title": "Short internal title for the thread (optional)",
      "tweets": [
        "First tweet text (max 280 characters)",
        "Second tweet text (max 280 characters)",
        "Third tweet text (max 280 characters)"
      ]
    }
  ]
}

Constraints:
- Generate exactly 5 threads.
- Each thread must have between 3 and 7 tweets.
- Each tweet MUST be <= 280 characters.
- No markdown, no backticks, no explanations.
- Only return JSON.
"""


def _strip_json_fences(raw: str) -> str:
    """Remove markdown code fences (e.g. ```json ... ```) from string."""
    text = raw.strip()
    # Match optional ```json or ``` at start, optional ``` at end
    m = re.match(r"^```(?:json)?\\s*\\n?(.*?)\\n?```\\s*$", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return text


SEO_SYSTEM_PROMPT = """
You are an SEO expert writing meta descriptions for search engine result pages (SERPs).

Given a long-form piece of content, you will generate multiple high-quality meta
descriptions that would appear under a page title in Google search results.

Each meta description must:
- Clearly explain what the page is about.
- Include the primary keyword naturally.
- Use active voice and be benefit-driven.
- Optionally end with a soft call-to-action (e.g., "Learn more", "Read the full guide").
"""


SEO_OUTPUT_INSTRUCTIONS = """
Return ONLY valid JSON in this exact schema:

{
  "metas": [
    {
      "description": "Meta description text",
      "primary_keyword": "the main keyword this meta targets"
    }
  ]
}

Constraints:
- Generate exactly 3 meta descriptions.
- Each description should be between 120 and 158 characters.
- Each description MUST include the primary keyword at least once.
- No markdown, no backticks, no explanations.
- Only return JSON.
"""


def _normalize_threads(parsed: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract and normalize threads to [{\"title\": str, \"tweets\": [str]}, ...]."""
    threads = parsed.get("threads")
    if not isinstance(threads, list):
        return []

    normalized: List[Dict[str, Any]] = []

    for item in threads:
        if not isinstance(item, dict):
            continue

        title = item.get("title") or ""
        title_str = str(title).strip()

        raw_tweets = item.get("tweets") or []
        if not isinstance(raw_tweets, list):
            continue

        cleaned_tweets: List[str] = []
        for t in raw_tweets:
            s = str(t or "").strip()
            if not s:
                continue
            if len(s) > 280:
                s = s[:277] + "..."
            cleaned_tweets.append(s)

        if not cleaned_tweets:
            continue

        normalized.append(
            {
                "title": title_str,
                "tweets": cleaned_tweets,
            }
        )

    return normalized


def _normalize_seo_metas(
    parsed: Dict[str, Any],
    primary_keyword: str,
) -> List[Dict[str, Any]]:
    """Extract and normalize SEO metas to a list of dicts.

    Each dict has: {\"id\", \"description\", \"character_count\", \"primary_keyword\"}.
    """
    metas = parsed.get("metas")
    if not isinstance(metas, list):
        return []

    normalized: List[Dict[str, Any]] = []

    for idx, item in enumerate(metas, start=1):
        if not isinstance(item, dict):
            continue

        description = str(item.get("description") or "").strip()
        if not description:
            continue

        character_count = len(description)
        normalized.append(
            {
                "id": idx,
                "description": description,
                "character_count": character_count,
                "primary_keyword": primary_keyword,
            }
        )

    # Keep at most 3 variants; callers treat empty list as an error.
    return normalized[:3]


def generate_twitter_threads_from_text(content_text: str) -> List[Dict[str, Any]]:
    """
    Generate 5 Twitter thread dicts from long-form text using Groq.

    Returns a list of dicts with keys \"title\" (str, may be empty) and
    \"tweets\" (list[str]).

    On API or network failure, raises (caller should map to 502).
    On parse failure or empty/invalid JSON, returns [] (caller should map to 500).
    """
    if not content_text or not content_text.strip():
        return []

    prompt = (
        f"{TWITTER_SYSTEM_PROMPT}\n\n"
        "Long-form content:\n"
        f"\"\"\"{content_text.strip()}\"\"\"\n\n"
        f"{TWITTER_OUTPUT_INSTRUCTIONS}\n"
    )

    try:
        completion = client.chat.completions.create(
            model=TWITTER_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            temperature=0.7,
        )
    except Exception as e:  # pragma: no cover - mapped to 502 by caller
        log.warning("groq_generate_failed", error=str(e))
        raise

    if not completion or not completion.choices:
        log.warning("groq_empty_completion", model=TWITTER_MODEL)
        return []

    raw_text = getattr(completion.choices[0].message, "content", None)
    if not raw_text or not str(raw_text).strip():
        log.warning("groq_empty_response", model=TWITTER_MODEL)
        return []

    text = str(raw_text).strip()

    # Parse JSON; retry after stripping code fences if needed.
    try:
        parsed_dict = json.loads(text)
    except json.JSONDecodeError:
        stripped = _strip_json_fences(text)
        try:
            parsed_dict = json.loads(stripped)
        except json.JSONDecodeError as e:
            log.warning("groq_invalid_json", error=str(e))
            return []

    if not isinstance(parsed_dict, dict):
        log.warning("groq_unexpected_structure", type=type(parsed_dict).__name__)
        return []

    return _normalize_threads(parsed_dict)


def generate_seo_meta_from_text(
    content_text: str,
    *,
    title: str | None,
    primary_keyword: str,
    search_intent: str,
    tone: str | None = None,
) -> List[Dict[str, Any]]:
    """
    Generate up to 3 SEO meta description dicts from long-form text using Groq.

    Returns a list of dicts compatible with SeoMetaVariant:
    [{\"id\", \"description\", \"character_count\", \"primary_keyword\"}, ...].

    On API or network failure, raises (caller should map to 502).
    On parse failure or empty/invalid JSON, returns [] (caller should map to 500).
    """
    # Build the prompt for the Groq API to generate SEO meta descriptions.
    # - If there is no content, return an empty list.
    # - Collect the prompt instructions, page title, keyword, search intent, tone, and content.
    # - Join it all together for the model.

    if not content_text or not content_text.strip():
        # If there is no content to analyze, return an empty list.
        return []

    parts: list[str] = [SEO_SYSTEM_PROMPT.strip(), ""]

    if title:
        # If a title is given, add it to the prompt.
        parts.append(f"Page title: {title.strip()}")

    # Always add primary keyword and search intent to the prompt.
    parts.append(f"Primary keyword: {primary_keyword.strip()}")
    parts.append(f"Search intent: {search_intent.strip()}")

    if tone:
        # If a tone is given, add it to the prompt.
        parts.append(f"Tone: {tone.strip()}")

    # Add the main content to the prompt, separated for clarity.
    parts.append("\nLong-form content:\n")
    parts.append(f"\"\"\"{content_text.strip()}\"\"\"")
    parts.append("\n")

    # Add instructions for how the output should be formatted.
    parts.append(SEO_OUTPUT_INSTRUCTIONS.strip())

    prompt = "\n".join(parts)

    try:
        completion = client.chat.completions.create(
            model=TWITTER_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            temperature=0.5,
        )
    except Exception as e:  # pragma: no cover - mapped to 502 by caller
        log.warning("groq_seo_generate_failed", error=str(e))
        raise

    if not completion or not completion.choices:
        log.warning("groq_seo_empty_completion", model=TWITTER_MODEL)
        return []

    raw_text = getattr(completion.choices[0].message, "content", None)
    if not raw_text or not str(raw_text).strip():
        log.warning("groq_seo_empty_response", model=TWITTER_MODEL)
        return []

    text = str(raw_text).strip()

    # Parse JSON; retry after stripping code fences if needed.
    try:
        parsed_dict = json.loads(text)
    except json.JSONDecodeError:
        stripped = _strip_json_fences(text)
        try:
            parsed_dict = json.loads(stripped)
        except json.JSONDecodeError as e:
            log.warning("groq_seo_invalid_json", error=str(e))
            return []

    if not isinstance(parsed_dict, dict):
        log.warning("groq_seo_unexpected_structure", type=type(parsed_dict).__name__)
        return []

    return _normalize_seo_metas(parsed_dict, primary_keyword=primary_keyword)

