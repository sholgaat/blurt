from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class BackendSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env.backend",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    github_token: str = ""
    github_repo_owner: str = ""
    github_repo_name: str = ""
    llm_provider: str = "gemini"
    gemini_api_key: str = ""
    openai_api_key: str = ""
    dry_run: bool = False


@lru_cache(maxsize=1)
def get_backend_settings() -> BackendSettings:
    return BackendSettings()
