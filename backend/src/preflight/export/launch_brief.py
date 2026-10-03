"""FR-08: the Markdown launch brief, rendered by a pure function.

Wording follows PRD §12.8 and §15: the brief states what the pretest measured, labels its
confidence and the rule behind it, and sends the reader to a live A/B test to confirm.
It never promises reach, revenue or any other outcome.
"""

from collections.abc import Mapping

from preflight.contracts import (
    Brief,
    Confidence,
    CreativeConcept,
    Ranking,
    Reason,
    Report,
    SoundRecord,
)
from preflight.errors import PreflightValidationError

_CONFIDENCE_LABEL = {Confidence.HIGH: "High", Confidence.LOW: "Low"}

_LOW_CONFIDENCE_NOTE = "Treat the winner as a starting hypothesis and let the live A/B test decide."
_BRAIN_SIM_ON = "Brain sim: on. The ranking draws on the brain sim and the simulated viewers."
_BRAIN_SIM_OFF = (
    "Brain sim off. The ranking uses simulated viewers only; there is no brain data behind it."
)
_DISCLAIMER = (
    "This pretest ranks these variants against each other using simulated viewers. "
    "It is not a forecast of reach or revenue and it guarantees no outcome. "
    "Confirm the winner with a live A/B test before you commit budget."
)


def render_launch_brief(
    brief: Brief,
    concept_winner: CreativeConcept,
    concept_runner_up: CreativeConcept | None,
    ranking: Ranking,
    report: Report,
    sounds: Mapping[str, SoundRecord] | None = None,
) -> str:
    """Return the launch brief as Markdown.

    Args:
        brief: The customer's brief; supplies the product name.
        concept_winner: Concept of ``report.winner``.
        concept_runner_up: Concept of ``report.runner_up``, or ``None`` when only one variant
            finished the pretest.
        ranking: The scored ranking with its confidence label and rule.
        report: Reasons, next-time advice, token savings and whether the brain sim ran.
        sounds: Sound added to the exported videos, by variant; ``None`` or empty when they
            are the silent renders that were pretested.

    Raises:
        PreflightValidationError: The concepts do not match the report's winner and runner-up.
    """
    _require_matching_concepts(concept_winner, concept_runner_up, report)
    sections: list[str] = [
        f"# Launch brief: {brief.product_name}",
        f"Preflight pretested {len(ranking.order)} video variant"
        f"{'' if len(ranking.order) == 1 else 's'} for {brief.product_name} with simulated "
        "viewers. This brief says which to post, which to A/B test, and why.",
        _post_section(concept_winner),
        _ab_test_section(concept_winner, concept_runner_up),
        _why_section(concept_winner, concept_runner_up, report),
        _next_time_section(report),
        _trust_section(ranking, report),
        _token_savings_section(report),
    ]
    if sounds:
        sections.append(_sound_section(sounds))
    sections.append(f"## Before you launch\n\n{_DISCLAIMER}")
    return "\n\n".join(sections) + "\n"


def _require_matching_concepts(
    winner: CreativeConcept, runner_up: CreativeConcept | None, report: Report
) -> None:
    if winner.variant_id != report.winner:
        raise PreflightValidationError(
            f"winner concept is {winner.variant_id} but the report names {report.winner}"
        )
    expected = report.runner_up
    actual = runner_up.variant_id if runner_up else None
    if actual != expected:
        raise PreflightValidationError(
            f"runner-up concept is {actual} but the report names {expected}"
        )


def _describe(concept: CreativeConcept) -> str:
    """Variant, hook and hypothesis on one line."""
    return f'Variant {concept.variant_id}: "{concept.hook}" ({concept.hypothesis})'


def _post_section(winner: CreativeConcept) -> str:
    return f"## Post this\n\nPost {_describe(winner)}."


