"""Test-only builders that lay out a finished project on disk the way the pipeline would."""

import json
from datetime import UTC, datetime

from preflight.contracts import (
    BrainArtifact,
    Brief,
    Confidence,
    CreativeConcept,
    Ranking,
    Reason,
    Report,
    RunRecord,
    RunState,
    SimulatorName,
    TokenSavings,
)
from preflight.storage import ProjectPaths, ProjectStore
from tests.factories import make_brief, make_concept, make_result

PROJECT_ID = "proj-1"
NOW = datetime(2026, 10, 3, 12, 0, tzinfo=UTC)
VIDEO_BYTES = {"A": bytes(range(256)) * 8, "B": b"video-B" * 100, "C": b"video-C" * 100}
BRAIN_BYTES = b"\x93NUMPY-test-bytes"


def make_ranking(order: tuple[str, ...] = ("A", "B"), **overrides) -> Ranking:
    scores = {variant: round(0.9 - 0.3 * index, 2) for index, variant in enumerate(order)}
    data = {
        "order": order,
        "scores": scores,
        "per_simulator": {SimulatorName.GEMINI_PANEL: dict(scores)},
        "confidence": Confidence.HIGH,
        "rule": "High when every simulator ranks the same winner.",
    }
    return Ranking(**{**data, **overrides})


def make_report(winner: str = "A", runner_up: str | None = "B", **overrides) -> Report:
    reasons = {
        winner: (
            Reason(t=2, scene_index=0, text="Viewers hold on the outcome-first headline."),
            Reason(t=11, scene_index=3, text="Attention drops when the screenshot changes."),
        ),
    }
    if runner_up:
        reasons[runner_up] = (Reason(t=5, scene_index=1, text="The product shot arrives late."),)
    data = {
        "winner": winner,
        "runner_up": runner_up,
        "reasons": reasons,
        "next_time": ("Open with the screenshot that earned the longest hold.",),
        "token_savings": TokenSavings(
            calls=6, input_tokens_original=12000, input_tokens_sent=7800, output_tokens=900
        ),
        "brain_sim": True,
    }
    return Report(**{**data, **overrides})


def seed_project(
    store: ProjectStore,
    *,
    variants: tuple[str, ...] = ("A", "B"),
    state: RunState = RunState.DONE,
    finished: bool = True,
    brain: bool = False,
    project_id: str = PROJECT_ID,
) -> ProjectPaths:
    """Create a project with concepts, videos and simulations, plus ranking/report if finished."""
    paths = store.create(project_id)
    store.write(paths.brief, make_brief(project_id=project_id))
    store.write(paths.run, RunRecord(project_id=project_id, state=state, updated_at=NOW))
    for variant in variants:
        store.write(paths.concept(variant), make_concept(variant))
        _write_video(paths, variant)
        store.write(paths.simulation(variant, "gemini_panel"), make_result(variant))
    if brain:
        _write_brain(store, paths, variants[0])
    if finished:
        runner_up = variants[1] if len(variants) > 1 else None
        store.write(paths.ranking, make_ranking(variants))
        store.write(paths.report, make_report(variants[0], runner_up))
    return paths


def _write_video(paths: ProjectPaths, variant: str) -> None:
    video = paths.video(variant)
    video.parent.mkdir(parents=True, exist_ok=True)
    video.write_bytes(VIDEO_BYTES.get(variant, b"video"))


def _write_brain(store: ProjectStore, paths: ProjectPaths, variant: str) -> None:
    directory = paths.brain_dir(variant)
    directory.mkdir(parents=True)
    (directory / "activity.npy").write_bytes(BRAIN_BYTES)
    (directory / "groups.json").write_text(json.dumps({"visual": [0, 1, 2]}))
    artifact = BrainArtifact(
        n_vertices=3,
        activity_path=f"brain/{variant}/activity.npy",
        atlas="test-atlas",
        groups_path=f"brain/{variant}/groups.json",
    )
    result = make_result(variant, SimulatorName.TRIBE_V2, brain=artifact)
    store.write(paths.simulation(variant, "tribe_v2"), result)


def brief_and_concepts() -> tuple[Brief, CreativeConcept, CreativeConcept]:
    return make_brief(), make_concept("A"), make_concept("B")
