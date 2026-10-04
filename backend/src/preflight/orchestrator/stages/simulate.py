"""SIMULATED: run every simulator on every rendered variant (FR-04)."""

import logging
from collections.abc import Sequence
from functools import partial

from preflight.contracts import RunState, SimulationResult, Step, VariantRecord
from preflight.errors import PreflightValidationError, ProviderError
from preflight.orchestrator.concurrency import gather_bounded
from preflight.orchestrator.context import RunContext
from preflight.orchestrator.retry import StepPolicy
from preflight.ports import SimulationRequest, Simulator

SIMULATION_CONCURRENCY = 2
_LOG = logging.getLogger(__name__)


class SimulateStage:
    """Persists one result per variant per simulator; an unavailable simulator is dropped."""

    step = Step.SIMULATE
    completes = RunState.SIMULATED
    title = "Simulating viewers"

    def __init__(self, simulators: Sequence[Simulator], policy: StepPolicy) -> None:
        """Run ``simulators`` under ``policy``."""
        self._simulators = tuple(simulators)
        self._policy = policy

    async def run(self, ctx: RunContext) -> str:
        """Simulate, then require at least one simulator that covers every rendered variant."""
        variants = ctx.rendered_variants()
        jobs = [
            partial(self._simulate_one, ctx, variant, simulator)
            for variant in variants
            for simulator in self._simulators
        ]
        await gather_bounded(SIMULATION_CONCURRENCY, jobs)
        scored = {r.simulator for r in ctx.archive.scoring_results(variants)}
        for simulator in self._simulators:
            if simulator.name not in scored:
                ctx.log.skipped(
                    Step.SIMULATE,
                    f"{simulator.name} left out: no result for every rendered variant",
                )
        if not scored:
            raise ProviderError("no simulator produced results for every rendered variant")
        names = ", ".join(sorted(scored))
        return f"Simulated {len(variants)} variants with {names}"

    async def _simulate_one(
        self, ctx: RunContext, variant: VariantRecord, simulator: Simulator
    ) -> None:
        variant_id, name = variant.variant_id, simulator.name
        if ctx.archive.load(variant, name) is not None:
            ctx.log.skipped(
                Step.SIMULATE,
                f"{name} already simulated variant {variant_id}",
                variant_id=variant_id,
            )
            return
        try:
            with ctx.log.step(
                Step.SIMULATE, f"Simulating variant {variant_id} with {name}", variant_id=variant_id
            ) as handle:
                result = await self._policy.run(partial(simulator.simulate, _request(ctx, variant)))
                _require_matches(result, variant, simulator)
                ctx.archive.save(result)
                handle.report(f"Simulated variant {variant_id} with {name}")
        except ProviderError as exc:
            _LOG.warning("%s unavailable for variant %s: %s", name, variant_id, exc)


def _request(ctx: RunContext, variant: VariantRecord) -> SimulationRequest:
    variant_id = variant.variant_id
    artifacts = ctx.paths.brain_dir(variant_id)
    artifacts.mkdir(parents=True, exist_ok=True)
    if variant.video_sha256 is None:
        raise PreflightValidationError(f"rendered variant {variant_id} has no video hash")
    video_path = (
        ctx.paths.root / variant.video_path if variant.video_path else ctx.paths.video(variant_id)
    )
    return SimulationRequest(
        brief=ctx.brief,
        concept=ctx.read_concept(variant_id),
        video_path=video_path,
        video_sha256=variant.video_sha256,
        artifacts_dir=artifacts,
    )


def _require_matches(
    result: SimulationResult, variant: VariantRecord, simulator: Simulator
) -> None:
    """Reject a result that is about another variant, simulator or video than was asked."""
    expected = (variant.variant_id, simulator.name, variant.video_sha256)
    if (result.variant_id, result.simulator, result.video_sha256) != expected:
        raise PreflightValidationError(
            f"{simulator.name} returned a result that does not match variant {variant.variant_id}"
        )
