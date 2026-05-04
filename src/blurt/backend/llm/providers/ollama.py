from __future__ import annotations

from blurt.backend.llm.base import (
    BaseLlmProvider,
    CleanedIdea,
    LlmError,
    SYSTEM_INSTRUCTION,
)
from blurt.backend.llm._logging import log_token_usage
from blurt.backend.settings import get_backend_settings


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
            f"{SYSTEM_INSTRUCTION}\n\n" f"TEXT:\n{raw_note}\n\n" "Respond using JSON."
        )

        try:
            response = await self._client.generate(
                model=self.model_name,
                prompt=prompt,
                format=CleanedIdea.model_json_schema(),
                stream=False,
            )

            response_text = self._response_value(response, "response", "")
            if not str(response_text).strip():
                raise LlmError(f"{self.display_name} returned an empty response.")

            log_token_usage(self, response)

            return CleanedIdea.model_validate_json(response_text)
        except LlmError:
            raise
        except TimeoutError as exc:
            raise LlmError(
                f"{self.display_name} request timed out - the model {self.model_name!r} may require more time to load or respond"
            ) from exc
        except ConnectionError as exc:
            raise LlmError(
                f"{self.display_name} could not be reached at {self.api_base} - ensure it is running and the address is correct"
            ) from exc
        except self._response_error_cls as exc:
            error_msg = str(getattr(exc, "error", "") or str(exc))
            if "not found" in error_msg.lower():
                raise LlmError(
                    f"{self.display_name} model '{self.model_name}' could not be found - ensure it has been pulled"
                ) from exc
            raise LlmError(f"{self.display_name} error: {error_msg}") from exc
        except Exception as exc:
            raise LlmError(f"{self.display_name} client call failed") from exc

    def get_input_tokens(self, response) -> int | None:
        """Extract input token count from Ollama response."""
        return self._response_value(response, "prompt_eval_count", None)

    def get_output_tokens(self, response) -> int | None:
        """Extract output token count from Ollama response."""
        return self._response_value(response, "eval_count", None)

    def get_total_tokens(self, response) -> int | None:
        """Extract or derive total token count from Ollama response."""
        prompt = self.get_input_tokens(response)
        output = self.get_output_tokens(response)
        if prompt is not None and output is not None:
            return prompt + output
        return None

    @staticmethod
    def _response_value(response: object, key: str, default: object) -> object:
        if isinstance(response, dict):
            return response.get(key, default)
        return getattr(response, key, default)
