"""Pure translation of per-persona answers into one shared ``SimulationResult`` (FR-04).

Kept free of I/O so the aggregation rules are testable and deterministic: the same persona
answers always give the same result.
"""

from dataclasses import dataclass
from statistics import fmean

from preflight.contracts import EventType, SimEvent, SimulationResult, SimulatorName

from .schemas import MomentFlag, Persona, PersonaRating, parse_timestamp

GOAL_FIT = "goal_fit"
CLARITY = "clarity"
MIN_AGREEING_PERSONAS = 2
MERGE_WINDOW_S = 1.0


@dataclass(frozen=True)
class FlaggedMoment:
    """A hold or drop one persona flagged, with the persona's 1-based position."""

    persona: int
    t: float
    kind: EventType
    label: str


@dataclass(frozen=True)
class PersonaReading:
    """A validated persona answer, ordered by second."""

    index: int
    persona: Persona
    goal_fit: tuple[float, ...]
    clarity: tuple[float, ...]
    moments: tuple[FlaggedMoment, ...]


def reading_from(index: int, persona: Persona, rating: PersonaRating) -> PersonaReading:
    """Order a checked ``rating`` by second and convert its ``mm:ss`` moments to seconds.

    ``rating`` must already satisfy :func:`~.schemas.rating_problems`.
    """
    ordered = sorted(rating.seconds, key=lambda entry: entry.second)
    moments = tuple(_flag(index, moment) for moment in rating.moments)
    return PersonaReading(
        index=index,
        persona=persona,
        goal_fit=tuple(entry.goal_fit for entry in ordered),
        clarity=tuple(entry.clarity for entry in ordered),
        moments=moments,
    )


def _flag(index: int, moment: MomentFlag) -> FlaggedMoment:
    seconds = parse_timestamp(moment.timestamp)
    if seconds is None:
        raise ValueError(f"unchecked rating: bad timestamp {moment.timestamp!r}")
    return FlaggedMoment(index, float(seconds), moment.kind, moment.label)


def merge_moments(readings: list[PersonaReading]) -> tuple[SimEvent, ...]:
    """Events for moments of one kind that at least two personas flagged within one second.

    Flags are grouped greedily from the earliest: a flag joins the open group while it is
    within ``MERGE_WINDOW_S`` of the group's first flag. The event sits at the group's mean
    time and carries the label of its first flag.
    """
    flags = [moment for reading in readings for moment in reading.moments]
    events = [
        SimEvent(t=fmean(flag.t for flag in group), type=kind, label=group[0].label)
        for kind in EventType
        for group in _groups(sorted((f for f in flags if f.kind is kind), key=_by_time))
        if len({flag.persona for flag in group}) >= MIN_AGREEING_PERSONAS
    ]
    return tuple(sorted(events, key=lambda event: (event.t, event.type.value)))


def _by_time(flag: FlaggedMoment) -> tuple[float, int]:
    return (flag.t, flag.persona)


def _groups(flags: list[FlaggedMoment]) -> list[list[FlaggedMoment]]:
    groups: list[list[FlaggedMoment]] = []
    for flag in flags:
        if groups and flag.t - groups[-1][0].t <= MERGE_WINDOW_S:
            groups[-1].append(flag)
        else:
            groups.append([flag])
    return groups


def build_series(readings: list[PersonaReading]) -> dict[str, tuple[float, ...]]:
    """``goal_fit`` and ``clarity`` as persona means, plus each persona's own ``goal_fit``."""
    series = {
        GOAL_FIT: _mean_series([r.goal_fit for r in readings]),
        CLARITY: _mean_series([r.clarity for r in readings]),
    }
    series.update({f"persona_{r.index}_goal_fit": r.goal_fit for r in readings})
    return series


def _mean_series(per_persona: list[tuple[float, ...]]) -> tuple[float, ...]:
    return tuple(fmean(values) for values in zip(*per_persona, strict=True))


def to_result(
    readings: list[PersonaReading],
    *,
    variant_id: str,
    video_sha256: str,
    duration_s: float,
    version: str,
    meta: dict[str, object],
) -> SimulationResult:
    """The panel's single ``SimulationResult``: 1 Hz samples starting at second 0."""
    series = build_series(readings)
    return SimulationResult(
        variant_id=variant_id,
        simulator=SimulatorName.GEMINI_PANEL,
        version=version,
        hz=1.0,
        video_sha256=video_sha256,
        duration_s=duration_s,
        timestamps_s=tuple(float(second) for second in range(len(series[GOAL_FIT]))),
        series=series,
        primary_series=GOAL_FIT,
        events=merge_moments(readings),
        meta=meta,
    )
