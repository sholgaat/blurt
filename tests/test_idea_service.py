import pytest

from bot.shared.backend_client import (
    BackendConnectionError,
    BackendResponseError,
    IdeaBackendClient,
)
from bot.shared.idea_service import format_issue_reply, submit_idea


class DummyBackend(IdeaBackendClient):
    def __init__(self, response: dict | Exception):
        super().__init__("http://example.com")
        self.response = response

    async def create_idea(self, text: str, user_id: str, source: str) -> dict:
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


@pytest.mark.asyncio
async def test_submit_idea_success():
    backend = DummyBackend({"title": "Hello", "url": "http://example.com"})
    result, error = await submit_idea(
        backend,
        text="text",
        user_id="1",
        source="discord",
    )
    assert error is None
    assert result and result.title == "Hello" and result.url == "http://example.com"
    assert format_issue_reply(result) == "💡 Created issue: Hello\nhttp://example.com"


@pytest.mark.asyncio
async def test_submit_idea_backend_connection_error():
    backend = DummyBackend(BackendConnectionError("down"))
    result, error = await submit_idea(
        backend, text="text", user_id="1", source="discord"
    )
    assert result is None
    assert "reach the backend" in error


@pytest.mark.asyncio
async def test_submit_idea_backend_response_error():
    backend = DummyBackend(BackendResponseError("bad response"))
    result, error = await submit_idea(
        backend, text="text", user_id="1", source="discord"
    )
    assert result is None
    assert "log that idea" in error


@pytest.mark.asyncio
async def test_submit_idea_missing_url_uses_placeholder():
    backend = DummyBackend({"title": "Hello"})
    result, error = await submit_idea(
        backend, text="text", user_id="1", source="discord"
    )
    assert error is None
    assert result and result.url == "(no URL returned)"


def test_format_issue_reply_bold():
    class Obj:
        title = "Title"
        url = "http://example.com"

    assert format_issue_reply(Obj(), bold_title=True) == "💡 Created issue: **Title**\nhttp://example.com"
