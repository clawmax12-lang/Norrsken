"""Claim-level grounding for written copy (FR-02, PRD §15, §16 "claim-level grounding").

Copy may be phrased freely, but no fact may be invented. The checks are deterministic:

1. Every number in the copy appears in the brief.
2. Every name (a capitalised word that does not start a sentence, or a word with an inner
   capital or digit such as "iOS") appears in the brief, so no other company, product,
   integration or customer can be named. Lines where every word is capitalised (Title Case)
   are exempt from the mid-sentence rule only.
3. No unverifiable superlative ("bäst", "fastest", "#1") and no quotation marks, so no
   ranking or testimonial can be implied. No hype word ("blixtsnabb", "seamless") either,
   even when the brief uses one: it reads as an ad, and it is not a benefit.
4. Every listed claim cites a brief field whose text contains its ``source_span`` verbatim.

What the checks cannot see (a reworded benefit that overstates the brief) is left to the
claims list, the explanation and the customer's own review.
"""

import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from preflight.contracts import Brief, BriefField

from .grounding import FUNCTION_WORDS

_NUMBER = re.compile(r"\d+(?:[.,]\d+)?")
_DIGIT_SPACE = re.compile(r"(?<=\d)[\s\u00a0\u202f](?=\d{3}\b)")
_WORD = re.compile(r"[\w'\u2019-]+")
_SENTENCE_END = re.compile(r"[.!?:;]$")
STEM_LENGTH = 5
MIN_CONTENT_LENGTH = 3
_QUOTES = frozenset('"“”„«»')

SUPERLATIVES = frozenset(
    {
        # Swedish
        "bäst", "bästa", "snabbast", "snabbaste", "billigast", "billigaste", "störst",
        "största", "ledande", "marknadsledande", "världens", "garanterat", "garanterad",
        "nummer", "unik", "unika", "överlägsen", "överlägsna",
        # English
        "best", "fastest", "cheapest", "biggest", "largest", "leading", "world's", "worlds",
        "guaranteed", "guarantee", "unbeatable", "unrivalled", "unrivaled", "#1",
    }
)  # fmt: skip

# Word beginnings, so inflections ("blixtsnabba", "sömlöst") are caught too.
HYPE_STEMS = (
    # Swedish
    "blixtsnabb", "supersnabb", "busenk", "superenk", "jätteenk", "sömlös", "revolutioner",
    "banbrytande", "magisk", "otrolig", "fantastisk", "världsklass", "enastående", "makalös",
    "extremt", "galet",
    # English
    "seamless", "lightning", "blazing", "revolutionary", "game-chang", "incredibl", "amazing",
    "magical", "effortless", "unparalleled", "cutting-edge", "next-level", "supercharg",
)  # fmt: skip


@dataclass(frozen=True)
class CopyLine:
    """One piece of copy (on-screen or spoken) and where it sits in the plan."""

    location: str
    text: str


@dataclass(frozen=True)
class ClaimRef:
    """A claim as the planner listed it: the statement, the field it cites and the span."""

    text: str
    source_field: BriefField
    source_span: str


def brief_corpus(brief: Brief) -> str:
    """All sourceable brief text in one string (the only place facts may come from)."""
    return " ".join(brief.field_text(field) for field in BriefField)


def brief_mentions(brief: Brief, name: str) -> bool:
    """True when every word of ``name`` (for example "Apple Pay") appears in the brief."""
    words = _words(name)
    return bool(words) and words <= _words(brief_corpus(brief))


def proof_numbers(brief: Brief) -> set[str]:
    """Numbers in proof_points: the strongest evidence a video can show."""
    return _numbers(brief.field_text(BriefField.PROOF_POINTS))


def numbers_in(text: str) -> set[str]:
    """Numbers in ``text``, normalised like the brief's ("1 200" and "1200" match)."""
    return _numbers(text)


def content_stems(text: str) -> set[str]:
    """Five-letter stems of the meaningful words, so "betalning" matches "betala"."""
    return {
        word.casefold()[:STEM_LENGTH]
        for word in _WORD.findall(text)
        if len(word) >= MIN_CONTENT_LENGTH and word.casefold() not in FUNCTION_WORDS
    }


def brief_names(brief: Brief) -> set[str]:
    """Names the brief uses (partners, integrations, the product itself), casefolded."""
    names = {name.casefold() for field in BriefField for name in _names(brief.field_text(field))}
    return names | _words(brief.product_name)


