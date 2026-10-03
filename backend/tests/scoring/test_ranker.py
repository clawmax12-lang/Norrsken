import itertools
import math

import pytest
from hypothesis import given
from hypothesis import strategies as st

from preflight.contracts import Confidence, SimulationResult, SimulatorName
from preflight.errors import PreflightValidationError
from preflight.scoring import score_and_rank
from tests.factories import make_result

TRIBE = SimulatorName.TRIBE_V2
GEMINI = SimulatorName.GEMINI_PANEL


def result(
    variant: str, level: float, simulator: SimulatorName = GEMINI, **overrides: object
) -> SimulationResult:
    """A result whose primary series is the constant ``level``."""
    return make_result(variant, simulator, (level,) * 15, **overrides)


def test_ranks_by_mean_of_primary_series_with_min_max_scores() -> None:
    results = [result("A", 0.2), result("B", 0.8), result("C", 0.5)]

    ranking = score_and_rank(results)

    assert ranking.order == ("B", "C", "A")
    assert ranking.scores == pytest.approx({"A": 0.0, "B": 1.0, "C": 0.5})
    assert ranking.per_simulator == {GEMINI: ranking.scores}


def test_sub_score_is_the_mean_not_the_peak() -> None:
    spiky = make_result("A", GEMINI, (1.0,) + (0.0,) * 14)
    steady = make_result("B", GEMINI, (0.2,) * 15)

    assert score_and_rank([spiky, steady]).order == ("B", "A")


def test_equal_variants_all_score_one_half_and_tie_breaks_on_lower_id() -> None:
    ranking = score_and_rank([result("C", 0.4), result("A", 0.4), result("B", 0.4)])

    assert ranking.order == ("A", "B", "C")
    assert set(ranking.scores.values()) == {0.5}


def test_a_tie_for_first_goes_to_the_lower_variant_id() -> None:
    ranking = score_and_rank([result("B", 0.9), result("A", 0.9), result("C", 0.1)])

    assert ranking.order == ("A", "B", "C")


def test_single_variant_is_valid_and_has_low_confidence() -> None:
    ranking = score_and_rank([result("A", 0.7, TRIBE), result("A", 0.6, GEMINI)])

    assert ranking.order == ("A",)
    assert ranking.scores == {"A": 0.5}
    assert ranking.confidence is Confidence.LOW


def test_agreeing_simulators_give_high_confidence() -> None:
    results = [
        result("A", 0.3, TRIBE),
        result("B", 0.9, TRIBE),
        result("A", 0.1, GEMINI),
        result("B", 0.6, GEMINI),
    ]

    ranking = score_and_rank(results)

    assert ranking.order == ("B", "A")
    assert ranking.confidence is Confidence.HIGH
    assert set(ranking.per_simulator) == {TRIBE, GEMINI}


def test_disagreeing_simulators_give_low_confidence() -> None:
    results = [
        result("A", 0.9, TRIBE),
        result("B", 0.1, TRIBE),
        result("A", 0.4, GEMINI),
        result("B", 0.6, GEMINI),
    ]

    ranking = score_and_rank(results)

    assert ranking.confidence is Confidence.LOW
    assert ranking.scores == pytest.approx({"A": 0.5, "B": 0.5})
    assert ranking.order == ("A", "B")


def test_a_simulator_that_cannot_tell_variants_apart_does_not_confirm_the_winner() -> None:
    results = [
        result("A", 0.2, TRIBE),
        result("B", 0.8, TRIBE),
        result("A", 0.5, GEMINI),
        result("B", 0.5, GEMINI),
    ]

    ranking = score_and_rank(results)

    assert ranking.order == ("B", "A")
    assert ranking.confidence is Confidence.LOW
    assert "gemini_panel scored every variant the same" in ranking.rule


def test_single_simulator_rule_says_so() -> None:
    ranking = score_and_rank([result("A", 0.2), result("B", 0.8)])

    assert ranking.confidence is Confidence.LOW
    assert "Single-simulator run" in ranking.rule


def test_rule_states_the_method_and_that_it_is_not_a_success_predictor() -> None:
    rule = score_and_rank([result("A", 0.2), result("B", 0.8)]).rule

    assert "mean of its primary series" in rule
    assert "min-max normalised" in rule
    assert "lower variant id" in rule
    assert "not a validated predictor" in rule


def test_weights_are_renormalised_and_change_the_outcome() -> None:
    results = [
        result("A", 0.9, TRIBE),
        result("B", 0.1, TRIBE),
        result("A", 0.4, GEMINI),
        result("B", 0.6, GEMINI),
    ]

    ranking = score_and_rank(results, weights={TRIBE: 3.0, GEMINI: 1.0})

    assert ranking.order == ("A", "B")
    assert ranking.scores == pytest.approx({"A": 0.75, "B": 0.25})
    assert "gemini_panel 0.25, tribe_v2 0.75" in ranking.rule


def test_zero_weight_removes_a_simulators_influence() -> None:
    results = [
        result("A", 0.9, TRIBE),
        result("B", 0.1, TRIBE),
        result("A", 0.4, GEMINI),
        result("B", 0.6, GEMINI),
    ]

    ranking = score_and_rank(results, weights={TRIBE: 0.0})

    assert ranking.order == ("B", "A")


