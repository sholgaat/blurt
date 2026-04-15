from __future__ import annotations

import logging

import discord

from bot.connector.bot_connector import BotConnector, MessageEnvelope, MessageHandler

logger = logging.getLogger(__name__)


class DiscordConnector(BotConnector):
    def __init__(self, token: str, handler: MessageHandler, *, idea_channel_id: str = ""):
        super().__init__(handler)
        if not token:
            raise RuntimeError("DISCORD_BOT_TOKEN is required.")
        self._token = token
        self._idea_channel_id = idea_channel_id

        intents = discord.Intents.default()
        intents.message_content = True
        self._client = discord.Client(intents=intents)
        self._client.event(self.on_ready)
        self._client.event(self.on_message)

    def start(self) -> None:
        self._client.run(self._token)

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

        await self._message_handler(envelope)

    def _should_process_message(self, message: discord.Message) -> bool:
        """
        Platform-level filtering: determine if this Discord message should be routed
        to the application handler based on channel/DM constraints.
        
        This is distinct from app-level auth (allowed user IDs), which is handled by
        IdeaHandler. The connector's job is to filter based on platform routing rules:
        - DMs are always accepted
        - Guild messages are only accepted if a specific channel ID is configured and matches
        """
        if isinstance(message.channel, discord.DMChannel):
            return True
        if not self._idea_channel_id:
            return False
        return str(message.channel.id) == self._idea_channel_id
