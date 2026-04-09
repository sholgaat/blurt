import pytest

from bot.telegram.main import handle_message
from bot.shared.idea_service import MAX_IDEA_LENGTH
from bot.shared.backend_client import BackendConnectionError, BackendResponseError
from tests.conftest import FakeBackend


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
    backend = FakeBackend()
    update = DummyUpdate(DummyMessage("An idea"), DummyUser(42))

    await handle_message(backend, {"42"}, update, None)

    assert backend.called_with == ("An idea", "42", "telegram")
    assert update.message.replies == [
        "Idea captured — Test Idea\n\nA test idea summary.\n\nTags: test · idea\n\nhttp://example.com/idea"
    ]


@pytest.mark.asyncio
async def test_handle_message_returns_early_when_no_message():
    backend = FakeBackend()
    update = DummyUpdate(None, DummyUser(42))

    await handle_message(backend, {"42"}, update, None)

    assert backend.called_with is None


@pytest.mark.asyncio
async def test_handle_message_returns_early_when_no_user():
    backend = FakeBackend()
    update = DummyUpdate(DummyMessage("An idea"), None)

    await handle_message(backend, {"42"}, update, None)

    assert backend.called_with is None


@pytest.mark.asyncio
async def test_handle_message_backend_connection_error():
    backend = FakeBackend(BackendConnectionError("down"))
    update = DummyUpdate(DummyMessage("An idea"), DummyUser(42))

    await handle_message(backend, {"42"}, update, None)

    assert update.message.replies == ["Couldn't reach the backend right now — please try again shortly."]


@pytest.mark.asyncio
async def test_handle_message_backend_response_error():
    backend = FakeBackend(BackendResponseError("bad"))
    update = DummyUpdate(DummyMessage("An idea"), DummyUser(42))

    await handle_message(backend, {"42"}, update, None)

    assert update.message.replies == ["Something went wrong saving that idea — please try again."]


@pytest.mark.asyncio
async def test_handle_message_blocks_unapproved_user():
    backend = FakeBackend()
    update = DummyUpdate(DummyMessage("Idea text"), DummyUser(999))

    await handle_message(backend, {"42"}, update, None)

    assert backend.called_with is None
    assert update.message.replies == [
        "This bot is private — you're not on the approved list. "
        "Ask the owner to add your user ID: 999"
    ]


@pytest.mark.asyncio
async def test_handle_message_rejects_empty_message():
    backend = FakeBackend()
    update = DummyUpdate(DummyMessage("   "), DummyUser(42))

    await handle_message(backend, {"42"}, update, None)

    assert backend.called_with is None
    assert update.message.replies == ["Send me your idea as a message and I'll log it."]


@pytest.mark.asyncio
async def test_handle_message_rejects_too_long_message():
    backend = FakeBackend()
    update = DummyUpdate(DummyMessage("x" * 4097), DummyUser(42))

    await handle_message(backend, {"42"}, update, None)

    assert backend.called_with is None
    assert update.message.replies == [
        f"That message is too long (max {MAX_IDEA_LENGTH} characters). Try summarising it a bit."
    ]


@pytest.mark.asyncio
async def test_handle_message_accepts_message_at_max_length():
    backend = FakeBackend()
    update = DummyUpdate(DummyMessage("x" * 4096), DummyUser(42))

    await handle_message(backend, {"42"}, update, None)

    assert backend.called_with is not None
