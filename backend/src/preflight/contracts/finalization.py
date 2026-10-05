"""Selected-winner finalization, separate from the original experiment and its verdict."""

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import Field

from ._base import SHA256_PATTERN, Contract
from .composition import CompositionSpec, Layout, RenderResult, Transition
from .concept import FocusBox, Shot, VariantId
from .simulation import SimulationResult
from .sound import SoundRecord

Sha256 = Annotated[str, Field(pattern=SHA256_PATTERN)]
# Who directs the finish: Opus (motion recipe) or Gemini (shots and taps from the screens).
Director = Literal["opus", "gemini"]


class SceneFinish(Contract):
    """Motion decisions only: no new copy, paths, product claims or executable code."""

    duration_frames: Annotated[int, Field(ge=30, le=240)]
    layout: Layout
    transition_in: Transition


class MotionRecipe(Contract):
    """Opus directs the existing template's rhythm and layouts for 4-6 source scenes."""

    scenes: Annotated[tuple[SceneFinish, ...], Field(min_length=4, max_length=6)]


class GeminiSceneFinish(Contract):
    """Gemini's camera for one scene: how it is framed, what is tapped, which word lands.

    ``taps`` are the UI elements the finger works through, in the order the line names them;
    the first is the scene's focus.
    """

    shot: Shot
    taps: Annotated[tuple[FocusBox, ...], Field(max_length=3)] = ()
    emphasis: str | None = None


class GeminiFinish(Contract):
    """One decision per scene before the end card, in order; copy and timing are fixed."""

    scenes: Annotated[tuple[GeminiSceneFinish, ...], Field(min_length=1, max_length=6)]


class OpusUsage(Contract):
    """Actual provider counts of the finish's director; no invented pricing or savings."""

    model: str
    route: Literal["condense/anthropic", "gemini"] = "condense/anthropic"
    input_tokens: Annotated[int, Field(ge=0)]
    output_tokens: Annotated[int, Field(ge=0)]


class FinalComposition(Contract):
    """Atomic checkpoint so resuming a render never buys the composition twice."""

    spec: CompositionSpec
    usage: OpusUsage


class FinalStatus(StrEnum):
    """Persisted lifecycle of the one final asset; the initial RunRecord is not modified."""

    QUEUED = "queued"
    COMPOSING = "composing"
    RENDERING = "rendering"
    AUDIO = "audio"
    SIMULATING = "simulating"
    DONE = "done"
    FAILED = "failed"


class FinalizeCommand(Contract):
    """Approval binds one finalization to the selected, tested winner's exact bytes."""

    command_id: Annotated[str, Field(pattern=r"^[A-Za-z0-9_-]{8,80}$")]
    confirmed: Literal[True]
    variant_id: VariantId
    source_video_sha256: Sha256
    director: Director = "opus"


Score = Annotated[float, Field(ge=0, le=1)]


class FinalComparison(Contract):
    """The final's Gemini pretest next to the original winner's, on the same panel series.

    ``keep_original`` is set when the finished cut scores lower overall: Finish must never
    ship a worse ad, so the original is recommended instead.
    """

    original: Score
    final: Score
    original_hook: Score
    final_hook: Score
    keep_original: bool


class FinalizationRecord(Contract):
    """Lineage, bounded Opus usage and evidence for the exact final MP4, never a new ranking."""

    command_id: str
    variant_id: VariantId
    source_video_sha256: Sha256
    source_fingerprint: Sha256
    status: FinalStatus
    updated_at: datetime
    director: Director = "opus"
    opus_attempts: Annotated[int, Field(ge=0, le=2)] = 0
    usage: OpusUsage | None = None
    render: RenderResult | None = None
    sound: SoundRecord | None = None
    video_sha256: Sha256 | None = None
    simulations: tuple[SimulationResult, ...] = ()
    brain_sim: bool = False
    comparison: FinalComparison | None = None
    error: str | None = None
    files: dict[str, str] = Field(default_factory=dict)
