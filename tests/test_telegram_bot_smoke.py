import asyncio
from types import SimpleNamespace

import pytest

from bot.connector.telegram_connector import TelegramConnector
from bot.backend_client import BackendConnectionError, BackendResponseError
from bot.connector.bot_connector import MessageEnvelope
from bot.idea_handler import IdeaHandler
from bot.idea_service import MAX_IDEA_LENGTH
from tests.conftest import FakeBackend


class DummyConversation:
    def __init__(self, user_id: str, text: str, *, expected_replies: int = 2):
        self.user_id = user_id
        self.text = text
        self.expected_replies = expected_replies
        self.replies: list[str] = []
        self.done = asyncio.Event()

    async def reply(self, text: str) -> None:
        self.replies.append(text)
        if len(self.replies) >= self.expected_replies:
            self.done.set()


def _make_handler(
    backend: FakeBackend, allowed_user_ids: set[str] | None = None
) -> IdeaHandler:
    return IdeaHandler(
        backend_client=backend,
        allowed_user_ids=allowed_user_ids or {"42"},
        source="telegram",
        backend_timeout=30,
    )


def test_validate_config_raises_when_token_missing():
    with pytest.raises(RuntimeError, match="TELEGRAM_BOT_TOKEN"):
        TelegramConnector.validate_config(
            SimpleNamespace(
                telegram_bot_token="",
                telegram_allowed_user_ids={"42"},
            )
        )


def test_validate_config_raises_when_allowed_users_missing():
    with pytest.raises(RuntimeError, match="TELEGRAM_ALLOWED_USER_IDS"):
        TelegramConnector.validate_config(
            SimpleNamespace(
                telegram_bot_token="token",
                telegram_allowed_user_ids=set(),
            )
        )


@pytest.mark.asyncio
async def test_handle_message_calls_backend_and_replies():
    backend = FakeBackend()
    handler = _make_handler(backend)
    conversation = DummyConversation("42", "An idea")

    await handler.handle_message(
        MessageEnvelope(
            user_id=conversation.user_id,
            text=conversation.text,
            reply=conversation.reply,
        )
    )

    assert conversation.replies == [
        "📝 Got it, processing your idea...",
        "Idea captured — Test Idea\n\nA test idea summary.\n\nTags: test · idea\n\nhttp://example.com/idea",
    ]
    assert backend.called_with == ("An idea", "42", "telegram")


@pytest.mark.asyncio
async def test_handle_message_returns_early_when_user_is_not_allowed():
    backend = FakeBackend()
    handler = _make_handler(backend, allowed_user_ids={"42"})
    conversation = DummyConversation("999", "An idea", expected_replies=1)

    await handler.handle_message(
        MessageEnvelope(
            user_id=conversation.user_id,
            text=conversation.text,
            reply=conversation.reply,
        )
    )

    assert backend.called_with is None
    assert conversation.replies == [
        "This bot is private — you're not on the approved list. Ask the owner to add your user ID: 999"
    ]


@pytest.mark.asyncio
async def test_handle_message_returns_early_when_no_message():
    backend = FakeBackend()
    handler = _make_handler(backend)
    conversation = DummyConversation("42", "   ", expected_replies=1)

    await handler.handle_message(
        MessageEnvelope(
            user_id=conversation.user_id,
            text=conversation.text,
            reply=conversation.reply,
        )
    )

    assert backend.called_with is None
    assert conversation.replies == ["Send me your idea as a message and I'll log it."]


@pytest.mark.asyncio
async def test_handle_message_returns_early_when_message_is_too_long():
    backend = FakeBackend()
    handler = _make_handler(backend)
    conversation = DummyConversation("42", "x" * 4097, expected_replies=1)

    await handler.handle_message(
        MessageEnvelope(
            user_id=conversation.user_id,
            text=conversation.text,
            reply=conversation.reply,
        )
    )

    assert backend.called_with is None
    assert conversation.replies == [
        f"That message is too long (max {MAX_IDEA_LENGTH} characters). Try summarising it a bit."
    ]


@pytest.mark.asyncio
async def test_handle_message_backend_connection_error():
    backend = FakeBackend(BackendConnectionError("down"))
    handler = _make_handler(backend)
    conversation = DummyConversation("42", "An idea")

    await handler.handle_message(
        MessageEnvelope(
            user_id=conversation.user_id,
            text=conversation.text,
            reply=conversation.reply,
        )
    )
    await conversation.done.wait()

    assert conversation.replies == [
        "📝 Got it, processing your idea...",
        "Couldn't reach the backend right now — please try again shortly.",
    ]


@pytest.mark.asyncio
async def test_handle_message_backend_response_error():
    backend = FakeBackend(BackendResponseError("bad"))
    handler = _make_handler(backend)
    conversation = DummyConversation("42", "An idea")

    await handler.handle_message(
        MessageEnvelope(
            user_id=conversation.user_id,
            text=conversation.text,
            reply=conversation.reply,
        )
    )
    await conversation.done.wait()

    assert conversation.replies == [
        "📝 Got it, processing your idea...",
        "Something went wrong saving that idea — please try again.",
    ]
