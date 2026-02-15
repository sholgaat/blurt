from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Set

from dotenv import load_dotenv

_DEFAULT_TELEGRAM_ALLOWED_IDS: Set[int] = {123456789}


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


def get_telegram_allowed_user_ids() -> Set[int]:
    raw_value = _get_env("TELEGRAM_ALLOWED_USER_IDS")
    ids: Set[int] = set()
    if raw_value:
        for chunk in raw_value.split(","):
            chunk = chunk.strip()
            if not chunk:
                continue
            try:
                ids.add(int(chunk))
            except ValueError:
                continue
    return ids or set(_DEFAULT_TELEGRAM_ALLOWED_IDS)


def get_gemini_api_key() -> str | None:
    return _get_env("GEMINI_API_KEY")


def get_github_repo_owner() -> str | None:
    return _get_env("GITHUB_REPO_OWNER")


def get_github_repo_name() -> str | None:
    return _get_env("GITHUB_REPO_NAME")


def get_github_token() -> str | None:
    return _get_env("GITHUB_TOKEN")


def is_dry_run_enabled() -> bool:
    return _parse_bool(_get_env("DRY_RUN"), False)
