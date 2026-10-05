"""PLANNED: ask the planner for the concepts and persist them (FR-02).

When a narrator is wired, each concept's scene lengths are then fitted to its spoken voice
lines and every word's start is measured (PRD §9.3, voice-led timing); a narrator failure
pauses the run. Planner notes (a screenshot that shows another brand, a
call to action aimed at the wrong person) are logged and saved for the report.
"""

from collections.abc import Sequence
from functools import partial

from preflight.contracts import CreativeConcept, PlanNotes, RunState, Step, VariantRecord
from preflight.errors import NarrationError, PreflightError, PreflightValidationError
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
        """Plan, validate the count, write one file per concept and register the variants.

        Concepts are saved before they are timed to the voice, so a run that paused on the
        narrator resumes with the same concepts instead of planning new ones.
        """
        concepts: Sequence[CreativeConcept] | None = self._saved(ctx)
        if concepts is None:
            planned = partial(self._planner.plan_variants, ctx.brief, count=self._count)
            concepts = _require_distinct(await self._policy.run(planned), self._count)
            self._save_notes(ctx)
            for concept in concepts:
                ctx.store.write(ctx.paths.concept(concept.variant_id), concept)
        timed = [await self._time(concept) for concept in concepts]
        for concept in timed:
            ctx.store.write(ctx.paths.concept(concept.variant_id), concept)
        ctx.tracker.set_variants(tuple(VariantRecord(variant_id=c.variant_id) for c in timed))
        return f"Planned {len(timed)} concepts"

    def _saved(self, ctx: RunContext) -> list[CreativeConcept] | None:
        """The concepts an earlier attempt of this run already planned, if it planned them all."""
        folder = ctx.paths.concept("A").parent
        files = sorted(folder.glob("*.json")) if folder.is_dir() else []
        if len(files) != self._count:
            return None
        return [ctx.store.read(path, CreativeConcept) for path in files]

    def _save_notes(self, ctx: RunContext) -> None:
        notes = getattr(self._planner, "last_notes", None)
        if not isinstance(notes, PlanNotes):
            return
        ctx.store.write(ctx.paths.plan_notes, notes)
        for message in notes.messages:
            ctx.log.skipped(Step.PLAN, message)

    async def _time(self, concept: CreativeConcept) -> CreativeConcept:
        """Fit the scenes to the spoken lines.

        Raises:
            NarrationError: the narrator could not speak a line; the run pauses here.
        """
        if self._voice is None:
            return concept
        try:
            return await time_to_voice(concept, self._voice)
        except PreflightError as exc:
            raise NarrationError(
                f"Narration failed for variant {concept.variant_id} ({exc}). The run paused "
                "after planning; run it again to resume with the same concepts"
            ) from exc


def _require_distinct(concepts: Sequence[CreativeConcept], count: int) -> Sequence[CreativeConcept]:
    ids = {concept.variant_id for concept in concepts}
    if len(concepts) != count or len(ids) != count:
        raise PreflightValidationError(
            f"planner must return {count} concepts with distinct variant ids, got {len(concepts)}"
        )
    return concepts
