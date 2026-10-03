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
    gemini_model: str = Field(
        default="gemini-3.8-flash",
        description="Gemini model for planning, the viewer panel and explanations "
        "(the default in Google's docs on 2026-10-03).",
    )
    condense_api_key: SecretStr | None = None
    condense_base_url: str = "https://api.condense.chat"
    condense_compression_rate: float = Field(default=0.2, ge=0.0, le=1.0)
    condense_proxy: bool = Field(
        default=True,
        description="With CONDENSE_API_KEY set, send Gemini calls through the Condense proxy; "
        "a proxy failure falls back to calling Gemini directly.",
    )
    condense_upstream_url: str = Field(
        default="https://generativelanguage.googleapis.com/v1beta/openai",
        description="Where the Condense proxy forwards: Gemini's OpenAI-compatible endpoint.",
    )
    tribe_endpoint: str | None = Field(
        default=None, description="Base URL of our TRIBE GPU worker; unset means 'Brain sim off'."
    )

    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000"],
        description="Browser origins allowed to call the API (JSON list in the environment).",
    )

    max_variants: int = Field(default=3, ge=1, le=26)
    max_revisions: int = Field(default=1, ge=0)
    step_timeout_s: float = Field(default=600.0, gt=0)
    step_retries: int = Field(default=1, ge=0)


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance; tests construct ``Settings`` directly instead."""
    return Settings()
