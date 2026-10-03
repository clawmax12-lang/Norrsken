"""Assemble what a run has produced so far (FR-07 reads this)."""

from pathlib import Path
from string import ascii_uppercase

from pydantic import BaseModel

from preflight.contracts import (
    CreativeConcept,
    Ranking,
    Report,
    RunRecord,
    SimulationResult,
    SimulatorName,
    SoundRecord,
    VariantId,
)
from preflight.storage import ProjectPaths, ProjectStore

from .files import FileKind, file_url, locate_file
from .schemas import ResultsResponse, VariantResults


def build_results(store: ProjectStore, project_id: str) -> ResultsResponse:
    """Return every result that exists for the project; missing steps are ``None``/absent.

    Blocking file I/O: call from a worker thread.
    """
    paths = store.paths(project_id)
    run = store.read(paths.run, RunRecord)
    variants = tuple(
        _variant_results(store, paths, run, project_id, variant)
        for variant in ascii_uppercase
        if paths.concept(variant).is_file()
    )
    return ResultsResponse(
        project_id=project_id,
        state=run.state,
        ranking=_read_if_present(store, paths.ranking, Ranking),
        report=_read_if_present(store, paths.report, Report),
        variants=variants,
    )


def _variant_results(
    store: ProjectStore, paths: ProjectPaths, run: RunRecord, project_id: str, variant: VariantId
) -> VariantResults:
    return VariantResults(
        variant_id=variant,
        concept=store.read(paths.concept(variant), CreativeConcept),
        render=next((record for record in run.variants if record.variant_id == variant), None),
        simulations=_simulations(store, paths, variant),
        files={
            kind.value: file_url(project_id, kind, variant)
            for kind in FileKind
            if locate_file(store, paths, kind, variant) is not None
        },
        sound=_read_if_present(store, paths.sound(variant), SoundRecord),
    )


def _simulations(
    store: ProjectStore, paths: ProjectPaths, variant: VariantId
) -> tuple[SimulationResult, ...]:
    results = (
        _read_if_present(store, paths.simulation(variant, simulator.value), SimulationResult)
        for simulator in SimulatorName
    )
    return tuple(result for result in results if result is not None)


def _read_if_present[M: BaseModel](
    store: ProjectStore, path: Path, model_type: type[M]
) -> M | None:
    return store.read(path, model_type) if path.is_file() else None
