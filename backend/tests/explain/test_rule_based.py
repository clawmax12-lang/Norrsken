import re

import pytest
from hypothesis import given
from hypothesis import strategies as st

from preflight.contracts import (
    BriefField,
    CreativeConcept,
    EventType,
    Reason,
    Scene,
    SimEvent,
    SimulationResult,
    SimulatorName,
)
from preflight.errors import PreflightValidationError
from preflight.explain import RuleBasedExplainer
from preflight.scoring import score_and_rank
from tests.factories import make_brief, make_concept, make_result

TRIBE = SimulatorName.TRIBE_V2
GEMINI = SimulatorName.GEMINI_PANEL
FORBIDDEN = re.compile(r"emotion|desire|attention|buy|purchase intent|viral|predict", re.IGNORECASE)

SCENE_TEXTS = ("Capture", "Notes that organise themselves", "Search", "Share", "Try it free")


def concept_with_distinct_scenes(variant_id: str = "A") -> CreativeConcept:
    scenes = tuple(
        Scene(
            t_start=3 * i,
            t_end=3 * (i + 1),
            screenshot=f"uploads/{i % 3 + 1}.png",
            text=text,
            source_field=BriefField.ONE_LINER,
        )
        for i, text in enumerate(SCENE_TEXTS)
    )
    return make_concept(variant_id, scenes=scenes)


def event(t: float, kind: EventType, label: str) -> SimEvent:
    return SimEvent(t=t, type=kind, label=label)


def hold(t: float, label: str = "viewers stayed") -> SimEvent:
    return event(t, EventType.HOLD, label)


def drop(t: float, label: str = "viewers left") -> SimEvent:
    return event(t, EventType.DROP, label)


async def explain(
    results: list[SimulationResult], concept: CreativeConcept | None = None
) -> tuple[Reason, ...]:
    concept = concept or concept_with_distinct_scenes()
    ranking = score_and_rank([make_result("A"), make_result("B", values=(0.4,) * 15)])
    return await RuleBasedExplainer().explain(make_brief(), concept, ranking, results)


async def test_reason_names_the_scene_on_screen_the_event_and_the_simulator() -> None:
    reasons = await explain(
        [make_result("A", GEMINI, events=(hold(3, "outcome stated"), drop(10)))]
    )

    assert [reason.t for reason in reasons] == [3, 10]
    assert [reason.scene_index for reason in reasons] == [1, 3]
    assert reasons[0].text == (
        "Hold at 0:03 (scene 2, 0:03-0:06, 'Notes that organise themselves'): "
        "outcome stated (reported by the simulated viewer panel)"
    )
    assert reasons[1].text.startswith("Drop at 0:10 (scene 4, 0:09-0:12, 'Share'): viewers left")


async def test_picks_one_drop_then_the_strongest_holds_and_sorts_by_time() -> None:
    values = (0.1, 0.9, 0.2, 0.8, 0.3, 0.7, 0.4, 0.6, 0.5, 0.5, 0.2, 0.5, 0.5, 0.5, 0.5)
    events = (hold(1), hold(3), hold(5), hold(7), hold(8), drop(2), drop(10))
    reasons = await explain([make_result("A", GEMINI, values, events=events)])

    # the weakest drop (0.2 at 2 and 10, earlier wins) plus the three strongest holds, at 1, 3, 5
    assert [reason.t for reason in reasons] == [1, 2, 3, 5]
    assert sum(reason.text.startswith("Drop") for reason in reasons) == 1


async def test_keeps_a_drop_even_when_there_are_many_holds() -> None:
    events = (*(hold(t) for t in range(6)), drop(14))

    reasons = await explain([make_result("A", GEMINI, events=events)])

    assert len(reasons) == 4
    assert any(reason.text.startswith("Drop at 0:14") for reason in reasons)


async def test_events_in_the_same_second_yield_one_reason() -> None:
    events = (hold(4.1), hold(4.8), drop(9))

    reasons = await explain([make_result("A", GEMINI, events=events)])

    assert [int(reason.t) for reason in reasons] == [4, 9]


async def test_events_from_every_simulator_are_considered() -> None:
    reasons = await explain(
        [
            make_result("A", TRIBE, events=(hold(2),)),
            make_result("A", GEMINI, events=(drop(11),)),
        ]
    )

    assert "reported by the brain sim" in reasons[0].text
    assert "reported by the simulated viewer panel" in reasons[1].text


async def test_other_variants_results_are_ignored() -> None:
    reasons = await explain(
        [
            make_result("B", GEMINI, events=(hold(1), hold(2))),
            make_result("A", GEMINI, events=(hold(5), drop(8))),
        ]
    )

    assert [reason.t for reason in reasons] == [5, 8]


async def test_event_at_the_very_end_maps_to_the_last_scene() -> None:
    reasons = await explain([make_result("A", GEMINI, events=(hold(1), drop(15)))])

    assert reasons[-1].t == 15
    assert reasons[-1].scene_index == 4