@pytest.mark.parametrize(
    "weights", [{GEMINI: -1.0}, {GEMINI: math.nan}, {GEMINI: math.inf}, {GEMINI: 0.0}]
)
def test_invalid_weights_are_rejected(weights: dict[SimulatorName, float]) -> None:
    with pytest.raises(PreflightValidationError, match="weights"):
        score_and_rank([result("A", 0.2), result("B", 0.8)], weights=weights)


def test_weights_of_simulators_that_did_not_run_are_ignored() -> None:
    ranking = score_and_rank([result("A", 0.2), result("B", 0.8)], weights={TRIBE: -5.0})

    assert ranking.order == ("B", "A")


def test_a_simulator_missing_a_variant_is_dropped_and_named() -> None:
    results = [
        result("A", 0.2, GEMINI),
        result("B", 0.8, GEMINI),
        result("A", 0.9, TRIBE),
    ]

    ranking = score_and_rank(results)

    assert ranking.order == ("B", "A")
    assert set(ranking.per_simulator) == {GEMINI}
    assert "Dropped from scoring: tribe_v2 has no result for variant(s) B" in ranking.rule


def test_no_simulator_covering_every_variant_is_an_error() -> None:
    results = [result("A", 0.2, GEMINI), result("B", 0.8, TRIBE)]

    with pytest.raises(PreflightValidationError, match="every variant"):
        score_and_rank(results)


def test_excluded_variants_are_passed_through_sorted() -> None:
    ranking = score_and_rank(
        [result("A", 0.2), result("B", 0.8)], excluded={"D": "render failed", "C": "no video"}
    )

    assert ranking.excluded == {"C": "no video", "D": "render failed"}
    assert list(ranking.excluded) == ["C", "D"]


def test_a_variant_cannot_be_both_ranked_and_excluded() -> None:
    with pytest.raises(PreflightValidationError, match="excluded"):
        score_and_rank([result("A", 0.2), result("B", 0.8)], excluded={"B": "render failed"})


def test_no_results_is_an_error() -> None:
    with pytest.raises(PreflightValidationError, match="without simulation results"):
        score_and_rank([])


def test_duplicate_result_for_a_variant_and_simulator_is_an_error() -> None:
    with pytest.raises(PreflightValidationError, match="duplicate result for variant A"):
        score_and_rank([result("A", 0.2), result("A", 0.3)])


def test_results_for_different_videos_of_one_variant_are_an_error() -> None:
    results = [result("A", 0.2, TRIBE), result("A", 0.3, GEMINI, video_sha256="b" * 64)]

    with pytest.raises(PreflightValidationError, match="different videos"):
        score_and_rank(results)


def test_empty_primary_series_is_an_error() -> None:
    empty = make_result("A", GEMINI, ())

    with pytest.raises(PreflightValidationError, match="empty primary series"):
        score_and_rank([empty])


@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf])
def test_non_finite_values_are_an_error(bad: float) -> None:
    # model_construct skips the contract's own validation: scoring must not trust it blindly.
    broken = SimulationResult.model_construct(
        **{**result("A", 0.5).__dict__, "series": {"signal": (0.5, bad)}}
    )

    with pytest.raises(PreflightValidationError, match="non-finite"):
        score_and_rank([broken])


def test_permuting_the_input_gives_byte_identical_output() -> None:
    results = [
        result("A", 0.31, TRIBE),
        result("B", 0.77, TRIBE),
        result("C", 0.52, TRIBE),
        result("A", 0.44, GEMINI),
        result("B", 0.12, GEMINI),
        result("C", 0.9, GEMINI),
    ]
    expected = score_and_rank(results).model_dump_json()

    for permutation in itertools.permutations(results):
        assert score_and_rank(permutation).model_dump_json() == expected


series_values = st.lists(st.floats(0.0, 1.0), min_size=1, max_size=15)


@st.composite
def run_results(draw: st.DrawFn) -> list[SimulationResult]:
    variants = draw(st.lists(st.sampled_from("ABCDE"), min_size=1, max_size=5, unique=True))
    simulators = draw(st.lists(st.sampled_from(SimulatorName), min_size=1, max_size=2, unique=True))
    return [
        make_result(variant, simulator, tuple(draw(series_values)))
        for variant in variants
        for simulator in simulators
    ]


@given(results=run_results(), data=st.data())
def test_ranking_invariants_hold_for_any_run(
    results: list[SimulationResult], data: st.DataObject
) -> None:
    shuffled = data.draw(st.permutations(results))

    ranking = score_and_rank(results)

    assert score_and_rank(shuffled).model_dump_json() == ranking.model_dump_json()
    assert sorted(ranking.order) == sorted({r.variant_id for r in results})
    assert all(0.0 <= score <= 1.0 for score in ranking.scores.values())
    assert ranking.scores[ranking.order[0]] == max(ranking.scores.values())
    assert [ranking.scores[v] for v in ranking.order] == sorted(
        ranking.scores.values(), reverse=True
    )
