from __future__ import annotations

import logging
from functools import lru_cache

from backend.llm.base import BaseLlmProvider, LlmError
from backend.llm.providers.gemini import GeminiLlmProvider
from backend.settings import get_backend_settings

LOGGER = logging.getLogger(__name__)

_PROVIDER_REGISTRY: dict[str, type[BaseLlmProvider]] = {
    GeminiLlmProvider.provider_key: GeminiLlmProvider,
}


@lru_cache(maxsize=1)
def get_llm_provider() -> BaseLlmProvider:
    settings = get_backend_settings()
    provider_key = settings.llm_provider.strip().lower()

    provider_cls = _PROVIDER_REGISTRY.get(provider_key)
    if provider_cls is None:
        raise LlmError(f"Unsupported LLM provider: {provider_key!r}")

    provider = provider_cls()
    LOGGER.info(
        "Selected LLM provider %s (%s) with model %s",
        provider.display_name,
        provider.provider_key,
        provider.model_name,
    )
    return provider
