from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar, TypedDict


SYSTEM_INSTRUCTION = "Extract a short descriptive title, a clear concise summary, and 2-7 relevant tags from the user text."

RESPONSE_SCHEMA = {
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


class CleanedIdea(TypedDict):
    """Structure returned by LLM cleanup."""

    title: str
    summary: str
    tags: list[str]


class LlmError(Exception):
    """Raised when the LLM cleanup process fails."""


def ensure_default_tags(tags: list[str]) -> list[str]:
    """Deduplicate tags and fall back to ['misc'] if empty."""

    unique = list(dict.fromkeys(tag for tag in tags if tag))
    return unique or ["misc"]


def normalize_cleaned_idea(
    parsed: object, *, provider_display_name: str
) -> CleanedIdea:
    if not isinstance(parsed, dict):
        raise LlmError(f"{provider_display_name} returned invalid structured output.")

    title = str(parsed.get("title", "") or "")
    summary = str(parsed.get("summary", "") or "")
    tags_value: Any = parsed.get("tags") or []

    if isinstance(tags_value, list):
        tags = [str(tag).lower() for tag in tags_value if tag]
    else:
        tags = []

    tags = ensure_default_tags(tags)

    if not title or not summary:
        raise LlmError(
            f"{provider_display_name} returned incomplete structured output."
        )

    return {"title": title, "summary": summary, "tags": tags}


class BaseLlmProvider(ABC):
    provider_key: ClassVar[str]
    display_name: ClassVar[str]
    default_model_name: ClassVar[str]

    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name or self.default_model_name

    @abstractmethod
    async def cleanup(self, raw_note: str) -> CleanedIdea:
        raise NotImplementedError
