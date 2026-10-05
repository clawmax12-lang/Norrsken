from preflight.contracts import BeatKind, Layout, Transition
from preflight.generation.compose import TRANSITION_FRAMES, compose
from tests.factories import make_brief, make_concept


def test_the_opening_scene_shows_the_product_from_the_first_frame() -> None:
    concept = make_concept("A")
    spec = compose(make_brief(), concept, ())

    assert spec.scenes[0].layout is Layout.DEVICE_CENTER
    assert spec.scenes[0].screenshot == concept.scenes[0].screenshot
    assert spec.scenes[0].text == concept.hook
    assert spec.scenes[0].transition_in is Transition.CUT
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


def test_voice_focus_emphasis_and_chips_reach_the_renderer() -> None:
    base = make_concept("A")
    first = base.scenes[1].model_copy(
        update={
            "voice": "Your notes sort themselves",
            "focus": (0.1, 0.2, 0.5, 0.3),
            "emphasis": "organise",
        }
    )
    concept = base.model_copy(
        update={
            "scenes": (base.scenes[0], first, *base.scenes[2:]),
            "end_voice": "Try Acme Notes",
            "chips": ("For busy founders",),
        }
    )

    spec = compose(make_brief(), concept, ())

    assert spec.scenes[1].voice == "Your notes sort themselves"
    assert spec.scenes[1].focus == (0.1, 0.2, 0.5, 0.3)
    assert spec.scenes[1].emphasis == "organise"
    assert spec.scenes[-1].focus is None and spec.scenes[-1].voice is None
    assert spec.end_voice == "Try Acme Notes"
    assert spec.chips == ("For busy founders",)


def test_the_spec_carries_one_clock_for_words_beats_and_sound() -> None:
    base = make_concept("A")
    timed = base.scenes[1].model_copy(
        update={
            "text": "Save 3 hours",
            "voice": "Save three hours",
            "voice_s": 1.2,
            "voice_words": (0.0, 0.4, 0.8),
            "focus": (0.1, 0.2, 0.4, 0.2),
        }
    )
    concept = base.model_copy(update={"scenes": (base.scenes[0], timed, *base.scenes[2:])})

    spec = compose(make_brief(), concept, ())

    kinds = [(beat.kind, beat.scene) for beat in spec.beats]
    assert kinds[0] == (BeatKind.HOOK, 0)
    assert (BeatKind.MOVE, 1) in kinds and (BeatKind.COUNT, 1) in kinds
    assert (BeatKind.TAP, 1) in kinds and (BeatKind.PUNCH, 1) in kinds
    assert kinds[-2:] == [(BeatKind.CTA, 4), (BeatKind.TAP, 4)]  # the finger presses the button
    assert [beat.frame for beat in spec.beats] == sorted(beat.frame for beat in spec.beats)
    assert spec.scenes[0].text_frames == (0, 0, 0, 0)
    assert spec.scenes[1].text_frames[0] == round((3 + 0.3) * 30)
    assert spec.scenes[-1].text_frames == ()
