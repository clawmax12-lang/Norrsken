"""Plan-level checks that need the brief: everything the schema alone cannot express (FR-02)."""

from collections.abc import Iterator
from itertools import pairwise

from pydantic import ValidationError

from preflight.contracts import Brief, BriefField, CreativeConcept

from .archetypes import Archetype
from .claims import ClaimRef, CopyLine, content_stems, copy_problems, numbers_in, proof_numbers
from .draft import (
    ConceptDraft,
    PlanDraft,
    SceneDraft,
    assemble_concepts,
    excluded_screenshots,
    variant_id,
)

MIN_VOICE_WORDS = 14
MAX_VOICE_WORDS = 36
MAX_SCENE_TEXT_WORDS = 8
VOICE_WORDS_PER_S = 3.2
MIN_AD_SCENES = 5


def plan_problems(
    draft: PlanDraft, brief: Brief, archetypes: tuple[Archetype, ...], *, craft: bool = True
) -> list[str]:
    """Every reason ``draft`` is unusable, phrased for the model; empty means acceptable.

    ``craft=False`` leaves out the craft rules (a proof number on screen, the voice echoing
    the text, each line's pace): a plan missing only those still makes a truthful, timed film.
    It also skips the optional end-card copy, which :func:`without_unsourced_extras` drops
    when it is not grounded.
    """
    if len(draft.concepts) != len(archetypes):
        return [f"return exactly {len(archetypes)} concepts, not {len(draft.concepts)}"]
    index_problems = _screenshot_index_problems(draft, len(brief.screenshots))
    if index_problems:
        return index_problems
    sequence_problems = [
        *_screenshot_sequence_problems(draft, len(brief.screenshots)),
        *_excluded_screenshot_problems(draft, brief),
        *_coverage_problems(draft, brief),
        *_variety_problems(draft, brief),
    ]
    try:
        concepts = assemble_concepts(draft, brief, archetypes)
    except ValidationError as exc:
        return [
            *sequence_problems,
            *(f"concept does not satisfy the contract: {error['msg']}" for error in exc.errors()),
        ]
    # Everything at once: the model gets a single repair, so a problem reported later is fatal.
    return [
        *sequence_problems,
        *_set_problems(concepts),
        *_voice_problems(draft),
        *_cta_problems(draft, brief),
        *_copy_problems(draft, concepts, brief, extras=craft),
        *(craft_problems(draft, brief) if craft else ()),
    ]


def craft_problems(draft: PlanDraft, brief: Brief) -> list[str]:
    """Rules that make a stronger film but never make it untrue or mistimed."""
    return [
        *_proof_problems(draft, brief),
        *_pace_problems(draft),
        *_end_card_problems(draft, brief),
        *_cohesion_problems(draft, brief),
        *_text_voice_problems(draft),
        *_story_problems(draft),
    ]


# Second-person words a hook uses to talk to the audience, by brief language.
_YOU = {
    "sv": frozenset({"du", "din", "ditt", "dina", "dig", "ni", "er", "ert", "era"}),
    "en": frozenset({"you", "your", "you're", "yours"}),
}


def _story_problems(draft: PlanDraft) -> list[str]:
    """The ad's arc: a hook that talks to the audience, a fast cut, no ending first."""
    problems: list[str] = []
    you = _YOU.get(draft.language.casefold()[:2])
    confirmations = {note.index for note in draft.screenshots if note.confirmation}
    for c, concept in enumerate(draft.concepts):
        label = f"concept {variant_id(c)}"
        opener = concept.scenes[0]
        heard = f"{concept.hook} {opener.voice}".casefold().split()
        if you and not you & {word.strip(".,!?:;") for word in heard}:
            problems.append(
                f"{label}: the hook does not talk to the audience; ask them about their problem "
                f"or promise them the gain, in the second person ({', '.join(sorted(you))})"
            )
        if opener.screenshot_index in confirmations:
            problems.append(
                f"{label} opens on a confirmation screen (screenshot {opener.screenshot_index}); "
                "open on the screen where the problem or the action happens, and save the "
                "confirmation for the proof"
            )
        if len(concept.scenes) < MIN_AD_SCENES:
            problems.append(
                f"{label} has {len(concept.scenes)} scenes; use {MIN_AD_SCENES} or 6 so the "
                "picture changes every 2 to 3 seconds"
            )
    return problems