def copy_problems(lines: Iterable[CopyLine], claims: Sequence[ClaimRef], brief: Brief) -> list[str]:
    """Every grounding problem in ``lines`` and ``claims``, worded for a repair prompt."""
    corpus = brief_corpus(brief)
    numbers = _numbers(corpus)
    names = _words(corpus)
    problems: list[str] = []
    for line in lines:
        problems.extend(_line_problems(line, numbers, names))
    problems.extend(_claim_problems(claims, brief))
    return problems


def _line_problems(line: CopyLine, numbers: set[str], names: set[str]) -> list[str]:
    problems = []
    unknown_numbers = sorted(set(_numbers(line.text)) - numbers)
    if unknown_numbers:
        problems.append(
            f'{line.location}: "{line.text}" uses the number(s) {", ".join(unknown_numbers)}, '
            "which the brief does not contain; only use numbers from the brief"
        )
    unknown_names = [name for name in _names(line.text) if not _known_name(name, names)]
    if unknown_names:
        problems.append(
            f'{line.location}: "{line.text}" names {", ".join(unknown_names)}, which the brief '
            "does not mention; never name a company, product or customer the brief does not"
        )
    hype = sorted({word for word in _tokens(line.text) if word.casefold() in SUPERLATIVES})
    if hype:
        problems.append(
            f'{line.location}: "{line.text}" uses {", ".join(hype)}, an unverifiable '
            "superlative; state a concrete benefit instead"
        )
    hyped = sorted({word for word in _tokens(line.text) if _is_hype(word)})
    if hyped:
        problems.append(
            f'{line.location}: "{line.text}" uses {", ".join(hyped)}, a hype word; say what '
            "the product actually does instead"
        )
    if any(char in _QUOTES for char in line.text):
        problems.append(
            f'{line.location}: "{line.text}" contains quotation marks; never quote anyone'
        )
    return problems


def _is_hype(word: str) -> bool:
    return word.casefold().startswith(HYPE_STEMS)


def _known_name(name: str, names: set[str]) -> bool:
    """In the brief, or a compound whose capitalised parts are ("Stripe-", "Pay-kassa")."""
    if name.casefold() in names:
        return True
    capitalised = [part for part in name.split("-") if any(char.isupper() for char in part)]
    return bool(capitalised) and all(part.casefold() in names for part in capitalised)


def _claim_problems(claims: Sequence[ClaimRef], brief: Brief) -> list[str]:
    problems = []
    for index, claim in enumerate(claims, start=1):
        field_text = _normalise(brief.field_text(claim.source_field))
        if not field_text or _normalise(claim.source_span) not in field_text:
            problems.append(
                f'claim {index} ("{claim.text}"): source_span "{claim.source_span}" is not '
                f"text of brief field {claim.source_field.value}; quote that field exactly"
            )
    return problems


def _normalise(text: str) -> str:
    return " ".join(text.casefold().split())


def _numbers(text: str) -> set[str]:
    joined = _DIGIT_SPACE.sub("", text)
    return {number.replace(",", ".") for number in _NUMBER.findall(joined)}


def _tokens(text: str) -> list[str]:
    return _WORD.findall(text) + (["#1"] if "#1" in text else [])


def _words(text: str) -> set[str]:
    """Words of ``text``; a compound like "Stripe-checkout" also yields "stripe" and "checkout"."""
    words = {word.casefold() for word in _WORD.findall(text)}
    return words | {part for word in words for part in word.split("-") if part}


def _names(text: str) -> list[str]:
    """Words that look like names: mid-sentence capitals or inner capitals/digits."""
    pieces = text.split()
    words = [piece.strip(".,!?:;()[]") for piece in pieces]
    title_case = len(words) > 1 and all(word[:1].isupper() for word in words if word)
    names: list[str] = []
    sentence_start = True
    for piece, word in zip(pieces, words, strict=True):
        if word and word.casefold() not in FUNCTION_WORDS:
            inner = any(char.isupper() for char in word[1:]) or (
                any(char.isdigit() for char in word) and any(char.isalpha() for char in word)
            )
            mid_capital = word[:1].isupper() and not sentence_start and not title_case
            if inner or mid_capital:
                names.append(word)
        sentence_start = bool(_SENTENCE_END.search(piece))
    return list(dict.fromkeys(names))
