import json

from preflight.planning.archetypes import archetypes_for
from preflight.planning.draft import PlanDraft
from preflight.planning.validation import _set_problems, plan_problems
from tests.factories import make_brief, make_concept
from tests.planning.helpers import OUTCOME, concept_json, plan_json, scene

BRIEF = make_brief()
ARCHETYPES = archetypes_for(3)


def problems(raw: str) -> list[str]:
    return plan_problems(PlanDraft.model_validate_json(raw), BRIEF, ARCHETYPES)


def test_valid_plan_has_no_problems() -> None:
    assert problems(plan_json()) == []


def test_wrong_concept_count_is_reported_first() -> None:
    assert problems(plan_json(concept_json(), concept_json())) == [
        "return exactly 3 concepts, not 2"
    ]


def test_out_of_range_screenshot_index_names_the_scene_and_valid_range() -> None:
    bad = concept_json(scenes=[scene(0, 3), scene(1, 3), scene(2, 3), scene(3, 3), scene(0, 3)])

    result = problems(plan_json(concept_json(), bad, concept_json()))

    assert result == ["concept B scene 4: screenshot_index 3 does not exist; use 0 to 2"]


def test_ungrounded_text_is_reported_with_the_concept_id() -> None:
    bad = concept_json(cta="Try it free")

    result = problems(plan_json(concept_json(), concept_json(), bad))

    assert len(result) == 1
    assert result[0].startswith('concept C cta: text "Try it free" uses "try", "free"')


def test_contract_violations_are_reported_not_raised() -> None:
    raw = json.loads(plan_json())
    raw["concepts"][0]["hook"] = "one two three four five six seven eight nine"

    assert problems(json.dumps(raw)) == [
        "concept does not satisfy the contract: Value error, hook has more than 8 words"
    ]


def test_set_invariants_flag_duplicate_hypotheses_and_bad_ids() -> None:
    concepts = (make_concept("A"), make_concept("C"))

    assert _set_problems(concepts) == [
        "variant ids must be A, B, C... in order",
        "every concept needs a distinct hypothesis",
    ]


def test_set_invariants_accept_a_valid_plan() -> None:
    concepts = (make_concept("A", hypothesis="x"), make_concept("B", hypothesis="y"))

    assert _set_problems(concepts) == []


def test_scene_durations_must_fill_the_video() -> None:
    short = concept_json(scenes=[scene(0, 3), scene(1, 3), scene(2, 3), scene(0, 3)])

    try:
        PlanDraft.model_validate_json(plan_json(short, short, short))
    except ValueError as exc:
        assert "add up to 15 seconds, got 12" in str(exc)
    else:
        raise AssertionError("expected a validation error")


def test_helper_scene_text_is_grounded_in_the_brief() -> None:
    assert OUTCOME["text"] == BRIEF.one_liner
