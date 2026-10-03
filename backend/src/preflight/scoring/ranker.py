"""FR-05: turn simulator results into one deterministic ranking (PRD §8 FR-05, §10.3).

The rule is documented in ``docs/backend/ARCHITECTURE.md`` ("Scoring rule") and restated in
``Ranking.rule`` so every report carries the rule that produced it. Scores rank the variants
of one run against each other. They are not a validated predictor of launch success.

Everything here is a pure function of its inputs. Determinism is a requirement, so every
mapping is built in sorted order: the same results in any input order serialise to the same
bytes.
"""

import math
from collections import defaultdict
from collections.abc import Mapping, Sequence

from preflight.contracts import Confidence, Ranking, SimulationResult, SimulatorName, VariantId
from preflight.errors import PreflightValidationError

NEUTRAL_SCORE = 0.5
DEFAULT_WEIGHT = 1.0

type SubScores = dict[VariantId, float]

_DISCLAIMER = (
    "Scores rank these variants against each other; "
    "they are not a validated predictor of launch success."
)


def score_and_rank(
    results: Sequence[SimulationResult],
    *,
    weights: Mapping[SimulatorName, float] | None = None,
    excluded: Mapping[str, str] | None = None,
) -> Ranking:
    """Rank the variants in ``results`` by their combined, normalised simulator sub-scores.

    A simulator takes part only when it produced a result for every ranked variant, so a
    missing result can never be mistaken for a bad one; dropped simulators are named in
    ``Ranking.rule``. A single ranked variant is valid (``order`` has length one); downstream
    code then has no runner-up.

    Args:
        results: One result per (variant, simulator), all for the same rendered videos.
        weights: Relative importance per simulator; unlisted simulators weigh 1.0. Weights
            are renormalised over the simulators that take part.
        excluded: Variants left out of the run (for example a failed render) with the reason;
            passed through to ``Ranking.excluded``.

    Returns:
        The ranking: order by score descending, ties to the lower variant id.

    Raises:
        PreflightValidationError: On no results, duplicates, non-finite or empty series,
            results for different videos of one variant, a variant that is both ranked and
            excluded, invalid weights, or no simulator covering every variant.
    """
    means = _mean_primary_series(results)
    ranked_variants = sorted({variant for per_variant in means.values() for variant in per_variant})
    skipped = dict(sorted((excluded or {}).items()))
    _reject_excluded_results(ranked_variants, skipped)

    usable, dropped = _split_by_coverage(means, ranked_variants)
    if not usable:
        raise PreflightValidationError(
            "no simulator produced a result for every variant: " + _describe_dropped(dropped)
        )
    simulator_weights = _resolve_weights(usable, weights)
    normalised = {simulator: _min_max(scores) for simulator, scores in usable.items()}
    scores = _weighted_mean(normalised, simulator_weights)
    order = tuple(sorted(scores, key=lambda variant: (-scores[variant], variant)))
    return Ranking(
        order=order,
        scores=scores,
        per_simulator=normalised,
        confidence=_confidence(order[0], normalised),
        rule=_describe_rule(simulator_weights, normalised, dropped),
        excluded=skipped,
    )


def _mean_primary_series(
    results: Sequence[SimulationResult],
) -> dict[SimulatorName, SubScores]:
    """Validate ``results`` and return each simulator's raw mean per variant, sorted."""
    if not results:
        raise PreflightValidationError("cannot rank without simulation results")
    _require_one_video_per_variant(results)
    means: defaultdict[SimulatorName, SubScores] = defaultdict(dict)
    for result in results:
        if result.variant_id in means[result.simulator]:
            raise PreflightValidationError(
                f"duplicate result for variant {result.variant_id} from {result.simulator.value}"
            )
        means[result.simulator][result.variant_id] = _mean_of_primary_series(result)
    return {simulator: dict(sorted(means[simulator].items())) for simulator in sorted(means)}


def _mean_of_primary_series(result: SimulationResult) -> float:
    values = result.series[result.primary_series]
    if not values:
        raise PreflightValidationError(
            f"empty primary series for variant {result.variant_id} from {result.simulator.value}"
        )
    if not all(math.isfinite(value) for value in values):
        raise PreflightValidationError(
            f"non-finite primary series for variant {result.variant_id} "
            f"from {result.simulator.value}"
        )
    return math.fsum(values) / len(values)


def _require_one_video_per_variant(results: Sequence[SimulationResult]) -> None:
    """Every simulator of a variant must have watched the same rendered file."""
    hashes: defaultdict[VariantId, set[str]] = defaultdict(set)
    for result in results:
        hashes[result.variant_id].add(result.video_sha256)
    mismatched = sorted(variant for variant, seen in hashes.items() if len(seen) > 1)
    if mismatched:
        raise PreflightValidationError(
            f"results for variant(s) {', '.join(mismatched)} come from different videos"
        )


