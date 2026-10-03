import json

import pytest

from preflight.contracts import RunRecord, RunState
from preflight.errors import StorageError
from preflight.orchestrator.preparation import prepare_run
from preflight.storage import ProjectStore
from tests.factories import FIXED_NOW, make_brief

PROJECT = "launch-draft"


def web_app_brief(store: ProjectStore, one_liner: str = "Notes that organise themselves") -> None:
    """What the Next.js app writes: brief.json only, with repo-root screenshot paths."""
    root = store.paths(PROJECT).root
    root.mkdir(parents=True, exist_ok=True)
    brief = make_brief(
        project_id=PROJECT,
        one_liner=one_liner,
        screenshots=tuple(f"data/projects/{PROJECT}/assets/{n}.png" for n in range(3)),
        goal_note="",
    )
    (root / "brief.json").write_text(json.dumps(brief.model_dump(mode="json")))


def prepare(store: ProjectStore) -> RunRecord:
    return prepare_run(store, PROJECT, lambda: FIXED_NOW)


def test_a_brief_saved_by_the_web_app_becomes_runnable(tmp_path) -> None:
    store = ProjectStore(tmp_path)
    web_app_brief(store)

    record = prepare(store)

    assert record.state is RunState.BRIEF_RECEIVED
    assert store.paths(PROJECT).run.is_file()
    assert store.read_brief(PROJECT).screenshots == ("assets/0.png", "assets/1.png", "assets/2.png")


def test_an_unchanged_brief_resumes_the_previous_run(tmp_path) -> None:
    store = ProjectStore(tmp_path)
    web_app_brief(store)
    prepare(store)
    paths = store.paths(PROJECT)
    store.write(paths.run, RunRecord(project_id=PROJECT, state=RunState.DONE, updated_at=FIXED_NOW))

    assert prepare(store).state is RunState.DONE


def test_a_changed_brief_archives_the_previous_run_and_starts_over(tmp_path) -> None:
    store = ProjectStore(tmp_path)
    web_app_brief(store)
    prepare(store)
    paths = store.paths(PROJECT)
    store.write(paths.run, RunRecord(project_id=PROJECT, state=RunState.DONE, updated_at=FIXED_NOW))
    paths.video("A").parent.mkdir()
    paths.video("A").write_bytes(b"old video")

    web_app_brief(store, one_liner="A different product line")
    record = prepare(store)

    assert record.state is RunState.BRIEF_RECEIVED
    assert not paths.video("A").exists()
    (archived,) = (paths.root / "history").iterdir()
    assert (archived / "videos" / "A.mp4").read_bytes() == b"old video"
    assert (archived / "run.json").is_file()
    assert (paths.root / "brief.json").is_file()


def test_a_project_without_a_brief_cannot_start(tmp_path) -> None:
    store = ProjectStore(tmp_path)
    store.paths(PROJECT).root.mkdir(parents=True)

    with pytest.raises(StorageError, match="missing file"):
        prepare(store)
