"""PLANNED: ask the planner for the concepts and persist them (FR-02)."""

from collections.abc import Sequence
from functools import partial

from preflight.contracts import CreativeConcept, RunState, Step, VariantRecord
from preflight.errors import PreflightValidationError
from preflight.orchestrator.context import RunContext
from preflight.orchestrator.retry import StepPolicy
from preflight.ports import Planner


class PlanStage:
    """Persists exactly ``count`` distinct concepts under ``concepts/`` and lists the variants."""

    step = Step.PLAN
    completes = RunState.PLANNED
    title = "Planning concepts"

    def __init__(self, planner: Planner, policy: StepPolicy, count: int) -> None:
        """Plan ``count`` concepts, calling the planner under ``policy``."""
        self._planner = planner
        self._policy = policy
        self._count = count

    async def run(self, ctx: RunContext) -> str:
        """Plan, validate the count, write one file per concept and register the variants."""
        planned = partial(self._planner.plan_variants, ctx.brief, count=self._count)
        concepts = _require_distinct(await self._policy.run(planned), self._count)
        for concept in concepts:
            ctx.store.write(ctx.paths.concept(concept.variant_id), concept)
        ctx.tracker.set_variants(tuple(VariantRecord(variant_id=c.variant_id) for c in concepts))
        return f"Planned {len(concepts)} concepts"


def _require_distinct(concepts: Sequence[CreativeConcept], count: int) -> Sequence[CreativeConcept]:
    ids = {concept.variant_id for concept in concepts}
    if len(concepts) != count or len(ids) != count:
        raise PreflightValidationError(
            f"planner must return {count} concepts with distinct variant ids, got {len(concepts)}"
        )
    return concepts
