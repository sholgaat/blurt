import pytest

from bot.shared.backend_client import BackendConnectionError, BackendResponseError
from bot.shared.idea_service import submit_idea
from tests.conftest import FakeBackend


@pytest.mark.asyncio
async def test_submit_idea_success():
    backend = FakeBackend({"title": "Hello", "url": "http://example.com"})
    reply = await submit_idea(backend, text="text", user_id="1", source="discord")
    assert reply == "Created issue: **Hello**\nhttp://example.com"


@pytest.mark.asyncio
async def test_submit_idea_backend_connection_error():
    backend = FakeBackend(BackendConnectionError("down"))
    reply = await submit_idea(backend, text="text", user_id="1", source="discord")
    assert "reach the backend" in reply


@pytest.mark.asyncio
async def test_submit_idea_backend_response_error():
    backend = FakeBackend(BackendResponseError("bad"))
    reply = await submit_idea(backend, text="text", user_id="1", source="discord")
    assert "log that idea" in reply


@pytest.mark.asyncio
async def test_submit_idea_missing_title_uses_untitled():
    backend = FakeBackend({"url": "http://example.com"})
    reply = await submit_idea(backend, text="text", user_id="1", source="discord")
    assert "**Untitled**" in reply


@pytest.mark.asyncio
async def test_submit_idea_missing_url_uses_placeholder():
    backend = FakeBackend({"title": "Hello"})
    reply = await submit_idea(backend, text="text", user_id="1", source="discord")
    assert "(no URL returned)" in reply
