"""The fixed hypotheses a plan chooses from (FR-02).

Archetypes are assigned to variants by index, so the three concepts differ by construction
instead of by hoping the model varies them. Each archetype is a selling angle (what the film
leads with), not a scene order, so an A/B test compares messages. Every angle can be written
from the customer's own facts: none needs a testimonial, statistic or customer count that the
brief does not contain, which Preflight must never invent (PRD §15).
"""

from dataclasses import dataclass

from preflight.errors import PreflightValidationError


@dataclass(frozen=True)
class Archetype:
    """A creative hypothesis: ``name`` becomes ``CreativeConcept.hypothesis``."""

    name: str
    guidance: str


ARCHETYPES = (
    Archetype(
        "speed and ease",
        "Lead with how quick or effortless the product makes the audience's job, as far as "
        "the brief supports it. Hook: a short promise about speed or ease. Open on the screen "
        "where that happens and zoom into the control that does it.",
    ),
    Archetype(
        "business outcome",
        "Lead with what the audience gains (for example more completed purchases or less "
        "manual work), stated only as strongly as the brief allows. Hook: the gain in the "
        "audience's words. Show the result screen early, then how the product gets there.",
    ),
    Archetype(
        "product demo",
        "Lead straight into the product doing its main job. Hook: name the job in a few "
        "words. Each scene shows one step on a different screen or zoomed region, and the "
        "voice explains the step while the text labels it.",
    ),
    Archetype(
        "pain relief",
        "Open on the friction the audience has today, in words the brief supports, then show "
        "the product removing it.",
    ),
    Archetype(
        "audience first",
        "Open by addressing the audience described in the brief, then connect them to the "
        "product and its screens.",
    ),
)


def archetypes_for(count: int) -> tuple[Archetype, ...]:
    """Return the first ``count`` archetypes (variant ``A`` gets the first, and so on).

    Raises:
        PreflightValidationError: ``count`` is outside ``1..len(ARCHETYPES)``.
    """
    if not 1 <= count <= len(ARCHETYPES):
        raise PreflightValidationError(
            f"cannot plan {count} concepts: between 1 and {len(ARCHETYPES)} distinct "
            "hypotheses are available"
        )
    return ARCHETYPES[:count]
