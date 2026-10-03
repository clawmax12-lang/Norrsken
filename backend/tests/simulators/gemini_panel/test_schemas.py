import pytest

from preflight.simulators.gemini_panel.schemas import (
    PersonaRating,
    parse_timestamp,
    rating_problems,
)
from tests.simulators.gemini_panel.fakes import rating_json


@pytest.mark.parametrize(
    ("text", "expected"),
    [("00:00", 0), ("00:07", 7), ("0:14", 14), ("01:05", 65), (" 00:03 ", 3)],
)
def test_parse_timestamp_accepts_mm_ss(text: str, expected: int) -> None:
    assert parse_timestamp(text) == expected


@pytest.mark.parametrize("text", ["7", "00:7", "00:60", "abc", "1:2:3", "", "-0:05"])
def test_parse_timestamp_rejects_everything_else(text: str) -> None:
    assert parse_timestamp(text) is None


def test_complete_rating_has_no_problems() -> None:
    rating = PersonaRating.model_validate_json(rating_json(moments=[("00:15", "drop", "end card")]))

    assert rating_problems(rating, 15) == []


def test_missing_and_duplicate_seconds_are_reported() -> None:
    rating = PersonaRating.model_validate_json(rating_json(seconds=14))

    (problem,) = rating_problems(rating, 15)

    assert "exactly one rating for each of 0..14" in problem


def test_moment_outside_the_video_or_malformed_is_reported() -> None:
    rating = PersonaRating.model_validate_json(
        rating_json(moments=[("00:16", "hold", "x"), ("5s", "drop", "y")])
    )

    problems = rating_problems(rating, 15)

    assert len(problems) == 2
    assert '"00:16"' in problems[0] and '"5s"' in problems[1]


def test_ratings_outside_zero_to_one_are_rejected_by_the_schema() -> None:
    with pytest.raises(ValueError, match="less than or equal to 1"):
        PersonaRating.model_validate_json(rating_json(goal_fit=lambda s: 1.5))
