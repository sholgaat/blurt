from __future__ import annotations

import asyncio
import types as pytypes

import pytest

from blurt.backend.llm.base import CleanedIdea, LlmError


class FakeGeminiAioModels:
    def __init__(self, response=None, exc: Exception | None = None):
        self._response = response
        self._exc = exc
        self.kwargs = None

    async def generate_content(self, **kwargs):
        self.kwargs = kwargs
        if self._exc:
            raise self._exc
        return self._response


class FakeGeminiClient:
    def __init__(self, response=None, exc: Exception | None = None):
        self.aio = pytypes.SimpleNamespace(
            models=FakeGeminiAioModels(response=response, exc=exc)
        )


def _response(text: str | None, parsed=None):
    return pytypes.SimpleNamespace(
        text=text,
        parsed=parsed,
        usage_metadata=pytypes.SimpleNamespace(
            prompt_token_count=11,
            candidates_token_count=7,
            total_token_count=18,
        ),
    )


def test_gemini_cleanup_returns_normalized_idea():
    from blurt.backend.llm.providers.gemini import GeminiLlmProvider

    provider = GeminiLlmProvider(
        client=FakeGeminiClient(
            response=_response(
                '{"title": " Build notes ", "summary": " Short summary ", '
                '"tags": ["Dev", "DevOps", "Dev"]}',
                parsed={
                    "title": " Build notes ",
                    "summary": " Short summary ",
                    "tags": ["Dev", "DevOps", "Dev"],
                },
            )
        )
    )

    result = asyncio.run(provider.cleanup("some raw idea"))

    assert result == CleanedIdea(
        title="Build notes",
        summary="Short summary",
        tags=["dev", "devops"],
    )
    kwargs = provider._client.aio.models.kwargs
    assert kwargs["model"] == "gemini-2.5-flash-lite"
    assert kwargs["contents"] == "TEXT:\nsome raw idea"
    assert kwargs["config"].system_instruction
    assert kwargs["config"].response_mime_type == "application/json"
    assert kwargs["config"].response_schema is CleanedIdea


def test_gemini_cleanup_requires_api_key(monkeypatch):
    from blurt.backend.llm.providers.gemini import GeminiLlmProvider

    monkeypatch.setattr(
        "blurt.backend.llm.providers.gemini.get_backend_settings",
        lambda: type("Cfg", (), {"gemini_api_key": ""})(),
    )

    with pytest.raises(LlmError, match="Gemini API key is not configured"):
        GeminiLlmProvider()


def test_gemini_cleanup_rejects_empty_response():
    from blurt.backend.llm.providers.gemini import GeminiLlmProvider

    provider = GeminiLlmProvider(client=FakeGeminiClient(response=_response("   ")))

    with pytest.raises(LlmError, match="Gemini returned an empty response"):
        asyncio.run(provider.cleanup("some raw idea"))


def test_gemini_cleanup_rejects_invalid_json():
    from blurt.backend.llm.providers.gemini import GeminiLlmProvider

    provider = GeminiLlmProvider(client=FakeGeminiClient(response=_response("not json")))

    with pytest.raises(LlmError, match="Gemini returned invalid structured output"):
        asyncio.run(provider.cleanup("some raw idea"))


def test_gemini_cleanup_rejects_invalid_schema():
    from blurt.backend.llm.providers.gemini import GeminiLlmProvider

    provider = GeminiLlmProvider(
        client=FakeGeminiClient(
            response=_response('{"title": "   ", "summary": "y", "tags": ["dev"]}')
        )
    )

    with pytest.raises(LlmError, match="Gemini returned invalid structured output"):
        asyncio.run(provider.cleanup("some raw idea"))


def test_factory_selects_gemini_provider(monkeypatch):
    import blurt.backend.llm.factory as factory_module

    class FakeProvider:
        provider_key = "gemini"

        def __init__(self):
            self.display_name = "Gemini"
            self.provider_key = "gemini"
            self.model_name = "gemini-2.5-flash-lite"

    factory_module.get_llm_provider.cache_clear()

    monkeypatch.setattr(
        factory_module,
        "get_backend_settings",
        lambda: type("Cfg", (), {"llm_provider": "gemini"})(),
    )
    monkeypatch.setitem(factory_module._PROVIDER_REGISTRY, "gemini", FakeProvider)

    provider = factory_module.get_llm_provider()

    assert isinstance(provider, FakeProvider)
    factory_module.get_llm_provider.cache_clear()
