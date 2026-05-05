from __future__ import annotations

import asyncio
import types

import pytest

from blurt.backend.llm.base import CleanedIdea, LlmError


class FakeAnthropicMessages:
    def __init__(self, parsed_output=None):
        self._parsed_output = parsed_output
        self.parse_kwargs = None

    async def parse(self, **kwargs):
        self.parse_kwargs = kwargs
        return types.SimpleNamespace(
            parsed_output=self._parsed_output,
            usage=types.SimpleNamespace(input_tokens=11, output_tokens=7),
        )


class FakeAnthropicClient:
    def __init__(self, parsed_output=None):
        self.messages = FakeAnthropicMessages(parsed_output=parsed_output)


def test_anthropic_cleanup_returns_normalized_idea():
    from blurt.backend.llm.providers.anthropic import AnthropicLlmProvider

    response = CleanedIdea(
        title="Build notes",
        summary="Short summary",
        tags=["Dev", "DevOps"],
    )
    provider = AnthropicLlmProvider(model_name="claude-haiku-4-5", client=FakeAnthropicClient(response))
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


def test_anthropic_uses_configured_model(monkeypatch):
    from blurt.backend.llm.providers.anthropic import AnthropicLlmProvider

    monkeypatch.setattr(
        "blurt.backend.llm.providers.anthropic.get_backend_settings",
        lambda: type("Cfg", (), {
            "anthropic_api_key": "key",
            "anthropic_model": "custom-model-789"
        })(),
    )

    response = CleanedIdea(title="t", summary="s", tags=["tag"])
    provider = AnthropicLlmProvider(client=FakeAnthropicClient(response))
    assert provider.model_name == "custom-model-789"


def test_anthropic_uses_explicit_model_name_override(monkeypatch):
    from blurt.backend.llm.providers.anthropic import AnthropicLlmProvider

    monkeypatch.setattr(
        "blurt.backend.llm.providers.anthropic.get_backend_settings",
        lambda: type("Cfg", (), {
            "anthropic_api_key": "key",
            "anthropic_model": "settings-model"
        })(),
    )

    response = CleanedIdea(title="t", summary="s", tags=["tag"])
    provider = AnthropicLlmProvider(model_name="override-model", client=FakeAnthropicClient(response))
    assert provider.model_name == "override-model"


def test_anthropic_throws_without_configured_model(monkeypatch):
    from blurt.backend.llm.providers.anthropic import AnthropicLlmProvider

    monkeypatch.setattr(
        "blurt.backend.llm.providers.anthropic.get_backend_settings",
        lambda: type("Cfg", (), {
            "anthropic_api_key": "key",
            "anthropic_model": ""
        })(),
    )

    with pytest.raises(LlmError, match="Anthropic model is not configured"):
        AnthropicLlmProvider()


def test_anthropic_cleanup_requires_api_key(monkeypatch):
    from blurt.backend.llm.providers.anthropic import AnthropicLlmProvider

    monkeypatch.setattr(
        "blurt.backend.llm.providers.anthropic.get_backend_settings",
        lambda: type("Cfg", (), {
            "anthropic_api_key": "",
            "anthropic_model": "claude-haiku-4-5"
        })(),
    )

    with pytest.raises(LlmError, match="Anthropic API key is not configured"):
        AnthropicLlmProvider()


def test_factory_selects_anthropic_provider(monkeypatch):
    import blurt.backend.llm.factory as factory_module

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
