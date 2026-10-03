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


@pytest.mark.parametrize("count", [0, -1, len(ARCHETYPES) + 1])
def test_unsupported_counts_are_rejected(count: int) -> None:
    with pytest.raises(PreflightValidationError, match="distinct hypotheses"):
        archetypes_for(count)


def test_no_archetype_asks_for_invented_proof() -> None:
    forbidden = ("testimonial", "review", "customers", "statistic", "social proof")
    assert not any(word in a.guidance.lower() for a in ARCHETYPES for word in forbidden)
