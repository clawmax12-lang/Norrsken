"""Test-only stand-ins. None of this may be imported by application code.

``FakePredictor`` returns deterministic numbers derived from the video path so tests can check
plumbing; it is not brain activity and must never be rendered as such.
"""

import threading
from pathlib import Path

import numpy as np

from tribe_worker.atlas import (
    FSAVERAGE5_HEMISPHERE_VERTICES,
    GroupDefinitions,
    RegionGroups,
    SurfaceAtlas,
    load_group_definitions,
    resolve_groups,
)
from tribe_worker.predictor import Prediction, PredictorInfo

N_VERTICES = 2 * FSAVERAGE5_HEMISPHERE_VERTICES
FAKE_REVISION = "tribev2-fake"


def fake_atlas_for(definitions: GroupDefinitions) -> SurfaceAtlas:
    """An atlas whose vertices cycle through the labels the groups name (plus one unnamed)."""
    names = ["Unknown", *(label for g in definitions.groups for label in g.atlas_labels)]
    cycle = np.arange(len(names))
    hemisphere = np.resize(cycle, FSAVERAGE5_HEMISPHERE_VERTICES)
    return SurfaceAtlas(labels=tuple(names), left=hemisphere, right=hemisphere.copy())


def fake_groups() -> RegionGroups:
    """The reviewed group file resolved against the synthetic atlas."""
    definitions = load_group_definitions()
    return resolve_groups(definitions, fake_atlas_for(definitions))


class FakePredictor:
    """Counts calls, can block inference, and can be told to fail."""

    def __init__(self, *, n_rows: int = 15, padding_rows: int = 3, loaded: bool = True) -> None:
        self.n_rows = n_rows
        self.padding_rows = padding_rows
        self.loaded = loaded
        self.predict_calls: list[Path] = []
        self.fail_with: Exception | None = None
        self.gate: threading.Event | None = None
        self.entered = threading.Event()

    def info(self) -> PredictorInfo:
        return PredictorInfo(
            loaded=self.loaded,
            device="cpu",
            gpu_name=None,
            vram_total_mb=None,
            torch_version=None,
            tribev2_revision="a" * 40,
            checkpoint_revision="b" * 40 if self.loaded else None,
            load_seconds=0.5 if self.loaded else None,
        )

    def load(self) -> None:
        self.loaded = True

    def predict(self, video_path: Path) -> Prediction:
        self.predict_calls.append(video_path)
        self.entered.set()
        if self.gate is not None:
            self.gate.wait(timeout=10)
        if self.fail_with is not None:
            raise self.fail_with
        rows = self.n_rows + self.padding_rows
        rng = np.random.default_rng(0)
        activity = rng.normal(0.0, 0.5, size=(rows, N_VERTICES)).astype(np.float32)
        return Prediction(
            activity=activity, start_times_s=tuple(float(i) for i in range(rows)), hz=1.0
        )
