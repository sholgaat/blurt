from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_int_set(value: object) -> set[int]:
    """Coerce a comma-separated string or other input into a set of ints."""
    if isinstance(value, set):
        return value
    if isinstance(value, (list, tuple, frozenset)):
        return {int(v) for v in value if str(v).strip()}
    if isinstance(value, int):
        return {value}
    if isinstance(value, str):
        parts = value.split(",")
        return {int(p.strip()) for p in parts if p.strip()}
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
    discord_allowed_user_ids: set[int] = Field(default_factory=set)
    discord_idea_channel_id: int | None = None

    # Telegram
    telegram_bot_token: str = ""
    telegram_allowed_user_ids: set[int] = Field(default_factory=set)

    @field_validator("discord_allowed_user_ids", "telegram_allowed_user_ids", mode="before")
    @classmethod
    def _parse_id_set(cls, v: object) -> set[int]:
        return _parse_int_set(v)


@lru_cache(maxsize=1)
def get_bot_settings() -> BotSettings:
    return BotSettings()
