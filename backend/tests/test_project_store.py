from pathlib import Path

import pytest

from preflight.contracts import ActivityEvent, Step, StepStatus
from preflight.errors import PreflightValidationError, StorageError
from preflight.storage import ProjectStore
from tests.factories import FIXED_NOW, make_brief


def test_write_then_read_round_trips_atomically(tmp_path: Path) -> None:
    store = ProjectStore(tmp_path)
    paths = store.create("proj-1")
    brief = make_brief()
    store.write(paths.brief, brief)
    assert store.read(paths.brief, type(brief)) == brief
    assert not list(paths.root.glob(".*.tmp"))


@pytest.mark.parametrize("bad_id", ["../etc", "a/b", "", ".hidden", "x" * 65])
def test_unsafe_project_ids_are_rejected(tmp_path: Path, bad_id: str) -> None:
    with pytest.raises(PreflightValidationError):
        ProjectStore(tmp_path).paths(bad_id)


def test_duplicate_project_and_missing_file_fail_loudly(tmp_path: Path) -> None:
    store = ProjectStore(tmp_path)
    paths = store.create("p")
    with pytest.raises(PreflightValidationError):
        store.create("p")
    with pytest.raises(StorageError):
        store.read(paths.brief, type(make_brief()))


def test_event_log_appends_and_resumes_from_offset(tmp_path: Path) -> None:
    store = ProjectStore(tmp_path)
    store.create("p")
    for step in (Step.PLAN, Step.RENDER, Step.SIMULATE):
        store.append_event(
            "p",
            ActivityEvent(at=FIXED_NOW, step=step, status=StepStatus.STARTED, message=step.value),
        )
    assert [e.step for e in store.read_events("p")] == [Step.PLAN, Step.RENDER, Step.SIMULATE]
    assert [e.step for e in store.read_events("p", start=2)] == [Step.SIMULATE]
