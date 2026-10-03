"""Selected-winner finalization, separate from the original experiment and its verdict."""

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import Field

from ._base import SHA256_PATTERN, Contract
from .composition import CompositionSpec, Layout, RenderResult, Transition
from .concept import VariantId
from .simulation import SimulationResult
from .sound import SoundRecord

Sha256 = Annotated[str, Field(pattern=SHA256_PATTERN)]


class SceneFinish(Contract):
    """Motion decisions only: no new copy, paths, product claims or executable code."""

    duration_frames: Annotated[int, Field(ge=30, le=240)]
    layout: Layout
    transition_in: Transition


class MotionRecipe(Contract):
    """Opus directs the existing template's rhythm and layouts for 4-6 source scenes."""

    scenes: Annotated[tuple[SceneFinish, ...], Field(min_length=4, max_length=6)]


class OpusUsage(Contract):
    """Actual provider counts; no invented pricing or Condense savings."""

    model: str
    route: Literal["condense/anthropic"] = "condense/anthropic"
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


class FinalizationRecord(Contract):
    """Lineage, bounded Opus usage and evidence for the exact final MP4, never a new ranking."""

    command_id: str
    variant_id: VariantId
    source_video_sha256: Sha256
    source_fingerprint: Sha256
    status: FinalStatus
    updated_at: datetime
    opus_attempts: Annotated[int, Field(ge=0, le=2)] = 0
    usage: OpusUsage | None = None
    render: RenderResult | None = None
    sound: SoundRecord | None = None
    video_sha256: Sha256 | None = None
    simulations: tuple[SimulationResult, ...] = ()
    brain_sim: bool = False
    error: str | None = None
    files: dict[str, str] = Field(default_factory=dict)
