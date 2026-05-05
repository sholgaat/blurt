from __future__ import annotations

import json

from google import genai
from google.genai import types
from pydantic import ValidationError

from blurt.backend.llm.base import (
    BaseLlmProvider,
    CleanedIdea,
    LlmError,
    SYSTEM_INSTRUCTION,
)
from blurt.backend.llm._logging import log_token_usage
from blurt.backend.settings import get_backend_settings


class GeminiLlmProvider(BaseLlmProvider):
    provider_key = "gemini"
    display_name = "Gemini"

    def __init__(
        self,
        model_name: str | None = None,
        client: object | None = None,
    ) -> None:
        settings = get_backend_settings()
        resolved_model = model_name or settings.gemini_model
        if not resolved_model:
            raise LlmError(f"{self.display_name} model is not configured.")
        super().__init__(model_name=resolved_model)
        self._client = client or self._create_client()

    def _create_client(self) -> genai.Client:
        api_key = get_backend_settings().gemini_api_key
        if not api_key:
            raise LlmError(f"{self.display_name} API key is not configured.")
        return genai.Client(api_key=api_key)

    async def cleanup(self, raw_note: str) -> CleanedIdea:
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=CleanedIdea,
        )

        try:
            response = await self._client.aio.models.generate_content(
                model=self.model_name,
                contents=f"TEXT:\n{raw_note}",
                config=config,
            )
            response_text = response.text or ""
            if not response_text.strip():
                raise LlmError(f"{self.display_name} returned an empty response.")

            log_token_usage(self, response)

            parsed = getattr(response, "parsed", None)
            if parsed is None:
                parsed = json.loads(response_text)
            return CleanedIdea.model_validate(parsed)
        except (json.JSONDecodeError, ValidationError) as exc:
            raise LlmError(
                f"{self.display_name} returned invalid structured output."
            ) from exc
        except LlmError:
            raise
        except Exception as exc:
            raise LlmError(f"{self.display_name} client call failed") from exc

    def get_input_tokens(self, response) -> int | None:
        """Extract input token count from Gemini response."""
        usage = getattr(response, "usage_metadata", None)
        if not usage:
            return None
        return getattr(usage, "prompt_token_count", None)

    def get_output_tokens(self, response) -> int | None:
        """Extract output token count from Gemini response."""
        usage = getattr(response, "usage_metadata", None)
        if not usage:
            return None
        return getattr(usage, "candidates_token_count", None)

    def get_total_tokens(self, response) -> int | None:
        """Extract total token count from Gemini response."""
        usage = getattr(response, "usage_metadata", None)
        if not usage:
            return None
        return getattr(usage, "total_token_count", None)
