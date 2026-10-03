"""FR-09 / PRD §9: the deterministic, resumable state machine.

``BRIEF_RECEIVED -> PLANNED -> RENDERED -> SIMULATED -> SCORED -> EXPLAINED -> DONE`` (or
``FAILED``). The pipeline only sequences stages: each stage persists its artifacts through
the project store, so a re-run resumes after the last completed state without repeating work.
Nothing here knows about HTTP; the API layer reads the log and ``run.json`` from the store.
"""

from collections.abc import Sequence

from preflight.config import Settings
from preflight.contracts import Brief, RunRecord, RunState
from preflight.errors import PreflightError
from preflight.explain import next_time_suggestions
from preflight.ports import (
    AssetGenerator,
    Clock,
    Composer,
    Explainer,
    Planner,
    Renderer,
    Simulator,
    UsageMeter,
)
from preflight.scoring import score_and_rank
from preflight.storage import ProjectStore

from .activity import ActivityLog
from .archive import SimulationArchive
from .context import RunContext
from .retry import StepPolicy
from .stages import (
    ExplainStage,
    NextTimeSuggester,
    PlanStage,
    Ranker,
    RenderStage,
    ScoreStage,
    SimulateStage,
    Stage,
)
from .tracker import RunTracker


class Pipeline:
    """Runs one project from its saved brief to a ranked, explained report."""

    def __init__(  # noqa: PLR0913, PLR0917 - composition root: one port per component
        self,
        store: ProjectStore,
        planner: Planner,
        asset_generator: AssetGenerator,
        composer: Composer,
        renderer: Renderer,
        simulators: Sequence[Simulator],
        explainer: Explainer,
        usage: UsageMeter,
        settings: Settings,
        clock: Clock,
        *,
        ranker: Ranker = score_and_rank,
        next_time: NextTimeSuggester = next_time_suggestions,
    ) -> None:
        """Wire the ports; ``ranker`` and ``next_time`` default to the real pure functions."""
        policy = StepPolicy.from_settings(settings)
        self._store = store
        self._clock = clock
        self._simulator_names = tuple(simulator.name for simulator in simulators)
        self._stages: tuple[Stage, ...] = (
            PlanStage(planner, policy, settings.max_variants),
            RenderStage(asset_generator, composer, renderer, policy),
            SimulateStage(simulators, policy),
            ScoreStage(ranker),
            ExplainStage(explainer, usage, policy, next_time),
        )

    async def run(self, project_id: str) -> RunRecord:
        """Run or resume ``project_id`` and return its final record (``DONE`` or ``FAILED``).

        Expected failures (``PreflightError``) end in ``FAILED`` with the reason recorded and
        can be re-run to resume. Unexpected exceptions propagate and leave ``run.json`` at
        the last completed state, which is exactly where the next ``run`` resumes.
        """
        ctx = self._open(project_id)
        if ctx.tracker.record.state is RunState.DONE:
            return ctx.tracker.record
        try:
            for stage in self._stages:
                await _run_stage(stage, ctx)
        except PreflightError as exc:
            ctx.tracker.fail(exc)
        else:
            ctx.tracker.advance(RunState.DONE)
        return ctx.tracker.record

    def _open(self, project_id: str) -> RunContext:
        paths = self._store.paths(project_id)
        return RunContext(
            store=self._store,
            paths=paths,
            brief=self._store.read(paths.brief, Brief),
            log=ActivityLog(self._store, project_id, self._clock),
            tracker=RunTracker.open(self._store, project_id, self._clock),
            archive=SimulationArchive(self._store, paths, self._simulator_names),
        )


async def _run_stage(stage: Stage, ctx: RunContext) -> None:
    if ctx.tracker.has_completed(stage.completes):
        ctx.log.skipped(stage.step, f"{stage.step.value} already complete; resuming after it")
        return
    with ctx.log.step(stage.step, stage.title) as handle:
        handle.report(await stage.run(ctx))
    ctx.tracker.advance(stage.completes)
