import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st
from preflight.contracts import EventType

from tests.fakes import N_VERTICES, fake_groups
from tribe_worker.analysis import (
    MAX_EVENTS_PER_TYPE,
    PRIMARY_SERIES,
    UnusablePredictionError,
    find_events,
    reduce_to_series,
    squash,
    trim_to_video,
)
from tribe_worker.predictor import Prediction

GROUPS = fake_groups()


def prediction(rows: int, *, fill: float = 0.0, starts: tuple[float, ...] | None = None) -> Prediction:
    activity = np.full((rows, N_VERTICES), fill, dtype=np.float32)
    return Prediction(
        activity=activity,
        start_times_s=starts if starts is not None else tuple(float(i) for i in range(rows)),
        hz=1.0,
    )


def test_trim_drops_padding_after_the_video_and_keeps_order() -> None:
    trimmed = trim_to_video(prediction(18), duration_s=15.0)
    assert trimmed.start_times_s == tuple(float(i) for i in range(15))
    assert trimmed.activity.shape == (15, N_VERTICES)


def test_trim_keeps_gaps_from_dropped_empty_segments() -> None:
    gapped = prediction(4, starts=(0.0, 1.0, 4.0, 20.0))
    assert trim_to_video(gapped, duration_s=15.0).start_times_s == (0.0, 1.0, 4.0)


def test_trim_rejects_a_prediction_with_nothing_inside_the_video() -> None:
    with pytest.raises(UnusablePredictionError, match="no segment"):
        trim_to_video(prediction(2, starts=(30.0, 31.0)), duration_s=15.0)


def test_trim_rejects_non_finite_output() -> None:
    bad = prediction(2)
    bad.activity[0, 0] = np.nan
    with pytest.raises(UnusablePredictionError, match="NaN"):
        trim_to_video(bad, duration_s=15.0)


@given(st.floats(min_value=0, max_value=1e6), st.floats(min_value=0, max_value=1e6))
def test_squash_is_monotone_and_bounded(a: float, b: float) -> None:
    low, high = sorted((a, b))
    squashed = squash(np.array([low, high]))
    assert 0.0 <= squashed[0] <= squashed[1] <= 1.0


def test_series_values_depend_only_on_the_clip_itself() -> None:
    """No per-clip min-max: the same activity inside a longer clip gives the same values."""
    short = reduce_to_series(prediction(3, fill=0.4).activity, GROUPS)
    long = reduce_to_series(prediction(9, fill=0.4).activity, GROUPS)
    assert long[PRIMARY_SERIES][:3] == short[PRIMARY_SERIES]
    assert len(set(long[PRIMARY_SERIES])) == 1


def test_stronger_response_gives_a_higher_primary_series() -> None:
    weak = reduce_to_series(prediction(2, fill=0.1).activity, GROUPS)
    strong = reduce_to_series(prediction(2, fill=0.9).activity, GROUPS)
    assert strong[PRIMARY_SERIES][0] > weak[PRIMARY_SERIES][0]


def test_series_has_one_curve_per_group_plus_primary_within_unit_range() -> None:
    series = reduce_to_series(prediction(3, fill=-5.0).activity, GROUPS)
    assert set(series) == {"visual", "auditory", "language", PRIMARY_SERIES}
    assert all(0.0 <= v <= 1.0 for values in series.values() for v in values)


def test_sign_of_the_response_does_not_matter() -> None:
    up = reduce_to_series(prediction(2, fill=0.3).activity, GROUPS)
    down = reduce_to_series(prediction(2, fill=-0.3).activity, GROUPS)
    assert up == down


def _series(strength: list[float], dominant: str = "visual") -> dict[str, tuple[float, ...]]:
    flat = tuple(0.0 for _ in strength)
    curves = {"visual": flat, "auditory": flat, "language": flat}
    curves[dominant] = tuple(strength)
    return {**curves, PRIMARY_SERIES: tuple(strength)}


def test_events_label_peaks_and_declines_with_the_dominant_group() -> None:
    strength = [0.1, 0.5, 0.2, 0.2, 0.6, 0.1]
    events = find_events([float(i) for i in range(6)], _series(strength), GROUPS)
    by_type = {(e.type, e.t): e.label for e in events}
    assert by_type[(EventType.HOLD, 1.0)] == "Predicted visual-cortex response peaks"
    assert by_type[(EventType.HOLD, 4.0)] == "Predicted visual-cortex response peaks"
    assert by_type[(EventType.DROP, 2.0)] == "Predicted visual-cortex response declines"
    assert by_type[(EventType.DROP, 5.0)] == "Predicted visual-cortex response declines"
    assert [e.t for e in events] == sorted(e.t for e in events)


def test_events_name_the_auditory_group_when_it_leads() -> None:
    events = find_events([0.0, 1.0, 2.0], _series([0.1, 0.5, 0.1], "auditory"), GROUPS)
    assert events[0].label == "Predicted auditory-cortex response peaks"


def test_a_flat_series_has_no_events() -> None:
    assert find_events([0.0, 1.0, 2.0], _series([0.3, 0.3, 0.3]), GROUPS) == ()


def test_wiggles_below_the_threshold_are_not_events() -> None:
    assert find_events([0.0, 1.0, 2.0], _series([0.300, 0.305, 0.300]), GROUPS) == ()


def test_event_count_is_capped_per_type_and_strongest_win() -> None:
    strength = [0.0, 0.2, 0.0, 0.4, 0.0, 0.6, 0.0, 0.8, 0.0]
    events = find_events([float(i) for i in range(9)], _series(strength), GROUPS)
    holds = [e.t for e in events if e.type is EventType.HOLD]
    assert len(holds) == MAX_EVENTS_PER_TYPE
    assert sorted(holds) == [5.0, 7.0]


def test_events_use_the_returned_timestamps_not_the_index() -> None:
    events = find_events([0.0, 1.0, 4.0], _series([0.1, 0.6, 0.1]), GROUPS)
    assert {(e.type, e.t) for e in events} == {(EventType.HOLD, 1.0), (EventType.DROP, 4.0)}


@given(st.lists(st.floats(min_value=0, max_value=1), min_size=1, max_size=20))
def test_events_are_deterministic_and_inside_the_clip(strength: list[float]) -> None:
    stamps = [float(i) for i in range(len(strength))]
    first = find_events(stamps, _series(strength), GROUPS)
    assert first == find_events(stamps, _series(strength), GROUPS)
    assert all(0.0 <= e.t <= stamps[-1] for e in first)
