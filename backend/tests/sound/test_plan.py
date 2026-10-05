import pytest

from preflight.contracts import Beat, BeatKind, CueKind, SceneSpec, Transition
from preflight.generation.compose import compose
from preflight.motion.compose import compose_motion
from preflight.motion.scene import ExtractedLayers, LayerKind, MotionLayer
from preflight.sound.plan import BEAT_S, plan_motion_soundtrack, plan_soundtrack
from tests.factories import make_brief, make_concept
from tests.sound.helpers import make_spec


def test_every_cut_lands_on_a_beat() -> None:
    spec = make_spec()
    for scene in spec.scenes:
        start = scene.start_frame / spec.fps
        assert start / BEAT_S == pytest.approx(round(start / BEAT_S))


def test_sound_structure_follows_the_scenes_and_the_end_card() -> None:
    plan = plan_soundtrack(make_spec())

    assert plan.duration_s == 15.0
    assert plan.drop_s == 3.0  # the first scene change
    assert plan.outro_s == 12.0  # locked 3 s end card, snapped to a beat


def test_narration_covers_distinct_copy_then_the_end_card() -> None:
    plan = plan_soundtrack(make_spec())

    # Fixture scenes reuse the one-liner, so dedupe keeps a single opening line.
    assert len(plan.lines) == 1
    assert plan.lines[0].start_s == pytest.approx(0.3)
    assert plan.lines[0].text == "Notes that organise themselves"

    varied = make_spec(
        hook="Start here",
        scenes=tuple(
            scene.model_copy(update={"text": text})
            for scene, text in zip(
                make_concept().scenes,
                ("Start here", "Keep going", "See results", "Try Acme", "Acme Notes"),
                strict=True,
            )
        ),
    )
    varied_plan = plan_soundtrack(varied)
    texts = [line.text.casefold() for line in varied_plan.lines]
    assert len(texts) == len(set(texts))
    assert varied_plan.lines[-1].start_s > varied_plan.outro_s - BEAT_S


VOICES = (
    "Your notes sort themselves",
    "Find anything in seconds",
    "Every idea lands in place",
    "Built for busy founders",
)


def _voiced_spec():
    scenes = tuple(
        scene.model_copy(update={"voice": voice})
        for scene, voice in zip(make_concept().scenes, (*VOICES, None), strict=True)
    )
    return make_spec(scenes=scenes, end_voice="Try Acme Notes")


def test_a_written_voice_over_is_spoken_in_full_without_dedupe() -> None:
    plan = plan_soundtrack(_voiced_spec())

    assert [line.text for line in plan.lines] == [*VOICES, "Try Acme Notes"]
    assert plan.lines[-1].start_s > plan.outro_s - BEAT_S


def test_the_voice_over_has_no_gap_longer_than_a_second_before_the_end_card() -> None:
    plan = plan_soundtrack(_voiced_spec())

    ends = [line.start_s + line.window_s for line in plan.lines]
    gaps = [later.start_s - end for end, later in zip(ends, plan.lines[1:], strict=False)]
    assert all(0 < gap <= 1.0 for gap in gaps)


def test_lines_never_overlap_and_end_before_the_video_does() -> None:
    plan = plan_soundtrack(make_spec())

    ends = [line.start_s + line.window_s for line in plan.lines]
    assert all(later.start_s > end for end, later in zip(ends, plan.lines[1:], strict=False))
    assert ends[-1] <= plan.duration_s


def test_every_line_keeps_its_source_field() -> None:
    spec = make_spec()
    plan = plan_soundtrack(spec)

    assert plan.lines[0].source_field == spec.scenes[0].source_field
    assert plan.lines[-1].source_field == spec.headline_source_field