async def test_events_past_the_concept_video_are_ignored() -> None:
    late = make_result("A", GEMINI, events=(hold(1), drop(5), hold(20)), duration_s=25.0)

    reasons = await explain([late])

    assert [reason.t for reason in reasons] == [1, 5]


async def test_derives_moments_from_the_series_when_no_event_exists() -> None:
    values = (0.5, 0.6, 0.9, 0.8, 0.3, 0.4) + (0.5,) * 9

    reasons = await explain([make_result("A", GEMINI, values)])

    assert [reason.t for reason in reasons] == [2, 4]
    assert reasons[0].text.startswith("Series peak at 0:02 (scene 1,")
    assert "primary series peaks at 0.90" in reasons[0].text
    assert reasons[1].text.startswith("Steepest drop at 0:04 (scene 2,")
    assert "primary series falls from 0.80 to 0.30" in reasons[1].text
    assert all("derived from the simulated viewer panel series" in r.text for r in reasons)
    assert all("reported by" not in reason.text for reason in reasons)


async def test_a_single_event_is_topped_up_from_the_series() -> None:
    values = (0.5,) * 6 + (0.9, 0.2) + (0.5,) * 7

    reasons = await explain([make_result("A", GEMINI, values, events=(hold(1),))])

    assert [reason.t for reason in reasons] == [1, 6, 7]
    assert "reported by" in reasons[0].text
    assert all("derived from" in reason.text for reason in reasons[1:])


async def test_a_rising_series_uses_its_lowest_point_instead_of_a_drop() -> None:
    values = tuple(i / 14 for i in range(15))

    reasons = await explain([make_result("A", GEMINI, values)])

    assert [reason.t for reason in reasons] == [0, 14]
    assert reasons[0].text.startswith("Series low at 0:00")
    assert reasons[1].text.startswith("Series peak at 0:14")


async def test_a_flat_series_still_gives_two_distinct_moments() -> None:
    reasons = await explain([make_result("A", GEMINI)])

    assert [reason.t for reason in reasons] == [0, 14]


async def test_fractional_seconds_are_shown_as_given() -> None:
    reasons = await explain([make_result("A", GEMINI, events=(hold(2.5), drop(9.0)))])

    assert reasons[0].text.startswith("Hold at 0:02.5 (scene 1,")


async def test_a_series_with_one_second_cannot_be_explained() -> None:
    result = make_result("A", GEMINI, (0.5,))

    with pytest.raises(PreflightValidationError, match="too few distinct seconds"):
        await explain([result])


async def test_no_result_for_the_variant_is_an_error() -> None:
    with pytest.raises(PreflightValidationError, match="no simulation result for variant A"):
        await explain([make_result("B", GEMINI)])


async def test_a_result_without_samples_inside_the_video_is_an_error() -> None:
    result = make_result("A", GEMINI, (0.5, 0.5), timestamps_s=(16.0, 17.0), duration_s=20.0)

    with pytest.raises(PreflightValidationError, match="no samples inside the video"):
        await explain([result])


async def test_output_is_deterministic_for_any_result_order() -> None:
    results = [
        make_result("A", TRIBE, events=(hold(2), drop(7))),
        make_result("A", GEMINI, events=(hold(2), drop(7))),
    ]

    assert await explain(results) == await explain(results[::-1])


@st.composite
def varied_results(draw: st.DrawFn) -> list[SimulationResult]:
    simulators = draw(st.lists(st.sampled_from(SimulatorName), min_size=1, max_size=2, unique=True))
    results = []
    for simulator in simulators:
        values = tuple(draw(st.lists(st.floats(0.0, 1.0), min_size=15, max_size=15)))
        times = draw(st.lists(st.floats(0.0, 15.0), max_size=6))
        kinds = draw(st.lists(st.sampled_from(EventType), min_size=len(times), max_size=len(times)))
        events = tuple(event(t, kind, "label") for t, kind in zip(times, kinds, strict=True))
        results.append(make_result("A", simulator, values, events=events))
    return results


@given(results=varied_results())
async def test_reasons_always_satisfy_the_fr06_acceptance_criteria(
    results: list[SimulationResult],
) -> None:
    concept = concept_with_distinct_scenes()

    reasons = await explain(results, concept)

    assert 2 <= len(reasons) <= 4
    assert len({int(reason.t) for reason in reasons}) == len(reasons)
    assert [reason.t for reason in reasons] == sorted(reason.t for reason in reasons)
    for reason in reasons:
        assert 0 <= reason.t <= concept.duration_s
        scene = concept.scenes[reason.scene_index]
        assert scene.t_start <= reason.t <= scene.t_end
        assert f"'{scene.text}'" in reason.text
        assert not FORBIDDEN.search(reason.text)
