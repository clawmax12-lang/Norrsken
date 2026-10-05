import pytest

from preflight.errors import PreflightValidationError
from preflight.planning.archetypes import ARCHETYPES, archetypes_for


def test_archetype_names_are_distinct() -> None:
    assert len({a.name for a in ARCHETYPES}) == len(ARCHETYPES)


def test_first_archetypes_are_assigned_in_fixed_order() -> None:
    assert [a.name for a in archetypes_for(3)] == [
        "pain relief",
        "business outcome",
        "speed and ease",
    ]


def test_the_three_launch_hypotheses_are_different_selling_angles() -> None:
    by_name = {a.name: a.guidance.casefold() for a in archetypes_for(3)}
    assert "quick or effortless" in by_name["speed and ease"]
    assert "what the audience gains" in by_name["business outcome"]
    assert "problem the audience has today" in by_name["pain relief"]


def test_every_launch_angle_builds_to_the_brief_s_proof() -> None:
    for archetype in archetypes_for(3):
        assert "number" in archetype.guidance


def test_every_angle_is_capped_by_what_the_brief_supports() -> None:
    by_name = {a.name: a.guidance.casefold() for a in archetypes_for(3)}
    assert "brief supports" in by_name["speed and ease"]
    assert "brief allows" in by_name["business outcome"]


@pytest.mark.parametrize("count", [0, -1, len(ARCHETYPES) + 1])
def test_unsupported_counts_are_rejected(count: int) -> None:
    with pytest.raises(PreflightValidationError, match="distinct hypotheses"):
        archetypes_for(count)


def test_no_archetype_asks_for_invented_proof() -> None:
    forbidden = ("testimonial", "review", "customers", "statistic", "social proof")
    assert not any(word in a.guidance.lower() for a in ARCHETYPES for word in forbidden)
