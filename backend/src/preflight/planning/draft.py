"""What Gemini returns (``PlanDraft``) and how it becomes validated ``CreativeConcept`` s.

The model never chooses ids, hypotheses, timestamps or file paths: it picks screenshots by
index and gives scene lengths in whole seconds, and code maps those onto the contract. That
removes whole classes of invented or malformed output.

Besides the concepts, the model reports what it saw in each screenshot (whether it shows the
customer's product or another brand) and whether the brief's own call to action addresses the
audience. Code, not the model, decides what to do with those observations.
"""

from collections.abc import Mapping, Sequence
from functools import partial
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from preflight.advice import advice
from preflight.contracts import (
    Brief,
    BriefField,
    Claim,
    CreativeConcept,
    PlanNotes,
    Scene,
    Shot,
)
from preflight.contracts.concept import (
    MAX_CHIP_WORDS,
    MAX_CHIPS,
    MAX_HOOK_WORDS,
    MAX_SCENES,
    MIN_SCENES,
)
from preflight.timing import BUTTON_MAX_WORDS, END_CARD_S

from .archetypes import Archetype
from .claims import brief_mentions, brief_names
from .screens import ScreenImage, crop_focus

VIDEO_SECONDS = 15
FIRST_VARIANT_ID = "A"
# Below this many source pixels across the shown product, the film cannot look sharp.
MIN_SHARP_PRODUCT_PX = 450
END_CARD_SECONDS = int(END_CARD_S)
MAX_END_VOICE_WORDS = 8
MAX_SCREENSHOT_ISSUES = 2
# The hook has this long to stop the scroll before the story moves on.
HOOK_MAX_SECONDS = 2
MAX_CTA_HINT_WORDS = 5


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
    cta_hint: Annotated[
        str, Field(description="2 to 5 words under the button that make acting feel easy")
    ] = ""
    chips: tuple[str, ...] = ()
    claims: tuple[ClaimDraft, ...] = ()

    @model_validator(mode="after")
    def _scenes_fill_the_video(self) -> Self:
        """Scale the scene lengths to exactly 15 s, keeping their proportions.

        Gemini often returns 12-14 s in total; asking it again costs a whole call for
        arithmetic that code does exactly. The hook is held to ``HOOK_MAX_SECONDS``.
        """
        durations = fit_durations([scene.duration_s for scene in self.scenes], VIDEO_SECONDS)
        durations = cap_hook(durations)
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
    device_box: Annotated[
        list[int],
        Field(
            description="[ymin, xmin, ymax, xmax] 0-1000 tightly around the whole device when "
            "the image shows a phone/tablet/laptop on a backdrop (a mockup); empty for a plain "
            "screenshot"
        ),
    ] = []
    note: str = ""
    confirmation: Annotated[
        bool,
        Field(description="True for a screen confirming a finished action (thank-you, paid)"),
    ] = False
    issues: Annotated[
        list[str],
        Field(
            description="At most 2 problems a viewer would notice: numbers or claims not in the "
            "brief, text in another language, a style unlike the other screenshots"
        ),
    ] = []


def fit_durations(
    durations: list[int], total: int, *, last_locked: int | None = END_CARD_SECONDS
) -> list[int]:
    """Whole-second lengths summing to ``total``. The last scene is locked to the end card."""
    if last_locked is None or len(durations) < 2:
        return _fit_body(durations, total)
    last = min(last_locked, total - (len(durations) - 1))
    body = _fit_body(durations[:-1], total - last)
    return [*body, last]


def cap_hook(durations: list[int]) -> list[int]:
    """``durations`` with the hook at most ``HOOK_MAX_SECONDS``; the middle scenes absorb it."""
    if len(durations) < 3 or durations[0] <= HOOK_MAX_SECONDS:
        return durations
    middle = durations[1:-1]
    return [
        HOOK_MAX_SECONDS,
        *_fit_body(middle, sum(durations[:-1]) - HOOK_MAX_SECONDS),
        durations[-1],
    ]


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
        Field(
            description="True when the brief's call to action (buyer_cta, else goal_note) is "
            "empty or addresses the brief's audience"
        ),
    ] = True
    cta_note: str = ""
    audience_cta: Annotated[
        str,
        Field(
            description="A 2 to 4 word action for the audience, with no claim in it; used when "
            "the brief's call to action does not fit the audience"
        ),
    ] = ""


def variant_id(index: int) -> str:
    """``A``, ``B``, ``C``... for the ``index``-th concept."""
    return chr(ord(FIRST_VARIANT_ID) + index)


