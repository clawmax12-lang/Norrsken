from preflight.finalization.compare import compare
from tests.factories import make_result

STRONG_OPEN = (0.9, 0.9, 0.9) + (0.6,) * 12
WEAK_OPEN = (0.3, 0.3, 0.3) + (0.6,) * 12


def test_a_final_that_scores_lower_recommends_the_original() -> None:
    comparison = compare(make_result("B", values=STRONG_OPEN), make_result("B", values=WEAK_OPEN))

    assert (comparison.original_hook, comparison.final_hook) == (0.9, 0.3)
    assert comparison.final < comparison.original
    assert comparison.keep_original


def test_a_final_that_scores_higher_is_kept() -> None:
    comparison = compare(make_result("B", values=WEAK_OPEN), make_result("B", values=STRONG_OPEN))

    assert comparison.original == 0.54 and comparison.final == 0.66
    assert not comparison.keep_original
