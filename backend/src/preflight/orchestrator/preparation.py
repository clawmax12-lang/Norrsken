"""Make a project runnable before its run starts, whoever saved the brief.

The web app saves ``brief.json`` itself (no ``run.json``) and reuses one project id across
runs. A run therefore starts fresh when the brief changed since the last run: the previous
run's outputs are moved to ``history/`` instead of being resumed with a different brief.
An unchanged brief keeps resuming from the last completed state.
"""

import hashlib
import shutil

from preflight.contracts import RunRecord, RunState
from preflight.errors import StorageError
from preflight.ports import Clock
from preflight.storage import ProjectPaths, ProjectStore

BRIEF_DIGEST_FILE = "brief.sha256"
_RUN_OUTPUTS = (
    "run.json",
    "log.jsonl",
    "ranking.json",
    "report.json",
    "concepts",
    "specs",
    "videos",
    "simulations",
    "brain",
    "exports",
)


def prepare_run(store: ProjectStore, project_id: str, clock: Clock) -> RunRecord:
    """Archive a stale run if the brief changed, ensure ``run.json`` exists and return it.

    Raises:
        StorageError: The project has no readable ``brief.json``.
    """
    paths = store.paths(project_id)
    try:
        digest = hashlib.sha256(paths.brief.read_bytes()).hexdigest()
    except FileNotFoundError as exc:
        raise StorageError(f"missing file: {paths.brief}") from exc
    store.read_brief(project_id)
    marker = paths.root / BRIEF_DIGEST_FILE
    previous = marker.read_text(encoding="utf-8").strip() if marker.is_file() else None
    if previous is not None and previous != digest:
        _archive_outputs(paths, clock)
    marker.write_text(digest, encoding="utf-8")
    if not paths.run.exists():
        store.write(
            paths.run,
            RunRecord(project_id=project_id, state=RunState.BRIEF_RECEIVED, updated_at=clock()),
        )
    return store.read(paths.run, RunRecord)


def _archive_outputs(paths: ProjectPaths, clock: Clock) -> None:
    destination = paths.root / "history" / clock().strftime("%Y%m%dT%H%M%S%fZ")
    for name in _RUN_OUTPUTS:
        source = paths.root / name
        if source.exists():
            destination.mkdir(parents=True, exist_ok=True)
            shutil.move(source, destination / name)
