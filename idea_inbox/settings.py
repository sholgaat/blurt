from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Set

from dotenv import load_dotenv


@lru_cache(maxsize=1)
def _load_env() -> None:
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    else:
        load_dotenv()


def ensure_env_loaded() -> None:
    _load_env()


def _get_env(name: str, default: str | None = None) -> str | None:
    _load_env()
    value = os.getenv(name)
    if value is None:
        return default
    return value


def _parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def require_env(name: str) -> str:
    value = _get_env(name)
    if not value:
        raise ValueError(f"Environment variable {name} is required.")
    return value


def get_backend_url() -> str:
    return _get_env("BACKEND_URL", "http://localhost:8000") or "http://localhost:8000"


def get_discord_bot_token() -> str | None:
    return _get_env("DISCORD_BOT_TOKEN")


def get_telegram_bot_token() -> str | None:
    return _get_env("TELEGRAM_BOT_TOKEN")


def _parse_int_list(raw_value: str | None) -> Set[int]:
    ids: Set[int] = set()
    if not raw_value:
        return ids
    for chunk in raw_value.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        try:
            ids.add(int(chunk))
        except ValueError:
            continue
    return ids


def get_telegram_allowed_user_ids() -> Set[int]:
    return _parse_int_list(_get_env("TELEGRAM_ALLOWED_USER_IDS"))


def get_discord_allowed_user_ids() -> Set[int]:
    return _parse_int_list(_get_env("DISCORD_ALLOWED_USER_IDS"))


def get_discord_idea_channel_id() -> int | None:
    raw = _get_env("DISCORD_IDEA_CHANNEL_ID")
    if not raw or not raw.strip():
        return None
    try:
        return int(raw.strip())
    except ValueError:
        return None


def get_gemini_api_key() -> str | None:
    return _get_env("GEMINI_API_KEY")

def is_dry_run_enabled() -> bool:
    return _parse_bool(_get_env("DRY_RUN"), False)
