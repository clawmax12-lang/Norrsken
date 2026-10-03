"""Composition root: the real components behind every port, built once per run.

Each run gets its own ``TokenLedger`` (so ``report.json`` shows that run's Condense savings)
and its own Condense session id (so the run is grouped in the Condense dashboard). The
planner calls Gemini directly because the Condense proxy rewrites its multi-screenshot
message; the viewer panel and the explanations go through the proxy (FR-10).
"""

import httpx

from preflight.config import Settings
from preflight.contracts import RunRecord
from preflight.explain.gemini import GeminiExplainer
from preflight.generation.assets import TemplateBackdrops
from preflight.generation.compose import TemplateComposer
from preflight.llm import TokenLedger, build_gemini_client
from preflight.orchestrator import Pipeline
from preflight.planning.planner import GeminiPlanner
from preflight.ports import Clock, Simulator
from preflight.rendering import RemotionRenderer
from preflight.simulators.gemini_panel.panel import GeminiViewerPanel
from preflight.simulators.tribe import TribeSimulator
from preflight.storage import ProjectStore


class ProductionRunService:
    """Implements ``api.RunService`` with Gemini, Condense, Remotion and (optionally) TRIBE."""

    def __init__(
        self,
        settings: Settings,
        store: ProjectStore,
        http_client: httpx.AsyncClient,
        clock: Clock,
    ) -> None:
        """The caller owns ``http_client``'s lifetime."""
        self._settings = settings
        self._store = store
        self._http = http_client
        self._clock = clock

    async def run(self, project_id: str) -> RunRecord:
        """Build the pipeline for ``project_id`` and run it to ``DONE`` or ``FAILED``.

        Raises:
            ProviderError: ``GEMINI_API_KEY`` is not set (the run is then marked failed).
        """
        return await self.build_pipeline(project_id).run(project_id)

    def build_pipeline(self, project_id: str) -> Pipeline:
        """Wire every port for one project."""
        settings, http = self._settings, self._http
        ledger = TokenLedger()
        client = build_gemini_client(
            settings, ledger=ledger, http_client=http, project_id=project_id
        )
        planner_client = build_gemini_client(
            settings, ledger=ledger, http_client=http, project_id=project_id, proxy=False
        )
        root = self._store.paths(project_id).root
        simulators: list[Simulator] = [GeminiViewerPanel(client)]
        if settings.tribe_endpoint:
            simulators.insert(0, TribeSimulator(http, settings.tribe_endpoint, root))
        renderer = RemotionRenderer(
            settings.renderer_dir,
            root,
            node=settings.node_binary,
            concurrency=settings.render_concurrency,
        )
        return Pipeline(
            self._store,
            GeminiPlanner(planner_client, self._store),
            TemplateBackdrops(),
            TemplateComposer(),
            renderer,
            simulators,
            GeminiExplainer(client),
            ledger,
            settings,
            self._clock,
        )
