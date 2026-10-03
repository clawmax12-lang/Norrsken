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
    Simulation results carry series and events and point at brain data by file, never inline.
    """

    variant_id: VariantId
    concept: CreativeConcept
    render: VariantRecord | None
    simulations: tuple[SimulationResult, ...]
    files: dict[str, str]


class ResultsResponse(BaseModel):
    """Results so far: ranking and report appear once those steps have finished."""

    project_id: str
    state: RunState
    ranking: Ranking | None
    report: Report | None
    variants: tuple[VariantResults, ...]


class HealthResponse(BaseModel):
    """Liveness probe body."""

    status: Literal["ok"] = "ok"
