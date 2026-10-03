import hashlib
from dataclasses import dataclass, field

from pydantic import SecretStr

from preflight.config import Settings
from preflight.contracts import CompositionSpec, RenderResult, Report, RunRecord, RunState
from preflight.contracts.finalization import (
    FinalizationRecord,
    FinalizeCommand,
    MotionRecipe,
    OpusUsage,
)
from preflight.errors import ProviderError
from preflight.finalization.job import FinalizationJob
from preflight.finalization.opus import apply_recipe
from preflight.finalization.service import FinalizationService
from preflight.orchestrator.retry import StepPolicy
from tests.factories import FIXED_NOW
from tests.orchestrator.fakes import FakeRenderer, FakeSoundFinisher, World


def recipe(spec):
    return MotionRecipe(
        scenes=tuple(
            {
                "duration_frames": s.end_frame - s.start_frame,
                "layout": "device_float",
                "transition_in": "push",
            }
            for s in spec.scenes
        )
    )


@dataclass
class FakeOpus:
    calls: int = 0
    failures: int = 0

    async def compose(self, spec: CompositionSpec, report: Report, project_id: str):
        self.calls += 1
        if self.failures:
            self.failures -= 1
            raise ProviderError("Opus temporarily unavailable")
        return apply_recipe(spec, recipe(spec)), OpusUsage(
            model="claude-opus-5-5",
            input_tokens=800,
            output_tokens=240,
        )


class FinalRenderer(FakeRenderer):
    async def render(self, spec, output):
        self.calls.append(spec.variant_id)
        self.failures.maybe_raise(spec.variant_id)
        data = b"MOCK-Opus-render-" + spec.model_dump_json().encode()
        output.write_bytes(data)
        return RenderResult(
            variant_id=spec.variant_id,
            video_path=str(output),
            video_sha256=hashlib.sha256(data).hexdigest(),
            render_seconds=1,
        )


@dataclass
class FinalWorld:
    world: World
    opus: FakeOpus = field(default_factory=FakeOpus)
    renderer: FinalRenderer = field(default_factory=FinalRenderer)
    sound: FakeSoundFinisher | None = field(default_factory=FakeSoundFinisher)

    @property
    def settings(self):
        return Settings(
            anthropic_api_key=SecretStr("MOCK-ant"),
            condense_api_key=SecretStr("MOCK-condense"),
            gemini_api_key=SecretStr("MOCK-google"),
        )

    @property
    def command(self):
        paths, store = self.world.store.paths(self.world.project_id), self.world.store
        report = store.read(paths.report, Report)
        run = self.world.store.read(paths.run, RunRecord)
        source = next(v.video_sha256 for v in run.variants if v.variant_id == report.winner)
        return FinalizeCommand(
            command_id="finish-12345678",
            confirmed=True,
            variant_id=report.winner,
            source_video_sha256=source,
        )

    def job(self, project_id, source):
        return FinalizationJob(
            self.world.store,
            project_id,
            source,
            self.opus,
            self.renderer,
            [self.world.gemini, *self.world.extra_simulators],
            self.sound,
            StepPolicy(2, 1),
            lambda: FIXED_NOW,
        )

    def service(self, **overrides):
        return FinalizationService(
            self.settings.model_copy(update=overrides),
            self.world.store,
            self.job,
            lambda: FIXED_NOW,
        )

    def record(self):
        return self.world.store.read(
            self.world.store.paths(self.world.project_id).finalization, FinalizationRecord
        )


async def seed_final_world(store):
    world = World(store)
    paths = store.paths(world.project_id)
    for screenshot in world.store.read_brief(world.project_id).screenshots:
        path = paths.root / screenshot
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"MOCK screenshot")
    result = await world.pipeline().run(world.project_id)
    assert result.state is RunState.DONE
    return FinalWorld(world)