def _reject_excluded_results(ranked: Sequence[VariantId], excluded: Mapping[str, str]) -> None:
    both = [variant for variant in ranked if variant in excluded]
    if both:
        raise PreflightValidationError(
            f"variant(s) {', '.join(both)} are excluded but have simulation results"
        )


def _split_by_coverage(
    means: Mapping[SimulatorName, SubScores], ranked: Sequence[VariantId]
) -> tuple[dict[SimulatorName, SubScores], dict[SimulatorName, list[VariantId]]]:
    """Separate simulators covering every ranked variant from those missing some."""
    usable: dict[SimulatorName, SubScores] = {}
    dropped: dict[SimulatorName, list[VariantId]] = {}
    for simulator, scores in means.items():
        missing = [variant for variant in ranked if variant not in scores]
        if missing:
            dropped[simulator] = missing
        else:
            usable[simulator] = scores
    return usable, dropped


def _resolve_weights(
    simulators: Mapping[SimulatorName, SubScores],
    weights: Mapping[SimulatorName, float] | None,
) -> dict[SimulatorName, float]:
    resolved = {
        simulator: (weights or {}).get(simulator, DEFAULT_WEIGHT) for simulator in simulators
    }
    if any(not math.isfinite(weight) or weight < 0 for weight in resolved.values()):
        raise PreflightValidationError("simulator weights must be finite and not negative")
    if sum(resolved.values()) <= 0:
        raise PreflightValidationError("simulator weights must not all be zero")
    return resolved


def _min_max(scores: SubScores) -> SubScores:
    """Scale to [0, 1] across variants; when all are equal nobody is better, so 0.5."""
    low, high = min(scores.values()), max(scores.values())
    if low == high:
        return dict.fromkeys(scores, NEUTRAL_SCORE)
    return {variant: (score - low) / (high - low) for variant, score in scores.items()}


def _weighted_mean(
    normalised: Mapping[SimulatorName, SubScores], weights: Mapping[SimulatorName, float]
) -> SubScores:
    """Weighted mean per variant, summed in a fixed simulator order so it stays bit-stable.

    Dividing by the sum of the same weights, in the same order, guarantees the result never
    leaves [0, 1] through rounding.
    """
    total_weight = sum(weights[simulator] for simulator in normalised)
    variants = sorted(next(iter(normalised.values())))
    return {
        variant: sum(
            weights[simulator] * normalised[simulator][variant] for simulator in normalised
        )
        / total_weight
        for variant in variants
    }


def _leader(scores: SubScores) -> VariantId | None:
    """The variant a simulator prefers, or ``None`` when it sees no difference between them."""
    if len(set(scores.values())) == 1:
        return None
    return min(scores, key=lambda variant: (-scores[variant], variant))


def _confidence(winner: VariantId, normalised: Mapping[SimulatorName, SubScores]) -> Confidence:
    """High only when two or more simulators each independently prefer the winner."""
    if len(normalised) < 2:
        return Confidence.LOW
    agree = all(_leader(scores) == winner for scores in normalised.values())
    return Confidence.HIGH if agree else Confidence.LOW


def _describe_dropped(dropped: Mapping[SimulatorName, Sequence[VariantId]]) -> str:
    return "; ".join(
        f"{simulator.value} has no result for variant(s) {', '.join(missing)}"
        for simulator, missing in dropped.items()
    )


def _describe_rule(
    weights: Mapping[SimulatorName, float],
    normalised: Mapping[SimulatorName, SubScores],
    dropped: Mapping[SimulatorName, Sequence[VariantId]],
) -> str:
    """State, for this particular run, exactly how the order and confidence came about."""
    total_weight = sum(weights.values())
    shares = ", ".join(
        f"{simulator.value} {weight / total_weight:.2f}" for simulator, weight in weights.items()
    )
    sentences = [
        "Per simulator, a variant's sub-score is the mean of its primary series, "
        "min-max normalised across the variants (0.5 for every variant when all are equal).",
        f"Score is the weighted mean over the simulators that covered every variant ({shares}); "
        "ties go to the lower variant id.",
        _describe_confidence_rule(normalised),
    ]
    flat = [simulator.value for simulator, scores in normalised.items() if _leader(scores) is None]
    if flat:
        sentences.append(
            f"{', '.join(flat)} scored every variant the same, so it cannot confirm the winner."
        )
    if dropped:
        sentences.append(f"Dropped from scoring: {_describe_dropped(dropped)}.")
    sentences.append(_DISCLAIMER)
    return " ".join(sentences)


def _describe_confidence_rule(normalised: Mapping[SimulatorName, SubScores]) -> str:
    if len(normalised) < 2:
        return (
            "Single-simulator run: confidence is low because no second simulator "
            "cross-checks the order."
        )
    return (
        "Confidence is high only when at least two simulators each rank the same variant first; "
        "otherwise it is low."
    )
