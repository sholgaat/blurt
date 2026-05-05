from __future__ import annotations

import asyncio
import types

import pytest

from blurt.backend.llm.base import CleanedIdea, LlmError


class FakeOpenAIClient:
    def __init__(self, parsed):
        self._parsed = parsed
        self.beta = types.SimpleNamespace(
            chat=types.SimpleNamespace(
                completions=types.SimpleNamespace(parse=self._parse)
            )
        )

    async def _parse(self, **kwargs):
        self.kwargs = kwargs
        return types.SimpleNamespace(
            choices=[
                types.SimpleNamespace(
                    message=types.SimpleNamespace(parsed=self._parsed)
                )
            ],
            usage=types.SimpleNamespace(
                prompt_tokens=11, completion_tokens=7, total_tokens=18
            ),
        )

def test_openai_cleanup_returns_normalized_idea():
    from blurt.backend.llm.providers.openai import OpenAILlmProvider

    response = CleanedIdea(
        title="Build notes",
        summary="Short summary",
        tags=["Dev", "DevOps"],
    )
    provider = OpenAILlmProvider(model_name="gpt-4o-mini", client=FakeOpenAIClient(response))
    result = asyncio.run(provider.cleanup("some raw idea"))

    assert result == CleanedIdea(
        title="Build notes",
        summary="Short summary",
        tags=["dev", "devops"],
    )
    assert provider._client.kwargs == {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "system",
                "content": "Extract a short descriptive title, a clear concise summary, and 2-7 relevant tags from the user text.",
            },
            {"role": "user", "content": "TEXT:\nsome raw idea"},
        ],
        "response_format": CleanedIdea,
    }


def test_openai_uses_configured_model(monkeypatch):
    from blurt.backend.llm.providers.openai import OpenAILlmProvider

    monkeypatch.setattr(
        "blurt.backend.llm.providers.openai.get_backend_settings",
        lambda: type("Cfg", (), {
            "openai_api_key": "key",
            "openai_model": "custom-model-456"
        })(),
    )

    response = CleanedIdea(title="t", summary="s", tags=["tag"])
    provider = OpenAILlmProvider(client=FakeOpenAIClient(response))
    assert provider.model_name == "custom-model-456"


def test_openai_uses_explicit_model_name_override(monkeypatch):
    from blurt.backend.llm.providers.openai import OpenAILlmProvider

    monkeypatch.setattr(
        "blurt.backend.llm.providers.openai.get_backend_settings",
        lambda: type("Cfg", (), {
            "openai_api_key": "key",
            "openai_model": "settings-model"
        })(),
    )

    response = CleanedIdea(title="t", summary="s", tags=["tag"])
    provider = OpenAILlmProvider(model_name="override-model", client=FakeOpenAIClient(response))
    assert provider.model_name == "override-model"


def test_openai_throws_without_configured_model(monkeypatch):
    from blurt.backend.llm.providers.openai import OpenAILlmProvider

    monkeypatch.setattr(
        "blurt.backend.llm.providers.openai.get_backend_settings",
        lambda: type("Cfg", (), {
            "openai_api_key": "key",
            "openai_model": ""
        })(),
    )

    with pytest.raises(LlmError, match="OpenAI model is not configured"):
        OpenAILlmProvider()


def test_openai_cleanup_requires_api_key(monkeypatch):
    from blurt.backend.llm.providers.openai import OpenAILlmProvider

    monkeypatch.setattr(
        "blurt.backend.llm.providers.openai.get_backend_settings",
        lambda: type("Cfg", (), {
            "openai_api_key": "",
            "openai_model": "gpt-4o-mini"
        })(),
    )

    with pytest.raises(LlmError, match="OpenAI API key is not configured"):
        OpenAILlmProvider()


def test_factory_selects_openai_provider(monkeypatch):
    import blurt.backend.llm.factory as factory_module

    class FakeProvider:
        provider_key = "openai"

        def __init__(self):
            self.display_name = "OpenAI"
            self.provider_key = "openai"
            self.model_name = "gpt-4o-mini"

    factory_module.get_llm_provider.cache_clear()

    monkeypatch.setattr(
        factory_module,
        "get_backend_settings",
        lambda: type("Cfg", (), {"llm_provider": "openai"})(),
    )
    monkeypatch.setitem(factory_module._PROVIDER_REGISTRY, "openai", FakeProvider)

    provider = factory_module.get_llm_provider()

    assert isinstance(provider, FakeProvider)
    factory_module.get_llm_provider.cache_clear()
