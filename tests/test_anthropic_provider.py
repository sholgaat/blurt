from __future__ import annotations

import asyncio
import types

import pytest

from backend.llm.base import CleanedIdea, LlmError


class FakeAnthropicMessages:
    def __init__(self, parsed_output=None, text_response: str | None = None):
        self._parsed_output = parsed_output
        self._text_response = text_response or ""
        self.parse_kwargs = None
        self.create_kwargs = None

    async def parse(self, **kwargs):
        self.parse_kwargs = kwargs
        return types.SimpleNamespace(
            parsed_output=self._parsed_output,
            usage=types.SimpleNamespace(input_tokens=11, output_tokens=7),
        )

    async def create(self, **kwargs):
        self.create_kwargs = kwargs
        return types.SimpleNamespace(
            content=[types.SimpleNamespace(type="text", text=self._text_response)],
            usage=types.SimpleNamespace(input_tokens=13, output_tokens=9),
        )


class FakeAnthropicClient:
    def __init__(self, parsed_output=None, text_response: str | None = None):
        self.messages = FakeAnthropicMessages(
            parsed_output=parsed_output,
            text_response=text_response,
        )


def test_anthropic_cleanup_returns_normalized_idea():
    from backend.llm.providers.anthropic import AnthropicLlmProvider

    response = CleanedIdea(
        title="Build notes",
        summary="Short summary",
        tags=["Dev", "DevOps"],
    )
    provider = AnthropicLlmProvider(client=FakeAnthropicClient(response))
    result = asyncio.run(provider.cleanup("some raw idea"))

    assert result == CleanedIdea(
        title="Build notes",
        summary="Short summary",
        tags=["dev", "devops"],
    )
    assert provider._client.messages.parse_kwargs == {
        "max_tokens": 1024,
        "model": "claude-haiku-4-5",
        "system": "Extract a short descriptive title, a clear concise summary, and 2-7 relevant tags from the user text.",
        "messages": [{"role": "user", "content": "TEXT:\nsome raw idea"}],
        "output_format": CleanedIdea,
    }


def test_anthropic_cleanup_requires_api_key(monkeypatch):
    from backend.llm.providers.anthropic import AnthropicLlmProvider

    monkeypatch.setattr(
        "backend.llm.providers.anthropic.get_backend_settings",
        lambda: type("Cfg", (), {"anthropic_api_key": ""})(),
    )

    with pytest.raises(LlmError, match="Anthropic API key is not configured"):
        AnthropicLlmProvider()


def test_anthropic_cleanup_falls_back_to_json_schema_output_config():
    from backend.llm.providers.anthropic import AnthropicLlmProvider

    text_response = (
        '{"title": "  Build notes  ", "summary": " Short summary ", '
        '"tags": ["Dev", "DevOps", "Dev"]}'
    )
    provider = AnthropicLlmProvider(client=FakeAnthropicClient(text_response=text_response))
    provider._client.messages.parse = None

    result = asyncio.run(provider.cleanup("some raw idea"))

    assert result == CleanedIdea(
        title="Build notes",
        summary="Short summary",
        tags=["dev", "devops"],
    )
    kwargs = provider._client.messages.create_kwargs
    assert kwargs["model"] == "claude-haiku-4-5"
    assert kwargs["messages"] == [{"role": "user", "content": "TEXT:\nsome raw idea"}]
    assert kwargs["output_config"]["format"]["type"] == "json_schema"
    assert "schema" in kwargs["output_config"]["format"]


def test_factory_selects_anthropic_provider(monkeypatch):
    import backend.llm.factory as factory_module

    class FakeProvider:
        provider_key = "anthropic"

        def __init__(self):
            self.display_name = "Anthropic"
            self.provider_key = "anthropic"
            self.model_name = "claude-haiku-4-5"

    factory_module.get_llm_provider.cache_clear()

    monkeypatch.setattr(
        factory_module,
        "get_backend_settings",
        lambda: type("Cfg", (), {"llm_provider": "anthropic"})(),
    )
    monkeypatch.setitem(factory_module._PROVIDER_REGISTRY, "anthropic", FakeProvider)

    provider = factory_module.get_llm_provider()

    assert isinstance(provider, FakeProvider)
    factory_module.get_llm_provider.cache_clear()
