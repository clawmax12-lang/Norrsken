"""FR-02: a creative concept (PRD §10.3 ``CreativeConcept``)."""

from typing import Annotated, Self

from pydantic import Field, model_validator

from ._base import VARIANT_ID_PATTERN, VIDEO_DURATION_S, Contract
from .brief import BriefField, NonEmpty

MAX_HOOK_WORDS = 8
MIN_SCENES = 4
MAX_SCENES = 6
_EPSILON = 1e-6

VariantId = Annotated[str, Field(pattern=VARIANT_ID_PATTERN)]


class Scene(Contract):
    """One timed screen of a video. ``text`` must be traceable to ``source_field``."""

    t_start: Annotated[float, Field(ge=0)]
    t_end: Annotated[float, Field(gt=0)]
    screenshot: NonEmpty
    text: NonEmpty
    source_field: BriefField

    @model_validator(mode="after")
    def _forward_in_time(self) -> Self:
        if self.t_end <= self.t_start:
            raise ValueError("scene must end after it starts")
        return self


class CreativeConcept(Contract):
    """A hypothesis about what makes viewers act, expressed as 4-6 contiguous scenes."""

    variant_id: VariantId
    hypothesis: NonEmpty
    hook: NonEmpty
    hook_source_field: BriefField
    scenes: Annotated[tuple[Scene, ...], Field(min_length=MIN_SCENES, max_length=MAX_SCENES)]
    cta: NonEmpty
    cta_source_field: BriefField
    duration_s: Annotated[int, Field(ge=VIDEO_DURATION_S, le=VIDEO_DURATION_S)] = VIDEO_DURATION_S

    @model_validator(mode="after")
    def _hook_is_short(self) -> Self:
        if len(self.hook.split()) > MAX_HOOK_WORDS:
            raise ValueError(f"hook has more than {MAX_HOOK_WORDS} words")
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
