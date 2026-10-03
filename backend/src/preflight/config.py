"""Runtime configuration from environment variables (PRD §10.4). Secrets never live in code."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# <repo>/backend/src/preflight/config.py -> <repo>
_REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """All tunables in one place. Names match ``.env.example``."""

    model_config = SettingsConfigDict(env_file=(_REPO_ROOT / ".env", ".env"), extra="ignore")

    data_dir: Path = _REPO_ROOT / "data" / "projects"

    anthropic_api_key: SecretStr | None = None
    anthropic_model: str = Field(default="claude-opus-5-5", pattern=r"^claude-opus-[a-zA-Z0-9.-]+$")
    opus_max_output_tokens: int = Field(default=4096, ge=1024, le=8192)

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

    renderer_dir: Path = Field(
        default=_REPO_ROOT / "workers" / "renderer",
        description="The Remotion worker package (run `npm ci` there once).",
    )
    node_binary: str = Field(default="node", description="Node.js >= 22.18 for the renderer.")
    render_concurrency: int | None = Field(
        default=None,
        ge=1,
        description="Frames rendered in parallel per video; unset = Remotion's default.",
    )

    sound_enabled: bool = Field(
        default=True,
        description="Add music and sound effects (and narration) to the exported videos.",
    )
    narration_enabled: bool = Field(
        default=True, description="Gemini text-to-speech narration of the on-screen copy."
    )
    tts_model: str = Field(
        default="gemini-3.8-flash-tts",
        description="Gemini text-to-speech model (the id in Google's docs on 2026-10-03).",
    )
    narration_voice: str = Field(
        default="Kore", description="Gemini prebuilt voice; the Live Director uses the same one."
    )
    ffmpeg_binary: str = Field(default="ffmpeg", description="ffmpeg for mixing and muxing.")
    ffprobe_binary: str = Field(default="ffprobe", description="ffprobe to verify the output.")

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
