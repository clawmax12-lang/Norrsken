"""Composition root: the real components behind every port, built once per run.

Each run gets its own ``TokenLedger`` (so ``report.json`` shows that run's Condense savings)
and its own Condense session id (so the run is grouped in the Condense dashboard). Every
Gemini generation (planner, viewer panel, explanations) goes through the Condense proxy
(FR-10); only the free ``countTokens`` calls that measure the savings go to Gemini directly.
"""

import httpx

from preflight.config import Settings
from preflight.contracts import RunRecord
from preflight.explain.gemini import GeminiExplainer
from preflight.finalization.job import FinalizationJob
from preflight.finalization.opus import OpusComposer
from preflight.finalization.service import FinalizationService
from preflight.finalization.source import FinalSource
from preflight.generation.assets import TemplateBackdrops
from preflight.generation.compose import TemplateComposer
from preflight.llm import GenAIBackend, TokenLedger, build_gemini_client
from preflight.orchestrator import Pipeline
from preflight.orchestrator.retry import StepPolicy
from preflight.planning.planner import GeminiPlanner
from preflight.ports import Clock, Simulator
from preflight.rendering import RemotionRenderer
from preflight.simulators.gemini_panel.panel import GeminiViewerPanel
from preflight.simulators.tribe import TribeSimulator
from preflight.sound import Ffmpeg, GeminiSpeech, SoundStudio
from preflight.storage import ProjectPaths, ProjectStore


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
            GeminiPlanner(client, self._store),
            TemplateBackdrops(),
            TemplateComposer(),
            renderer,
            simulators,
            GeminiExplainer(client),
            ledger,
            settings,
            self._clock,
            sound=_sound_studio(settings, self._store.paths(project_id)),
        )

    def finalization_service(self) -> FinalizationService:
        """Separate, explicit last step; does not change the three-video Gemini pipeline."""
        return FinalizationService(
            self._settings, self._store, self.build_finalization, self._clock
        )

    def build_finalization(self, project_id: str, source: FinalSource) -> FinalizationJob:
        """Use Opus only for motion composition; Gemini/TRIBE retest the final MP4."""
        settings, http = self._settings, self._http
        client = build_gemini_client(
            settings, ledger=TokenLedger(), http_client=http, project_id=project_id
        )
        paths = self._store.paths(project_id)
        simulators: list[Simulator] = [GeminiViewerPanel(client)]
        if settings.tribe_endpoint:
            simulators.insert(0, TribeSimulator(http, settings.tribe_endpoint, paths.root))
        return FinalizationJob(
            self._store,
            project_id,
            source,
            OpusComposer(settings, http),
            RemotionRenderer(
                settings.renderer_dir,
                paths.root,
                node=settings.node_binary,
                concurrency=settings.render_concurrency,
            ),
            simulators,
            # Keep the existing audio team's stage intact. No new direct TTS routing
            # exception: the Opus final has local music/SFX, not extra narration calls.
            SoundStudio(Ffmpeg(settings.ffmpeg_binary, settings.ffprobe_binary), None)
            if settings.sound_enabled
            else None,
            StepPolicy.from_settings(settings),
            self._clock,
        )


def _sound_studio(settings: Settings, paths: ProjectPaths) -> SoundStudio | None:
    """Narration, music and effects for the exported videos, or ``None`` when sound is off.

    Narration calls Gemini's text-to-speech model directly, not through Condense: Condense
    documents only text chat routes, and each call sends a single on-screen line, so there is
    nothing to compress. This is a logged exception to FR-10 (PRD §16).
    """
    if not settings.sound_enabled:
        return None
    speech = None
    if settings.narration_enabled and settings.gemini_api_key is not None:
        speech = GeminiSpeech(
            GenAIBackend.from_api_key(settings.gemini_api_key.get_secret_value()),
            model=settings.tts_model,
            voice=settings.narration_voice,
            cache_dir=paths.sound_work / "cache",
        )
    ffmpeg = Ffmpeg(settings.ffmpeg_binary, settings.ffprobe_binary)
    return SoundStudio(ffmpeg, speech, voice=settings.narration_voice, tts_model=settings.tts_model)
