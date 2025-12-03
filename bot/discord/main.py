from __future__ import annotations

import logging

import discord
from discord import Message

from bot.config import BACKEND_URL, DISCORD_TOKEN
from bot.shared.backend_client import (
    BackendConnectionError,
    BackendResponseError,
    IdeaBackendClient,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IdeaInboxBot(discord.Client):
    def __init__(self, *, intents: discord.Intents, backend_client: IdeaBackendClient):
        super().__init__(intents=intents)
        self.backend_client = backend_client

    async def setup_hook(self) -> None:
        await self.backend_client.start()

    async def close(self) -> None:
        await self.backend_client.close()
        await super().close()

    async def on_ready(self) -> None:
        logger.info("Discord bot is running...")

    async def on_message(self, message: Message) -> None:
        if message.author == self.user:
            return

        if not self._should_process_message(message):
            return

        try:
            data = await self.backend_client.create_idea(
                text=message.content or "",
                user_id=str(message.author.id),
                source="discord",
            )
        except BackendConnectionError:
            await message.reply("Sorry, I couldn't reach the backend right now.")
            return
        except BackendResponseError:
            await message.reply("Sorry, I couldn't create that idea (backend error).")
            return

        title = data.get("title", "Untitled")
        url = data.get("url", BACKEND_URL)
        await message.reply(f"💡 Created issue: **{title}**\n{url}")

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

    backend_client = IdeaBackendClient(BACKEND_URL)
    client = IdeaInboxBot(intents=intents, backend_client=backend_client)
    client.run(DISCORD_TOKEN)


if __name__ == "__main__":
    main()
