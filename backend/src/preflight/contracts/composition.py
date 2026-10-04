"""FR-03: the validated render spec handed to Remotion, plus asset provenance (PRD §9.2).

``CompositionSpec`` is the only thing that reaches the renderer. Product UI appears solely as
the customer's real screenshots; generated assets are backgrounds and motion and carry
provenance. The renderer worker validates the same JSON Schema (exported from this model).
"""

from enum import StrEnum
from typing import Annotated, Self

from pydantic import Field, model_validator

from ._base import SHA256_PATTERN, VIDEO_FPS, VIDEO_HEIGHT, VIDEO_WIDTH, Contract
from .brief import BriefField, NonEmpty
from .concept import VariantId

HexColor = Annotated[str, Field(pattern=r"^#[0-9a-fA-F]{6}$")]


class AssetKind(StrEnum):
    """Generated supporting asset type."""

    IMAGE = "image"
    VIDEO = "video"


class GeneratedAsset(Contract):
    """A generated background or b-roll clip with provenance. Never contains product UI or text."""

    kind: AssetKind
    path: NonEmpty
    model: NonEmpty
    prompt: NonEmpty
    sha256: Annotated[str, Field(pattern=SHA256_PATTERN)]
    duration_s: Annotated[float, Field(gt=0)] | None = None


class Transition(StrEnum):
    """How a scene enters."""

    CUT = "cut"
    FADE = "fade"
    PUSH = "push"
    SCALE = "scale"


class Layout(StrEnum):
    """Where the real screenshot sits relative to the headline."""

    DEVICE_CENTER = "device_center"
    DEVICE_FLOAT = "device_float"
    TEXT_ONLY = "text_only"


class Theme(Contract):
    """Visual tokens for one video. Typography follows the template's design system."""

    background: HexColor
    foreground: HexColor
    accent: HexColor
    font_family: NonEmpty


class SceneSpec(Contract):
    """One scene in frames, with its copy, real screenshot and optional generated backdrop."""

    start_frame: Annotated[int, Field(ge=0)]
    end_frame: Annotated[int, Field(gt=0)]
    text: NonEmpty
    source_field: BriefField
    screenshot: NonEmpty
    layout: Layout
    transition_in: Transition
    backdrop: GeneratedAsset | None = None


class CompositionSpec(Contract):
    """Everything Remotion needs to render one 1080x1920, 30 fps, 15 s variant."""

    variant_id: VariantId
    width: Annotated[int, Field(ge=VIDEO_WIDTH, le=VIDEO_WIDTH)] = VIDEO_WIDTH
    height: Annotated[int, Field(ge=VIDEO_HEIGHT, le=VIDEO_HEIGHT)] = VIDEO_HEIGHT
    fps: Annotated[int, Field(ge=VIDEO_FPS, le=VIDEO_FPS)] = VIDEO_FPS
    duration_frames: Annotated[int, Field(gt=0)]
    theme: Theme
    scenes: tuple[SceneSpec, ...] = Field(min_length=1)
    cta: NonEmpty
    cta_source_field: BriefField
    wordmark: NonEmpty
    headline: NonEmpty
    headline_source_field: BriefField
    logo: str | None = None

    @model_validator(mode="after")
    def _scenes_tile_the_timeline(self) -> Self:
        if self.scenes[0].start_frame != 0:
            raise ValueError("first scene must start at frame 0")
        for previous, current in zip(self.scenes, self.scenes[1:], strict=False):
            if previous.end_frame != current.start_frame:
                raise ValueError("scenes must be contiguous")
        if self.scenes[-1].end_frame != self.duration_frames:
            raise ValueError("last scene must end at duration_frames")
        return self


class RenderResult(Contract):
    """A finished render: path, content hash and how long it took (FR-03 logs render time)."""

    variant_id: VariantId
    video_path: NonEmpty
    video_sha256: Annotated[str, Field(pattern=SHA256_PATTERN)]
    render_seconds: Annotated[float, Field(ge=0)]
