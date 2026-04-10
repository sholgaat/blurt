from __future__ import annotations

import logging
from typing import Any

from backend.llm.base import BaseLlmProvider

LOGGER = logging.getLogger(__name__)


def log_token_usage(provider: BaseLlmProvider, response: Any) -> None:
    """Log token usage for a provider response.
    
    Each provider's get_*_tokens methods normalize their response
    structure to this common interface.
    """
    LOGGER.info(
        "%s usage - prompt: %s tokens, completion: %s tokens, total: %s tokens",
        provider.display_name,
        provider.get_input_tokens(response),
        provider.get_output_tokens(response),
        provider.get_total_tokens(response),
    )
