from pathlib import Path

import pytest

from preflight.contracts import Confidence, Reason, TokenSavings
from preflight.errors import PreflightValidationError
from preflight.export import render_launch_brief
from tests.export.seed import make_ranking, make_report
from tests.factories import make_brief, make_concept

GOLDEN = Path(__file__).parent / "golden"
FORBIDDEN_PHRASES = (
    "will go viral",
    "predicts sales",
    "reads emotions",
    "mind reading",
    "TRIBE output",
)


def winner_concept():
    return make_concept("A", hook="Notes that sort themselves", hypothesis="outcome first")


def runner_up_concept():
    return make_concept("B", hook="Stop losing your notes", hypothesis="problem first")


def render_two_variants() -> str:
    return render_launch_brief(
        make_brief(), winner_concept(), runner_up_concept(), make_ranking(), make_report()
    )


def render_one_variant_brain_off() -> str:
    ranking = make_ranking(
        ("A",),
        confidence=Confidence.LOW,
        rule="Only one simulator ran, so confidence is low.",
        excluded={"B": "render failed twice"},
    )
    report = make_report("A", None, brain_sim=False, token_savings=TokenSavings())
    return render_launch_brief(make_brief(), winner_concept(), None, ranking, report)


def test_two_variant_brief_matches_the_golden_file():
    assert render_two_variants() == (GOLDEN / "launch_brief_two_variants.md").read_text()


def test_single_variant_brain_off_brief_matches_the_golden_file():
    expected = (GOLDEN / "launch_brief_one_variant_brain_off.md").read_text()

    assert render_one_variant_brain_off() == expected


@pytest.mark.parametrize("render", [render_two_variants, render_one_variant_brain_off])
def test_the_brief_never_promises_outcomes_or_uses_banned_wording(render):
    text = render().lower()

    assert not [phrase for phrase in FORBIDDEN_PHRASES if phrase.lower() in text]
    assert "live a/b test" in text
    assert "guarantees no outcome" in text


def test_brain_sim_off_says_so_and_brain_sim_on_does_not():
    assert "Brain sim off" in render_one_variant_brain_off()
    assert "Brain sim off" not in render_two_variants()


def test_confidence_label_and_rule_are_stated():
    assert "Confidence: **High**. Rule: High when every simulator ranks the same winner." in (
        render_two_variants()
    )
    assert "Confidence: **Low**" in render_one_variant_brain_off()


def test_low_confidence_adds_a_caution_and_high_confidence_does_not():
    assert "starting hypothesis" in render_one_variant_brain_off()
    assert "starting hypothesis" not in render_two_variants()


def test_reasons_are_timestamped_and_name_the_scene():
    assert '- 0:11, scene 4 ("Notes that organise themselves"): Attention drops' in (
        render_two_variants()
    )


def test_timestamps_over_a_minute_use_minutes_and_seconds():
    report = make_report(reasons={"A": (Reason(t=75.9, scene_index=0, text="late"),), "B": ()})

    text = render_launch_brief(
        make_brief(), winner_concept(), runner_up_concept(), make_ranking(), report
    )

    assert "- 1:15, scene 1" in text
    assert "No reasons recorded." in text


def test_a_reason_pointing_past_the_last_scene_still_renders():
    report = make_report(reasons={"A": (Reason(t=1, scene_index=9, text="odd"),), "B": ()})

    text = render_launch_brief(
        make_brief(), winner_concept(), runner_up_concept(), make_ranking(), report
    )

    assert "- 0:01, scene 10: odd" in text


def test_token_savings_are_the_measured_numbers():
    assert "6 Condense calls sent 7,800 of 12,000 input tokens, saving 4,200 (35.0%)" in (
        render_two_variants()
    )


def test_zero_calls_reports_no_savings_rather_than_a_number():
    text = render_one_variant_brain_off()

    assert "No Condense calls were recorded" in text
    assert "%" not in text


def test_excluded_variants_are_listed_with_their_reason():
    assert "Variant B was left out: render failed twice" in render_one_variant_brain_off()


def test_winner_concept_must_be_the_reports_winner():
    with pytest.raises(PreflightValidationError, match="winner concept is B"):
        render_launch_brief(
            make_brief(), runner_up_concept(), runner_up_concept(), make_ranking(), make_report()
        )


def test_runner_up_concept_must_match_the_report():
    with pytest.raises(PreflightValidationError, match="runner-up concept is None"):
        render_launch_brief(make_brief(), winner_concept(), None, make_ranking(), make_report())
    with pytest.raises(PreflightValidationError, match="runner-up concept is B"):
        render_launch_brief(
            make_brief(),
            winner_concept(),
            runner_up_concept(),
            make_ranking(("A",)),
            make_report("A", None),
        )
