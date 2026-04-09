from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

from pydantic import BaseModel, field_validator


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


class CleanedIdea(BaseModel):
    """Structure returned by LLM cleanup."""

    title: str
    summary: str
    tags: list[str]

    @field_validator("title", "summary")
    @classmethod
    def must_not_be_blank(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("must not be empty")
        return value.strip()

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, value: list[str]) -> list[str]:
        return _default_tags([tag.lower() for tag in value if tag])


class LlmError(Exception):
    """Raised when the LLM cleanup process fails."""


def _default_tags(tags: list[str]) -> list[str]:
    """Deduplicate tags and fall back to ['misc'] if empty."""

    unique = list(dict.fromkeys(tags))
    return unique or ["misc"]


class BaseLlmProvider(ABC):
    provider_key: ClassVar[str]
    display_name: ClassVar[str]
    default_model_name: ClassVar[str]

    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name or self.default_model_name

    @abstractmethod
    async def cleanup(self, raw_note: str) -> CleanedIdea:
        raise NotImplementedError
