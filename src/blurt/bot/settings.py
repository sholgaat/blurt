from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env.bot",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_provider: str = "telegram"
    backend_url: str = "http://localhost:8000"
    idea_creation_timeout: int = 30

    # Allowed user IDs in format "platform:id" (e.g. ["discord:123456", "telegram:789012"])
    allowed_user_ids: set[str] = Field(default_factory=set)

    # Discord
    discord_bot_token: str = ""
    # Optional Discord channel IDs where the bot listens. If empty, DM-only mode.
    # If set, bot listens to DMs AND these channels.
    # Format: comma-separated or JSON array of numeric channel IDs
    discord_channel_ids: set[int] = Field(default_factory=set)

    # Telegram
    telegram_bot_token: str = ""


@lru_cache(maxsize=1)
def get_bot_settings() -> BotSettings:
    return BotSettings()