def _screenshot_index_problems(draft: PlanDraft, screenshot_count: int) -> list[str]:
    return [
        f"concept {variant_id(c)} scene {s}: screenshot_index {scene.screenshot_index} does not "
        f"exist; use 0 to {screenshot_count - 1}"
        for c, concept in enumerate(draft.concepts)
        for s, scene in enumerate(concept.scenes, start=1)
        if scene.screenshot_index >= screenshot_count
    ]


def _screenshot_sequence_problems(draft: PlanDraft, screenshot_count: int) -> list[str]:
    """Reject a repeated screen and a plan whose concepts are the same film reordered nowhere.

    A screenshot may follow itself only when the second scene zooms into a different region,
    so the picture still changes. The end card covers the last scene's picture, so a repeat
    into it is never seen.
    """
    if screenshot_count < 2:
        return []
    problems: list[str] = []
    sequences: list[tuple[int, ...]] = []
    for concept_index, concept in enumerate(draft.concepts):
        indexes = [scene.screenshot_index for scene in concept.scenes]
        sequences.append(tuple(indexes))
        for scene_index, (left, right) in enumerate(pairwise(concept.scenes[:-1]), start=1):
            if left.screenshot_index == right.screenshot_index and not _new_focus(left, right):
                problems.append(
                    f"concept {variant_id(concept_index)} scenes {scene_index} and "
                    f"{scene_index + 1} repeat screenshot_index {left.screenshot_index}; pick a "
                    "different screenshot or zoom into a different region with focus"
                )
    if len(sequences) >= 2 and len(set(sequences)) == 1:
        problems.append(
            "concepts must not share the same screenshot sequence; vary the order across A, B and C"
        )
    return problems


def _new_focus(left: SceneDraft, right: SceneDraft) -> bool:
    return right.focus is not None and right.focus != left.focus


def _excluded_screenshot_problems(draft: PlanDraft, brief: Brief) -> list[str]:
    excluded = set(excluded_screenshots(draft, brief))
    return [
        f"concept {variant_id(c)} scene {s}: screenshot_index {scene.screenshot_index} does not "
        "show the brief's product (you reported it under screenshots); use another index"
        for c, concept in enumerate(draft.concepts)
        for s, scene in enumerate(concept.scenes, start=1)
        if scene.screenshot_index in excluded and s < len(concept.scenes)
    ]


def _usable_screenshots(draft: PlanDraft, brief: Brief) -> int:
    return len(brief.screenshots) - len(excluded_screenshots(draft, brief))


def _coverage_problems(draft: PlanDraft, brief: Brief) -> list[str]:
    """Every usable screen is shown before one repeats; the end card hides the last scene."""
    usable = _usable_screenshots(draft, brief)
    problems = []
    for c, concept in enumerate(draft.concepts):
        body = concept.scenes[:-1]
        shown = len({scene.screenshot_index for scene in body})
        if shown < min(usable, len(body)):
            problems.append(
                f"concept {variant_id(c)} shows only {shown} of the {usable} usable screenshots "
                "before the end card (the end card covers the last scene's picture); show every "
                "screenshot once before repeating one"
            )
    return problems


def _variety_problems(draft: PlanDraft, brief: Brief) -> list[str]:
    """Concepts must look different from the first frame, not only read differently."""
    problems = []
    # Not "all different": with few screens that would force one concept to open on a
    # confirmation screen, before the screen that leads to it.
    openers = [concept.scenes[0].screenshot_index for concept in draft.concepts]
    if len(openers) > 1 and _usable_screenshots(draft, brief) > 1 and len(set(openers)) == 1:
        problems.append(
            f"every concept opens on screenshot {openers[0]}; open at least one angle on a "
            "different screen"
        )
    hooks = [concept.hook.casefold().strip() for concept in draft.concepts]
    if len(set(hooks)) < len(hooks):
        problems.append("every concept needs its own hook; two concepts open with the same words")
    return problems


