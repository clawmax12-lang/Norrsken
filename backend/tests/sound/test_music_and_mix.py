import numpy as np
import pytest

from preflight.contracts import CueKind, SoundCue
from preflight.sound import dsp
from preflight.sound.mix import SpokenClip, duck_curve, mix, render_effects
from preflight.sound.music import render_music
from preflight.sound.plan import SoundPlan

PLAN = SoundPlan(duration_s=15.0, drop_s=3.0, outro_s=13.0, lines=(), cues=())


def rms(signal: np.ndarray, start_s: float, end_s: float) -> float:
    part = signal[dsp.seconds(start_s) : dsp.seconds(end_s)]
    return float(np.sqrt(np.mean(part**2)))


def test_music_is_exactly_as_long_as_the_video_and_ends_silent() -> None:
    music = render_music(PLAN)

    assert music.shape == (dsp.seconds(15.0), 2)
    assert np.all(np.isfinite(music))
    assert abs(music[-1]).max() == 0.0


def test_the_drop_brings_the_drums_in_and_the_outro_takes_them_out() -> None:
    music = render_music(PLAN)[:, 0]

    assert rms(music, 4.0, 8.0) > 2 * rms(music, 0.5, 2.5)  # intro is pad only
    assert rms(music, 4.0, 8.0) > 2 * rms(music, 13.6, 14.8)  # outro is pad only


def test_music_is_deterministic() -> None:
    assert np.array_equal(render_music(PLAN), render_music(PLAN))


def test_music_ducks_under_speech_and_recovers() -> None:
    clip = SpokenClip(2.0, np.ones(dsp.seconds(1.0), dtype=np.float32) * 0.1)

    gain = duck_curve([clip], dsp.seconds(6.0))

    assert gain[dsp.seconds(1.0)] == pytest.approx(1.0, abs=0.01)
    assert gain[dsp.seconds(2.6)] < 0.4  # about -9 dB while speaking
    assert gain[dsp.seconds(5.5)] > 0.95  # released again


def test_an_effect_peaks_where_its_cue_says() -> None:
    effects = render_effects((SoundCue(kind=CueKind.WHOOSH, t=6.0),), 15.0)

    window = dsp.SAMPLE_RATE // 25
    loudness = np.convolve(np.abs(effects[:, 0]), np.ones(window) / window, mode="same")
    assert np.argmax(loudness) / dsp.SAMPLE_RATE == pytest.approx(6.0, abs=0.08)


def test_a_cue_that_starts_before_zero_is_cut_rather_than_rejected() -> None:
    effects = render_effects((SoundCue(kind=CueKind.WHOOSH, t=0.1),), 2.0)

    assert effects.shape == (dsp.seconds(2.0), 2)
    assert np.max(np.abs(effects)) > 0


def test_the_mix_leaves_headroom_and_keeps_speech_audible() -> None:
    music = render_music(PLAN)
    effects = render_effects((SoundCue(kind=CueKind.IMPACT, t=3.0),), 15.0)
    voice = SpokenClip(1.0, (0.2 * np.sin(np.arange(dsp.seconds(1.5)) / 20)).astype(np.float32))

    mixed = mix(music, effects, [voice])

    assert mixed.shape == music.shape
    assert np.max(np.abs(mixed)) <= 0.7 + 1e-6
    assert rms(mixed[:, 0], 1.2, 2.2) > 0.05
