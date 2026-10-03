"""FR-09: run state machine vocabulary and the live activity log (PRD §9)."""

from datetime import datetime
from enum import StrEnum
from typing import Annotated

from pydantic import Field

from ._base import Contract
from .concept import VariantId


class RunState(StrEnum):
    """Deterministic states; a run resumes from the last completed one."""

    BRIEF_RECEIVED = "BRIEF_RECEIVED"
    PLANNED = "PLANNED"
    RENDERED = "RENDERED"
    SIMULATED = "SIMULATED"
    SCORED = "SCORED"
    EXPLAINED = "EXPLAINED"
    ITERATED = "ITERATED"
    DONE = "DONE"
    FAILED = "FAILED"


class Step(StrEnum):
    """User-visible steps in the activity log."""

    PLAN = "plan"
    GENERATE = "generate"
    RENDER = "render"
    SIMULATE = "simulate"
    SCORE = "score"
    EXPLAIN = "explain"
    ITERATE = "iterate"
    EXPORT = "export"


class StepStatus(StrEnum):
    """Lifecycle of one logged step."""

    STARTED = "started"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"


class ActivityEvent(Contract):
    """One line of the append-only activity log, streamed live and saved with the project."""

    at: datetime
    step: Step
    status: StepStatus
    message: Annotated[str, Field(min_length=1)]
    variant_id: VariantId | None = None
    duration_s: Annotated[float, Field(ge=0)] | None = None


class RenderStatus(StrEnum):
    """Outcome of rendering one variant."""

    PENDING = "pending"
    RENDERED = "rendered"
    FAILED = "failed"


class VariantRecord(Contract):
    """Per-variant progress kept in ``run.json``."""

    variant_id: VariantId
    render_status: RenderStatus = RenderStatus.PENDING
    video_path: str | None = None
    video_sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")] | None = None
    render_seconds: Annotated[float, Field(ge=0)] | None = None
    error: str | None = None


class RunRecord(Contract):
    """Persisted run snapshot (``run.json``)."""

    project_id: str
    state: RunState
    variants: tuple[VariantRecord, ...] = ()
    error: str | None = None
    updated_at: datetime
