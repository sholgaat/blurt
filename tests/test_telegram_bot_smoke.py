import pytest

from bot.telegram import main as telegram_main
from bot.shared.backend_client import IdeaBackendClient


class DummyBackend(IdeaBackendClient):
    def __init__(self):
        super().__init__(base_url="http://example.com")
        self.called_with = None

    async def start(self) -> None:  # pragma: no cover - no-op for tests
        return None

    async def close(self) -> None:  # pragma: no cover - no-op for tests
        return None

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
    def __init__(self, backend_client: IdeaBackendClient):
        self.bot_data = {"backend_client": backend_client}


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
