from __future__ import annotations

from backend.llm.base import BaseLlmProvider, CleanedIdea, LlmError, SYSTEM_INSTRUCTION
from backend.llm._logging import log_token_usage
from backend.settings import get_backend_settings


class AnthropicLlmProvider(BaseLlmProvider):
    provider_key = "anthropic"
    display_name = "Anthropic"
    default_model_name = "claude-haiku-4-5"

    def __init__(
        self,
        model_name: str | None = None,
        client: object | None = None,
    ) -> None:
        super().__init__(model_name=model_name)
        self._client = client or self._create_client()

    def _create_client(self):
        api_key = get_backend_settings().anthropic_api_key
        if not api_key:
            raise LlmError(f"{self.display_name} API key is not configured.")

        try:
            import anthropic
        except ImportError as exc:
            raise LlmError(f"{self.display_name} SDK is not installed.") from exc

        return anthropic.AsyncAnthropic(api_key=api_key)

    async def cleanup(self, raw_note: str) -> CleanedIdea:
        try:
            response = await self._client.messages.parse(
                max_tokens=1024,
                model=self.model_name,
                system=SYSTEM_INSTRUCTION,
                messages=[{"role": "user", "content": f"TEXT:\n{raw_note}"}],
                output_format=CleanedIdea,
            )

            parsed = getattr(response, "parsed_output", None)
            if parsed is None:
                raise LlmError(f"{self.display_name} returned an empty response.")

            log_token_usage(self, response)
            return parsed
        except LlmError:
            raise
        except Exception as exc:
            raise LlmError(f"{self.display_name} client call failed") from exc

    def get_input_tokens(self, response) -> int | None:
        """Extract input token count from Anthropic response."""
        usage = getattr(response, "usage", None)
        if not usage:
            return None
        return getattr(usage, "input_tokens", None)

    def get_output_tokens(self, response) -> int | None:
        """Extract output token count from Anthropic response."""
        usage = getattr(response, "usage", None)
        if not usage:
            return None
        return getattr(usage, "output_tokens", None)

    def get_total_tokens(self, response) -> int | None:
        """Extract or derive total token count from Anthropic response."""
        usage = getattr(response, "usage", None)
        if not usage:
            return None

        return getattr(usage, "total_tokens", None)
