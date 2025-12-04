from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, List

from google import genai
from google.genai import types
import tiktoken

from idea_inbox import settings

LOGGER = logging.getLogger(__name__)
MODEL_NAME = "gemini-2.5-flash-lite"
SYSTEM_INSTRUCTION = (
    "Extract a short descriptive title, a clear concise summary, and 2–7 relevant tags from the user text."
)
ENCODING = tiktoken.get_encoding("cl100k_base")


def _escape_text(text: str) -> str:
    """Escape user-provided text for safe JSON embedding."""
    dumped = json.dumps(text or "")
    return dumped[1:-1]


def _count_tokens(text: str) -> int:
    if not text:
        return 0
    try:
        return len(ENCODING.encode(text))
    except Exception as exc:  # pragma: no cover - defensive logging
        LOGGER.warning("Failed to count tokens: %s", exc)
        return 0


class LlmError(Exception):
    """Raised when the LLM cleanup process fails."""


async def call_ai_cleanup(raw_note: str) -> Dict[str, Any]:
    """Call Google Gemini to clean up an idea note."""
    api_key = settings.get_google_api_key()
    if not api_key:
        raise LlmError("GOOGLE_API_KEY is not configured.")

    client = genai.Client(api_key=api_key)
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        response_mime_type="application/json",
        response_schema={
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
        },
    )

    escaped_text = _escape_text(raw_note or "")
    prompt_tokens = _count_tokens(raw_note)

    def _invoke_model() -> Any:
        return client.models.generate_content(
            model=MODEL_NAME,
            contents=f"TEXT:\n{escaped_text}",
            config=config,
        )

    try:
        response = await asyncio.to_thread(_invoke_model)
        response_text = response.text or ""
        completion_tokens = _count_tokens(response_text)
        total_tokens = prompt_tokens + completion_tokens
        LOGGER.info(
            "LLM usage - prompt: %s tokens, completion: %s tokens, total: %s tokens",
            prompt_tokens,
            completion_tokens,
            total_tokens,
        )
        parsed = json.loads(response_text or "{}")
    except Exception as exc:
        LOGGER.exception("Gemini client call failed: %s", exc)
        raise LlmError("Gemini client call failed") from exc

    title = str(parsed.get("title", "") or "")
    summary = str(parsed.get("summary", "") or "")
    tags_value = parsed.get("tags") or []
    if isinstance(tags_value, list):
        tags: List[str] = [str(tag).lower() for tag in tags_value if tag]
    else:
        tags = []

    if not tags:
        tags = ["misc"]

    return {"title": title, "summary": summary, "tags": tags}
