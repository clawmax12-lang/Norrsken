import json

import pytest

from preflight.contracts import BriefField, Shot
from preflight.planning.archetypes import archetypes_for
from preflight.planning.draft import (
    PlanDraft,
    assemble_concepts,
    excluded_screenshots,
    plan_notes,
    shots_for,
)
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


def test_a_buyer_cta_that_fits_the_audience_wins_and_silences_the_note() -> None:
    brief = make_brief(goal_note="Book an investor demo", buyer_cta="Book a table")
    draft = draft_with()

    concepts = assemble_concepts(draft, brief, ARCHETYPES)

    assert all(c.cta == "Book a table" for c in concepts)
    assert all(c.cta_source_field is BriefField.BUYER_CTA for c in concepts)
    assert plan_notes(draft, brief).messages == ()


def test_a_buyer_cta_for_the_wrong_audience_is_replaced_and_explained() -> None:
    brief = make_brief(buyer_cta="Betala med Apple Pay", audience="E-handlare")
    draft = draft_with(
        cta_fits_audience=False, cta_note="speaks to shoppers", audience_cta="Skapa konto"
    )

    concepts = assemble_concepts(draft, brief, ARCHETYPES)

    assert all(c.cta == "Skapa konto" for c in concepts)
    assert all(c.cta_source_field is BriefField.PRODUCT_NAME for c in concepts)
    message = plan_notes(draft, brief).messages[0]
    assert message.startswith('Your call to action "Betala med Apple Pay" speaks to someone')
    assert "change buyer_cta" in message


def test_a_screen_too_small_for_a_sharp_video_is_reported() -> None:
    screens = {
        0: ScreenImage(1066, 756, crop=(0.4, 0.08, 0.27, 0.8)),
        1: ScreenImage(1170, 2532),
    }

    notes = plan_notes(draft_with(), make_brief(), screens)

    assert len(notes.messages) == 1
    assert notes.messages[0].startswith("Screenshot 1: its screen is only 288 px wide")
    assert notes.smallest_screen_px == 288


def test_notes_follow_a_swedish_brief() -> None:
    brief = make_brief(buyer_cta="Betala med Apple Pay", audience="E-handlare")
    draft = draft_with(language="sv", cta_fits_audience=False, audience_cta="Skapa konto")
    screens = {0: ScreenImage(1066, 756, crop=(0.4, 0.08, 0.27, 0.8))}

    notes = plan_notes(draft, brief, screens)

    assert notes.messages[0].startswith("Skärmdump 1: skärmen i bilden är bara 288 px bred")
    assert notes.messages[1].startswith('Er uppmaning "Betala med Apple Pay" vänder sig till')
    assert "ändra buyer_cta" in notes.messages[1]


def test_mockup_crops_reach_every_scene_and_move_focus_into_the_crop() -> None:
    raw = json.loads(plan_json())
    raw["concepts"][0]["scenes"][0]["focus"] = [0.45, 0.3, 0.1, 0.2]
    draft = PlanDraft.model_validate(raw)
    crop = (0.4, 0.1, 0.25, 0.8)

    concepts = assemble_concepts(draft, make_brief(), ARCHETYPES, {0: ScreenImage(1066, 756, crop)})

    first = concepts[0].scenes[0]
    assert first.crop == crop
    assert first.focus == pytest.approx((0.2, 0.25, 0.4, 0.25))
    assert all(s.crop is None for s in concepts[0].scenes if s.screenshot != first.screenshot)


def test_variants_open_on_different_shots_when_screens_are_sharp() -> None:
    draft = PlanDraft.model_validate(json.loads(plan_json()))
    sharp = {i: ScreenImage(1170, 2532) for i in range(4)}

    concepts = assemble_concepts(draft, make_brief(), ARCHETYPES, sharp)

    assert len({c.scenes[0].shot for c in concepts}) == 3
    assert all(len({s.shot for s in c.scenes}) >= 3 for c in concepts if len(c.scenes) >= 4)


def test_small_or_wide_screens_never_get_a_close_up_or_takeover() -> None:
    small = ScreenImage(284, 600)
    wide = ScreenImage(1920, 1080)

    for position in range(3):
        for screen in (small, wide, None):
            assert set(shots_for(position, [screen] * 4)) == {Shot.HERO, Shot.TILT}


def test_close_up_needs_more_pixels_than_takeover() -> None:
    mid = ScreenImage(560, 1200)

    assert shots_for(0, [mid] * 3) == [Shot.HERO, Shot.TILT, Shot.TAKEOVER]
