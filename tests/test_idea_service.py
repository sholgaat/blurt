import pytest

from bot.backend_client import (
    BackendConnectionError,
    BackendResponseError,
    BackendTimeoutError,
)
from bot.idea_service import summarise_idea
from tests.conftest import FakeBackend


@pytest.mark.asyncio
async def test_submit_idea_success():
    backend = FakeBackend({"title": "Hello", "url": "http://example.com"})
    reply = await summarise_idea(backend, text="text", user_id="1", source="discord")
    assert reply == "Idea captured — Hello\n\n\n\nhttp://example.com"


@pytest.mark.asyncio
async def test_submit_idea_backend_connection_error():
    backend = FakeBackend(BackendConnectionError("down"))
    reply = await summarise_idea(backend, text="text", user_id="1", source="discord")
    assert "reach the backend" in reply


@pytest.mark.asyncio
async def test_submit_idea_backend_response_error():
    backend = FakeBackend(BackendResponseError("bad"))
    reply = await summarise_idea(backend, text="text", user_id="1", source="discord")
    assert "went wrong" in reply


@pytest.mark.asyncio
async def test_submit_idea_backend_timeout_error():
    backend = FakeBackend(BackendTimeoutError("slow"))
    reply = await summarise_idea(backend, text="text", user_id="1", source="discord")
    assert "longer than expected" in reply


@pytest.mark.asyncio
async def test_submit_idea_missing_title_uses_untitled():
    backend = FakeBackend({"url": "http://example.com"})
    reply = await summarise_idea(backend, text="text", user_id="1", source="discord")
    assert "Untitled" in reply


@pytest.mark.asyncio
async def test_submit_idea_missing_url_uses_placeholder():
    backend = FakeBackend({"title": "Hello"})
    reply = await summarise_idea(backend, text="text", user_id="1", source="discord")
    assert "(no URL returned)" in reply


@pytest.mark.asyncio
async def test_submit_idea_includes_summary_and_tags():
    backend = FakeBackend(
        {
            "title": "Hello",
            "url": "http://example.com",
            "summary": "A short summary.",
            "tags": ["design", "ux"],
        }
    )
    reply = await summarise_idea(backend, text="text", user_id="1", source="discord")
    assert "A short summary." in reply
    assert "design · ux" in reply
