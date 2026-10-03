"""Worker configuration from ``TRIBE_WORKER_*`` environment variables."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

MAX_UPLOAD_BYTES = 50 * 1024 * 1024


class WorkerSettings(BaseSettings):
    """Tunables of the GPU worker. Everything lives under ``data_dir`` so one volume is enough."""

    model_config = SettingsConfigDict(env_prefix="TRIBE_WORKER_", env_file=".env", extra="ignore")

    data_dir: Path = Path("data")
    model_repo: str = "facebook/tribev2"
    device: str = "cuda"
    preload_model: bool = Field(
        default=True, description="Load the model at startup instead of on the first job."
    )
    max_upload_bytes: int = Field(default=MAX_UPLOAD_BYTES, gt=0)
    max_video_duration_s: float = Field(default=60.0, gt=0)
    queue_size: int = Field(default=4, ge=1, description="Jobs waiting behind the running one.")
    atlas_data_dir: Path | None = Field(
        default=None, description="nilearn data directory holding the Destrieux atlas."
    )

    @property
    def feature_cache_dir(self) -> Path:
        """Where tribev2 caches extracted video/audio/text features."""
        return self.data_dir / "feature-cache"

    @property
    def upload_dir(self) -> Path:
        """Validated uploads, named by content hash."""
        return self.data_dir / "uploads"

    @property
    def result_dir(self) -> Path:
        """Finished results keyed by video hash and model revision."""
        return self.data_dir / "results"
