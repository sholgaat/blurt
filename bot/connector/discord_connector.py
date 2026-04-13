from __future__ import annotations

import logging

import discord

from bot.connector.bot_connector import BotConnector, MessageEnvelope

logger = logging.getLogger(__name__)


class DiscordConnector(BotConnector):
    @classmethod
    def validate_config(cls, cfg) -> None:
        if not cfg.discord_bot_token:
            raise RuntimeError("DISCORD_BOT_TOKEN is not set in the environment.")
        if not cfg.discord_allowed_user_ids:
            raise RuntimeError(
                "DISCORD_ALLOWED_USER_IDS is not set in the environment. "
                "Provide a comma-separated list of Discord user IDs that are allowed to submit ideas."
            )
        if not cfg.discord_idea_channel_id:
            logger.warning(
                "DISCORD_IDEA_CHANNEL_ID is not set. The bot will only respond to Direct Messages. Set DISCORD_IDEA_CHANNEL_ID to also accept ideas from a guild channel."
            )

    def __init__(self, token: str, *, idea_channel_id: str = ""):
        super().__init__()
        self._token = token
        self._idea_channel_id = idea_channel_id

        intents = discord.Intents.default()
        intents.message_content = True
        self._client = discord.Client(intents=intents)
        self._client.event(self.on_ready)
        self._client.event(self.on_message)

    def start(self) -> None:
        if not self._token:
            raise RuntimeError("DISCORD_BOT_TOKEN is not set in the environment.")
        self._client.run(self._token)

    def stop(self) -> None:
        loop = self._client.loop
        if loop and loop.is_running():
            loop.create_task(self._client.close())

    async def on_ready(self) -> None:
        logger.info(
            "Discord bot is running... try sending it a message to see it in action!"
        )

    async def on_message(self, message: discord.Message) -> None:
        if self._client.user and message.author == self._client.user:
            return
        if not self._should_process_message(message):
            return

        envelope = MessageEnvelope(
            user_id=str(message.author.id),
            text=message.content or "",
            reply=message.reply,
        )

        if self._message_handler is None:
            return
        await self._message_handler(envelope)

    def _should_process_message(self, message: discord.Message) -> bool:
        if isinstance(message.channel, discord.DMChannel):
            return True
        if not self._idea_channel_id:
            return False
        return str(message.channel.id) == self._idea_channel_id
