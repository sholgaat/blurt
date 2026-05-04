from __future__ import annotations

import openai

from blurt.backend.llm.base import BaseLlmProvider, CleanedIdea, LlmError, SYSTEM_INSTRUCTION
from blurt.backend.llm._logging import log_token_usage
from blurt.backend.settings import get_backend_settings


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

            log_token_usage(self, response)
            return parsed
        except LlmError:
            raise
        except Exception as exc:
            raise LlmError(f"{self.display_name} client call failed") from exc

    def get_input_tokens(self, response) -> int | None:
        """Extract input token count from OpenAI response."""
        usage = getattr(response, "usage", None)
        if not usage:
            return None
        return getattr(usage, "prompt_tokens", None)

    def get_output_tokens(self, response) -> int | None:
        """Extract output token count from OpenAI response."""
        usage = getattr(response, "usage", None)
        if not usage:
            return None
        return getattr(usage, "completion_tokens", None)

    def get_total_tokens(self, response) -> int | None:
        """Extract total token count from OpenAI response."""
        usage = getattr(response, "usage", None)
        if not usage:
            return None
        return getattr(usage, "total_tokens", None)