def _cta_problems(draft: PlanDraft, brief: Brief) -> list[str]:
    """When the brief's own call to action speaks to someone else, the model supplies one."""
    given = (brief.buyer_cta or "").strip() or (brief.goal_note or "").strip()
    if not given or draft.cta_fits_audience or draft.audience_cta.strip():
        return []
    return [
        "you reported that the brief's call to action does not fit the audience; write a 2 to "
        "4 word action for the audience in audience_cta"
    ]


def _set_problems(concepts: tuple[CreativeConcept, ...]) -> list[str]:
    """The invariants of the whole plan: sequential unique ids and distinct hypotheses."""
    problems: list[str] = []
    if [c.variant_id for c in concepts] != [variant_id(i) for i in range(len(concepts))]:
        problems.append("variant ids must be A, B, C... in order")
    if len({c.hypothesis for c in concepts}) != len(concepts):
        problems.append("every concept needs a distinct hypothesis")
    return problems


def _voice_problems(draft: PlanDraft) -> list[str]:
    """The narration must run through the whole film and fit it."""
    problems: list[str] = []
    for c, concept in enumerate(draft.concepts):
        label = f"concept {variant_id(c)}"
        body = concept.scenes[:-1]
        silent = [s for s, scene in enumerate(body, start=1) if not scene.voice]
        if silent:
            problems.append(
                f"{label}: scenes {', '.join(map(str, silent))} have no voice line; every scene "
                "before the end card needs one so the narration never stops"
            )
        words = sum(len(scene.voice.split()) for scene in body)
        if words and not MIN_VOICE_WORDS <= words <= MAX_VOICE_WORDS:
            problems.append(
                f"{label}: the voice lines before the end card have {words} words; write "
                f"{MIN_VOICE_WORDS} to {MAX_VOICE_WORDS} so they fill 12 seconds"
            )
        problems.extend(
            f'{label} scene {s}: on-screen text "{scene.text}" has more than '
            f"{MAX_SCENE_TEXT_WORDS} words; keep it short and let the voice explain"
            for s, scene in enumerate(body, start=1)
            if len(scene.text.split()) > MAX_SCENE_TEXT_WORDS
        )
    return problems


def _pace_problems(draft: PlanDraft) -> list[str]:
    """A line too long for its scene; voice timing lengthens the scene, at the others' cost."""
    return [
        f"concept {variant_id(c)} scene {s}: the voice line has {len(scene.voice.split())} "
        f"words for a {scene.duration_s} s scene; shorten it or lengthen the scene"
        for c, concept in enumerate(draft.concepts)
        for s, scene in enumerate(concept.scenes[:-1], start=1)
        if len(scene.voice.split()) > scene.duration_s * VOICE_WORDS_PER_S + 1
    ]


def _proof_problems(draft: PlanDraft, brief: Brief) -> list[str]:
    """A brief with numbers in proof_points is wasted by a film that shows none of them."""
    numbers = proof_numbers(brief)
    if not numbers:
        return []
    listed = ", ".join(sorted(numbers))
    return [
        f"concept {variant_id(c)} uses none of the numbers in proof_points ({listed}); put at "
        "least one in a scene's text or voice, it is the strongest proof the brief has"
        for c, concept in enumerate(draft.concepts)
        if not numbers & numbers_in(" ".join(_concept_copy(concept)))
    ]


def _end_card_problems(draft: PlanDraft, brief: Brief) -> list[str]:
    """The last frame sells with proof: a number in the headline and in at least one chip."""
    numbers = proof_numbers(brief)
    if not numbers:
        return []
    problems: list[str] = []
    for c, concept in enumerate(draft.concepts):
        label = f"concept {variant_id(c)}"
        if concept.closing_line and not numbers & numbers_in(concept.closing_line):
            problems.append(
                f"{label}: closing_line {concept.closing_line!r} has no proof number; make it "
                "the strongest benefit with one of the brief's numbers"
            )
        if concept.chips and not any(numbers & numbers_in(chip) for chip in concept.chips):
            problems.append(
                f"{label}: chips {list(concept.chips)} are not proofs; make them concrete "
                "facts from proof_points, at least one with its number"
            )
    return problems


