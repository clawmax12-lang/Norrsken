"""EXPLAINED: timestamped reasons per variant and the final ``report.json`` (FR-06, FR-10)."""

from collections.abc import Callable, Sequence
from functools import partial

from preflight.contracts import (
    Ranking,
    Reason,
    Report,
    RunState,
    SimulationResult,
    SimulatorName,
    Step,
)
from preflight.orchestrator.concurrency import gather_bounded
from preflight.orchestrator.context import RunContext
from preflight.orchestrator.retry import StepPolicy
from preflight.ports import Explainer, UsageMeter

EXPLAIN_CONCURRENCY = 2
NextTimeSuggester = Callable[..., tuple[str, ...]]


class ExplainStage:
    """Explains every ranked variant, then writes the report the founder downloads."""

    step = Step.EXPLAIN
    completes = RunState.EXPLAINED
    title = "Explaining results"

    def __init__(
        self,
        explainer: Explainer,
        usage: UsageMeter,
        policy: StepPolicy,
        next_time: NextTimeSuggester,
    ) -> None:
        """Explain with ``explainer`` under ``policy``; ``usage`` is read once, at the end."""
        self._explainer = explainer
        self._usage = usage
        self._policy = policy
        self._next_time = next_time

    async def run(self, ctx: RunContext) -> str:
        """Gather reasons for each ranked variant and persist ``report.json``."""
        ranking = ctx.store.read(ctx.paths.ranking, Ranking)
        results = ctx.archive.scoring_results(ctx.rendered_variants())
        jobs = [partial(self._explain_one, ctx, ranking, results, v) for v in ranking.order]
        reasons = dict(await gather_bounded(EXPLAIN_CONCURRENCY, jobs))
        ctx.store.write(ctx.paths.report, self._report(ctx, ranking, results, reasons))
        return f"Explained {len(reasons)} variants"

    async def _explain_one(
        self,
        ctx: RunContext,
        ranking: Ranking,
        results: Sequence[SimulationResult],
        variant_id: str,
    ) -> tuple[str, tuple[Reason, ...]]:
        own_results = [r for r in results if r.variant_id == variant_id]
        explain = partial(
            self._explainer.explain, ctx.brief, ctx.read_concept(variant_id), ranking, own_results
        )
        with ctx.log.step(
            Step.EXPLAIN, f"Explaining variant {variant_id}", variant_id=variant_id
        ) as handle:
            reasons = await self._policy.run(explain)
            handle.report(f"Explained variant {variant_id} with {len(reasons)} reasons")
        return variant_id, reasons

    def _report(
        self,
        ctx: RunContext,
        ranking: Ranking,
        results: Sequence[SimulationResult],
        reasons: dict[str, tuple[Reason, ...]],
    ) -> Report:
        winner, *others = ranking.order
        return Report(
            winner=winner,
            runner_up=others[0] if others else None,
            reasons=reasons,
            next_time=self._next_time(ctx.read_concept(winner), ranking, results),
            token_savings=self._usage.snapshot(),
            brain_sim=any(r.simulator is SimulatorName.TRIBE_V2 for r in results),
        )
