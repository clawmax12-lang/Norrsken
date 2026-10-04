import json

from preflight.contracts import BriefField
from preflight.planning.archetypes import archetypes_for
from preflight.planning.draft import PlanDraft, assemble_concepts, fit_durations
from preflight.planning.validation import _set_problems, plan_problems
from tests.factories import make_brief, make_concept
from tests.planning.helpers import OUTCOME, PRODUCT, concept_json, plan_json, scene

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
    raw = json.loads(plan_json())
    raw["concepts"][2]["cta"] = "Try it free"

    result = problems(json.dumps(raw))

    assert len(result) == 1
    assert result[0].startswith('concept C cta: text "Try it free" uses "try", "free"')


def test_adjacent_screenshot_repeats_are_rejected() -> None:
    repeated = concept_json(
        scenes=[scene(0, 3), scene(0, 3, PRODUCT), scene(1, 3), scene(2, 3), scene(1, 3)]
    )
    others = json.loads(plan_json())["concepts"]

    result = problems(plan_json(repeated, others[1], others[2]))

    assert result == [
        "concept A scenes 1 and 2 repeat screenshot_index 0; pick a different screenshot"
    ]


def test_identical_screenshot_sequences_are_rejected() -> None:
    same = concept_json()

    result = problems(plan_json(same, same, same))

    assert result == [
        "concepts must not share the same screenshot sequence; vary the order across A, B and C"
    ]


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


def test_scene_durations_are_scaled_to_fill_the_video() -> None:
    short = concept_json(scenes=[scene(0, 2), scene(1, 4), scene(2, 3), scene(0, 3)])

    draft = PlanDraft.model_validate_json(plan_json(short, short, short))

    for concept in draft.concepts:
        assert [s.duration_s for s in concept.scenes] == [3, 5, 4, 3]


def test_fit_durations_keeps_exact_lengths_and_handles_long_plans() -> None:
    assert fit_durations([3, 3, 3, 3, 3], 15) == [3, 3, 3, 3, 3]
    assert fit_durations([5, 5, 5, 5, 5, 5], 15)[-1] == 3
    assert sum(fit_durations([5, 5, 5, 5, 5, 5], 15)) == 15
    assert min(fit_durations([1, 1, 1, 12], 15)) >= 1


def test_helper_scene_text_is_grounded_in_the_brief() -> None:
    assert OUTCOME["text"] == BRIEF.one_liner


def test_assemble_uses_goal_note_as_cta_when_present() -> None:
    brief = make_brief(goal_note="Start selling today")
    draft = PlanDraft.model_validate_json(plan_json())

    concepts = assemble_concepts(draft, brief, ARCHETYPES)

    assert all(c.cta == "Start selling today" for c in concepts)
    assert all(c.cta_source_field is BriefField.GOAL_NOTE for c in concepts)


def test_assemble_keeps_a_goal_note_cta_the_model_already_wrote() -> None:
    brief = make_brief(goal_note="Start selling today")
    sourced = concept_json(cta="Start selling", cta_source_field="goal_note")
    draft = PlanDraft.model_validate_json(plan_json(sourced, sourced, sourced))

    concepts = assemble_concepts(draft, brief, ARCHETYPES)

    assert concepts[0].cta == "Start selling"
    assert concepts[0].cta_source_field is BriefField.GOAL_NOTE