def _ab_test_section(winner: CreativeConcept, runner_up: CreativeConcept | None) -> str:
    if runner_up is None:
        body = (
            "No runner-up finished the pretest, so there is no second Preflight variant to test. "
            f"A/B test Variant {winner.variant_id} against the creative you would otherwise post."
        )
    else:
        body = (
            f"{_describe(runner_up)}\n\n"
            f"Test it live against Variant {winner.variant_id}; the pretest only ranks them."
        )
    return f"## A/B test it against\n\n{body}"


def _why_section(winner: CreativeConcept, runner_up: CreativeConcept | None, report: Report) -> str:
    parts = ["## Why", _reasons_block(winner, "winner", report)]
    if runner_up is not None:
        parts.append(_reasons_block(runner_up, "runner-up", report))
    return "\n\n".join(parts)


def _reasons_block(concept: CreativeConcept, role: str, report: Report) -> str:
    lines = [f"### Variant {concept.variant_id} ({role})", ""]
    reasons = report.reasons.get(concept.variant_id, ())
    lines += [_reason_line(concept, reason) for reason in reasons] or ["- No reasons recorded."]
    return "\n".join(lines)


def _reason_line(concept: CreativeConcept, reason: Reason) -> str:
    scene = f"scene {reason.scene_index + 1}"
    if reason.scene_index < len(concept.scenes):
        scene += f' ("{concept.scenes[reason.scene_index].text}")'
    return f"- {_clock(reason.t)}, {scene}: {reason.text}"


def _clock(seconds: float) -> str:
    whole = int(seconds)
    return f"{whole // 60}:{whole % 60:02d}"


def _next_time_section(report: Report) -> str:
    items = "\n".join(f"- {item}" for item in report.next_time) or "- Nothing recorded."
    return f"## Change next time\n\n{items}"


def _trust_section(ranking: Ranking, report: Report) -> str:
    lines = [
        "## How far to trust this ranking",
        "",
        f"- Confidence: **{_CONFIDENCE_LABEL[ranking.confidence]}**. Rule: {ranking.rule}",
    ]
    if ranking.confidence is Confidence.LOW:
        lines.append(f"- {_LOW_CONFIDENCE_NOTE}")
    scores = ", ".join(f"{variant} {ranking.scores[variant]:.2f}" for variant in ranking.order)
    lines.append(f"- Scores (0 to 1, relative to these variants only): {scores}")
    lines += [
        f"- Variant {variant} was left out: {why}" for variant, why in ranking.excluded.items()
    ]
    lines.append(f"- {_BRAIN_SIM_ON if report.brain_sim else _BRAIN_SIM_OFF}")
    return "\n".join(lines)


def _sound_section(sounds: Mapping[str, SoundRecord]) -> str:
    lines = [
        "## Sound in the exported videos",
        "",
        "Narration, music and sound effects were added after the pretest. The simulated "
        "viewers watched the silent renders, so the ranking above does not cover the audio.",
        "",
    ]
    for variant, record in sorted(sounds.items()):
        lines.append(f"- Variant {variant}: {_sound_line(record)}")
    return "\n".join(lines)


def _sound_line(record: SoundRecord) -> str:
    if record.narrated:
        spoken = "; ".join(f'"{line.text}"' for line in record.narration)
        return (
            f"narrated by the Gemini voice {record.voice}, reading only the on-screen text "
            f"({spoken}), with music and sound effects."
        )
    return f"music and sound effects only. {record.note or ''}".strip()


def _token_savings_section(report: Report) -> str:
    savings = report.token_savings
    if savings.calls == 0:
        body = "No Condense calls were recorded for this run, so no savings are reported."
    else:
        body = (
            f"{savings.calls} Condense calls sent {savings.input_tokens_sent:,} of "
            f"{savings.input_tokens_original:,} input tokens, saving {savings.tokens_saved:,} "
            f"({savings.percent}%). Output tokens: {savings.output_tokens:,}. "
            "Figures come from the Condense usage meter."
        )
    return f"## Measured token savings\n\n{body}"
