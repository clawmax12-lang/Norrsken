import hashlib

from preflight.contracts import (
    CompositionSpec,
    RenderMode,
    RenderResult,
    RenderStatus,
    Step,
    StepStatus,
)
from preflight.motion.pipeline import MotionPipeline
from preflight.orchestrator.stages.render import RenderStage
from preflight.storage import ProjectStore
from tests.factories import make_brief
from tests.orchestrator.fakes import World


class _FailingMotion(MotionPipeline):
    async def ready_for_all(self, *args, **kwargs):
        return False

    async def try_render(self, brief, concept, showcase, paths, output):
        return None


class _SpyMotion(MotionPipeline):
    def __init__(self) -> None:
        super().__init__()
        self.calls = 0

    async def try_render(self, *args, **kwargs):
        self.calls += 1


class _OkMotion(MotionPipeline):
    async def ready_for_all(self, *args, **kwargs):
        return True

    async def try_render(self, brief, concept, showcase, paths, output):
        data = b"motion-bytes"
        output.write_bytes(data)
        return RenderResult(
            variant_id=concept.variant_id,
            video_path=str(output),
            video_sha256=hashlib.sha256(data).hexdigest(),
            render_seconds=1.0,
        )


async def test_motion_mode_falls_back_to_unchanged_showcase_bytes(tmp_path) -> None:
    world = World(store=ProjectStore(tmp_path))
    world.store.write(
        world.store.paths(world.project_id).brief,
        make_brief(project_id=world.project_id, render_mode=RenderMode.GENERATIVE_MOTION),
    )
    pipeline = world.pipeline()
    next(s for s in pipeline._stages if isinstance(s, RenderStage))._motion = _FailingMotion()

    record = await pipeline.run(world.project_id)

    assert all(variant.render_status is RenderStatus.RENDERED for variant in record.variants)
    video = world.store.paths(world.project_id).video("A")
    assert video.read_bytes() == b"video-A"
    spec = world.store.read(world.store.paths(world.project_id).spec("A"), CompositionSpec)
    assert spec.fps == 30
    events = list(world.store.read_events(world.project_id))
    assert any(
        event.step is Step.RENDER
        and event.status is StepStatus.SKIPPED
        and "Showcase" in event.message
        for event in events
    )


async def test_default_showcase_never_calls_motion(tmp_path) -> None:
    world = World(store=ProjectStore(tmp_path))
    spy = _SpyMotion()
    pipeline = world.pipeline()
    next(s for s in pipeline._stages if isinstance(s, RenderStage))._motion = spy
    await pipeline.run(world.project_id)
    assert spy.calls == 0
    assert world.store.paths(world.project_id).video("A").read_bytes() == b"video-A"


async def test_motion_success_writes_motion_bytes_and_keeps_showcase_spec(tmp_path) -> None:
    world = World(store=ProjectStore(tmp_path))
    world.store.write(
        world.store.paths(world.project_id).brief,
        make_brief(project_id=world.project_id, render_mode=RenderMode.GENERATIVE_MOTION),
    )
    pipeline = world.pipeline()
    next(s for s in pipeline._stages if isinstance(s, RenderStage))._motion = _OkMotion()
    await pipeline.run(world.project_id)
    assert world.store.paths(world.project_id).video("A").read_bytes() == b"motion-bytes"
    spec = world.store.read(world.store.paths(world.project_id).spec("A"), CompositionSpec)
    assert spec.fps == 30
