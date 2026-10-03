"""Base class and shared constants for every contract model."""

from pydantic import BaseModel, ConfigDict

VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
VIDEO_FPS = 30
VIDEO_DURATION_S = 15
SHA256_PATTERN = r"^[0-9a-f]{64}$"
VARIANT_ID_PATTERN = r"^[A-Z]$"


class Contract(BaseModel):
    """Frozen, strict model: unknown fields are errors, instances are immutable."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)
