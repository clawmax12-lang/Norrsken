"""FR-08: assemble the four downloads under ``exports/``."""

import os
import shutil
import tempfile
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

from preflight.contracts import CreativeConcept, Ranking, Report, SoundRecord
from preflight.errors import StorageError
from preflight.storage import ProjectPaths, ProjectStore

from .launch_brief import render_launch_brief

WINNER_VIDEO = "winner.mp4"
RUNNER_UP_VIDEO = "runner_up.mp4"
REPORT_JSON = "report.json"
LAUNCH_BRIEF = "launch_brief.md"


@dataclass(frozen=True)
class ExportBundle:
    """Where the export files are. ``runner_up_video`` is ``None`` when none exists."""

    winner_video: Path
    runner_up_video: Path | None
    report: Path
    launch_brief: Path


def build_export(store: ProjectStore, project_id: str) -> ExportBundle:
    """Write the export files for a finished project and return their locations.

    The videos are copies of the cuts with narration, music and effects when sound was added
    (the pretest watched those mixed files), otherwise of the
    rendered MP4s. ``report.json`` is the validated report and
    the launch brief is rendered from the stored results. When only one variant survived there
    is no runner-up video: the file is absent (a stale one from an earlier run is removed)
    rather than faked. Every file is replaced atomically, so calling it again is safe and a
    concurrent download never sees a half-written file. It does blocking file I/O; call it
    from a worker thread inside async code.

    Raises:
        StorageError: A required result, concept or video is missing or unreadable.
    """
    paths = store.paths(project_id)
    brief = store.read_brief(project_id)
    ranking = store.read(paths.ranking, Ranking)
    report = store.read(paths.report, Report)
    winner = store.read(paths.concept(report.winner), CreativeConcept)
    runner_up = (
        store.read(paths.concept(report.runner_up), CreativeConcept) if report.runner_up else None
    )
    sounds = _sound_records(store, paths, report)
    launch_brief = render_launch_brief(brief, winner, runner_up, ranking, report, sounds)

    paths.exports.mkdir(exist_ok=True)
    winner_video = paths.exports / WINNER_VIDEO
    _publish(
        winner_video, lambda tmp: _copy_video(_exported_video(paths, report.winner, sounds), tmp)
    )
    store.write(paths.exports / REPORT_JSON, report)
    _publish(paths.exports / LAUNCH_BRIEF, lambda tmp: tmp.write_text(launch_brief, "utf-8"))
    return ExportBundle(
        winner_video=winner_video,
        runner_up_video=_export_runner_up(paths, report.runner_up, sounds),
        report=paths.exports / REPORT_JSON,
        launch_brief=paths.exports / LAUNCH_BRIEF,
    )


def _sound_records(
    store: ProjectStore, paths: ProjectPaths, report: Report
) -> dict[str, SoundRecord]:
    """Sound records of the exported variants whose final video (with sound) exists."""
    exported = [v for v in (report.winner, report.runner_up) if v is not None]
    return {
        variant: store.read(paths.sound(variant), SoundRecord)
        for variant in exported
        if paths.sound(variant).is_file() and paths.final_video(variant).is_file()
    }


def _exported_video(paths: ProjectPaths, variant: str, sounds: Mapping[str, SoundRecord]) -> Path:
    """The cut with sound when one was made, otherwise the silent render that was pretested."""
    return paths.final_video(variant) if variant in sounds else paths.video(variant)


def _export_runner_up(
    paths: ProjectPaths, runner_up: str | None, sounds: Mapping[str, SoundRecord]
) -> Path | None:
    destination = paths.exports / RUNNER_UP_VIDEO
    if runner_up is None:
        destination.unlink(missing_ok=True)
        return None
    _publish(destination, lambda tmp: _copy_video(_exported_video(paths, runner_up, sounds), tmp))
    return destination


def _copy_video(source: Path, destination: Path) -> None:
    try:
        shutil.copyfile(source, destination)
    except FileNotFoundError as exc:
        raise StorageError(f"missing file: {source}") from exc


def _publish(destination: Path, fill: Callable[[Path], object]) -> None:
    """Fill a temporary sibling file, then rename it over ``destination``."""
    descriptor, name = tempfile.mkstemp(dir=destination.parent, prefix=f".{destination.name}.")
    os.close(descriptor)
    temporary = Path(name)
    try:
        fill(temporary)
        temporary.replace(destination)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
