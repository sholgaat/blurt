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
    github_repo: str = ""
    llm_provider: str = "gemini"
    gemini_api_key: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    ollama_api_base: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    model_timeout_seconds: int = 30


@lru_cache(maxsize=1)
def get_backend_settings() -> BackendSettings:
    return BackendSettings()


def validate_github_config(settings: BackendSettings) -> None:
    """Validate that both github_token and github_repo are configured together.
    
    Raises ValueError if one is set but not the other.
    """
    token = (settings.github_token or "").strip()
    repo = (settings.github_repo or "").strip()
    
    token_set = bool(token)
    repo_set = bool(repo)
    
    if token_set != repo_set:  # XOR: exactly one is set
        raise ValueError(
            "Both GITHUB_TOKEN and GITHUB_REPO must be configured together. "
            "Either set both or set neither."
        )
