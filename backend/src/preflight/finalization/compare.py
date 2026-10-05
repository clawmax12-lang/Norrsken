"""The finished cut's pretest against the original winner's: Finish must not make it worse."""

from preflight.contracts import SimulationResult
from preflight.contracts.finalization import FinalComparison

HOOK_SECONDS = 3.0


def compare(original: SimulationResult, final: SimulationResult) -> FinalComparison:
    """Mean of each result's primary series, over the whole video and its first seconds."""
    return FinalComparison(
        original=_mean(original),
        final=_mean(final),
        original_hook=_mean(original, until=HOOK_SECONDS),
        final_hook=_mean(final, until=HOOK_SECONDS),
        keep_original=_mean(final) < _mean(original),
    )


def _mean(result: SimulationResult, until: float | None = None) -> float:
    values = [
        value
        for t, value in zip(result.timestamps_s, result.series[result.primary_series], strict=True)
        if until is None or t < until
    ]
    return round(sum(values) / len(values), 4) if values else 0.0
