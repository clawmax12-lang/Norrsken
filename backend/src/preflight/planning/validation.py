"""Plan-level checks that need the brief: everything the schema alone cannot express (FR-02)."""

from collections.abc import Iterator
from itertools import pairwise

from pydantic import ValidationError

from preflight.contracts import Brief, BriefField, CreativeConcept

from .archetypes import Archetype
from .claims import ClaimRef, CopyLine, copy_problems
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
MAX_END_VOICE_WORDS = 8
MAX_SCENE_TEXT_WORDS = 8
VOICE_WORDS_PER_S = 3.2


def plan_problems(draft: PlanDraft, brief: Brief, archetypes: tuple[Archetype, ...]) -> list[str]:
    """Every reason ``draft`` is unusable, phrased for the model; empty means acceptable."""
    if len(draft.concepts) != len(archetypes):
        return [f"return exactly {len(archetypes)} concepts, not {len(draft.concepts)}"]
    index_problems = _screenshot_index_problems(draft, len(brief.screenshots))
    if index_problems:
        return index_problems
    sequence_problems = [
        *_screenshot_sequence_problems(draft, len(brief.screenshots)),
        *_excluded_screenshot_problems(draft, brief),
    ]
    if sequence_problems:
        return sequence_problems
    try:
        concepts = assemble_concepts(draft, brief, archetypes)
    except ValidationError as exc:
        return [f"concept does not satisfy the contract: {error['msg']}" for error in exc.errors()]
    return [
        *_set_problems(concepts),
        *_voice_problems(draft),
        *_copy_problems(draft, concepts, brief),
    ]


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
    so the picture still changes.
    """
    if screenshot_count < 2:
        return []
    problems: list[str] = []
    sequences: list[tuple[int, ...]] = []
    for concept_index, concept in enumerate(draft.concepts):
        indexes = [scene.screenshot_index for scene in concept.scenes]
        sequences.append(tuple(indexes))
        for scene_index, (left, right) in enumerate(pairwise(concept.scenes), start=1):
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
            f"{label} scene {s}: the voice line has {len(scene.voice.split())} words for a "
            f"{scene.duration_s} s scene; shorten it or lengthen the scene"
            for s, scene in enumerate(body, start=1)
            if len(scene.voice.split()) > scene.duration_s * VOICE_WORDS_PER_S + 1
        )
        if not concept.end_voice:
            problems.append(f"{label}: end_voice is empty; give the narrator a closing line")
        elif len(concept.end_voice.split()) > MAX_END_VOICE_WORDS:
            problems.append(
                f"{label}: end_voice has more than {MAX_END_VOICE_WORDS} words; it must fit the "
                "3 s end card"
            )
        problems.extend(
            f'{label} scene {s}: on-screen text "{scene.text}" has more than '
            f"{MAX_SCENE_TEXT_WORDS} words; keep it short and let the voice explain"
            for s, scene in enumerate(body, start=1)
            if len(scene.text.split()) > MAX_SCENE_TEXT_WORDS
        )
    return problems


def _copy_problems(
    draft: PlanDraft, concepts: tuple[CreativeConcept, ...], brief: Brief
) -> list[str]:
    problems: list[str] = []
    for draft_concept, concept in zip(draft.concepts, concepts, strict=True):
        claims = [
            ClaimRef(claim.text, claim.source_field, claim.source_span)
            for claim in draft_concept.claims
        ]
        problems.extend(
            f"concept {concept.variant_id} {problem}"
            for problem in copy_problems(_copy_lines(draft_concept, concept), claims, brief)
        )
    return problems


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
    for index, chip in enumerate(draft.chips, start=1):
        yield CopyLine(f"chip {index}", chip)
    if concept.cta_source_field not in {BriefField.BUYER_CTA, BriefField.GOAL_NOTE}:
        yield CopyLine("cta", concept.cta)
