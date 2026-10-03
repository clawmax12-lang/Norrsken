"""Pick the moments of a video worth explaining from what the simulators reported.

Selection uses only what simulators returned: reported hold/drop events, ranked by the
primary series at that second, and, when fewer than two distinct moments were reported,
the strongest point and the steepest drop of the primary series itself. Nothing is invented.
"""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from enum import StrEnum
from itertools import pairwise

from preflight.contracts import CreativeConcept, EventType, SimulationResult, SimulatorName
from preflight.errors import PreflightValidationError

MIN_MOMENTS = 2
MAX_MOMENTS = 4

_SIMULATOR_ORDER = {name: position for position, name in enumerate(SimulatorName)}

type Sample = tuple[float, float]


class MomentKind(StrEnum):
    """What a moment is; the value is its headline in a reason."""

    HOLD = "Hold"
    DROP = "Drop"
    PEAK = "Series peak"
    STEEPEST_DROP = "Steepest drop"
    LOW = "Series low"


_REPORTED_KINDS = {EventType.HOLD: MomentKind.HOLD, EventType.DROP: MomentKind.DROP}


@dataclass(frozen=True)
class Moment:
    """One second of a video with a factual ``detail``, attributed to one simulator.

    ``strength`` is the simulator's primary series at ``t``; it ranks moments of one kind.
    """

    t: float
    kind: MomentKind
    detail: str
    simulator: SimulatorName
    strength: float

    @property
    def reported(self) -> bool:
        """True for a hold/drop event the simulator reported, false when derived from the series."""
        return self.kind in (MomentKind.HOLD, MomentKind.DROP)

    @property
    def second(self) -> int:
        """The whole second the moment falls in; reasons must be at distinct seconds."""
        return int(self.t)

    def tie_break(self) -> tuple[float, int, str]:
        """A total order for moments of equal strength, so selection is deterministic."""
        return (self.t, _SIMULATOR_ORDER[self.simulator], self.detail)


def variant_results(
    concept: CreativeConcept, results: Sequence[SimulationResult]
) -> tuple[SimulationResult, ...]:
    """The results for ``concept``'s variant, in a fixed simulator order.

    Raises:
        PreflightValidationError: If no result covers the variant or one has no samples
            inside the concept's video.
    """
    own = sorted(
        (result for result in results if result.variant_id == concept.variant_id),
        key=lambda result: _SIMULATOR_ORDER[result.simulator],
    )
    if not own:
        raise PreflightValidationError(f"no simulation result for variant {concept.variant_id}")
    for result in own:
        _samples(result, concept.duration_s)
    return tuple(own)


def select_moments(results: Sequence[SimulationResult], duration_s: float) -> tuple[Moment, ...]:
    """Choose 2-4 moments at distinct seconds, sorted by time.

    Reported events come first: one drop is always kept when any exists, then holds from
    strongest down, then further drops. If that yields fewer than two moments the
    primary series fills the gap.

    Raises:
        PreflightValidationError: If the series is too short to give two distinct seconds.
    """
    holds, drops = _reported_moments(results, duration_s)
    picked = _first_at_distinct_seconds([*drops[:1], *holds, *drops[1:]])
    if len(picked) < MIN_MOMENTS:
        picked = _first_at_distinct_seconds([*picked, *series_moments(results[0], duration_s)])
    if len(picked) < MIN_MOMENTS:
        raise PreflightValidationError("too few distinct seconds to explain this variant")
    return tuple(sorted(picked, key=lambda moment: moment.t))


def weakest_moment(results: Sequence[SimulationResult], duration_s: float) -> Moment:
    """The weakest moment: the lowest reported drop, else the series' steepest drop or low."""
    _, drops = _reported_moments(results, duration_s)
    return drops[0] if drops else series_moments(results[0], duration_s)[1]


def series_moments(result: SimulationResult, duration_s: float) -> tuple[Moment, Moment]:
    """The primary series' strongest point and its steepest drop (lowest point if it never falls).

    For equal values the strongest point is the earliest and the lowest the latest, so even
    a flat series yields two distinct seconds.
    """
    samples = _samples(result, duration_s)
    peak_t, peak = max(samples, key=lambda sample: (sample[1], -sample[0]))
    strongest = Moment(
        peak_t, MomentKind.PEAK, f"primary series peaks at {peak:.2f}", result.simulator, peak
    )
    return strongest, _weakest_point(result.simulator, samples)


def _weakest_point(simulator: SimulatorName, samples: Sequence[Sample]) -> Moment:
    steps = [(after[1] - before[1], before, after) for before, after in pairwise(samples)]
    if steps:
        delta, before, after = min(steps, key=lambda step: (step[0], step[2][0]))
        if delta < 0:
            detail = f"primary series falls from {before[1]:.2f} to {after[1]:.2f}"
            return Moment(after[0], MomentKind.STEEPEST_DROP, detail, simulator, after[1])
    low_t, low = min(samples, key=lambda sample: (sample[1], -sample[0]))
    return Moment(low_t, MomentKind.LOW, f"primary series is lowest at {low:.2f}", simulator, low)


def _reported_moments(
    results: Sequence[SimulationResult], duration_s: float
) -> tuple[list[Moment], list[Moment]]:
    """Reported (holds, drops) inside the video: holds strongest first, drops weakest first."""
    holds: list[Moment] = []
    drops: list[Moment] = []
    for result in results:
        samples = _samples(result, duration_s)
        for event in result.events:
            if event.t > duration_s:
                continue
            kind = _REPORTED_KINDS[event.type]
            moment = Moment(
                event.t, kind, event.label, result.simulator, _value_at(samples, event.t)
            )
            (holds if kind is MomentKind.HOLD else drops).append(moment)
    holds.sort(key=lambda moment: (-moment.strength, *moment.tie_break()))
    drops.sort(key=lambda moment: (moment.strength, *moment.tie_break()))
    return holds, drops


def _first_at_distinct_seconds(candidates: Iterable[Moment]) -> list[Moment]:
    picked: list[Moment] = []
    seconds: set[int] = set()
    for moment in candidates:
        if len(picked) == MAX_MOMENTS:
            break
        if moment.second not in seconds:
            picked.append(moment)
            seconds.add(moment.second)
    return picked


def _samples(result: SimulationResult, duration_s: float) -> list[Sample]:
    """The primary series as (second, value) pairs that lie within the video."""
    values = result.series[result.primary_series]
    samples = [
        (t, value) for t, value in zip(result.timestamps_s, values, strict=True) if t <= duration_s
    ]
    if not samples:
        raise PreflightValidationError(
            f"{result.simulator.value} has no samples inside the video "
            f"for variant {result.variant_id}"
        )
    return samples


def _value_at(samples: Sequence[Sample], t: float) -> float:
    """The primary series at the sample nearest to ``t`` (the earlier one on a tie)."""
    return min(samples, key=lambda sample: (abs(sample[0] - t), sample[0]))[1]