def test_a_spec_with_beats_gets_one_figure_per_beat_on_its_frame() -> None:
    spec = make_spec().model_copy(
        update={
            "beats": (
                Beat(kind=BeatKind.HOOK, frame=0, frames=8, scene=0),
                Beat(kind=BeatKind.MOVE, frame=90, frames=18, scene=1),
                Beat(kind=BeatKind.TAP, frame=130, frames=8, scene=1, point=(0.9, 0.5)),
                Beat(kind=BeatKind.PUNCH, frame=134, frames=10, scene=1),
                Beat(kind=BeatKind.COUNT, frame=150, frames=15, scene=1),
                Beat(kind=BeatKind.WORD, frame=200, frames=6, scene=2),
                Beat(kind=BeatKind.CTA, frame=360, frames=8, scene=4),
            )
        }
    )

    cues = plan_soundtrack(spec).cues

    def at(kind: CueKind) -> list[float]:
        return [round(cue.t, 3) for cue in cues if cue.kind is kind]

    assert at(CueKind.THUD) == [0.0, 12.0]
    assert at(CueKind.TAP) == [round(130 / 30, 3)]
    whoosh = next(cue for cue in cues if cue.kind is CueKind.WHOOSH and cue.t < 4)
    assert whoosh.t == pytest.approx((90 + 18 * 0.6) / 30)
    assert whoosh.duration_s == pytest.approx(18 / 30 + 0.25)
    assert whoosh.pan == 0.5
    assert len(at(CueKind.TICK)) == 6
    assert at(CueKind.CONFIRM) == [round(165 / 30, 3)]
    assert round(200 / 30, 3) in at(CueKind.POP)
    assert at(CueKind.RISER) == [12.0]
    assert 12.28 in at(CueKind.POP)
    tap = next(cue for cue in cues if cue.kind is CueKind.TAP)
    assert tap.pan is not None and tap.pan > 0


def test_a_headline_that_follows_the_voice_gets_a_soft_select_as_it_appears() -> None:
    spec = make_spec()
    scenes = list(spec.scenes)
    scenes[1] = scenes[1].model_copy(
        update={"text_frames": tuple(100 + 2 * i for i in range(len(scenes[1].text.split())))}
    )
    timed = spec.model_copy(
        update={
            "scenes": tuple(scenes),
            "beats": (Beat(kind=BeatKind.HOOK, frame=0, frames=8, scene=0),),
        }
    )

    selects = [cue.t for cue in plan_soundtrack(timed).cues if cue.kind is CueKind.SELECT]

    assert pytest.approx(100 / 30) in selects
    assert 0.0 not in selects
    assert len(selects) == sum(1 for scene in timed.scenes[1:] if scene.text_frames)


def test_effects_follow_the_transition_style_in_a_spec_without_beats() -> None:
    spec = make_spec().model_copy(update={"beats": ()})
    plan = plan_soundtrack(spec)

    by_time: dict[float, set[CueKind]] = {}
    for cue in plan.cues:
        by_time.setdefault(cue.t, set()).add(cue.kind)
    for scene in spec.scenes[1:-1]:
        start = scene.start_frame / spec.fps
        expected = {
            Transition.SCALE: {CueKind.WHOOSH, CueKind.IMPACT},
            Transition.PUSH: {CueKind.WHOOSH},
            Transition.FADE: {CueKind.SHIMMER},
            Transition.CUT: {CueKind.IMPACT},
        }[scene.transition_in]
        assert expected <= by_time[start]
    cta_s = 12.0
    at_cta = next(kinds for t, kinds in by_time.items() if t == pytest.approx(cta_s))
    assert {CueKind.IMPACT, CueKind.SHIMMER} <= at_cta


def test_cues_are_sorted_and_inside_the_video() -> None:
    plan = plan_soundtrack(make_spec())

    times = [cue.t for cue in plan.cues]
    assert times == sorted(times)
    assert times[0] >= 0 and times[-1] < plan.duration_s


def test_a_single_scene_video_still_has_a_plan() -> None:
    spec = make_spec()
    only = spec.scenes[0].model_copy(update={"end_frame": spec.duration_frames})
    short = spec.model_copy(update={"scenes": (only,)})

    plan = plan_soundtrack(short)

    assert plan.drop_s == 0.0
    assert plan.lines and plan.cues
    assert isinstance(only, SceneSpec)


def test_motion_soundtrack_uses_the_sixty_fps_end_card() -> None:
    concept = make_concept("A")
    layers = (
        MotionLayer(id="a", kind=LayerKind.PANEL, bbox_norm=(0.1, 0.2, 0.5, 0.4), confidence=0.9),
        MotionLayer(
            id="b", kind=LayerKind.BUTTON, bbox_norm=(0.2, 0.7, 0.3, 0.08), confidence=0.88
        ),
    )
    extracted = {
        scene.screenshot: ExtractedLayers(screenshot=scene.screenshot, layers=layers)
        for scene in concept.scenes
    }
    brief = make_brief()
    spec = compose_motion(concept, compose(brief, concept, ()).theme, extracted, brief)
    assert spec is not None
    plan = plan_motion_soundtrack(spec)
    assert plan.outro_s == 12.0
    assert any(cue.t == pytest.approx(12.0) for cue in plan.cues)
