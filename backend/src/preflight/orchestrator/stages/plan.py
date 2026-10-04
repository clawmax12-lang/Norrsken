"""PLANNED: ask the planner for the concepts and persist them (FR-02).

When a narrator is wired, each concept's scene lengths are then fitted to its spoken voice
lines (PRD §9.3, voice-led timing). Planner notes (a screenshot that shows another brand, a
call to action aimed at the wrong person) are logged and saved for the report.
"""

from collections.abc import Sequence
from functools import partial

from preflight.contracts import CreativeConcept, PlanNotes, RunState, Step, VariantRecord
from preflight.errors import PreflightError, PreflightValidationError
from preflight.orchestrator.context import RunContext
from preflight.orchestrator.retry import StepPolicy
from preflight.ports import Planner, SpeechSynthesizer
from preflight.sound.voice_timing import time_to_voice


class PlanStage:
    """Persists exactly ``count`` distinct concepts under ``concepts/`` and lists the variants."""

    step = Step.PLAN
    completes = RunState.PLANNED
    title = "Planning concepts"

    def __init__(
        self,
        planner: Planner,
        policy: StepPolicy,
        count: int,
        *,
        voice: SpeechSynthesizer | None = None,
    ) -> None:
        """Plan ``count`` concepts under ``policy``; ``voice`` times scenes to the narration."""
        self._planner = planner
        self._policy = policy
        self._count = count
        self._voice = voice

    async def run(self, ctx: RunContext) -> str:
        """Plan, validate the count, write one file per concept and register the variants."""
        planned = partial(self._planner.plan_variants, ctx.brief, count=self._count)
        concepts = _require_distinct(await self._policy.run(planned), self._count)
        self._save_notes(ctx)
        timed = [await self._time(ctx, concept) for concept in concepts]
        for concept in timed:
            ctx.store.write(ctx.paths.concept(concept.variant_id), concept)
        ctx.tracker.set_variants(tuple(VariantRecord(variant_id=c.variant_id) for c in timed))
        return f"Planned {len(timed)} concepts"

    def _save_notes(self, ctx: RunContext) -> None:
        notes = getattr(self._planner, "last_notes", None)
        if not isinstance(notes, PlanNotes):
            return
        ctx.store.write(ctx.paths.plan_notes, notes)
        for message in notes.messages:
            ctx.log.skipped(Step.PLAN, message)

    async def _time(self, ctx: RunContext, concept: CreativeConcept) -> CreativeConcept:
        if self._voice is None:
            return concept
        try:
            return await time_to_voice(concept, self._voice)
        except PreflightError as exc:
            ctx.log.skipped(
                Step.PLAN,
                f"Voice timing unavailable for variant {concept.variant_id} ({exc}); "
                "keeping the planned scene lengths",
                variant_id=concept.variant_id,
            )
            return concept


def _require_distinct(concepts: Sequence[CreativeConcept], count: int) -> Sequence[CreativeConcept]:
    ids = {concept.variant_id for concept in concepts}
    if len(concepts) != count or len(ids) != count:
        raise PreflightValidationError(
            f"planner must return {count} concepts with distinct variant ids, got {len(concepts)}"
        )
    return concepts
