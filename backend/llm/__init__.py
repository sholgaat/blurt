from __future__ import annotations

import logging

from backend.llm.base import CleanedIdea, LlmError, ensure_default_tags
from backend.llm.factory import get_llm_provider

LOGGER = logging.getLogger(__name__)


async def call_ai_cleanup(raw_note: str) -> CleanedIdea:
    provider = get_llm_provider()
    LOGGER.debug(
        "Running LLM cleanup with %s (%s)", provider.display_name, provider.provider_key
    )
    return await provider.cleanup(raw_note)


__all__ = [
    "CleanedIdea",
    "LlmError",
    "call_ai_cleanup",
    "ensure_default_tags",
    "get_llm_provider",
]
