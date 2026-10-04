from tests.factories import make_brief, make_concept

from preflight.contracts import RenderMode
from preflight.generation.compose import compose
from preflight.motion.compose import compose_motion
from preflight.motion.pipeline import MotionPipeline
from preflight.motion.scene import ExtractedLayers, LayerKind, MotionLayer
from preflight.storage import ProjectStore


def _layers() -> tuple[MotionLayer, ...]:
    return (
        MotionLayer(id="a", kind=LayerKind.PANEL, bbox_norm=(0.1, 0.2, 0.5, 0.4), confidence=0.9),
        MotionLayer(
            id="b", kind=LayerKind.BUTTON, bbox_norm=(0.2, 0.7, 0.3, 0.08), confidence=0.88
        ),
    )


def test_compose_motion_tiles_900_frames() -> None:
    concept = make_concept("A")
    extracted = {
        scene.screenshot: ExtractedLayers(screenshot=scene.screenshot, layers=_layers())
        for scene in concept.scenes
    }
    spec = compose_motion(concept, compose(make_brief(), concept, ()).theme, extracted)
    assert spec is not None
    assert spec.fps == 60
    assert spec.duration_frames == 900
    assert spec.shots[-1].end_frame == 900
    assert spec.shots[-1].layers == ()
    assert spec.shots[-1].start_frame == 720
    assert spec.underlay is False


def test_compose_motion_fails_closed_without_layers() -> None:
    concept = make_concept("A")
    extracted = {
        scene.screenshot: ExtractedLayers(screenshot=scene.screenshot, layers=(), skipped="too few")
        for scene in concept.scenes
    }
    assert compose_motion(concept, compose(make_brief(), concept, ()).theme, extracted) is None


async def test_pipeline_stub_without_client_always_falls_back(tmp_path) -> None:
    store = ProjectStore(tmp_path)
    paths = store.create("proj-1")
    brief = make_brief(project_id="proj-1", render_mode=RenderMode.GENERATIVE_MOTION)
    store.write(paths.brief, brief)
    concept = make_concept("A")
    showcase = compose(brief, concept, ())
    result = await MotionPipeline().try_render(brief, concept, showcase, paths, paths.video("A"))
    assert result is None
    assert not paths.motion_spec("A").exists()
