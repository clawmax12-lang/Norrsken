"""MotionScene / MotionSpec: 60 fps generative track, isolated from CompositionSpec."""

from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import Field, field_validator, model_validator

from preflight.contracts._base import VIDEO_DURATION_S, Contract
from preflight.contracts.brief import BriefField, NonEmpty
from preflight.contracts.composition import Theme
from preflight.contracts.concept import VariantId

MOTION_FPS = 60
MOTION_FRAMES = VIDEO_DURATION_S * MOTION_FPS
CONFIDENCE_MIN = 0.75
MIN_LAYERS = 2


class LayerKind(StrEnum):
    """Closed set of reconstructed UI kinds. Unknown regions are ``other``."""

    PANEL = "panel"
    BUTTON = "button"
    CHART = "chart"
    TEXT = "text"
    ICON = "icon"
    OTHER = "other"


class MotionLayer(Contract):
    """One reconstructed region. ``bbox_norm`` is x, y, w, h in the unit square."""

    id: NonEmpty
    kind: LayerKind
    bbox_norm: tuple[float, float, float, float]
    confidence: Annotated[float, Field(ge=0, le=1)]
    path: str | None = None
    label: str | None = None

    @field_validator("bbox_norm")
    @classmethod
    def _unit_square(
        cls, value: tuple[float, float, float, float]
    ) -> tuple[float, float, float, float]:
        x, y, width, height = value
        if width <= 0 or height <= 0:
            raise ValueError("bbox width and height must be positive")
        if x < 0 or y < 0 or x + width > 1.02 or y + height > 1.02:
            raise ValueError("bbox must lie in the unit square")
        return value


class ExtractedLayers(Contract):
    """Persisted Vision output for one screenshot after confidence filtering."""

    screenshot: NonEmpty
    layers: tuple[MotionLayer, ...]
    skipped: str | None = None


class MotionShot(Contract):
    """One 60 fps beat. Timestamps stay in seconds; frames are derived at compose time."""

    screenshot: NonEmpty
    start_frame: Annotated[int, Field(ge=0)]
    end_frame: Annotated[int, Field(gt=0)]
    text: NonEmpty
    source_field: BriefField
    layers: tuple[MotionLayer, ...]
    t_start: Annotated[float, Field(ge=0, le=VIDEO_DURATION_S)]
    t_end: Annotated[float, Field(gt=0, le=VIDEO_DURATION_S)]


class MotionSpec(Contract):
    """Input to the isolated ``PreflightMotion`` Remotion composition."""

    variant_id: VariantId
    width: Literal[1080] = 1080
    height: Literal[1920] = 1920
    fps: Literal[60] = 60
    duration_frames: Literal[900] = 900
    theme: Theme
    shots: tuple[MotionShot, ...]
    cta: NonEmpty
    cta_source_field: BriefField
    wordmark: NonEmpty
    headline: NonEmpty
    headline_source_field: BriefField
    logo: str | None = None
    underlay: bool = False

    @model_validator(mode="after")
    def _timeline_covers_the_video(self) -> Self:
        if not self.shots:
            raise ValueError("motion spec needs at least one shot")
        cursor = 0
        for shot in self.shots:
            if shot.start_frame != cursor or shot.end_frame <= shot.start_frame:
                raise ValueError("shots must tile the 900-frame timeline")
            cursor = shot.end_frame
        if cursor != self.duration_frames:
            raise ValueError("last shot must end at duration_frames")
        return self
