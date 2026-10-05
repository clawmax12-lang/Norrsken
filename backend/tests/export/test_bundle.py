import pytest

from preflight.contracts import Report
from preflight.errors import StorageError
from preflight.export import build_export, render_launch_brief
from preflight.storage import ProjectStore
from tests.export.seed import (
    PROJECT_ID,
    VIDEO_BYTES,
    add_sound,
    make_ranking,
    make_report,
    seed_project,
)
from tests.factories import make_brief, make_concept


@pytest.fixture
def store(tmp_path):
    return ProjectStore(tmp_path / "projects")


def test_exports_both_videos_as_copies_of_the_renders(store):
    paths = seed_project(store)

    bundle = build_export(store, PROJECT_ID)

    assert bundle.winner_video == paths.exports / "winner.mp4"
    assert bundle.winner_video.read_bytes() == VIDEO_BYTES["A"]
    assert bundle.runner_up_video == paths.exports / "runner_up.mp4"
    assert bundle.runner_up_video.read_bytes() == VIDEO_BYTES["B"]


def test_report_json_is_the_report_contract(store):
    seed_project(store)

    bundle = build_export(store, PROJECT_ID)

    assert Report.model_validate_json(bundle.report.read_text()) == make_report()


def test_launch_brief_is_rendered_from_the_stored_results(store):
    seed_project(store)

    bundle = build_export(store, PROJECT_ID)

    expected = render_launch_brief(
        make_brief(), make_concept("A"), make_concept("B"), make_ranking(), make_report()
    )
    assert bundle.launch_brief.read_text() == expected


def test_without_a_runner_up_there_is_no_runner_up_file(store):
    paths = seed_project(store, variants=("A",))

    bundle = build_export(store, PROJECT_ID)

    assert bundle.runner_up_video is None
    assert not (paths.exports / "runner_up.mp4").exists()
    assert sorted(p.name for p in paths.exports.iterdir()) == [
        "launch_brief.md",
        "report.json",
        "winner.mp4",
    ]


def test_a_stale_runner_up_from_an_earlier_export_is_removed(store):
    paths = seed_project(store, variants=("A",))
    (paths.exports / "runner_up.mp4").write_bytes(b"stale")

    build_export(store, PROJECT_ID)

    assert not (paths.exports / "runner_up.mp4").exists()


def test_exporting_again_regenerates_without_leftovers(store):
    paths = seed_project(store)
    build_export(store, PROJECT_ID)
    paths.video("A").write_bytes(b"re-rendered")

    bundle = build_export(store, PROJECT_ID)

    assert bundle.winner_video.read_bytes() == b"re-rendered"
    assert sorted(p.name for p in paths.exports.iterdir()) == [
        "launch_brief.md",
        "report.json",
        "runner_up.mp4",
        "winner.mp4",
    ]


def test_a_missing_video_is_a_storage_error_and_leaves_no_partial_file(store):
    paths = seed_project(store)
    paths.video("A").unlink()

    with pytest.raises(StorageError, match="missing file"):
        build_export(store, PROJECT_ID)

    assert list(paths.exports.iterdir()) == []


def test_results_that_do_not_exist_yet_are_a_missing_file_error(store):
    seed_project(store, finished=False)

    with pytest.raises(StorageError) as raised:
        build_export(store, PROJECT_ID)

    assert isinstance(raised.value.__cause__, FileNotFoundError)


def test_videos_with_sound_are_exported_instead_of_the_silent_renders(store):
    paths = seed_project(store)
    winner = add_sound(store, paths, "A")
    runner_up = add_sound(store, paths, "B")

    bundle = build_export(store, PROJECT_ID)

    assert bundle.winner_video.read_bytes() == winner
    assert bundle.runner_up_video.read_bytes() == runner_up
    assert paths.video("A").read_bytes() == VIDEO_BYTES["A"]  # the tested render stays on disk


def test_only_variants_whose_sound_finished_get_the_sound_cut(store):
    paths = seed_project(store)
    add_sound(store, paths, "A")

    bundle = build_export(store, PROJECT_ID)

    assert bundle.winner_video.read_bytes().startswith(b"final-with-sound")
    assert bundle.runner_up_video.read_bytes() == VIDEO_BYTES["B"]


def test_a_sound_record_without_its_video_falls_back_to_the_silent_render(store):
    paths = seed_project(store)
    add_sound(store, paths, "A")
    paths.final_video("A").unlink()

    assert build_export(store, PROJECT_ID).winner_video.read_bytes() == VIDEO_BYTES["A"]


def test_the_launch_brief_tells_the_reader_the_pretest_covered_the_silent_render(store):
    paths = seed_project(store)
    add_sound(store, paths, "A")
    add_sound(store, paths, "B", narrated=False)

    brief = build_export(store, PROJECT_ID).launch_brief.read_text()

    assert "## Sound in the exported videos" in brief
    assert "Simulated viewers watched the soundtrack cut" in brief
    assert "The simulated viewers watched the silent renders" not in brief
    assert "Variant A: narrated by the Gemini voice Kore, reading only the on-screen text" in brief
    assert "Variant B: ambience and sound effects only. Narration is off." in brief
