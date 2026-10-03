"""Runtime configuration from environment variables (PRD §10.4). Secrets never live in code."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All tunables in one place. Names match ``.env.example``."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    data_dir: Path = Path("data/projects")

    gemini_api_key: SecretStr | None = None
    condense_api_key: SecretStr | None = None
    tribe_endpoint: str | None = Field(
        default=None, description="Base URL of our TRIBE GPU worker; unset means 'Brain sim off'."
    )

    max_variants: int = Field(default=3, ge=1, le=26)
    max_revisions: int = Field(default=1, ge=0)
    step_timeout_s: float = Field(default=600.0, gt=0)
    step_retries: int = Field(default=1, ge=0)


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance; tests construct ``Settings`` directly instead."""
    return Settings()
