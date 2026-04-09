from __future__ import annotations

import logging

import openai

from backend.llm.base import BaseLlmProvider, CleanedIdea, LlmError, SYSTEM_INSTRUCTION
from backend.settings import get_backend_settings

LOGGER = logging.getLogger(__name__)


class OpenAILlmProvider(BaseLlmProvider):
    provider_key = "openai"
    display_name = "OpenAI"
    default_model_name = "gpt-4o-mini"

    def __init__(
        self,
        model_name: str | None = None,
        client: object | None = None,
    ) -> None:
        super().__init__(model_name=model_name)
        self._client = client or self._create_client()

    def _create_client(self):
        api_key = get_backend_settings().openai_api_key
        if not api_key:
            raise LlmError(f"{self.display_name} API key is not configured.")
        return openai.AsyncOpenAI(api_key=api_key)

    async def cleanup(self, raw_note: str) -> CleanedIdea:
        try:
            response = await self._client.beta.chat.completions.parse(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": SYSTEM_INSTRUCTION},
                    {"role": "user", "content": f"TEXT:\n{raw_note}"},
                ],
                response_format=CleanedIdea,
            )
            choice = response.choices[0]
            parsed = choice.message.parsed
            if parsed is None:
                raise LlmError(f"{self.display_name} returned an empty response.")

            usage = getattr(response, "usage", None)
            if usage:
                LOGGER.info(
                    "%s usage - prompt: %s tokens, completion: %s tokens, total: %s tokens",
                    self.display_name,
                    getattr(usage, "prompt_tokens", "?"),
                    getattr(usage, "completion_tokens", "?"),
                    getattr(usage, "total_tokens", "?"),
                )

            return parsed
        except LlmError:
            LOGGER.warning("%s returned invalid structured output", self.display_name)
            raise
        except Exception as exc:
            LOGGER.exception("%s client call failed: %s", self.display_name, exc)
            raise LlmError(f"{self.display_name} client call failed") from exc
