import pytest

from preflight.errors import PreflightValidationError
from preflight.planning.archetypes import ARCHETYPES, archetypes_for


def test_archetype_names_are_distinct() -> None:
    assert len({a.name for a in ARCHETYPES}) == len(ARCHETYPES)


def test_first_archetypes_are_assigned_in_fixed_order() -> None:
    assert [a.name for a in archetypes_for(3)] == [
        "problem first",
        "outcome first",
        "product first",
    ]


def test_problem_first_opens_on_the_problem_then_the_product() -> None:
    guidance = next(a.guidance for a in ARCHETYPES if a.name == "problem first").casefold()
    assert "audience" in guidance and "product name" in guidance
    assert "yes/no" in guidance
    assert "not a label of a screenshot" in guidance
    assert "thank-you" in guidance


def test_the_three_launch_hypotheses_open_on_different_hooks() -> None:
    by_name = {a.name: a.guidance.casefold() for a in archetypes_for(3)}
    assert "problem" in by_name["problem first"]
    assert "one-liner says the product achieves" in by_name["outcome first"]
    assert "product name and the one-liner" in by_name["product first"]


@pytest.mark.parametrize("count", [0, -1, len(ARCHETYPES) + 1])
def test_unsupported_counts_are_rejected(count: int) -> None:
    with pytest.raises(PreflightValidationError, match="distinct hypotheses"):
        archetypes_for(count)


def test_no_archetype_asks_for_invented_proof() -> None:
    forbidden = ("testimonial", "review", "customers", "statistic", "social proof")
    assert not any(word in a.guidance.lower() for a in ARCHETYPES for word in forbidden)
