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
        "The first scene's text is the hook: the problem, using only audience or one-liner "
        "words, and the product name may be mixed in. It is not a label of a screenshot. Then "
        "show the product on one screen, then a different screen. Do not open with a yes/no "
        "question about whether this is for the audience. Do not put a confirmation or "
        "thank-you screen before the screen that leads to it.",
    ),
    Archetype(
        "outcome first",
        "The first scene's text is the hook: what the one-liner says the product achieves, "
        "not a label of a screenshot. Then walk the screens forward, each scene a different "
        "screenshot from the one before it. Do not put a confirmation or thank-you screen "
        "before the screen that leads to it.",
    ),
    Archetype(
        "product first",
        "The first scene's text is the hook: the product name and the one-liner, not a "
        "screenshot label. Then walk through different screens. Do not put a confirmation or "
        "thank-you screen before the screen that leads to it.",
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
