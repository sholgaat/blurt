import logging
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import discord
import pytest

from bot.discord.main import IdeaInboxBot
from bot.shared.backend_client import (
    BackendConnectionError,
    BackendResponseError,
    IdeaBackendClient,
)
from tests.conftest import FakeBackend

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_ALLOWED_USER_ID = 111
_OTHER_USER_ID = 999
_IDEA_CHANNEL_ID = 42


# ---------------------------------------------------------------------------
# Mock helpers
# ---------------------------------------------------------------------------


def _make_bot(
    backend: IdeaBackendClient,
    *,
    allowed_user_ids: set[int] | None = None,
    idea_channel_id: int | None = None,
) -> IdeaInboxBot:
    if allowed_user_ids is None:
        allowed_user_ids = {_ALLOWED_USER_ID}
    intents = discord.Intents.none()
    return IdeaInboxBot(
        intents=intents,
        backend_client=backend,
        allowed_user_ids=allowed_user_ids,
        idea_channel_id=idea_channel_id,
    )


def _patch_bot_user(bot: IdeaInboxBot, user: MagicMock):
    """Patch the read-only discord.Client.user property for testing."""
    return patch.object(type(bot), "user", new_callable=PropertyMock, return_value=user)


def _make_message(
    content: str = "An idea",
    *,
    author_id: int = _ALLOWED_USER_ID,
    channel_type: str = "dm",
    channel_id: int = _IDEA_CHANNEL_ID,
) -> tuple:
    """Build a minimal discord.Message-like mock pair (message, author)."""
    message = MagicMock(spec=discord.Message)
    message.content = content

    author = MagicMock()
    author.id = author_id
    message.author = author

    if channel_type == "dm":
        channel = MagicMock(spec=discord.DMChannel)
    else:
        channel = MagicMock(spec=discord.TextChannel)
        channel.id = channel_id
    message.channel = channel
    message.reply = AsyncMock()

    return message, author


def _make_dm_message(content: str = "An idea", *, author_id: int = _ALLOWED_USER_ID) -> tuple:
    return _make_message(content, author_id=author_id, channel_type="dm")


def _make_guild_message(
    content: str = "An idea",
    *,
    author_id: int = _ALLOWED_USER_ID,
    channel_id: int = _IDEA_CHANNEL_ID,
) -> tuple:
    return _make_message(
        content, author_id=author_id, channel_type="text", channel_id=channel_id
    )


# Sentinel: a distinct object that will NOT equal any message author.
_DIFFERENT_USER = MagicMock()


# ---------------------------------------------------------------------------
# Tests: DM processing
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dm_from_allowed_user_is_processed():
    backend = FakeBackend()
    bot = _make_bot(backend)
    message, _ = _make_dm_message("My idea", author_id=_ALLOWED_USER_ID)

    with _patch_bot_user(bot, _DIFFERENT_USER):
        await bot.on_message(message)

    assert backend.called_with == ("My idea", str(_ALLOWED_USER_ID), "discord")
    message.reply.assert_awaited_once()
    reply_text = message.reply.call_args[0][0]
    assert "Test Idea" in reply_text
    assert "http://example.com/idea" in reply_text


# ---------------------------------------------------------------------------
# Tests: Allowlist blocking
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dm_from_blocked_user_is_rejected():
    backend = FakeBackend()
    bot = _make_bot(backend, allowed_user_ids={_ALLOWED_USER_ID})
    message, _ = _make_dm_message(author_id=_OTHER_USER_ID)

    with _patch_bot_user(bot, _DIFFERENT_USER):
        await bot.on_message(message)

    assert backend.called_with is None
    message.reply.assert_awaited_once()
    assert "private" in message.reply.call_args[0][0].lower()


# ---------------------------------------------------------------------------
# Tests: Bot ignores its own messages
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_bot_ignores_own_messages():
    backend = FakeBackend()
    bot = _make_bot(backend)
    message, author = _make_dm_message(author_id=_ALLOWED_USER_ID)

    # bot.user IS the author -> should be ignored
    with _patch_bot_user(bot, author):
        await bot.on_message(message)

    assert backend.called_with is None
    message.reply.assert_not_awaited()


