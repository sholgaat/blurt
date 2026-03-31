import pytest

from bot.telegram.main import handle_message
from tests.conftest import (
    DummyBackend,
    BackendRaisesConnectionError,
    BackendRaisesResponseError,
)


class DummyMessage:
    def __init__(self, text: str):
        self.text = text
        self.replies: list[str] = []

    async def reply_text(self, text: str) -> None:
        self.replies.append(text)


class DummyUser:
    def __init__(self, user_id: int):
        self.id = user_id


class DummyUpdate:
    def __init__(self, message: DummyMessage | None, user: DummyUser | None):
        self.message = message
        self.effective_user = user


@pytest.mark.asyncio
async def test_handle_message_calls_backend_and_replies():
    backend = DummyBackend()
    update = DummyUpdate(DummyMessage("An idea"), DummyUser(42))

    await handle_message(backend, {42}, update, None)

    assert backend.called_with == ("An idea", "42", "telegram")
    assert update.message.replies == ["💡 Created issue: Test Idea\nhttp://example.com/idea"]


@pytest.mark.asyncio
async def test_handle_message_returns_early_when_no_message():
    backend = DummyBackend()
    update = DummyUpdate(None, DummyUser(42))

    await handle_message(backend, {42}, update, None)

    assert backend.called_with is None


@pytest.mark.asyncio
async def test_handle_message_returns_early_when_no_user():
    backend = DummyBackend()
    update = DummyUpdate(DummyMessage("An idea"), None)

    await handle_message(backend, {42}, update, None)

    assert backend.called_with is None


@pytest.mark.asyncio
async def test_handle_message_backend_connection_error():
    backend = BackendRaisesConnectionError()
    update = DummyUpdate(DummyMessage("An idea"), DummyUser(42))

    await handle_message(backend, {42}, update, None)

    assert update.message.replies == ["Sorry, I couldn't reach the backend right now."]


@pytest.mark.asyncio
async def test_handle_message_backend_response_error():
    backend = BackendRaisesResponseError()
    update = DummyUpdate(DummyMessage("An idea"), DummyUser(42))

    await handle_message(backend, {42}, update, None)

    assert update.message.replies == ["Sorry, I couldn't log that idea (backend error)."]


@pytest.mark.asyncio
async def test_handle_message_blocks_unapproved_user():
    backend = DummyBackend()
    update = DummyUpdate(DummyMessage("Idea text"), DummyUser(999))

    await handle_message(backend, {42}, update, None)

    assert backend.called_with is None
    assert update.message.replies == ["Sorry, this bot is restricted to approved users."]