def excluded_screenshots(draft: PlanDraft, brief: Brief) -> tuple[int, ...]:
    """Indexes that show another brand or not the product, unless too few would remain.

    A brand the brief itself names (a payment partner, an integration) is not another brand.
    """
    screenshot_count = len(brief.screenshots)
    excluded = tuple(
        sorted(
            {
                note.index
                for note in draft.screenshots
                if note.index < screenshot_count and _off_brand(note, brief)
            }
        )
    )
    if screenshot_count - len(excluded) < 2:
        return ()
    return excluded


def _off_brand(note: ScreenshotNote, brief: Brief) -> bool:
    other = bool(note.other_brand) and not brief_mentions(brief, note.other_brand)
    return not note.shows_product or other


def plan_notes(
    draft: PlanDraft, brief: Brief, screens: Mapping[int, ScreenImage] | None = None
) -> PlanNotes:
    """Customer-facing notes: screenshots left out or too small, and a mismatched CTA."""
    excluded = excluded_screenshots(draft, brief)
    say = partial(advice, language=draft.language)
    messages: list[str] = []
    for index, screen in sorted((screens or {}).items()):
        if index not in excluded and screen.product_width_px < MIN_SHARP_PRODUCT_PX:
            where = say("soft_where_crop" if screen.crop else "soft_where_plain")
            messages.append(
                say("soft_screen", n=index + 1, where=where, px=screen.product_width_px)
            )
    by_index = {note.index: note for note in draft.screenshots}
    for note in sorted(draft.screenshots, key=lambda n: n.index):
        if note.index not in excluded and note.index < len(brief.screenshots):
            messages.extend(
                say("screenshot_issue", n=note.index + 1, issue=issue.strip().rstrip("."))
                for issue in note.issues[:MAX_SCREENSHOT_ISSUES]
                if issue.strip()
            )
    for index in excluded:
        note = by_index[index]
        shows = (
            say("excluded_shows_brand", brand=note.other_brand)
            if note.other_brand
            else say("excluded_shows_none")
        )
        messages.append(say("excluded", n=index + 1, shows=shows, product=brief.product_name))
    if not excluded and any(_off_brand(note, brief) for note in draft.screenshots):
        messages.append(say("off_brand_kept"))
    buyer_cta = (brief.buyer_cta or "").strip()
    given = buyer_cta or (brief.goal_note or "").strip()
    if given and not draft.cta_fits_audience:
        reason = f" ({draft.cta_note})" if draft.cta_note else ""
        fix = say("cta_fix_buyer" if buyer_cta else "cta_fix_none")
        messages.append(
            say("cta_mismatch", given=given, audience=brief.audience, reason=reason, fix=fix)
        )
    widths = [s.product_width_px for i, s in (screens or {}).items() if i not in excluded]
    return PlanNotes(
        excluded_screenshots=excluded,
        messages=tuple(messages),
        smallest_screen_px=min(widths) if widths else None,
    )


def assemble_concepts(
    draft: PlanDraft,
    brief: Brief,
    archetypes: tuple[Archetype, ...],
    screens: Mapping[int, ScreenImage] | None = None,
) -> tuple[CreativeConcept, ...]:
    """Turn ``draft`` into contract concepts, assigning ids and hypotheses by position.

    Raises:
        IndexError: a screenshot index is out of range (callers check with
            :func:`preflight.planning.validation.plan_problems` first).
        pydantic.ValidationError: a concept breaks the ``CreativeConcept`` contract.
    """
    return tuple(
        _assemble(concept, draft, brief, index, archetype, screens or {})
        for index, (concept, archetype) in enumerate(zip(draft.concepts, archetypes, strict=True))
    )


def _assemble(
    concept: ConceptDraft,
    draft: PlanDraft,
    brief: Brief,
    position: int,
    archetype: Archetype,
    screens: Mapping[int, ScreenImage],
) -> CreativeConcept:
    scenes: list[Scene] = []
    elapsed = 0
    shots = shots_for(position, [screens.get(s.screenshot_index) for s in concept.scenes])
    for scene, shot in zip(concept.scenes, shots, strict=True):
        screen = screens.get(scene.screenshot_index)
        crop = screen.crop if screen else None
        scenes.append(
            Scene(
                t_start=elapsed,
                t_end=elapsed + scene.duration_s,
                screenshot=brief.screenshots[scene.screenshot_index],
                text=scene.text,
                source_field=scene.source_field,
                voice=scene.voice or None,
                focus=crop_focus(_focus(scene.focus), crop),
                crop=crop,
                emphasis=_emphasis(scene.emphasis, scene.text),
                shot=shot,
            )
        )
        elapsed += scene.duration_s
    cta, cta_source_field = cta_for(concept, draft, brief)
    return CreativeConcept(
        variant_id=variant_id(position),
        hypothesis=archetype.name,
        hook=concept.hook,
        hook_source_field=concept.hook_source_field,
        scenes=tuple(scenes),
        cta=cta,
        cta_source_field=cta_source_field,
        angle=concept.angle or None,
        closing_line=concept.closing_line or None,
        end_voice=end_voice_for(brief.product_name, cta, _hint(concept.cta_hint)),
        cta_hint=_hint(concept.cta_hint),
        chips=_chips(concept.chips, brief),
        claims=tuple(
            Claim(text=c.text, source_field=c.source_field, source_span=c.source_span)
            for c in concept.claims
        ),
        language=draft.language or None,
    )


