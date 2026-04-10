from __future__ import annotations

import asyncio
import inspect
import json
import logging
from typing import Any

from pydantic import TypeAdapter, ValidationError

from backend.llm.base import BaseLlmProvider, CleanedIdea, LlmError, SYSTEM_INSTRUCTION
from backend.settings import get_backend_settings

LOGGER = logging.getLogger(__name__)


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
            messages_client = self._client.messages
            parse_method = getattr(messages_client, "parse", None)

            if callable(parse_method):
                return await self._cleanup_with_parse(parse_method, raw_note)

            return await self._cleanup_with_json_schema(messages_client, raw_note)
        except LlmError:
            LOGGER.warning("%s returned invalid structured output", self.display_name)
            raise
        except Exception as exc:
            LOGGER.exception("%s client call failed: %s", self.display_name, exc)
            raise LlmError(f"{self.display_name} client call failed") from exc

    async def _cleanup_with_parse(self, parse_method, raw_note: str) -> CleanedIdea:
        try:
            response = await self._call_with_async_safety(
                parse_method,
                max_tokens=1024,
                model=self.model_name,
                system=SYSTEM_INSTRUCTION,
                messages=[{"role": "user", "content": f"TEXT:\n{raw_note}"}],
                output_format=CleanedIdea,
            )
        except TypeError:
            return await self._cleanup_with_json_schema(self._client.messages, raw_note)

        parsed = getattr(response, "parsed_output", None)
        if parsed is None:
            raise LlmError(f"{self.display_name} returned an empty response.")

        usage = getattr(response, "usage", None)
        if usage:
            total = getattr(usage, "total_tokens", "?")
            if total == "?":
                input_tokens = getattr(usage, "input_tokens", 0) or 0
                output_tokens = getattr(usage, "output_tokens", 0) or 0
                total = input_tokens + output_tokens

            LOGGER.info(
                "%s usage - prompt: %s tokens, completion: %s tokens, total: %s tokens",
                self.display_name,
                getattr(usage, "input_tokens", "?"),
                getattr(usage, "output_tokens", "?"),
                total,
            )

        try:
            return CleanedIdea.model_validate(parsed)
        except ValidationError as exc:
            raise LlmError(f"{self.display_name} returned invalid structured output.") from exc

    async def _cleanup_with_json_schema(self, messages_client, raw_note: str) -> CleanedIdea:
        adapter = TypeAdapter(CleanedIdea)
        schema = adapter.json_schema()

        transformed_schema = schema
        try:
            from anthropic.lib._parse._transform import transform_schema

            transformed_schema = transform_schema(schema)
        except Exception:
            LOGGER.debug("Using untransformed JSON schema for %s fallback", self.display_name)

        response = await self._call_with_async_safety(
            messages_client.create,
            max_tokens=1024,
            model=self.model_name,
            system=SYSTEM_INSTRUCTION,
            messages=[{"role": "user", "content": f"TEXT:\n{raw_note}"}],
            output_config={
                "format": {
                    "type": "json_schema",
                    "schema": transformed_schema,
                }
            },
        )

        response_text = self._extract_text_response(response)
        if not response_text.strip():
            raise LlmError(f"{self.display_name} returned an empty response.")

        usage = getattr(response, "usage", None)
        if usage:
            total = getattr(usage, "total_tokens", "?")
            if total == "?":
                input_tokens = getattr(usage, "input_tokens", 0) or 0
                output_tokens = getattr(usage, "output_tokens", 0) or 0
                total = input_tokens + output_tokens

            LOGGER.info(
                "%s usage - prompt: %s tokens, completion: %s tokens, total: %s tokens",
                self.display_name,
                getattr(usage, "input_tokens", "?"),
                getattr(usage, "output_tokens", "?"),
                total,
            )

        try:
            parsed = json.loads(response_text)
            return CleanedIdea.model_validate(parsed)
        except (json.JSONDecodeError, ValidationError) as exc:
            raise LlmError(f"{self.display_name} returned invalid structured output.") from exc

    async def _call_with_async_safety(self, method, **kwargs):
        if inspect.iscoroutinefunction(method):
            return await method(**kwargs)
        return await asyncio.to_thread(method, **kwargs)

    def _extract_text_response(self, response: Any) -> str:
        content = getattr(response, "content", None)
        if not content:
            return ""

        text_parts: list[str] = []
        for block in content:
            if getattr(block, "type", "") != "text":
                continue
            text_value = getattr(block, "text", "")
            if text_value:
                text_parts.append(text_value)

        return "\n".join(text_parts)
