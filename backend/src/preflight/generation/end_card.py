"""Source-backed strings for the 3 s end card. Never invent a call to action."""

from preflight.contracts import Brief, BriefField, CreativeConcept
from preflight.timing import BUTTON_MAX_WORDS


def end_card_fields(brief: Brief, concept: CreativeConcept) -> dict[str, str | None]:
    """Wordmark, headline, button label and optional logo path from the brief and concept."""
    note = (brief.goal_note or "").strip()
    headline = note or brief.one_liner
    headline_field = BriefField.GOAL_NOTE if note else BriefField.ONE_LINER
    button = concept.cta
    if note and len(note.split()) <= BUTTON_MAX_WORDS:
        button = note
    return {
        "wordmark": brief.product_name,
        "headline": headline,
        "headline_source_field": headline_field.value,
        "cta": button,
        "logo": brief.logo,
    }
