import pytest

from preflight.contracts import BeatKind, BriefField, Scene
from preflight.generation.beats import (
    COUNT_FRAMES,
    TEXT_DELAY,
    WORD_STAGGER,
    heard_frames,
    keyword_index,
    ordered,
    scene_beats,
    scene_clock,
)

FPS = 30


def scene(**overrides: object) -> Scene:
    data: dict[str, object] = {
        "t_start": 3,
        "t_end": 6,
        "screenshot": "uploads/1.png",
        "text": "Save 3 hours weekly",
        "source_field": BriefField.ONE_LINER,
        "voice": "You save three hours every week",
        "voice_s": 2.0,
        "voice_words": (0.0, 0.3, 0.6, 1.0, 1.4, 1.7),
        "focus": (0.1, 0.2, 0.4, 0.2),
    }
    return Scene(**{**data, **overrides})  # type: ignore[arg-type]


def test_words_are_heard_where_the_studio_plays_them() -> None:
    assert heard_frames(scene(), 90, 180, FPS) == (99, 108, 117, 129, 141, 150)


def test_an_overrunning_line_is_heard_faster_like_the_studio_speeds_it_up() -> None:
    window = 6 - 0.12 - 3.3
    fast = scene(voice_s=window * 3)

    heard = heard_frames(fast, 90, 180, FPS)

    assert heard[-1] == round((3.3 + 1.7 / 1.5) * FPS)


def test_the_headline_appears_with_the_voice_and_the_number_lands_when_spoken() -> None:
    clock = scene_clock(scene(), 90, 180, FPS, timed=True)

    assert clock.voice_start == 99
    assert clock.keyword == 117  # "three"
    assert clock.keyword_is_number
    assert clock.text_frames == (99, 117, 99 + 2 * WORD_STAGGER, 99 + 3 * WORD_STAGGER)


def test_the_emphasis_word_lands_when_no_number_is_in_the_headline() -> None:
    worded = scene(
        text="Notes sort themselves",
        emphasis="themselves",
        voice="Your notes sort themselves",
        voice_words=(0.0, 0.3, 0.7, 1.0),
    )

    clock = scene_clock(worded, 90, 180, FPS, timed=True)

    assert keyword_index(worded) == 2
    assert clock.keyword == 129
    assert not clock.keyword_is_number


def test_the_hook_is_readable_on_its_first_frame() -> None:
    clock = scene_clock(scene(t_start=0, t_end=3), 0, 90, FPS, timed=True, instant=True)

    assert clock.text_frames == (0, 0, 0, 0)
    assert not clock.keyword_is_number


def test_a_scene_without_a_measured_voice_shows_its_text_after_a_short_delay() -> None:
    quiet = scene(voice=None, voice_s=None, voice_words=())

    clock = scene_clock(quiet, 90, 180, FPS, timed=True)

    assert clock.text_frames[0] == 90 + TEXT_DELAY
    assert clock.keyword is None


def test_the_end_card_has_no_headline_frames() -> None:
    assert scene_clock(scene(), 360, 450, FPS, timed=False).text_frames == ()


def test_a_body_scene_moves_counts_then_taps_and_punches_into_its_focus() -> None:
    body = scene()
    clock = scene_clock(body, 90, 180, FPS, timed=True)

    beats = scene_beats(1, clock, body, last=False)

    assert [b.kind for b in beats] == [BeatKind.MOVE, BeatKind.COUNT, BeatKind.TAP, BeatKind.PUNCH]
    assert beats[1].frames == COUNT_FRAMES
    tap = beats[2]
    assert tap.frame == 127
    assert tap.point == pytest.approx((0.3, 0.3))
    assert beats[3].frame == tap.frame + 4


def test_the_first_scene_opens_on_a_hook_and_the_last_on_the_cta() -> None:
    clock = scene_clock(scene(), 0, 90, FPS, timed=True, instant=True)
    hook = scene_beats(0, clock, scene(focus=None), last=False)
    cta = scene_beats(4, scene_clock(scene(), 360, 450, FPS, timed=False), scene(), last=True)

    assert [(b.kind, b.frame) for b in hook] == [(BeatKind.HOOK, 0), (BeatKind.WORD, 27)]
    assert [(b.kind, b.frame) for b in cta] == [(BeatKind.CTA, 360), (BeatKind.TAP, 396)]


def test_beats_are_ordered_by_frame() -> None:
    clock = scene_clock(scene(), 90, 180, FPS, timed=True)
    beats = scene_beats(1, clock, scene(), last=False)

    assert [b.frame for b in ordered(reversed(beats))] == sorted(b.frame for b in beats)


def test_a_long_scene_pulls_the_camera_back_out_in_its_quiet_stretch() -> None:
    long = scene(t_end=7)
    clock = scene_clock(long, 90, 210, FPS, timed=True)

    beats = scene_beats(1, clock, long, last=False)

    punches = [b for b in beats if b.kind is BeatKind.PUNCH]
    assert len(punches) == 2
    assert punches[1].frame == 141 + (210 - 141) // 2 - 7
    assert punches[1].frame + punches[1].frames < 210
