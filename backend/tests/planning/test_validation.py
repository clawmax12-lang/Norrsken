import json

from preflight.contracts import BriefField
from preflight.generation.compose import compose
from preflight.planning.archetypes import archetypes_for
from preflight.planning.draft import PlanDraft, assemble_concepts, end_voice_for, fit_durations
from preflight.planning.validation import (
    _set_problems,
    craft_problems,
    plan_problems,
    without_unsourced_extras,
)
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


def test_free_phrasing_without_new_facts_is_allowed() -> None:
    raw = json.loads(plan_json())
    raw["concepts"][2]["cta"] = "Try it free"

    result = problems(json.dumps(raw))

    assert result == []


def test_unknown_numbers_in_copy_are_reported_with_the_concept_id() -> None:
    raw = json.loads(plan_json())
    raw["concepts"][2]["scenes"][0]["voice"] = "Save 40 percent with Acme Notes"

    result = problems(json.dumps(raw))

    assert len(result) == 1
    assert result[0].startswith("concept C")
    assert "40" in result[0]


def test_adjacent_screenshot_repeats_are_rejected() -> None:
    repeated = concept_json(
        scenes=[
            scene(0, 3),
            scene(0, 3, PRODUCT),
            scene(1, 3),
            scene(2, 3),
            scene(1, 3, voice=None),
        ]
    )
    others = json.loads(plan_json())["concepts"]

    result = problems(plan_json(repeated, others[1], others[2]))

    assert result == [
        "concept A scenes 1 and 2 repeat screenshot_index 0; "
        "pick a different screenshot or zoom into a different region with focus"
    ]


def test_a_repeat_is_allowed_when_the_second_scene_zooms_somewhere_new() -> None:
    zoomed = {**scene(0, 3, PRODUCT), "focus": [0.1, 0.5, 0.6, 0.3]}
    repeated = concept_json(
        scenes=[scene(0, 3), zoomed, scene(1, 3), scene(2, 3), scene(1, 3, voice=None)]
    )
    others = json.loads(plan_json())["concepts"]

    assert problems(plan_json(repeated, others[1], others[2])) == []


def test_every_body_scene_needs_a_voice_line() -> None:
    raw = json.loads(plan_json())
    raw["concepts"][0]["scenes"][1]["voice"] = ""

    result = problems(json.dumps(raw))

    assert (
        "concept A: scenes 2 have no voice line; every scene before the end card "
        "needs one so the narration never stops"
    ) in result


def test_identical_screenshot_sequences_are_rejected() -> None:
    same = concept_json()

    result = problems(plan_json(same, same, same))

    assert result == [
        "concepts must not share the same screenshot sequence; vary the order across A, B and C",
        "every concept opens on screenshot 0; open at least one angle on a different screen",
        "every concept needs its own hook; two concepts open with the same words",
    ]


def test_every_usable_screen_is_shown_before_the_end_card() -> None:
    # Body scenes use 0, 1, 1 (zoomed), 0; screenshot 2 only sits under the end card.
    zoomed = {**scene(1, 3, PRODUCT), "focus": [0.1, 0.5, 0.6, 0.3]}
    hidden = concept_json(scenes=[scene(0, 3), scene(1, 3), zoomed, scene(0, 3), scene(2, 3)])
    others = json.loads(plan_json())["concepts"]

    result = problems(plan_json(hidden, others[1], others[2]))

    assert result == [
        "concept A shows only 2 of the 3 usable screenshots before the end card (the end card "
        "covers the last scene's picture); show every screenshot once before repeating one"
    ]


def test_a_brief_cta_for_the_wrong_audience_needs_an_audience_cta() -> None:
    brief = make_brief(buyer_cta="Betala med Apple Pay")
    raw = json.loads(plan_json())
    raw["cta_fits_audience"] = False

    result = plan_problems(PlanDraft.model_validate(raw), brief, ARCHETYPES)

    assert result == [
        "you reported that the brief's call to action does not fit the audience; write a 2 to "
        "4 word action for the audience in audience_cta"
    ]
    raw["audience_cta"] = "Skapa konto"
    assert plan_problems(PlanDraft.model_validate(raw), brief, ARCHETYPES) == []


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
        assert [s.duration_s for s in concept.scenes] == [2, 6, 4, 3]  # the hook is held to 2 s


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


def test_assemble_keeps_a_goal_note_cta_the_model_shortened_from_a_long_note() -> None:
    brief = make_brief(goal_note="Start selling today with your whole team")
    sourced = concept_json(cta="Start selling", cta_source_field="goal_note")
    draft = PlanDraft.model_validate_json(plan_json(sourced, sourced, sourced))

    concepts = assemble_concepts(draft, brief, ARCHETYPES)

    assert concepts[0].cta == "Start selling"
    assert concepts[0].cta_source_field is BriefField.GOAL_NOTE


def test_screen_order_and_copy_problems_are_reported_together() -> None:
    repeated = concept_json(
        scenes=[scene(0, 3), scene(0, 3, PRODUCT), scene(1, 3), scene(2, 3), scene(1, 3)]
    )
    others = json.loads(plan_json())["concepts"]
    others[1]["scenes"][0]["voice"] = "Save 40 percent with Acme Notes"

    result = problems(plan_json(repeated, others[1], others[2]))

    assert any("repeat screenshot_index 0" in p for p in result)
    assert any("40" in p for p in result)


