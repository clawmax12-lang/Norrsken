import pytest

from preflight.contracts import CueKind, SceneSpec, Transition
from preflight.sound.plan import BEAT_S, plan_soundtrack
from tests.sound.helpers import make_spec


def test_every_cut_lands_on_a_beat() -> None:
    spec = make_spec()
    for scene in spec.scenes:
        start = scene.start_frame / spec.fps
        assert start / BEAT_S == pytest.approx(round(start / BEAT_S))


def test_music_structure_follows_the_scenes_and_the_end_card() -> None:
    plan = plan_soundtrack(make_spec())

    assert plan.duration_s == 15.0
    assert plan.drop_s == 3.0  # the first scene change
    assert plan.outro_s == 13.0  # the end card takes the last 1.8 s (60 % of 3 s), then a beat down


def test_narration_reads_each_distinct_on_screen_text_then_the_cta() -> None:
    plan = plan_soundtrack(make_spec())

    texts = [line.text for line in plan.lines]
    assert texts == [
        "Notes that organise themselves",
        "Acme Notes",
    ]  # repeated scene text read once
    assert plan.lines[0].start_s == pytest.approx(0.3)
    assert plan.lines[1].start_s > plan.outro_s - BEAT_S


def test_lines_never_overlap_and_end_before_the_video_does() -> None:
    plan = plan_soundtrack(make_spec())

    ends = [line.start_s + line.window_s for line in plan.lines]
    assert all(later.start_s > end for end, later in zip(ends, plan.lines[1:], strict=False))
    assert ends[-1] <= plan.duration_s


def test_every_line_keeps_its_source_field() -> None:
    spec = make_spec()
    plan = plan_soundtrack(spec)

    assert plan.lines[0].source_field == spec.scenes[0].source_field
    assert plan.lines[-1].source_field == spec.cta_source_field


def test_cta_is_not_repeated_when_the_last_scene_already_says_it() -> None:
    spec = make_spec(cta="Notes that organise themselves")

    assert [line.text for line in plan_soundtrack(spec).lines] == ["Notes that organise themselves"]


def test_effects_follow_the_transition_style() -> None:
    spec = make_spec()
    plan = plan_soundtrack(spec)

    by_time: dict[float, set[CueKind]] = {}
    for cue in plan.cues:
        by_time.setdefault(cue.t, set()).add(cue.kind)
    for scene in spec.scenes[1:]:
        start = scene.start_frame / spec.fps
        expected = {
            Transition.SCALE: {CueKind.WHOOSH, CueKind.IMPACT},
            Transition.PUSH: {CueKind.WHOOSH},
            Transition.FADE: {CueKind.SHIMMER},
            Transition.CUT: {CueKind.IMPACT},
        }[scene.transition_in]
        assert expected <= by_time[start]
    cta_s = 13.2  # the end card starts 1.8 s before the end
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
