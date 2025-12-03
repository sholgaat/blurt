from __future__ import annotations

import logging
from typing import Optional

import discord
import httpx
from discord import Message

from bot.config import BACKEND_URL, DISCORD_TOKEN

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IdeaInboxBot(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.http_client: Optional[httpx.AsyncClient] = None

    async def setup_hook(self) -> None:
        self.http_client = httpx.AsyncClient(base_url=BACKEND_URL)

    async def close(self) -> None:
        if self.http_client:
            await self.http_client.aclose()
        await super().close()

    async def on_ready(self) -> None:
        logger.info("Discord bot is running...")

    async def on_message(self, message: Message) -> None:
        if message.author == self.user:
            return

        if not self._should_process_message(message):
            return

        if not self.http_client:
            logger.error("HTTP client not initialized; cannot send idea.")
            return

        payload = {
            "text": message.content or "",
            "user_id": str(message.author.id),
            "source": "discord",
        }

        try:
            response = await self.http_client.post("/ideas", json=payload, timeout=15.0)
        except httpx.HTTPError:
            await message.reply("Sorry, I couldn't reach the backend right now.")
            return

        if response.status_code != 200:
            await message.reply("Sorry, I couldn't log that idea (backend error).")
            return

        data = response.json()
        title = data.get("title", "Untitled")
        url = data.get("url", BACKEND_URL)
        await message.reply(f"💡 Logged: **{title}**\n{url}")

    @staticmethod
    def _should_process_message(message: Message) -> bool:
        if isinstance(message.channel, discord.DMChannel):
            return True

        channel = getattr(message, "channel", None)
        channel_name = getattr(channel, "name", "")
        return channel_name == "idea-inbox"


def main() -> None:
    if not DISCORD_TOKEN:
        raise RuntimeError("DISCORD_TOKEN is not set in the environment.")

    intents = discord.Intents.default()
    intents.message_content = True

    client = IdeaInboxBot(intents=intents)
    client.run(DISCORD_TOKEN)


if __name__ == "__main__":
    main()
