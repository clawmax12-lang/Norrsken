"""SCORED: deterministic ranking of the variants that were simulated (FR-05)."""

import logging
from collections.abc import Mapping, Sequence
from typing import Protocol

from preflight.contracts import Ranking, RenderStatus, RunState, SimulationResult, Step
from preflight.orchestrator.context import RunContext

_LOG = logging.getLogger(__name__)


class Ranker(Protocol):
    """The shape of :func:`preflight.scoring.score_and_rank` that the pipeline relies on."""

    def __call__(
        self, results: Sequence[SimulationResult], *, excluded: Mapping[str, str] | None = None
    ) -> Ranking:
        """Return the ranking; ``excluded`` maps variants left out to the reason."""
        ...


class ScoreStage:
    """Ranks what exists: failed renders are excluded, never invented into a ranking."""

    step = Step.SCORE
    completes = RunState.SCORED
    title = "Scoring and ranking"

    def __init__(self, ranker: Ranker) -> None:
        """Rank with ``ranker``."""
        self._ranker = ranker

    async def run(self, ctx: RunContext) -> str:
        """Write ``ranking.json`` and summarise the verdict in one line."""
        results = ctx.archive.scoring_results(ctx.rendered_variants())
        ranking = self._ranker(results, excluded=_failed_renders(ctx))
        ctx.store.write(ctx.paths.ranking, ranking)
        summary = f"Ranked {len(ranking.order)} variants; winner {ranking.order[0]}"
        if len(ranking.order) == 1:
            _LOG.warning("only one variant rendered: no runner-up for %s", ctx.paths.root.name)
            summary += " (the only variant that rendered, so there is no runner-up)"
        return f"{summary}; confidence {ranking.confidence.value}"


def _failed_renders(ctx: RunContext) -> dict[str, str]:
    return {
        v.variant_id: v.error or "render failed"
        for v in ctx.tracker.record.variants
        if v.render_status is RenderStatus.FAILED
    }
