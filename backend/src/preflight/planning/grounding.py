"""Deterministic check that on-screen text is traceable to the brief (FR-02, PRD §9 guardrails).

Rule: every word of a piece of on-screen text (hook, scene text, CTA) must appear in the text
of the brief field it cites as its ``source_field``, ignoring case and punctuation. Words may
be dropped, reordered or recombined, but none may be added, so no claim, number, name or
testimonial can be invented. The exceptions are :data:`FUNCTION_WORDS` (grammatical glue
that carries no claim) and the words of the brief's product name, which any text may use
because naming the customer's own product claims nothing.

This is a word-level rule, not a semantic one: it cannot tell that a recombination changed the
meaning, and inflections ("organises" for "organise") count as new words. Both are accepted
so that the check stays deterministic and explainable.
"""

import re
from dataclasses import dataclass

from preflight.contracts import Brief, BriefField, CreativeConcept

FUNCTION_WORDS = frozenset(
    {
        "a", "an", "the",  # articles
        "and", "or", "but", "so", "than",  # conjunctions
        "of", "to", "for", "in", "on", "at", "with", "from", "by", "as", "into",  # prepositions
        "is", "are", "be", "it", "its", "this", "that",  # copulas and demonstratives
        "you", "your", "we", "our",  # pronouns
        # Swedish glue (same role: no claim)
        "och", "eller", "men", "så", "att", "som", "en", "ett", "den", "det", "de",
        "för", "med", "på", "i", "av", "till", "från", "om", "utan", "under",
        "din", "ditt", "dina", "vår", "vårt", "våra", "er", "ert", "era",
        "är", "vara", "var", "bli", "blir",
    }
)  # fmt: skip
_WORD = re.compile(r"\w+")


def words(text: str) -> tuple[str, ...]:
    """Lower-cased words of ``text`` with punctuation removed."""
    return tuple(_WORD.findall(text.casefold()))


def ungrounded_words(text: str, source_text: str) -> tuple[str, ...]:
    """Words of ``text`` found neither in ``source_text`` nor in :data:`FUNCTION_WORDS`.

    Each offending word is listed once, in order of first appearance.
    """
    allowed = set(words(source_text)) | FUNCTION_WORDS
    return tuple(dict.fromkeys(word for word in words(text) if word not in allowed))


@dataclass(frozen=True)
class GroundingViolation:
    """One piece of on-screen text that uses words its cited source field does not contain."""

    location: str
    text: str
    source_field: BriefField
    words: tuple[str, ...]

    def describe(self) -> str:
        """A sentence precise enough to be fed back to the model for repair."""
        listed = ", ".join(f'"{word}"' for word in self.words)
        return (
            f'{self.location}: text "{self.text}" uses {listed}, which '
            f"{'is' if len(self.words) == 1 else 'are'} not in brief field "
            f"{self.source_field.value}; use only words from that field"
        )


def find_violations(concept: CreativeConcept, brief: Brief) -> tuple[GroundingViolation, ...]:
    """All grounding violations in ``concept`` (empty when every text is traceable)."""
    claims = [
        ("hook", concept.hook, concept.hook_source_field),
        *(
            (f"scene {index}", scene.text, scene.source_field)
            for index, scene in enumerate(concept.scenes, start=1)
        ),
        ("cta", concept.cta, concept.cta_source_field),
    ]
    violations = (
        GroundingViolation(
            location,
            text,
            field,
            ungrounded_words(text, f"{brief.field_text(field)} {brief.product_name}"),
        )
        for location, text, field in claims
    )
    return tuple(violation for violation in violations if violation.words)
