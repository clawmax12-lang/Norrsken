from preflight.contracts import Layout, Transition
from preflight.generation.compose import TRANSITION_FRAMES, compose
from tests.factories import make_brief, make_concept


def test_the_opening_scene_is_type_only() -> None:
    concept = make_concept("A")
    spec = compose(make_brief(), concept, ())

    assert spec.scenes[0].layout is Layout.TEXT_ONLY
    assert spec.scenes[0].text == concept.hook
    assert spec.scenes[0].transition_in is Transition.FADE
    assert spec.scenes[1].layout is Layout.DEVICE_CENTER
    assert spec.scenes[-1].start_frame == 360
    assert spec.scenes[-1].end_frame == 450
    assert spec.headline == "Notes that organise themselves"
    assert spec.wordmark == "Acme Notes"
    assert [scene.transition_in for scene in spec.scenes[1:]] == [
        Transition.SCALE,
        Transition.PUSH,
        Transition.FADE,
        Transition.FADE,
    ]


def test_transition_overlap_is_twenty_frames() -> None:
    assert TRANSITION_FRAMES == 20


def test_showcase_spec_stays_locked_at_thirty_fps() -> None:
    spec = compose(make_brief(), make_concept("A"), ())
    assert spec.fps == 30
    assert spec.duration_frames == 450
    assert spec.width == 1080
    assert spec.height == 1920
