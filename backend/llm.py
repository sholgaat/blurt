from __future__ import annotations

import asyncio
import json
import logging
from functools import lru_cache
from typing import Any

from google import genai
from google.genai import types

from idea_inbox import settings

LOGGER = logging.getLogger(__name__)
MODEL_NAME = "gemini-2.5-flash-lite"
SYSTEM_INSTRUCTION = (
    "Extract a short descriptive title, a clear concise summary, and 2-7 relevant tags from the user text."
)

_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "summary": {"type": "string"},
        "tags": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
            "maxItems": 7,
        },
    },
    "required": ["title", "summary", "tags"],
}


@lru_cache(maxsize=1)
def _get_client() -> genai.Client:
    api_key = settings.get_gemini_api_key()
    if not api_key:
        raise LlmError("GEMINI_API_KEY is not configured.")
    return genai.Client(api_key=api_key)


class LlmError(Exception):
    """Raised when the LLM cleanup process fails."""


def ensure_default_tags(tags: list[str]) -> list[str]:
    """Deduplicate tags and fall back to ['misc'] if empty."""
    unique = list(dict.fromkeys(tag for tag in tags if tag))
    return unique or ["misc"]


async def call_ai_cleanup(raw_note: str) -> dict[str, Any]:
    """Call Google Gemini to clean up an idea note."""
    client = _get_client()
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        response_mime_type="application/json",
        response_schema=_RESPONSE_SCHEMA,
    )

    def _invoke_model() -> Any:
        return client.models.generate_content(
            model=MODEL_NAME,
            contents=f"TEXT:\n{raw_note}",
            config=config,
        )

    try:
        response = await asyncio.to_thread(_invoke_model)
        response_text = response.text or ""

        usage = getattr(response, "usage_metadata", None)
        if usage:
            LOGGER.info(
                "LLM usage - prompt: %s tokens, completion: %s tokens, total: %s tokens",
                getattr(usage, "prompt_token_count", "?"),
                getattr(usage, "candidates_token_count", "?"),
                getattr(usage, "total_token_count", "?"),
            )

        parsed = json.loads(response_text or "{}")
    except Exception as exc:
        LOGGER.exception("Gemini client call failed: %s", exc)
        raise LlmError("Gemini client call failed") from exc

    title = str(parsed.get("title", "") or "")
    summary = str(parsed.get("summary", "") or "")
    tags_value = parsed.get("tags") or []
    if isinstance(tags_value, list):
        tags = [str(tag).lower() for tag in tags_value if tag]
    else:
        tags = []

    tags = ensure_default_tags(tags)

    return {"title": title, "summary": summary, "tags": tags}
