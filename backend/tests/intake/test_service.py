import json
from datetime import UTC, datetime

import pytest

from preflight.contracts import Brief, Goal, RunRecord, RunState
from preflight.errors import PreflightValidationError
from preflight.intake import BriefForm, create_project
from preflight.storage import ProjectStore
from tests.intake.imaging import image_bytes, jpeg, png, three_screenshots

NOW = datetime(2026, 10, 3, 9, 30, tzinfo=UTC)


@pytest.fixture
def data_dir(tmp_path):
    return tmp_path / "projects"


@pytest.fixture
def store(data_dir):
    return ProjectStore(data_dir)


def make_form(**overrides) -> BriefForm:
    fields = {
        "product_name": "Acme Notes",
        "one_liner": "Notes that organise themselves",
        "goal": "signups",
        "audience": "busy startup founders",
        **overrides,
    }
    return BriefForm(**fields)


def create(store, form=None, screenshots=None, logo=None):
    return create_project(
        store,
        form or make_form(),
        screenshots if screenshots is not None else three_screenshots(),
        logo,
        clock=lambda: NOW,
        new_project_id=lambda: "proj-fixed",
    )


def project_dirs(data_dir):
    return sorted(path.name for path in data_dir.glob("*")) if data_dir.exists() else []


def test_creates_a_brief_that_matches_the_form(store):
    brief = create(store, make_form(goal_note="Launching soon", brand_color="#12ab34"))

    assert brief == Brief(
        project_id="proj-fixed",
        product_name="Acme Notes",
        one_liner="Notes that organise themselves",
        screenshots=(
            "uploads/screenshot-1.png",
            "uploads/screenshot-2.jpg",
            "uploads/screenshot-3.png",
        ),
        goal=Goal.SIGNUPS,
        goal_note="Launching soon",
        audience="busy startup founders",
        brand_color="#12ab34",
        logo=None,
    )


def test_brief_json_and_run_record_are_saved(store):
    brief = create(store)
    paths = store.paths(brief.project_id)

    assert store.read(paths.brief, Brief) == brief
    run = store.read(paths.run, RunRecord)
    assert (run.state, run.updated_at) == (RunState.BRIEF_RECEIVED, NOW)
    assert json.loads(paths.brief.read_text())["project_id"] == "proj-fixed"


def test_uploads_are_written_under_generated_names(store):
    screenshots = three_screenshots()
    brief = create(store, screenshots=screenshots, logo=png())
    paths = store.paths(brief.project_id)

    assert [(paths.root / name).read_bytes() for name in brief.screenshots] == screenshots
    assert brief.logo == "uploads/logo.png"
    assert (paths.root / brief.logo).read_bytes() == png()
    assert sorted(p.name for p in paths.uploads.iterdir()) == [
        "logo.png",
        "screenshot-1.png",
        "screenshot-2.jpg",
        "screenshot-3.png",
    ]


def test_extension_follows_content_not_upload_order(store):
    brief = create(store, screenshots=[jpeg(), jpeg(), png(), png()])

    assert [name.rsplit(".", 1)[1] for name in brief.screenshots] == ["jpg", "jpg", "png", "png"]


def test_blank_optional_fields_become_none(store):
    brief = create(store, make_form(goal_note="  ", brand_color=""))

    assert brief.goal_note is None
    assert brief.brand_color is None


def test_default_project_id_is_safe_and_unique(store):
    ids = {create_project(store, make_form(), three_screenshots()).project_id for _ in range(3)}

    assert len(ids) == 3
    assert all(store.exists(project_id) for project_id in ids)


@pytest.mark.parametrize("count", [0, 2, 7])
def test_screenshot_count_must_be_three_to_six(store, count):
    with pytest.raises(PreflightValidationError, match=f"got {count}"):
        create(store, screenshots=[png()] * count)


def test_a_bad_screenshot_names_which_one(store):
    with pytest.raises(PreflightValidationError, match="screenshot 2"):
        create(store, screenshots=[png(), b"not an image", png()])


def test_a_bad_logo_is_rejected(store):
    with pytest.raises(PreflightValidationError, match="logo"):
        create(store, logo=image_bytes("GIF"))


@pytest.mark.parametrize(
    ("overrides", "complaint"),
    [
        ({"product_name": ""}, "product_name"),
        ({"audience": "   "}, "audience"),
        ({"one_liner": "x" * 141}, "one_liner"),
        ({"goal": "go viral"}, "goal"),
        ({"brand_color": "red"}, "brand_color"),
    ],
)
def test_invalid_fields_are_rejected_and_nothing_is_written(store, data_dir, overrides, complaint):
    with pytest.raises(PreflightValidationError, match=complaint):
        create(store, make_form(**overrides))

    assert project_dirs(data_dir) == []


def test_a_one_liner_of_exactly_140_characters_is_accepted(store):
    assert len(create(store, make_form(one_liner="x" * 140)).one_liner) == 140


def test_a_failure_while_saving_leaves_no_half_made_project(store, data_dir, monkeypatch):
    def explode(*_args, **_kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(store, "write", explode)

    with pytest.raises(OSError, match="disk full"):
        create(store)

    assert project_dirs(data_dir) == []


def test_reusing_a_project_id_is_refused_and_keeps_the_first_project(store):
    first = create(store)

    with pytest.raises(PreflightValidationError, match="already exists"):
        create(store, make_form(product_name="Other"))

    assert store.read(store.paths("proj-fixed").brief, Brief) == first