# ---------------------------------------------------------------------------
# Tests: Channel ID filtering
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_guild_channel_matching_id_is_processed():
    backend = FakeBackend()
    bot = _make_bot(backend, idea_channel_id=_IDEA_CHANNEL_ID)
    message, _ = _make_guild_message(author_id=_ALLOWED_USER_ID, channel_id=_IDEA_CHANNEL_ID)

    with _patch_bot_user(bot, _DIFFERENT_USER):
        await bot.on_message(message)

    assert backend.called_with is not None
    assert backend.called_with[2] == "discord"


@pytest.mark.asyncio
async def test_guild_channel_non_matching_id_is_ignored():
    backend = FakeBackend()
    bot = _make_bot(backend, idea_channel_id=_IDEA_CHANNEL_ID)
    message, _ = _make_guild_message(author_id=_ALLOWED_USER_ID, channel_id=999_999)

    with _patch_bot_user(bot, _DIFFERENT_USER):
        await bot.on_message(message)

    assert backend.called_with is None
    message.reply.assert_not_awaited()


# ---------------------------------------------------------------------------
# Tests: No channel configured = DM-only
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_guild_message_ignored_when_no_channel_id_configured():
    backend = FakeBackend()
    bot = _make_bot(backend, idea_channel_id=None)
    message, _ = _make_guild_message(author_id=_ALLOWED_USER_ID, channel_id=_IDEA_CHANNEL_ID)

    with _patch_bot_user(bot, _DIFFERENT_USER):
        await bot.on_message(message)

    assert backend.called_with is None
    message.reply.assert_not_awaited()


@pytest.mark.asyncio
async def test_dm_still_processed_when_no_channel_id_configured():
    backend = FakeBackend()
    bot = _make_bot(backend, idea_channel_id=None)
    message, _ = _make_dm_message(author_id=_ALLOWED_USER_ID)

    with _patch_bot_user(bot, _DIFFERENT_USER):
        await bot.on_message(message)

    assert backend.called_with is not None


# ---------------------------------------------------------------------------
# Tests: Startup warning when no channel ID set
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_setup_hook_logs_warning_when_no_channel_id(caplog):
    backend = FakeBackend()
    backend.start = AsyncMock()
    bot = _make_bot(backend, idea_channel_id=None)

    with caplog.at_level(logging.WARNING, logger="bot.discord.main"):
        await bot.setup_hook()

    assert any("DISCORD_IDEA_CHANNEL_ID" in record.message for record in caplog.records)
    backend.start.assert_awaited_once()


@pytest.mark.asyncio
async def test_setup_hook_no_warning_when_channel_id_set(caplog):
    backend = FakeBackend()
    backend.start = AsyncMock()
    bot = _make_bot(backend, idea_channel_id=_IDEA_CHANNEL_ID)

    with caplog.at_level(logging.WARNING, logger="bot.discord.main"):
        await bot.setup_hook()

    assert not any("DISCORD_IDEA_CHANNEL_ID" in record.message for record in caplog.records)
    backend.start.assert_awaited_once()


# ---------------------------------------------------------------------------
# Tests: Backend error handling
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_backend_connection_error_replies_gracefully():
    backend = FakeBackend(BackendConnectionError("down"))
    bot = _make_bot(backend)
    message, _ = _make_dm_message(author_id=_ALLOWED_USER_ID)

    with _patch_bot_user(bot, _DIFFERENT_USER):
        await bot.on_message(message)

    message.reply.assert_awaited_once()
    assert "backend" in message.reply.call_args[0][0].lower()

@pytest.mark.asyncio
async def test_backend_response_error_replies_gracefully():
    backend = FakeBackend(BackendResponseError("bad"))
    bot = _make_bot(backend)
    message, _ = _make_dm_message(author_id=_ALLOWED_USER_ID)

    with _patch_bot_user(bot, _DIFFERENT_USER):
        await bot.on_message(message)

    message.reply.assert_awaited_once()
    assert "went wrong" in message.reply.call_args[0][0].lower()
