"""What Gemini returns (``PlanDraft``) and how it becomes validated ``CreativeConcept`` s.

The model never chooses ids, hypotheses, timestamps or file paths: it picks screenshots by
index and gives scene lengths in whole seconds, and code maps those onto the contract. That
removes whole classes of invented or malformed output.

Besides the concepts, the model reports what it saw in each screenshot (whether it shows the
customer's product or another brand) and whether the brief's own call to action addresses the
audience. Code, not the model, decides what to do with those observations.
"""

from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from preflight.contracts import Brief, BriefField, Claim, CreativeConcept, PlanNotes, Scene
from preflight.contracts.concept import (
    MAX_CHIP_WORDS,
    MAX_CHIPS,
    MAX_HOOK_WORDS,
    MAX_SCENES,
    MIN_SCENES,
)
from preflight.timing import BUTTON_MAX_WORDS, END_CARD_S

from .archetypes import Archetype

VIDEO_SECONDS = 15
FIRST_VARIANT_ID = "A"
END_CARD_SECONDS = int(END_CARD_S)


class _Draft(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


class SceneDraft(_Draft):
    """One scene: which screenshot (by index), how long, what is shown, said and zoomed into."""

    screenshot_index: Annotated[int, Field(ge=0, description="Index into the screenshot list")]
    duration_s: Annotated[int, Field(ge=1, le=VIDEO_SECONDS)]
    text: Annotated[str, Field(min_length=1, description="On-screen copy, at most 6 words")]
    source_field: BriefField
    voice: Annotated[str, Field(description="The narrator's line for this scene")] = ""
    emphasis: Annotated[str, Field(description="One word of text to colour, or empty")] = ""
    focus: Annotated[
        list[float] | None,
        Field(description="[x, y, width, height] 0-1 of the screenshot region to zoom into"),
    ] = None


class ClaimDraft(_Draft):
    """A factual statement made by the copy and the exact brief text that backs it."""

    text: Annotated[str, Field(min_length=1)]
    source_field: BriefField
    source_span: Annotated[str, Field(min_length=1, description="Verbatim text of that field")]


class ConceptDraft(_Draft):
    """One concept, in the order of the archetypes the prompt listed."""

    hook: Annotated[str, Field(min_length=1, description=f"At most {MAX_HOOK_WORDS} words")]
    hook_source_field: BriefField
    scenes: Annotated[tuple[SceneDraft, ...], Field(min_length=MIN_SCENES, max_length=MAX_SCENES)]
    cta: Annotated[str, Field(min_length=1)]
    cta_source_field: BriefField
    angle: str = ""
    closing_line: str = ""
    end_voice: str = ""
    chips: tuple[str, ...] = ()
    claims: tuple[ClaimDraft, ...] = ()

    @model_validator(mode="after")
    def _scenes_fill_the_video(self) -> Self:
        """Scale the scene lengths to exactly 15 s, keeping their proportions.

        Gemini often returns 12-14 s in total; asking it again costs a whole call for
        arithmetic that code does exactly.
        """
        durations = fit_durations([scene.duration_s for scene in self.scenes], VIDEO_SECONDS)
        if durations == [scene.duration_s for scene in self.scenes]:
            return self
        scenes = tuple(
            scene.model_copy(update={"duration_s": seconds})
            for scene, seconds in zip(self.scenes, durations, strict=True)
        )
        return self.model_copy(update={"scenes": scenes})


class ScreenshotNote(_Draft):
    """What the model saw in one screenshot."""

    index: Annotated[int, Field(ge=0)]
    shows_product: Annotated[
        bool, Field(description="True when it shows the brief's own product")
    ] = True
    other_brand: Annotated[
        str, Field(description="Name of another company/product it shows, or empty")
    ] = ""
    note: str = ""


def fit_durations(
    durations: list[int], total: int, *, last_locked: int | None = END_CARD_SECONDS
) -> list[int]:
    """Whole-second lengths summing to ``total``. The last scene is locked to the end card."""
    if last_locked is None or len(durations) < 2:
        return _fit_body(durations, total)
    last = min(last_locked, total - (len(durations) - 1))
    body = _fit_body(durations[:-1], total - last)
    return [*body, last]


def _fit_body(durations: list[int], total: int) -> list[int]:
    """Whole-second lengths summing to ``total``, proportional to ``durations``, each >= 1."""
    current = sum(durations)
    if current == total:
        return list(durations)
    if len(durations) > total:
        raise ValueError(f"{len(durations)} scenes cannot fit in {total} seconds")
    weights = [max(duration, 1) for duration in durations]
    shares = [total * weight / sum(weights) for weight in weights]
    fitted = [max(1, int(share)) for share in shares]
    while sum(fitted) > total:
        fitted[fitted.index(max(fitted))] -= 1
    by_remainder = sorted(
        range(len(shares)), key=lambda index: shares[index] - int(shares[index]), reverse=True
    )
    for index in by_remainder[: total - sum(fitted)]:
        fitted[index] += 1
    return fitted


class PlanDraft(_Draft):
    """The model's answer: observations, then one concept per requested archetype."""

    concepts: tuple[ConceptDraft, ...]
    language: Annotated[str, Field(description="ISO 639-1 code of the brief's language")] = ""
    screenshots: tuple[ScreenshotNote, ...] = ()
    cta_fits_audience: Annotated[
        bool,
        Field(description="True when goal_note is empty or addresses the brief's audience"),
    ] = True
    cta_note: str = ""


def variant_id(index: int) -> str:
    """``A``, ``B``, ``C``... for the ``index``-th concept."""
    return chr(ord(FIRST_VARIANT_ID) + index)


def excluded_screenshots(draft: PlanDraft, screenshot_count: int) -> tuple[int, ...]:
    """Indexes that show another brand or not the product, unless too few would remain."""
    excluded = tuple(
        sorted(
            {
                note.index
                for note in draft.screenshots
                if note.index < screenshot_count and (not note.shows_product or note.other_brand)
            }
        )
    )
    if screenshot_count - len(excluded) < 2:
        return ()
    return excluded


def plan_notes(draft: PlanDraft, brief: Brief) -> PlanNotes:
    """Customer-facing notes on screenshots left out and on a call to action that mismatches."""
    excluded = excluded_screenshots(draft, len(brief.screenshots))
    messages: list[str] = []
    by_index = {note.index: note for note in draft.screenshots}
    for index in excluded:
        note = by_index[index]
        shows = f"shows {note.other_brand}" if note.other_brand else "does not show the product"
        messages.append(
            f"Screenshot {index + 1} {shows}, not {brief.product_name}; it was left out of every "
            "video. Upload a screen of your own product to use it."
        )
    if not excluded and any(
        not note.shows_product or note.other_brand for note in draft.screenshots
    ):
        messages.append(
            "Some screenshots may not show your product, but too few would remain without them; "
            "replace them before launching."
        )
    goal_note = (brief.goal_note or "").strip()
    if goal_note and not brief.buyer_cta and not draft.cta_fits_audience:
        reason = f" ({draft.cta_note})" if draft.cta_note else ""
        messages.append(
            f'Your call to action "{goal_note}" speaks to someone other than your audience '
            f'"{brief.audience}"{reason}. The videos use a call to action for your audience '
            "instead; set buyer_cta in the brief to choose it yourself."
        )
    return PlanNotes(excluded_screenshots=excluded, messages=tuple(messages))


def assemble_concepts(
    draft: PlanDraft, brief: Brief, archetypes: tuple[Archetype, ...]
) -> tuple[CreativeConcept, ...]:
    """Turn ``draft`` into contract concepts, assigning ids and hypotheses by position.

    Raises:
        IndexError: a screenshot index is out of range (callers check with
            :func:`preflight.planning.validation.plan_problems` first).
        pydantic.ValidationError: a concept breaks the ``CreativeConcept`` contract.
    """
    return tuple(
        _assemble(concept, draft, brief, variant_id(index), archetype)
        for index, (concept, archetype) in enumerate(zip(draft.concepts, archetypes, strict=True))
    )


def _assemble(
    concept: ConceptDraft,
    draft: PlanDraft,
    brief: Brief,
    identifier: str,
    archetype: Archetype,
) -> CreativeConcept:
    scenes: list[Scene] = []
    elapsed = 0
    for scene in concept.scenes:
        scenes.append(
            Scene(
                t_start=elapsed,
                t_end=elapsed + scene.duration_s,
                screenshot=brief.screenshots[scene.screenshot_index],
                text=scene.text,
                source_field=scene.source_field,
                voice=scene.voice or None,
                focus=_focus(scene.focus),
                emphasis=_emphasis(scene.emphasis, scene.text),
            )
        )
        elapsed += scene.duration_s
    cta, cta_source_field = cta_for(concept, draft, brief)
    return CreativeConcept(
        variant_id=identifier,
        hypothesis=archetype.name,
        hook=concept.hook,
        hook_source_field=concept.hook_source_field,
        scenes=tuple(scenes),
        cta=cta,
        cta_source_field=cta_source_field,
        angle=concept.angle or None,
        closing_line=concept.closing_line or None,
        end_voice=concept.end_voice or None,
        chips=tuple(chip for chip in concept.chips if chip and len(chip.split()) <= MAX_CHIP_WORDS)[
            :MAX_CHIPS
        ],
        claims=tuple(
            Claim(text=c.text, source_field=c.source_field, source_span=c.source_span)
            for c in concept.claims
        ),
        language=draft.language or None,
    )


def cta_for(concept: ConceptDraft, draft: PlanDraft, brief: Brief) -> tuple[str, BriefField]:
    """The button: the buyer CTA, else a fitting goal note, else the model's buyer action."""
    if brief.buyer_cta and brief.buyer_cta.strip():
        return brief.buyer_cta.strip(), BriefField.BUYER_CTA
    note = (brief.goal_note or "").strip()
    if note and draft.cta_fits_audience and len(note.split()) <= BUTTON_MAX_WORDS:
        return note, BriefField.GOAL_NOTE
    if note and draft.cta_fits_audience and concept.cta_source_field is BriefField.GOAL_NOTE:
        return concept.cta, BriefField.GOAL_NOTE
    return concept.cta, concept.cta_source_field


def _focus(box: list[float] | None) -> tuple[float, float, float, float] | None:
    """A usable zoom box, clamped into the image; ``None`` when absent or degenerate."""
    if box is None or len(box) != 4:
        return None
    x, y, width, height = (min(max(value, 0.0), 1.0) for value in box)
    width, height = min(width, 1.0 - x), min(height, 1.0 - y)
    if width < 0.08 or height < 0.05:
        return None
    return (x, y, width, height)


def _emphasis(word: str, text: str) -> str | None:
    """Keep ``word`` only when it is one word of ``text`` (so the renderer can find it)."""
    bare = word.strip(" .,!?:;").casefold()
    if not bare or " " in bare:
        return None
    words = [w.strip(" .,!?:;").casefold() for w in text.split()]
    return word.strip(" .,!?:;") if bare in words else None
