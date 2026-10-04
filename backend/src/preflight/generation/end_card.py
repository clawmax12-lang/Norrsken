"""Strings for the 3 s end card. Never invent a call to action.

The headline is the concept's closing line when the planner wrote one (claim-checked like all
copy); older concepts fall back to the goal note or the one-liner. The button is the concept's
call to action, which the planner already resolved from ``buyer_cta``, a goal note that fits
the audience, or a short action for the audience.
"""

from preflight.contracts import Brief, BriefField, CreativeConcept
from preflight.timing import BUTTON_MAX_WORDS


def end_card_fields(brief: Brief, concept: CreativeConcept) -> dict[str, str | None]:
    """Wordmark, headline, button label and optional logo path from the brief and concept."""
    note = (brief.goal_note or "").strip()
    if concept.closing_line:
        headline, headline_field = concept.closing_line, concept.hook_source_field
    elif note:
        headline, headline_field = note, BriefField.GOAL_NOTE
    else:
        headline, headline_field = brief.one_liner, BriefField.ONE_LINER
    button = concept.cta
    if (
        concept.cta_source_field is BriefField.GOAL_NOTE
        and note
        and len(note.split()) <= BUTTON_MAX_WORDS
    ):
        button = note
    return {
        "wordmark": brief.product_name,
        "headline": headline,
        "headline_source_field": headline_field.value,
        "cta": button,
        "logo": brief.logo,
    }
