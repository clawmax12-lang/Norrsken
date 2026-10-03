"""Response bodies that combine several contracts."""

from typing import Literal

from pydantic import BaseModel

from preflight.contracts import (
    Brief,
    CreativeConcept,
    Ranking,
    Report,
    RunRecord,
    RunState,
    SimulationResult,
    SoundRecord,
    VariantId,
    VariantRecord,
)


class ProjectResponse(BaseModel):
    """A project: where its run stands and the brief it was started from."""

    run: RunRecord
    brief: Brief


class VariantResults(BaseModel):
    """Everything known so far about one variant.

    ``files`` maps each downloadable file kind to its URL; only files that exist are listed.
    ``sound`` says what narration, music and effects were added to ``video-final`` after the
    pretest (the simulations describe the silent ``video``).
    Simulation results carry series and events and point at brain data by file, never inline.
    """

    variant_id: VariantId
    concept: CreativeConcept
    render: VariantRecord | None
    simulations: tuple[SimulationResult, ...]
    files: dict[str, str]
    sound: SoundRecord | None = None


class ResultsResponse(BaseModel):
    """Results so far: ranking and report appear once those steps have finished."""

    project_id: str
    state: RunState
    ranking: Ranking | None
    report: Report | None
    variants: tuple[VariantResults, ...]


class HealthResponse(BaseModel):
    """Liveness probe body, plus which providers are configured so the UI can say so up front.

    ``brain_sim`` false means "Brain sim off": no TRIBE worker is configured.
    """

    status: Literal["ok"] = "ok"
    runs: bool = False
    gemini: bool = False
    condense: bool = False
    brain_sim: bool = False
    opus: bool = False
