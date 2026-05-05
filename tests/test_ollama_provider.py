from __future__ import annotations

import asyncio
import json

import pytest

from blurt.backend.llm.base import CleanedIdea, LlmError


class FakeResponseError(Exception):
    def __init__(self, error: str):
        super().__init__(error)
        self.error = error


class FakeOllamaClient:
    def __init__(self, response=None, exc: Exception | None = None):
        self._response = response
        self._exc = exc
        self.kwargs = None

    async def generate(self, **kwargs):
        self.kwargs = kwargs
        if self._exc:
            raise self._exc
        return self._response


def test_ollama_cleanup_returns_normalized_idea():
    from blurt.backend.llm.providers.ollama import OllamaLlmProvider

    response = {
        "response": json.dumps(
            {
                "title": " Build notes ",
                "summary": " Short summary ",
                "tags": ["Dev", "DevOps", "Dev"],
            }
        ),
        "prompt_eval_count": 11,
        "eval_count": 7,
    }
    provider = OllamaLlmProvider(model_name="llama3.2", client=FakeOllamaClient(response=response))
    result = asyncio.run(provider.cleanup("some raw idea"))

    assert result == CleanedIdea(
        title="Build notes",
        summary="Short summary",
        tags=["dev", "devops"],
    )
    assert provider._client.kwargs["model"] == "llama3.2"
    assert provider._client.kwargs["format"] == CleanedIdea.model_json_schema()
    assert "TEXT:\nsome raw idea" in provider._client.kwargs["prompt"]
    assert "Respond using JSON." in provider._client.kwargs["prompt"]


def test_ollama_cleanup_rejects_empty_response():
    from blurt.backend.llm.providers.ollama import OllamaLlmProvider

    provider = OllamaLlmProvider(
        model_name="llama3.2",
        client=FakeOllamaClient(response={"response": "   "})
    )

    with pytest.raises(LlmError, match="Ollama returned an empty response"):
        asyncio.run(provider.cleanup("some raw idea"))


def test_ollama_cleanup_reports_model_not_found():
    from blurt.backend.llm.providers.ollama import OllamaLlmProvider

    provider = OllamaLlmProvider(
        model_name="llama3.2",
        client=FakeOllamaClient(exc=FakeResponseError("not found"))
    )
    provider._response_error_cls = FakeResponseError

    with pytest.raises(LlmError, match="could not be found"):
        asyncio.run(provider.cleanup("some raw idea"))


def test_ollama_cleanup_reports_timeout():
    from blurt.backend.llm.providers.ollama import OllamaLlmProvider

    provider = OllamaLlmProvider(
        model_name="llama3.2",
        client=FakeOllamaClient(exc=TimeoutError("timeout"))
    )

    with pytest.raises(LlmError, match="timed out"):
        asyncio.run(provider.cleanup("some raw idea"))


def test_ollama_cleanup_reports_connection_error():
    from blurt.backend.llm.providers.ollama import OllamaLlmProvider

    provider = OllamaLlmProvider(
        model_name="llama3.2",
        client=FakeOllamaClient(exc=ConnectionError("connection refused"))
    )

    with pytest.raises(LlmError, match="could not be reached"):
        asyncio.run(provider.cleanup("some raw idea"))


def test_factory_selects_ollama_provider(monkeypatch):
    import blurt.backend.llm.factory as factory_module

    class FakeProvider:
        provider_key = "ollama"

        def __init__(self):
            self.display_name = "Ollama"
            self.provider_key = "ollama"
            self.model_name = "llama3.2"

    factory_module.get_llm_provider.cache_clear()

    monkeypatch.setattr(
        factory_module,
        "get_backend_settings",
        lambda: type("Cfg", (), {"llm_provider": "ollama"})(),
    )
    monkeypatch.setitem(factory_module._PROVIDER_REGISTRY, "ollama", FakeProvider)

    provider = factory_module.get_llm_provider()

    assert isinstance(provider, FakeProvider)
    factory_module.get_llm_provider.cache_clear()
