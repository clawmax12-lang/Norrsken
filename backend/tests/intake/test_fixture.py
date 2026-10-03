"""The tablehopp fixture validates against the Brief contract."""

from pathlib import Path

import pytest

from preflight.contracts import Goal
from preflight.errors import StorageError
from preflight.intake import load_fixture_brief

TABLEHOPP = Path(__file__).resolve().parents[3] / "fixtures" / "tablehopp" / "brief.json"


def test_tablehopp_fixture_validates_against_the_brief_contract():
    brief = load_fixture_brief(TABLEHOPP)

    assert brief.project_id == "tablehopp-demo"
    assert brief.product_name == "tablehopp"
    assert brief.goal is Goal.SIGNUPS
    assert brief.one_liner == "A product launch demo for tablehopp."
    assert brief.audience == "Prospective tablehopp users"
    assert len(brief.screenshots) == 3


def test_screenshots_are_relative_fixture_paths():
    brief = load_fixture_brief(TABLEHOPP)

    assert len(brief.screenshots) == 3
    assert all(path.startswith("fixtures/tablehopp/screenshots/") for path in brief.screenshots)


def test_missing_fixture_is_a_storage_error(tmp_path):
    with pytest.raises(StorageError, match="missing file"):
        load_fixture_brief(tmp_path / "nope.json")


def test_invalid_fixture_is_a_storage_error(tmp_path):
    broken = tmp_path / "brief.json"
    broken.write_text('{"product_name": "x"}')

    with pytest.raises(StorageError, match="invalid Brief"):
        load_fixture_brief(broken)
