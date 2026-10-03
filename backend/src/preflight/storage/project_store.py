"""Per-project JSON/JSONL persistence under ``data/projects/{project_id}/`` (PRD §9).

Every write is atomic (temp file + rename) so a crashed run never leaves half a file and
can resume from the last completed state.
"""

import os
import re
import tempfile
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from preflight.contracts import ActivityEvent, Brief
from preflight.errors import PreflightValidationError, StorageError

_PROJECT_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
_M = TypeVar("_M", bound=BaseModel)


@dataclass(frozen=True)
class ProjectPaths:
    """Well-known locations inside one project directory."""

    root: Path

    @property
    def brief(self) -> Path:
        """``brief.json``."""
        return self.root / "brief.json"

    @property
    def run(self) -> Path:
        """``run.json`` snapshot."""
        return self.root / "run.json"

    @property
    def log(self) -> Path:
        """Append-only activity log."""
        return self.root / "log.jsonl"

    @property
    def ranking(self) -> Path:
        """``ranking.json``."""
        return self.root / "ranking.json"

    @property
    def report(self) -> Path:
        """``report.json``."""
        return self.root / "report.json"

    @property
    def uploads(self) -> Path:
        """Customer screenshots and logo."""
        return self.root / "uploads"

    @property
    def assets(self) -> Path:
        """Generated supporting assets."""
        return self.root / "assets"

    @property
    def exports(self) -> Path:
        """Files offered for download."""
        return self.root / "exports"

    def concept(self, variant_id: str) -> Path:
        """Concept JSON for a variant."""
        return self.root / "concepts" / f"{variant_id}.json"

    def spec(self, variant_id: str) -> Path:
        """Composition spec JSON for a variant."""
        return self.root / "specs" / f"{variant_id}.json"

    def video(self, variant_id: str) -> Path:
        """Rendered MP4 for a variant."""
        return self.root / "videos" / f"{variant_id}.mp4"

    def final_video(self, variant_id: str) -> Path:
        """Rendered MP4 with narration, music and sound effects added after the pretest."""
        return self.root / "videos" / f"{variant_id}.final.mp4"

    @property
    def opus_dir(self) -> Path:
        """Separate finalization artifacts; never replaces candidate evidence."""
        return self.root / "finalization"

    @property
    def finalization(self) -> Path:
        """Persisted selected-winner job and exact-video evidence."""
        return self.opus_dir / "record.json"

    def sound(self, variant_id: str) -> Path:
        """What was added to a variant's final video (``SoundRecord``)."""
        return self.root / "sound" / f"{variant_id}.json"

    @property
    def sound_work(self) -> Path:
        """Scratch and cache for sound: synthesized narration lines and the mixed WAV."""
        return self.root / "sound" / "work"

    def simulation(self, variant_id: str, simulator: str) -> Path:
        """One simulator's result for a variant."""
        return self.root / "simulations" / f"{variant_id}.{simulator}.json"

    def brain_dir(self, variant_id: str) -> Path:
        """Directory for a variant's brain artifacts."""
        return self.root / "brain" / variant_id


class ProjectStore:
    """Creates project directories and reads/writes validated models inside them."""

    def __init__(self, data_dir: Path) -> None:
        """Store projects under ``data_dir``."""
        self._data_dir = data_dir

    def paths(self, project_id: str) -> ProjectPaths:
        """Return the paths for ``project_id`` after rejecting unsafe ids."""
        if not _PROJECT_ID.fullmatch(project_id):
            raise PreflightValidationError(f"invalid project id: {project_id!r}")
        return ProjectPaths(self._data_dir / project_id)

    def exists(self, project_id: str) -> bool:
        """True when the project directory exists."""
        return self.paths(project_id).root.is_dir()

    def create(self, project_id: str) -> ProjectPaths:
        """Create the project directory tree; fails if the id is already used."""
        paths = self.paths(project_id)
        try:
            paths.root.mkdir(parents=True, exist_ok=False)
        except FileExistsError as exc:
            raise PreflightValidationError(f"project already exists: {project_id}") from exc
        for directory in (paths.uploads, paths.assets, paths.exports):
            directory.mkdir()
        return paths

    def write(self, path: Path, model: BaseModel) -> None:
        """Atomically write ``model`` as pretty JSON."""
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = model.model_dump_json(indent=2) + "\n"
        fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(payload)
            Path(tmp_name).replace(path)
        except BaseException:
            Path(tmp_name).unlink(missing_ok=True)
            raise

    def read(self, path: Path, model_type: type[_M]) -> _M:
        """Read and validate a model; missing or invalid files raise :class:`StorageError`."""
        try:
            return model_type.model_validate_json(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise StorageError(f"missing file: {path}") from exc
        except ValidationError as exc:
            raise StorageError(f"invalid {model_type.__name__} in {path}: {exc}") from exc

    def read_brief(self, project_id: str) -> Brief:
        """Read ``brief.json`` with screenshot and logo paths relative to the project directory.

        The web app saves paths from the repository root (``data/projects/{id}/assets/x.png``);
        that prefix is dropped so every consumer resolves paths the same way.
        """
        brief = self.read(self.paths(project_id).brief, Brief)
        prefix = f"data/projects/{project_id}/"

        def relative(path: str) -> str:
            return path.removeprefix(prefix)

        return brief.model_copy(
            update={
                "screenshots": tuple(relative(p) for p in brief.screenshots),
                "logo": relative(brief.logo) if brief.logo else brief.logo,
            }
        )

    def append_event(self, project_id: str, event: ActivityEvent) -> None:
        """Append one activity event to ``log.jsonl`` (one JSON object per line)."""
        log = self.paths(project_id).log
        with log.open("a", encoding="utf-8") as handle:
            handle.write(event.model_dump_json() + "\n")

    def read_events(self, project_id: str, *, start: int = 0) -> Iterator[ActivityEvent]:
        """Yield logged events from line ``start`` (used to resume live streams)."""
        log = self.paths(project_id).log
        if not log.exists():
            return
        with log.open(encoding="utf-8") as handle:
            for index, line in enumerate(handle):
                if index >= start and line.strip():
                    yield ActivityEvent.model_validate_json(line)
