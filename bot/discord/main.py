from __future__ import annotations

import asyncio
import logging

import discord
from discord import Message

from bot.shared.backend_client import IdeaBackendClient
from bot.shared.idea_service import (
    EMPTY_IDEA_MSG,
    MAX_IDEA_LENGTH,
    TOO_LONG_IDEA_MSG,
    submit_idea,
)
from bot.settings import get_bot_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IdeaInboxBot(discord.Client):
    def __init__(
        self,
        *,
        intents: discord.Intents,
        backend_client: IdeaBackendClient,
        allowed_user_ids: set[str],
        idea_channel_id: str,
        idea_creation_timeout: int = 30,
    ):
        super().__init__(intents=intents)
        self.backend_client = backend_client
        self.allowed_user_ids = allowed_user_ids
        self.idea_channel_id = idea_channel_id
        self.idea_creation_timeout = idea_creation_timeout

    async def setup_hook(self) -> None:
        await self.backend_client.start()
        if not self.idea_channel_id:
            logger.warning(
                "DISCORD_IDEA_CHANNEL_ID is not set. "
                "The bot will only respond to Direct Messages. "
                "Set DISCORD_IDEA_CHANNEL_ID to also accept ideas from a guild channel."
            )

    async def close(self) -> None:
        await self.backend_client.close()
        await super().close()

    async def on_ready(self) -> None:
        logger.info(
            "Discord bot is running... try sending it a message to see it in action!"
        )

    async def on_message(self, message: Message) -> None:
        if message.author == self.user:
            return

        if not self._should_process_message(message):
            return

        if str(message.author.id) not in self.allowed_user_ids:
            logger.warning(
                "Blocked message from unauthorized {user_id=%s, username=%s}",
                message.author.id,
                message.author.name,
            )
            await message.reply(
                f"This bot is private — you're not on the approved list. "
                f"Ask the owner to add your user ID: {message.author.id}"
            )
            return

        text = message.content or ""
        if not text.strip():
            await message.reply(EMPTY_IDEA_MSG)
            return
        if len(text) > MAX_IDEA_LENGTH:
            await message.reply(TOO_LONG_IDEA_MSG)
            return

        await message.reply("📝 Got it, processing your idea...")
        asyncio.create_task(
            self.process_and_send_update(
                message=message,
                text=text,
                user_id=str(message.author.id),
            )
        )

    async def process_and_send_update(
        self,
        *,
        message: Message,
        text: str,
        user_id: str,
    ) -> None:
        try:
            reply = await submit_idea(
                self.backend_client,
                text=text,
                user_id=user_id,
                source="discord",
                timeout=self.idea_creation_timeout,
            )
            await message.reply(reply)
        except Exception:
            logger.exception("Failed to process or send Discord idea update")

    def _should_process_message(self, message: Message) -> bool:
        if isinstance(message.channel, discord.DMChannel):
            return True
        if not self.idea_channel_id:
            return False
        return str(message.channel.id) == self.idea_channel_id


def main() -> None:
    cfg = get_bot_settings()

    if not cfg.discord_bot_token:
        raise RuntimeError("DISCORD_BOT_TOKEN is not set in the environment.")
    if not cfg.discord_allowed_user_ids:
        raise RuntimeError(
            "DISCORD_ALLOWED_USER_IDS is not set in the environment. "
            "Provide a comma-separated list of Discord user IDs that are allowed to submit ideas."
        )

    intents = discord.Intents.default()
    intents.message_content = True

    backend_client = IdeaBackendClient(cfg.backend_url)
    client = IdeaInboxBot(
        intents=intents,
        backend_client=backend_client,
        allowed_user_ids=cfg.discord_allowed_user_ids,
        idea_channel_id=cfg.discord_idea_channel_id,
        idea_creation_timeout=cfg.idea_creation_timeout,
    )
    client.run(cfg.discord_bot_token)


if __name__ == "__main__":
    main()
