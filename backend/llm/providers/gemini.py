from __future__ import annotations

import asyncio
import json
import logging

from google import genai
from google.genai import types
from pydantic import ValidationError

from backend.llm.base import (
    BaseLlmProvider,
    CleanedIdea,
    LlmError,
    RESPONSE_SCHEMA,
    SYSTEM_INSTRUCTION,
)
from backend.settings import get_backend_settings

LOGGER = logging.getLogger(__name__)


class GeminiLlmProvider(BaseLlmProvider):
    provider_key = "gemini"
    display_name = "Gemini"
    default_model_name = "gemini-2.5-flash-lite"

    def __init__(self, model_name: str | None = None) -> None:
        super().__init__(model_name=model_name)
        self._client = self._create_client()

    def _create_client(self) -> genai.Client:
        api_key = get_backend_settings().gemini_api_key
        if not api_key:
            raise LlmError(f"{self.display_name} API key is not configured.")
        return genai.Client(api_key=api_key)

    async def cleanup(self, raw_note: str) -> CleanedIdea:
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=RESPONSE_SCHEMA,
        )

        def _invoke_model() -> types.GenerateContentResponse:
            return self._client.models.generate_content(
                model=self.model_name,
                contents=f"TEXT:\n{raw_note}",
                config=config,
            )

        try:
            response = await asyncio.to_thread(_invoke_model)
            response_text = response.text or ""
            if not response_text.strip():
                raise LlmError(f"{self.display_name} returned an empty response.")

            usage = getattr(response, "usage_metadata", None)
            if usage:
                LOGGER.info(
                    "%s usage - prompt: %s tokens, completion: %s tokens, total: %s tokens",
                    self.display_name,
                    getattr(usage, "prompt_token_count", "?"),
                    getattr(usage, "candidates_token_count", "?"),
                    getattr(usage, "total_token_count", "?"),
                )

            parsed = json.loads(response_text)
            return CleanedIdea.model_validate(parsed)
        except (json.JSONDecodeError, ValidationError) as exc:
            LOGGER.warning("%s returned invalid structured output", self.display_name)
            raise LlmError(
                f"{self.display_name} returned invalid structured output."
            ) from exc
        except LlmError:
            LOGGER.warning("%s returned invalid structured output", self.display_name)
            raise
        except Exception as exc:
            LOGGER.exception("%s client call failed: %s", self.display_name, exc)
            raise LlmError(f"{self.display_name} client call failed") from exc