def _story(raw: dict[str, object]) -> list[str]:
    return craft_problems(PlanDraft.model_validate(raw), BRIEF)


def test_an_english_hook_must_talk_to_the_audience() -> None:
    plan = json.loads(plan_json())
    plan["language"] = "en"
    told = [p for p in _story(plan) if "talk to the audience" in p]
    assert [p.split(":")[0] for p in told] == ["concept A", "concept C"]  # B says "Your notes"


def test_a_concept_must_not_open_on_its_confirmation_screen() -> None:
    plan = json.loads(plan_json())
    plan["screenshots"] = [{"index": 0, "confirmation": True}]
    assert any("concept A opens on a confirmation screen" in p for p in _story(plan))


def test_a_four_scene_concept_is_asked_for_a_faster_cut() -> None:
    four = concept_json(scenes=[scene(0, 2), scene(1, 5), scene(2, 5), scene(0, 3, voice=None)])
    plan = json.loads(plan_json(four, four, four))
    assert any("has 4 scenes; use 5 or 6" in p for p in _story(plan))


def test_the_button_hint_reaches_the_end_card_and_the_closing_voice() -> None:
    hinted = concept_json(cta_hint="Igång på 5 minuter")
    draft = PlanDraft.model_validate_json(plan_json(hinted, hinted, hinted))
    concept = assemble_concepts(draft, BRIEF, ARCHETYPES)[0]

    assert concept.cta_hint == "Igång på 5 minuter"
    assert concept.end_voice == "Acme Notes. Igång på 5 minuter."
    assert compose(BRIEF, concept, ()).cta_hint == "Igång på 5 minuter"
    assert end_voice_for("Acme", "Kom igång") == "Acme. Kom igång."


def test_the_end_card_sells_with_the_brief_s_numbers() -> None:
    brief = make_brief(proof_points="Sorts 40 notes a minute.")
    vague = concept_json(closing_line="Notes, sorted", chips=["Fast", "Simple"])
    proven = concept_json(closing_line="40 notes a minute", chips=["40 a minute", "Simple"])
    raw = json.loads(plan_json(vague, proven, proven))

    told = craft_problems(PlanDraft.model_validate(raw), brief)

    assert [p for p in told if "closing_line" in p or "chips" in p] == [
        "concept A: closing_line 'Notes, sorted' has no proof number; make it the strongest "
        "benefit with one of the brief's numbers",
        "concept A: chips ['Fast', 'Simple'] are not proofs; make them concrete facts from "
        "proof_points, at least one with its number",
    ]


def test_one_film_names_its_product_and_sums_up_on_the_end_card() -> None:
    nameless = [scene(i % 3, 3, voice="Notes organise themselves") for i in range(5)]
    told = craft_problems(
        PlanDraft.model_validate(
            json.loads(
                plan_json(
                    concept_json(scenes=nameless),
                    concept_json(closing_line="Acme Notes"),
                    concept_json(),
                )
            )
        ),
        BRIEF,
    )

    assert [p.split(";")[0] for p in told if "voice never" in p or "repeats" in p] == [
        "concept A: the voice never says 'Acme Notes'",
        "concept B: closing_line 'Acme Notes' repeats a scene's text",
    ]


def test_a_long_hook_line_is_a_craft_note_not_a_failure() -> None:
    wordy = concept_json(
        scenes=[
            scene(0, 2, voice="Acme Notes organise themselves while you do the real work"),
            *(scene(i % 3, 3) for i in range(1, 4)),
            scene(1, 4, voice=None),
        ]
    )
    raw = plan_json(wordy, *(_shifted(wordy, n) for n in (1, 2)))

    assert not any("words for a 2 s scene" in p for p in lenient(raw))
    assert any("words for a 2 s scene" in p for p in problems(raw))


def test_a_repeat_into_the_end_card_is_never_seen() -> None:
    ends_on_repeat = concept_json(
        scenes=[scene(0, 3), scene(1, 3), scene(2, 3), scene(0, 3), scene(0, 3, voice=None)]
    )
    raw = plan_json(ends_on_repeat, *(_shifted(ends_on_repeat, n) for n in (1, 2)))

    assert not any("repeat screenshot_index" in p for p in problems(raw))


def test_unsourced_end_card_copy_is_dropped_instead_of_failing_the_plan() -> None:
    invented = concept_json(
        closing_line="Notes in 3 seconds",
        cta_hint="Ready in 2 minutes",
        chips=["Organise themselves", "Loved by Google"],
    )
    raw = plan_json(invented, invented, invented)

    assert not any("closing_line" in p or "chip" in p or "cta_hint" in p for p in lenient(raw))
    cleaned = without_unsourced_extras(PlanDraft.model_validate_json(raw), BRIEF).concepts[0]
    assert (cleaned.closing_line, cleaned.cta_hint, cleaned.chips) == (
        "",
        "",
        ("Organise themselves",),
    )


def lenient(raw: str) -> list[str]:
    return plan_problems(PlanDraft.model_validate_json(raw), BRIEF, ARCHETYPES, craft=False)


def _shifted(concept: dict[str, object], shift: int) -> dict[str, object]:
    scenes = concept["scenes"]
    assert isinstance(scenes, list)
    moved = [{**s, "screenshot_index": (s["screenshot_index"] + shift) % 3} for s in scenes]
    return {**concept, "scenes": moved, "hook": f"{concept['hook']} {shift}"}
