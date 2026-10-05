import json

import pytest

from preflight.contracts import BriefField
from preflight.planning.archetypes import archetypes_for
from preflight.planning.draft import PlanDraft, assemble_concepts, excluded_screenshots, plan_notes
from preflight.planning.screens import ScreenImage
from preflight.planning.validation import plan_problems
from tests.factories import make_brief
from tests.planning.helpers import plan_json

ARCHETYPES = archetypes_for(3)


def draft_with(**extra: object) -> PlanDraft:
    raw = json.loads(plan_json())
    return PlanDraft.model_validate({**raw, **extra})


SHOPIFY = {"index": 2, "shows_product": False, "other_brand": "Shopify", "note": "admin"}


def test_a_screenshot_of_another_brand_is_left_out_and_explained() -> None:
    brief = make_brief()
    draft = draft_with(screenshots=[SHOPIFY])

    notes = plan_notes(draft, brief)

    assert notes.excluded_screenshots == (2,)
    assert notes.messages[0].startswith("Screenshot 3 shows Shopify, not Acme Notes")


def test_screenshots_are_kept_when_too_few_would_remain() -> None:
    brief = make_brief()
    two_bad = [SHOPIFY, {**SHOPIFY, "index": 1}]
    draft = draft_with(screenshots=two_bad)

    assert excluded_screenshots(draft, brief) == ()
    assert "replace them before launching" in plan_notes(draft, brief).messages[0]


def test_a_partner_the_brief_names_is_not_another_brand() -> None:
    brief = make_brief(one_liner="Checkout with Apple Pay built in")
    draft = draft_with(screenshots=[{**SHOPIFY, "shows_product": True, "other_brand": "Apple Pay"}])

    assert excluded_screenshots(draft, brief) == ()
    assert plan_notes(draft, brief).messages == ()


def test_concepts_may_not_use_an_excluded_screenshot() -> None:
    brief = make_brief()
    draft = draft_with(screenshots=[SHOPIFY])

    problems = plan_problems(draft, brief, ARCHETYPES)

    assert problems
    assert all("screenshot" in p for p in problems)


def test_a_goal_note_for_the_wrong_audience_never_becomes_the_button() -> None:
    brief = make_brief(goal_note="Book an investor demo", audience="restaurant owners")
    draft = draft_with(cta_fits_audience=False, cta_note="written for investors")

    concepts = assemble_concepts(draft, brief, ARCHETYPES)
    notes = plan_notes(draft, brief)

    assert all(c.cta == "Acme Notes" for c in concepts)
    assert "speaks to someone other than your audience" in notes.messages[0]
    assert "written for investors" in notes.messages[0]


def test_the_buyer_cta_always_wins_and_silences_the_note() -> None:
    brief = make_brief(goal_note="Book an investor demo", buyer_cta="Book a table")
    draft = draft_with(cta_fits_audience=False)

    concepts = assemble_concepts(draft, brief, ARCHETYPES)

    assert all(c.cta == "Book a table" for c in concepts)
    assert all(c.cta_source_field is BriefField.BUYER_CTA for c in concepts)
    assert plan_notes(draft, brief).messages == ()


def test_a_screen_too_small_for_a_sharp_video_is_reported() -> None:
    screens = {
        0: ScreenImage(1066, 756, crop=(0.4, 0.08, 0.27, 0.8)),
        1: ScreenImage(1170, 2532),
    }

    notes = plan_notes(draft_with(), make_brief(), screens)

    assert len(notes.messages) == 1
    assert notes.messages[0].startswith("Screenshot 1: its screen is only 288 px wide")


def test_mockup_crops_reach_every_scene_and_move_focus_into_the_crop() -> None:
    raw = json.loads(plan_json())
    raw["concepts"][0]["scenes"][0]["focus"] = [0.45, 0.3, 0.1, 0.2]
    draft = PlanDraft.model_validate(raw)
    crop = (0.4, 0.1, 0.25, 0.8)

    concepts = assemble_concepts(draft, make_brief(), ARCHETYPES, {0: crop})

    first = concepts[0].scenes[0]
    assert first.crop == crop
    assert first.focus == pytest.approx((0.2, 0.25, 0.4, 0.25))
    assert all(s.crop is None for s in concepts[0].scenes if s.screenshot != first.screenshot)
