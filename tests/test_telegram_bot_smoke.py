import pytest

from bot.telegram import main as telegram_main
from bot.shared.backend_client import IdeaBackendClient
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


class DummyApplication:
    def __init__(
        self,
        backend_client: IdeaBackendClient | None,
        allowed_user_ids: set[int] | None = None,
    ):
        self.bot_data: dict = {}
        if backend_client is not None:
            self.bot_data["backend_client"] = backend_client
        if allowed_user_ids is not None:
            self.bot_data["allowed_user_ids"] = allowed_user_ids


class DummyContext:
    def __init__(
        self,
        backend_client: IdeaBackendClient,
        allowed_user_ids: set[int] | None = None,
    ):
        self.application = DummyApplication(
            backend_client,
            allowed_user_ids=allowed_user_ids or set(),
        )


class DummyUpdate:
    def __init__(self, message: DummyMessage | None, user: DummyUser | None):
        self.message = message
        self.effective_user = user


@pytest.mark.asyncio
async def test_handle_message_calls_backend_and_replies():
    backend = DummyBackend()
    update = DummyUpdate(DummyMessage("An idea"), DummyUser(42))
    context = DummyContext(backend, allowed_user_ids={42})

    await telegram_main.handle_message(update, context)

    assert backend.called_with == ("An idea", "42", "telegram")
    assert update.message.replies == ["💡 Created issue: Test Idea\nhttp://example.com/idea"]


@pytest.mark.asyncio
async def test_handle_message_returns_early_when_no_message():
    backend = DummyBackend()
    update = DummyUpdate(None, DummyUser(42))
    context = DummyContext(backend, allowed_user_ids={42})

    await telegram_main.handle_message(update, context)

    # Backend should not be called
    assert backend.called_with is None


@pytest.mark.asyncio
async def test_handle_message_returns_early_when_no_user():
    backend = DummyBackend()
    update = DummyUpdate(DummyMessage("An idea"), None)
    context = DummyContext(backend, allowed_user_ids={42})

    await telegram_main.handle_message(update, context)

    # Backend should not be called
    assert backend.called_with is None


def test_build_application_wires_backend_client():
    backend = DummyBackend()
    application = telegram_main.build_application(
        token="TEST", backend_client=backend, allowed_user_ids={42}
    )

    assert application.bot_data["backend_client"] is backend
    assert application.bot_data["allowed_user_ids"] == {42}


@pytest.mark.asyncio
async def test_handle_message_backend_connection_error():
    """Test that BackendConnectionError is handled gracefully."""
    backend = BackendRaisesConnectionError()
    update = DummyUpdate(DummyMessage("An idea"), DummyUser(42))
    context = DummyContext(backend, allowed_user_ids={42})

    await telegram_main.handle_message(update, context)

    assert update.message.replies == ["Sorry, I couldn't reach the backend right now."]


@pytest.mark.asyncio
async def test_handle_message_backend_response_error():
    """Test that BackendResponseError is handled gracefully."""
    backend = BackendRaisesResponseError()
    update = DummyUpdate(DummyMessage("An idea"), DummyUser(42))
    context = DummyContext(backend, allowed_user_ids={42})

    await telegram_main.handle_message(update, context)

    assert update.message.replies == ["Sorry, I couldn't log that idea (backend error)."]


@pytest.mark.asyncio
async def test_on_startup_starts_backend_client():
    """Test that _on_startup initializes the backend client."""
    backend = DummyBackend()
    backend.start_called = False

    # Override start method to track if it's called
    async def track_start():
        backend.start_called = True

    backend.start = track_start

    application = DummyApplication(backend, allowed_user_ids={42})
    await telegram_main._on_startup(application)

    assert backend.start_called is True


@pytest.mark.asyncio
async def test_on_startup_with_no_backend_client():
    """Test that _on_startup handles missing backend client gracefully."""
    application = DummyApplication(backend_client=None)

    # Should not raise an exception
    await telegram_main._on_startup(application)


@pytest.mark.asyncio
async def test_on_shutdown_closes_backend_client():
    """Test that _on_shutdown closes the backend client."""
    backend = DummyBackend()
    backend.close_called = False

    # Override close method to track if it's called
    async def track_close():
        backend.close_called = True

    backend.close = track_close

    application = DummyApplication(backend, allowed_user_ids={42})
    await telegram_main._on_shutdown(application)

    assert backend.close_called is True


@pytest.mark.asyncio
async def test_on_shutdown_with_no_backend_client():
    """Test that _on_shutdown handles missing backend client gracefully."""
    application = DummyApplication(backend_client=None)

    # Should not raise an exception
    await telegram_main._on_shutdown(application)


@pytest.mark.asyncio
async def test_handle_message_blocks_unapproved_user():
    backend = DummyBackend()
    update = DummyUpdate(DummyMessage("Idea text"), DummyUser(999))
    context = DummyContext(backend, allowed_user_ids={42})

    await telegram_main.handle_message(update, context)

    assert backend.called_with is None
    assert update.message.replies == ["Sorry, this bot is restricted to approved users."]
