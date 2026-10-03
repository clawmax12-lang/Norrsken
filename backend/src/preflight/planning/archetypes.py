"""The fixed hypotheses a plan chooses from (FR-02).

Archetypes are assigned to variants by index, so the three concepts differ by construction
instead of by hoping the model varies them. Every archetype can be written using only the
customer's own brief text: none needs a testimonial, a statistic or a customer count, which
Preflight must never invent (PRD §15).
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
        "problem first",
        "Open on the situation the audience is in, using only words the brief gives for it, "
        "then present the product as the way out.",
    ),
    Archetype(
        "outcome first",
        "Open on what the one-liner says the product achieves, then show how with the screens.",
    ),
    Archetype(
        "product first",
        "Open on the product itself: its name and the one-liner, then walk through the screens.",
    ),
    Archetype(
        "demo first",
        "Open straight on the most telling screenshot with minimal copy, and let the screens "
        "carry the story; text only labels what is visible.",
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
