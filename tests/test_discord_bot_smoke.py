import asyncio
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import discord
import pytest

from bot.connectors.discord_connector import DiscordConnector


_ALLOWED_USER_ID = 111
_OTHER_USER_ID = 999
_IDEA_CHANNEL_ID = 42


def _make_connector(*, idea_channel_id: int | None = None) -> DiscordConnector:
    return DiscordConnector(
        "token",
        idea_channel_id=str(idea_channel_id) if idea_channel_id is not None else "",
    )


def _patch_connector_user(connector: DiscordConnector, user: MagicMock):
    return patch.object(
        type(connector._client), "user", new_callable=PropertyMock, return_value=user
    )


def _make_message(
    content: str = "An idea",
    *,
    author_id: int = _ALLOWED_USER_ID,
    channel_type: str = "dm",
    channel_id: int = _IDEA_CHANNEL_ID,
) -> tuple:
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


@pytest.mark.asyncio
async def test_dm_from_allowed_user_is_dispatched():
    connector = _make_connector()
    handler = AsyncMock()
    connector.register_message_handler(handler)
    message, _ = _make_message("My idea", author_id=_ALLOWED_USER_ID)

    with _patch_connector_user(connector, MagicMock()):
        await connector._normalise_message(message)

    assert handler.await_count == 1
    envelope = handler.await_args.args[0]
    assert envelope.user_id == str(_ALLOWED_USER_ID)
    assert envelope.text == "My idea"


@pytest.mark.asyncio
async def test_dm_from_blocked_user_still_dispatches_to_handler():
    connector = _make_connector()
    handler = AsyncMock()
    connector.register_message_handler(handler)
    message, _ = _make_message(author_id=_OTHER_USER_ID)

    with _patch_connector_user(connector, MagicMock()):
        await connector._normalise_message(message)

    assert handler.await_count == 1
    assert handler.await_args.args[0].user_id == str(_OTHER_USER_ID)


@pytest.mark.asyncio
async def test_bot_ignores_own_messages():
    connector = _make_connector()
    handler = AsyncMock()
    connector.register_message_handler(handler)
    message, author = _make_message(author_id=_ALLOWED_USER_ID)

    with _patch_connector_user(connector, author):
        await connector._normalise_message(message)

    handler.assert_not_awaited()


@pytest.mark.asyncio
async def test_guild_channel_matching_id_is_dispatched():
    connector = _make_connector(idea_channel_id=_IDEA_CHANNEL_ID)
    handler = AsyncMock()
    connector.register_message_handler(handler)
    message, _ = _make_message(
        author_id=_ALLOWED_USER_ID, channel_type="text", channel_id=_IDEA_CHANNEL_ID
    )

    with _patch_connector_user(connector, MagicMock()):
        await connector._normalise_message(message)

    assert handler.await_count == 1


@pytest.mark.asyncio
async def test_guild_channel_non_matching_id_is_ignored():
    connector = _make_connector(idea_channel_id=_IDEA_CHANNEL_ID)
    handler = AsyncMock()
    connector.register_message_handler(handler)
    message, _ = _make_message(
        author_id=_ALLOWED_USER_ID, channel_type="text", channel_id=999_999
    )

    with _patch_connector_user(connector, MagicMock()):
        await connector._normalise_message(message)

    handler.assert_not_awaited()


@pytest.mark.asyncio
async def test_guild_message_ignored_when_no_channel_id_configured():
    connector = _make_connector(idea_channel_id=None)
    handler = AsyncMock()
    connector.register_message_handler(handler)
    message, _ = _make_message(
        author_id=_ALLOWED_USER_ID, channel_type="text", channel_id=_IDEA_CHANNEL_ID
    )

    with _patch_connector_user(connector, MagicMock()):
        await connector._normalise_message(message)

    handler.assert_not_awaited()


@pytest.mark.asyncio
async def test_dm_still_dispatched_when_no_channel_id_configured():
    connector = _make_connector(idea_channel_id=None)
    handler = AsyncMock()
    connector.register_message_handler(handler)
    message, _ = _make_message(author_id=_ALLOWED_USER_ID)

    with _patch_connector_user(connector, MagicMock()):
        await connector._normalise_message(message)

    assert handler.await_count == 1
