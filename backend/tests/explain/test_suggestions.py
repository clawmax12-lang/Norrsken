import pytest

from preflight.contracts import EventType, SimEvent, SimulatorName
from preflight.errors import PreflightValidationError
from preflight.explain import next_time_suggestions
from preflight.scoring import score_and_rank
from tests.explain.test_rule_based import FORBIDDEN, concept_with_distinct_scenes, drop, hold
from tests.factories import make_result

TRIBE = SimulatorName.TRIBE_V2
GEMINI = SimulatorName.GEMINI_PANEL

LOW_CONFIDENCE = score_and_rank([make_result("A"), make_result("B", values=(0.4,) * 15)])
HIGH_CONFIDENCE = score_and_rank(
    [
        make_result("A", TRIBE, (0.9,) * 15),
        make_result("B", TRIBE, (0.1,) * 15),
        make_result("A", GEMINI, (0.8,) * 15),
        make_result("B", GEMINI, (0.2,) * 15),
    ]
)


def test_names_the_scene_of_the_lowest_reported_drop() -> None:
    values = (0.5,) * 9 + (0.2, 0.5, 0.5, 0.5, 0.5, 0.5)
    result = make_result("A", GEMINI, values, events=(drop(9, "viewers left"), drop(4)))

    suggestions = next_time_suggestions(concept_with_distinct_scenes(), HIGH_CONFIDENCE, [result])

    assert suggestions == (
        "Simulated viewers dropped on 'Share' (0:09-0:12, simulated viewer panel: viewers left): "
        "shorten this scene or tighten its wording.",
    )


def test_derives_the_weakest_moment_from_the_series_when_no_drop_was_reported() -> None:
    values = (0.5,) * 4 + (0.9, 0.2) + (0.5,) * 9
    result = make_result("A", GEMINI, values, events=(hold(4),))

    suggestions = next_time_suggestions(concept_with_distinct_scenes(), HIGH_CONFIDENCE, [result])

    assert suggestions == (
        "The simulated viewer panel series was weakest on 'Notes that organise themselves' "
        "(0:03-0:06): "
        "shorten this scene or tighten its wording.",
    )


def test_weakness_in_the_opening_scene_points_at_the_hook() -> None:
    result = make_result("A", GEMINI, events=(drop(1),))

    suggestions = next_time_suggestions(concept_with_distinct_scenes(), HIGH_CONFIDENCE, [result])

    assert len(suggestions) == 2
    assert (
        "opening scene: rework the hook 'Notes that organise themselves' (from one_liner)"
        in (suggestions[1])
    )


def test_opening_and_closing_scenes_are_named_by_the_copy_on_screen() -> None:
    concept = concept_with_distinct_scenes()

    opening = next_time_suggestions(
        concept, HIGH_CONFIDENCE, [make_result("A", GEMINI, events=(drop(1),))]
    )
    closing = next_time_suggestions(
        concept, HIGH_CONFIDENCE, [make_result("A", GEMINI, events=(drop(13),))]
    )

    assert f"'{concept.hook}' (0:00-0:03" in opening[0]
    assert f"'{concept.cta}' (0:12-0:15" in closing[0]


def test_weakness_in_the_closing_scene_points_at_the_call_to_action() -> None:
    result = make_result("A", GEMINI, events=(drop(13),))

    suggestions = next_time_suggestions(concept_with_distinct_scenes(), HIGH_CONFIDENCE, [result])

    assert (
        "closing scene: rework the call to action 'Acme Notes' (from product_name)"
        in (suggestions[1])
    )


def test_low_confidence_adds_an_ab_test_reminder() -> None:
    result = make_result("A", GEMINI, events=(drop(13),))

    suggestions = next_time_suggestions(concept_with_distinct_scenes(), LOW_CONFIDENCE, [result])

    assert len(suggestions) == 3
    assert "A/B test" in suggestions[2]


def test_always_between_one_and_three_suggestions_without_forbidden_wording() -> None:
    result = make_result(
        "A", GEMINI, events=(drop(6), SimEvent(t=1, type=EventType.HOLD, label="x"))
    )

    suggestions = next_time_suggestions(concept_with_distinct_scenes(), LOW_CONFIDENCE, [result])

    assert 1 <= len(suggestions) <= 3
    assert not any(FORBIDDEN.search(text) for text in suggestions)


def test_suggestions_follow_the_concepts_language() -> None:
    swedish = concept_with_distinct_scenes().model_copy(update={"language": "sv"})
    result = make_result("A", GEMINI, events=(drop(1, "för långsam start"),))

    suggestions = next_time_suggestions(swedish, LOW_CONFIDENCE, [result])

    assert suggestions[0].startswith(
        "Simulerade tittare tappade vid 'Notes that organise themselves' (0:00-0:03"
    )
    assert "den simulerade tittarpanelen: för långsam start" in suggestions[0]
    assert "skriv om kroken" in suggestions[1]
    assert "A/B-testa" in suggestions[2]


def test_unsupported_languages_get_english_advice() -> None:
    german = concept_with_distinct_scenes().model_copy(update={"language": "de"})
    result = make_result("A", GEMINI, events=(drop(13),))

    assert "A/B test it" in next_time_suggestions(german, LOW_CONFIDENCE, [result])[2]


def test_requires_a_result_for_the_variant() -> None:
    with pytest.raises(PreflightValidationError):
        next_time_suggestions(concept_with_distinct_scenes(), LOW_CONFIDENCE, [make_result("B")])
