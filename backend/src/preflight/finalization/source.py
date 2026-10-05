"""Bind finalization consent to unchanged inputs and preserve the initial winner evidence."""

import hashlib
import json
from dataclasses import dataclass

from preflight.config import Settings
from preflight.contracts import (
    Brief,
    CompositionSpec,
    CreativeConcept,
    Report,
    RunRecord,
    RunState,
    SimulationResult,
)
from preflight.contracts.finalization import FinalizeCommand
from preflight.errors import PreflightValidationError
from preflight.hashing import sha256_file
from preflight.storage import ProjectPaths, ProjectStore


@dataclass(frozen=True)
class FinalSource:
    """The trusted source snapshot; caller-provided composition/content is never accepted."""

    brief: Brief
    concept: CreativeConcept
    spec: CompositionSpec
    report: Report
    fingerprint: str


def read_source(
    store: ProjectStore, project_id: str, command: FinalizeCommand, settings: Settings
) -> FinalSource:
    """Reject incomplete runs, non-winners, stale approval, changed assets and unsafe paths."""
    paths = store.paths(project_id)
    run = store.read(paths.run, RunRecord)
    report = store.read(paths.report, Report)
    if run.state is not RunState.DONE or report.winner != command.variant_id:
        raise PreflightValidationError("Finishing requires the completed run's winner")
    render = next((v for v in run.variants if v.variant_id == report.winner), None)
    if render is None or render.video_sha256 != command.source_video_sha256:
        raise PreflightValidationError("Finalization approval is stale; reload the tested winner")
    tested_video = (
        paths.root / render.video_path if render.video_path else paths.video(report.winner)
    )
    if sha256_file(tested_video) != command.source_video_sha256:
        raise PreflightValidationError("The tested source video changed; run a new pretest")
    tested = store.read(paths.simulation(report.winner, "gemini_panel"), SimulationResult)
    if tested.video_sha256 != command.source_video_sha256 or tested.variant_id != report.winner:
        raise PreflightValidationError("The original winner has no matching pretest evidence")
    spec = store.read(paths.spec(report.winner), CompositionSpec)
    if spec.duration_frames != 450 or not 4 <= len(spec.scenes) <= 6:
        raise PreflightValidationError("Finalization requires the 15-second, 4-6-shot template")
    brief = store.read_brief(project_id)
    concept = store.read(paths.concept(report.winner), CreativeConcept)
    content = {
        "brief": brief.model_dump(),
        "spec": spec.model_dump(),
        "report": report.model_dump(),
        "concept": concept.model_dump(),
        "source_video_sha256": command.source_video_sha256,
        "assets": _assets(paths, spec, brief),
        "models": [settings.anthropic_model, settings.gemini_model, settings.tribe_endpoint],
        "sound": [settings.sound_enabled],
    }
    digest = hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()
    return FinalSource(brief, concept, spec, report, digest)


def _assets(paths: ProjectPaths, spec: CompositionSpec, brief: Brief) -> dict[str, str]:
    assets = {}
    for scene in spec.scenes:
        if scene.screenshot not in brief.screenshots:
            raise PreflightValidationError("Final source references an unapproved screenshot")
        for name in (scene.screenshot, *([scene.backdrop.path] if scene.backdrop else [])):
            path = (paths.root / name).resolve()
            if not path.is_relative_to(paths.root.resolve()) or not path.is_file():
                raise PreflightValidationError(
                    "Final source asset is missing or outside the project"
                )
            assets[name] = sha256_file(path)
    return assets
