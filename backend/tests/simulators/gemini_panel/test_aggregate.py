import pytest
from hypothesis import given
from hypothesis import strategies as st

from preflight.contracts import EventType
from preflight.simulators.gemini_panel.aggregate import (
    FlaggedMoment,
    PersonaReading,
    build_series,
    merge_moments,
    reading_from,
)
from preflight.simulators.gemini_panel.schemas import Persona, PersonaRating

PERSONA = Persona(label="p", description="d", looks_for="l")


def reading(
    index: int, *moments: tuple[float, EventType, str], goal=0.5, clarity=0.5
) -> PersonaReading:
    flags = tuple(FlaggedMoment(index, t, kind, label) for t, kind, label in moments)
    return PersonaReading(index, PERSONA, (goal,) * 3, (clarity,) * 3, flags)


def test_series_are_means_with_per_persona_goal_fit() -> None:
    first = PersonaReading(1, PERSONA, (0.0, 1.0), (0.2, 0.4), ())
    second = PersonaReading(2, PERSONA, (1.0, 1.0), (0.6, 0.8), ())

    series = build_series([first, second])

    assert series["goal_fit"] == (0.5, 1.0)
    assert series["clarity"] == pytest.approx((0.4, 0.6))
    assert series["persona_1_goal_fit"] == (0.0, 1.0)
    assert series["persona_2_goal_fit"] == (1.0, 1.0)


def test_a_moment_flagged_by_two_personas_within_a_second_becomes_one_event() -> None:
    drop = EventType.DROP

    events = merge_moments(
        [reading(1, (5.0, drop, "text-heavy screen")), reading(2, (6.0, drop, "dense text"))]
    )

    assert [(e.t, e.type, e.label) for e in events] == [(5.5, drop, "text-heavy screen")]


def test_a_moment_flagged_by_one_persona_is_not_an_event() -> None:
    assert merge_moments([reading(1, (5.0, EventType.HOLD, "x")), reading(2)]) == ()


def test_the_same_persona_flagging_twice_does_not_count_as_agreement() -> None:
    assert merge_moments([reading(1, (5.0, EventType.HOLD, "a"), (5.5, EventType.HOLD, "b"))]) == ()


def test_hold_and_drop_never_merge_with_each_other() -> None:
    events = merge_moments(
        [reading(1, (5.0, EventType.HOLD, "a")), reading(2, (5.0, EventType.DROP, "b"))]
    )

    assert events == ()


def test_flags_more_than_a_second_apart_are_separate_events() -> None:
    hold = EventType.HOLD
    events = merge_moments(
        [
            reading(1, (2.0, hold, "a"), (9.0, hold, "c")),
            reading(2, (2.0, hold, "b"), (9.0, hold, "d")),
            reading(3, (5.0, hold, "e")),
        ]
    )

    assert [e.t for e in events] == [2.0, 9.0]


def test_events_are_ordered_by_time() -> None:
    events = merge_moments(
        [
            reading(1, (8.0, EventType.DROP, "late"), (2.0, EventType.HOLD, "early")),
            reading(2, (8.0, EventType.DROP, "late"), (2.0, EventType.HOLD, "early")),
        ]
    )

    assert [e.t for e in events] == [2.0, 8.0]


def test_reading_orders_seconds_and_converts_timestamps() -> None:
    rating = PersonaRating.model_validate(
        {
            "seconds": [
                {"second": 1, "goal_fit": 0.9, "clarity": 0.1},
                {"second": 0, "goal_fit": 0.3, "clarity": 0.2},
            ],
            "moments": [{"timestamp": "00:07", "kind": "hold", "label": "demo"}],
        }
    )

    result = reading_from(2, PERSONA, rating)

    assert result.goal_fit == (0.3, 0.9)
    assert result.clarity == (0.2, 0.1)
    assert result.moments == (FlaggedMoment(2, 7.0, EventType.HOLD, "demo"),)


flags = st.lists(
    st.tuples(
        st.integers(0, 14).map(float), st.sampled_from(EventType), st.text("abc", min_size=1)
    ),
    max_size=6,
)


@given(st.lists(flags, min_size=1, max_size=3))
def test_every_event_is_backed_by_two_personas_and_stays_inside_the_video(per_persona) -> None:
    readings = [reading(i, *moments) for i, moments in enumerate(per_persona, start=1)]

    events = merge_moments(readings)

    for event in events:
        backers = {
            r.index
            for r in readings
            for m in r.moments
            if m.kind is event.type and abs(m.t - event.t) <= 1.0
        }
        assert len(backers) >= 2
        assert 0 <= event.t <= 14


@given(st.lists(st.lists(st.floats(0, 1), min_size=3, max_size=3), min_size=1, max_size=3))
def test_mean_series_stay_within_the_unit_interval(values) -> None:
    readings = [PersonaReading(i, PERSONA, tuple(v), tuple(v), ()) for i, v in enumerate(values, 1)]

    series = build_series(readings)

    assert all(0.0 <= x <= 1.0 for x in series["goal_fit"] + series["clarity"])


def test_reading_from_an_unchecked_rating_fails_loudly() -> None:
    rating = PersonaRating.model_validate(
        {
            "seconds": [{"second": 0, "goal_fit": 0.3, "clarity": 0.2}],
            "moments": [{"timestamp": "soon", "kind": "hold", "label": "demo"}],
        }
    )

    with pytest.raises(ValueError, match="unchecked rating"):
        reading_from(1, PERSONA, rating)
