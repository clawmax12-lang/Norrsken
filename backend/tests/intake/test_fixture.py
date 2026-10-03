"""The tablehopp fixture holds only known facts; everything else is a placeholder."""

from pathlib import Path

import pytest

from preflight.contracts import Goal
from preflight.errors import StorageError
from preflight.intake import load_fixture_brief

TABLEHOPP = Path(__file__).resolve().parents[3] / "fixtures" / "tablehopp" / "brief.json"
PLACEHOLDER = "PLACEHOLDER: William to supply"


def test_tablehopp_fixture_validates_against_the_brief_contract():
    brief = load_fixture_brief(TABLEHOPP)

    assert brief.product_name == "tablehopp"
    assert brief.goal_note == "Launching 7 Oct"


def test_every_other_text_field_is_a_placeholder():
    brief = load_fixture_brief(TABLEHOPP)

    assert brief.one_liner == PLACEHOLDER
    assert brief.audience == PLACEHOLDER


def test_screenshots_are_placeholders_not_files():
    brief = load_fixture_brief(TABLEHOPP)

    assert len(brief.screenshots) == 3
    assert all(path.startswith(PLACEHOLDER) for path in brief.screenshots)
    assert not any(Path(path).exists() for path in brief.screenshots)


def test_goal_is_the_one_value_that_cannot_be_a_placeholder():
    assert load_fixture_brief(TABLEHOPP).goal is Goal.UNDERSTAND


def test_missing_fixture_is_a_storage_error(tmp_path):
    with pytest.raises(StorageError, match="missing file"):
        load_fixture_brief(tmp_path / "nope.json")


def test_invalid_fixture_is_a_storage_error(tmp_path):
    broken = tmp_path / "brief.json"
    broken.write_text('{"product_name": "x"}')

    with pytest.raises(StorageError, match="invalid Brief"):
        load_fixture_brief(broken)
