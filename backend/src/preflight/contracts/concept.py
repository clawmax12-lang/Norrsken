"""FR-02: a creative concept (PRD §10.3 ``CreativeConcept``)."""

from typing import Annotated, Self

from pydantic import Field, model_validator

from ._base import VARIANT_ID_PATTERN, VIDEO_DURATION_S, Contract
from .brief import BriefField, NonEmpty

MAX_HOOK_WORDS = 8
MIN_SCENES = 4
MAX_SCENES = 6
MAX_CHIPS = 3
MAX_CHIP_WORDS = 4
_EPSILON = 1e-6

VariantId = Annotated[str, Field(pattern=VARIANT_ID_PATTERN)]
Unit = Annotated[float, Field(ge=0, le=1)]
FocusBox = tuple[Unit, Unit, Unit, Unit]
"""``(x, y, width, height)`` of a screenshot region, each 0-1 of the image size."""


class Claim(Contract):
    """One factual statement in the copy and the exact brief text that backs it (PRD §15)."""

    text: NonEmpty
    source_field: BriefField
    source_span: NonEmpty


class Scene(Contract):
    """One timed screen of a video. Every factual claim in ``text`` or ``voice`` is backed.

    ``voice`` is the narrator's line for this scene (it may differ from the on-screen text);
    ``focus`` is the region of the screenshot the camera punches into; ``emphasis`` is one
    word of ``text`` drawn in the brand colour. ``crop`` is the device display inside a mockup
    (a phone on a backdrop); when set, ``focus`` is relative to that crop.
    """

    t_start: Annotated[float, Field(ge=0)]
    t_end: Annotated[float, Field(gt=0)]
    screenshot: NonEmpty
    text: NonEmpty
    source_field: BriefField
    voice: str | None = None
    focus: FocusBox | None = None
    crop: FocusBox | None = None
    emphasis: str | None = None

    @model_validator(mode="after")
    def _forward_in_time(self) -> Self:
        if self.t_end <= self.t_start:
            raise ValueError("scene must end after it starts")
        return self

    @model_validator(mode="after")
    def _focus_inside_image(self) -> Self:
        for name, box in (("focus", self.focus), ("crop", self.crop)):
            if box is None:
                continue
            x, y, width, height = box
            if width <= 0 or height <= 0 or x + width > 1 + _EPSILON or y + height > 1 + _EPSILON:
                raise ValueError(f"{name} must be a non-empty box inside the screenshot")
        return self


class CreativeConcept(Contract):
    """A hypothesis about what makes viewers act, expressed as 4-6 contiguous scenes.

    ``closing_line`` is the end-card headline and ``end_voice`` the narrator's last line;
    ``chips`` are up to three short benefits stacked on the end card. ``claims`` lists every
    factual statement the copy makes with the brief text that backs it.
    """

    variant_id: VariantId
    hypothesis: NonEmpty
    hook: NonEmpty
    hook_source_field: BriefField
    scenes: Annotated[tuple[Scene, ...], Field(min_length=MIN_SCENES, max_length=MAX_SCENES)]
    cta: NonEmpty
    cta_source_field: BriefField
    duration_s: Annotated[int, Field(ge=VIDEO_DURATION_S, le=VIDEO_DURATION_S)] = VIDEO_DURATION_S
    angle: str | None = None
    closing_line: str | None = None
    end_voice: str | None = None
    chips: Annotated[tuple[NonEmpty, ...], Field(max_length=MAX_CHIPS)] = ()
    claims: tuple[Claim, ...] = ()
    language: str | None = None

    @model_validator(mode="after")
    def _hook_is_short(self) -> Self:
        if len(self.hook.split()) > MAX_HOOK_WORDS:
            raise ValueError(f"hook has more than {MAX_HOOK_WORDS} words")
        return self

    @model_validator(mode="after")
    def _chips_are_short(self) -> Self:
        if any(len(chip.split()) > MAX_CHIP_WORDS for chip in self.chips):
            raise ValueError(f"a chip has more than {MAX_CHIP_WORDS} words")
        return self

    @model_validator(mode="after")
    def _scenes_tile_the_video(self) -> Self:
        if abs(self.scenes[0].t_start) > _EPSILON:
            raise ValueError("first scene must start at 0")
        for previous, current in zip(self.scenes, self.scenes[1:], strict=False):
            if abs(previous.t_end - current.t_start) > _EPSILON:
                raise ValueError("scenes must be contiguous")
        if abs(self.scenes[-1].t_end - self.duration_s) > _EPSILON:
            raise ValueError("last scene must end at duration_s")
        return self

    def scene_at(self, t: float) -> Scene:
        """Return the scene on screen at second ``t`` (clamped to the video)."""
        clamped = min(max(t, 0.0), self.duration_s - _EPSILON)
        return next(s for s in self.scenes if s.t_start <= clamped < s.t_end)