def _cohesion_problems(draft: PlanDraft, brief: Brief) -> list[str]:
    """One film, not a list: the voice names the product, the end card sums up."""
    product = brief.product_name.casefold()
    problems: list[str] = []
    for c, concept in enumerate(draft.concepts):
        label = f"concept {variant_id(c)}"
        voice = " ".join(scene.voice for scene in concept.scenes).casefold()
        if product not in voice:
            problems.append(
                f"{label}: the voice never says {brief.product_name!r}; say it once where the "
                "product enters, so viewers remember whose ad it was"
            )
        texts = {_bare_line(scene.text) for scene in concept.scenes}
        if concept.closing_line and _bare_line(concept.closing_line) in texts:
            problems.append(
                f"{label}: closing_line {concept.closing_line!r} repeats a scene's text; sum "
                "the film up in new words"
            )
    return problems


def _bare_line(text: str) -> str:
    return " ".join(word.strip(".,!?:;\"'") for word in text.casefold().split())


def _concept_copy(concept: ConceptDraft) -> Iterator[str]:
    yield concept.hook
    yield concept.closing_line
    yield from concept.chips
    for scene in concept.scenes:
        yield scene.text
        yield scene.voice


def _text_voice_problems(draft: PlanDraft) -> list[str]:
    """The viewer reads and hears the same idea: the voice repeats a word of the text."""
    return [
        f'concept {variant_id(c)} scene {s}: the voice "{scene.voice}" does not say any word of '
        f'the on-screen text "{scene.text}"; let the voice repeat its key word'
        for c, concept in enumerate(draft.concepts)
        for s, scene in enumerate(concept.scenes[:-1], start=1)
        if scene.voice
        and content_stems(scene.text)
        and not content_stems(scene.text) & content_stems(scene.voice)
    ]


def _copy_problems(
    draft: PlanDraft, concepts: tuple[CreativeConcept, ...], brief: Brief, *, extras: bool
) -> list[str]:
    problems: list[str] = []
    for draft_concept, concept in zip(draft.concepts, concepts, strict=True):
        claims = [
            ClaimRef(claim.text, claim.source_field, claim.source_span)
            for claim in draft_concept.claims
        ]
        lines = [
            line
            for line in _copy_lines(draft_concept, concept)
            if extras or not line.location.startswith(_EXTRAS)
        ]
        problems.extend(
            f"concept {concept.variant_id} {problem}"
            for problem in copy_problems(lines, claims, brief)
        )
    return problems


# End-card copy a film can do without; end_voice carries the hint.
_EXTRAS = ("closing_line", "end_voice", "cta_hint", "chip ")


def without_unsourced_extras(draft: PlanDraft, brief: Brief) -> PlanDraft:
    """``draft`` with any closing line, hint or chip that the brief does not back removed."""

    def grounded(location: str, text: str) -> bool:
        return not text or not copy_problems([CopyLine(location, text)], [], brief)

    concepts = [
        concept.model_copy(
            update={
                "closing_line": concept.closing_line
                if grounded("closing_line", concept.closing_line)
                else "",
                "cta_hint": concept.cta_hint if grounded("cta_hint", concept.cta_hint) else "",
                "chips": tuple(chip for chip in concept.chips if grounded("chip", chip)),
            }
        )
        for concept in draft.concepts
    ]
    return draft.model_copy(update={"concepts": tuple(concepts)})


def _copy_lines(draft: ConceptDraft, concept: CreativeConcept) -> Iterator[CopyLine]:
    yield CopyLine("hook", concept.hook)
    for index, scene in enumerate(concept.scenes, start=1):
        yield CopyLine(f"scene {index} text", scene.text)
        if scene.voice:
            yield CopyLine(f"scene {index} voice", scene.voice)
    if concept.closing_line:
        yield CopyLine("closing_line", concept.closing_line)
    if concept.end_voice:
        yield CopyLine("end_voice", concept.end_voice)
    if concept.cta_hint:
        yield CopyLine("cta_hint", concept.cta_hint)
    for index, chip in enumerate(draft.chips, start=1):
        yield CopyLine(f"chip {index}", chip)
    if concept.cta_source_field not in {BriefField.BUYER_CTA, BriefField.GOAL_NOTE}:
        yield CopyLine("cta", concept.cta)
