"""What Gemini returns (``PlanDraft``) and how it becomes validated ``CreativeConcept`` s.

The model never chooses ids, hypotheses, timestamps or file paths: it picks screenshots by
index and gives scene lengths in whole seconds, and code maps those onto the contract. That
removes whole classes of invented or malformed output.
"""

from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from preflight.contracts import Brief, BriefField, CreativeConcept, Scene
from preflight.contracts.concept import MAX_HOOK_WORDS, MAX_SCENES, MIN_SCENES

from .archetypes import Archetype

VIDEO_SECONDS = 15
FIRST_VARIANT_ID = "A"


class _Draft(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


class SceneDraft(_Draft):
    """One scene: which screenshot (by index), how long, and its sourced on-screen text."""

    screenshot_index: Annotated[int, Field(ge=0, description="Index into the screenshot list")]
    duration_s: Annotated[int, Field(ge=1, le=VIDEO_SECONDS)]
    text: Annotated[str, Field(min_length=1, description="Built only from the cited field")]
    source_field: BriefField


class ConceptDraft(_Draft):
    """One concept, in the order of the archetypes the prompt listed."""

    hook: Annotated[str, Field(min_length=1, description=f"At most {MAX_HOOK_WORDS} words")]
    hook_source_field: BriefField
    scenes: Annotated[tuple[SceneDraft, ...], Field(min_length=MIN_SCENES, max_length=MAX_SCENES)]
    cta: Annotated[str, Field(min_length=1)]
    cta_source_field: BriefField

    @model_validator(mode="after")
    def _scenes_fill_the_video(self) -> Self:
        total = sum(scene.duration_s for scene in self.scenes)
        if total != VIDEO_SECONDS:
            raise ValueError(f"scene durations must add up to {VIDEO_SECONDS} seconds, got {total}")
        return self


class PlanDraft(_Draft):
    """The model's answer: one concept per requested archetype."""

    concepts: tuple[ConceptDraft, ...]


def variant_id(index: int) -> str:
    """``A``, ``B``, ``C``... for the ``index``-th concept."""
    return chr(ord(FIRST_VARIANT_ID) + index)


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
        _assemble(concept, brief, variant_id(index), archetype)
        for index, (concept, archetype) in enumerate(zip(draft.concepts, archetypes, strict=True))
    )


def _assemble(
    concept: ConceptDraft, brief: Brief, identifier: str, archetype: Archetype
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
            )
        )
        elapsed += scene.duration_s
    return CreativeConcept(
        variant_id=identifier,
        hypothesis=archetype.name,
        hook=concept.hook,
        hook_source_field=concept.hook_source_field,
        scenes=tuple(scenes),
        cta=concept.cta,
        cta_source_field=concept.cta_source_field,
    )
