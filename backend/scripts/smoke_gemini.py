"""Manual smoke check for generate_linkedin_posts_from_text. Run from backend/ with venv active.

Usage (from backend/):
  PYTHONPATH=. python scripts/smoke_gemini.py

Requires GEMINI_API_KEY in .env. Makes a real API call; for local/manual use only.
"""

import sys
from pathlib import Path

# Ensure app is importable when run as script from backend/
backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.services.gemini_service import generate_linkedin_posts_from_text

SAMPLE_TEXT = """
Remote work has fundamentally changed how we measure productivity. Instead of hours at a desk,
teams are focusing on outcomes and deliverables. This shift requires new habits: clear
communication, async-first workflows, and trust. Companies that adapt will attract and
retain the best talent.
"""


def main() -> None:
    print("Calling generate_linkedin_posts_from_text with sample text...")
    result = generate_linkedin_posts_from_text(SAMPLE_TEXT)
    print(f"len(result) = {len(result)}")
    if result:
        print(f"First post keys: {list(result[0].keys())}")
        print(f"First post title (preview): {result[0].get('title', '')[:60]}...")
        print(f"First post body (preview): {result[0].get('body', '')[:120]}...")
    else:
        print("No posts returned.")
    print("Smoke check done.")


if __name__ == "__main__":
    main()
