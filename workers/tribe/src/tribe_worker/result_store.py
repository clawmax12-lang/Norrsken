"""On-disk results keyed by video content hash and model revision.

A result is only valid for the exact video bytes and the model/checkpoint revision that produced
it (PRD §10.5), so both are part of the directory name. ``result.json`` is written last: a
directory without it is an interrupted write and is treated as absent.
"""

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from preflight.contracts import SimulationResult

from tribe_worker.result_builder import ACTIVITY_ARTIFACT, GROUPS_ARTIFACT

RESULT_FILE = "result.json"
ARTIFACT_NAMES = frozenset({ACTIVITY_ARTIFACT, GROUPS_ARTIFACT})


@dataclass(frozen=True)
class StoredResult:
    """A finished analysis and the directory holding its artifacts."""

    result: SimulationResult
    directory: Path


class ResultStore:
    """Persists and retrieves finished analyses."""

    def __init__(self, root: Path) -> None:
        """Keep results under ``root``."""
        self._root = root

    def get(self, video_sha256: str, revision: str) -> StoredResult | None:
        """Return the stored analysis for exactly this video and revision, if complete."""
        directory = self._directory(video_sha256, revision)
        result_file = directory / RESULT_FILE
        if not result_file.is_file():
            return None
        result = SimulationResult.model_validate_json(result_file.read_text("utf-8"))
        return StoredResult(result=result, directory=directory)

    def save(
        self,
        result: SimulationResult,
        revision: str,
        activity: NDArray[np.float16],
        groups_json: dict[str, object],
    ) -> StoredResult:
        """Write the artifacts, then the result file that marks them complete."""
        directory = self._directory(result.video_sha256, revision)
        directory.mkdir(parents=True, exist_ok=True)
        np.save(directory / ACTIVITY_ARTIFACT, activity, allow_pickle=False)
        (directory / GROUPS_ARTIFACT).write_text(json.dumps(groups_json), "utf-8")
        temporary = directory / f"{RESULT_FILE}.tmp"
        temporary.write_text(result.model_dump_json(), "utf-8")
        temporary.replace(directory / RESULT_FILE)
        return StoredResult(result=result, directory=directory)

    def _directory(self, video_sha256: str, revision: str) -> Path:
        return self._root / video_sha256 / revision
