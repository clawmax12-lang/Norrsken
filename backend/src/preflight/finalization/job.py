"""One resumable selected-video job. Original candidates, hashes and ranking stay untouched."""

from collections.abc import Callable, Sequence
from functools import partial

from preflight.contracts import CreativeConcept, Scene, SimulationResult, SimulatorName, Step
from preflight.contracts.finalization import FinalComposition, FinalizationRecord, FinalStatus
from preflight.errors import PreflightError, PreflightValidationError, RenderError
from preflight.hashing import sha256_file
from preflight.orchestrator.activity import ActivityLog
from preflight.orchestrator.retry import StepPolicy
from preflight.ports import (
    Clock,
    Renderer,
    SimulationRequest,
    Simulator,
    SoundFinisher,
    SoundRequest,
)
from preflight.storage import ProjectStore

from .opus import FinalComposer
from .source import FinalSource


class FinalizationJob:
    """Compose → render → sound → simulate EXACT final bytes; not a second A/B ranking."""

    def __init__(  # noqa: PLR0913, PLR0917 - one port per finalization collaborator
        self,
        store: ProjectStore,
        project_id: str,
        source: FinalSource,
        composer: FinalComposer,
        renderer: Renderer,
        simulators: Sequence[Simulator],
        sound: SoundFinisher | None,
        policy: StepPolicy,
        clock: Clock,
    ) -> None:
        """All expensive collaborators are injected; none run on selection or playback."""
        self._store, self._paths = store, store.paths(project_id)
        self._id, self._source = project_id, source
        self._composer, self._renderer = composer, renderer
        self._simulators, self._sound = simulators, sound
        self._policy, self._clock = policy, clock
        self._log = ActivityLog(store, project_id, clock)
        self._record = store.read(self._paths.finalization, FinalizationRecord)

    async def run(self, *, verify_source: Callable[[], None]) -> None:
        """Persist checkpoints; errors never replace the original run's DONE or verdict."""
        with self._log.step(
            Step.EXPORT, "Finishing selected video with Opus", variant_id=self._record.variant_id
        ):
            composition = await self._compose()
            await self._render(composition)
            await self._add_sound(composition)
            await self._simulate(composition)
            verify_source()
            self._save(
                status=FinalStatus.DONE,
                files={
                    "video": f"/api/projects/{self._id}/finalization/video",
                    "report": f"/api/projects/{self._id}/finalization/report",
                },
            )

    def fail(self, message: str) -> None:
        """Persist a sanitized, resumable failure without changing original candidate files."""
        self._save(status=FinalStatus.FAILED, error=message, files={})

    def _save(self, **changes: object) -> None:
        self._record = self._record.model_copy(
            update={"updated_at": self._clock(), "error": None, **changes}
        )
        self._store.write(self._paths.finalization, self._record)

    async def _compose(self) -> FinalComposition:
        path = self._paths.opus_dir / "composition.json"
        if path.is_file():
            composition = self._store.read(path, FinalComposition)
            self._save(usage=composition.usage)
            return composition
        if self._record.opus_attempts >= 2:
            raise PreflightError("Opus attempt limit reached; original winner remains available")
        self._save(status=FinalStatus.COMPOSING, opus_attempts=self._record.opus_attempts + 1)
        # No automatic Opus retry. A failed/uncertain call needs another explicit confirmation.
        once = StepPolicy(self._policy.timeout_s, retries=0)
        spec, usage = await once.run(
            partial(self._composer.compose, self._source.spec, self._source.report, self._id)
        )
        composition = FinalComposition(spec=spec, usage=usage)
        self._store.write(path, composition)
        self._save(usage=usage)
        return composition

    async def _render(self, composition: FinalComposition) -> None:
        path = self._paths.opus_dir / "picture.mp4"
        if self._record.render is not None:
            if not path.is_file() or sha256_file(path) != self._record.render.video_sha256:
                raise PreflightValidationError("Final render checkpoint changed or is missing")
            return
        self._save(status=FinalStatus.RENDERING)
        result = await self._policy.run(
            partial(self._renderer.render, composition.spec, path), retry_on=(RenderError,)
        )
        if sha256_file(path) != result.video_sha256:
            raise PreflightValidationError("Final renderer returned a mismatched video hash")
        self._save(render=result.model_copy(update={"video_path": "finalization/picture.mp4"}))

    async def _add_sound(self, composition: FinalComposition) -> None:
        picture = self._paths.opus_dir / "picture.mp4"
        render = self._record.render
        if render is None:
            raise PreflightError("Final video has not rendered")
        if self._record.video_sha256 is not None:
            final = self._paths.opus_dir / ("final.mp4" if self._record.sound else "picture.mp4")
            if not final.is_file() or sha256_file(final) != self._record.video_sha256:
                raise PreflightValidationError("Final video checkpoint changed or is missing")
            return
        self._save(status=FinalStatus.AUDIO)
        sound = None
        if self._sound is not None:
            request = SoundRequest(
                composition.spec,
                picture,
                render.video_sha256,
                self._paths.opus_dir / "final.mp4",
                self._paths.opus_dir / "sound",
            )
            try:
                sound = await self._policy.run(partial(self._sound.finish, request))
            except PreflightError:
                self._log.skipped(
                    Step.EXPORT, "Final sound unavailable; testing the silent Opus render"
                )
            if sound and sha256_file(request.output_path) != sound.final_video_sha256:
                raise PreflightValidationError("Final sound output hash does not match")
        self._save(
            sound=sound, video_sha256=sound.final_video_sha256 if sound else render.video_sha256
        )

    async def _simulate(self, composition: FinalComposition) -> None:
        self._save(status=FinalStatus.SIMULATING)
        path = self._paths.opus_dir / ("final.mp4" if self._record.sound else "picture.mp4")
        digest = sha256_file(path)
        if digest != self._record.video_sha256:
            raise PreflightValidationError("Final video changed before simulation")
        request = SimulationRequest(
            self._source.brief,
            _concept(composition, self._source),
            path,
            digest,
            self._paths.opus_dir / "brain",
        )
        results = []
        for simulator in self._simulators:
            result = await self._one_simulator(simulator, request)
            if result is not None:
                results.append(result)
                self._save(simulations=tuple(results))
        if not any(r.simulator is SimulatorName.GEMINI_PANEL for r in results):
            raise PreflightError("No Gemini pretest for the final video; it is not a tested export")
        if sha256_file(path) != digest:
            raise PreflightValidationError("Final video changed during simulation")
        self._save(
            simulations=tuple(results),
            brain_sim=any(r.simulator is SimulatorName.TRIBE_V2 for r in results),
        )

    async def _one_simulator(
        self, simulator: Simulator, request: SimulationRequest
    ) -> SimulationResult | None:
        cached = self._paths.opus_dir / f"{simulator.name.value}.json"
        if cached.is_file():
            result = self._store.read(cached, SimulationResult)
        else:
            try:
                result = await self._policy.run(partial(simulator.simulate, request))
            except PreflightError:
                if simulator.name is SimulatorName.GEMINI_PANEL:
                    raise
                self._log.skipped(Step.EXPORT, "Final brain sim off; TRIBE unavailable")
                return None
        if (
            result.video_sha256 != request.video_sha256
            or result.variant_id != self._record.variant_id
            or result.simulator != simulator.name
            or result.duration_s != 15
            or result.precomputed
        ):
            raise PreflightValidationError("Final simulation does not describe this exact video")
        self._store.write(cached, result)
        return result


def _concept(composition: FinalComposition, source: FinalSource) -> CreativeConcept:
    spec = composition.spec
    return CreativeConcept(
        variant_id=spec.variant_id,
        hypothesis=source.concept.hypothesis,
        hook=spec.scenes[0].text,
        hook_source_field=spec.scenes[0].source_field,
        scenes=tuple(
            Scene(
                t_start=s.start_frame / spec.fps,
                t_end=s.end_frame / spec.fps,
                screenshot=s.screenshot,
                text=s.text,
                source_field=s.source_field,
            )
            for s in spec.scenes
        ),
        cta=spec.cta,
        cta_source_field=spec.cta_source_field,
    )
