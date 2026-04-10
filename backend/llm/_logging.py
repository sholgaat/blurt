from __future__ import annotations

import logging
from typing import Any

from backend.llm.base import BaseLlmProvider

LOGGER = logging.getLogger(__name__)


def log_token_usage(provider: BaseLlmProvider, response: Any) -> None:
    """Log token usage for a provider response.
    
    Each provider's get_*_tokens methods normalize their response
    structure, returning either an int or None. This function
    formats them for logging, using "?" for unavailable values.
    """
    input_tokens = provider.get_input_tokens(response) or "?"
    output_tokens = provider.get_output_tokens(response) or "?"
    total_tokens = provider.get_total_tokens(response) or "?"

    LOGGER.info(
        "%s usage - prompt: %s tokens, completion: %s tokens, total: %s tokens",
        provider.display_name,
        input_tokens,
        output_tokens,
        total_tokens,
    )
