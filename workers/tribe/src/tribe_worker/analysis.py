"""Reduce a per-vertex prediction to the per-second curves and events of a SimulationResult.

Every rule here is fixed and clip-independent, so two variants analysed on different days stay
comparable. Nothing is normalised per clip.

``response_strength`` is ``tanh(mean |response| / RESPONSE_REFERENCE)``, where the mean is the
average of the three group means (each group counts equally). ``RESPONSE_REFERENCE`` is a
placeholder scale: it keeps values inside ``[0, 1]`` and monotone in the model's output, but it
is **uncalibrated** until the first real GPU run shows the typical magnitude of predictions.
Changing it changes ``SCALE_VERSION`` so stale results are never mixed with new ones.
"""

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from preflight.contracts import EventType, SimEvent

from tribe_worker.atlas import RegionGroups
from tribe_worker.predictor import Prediction

PRIMARY_SERIES = "response_strength"
RESPONSE_REFERENCE = 1.0
SCALE_VERSION = "v0-uncalibrated"
MIN_EVENT_DELTA = 0.01
MAX_EVENTS_PER_TYPE = 2


class UnusablePredictionError(ValueError):
    """The model returned nothing we can report on (empty or non-finite)."""


def trim_to_video(prediction: Prediction, duration_s: float) -> Prediction:
    """Keep only rows whose segment starts inside the video.

    The model pads its last batch past the end of the clip; rows starting at or after
    ``duration_s`` carry no stimulus and are dropped. Rows are never reordered or interpolated.
    """
    keep = [0.0 <= start < duration_s for start in prediction.start_times_s]
    if not any(keep):
        raise UnusablePredictionError("model returned no segment inside the video")
    activity = prediction.activity[np.array(keep)]
    if not np.isfinite(activity).all():
        raise UnusablePredictionError("model output contains NaN or infinite values")
    starts = tuple(s for s, kept in zip(prediction.start_times_s, keep, strict=True) if kept)
    return Prediction(activity=activity, start_times_s=starts, hz=prediction.hz)


def squash(mean_abs_response: NDArray[np.float64]) -> NDArray[np.float64]:
    """Fixed monotone map from a non-negative mean |response| to ``[0, 1)``."""
    squashed: NDArray[np.float64] = np.tanh(mean_abs_response / RESPONSE_REFERENCE)
    return squashed


def reduce_to_series(
    activity: NDArray[np.float32], groups: RegionGroups
) -> dict[str, tuple[float, ...]]:
    """Per-second curves: one per region group plus the primary ``response_strength``."""
    group_means = {
        group.definition.id: np.abs(activity[:, list(group.vertex_indices)]).mean(
            axis=1, dtype=np.float64
        )
        for group in groups.groups
    }
    series = {name: _as_unit_floats(squash(means)) for name, means in group_means.items()}
    overall = np.mean(list(group_means.values()), axis=0)
    series[PRIMARY_SERIES] = _as_unit_floats(squash(overall))
    return series


def _as_unit_floats(values: NDArray[np.float64]) -> tuple[float, ...]:
    return tuple(float(v) for v in np.clip(values, 0.0, 1.0))


@dataclass(frozen=True)
class _Moment:
    index: int
    magnitude: float


def find_events(
    timestamps_s: Sequence[float],
    series: dict[str, tuple[float, ...]],
    groups: RegionGroups,
) -> tuple[SimEvent, ...]:
    """Largest local peaks (holds) and steepest declines (drops) of ``response_strength``.

    Labels state only what the curves show, e.g. "Predicted visual-cortex response peaks";
    the named group is the one with the highest value at that moment.
    """
    strength = series[PRIMARY_SERIES]
    nouns = {g.definition.id: g.definition.event_noun for g in groups.groups}

    def dominant_noun(index: int) -> str:
        return nouns[max(nouns, key=lambda group_id: series[group_id][index])]

    holds = [
        SimEvent(
            t=timestamps_s[m.index],
            type=EventType.HOLD,
            label=f"Predicted {dominant_noun(m.index)} response peaks",
        )
        for m in _top(_peaks(strength))
    ]
    drops = [
        SimEvent(
            t=timestamps_s[m.index + 1],
            type=EventType.DROP,
            label=f"Predicted {dominant_noun(m.index)} response declines",
        )
        for m in _top(_declines(strength))
    ]
    return tuple(sorted(holds + drops, key=lambda event: (event.t, event.type.value)))


def _peaks(values: Sequence[float]) -> list[_Moment]:
    """Local maxima that rise at least ``MIN_EVENT_DELTA`` above their lower neighbour."""
    moments = []
    for i, value in enumerate(values):
        neighbours = [values[j] for j in (i - 1, i + 1) if 0 <= j < len(values)]
        is_peak = all(value >= n for n in neighbours) and any(value > n for n in neighbours)
        if is_peak and value - min(neighbours) >= MIN_EVENT_DELTA:
            moments.append(_Moment(index=i, magnitude=value))
    return moments


def _declines(values: Sequence[float]) -> list[_Moment]:
    """Steps between neighbouring samples that fall by at least ``MIN_EVENT_DELTA``."""
    return [
        _Moment(index=i, magnitude=values[i] - values[i + 1])
        for i in range(len(values) - 1)
        if values[i] - values[i + 1] >= MIN_EVENT_DELTA
    ]


def _top(moments: list[_Moment]) -> list[_Moment]:
    """The strongest moments; ties go to the earlier one so output is deterministic."""
    ranked = sorted(moments, key=lambda m: (-m.magnitude, m.index))
    return ranked[:MAX_EVENTS_PER_TYPE]
