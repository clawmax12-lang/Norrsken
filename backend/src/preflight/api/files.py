"""Download files that belong to a variant, from an allow-list only.

Clients name a *kind* and a variant id, never a path. Brain artifact locations come from the
stored simulation result and are accepted only if they resolve to a regular file inside the
project directory, so neither ``..`` segments nor symlinks can reach anything else.
"""

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from preflight.contracts import SimulationResult, SimulatorName, VariantId
from preflight.storage import ProjectPaths, ProjectStore


class FileKind(StrEnum):
    """The only kinds of file the API serves per variant."""

    VIDEO = "video"
    VIDEO_FINAL = "video-final"
    BRAIN_ACTIVITY = "brain-activity"
    BRAIN_GROUPS = "brain-groups"


_MEDIA_TYPES = {
    FileKind.VIDEO: "video/mp4",
    FileKind.VIDEO_FINAL: "video/mp4",
    FileKind.BRAIN_ACTIVITY: "application/octet-stream",
    FileKind.BRAIN_GROUPS: "application/json",
}


@dataclass(frozen=True)
class ServedFile:
    """A file on disk and the media type to send it as."""

    path: Path
    media_type: str


def file_url(project_id: str, kind: FileKind, variant: VariantId) -> str:
    """URL under which :func:`locate_file` results are served."""
    return f"/api/projects/{project_id}/files/{kind.value}/{variant}"


def locate_file(
    store: ProjectStore, paths: ProjectPaths, kind: FileKind, variant: VariantId
) -> ServedFile | None:
    """Return the file for ``kind``/``variant``, or ``None`` when it does not exist (yet)."""
    candidate = _candidate_path(store, paths, kind, variant)
    if candidate is None or not _is_inside(candidate, paths.root) or not candidate.is_file():
        return None
    return ServedFile(path=candidate, media_type=_MEDIA_TYPES[kind])


def _candidate_path(
    store: ProjectStore, paths: ProjectPaths, kind: FileKind, variant: VariantId
) -> Path | None:
    if kind is FileKind.VIDEO:
        final = paths.final_video(variant)
        return final if final.is_file() else paths.video(variant)
    if kind is FileKind.VIDEO_FINAL:
        return paths.final_video(variant)
    simulation = paths.simulation(variant, SimulatorName.TRIBE_V2.value)
    if not simulation.is_file():
        return None
    brain = store.read(simulation, SimulationResult).brain
    if brain is None:
        return None
    relative = brain.activity_path if kind is FileKind.BRAIN_ACTIVITY else brain.groups_path
    return paths.root / relative


def _is_inside(candidate: Path, root: Path) -> bool:
    return candidate.resolve().is_relative_to(root.resolve())
