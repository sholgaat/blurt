import httpx
import pytest

from bot.shared.backend_client import (
    BackendConnectionError,
    BackendResponseError,
    IdeaBackendClient,
)


@pytest.mark.asyncio
async def test_create_idea_success(monkeypatch):
    backend = IdeaBackendClient("http://example.com")

    async def fake_post(path, json, timeout):
        assert path == "/ideas"
        assert json["text"] == "hello"
        return httpx.Response(200, json={"title": "T"})

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
        return httpx.Response(500, json={"error": "nope"})

    backend.http_client = httpx.AsyncClient(base_url=backend.base_url)
    monkeypatch.setattr(backend.http_client, "post", fake_post)

    with pytest.raises(BackendResponseError):
        await backend.create_idea("hello", "u1", "telegram")

    await backend.http_client.aclose()


@pytest.mark.asyncio
async def test_start_and_close_create_http_client():
    backend = IdeaBackendClient("http://example.com")
    await backend.start()
    assert backend.http_client is not None
    await backend.close()
    assert backend.http_client is None
