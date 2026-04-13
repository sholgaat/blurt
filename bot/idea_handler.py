from __future__ import annotations

import asyncio
import logging

from bot.backend_client import IdeaBackendClient
from bot.connector.bot_connector import MessageEnvelope
from bot.idea_service import (
    EMPTY_IDEA_MSG,
    MAX_IDEA_LENGTH,
    TOO_LONG_IDEA_MSG,
    summarise_idea,
)

logger = logging.getLogger(__name__)

ACK_MESSAGE = "📝 Got it, processing your idea..."
UNAUTHORIZED_MESSAGE = (
    "This bot is private — you're not on the approved list. "
    "Ask the owner to add your user ID: {user_id}"
)


class IdeaHandler:
    def __init__(
        self,
        *,
        backend_client: IdeaBackendClient,
        allowed_user_ids: set[str],
        source: str,
        backend_timeout: int = 30,
    ):
        self.backend_client = backend_client
        self.allowed_user_ids = allowed_user_ids
        self.source = source
        self.backend_timeout = backend_timeout

    async def handle_message(self, message: MessageEnvelope) -> None:
        if not await self.is_user_allowed(message):
            return

        if not await self.is_message_valid_length(message):
            return

        if not await self.acknowledge_idea_received(message):
            return

        try:
            reply = await summarise_idea(
                self.backend_client,
                text=message.text,
                user_id=message.user_id,
                source=self.source,
                timeout=self.backend_timeout,
            )
        except Exception:
            logger.exception("Failed to summarise idea for user_id=%s", message.user_id)
            reply = "Something went wrong processing that idea — please try again."
        await message.reply(reply)

    async def is_user_allowed(self, message: MessageEnvelope) -> bool:
        if message.user_id in self.allowed_user_ids:
            return True
        await self._safe_reply(
            message,
            UNAUTHORIZED_MESSAGE.format(user_id=message.user_id),
            log_prefix="unauthorized message",
        )
        return False

    async def is_message_valid_length(self, message: MessageEnvelope) -> bool:
        message_text = message.text or ""
        if not message_text.strip():
            await self._safe_reply(message, EMPTY_IDEA_MSG, log_prefix="empty message")
            return False
        if len(message_text) > MAX_IDEA_LENGTH:
            await self._safe_reply(
                message, TOO_LONG_IDEA_MSG, log_prefix="too long message"
            )
            return False
        return True

    async def acknowledge_idea_received(self, message: MessageEnvelope) -> bool:
        return await self._safe_reply(message, ACK_MESSAGE, log_prefix="ack message")

    async def _safe_reply(
        self,
        message: MessageEnvelope,
        text: str,
        *,
        log_prefix: str,
    ) -> bool:
        try:
            await message.reply(text)
            return True
        except Exception:
            logger.exception(
                "Failed to send %s for user_id=%s", log_prefix, message.user_id
            )
            return False
