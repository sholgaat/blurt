from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_str_set(value: object) -> set[str]:
    """Coerce a comma-separated string or other input into a set of strings."""
    if isinstance(value, set):
        return {str(v).strip() for v in value if str(v).strip()}
    if isinstance(value, (list, tuple, frozenset)):
        return {str(v).strip() for v in value if str(v).strip()}
    if isinstance(value, int):
        return {str(value)}
    if isinstance(value, str):
        parts = value.split(",")
        return {p.strip() for p in parts if p.strip()}
    return set()


class BotSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env.bot",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_provider: str = "telegram"
    backend_url: str = "http://localhost:8000"

    # Discord
    discord_bot_token: str = ""
    discord_allowed_user_ids: set[str] = Field(default_factory=set)
    discord_idea_channel_id: str = ""

    # Telegram
    telegram_bot_token: str = ""
    telegram_allowed_user_ids: set[str] = Field(default_factory=set)

    @field_validator(
        "discord_allowed_user_ids", "telegram_allowed_user_ids", mode="before"
    )
    @classmethod
    def _parse_id_set(cls, v: object) -> set[str]:
        return _parse_str_set(v)


@lru_cache(maxsize=1)
def get_bot_settings() -> BotSettings:
    return BotSettings()
