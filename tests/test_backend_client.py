import httpx
import pytest

from bot.shared.backend_client import (
    BackendConnectionError,
    BackendResponseError,
    BackendTimeoutError,
    IdeaBackendClient,
)

_FAKE_REQUEST = httpx.Request("POST", "http://example.com/ideas")


@pytest.mark.asyncio
async def test_create_idea_success(monkeypatch):
    backend = IdeaBackendClient("http://example.com")

    async def fake_post(path, json, timeout):
        assert path == "/ideas"
        assert json["text"] == "hello"
        return httpx.Response(200, json={"title": "T"}, request=_FAKE_REQUEST)

    backend.http_client = httpx.AsyncClient(base_url=backend.base_url)
    monkeypatch.setattr(backend.http_client, "post", fake_post)

    result = await backend.create_idea("hello", "u1", "telegram")
    assert result == {"title": "T"}

    await backend.http_client.aclose()


@pytest.mark.asyncio
async def test_create_idea_raises_connection_error(monkeypatch):
    backend = IdeaBackendClient("http://example.com")

    async def fake_post(*args, **kwargs):
        raise httpx.HTTPError("boom")

    backend.http_client = httpx.AsyncClient(base_url=backend.base_url)
    monkeypatch.setattr(backend.http_client, "post", fake_post)

    with pytest.raises(BackendConnectionError):
        await backend.create_idea("hello", "u1", "telegram")

    await backend.http_client.aclose()


@pytest.mark.asyncio
async def test_create_idea_raises_response_error(monkeypatch):
    backend = IdeaBackendClient("http://example.com")

    async def fake_post(*args, **kwargs):
        return httpx.Response(500, json={"error": "nope"}, request=_FAKE_REQUEST)

    backend.http_client = httpx.AsyncClient(base_url=backend.base_url)
    monkeypatch.setattr(backend.http_client, "post", fake_post)

    with pytest.raises(BackendResponseError):
        await backend.create_idea("hello", "u1", "telegram")

    await backend.http_client.aclose()


@pytest.mark.asyncio
async def test_create_idea_raises_timeout_error(monkeypatch):
    backend = IdeaBackendClient("http://example.com")

    async def fake_post(*args, **kwargs):
        raise httpx.TimeoutException("slow")

    backend.http_client = httpx.AsyncClient(base_url=backend.base_url)
    monkeypatch.setattr(backend.http_client, "post", fake_post)

    with pytest.raises(BackendTimeoutError):
        await backend.create_idea("hello", "u1", "telegram")

    await backend.http_client.aclose()


@pytest.mark.asyncio
async def test_start_and_close_create_http_client():
    backend = IdeaBackendClient("http://example.com")
    await backend.start()
    assert backend.http_client is not None
    await backend.close()
    assert backend.http_client is None


@pytest.mark.asyncio
async def test_create_idea_auto_starts_client(monkeypatch):
    backend = IdeaBackendClient("http://example.com")
    assert backend.http_client is None

    async def fake_post(path, json, timeout):
        return httpx.Response(200, json={"title": "T"}, request=_FAKE_REQUEST)

    # Patch start to create client, then patch the client's post method
    original_start = backend.start

    async def patched_start():
        await original_start()
        monkeypatch.setattr(backend.http_client, "post", fake_post)

    monkeypatch.setattr(backend, "start", patched_start)

    result = await backend.create_idea("hello", "u1", "telegram")
    assert result == {"title": "T"}
    assert backend.http_client is not None

    await backend.close()
