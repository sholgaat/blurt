from __future__ import annotations

import logging

import discord

from blurt.bot.connector.bot_connector import BotConnector, MessageEnvelope, MessageHandler

logger = logging.getLogger(__name__)


class DiscordConnector(BotConnector):
    def __init__(self, token: str, handler: MessageHandler):
        super().__init__(handler)
        if not token:
            raise RuntimeError("DISCORD_BOT_TOKEN is required.")
        self._token = token

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

        envelope = MessageEnvelope(
            user_id=str(message.author.id),
            text=message.content or "",
            reply=message.reply,
        )

        await self._message_handler(envelope)