# Each variant frames its scenes in its own order, so the three films look different.
SHOT_PATTERNS = (
    (Shot.HERO, Shot.CLOSE_UP, Shot.TAKEOVER, Shot.TILT),
    (Shot.TAKEOVER, Shot.HERO, Shot.TILT, Shot.CLOSE_UP),
    (Shot.TILT, Shot.CLOSE_UP, Shot.HERO, Shot.TAKEOVER),
)
# Below these widths the shot would enlarge source pixels past the renderer's 2x cap.
TAKEOVER_MIN_PX = 540
CLOSE_UP_MIN_PX = 600
PHONE_MAX_ASPECT = 0.62


def shots_for(position: int, screens: Sequence[ScreenImage | None]) -> list[Shot]:
    """The variant's shot pattern, with shots a screen is too small or too wide for replaced."""
    pattern = SHOT_PATTERNS[position % len(SHOT_PATTERNS)]
    shots: list[Shot] = []
    for index, screen in enumerate(screens):
        wanted = pattern[index % len(pattern)]
        if not _fits(wanted, screen):
            previous = shots[-1] if shots else None
            wanted = next(s for s in (Shot.TILT, Shot.HERO) if s is not previous)
        shots.append(wanted)
    return shots


def _fits(shot: Shot, screen: ScreenImage | None) -> bool:
    if shot in {Shot.HERO, Shot.TILT}:
        return True
    if screen is None or screen.aspect > PHONE_MAX_ASPECT:
        return False
    needed = TAKEOVER_MIN_PX if shot is Shot.TAKEOVER else CLOSE_UP_MIN_PX
    return screen.product_width_px >= needed


def end_voice_for(product_name: str, cta: str, hint: str | None = None) -> str:
    """The narrator says the button, so the last thing heard is the action shown.

    With a hint the line is a call to act now ("Skapa konto. Igång på 5 minuter."), else the
    product name and the button.
    """
    action = cta.strip().rstrip(".!")
    if hint:
        urged = f"{action}. {hint.strip().rstrip('.!')}."
        if len(urged.split()) <= MAX_END_VOICE_WORDS:
            return urged
    named = f"{product_name.strip().rstrip('.')}. {action}."
    return named if len(named.split()) <= MAX_END_VOICE_WORDS else f"{action}."


def _hint(text: str) -> str | None:
    """The button's hint, or ``None`` when empty or too long to read under a button."""
    hint = text.strip().rstrip(".")
    return hint if hint and len(hint.split()) <= MAX_CTA_HINT_WORDS else None


def _chips(chips: Sequence[str], brief: Brief) -> tuple[str, ...]:
    """Short benefits only; a chip that is just a name ("Stripe", "Apple Pay") says nothing."""
    names = brief_names(brief)
    kept = (
        chip
        for chip in chips
        if chip
        and len(chip.split()) <= MAX_CHIP_WORDS
        and not all(word.strip(".,!?:;").casefold() in names for word in chip.split())
    )
    return tuple(kept)[:MAX_CHIPS]


def cta_for(concept: ConceptDraft, draft: PlanDraft, brief: Brief) -> tuple[str, BriefField]:
    """The button: the buyer CTA, else a fitting goal note, else the model's buyer action."""
    given = (brief.buyer_cta or "").strip() or (brief.goal_note or "").strip()
    if given and not draft.cta_fits_audience and draft.audience_cta.strip():
        return draft.audience_cta.strip(), BriefField.PRODUCT_NAME
    if brief.buyer_cta and brief.buyer_cta.strip():
        if draft.cta_fits_audience:
            return brief.buyer_cta.strip(), BriefField.BUYER_CTA
        return concept.cta, concept.cta_source_field
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
