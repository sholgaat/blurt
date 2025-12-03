import pytest

from bot.telegram import main as telegram_main
from bot.shared.backend_client import (
    BackendConnectionError,
    BackendResponseError,
    IdeaBackendClient,
)

# Constants
_TEST_BACKEND_URL = "http://example.com"


class BaseMockBackend(IdeaBackendClient):
    """Base class for mock backend implementations."""

    def __init__(self):
        super().__init__(base_url=_TEST_BACKEND_URL)

    async def start(self) -> None:  # pragma: no cover - no-op for tests
        pass

    async def close(self) -> None:  # pragma: no cover - no-op for tests
        pass


class DummyBackend(BaseMockBackend):
    def __init__(self):
        super().__init__()
        self.called_with = None

    async def create_idea(self, text: str, user_id: str, source: str) -> dict:
        self.called_with = (text, user_id, source)
        return {"title": "Test Idea", "url": "http://example.com/idea"}


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
    def __init__(self, backend_client: IdeaBackendClient | None):
        if backend_client is not None:
            self.bot_data = {"backend_client": backend_client}
        else:
            self.bot_data = {}


class DummyContext:
    def __init__(self, backend_client: IdeaBackendClient):
        self.application = DummyApplication(backend_client)


class DummyUpdate:
    def __init__(self, message: DummyMessage | None, user: DummyUser | None):
        self.message = message
        self.effective_user = user


@pytest.mark.asyncio
async def test_handle_message_calls_backend_and_replies():
    backend = DummyBackend()
    update = DummyUpdate(DummyMessage("An idea"), DummyUser(42))
    context = DummyContext(backend)

    await telegram_main.handle_message(update, context)

    assert backend.called_with == ("An idea", "42", "telegram")
    assert update.message.replies == ["💡 Logged: Test Idea\nhttp://example.com/idea"]


@pytest.mark.asyncio
async def test_handle_message_returns_early_when_no_message():
    backend = DummyBackend()
    update = DummyUpdate(None, DummyUser(42))
    context = DummyContext(backend)

    await telegram_main.handle_message(update, context)

    # Backend should not be called
    assert backend.called_with is None


@pytest.mark.asyncio
async def test_handle_message_returns_early_when_no_user():
    backend = DummyBackend()
    update = DummyUpdate(DummyMessage("An idea"), None)
    context = DummyContext(backend)

    await telegram_main.handle_message(update, context)

    # Backend should not be called
    assert backend.called_with is None


def test_build_application_wires_backend_client():
    backend = DummyBackend()
    application = telegram_main.build_application(token="TEST", backend_client=backend)

    assert application.bot_data["backend_client"] is backend


class BackendRaisesConnectionError(BaseMockBackend):
    """Mock backend that raises BackendConnectionError."""

    async def create_idea(self, text: str, user_id: str, source: str) -> dict:
        raise BackendConnectionError("Failed to reach backend.")


class BackendRaisesResponseError(BaseMockBackend):
    """Mock backend that raises BackendResponseError."""

    async def create_idea(self, text: str, user_id: str, source: str) -> dict:
        raise BackendResponseError("Backend returned an error status.")


@pytest.mark.asyncio
async def test_handle_message_backend_connection_error():
    """Test that BackendConnectionError is handled gracefully."""
    backend = BackendRaisesConnectionError()
    update = DummyUpdate(DummyMessage("An idea"), DummyUser(42))
    context = DummyContext(backend)

    await telegram_main.handle_message(update, context)

    assert update.message.replies == ["Sorry, I couldn't reach the backend right now."]


@pytest.mark.asyncio
async def test_handle_message_backend_response_error():
    """Test that BackendResponseError is handled gracefully."""
    backend = BackendRaisesResponseError()
    update = DummyUpdate(DummyMessage("An idea"), DummyUser(42))
    context = DummyContext(backend)

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
    
    application = DummyApplication(backend)
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
    
    application = DummyApplication(backend)
    await telegram_main._on_shutdown(application)
    
    assert backend.close_called is True


@pytest.mark.asyncio
async def test_on_shutdown_with_no_backend_client():
    """Test that _on_shutdown handles missing backend client gracefully."""
    application = DummyApplication(backend_client=None)
    
    # Should not raise an exception
    await telegram_main._on_shutdown(application)
