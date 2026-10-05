from preflight.contracts import PlanNotes
from preflight.scoring.production import MIN_FACTOR, production_for


def test_a_soft_screen_caps_the_score_at_half_and_says_why() -> None:
    production = production_for(PlanNotes(smallest_screen_px=284), "en")

    assert production is not None
    assert production.factor == MIN_FACTOR
    assert production.reasons == (
        "Production quality: the smallest screen in the videos is 284 px wide, so scores are "
        "capped at 50 %. Screenshots at least 600 px wide lift the cap.",
    )


def test_the_factor_grows_with_the_screen_until_it_is_sharp() -> None:
    middle = production_for(PlanNotes(smallest_screen_px=450), None)
    sharp = production_for(PlanNotes(smallest_screen_px=768), None)

    assert middle is not None
    assert middle.factor == 0.75
    assert sharp is not None
    assert sharp.factor == 1.0
    assert sharp.reasons == ()


def test_the_reason_follows_a_swedish_brief() -> None:
    production = production_for(PlanNotes(smallest_screen_px=300), "sv")

    assert production is not None
    assert production.reasons[0].startswith("Produktionskvalitet: den minsta skärmen")


def test_no_factor_without_a_measured_screen() -> None:
    assert production_for(PlanNotes(), "en") is None
