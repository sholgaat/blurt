import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import discord
import pytest

from blurt.bot.connector.discord_connector import DiscordConnector


_ALLOWED_USER_ID = 111
_OTHER_USER_ID = 999


def _make_connector() -> DiscordConnector:
    handler = AsyncMock()
    return DiscordConnector("token", handler)


def _patch_connector_user(connector: DiscordConnector, user: MagicMock):
    return patch.object(
        type(connector._client), "user", new_callable=PropertyMock, return_value=user
    )


def _make_message(
    content: str = "An idea",
    *,
    author_id: int = _ALLOWED_USER_ID,
    channel_type: str = "dm",
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
    message.channel = channel
    message.reply = AsyncMock()

    return message, author


@pytest.mark.asyncio
async def test_dm_from_allowed_user_is_dispatched():
    connector = _make_connector()
    message, _ = _make_message("My idea", author_id=_ALLOWED_USER_ID)

    with _patch_connector_user(connector, MagicMock()):
        await connector.on_message(message)

    assert connector._message_handler.await_count == 1
    envelope = connector._message_handler.await_args.args[0]
    assert envelope.user_id == str(_ALLOWED_USER_ID)
    assert envelope.text == "My idea"


@pytest.mark.asyncio
async def test_dm_from_blocked_user_still_dispatches_to_handler():
    connector = _make_connector()
    message, _ = _make_message(author_id=_OTHER_USER_ID)

    with _patch_connector_user(connector, MagicMock()):
        await connector.on_message(message)

    assert connector._message_handler.await_count == 1
    assert connector._message_handler.await_args.args[0].user_id == str(_OTHER_USER_ID)


@pytest.mark.asyncio
async def test_bot_ignores_own_messages():
    connector = _make_connector()
    message, author = _make_message(author_id=_ALLOWED_USER_ID)

    with _patch_connector_user(connector, author):
        await connector.on_message(message)

    connector._message_handler.assert_not_awaited()


@pytest.mark.asyncio
async def test_guild_message_is_dispatched():
    """Guild messages are accepted from any channel — auth is handled downstream."""
    connector = _make_connector()
    message, _ = _make_message(author_id=_ALLOWED_USER_ID, channel_type="text")

    with _patch_connector_user(connector, MagicMock()):
        await connector.on_message(message)

    assert connector._message_handler.await_count == 1
