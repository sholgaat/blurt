from __future__ import annotations

import json
import logging

from backend.llm.base import (
    BaseLlmProvider,
    CleanedIdea,
    LlmError,
    RESPONSE_SCHEMA,
    SYSTEM_INSTRUCTION,
)
from backend.settings import get_backend_settings

LOGGER = logging.getLogger(__name__)


class OllamaLlmProvider(BaseLlmProvider):
    provider_key = "ollama"
    display_name = "Ollama"
    default_model_name = "llama3.2"

    def __init__(
        self,
        model_name: str | None = None,
        client: object | None = None,
    ) -> None:
        settings = get_backend_settings()
        resolved_model = model_name or settings.ollama_model or self.default_model_name
        super().__init__(model_name=resolved_model)
        self.api_base = settings.ollama_api_base
        self.timeout_seconds = settings.model_timeout_seconds
        self._response_error_cls = Exception
        self._client = client or self._create_client()

    def _create_client(self):
        try:
            import ollama
        except ImportError as exc:
            raise LlmError(f"{self.display_name} SDK is not installed.") from exc

        self._response_error_cls = getattr(ollama, "ResponseError", Exception)
        return ollama.AsyncClient(
            host=self.api_base,
            timeout=self.timeout_seconds,
        )

    async def cleanup(self, raw_note: str) -> CleanedIdea:
        prompt = (
            f"{SYSTEM_INSTRUCTION}\n\n"
            f"TEXT:\n{raw_note}\n\n"
            "Respond using JSON."
        )

        try:
            response = await self._client.generate(
                model=self.model_name,
                prompt=prompt,
                format=RESPONSE_SCHEMA,
                stream=False,
            )

            response_text = self._response_value(response, "response", "")
            if not str(response_text).strip():
                raise LlmError(f"{self.display_name} returned an empty response.")

            prompt_tokens = self._response_value(response, "prompt_eval_count", "?")
            completion_tokens = self._response_value(response, "eval_count", "?")
            total_tokens = "?"
            if isinstance(prompt_tokens, int) and isinstance(completion_tokens, int):
                total_tokens = prompt_tokens + completion_tokens

            LOGGER.info(
                "%s usage - prompt: %s tokens, completion: %s tokens, total: %s tokens",
                self.display_name,
                prompt_tokens,
                completion_tokens,
                total_tokens,
            )

            parsed = json.loads(response_text)
            return CleanedIdea.model_validate(parsed)
        except LlmError:
            raise
        except Exception as exc:
            if isinstance(exc, self._response_error_cls):
                error_msg = str(getattr(exc, "error", "") or str(exc))
                if "not found" in error_msg.lower():
                    raise LlmError(
                        f"Model '{self.model_name}' could not be found - ensure it has been pulled"
                    ) from exc
                raise LlmError(f"{self.display_name} error: {error_msg}") from exc

            error_msg = str(exc).lower()
            if "timeout" in error_msg:
                raise LlmError(
                    "Ollama request timed out - the model may require more time to load or respond"
                ) from exc
            if (
                "connect" in error_msg
                or "connection" in error_msg
                or "refused" in error_msg
                or "unreachable" in error_msg
            ):
                raise LlmError(
                    f"Ollama could not be reached at {self.api_base} - ensure it is running and the address is correct"
                ) from exc

            LOGGER.exception("%s client call failed: %s", self.display_name, exc)
            raise LlmError(f"{self.display_name} client call failed") from exc

    @staticmethod
    def _response_value(response: object, key: str, default: object) -> object:
        if isinstance(response, dict):
            return response.get(key, default)
        return getattr(response, key, default)
