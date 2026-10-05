import numpy as np
import pytest

from preflight.contracts import CueKind, SoundCue
from preflight.sound import dsp
from preflight.sound.ambience import render_ambience
from preflight.sound.mix import SpokenClip, duck_curve, mix, render_effects
from preflight.sound.plan import SoundPlan
from preflight.sound.samples import SAMPLE_KINDS, takes

PLAN = SoundPlan(duration_s=15.0, drop_s=3.0, outro_s=12.0, lines=(), cues=())


def rms(signal: np.ndarray, start_s: float, end_s: float) -> float:
    part = signal[dsp.seconds(start_s) : dsp.seconds(end_s)]
    return float(np.sqrt(np.mean(part**2)))


def peak_s(effects: np.ndarray, channel: int = 0) -> float:
    window = dsp.SAMPLE_RATE // 200
    loudness = np.convolve(np.abs(effects[:, channel]), np.ones(window) / window, mode="same")
    return float(np.argmax(loudness)) / dsp.SAMPLE_RATE


def test_the_ambience_is_exactly_as_long_as_the_video_and_fades_out() -> None:
    bed = render_ambience(PLAN)

    assert bed.shape == (dsp.seconds(15.0), 2)
    assert np.all(np.isfinite(bed))
    assert np.max(np.abs(bed[-10:])) < 1e-3


def test_the_ambience_opens_quietly_and_lifts_into_the_end_card() -> None:
    bed = render_ambience(PLAN)

    assert rms(bed, 0.0, 0.1) < 0.2 * rms(bed, 2.0, 4.0)
    assert rms(bed, 12.2, 14.4) > 1.2 * rms(bed, 5.0, 8.0)


def test_the_ambience_is_wide_and_has_no_beat() -> None:
    bed = render_ambience(PLAN)
    left, right = bed[dsp.seconds(1.0) :, 0], bed[dsp.seconds(1.0) :, 1]

    assert abs(np.corrcoef(left, right)[0, 1]) < 0.5
    # Without drums the level barely moves from one half second to the next.
    halves = [rms(bed[:, 0], 2.0 + i * 0.5, 2.5 + i * 0.5) for i in range(12)]
    assert max(halves) < 1.6 * min(halves)


def test_the_ambience_is_deterministic() -> None:
    assert np.array_equal(render_ambience(PLAN), render_ambience(PLAN))


def test_the_bed_ducks_under_speech_and_recovers() -> None:
    clip = SpokenClip(2.0, np.ones(dsp.seconds(1.0), dtype=np.float32) * 0.1)

    gain = duck_curve([clip], dsp.seconds(6.0))

    assert gain[dsp.seconds(1.0)] == pytest.approx(1.0, abs=0.01)
    assert gain[dsp.seconds(2.6)] < 0.5  # about -7 dB while speaking
    assert gain[dsp.seconds(5.5)] > 0.95  # released again


def test_every_recorded_effect_has_several_takes_at_the_mix_rate() -> None:
    for kind in SAMPLE_KINDS:
        sounds = takes(kind)
        assert len(sounds) >= 2
        assert all(0.005 < len(s) / dsp.SAMPLE_RATE < 1.0 for s in sounds)


@pytest.mark.parametrize("kind", [*SAMPLE_KINDS, CueKind.WHOOSH, CueKind.IMPACT])
def test_an_effect_peaks_where_its_cue_says(kind: CueKind) -> None:
    effects = render_effects((SoundCue(kind=kind, t=6.0),), 15.0)

    assert peak_s(effects) == pytest.approx(6.0, abs=0.02 if kind in SAMPLE_KINDS else 0.08)


def test_a_riser_builds_to_its_cue_and_stops() -> None:
    effects = render_effects((SoundCue(kind=CueKind.RISER, t=6.0, duration_s=0.9),), 15.0)

    assert rms(effects[:, 0], 5.7, 5.98) > 3 * rms(effects[:, 0], 5.1, 5.3)
    assert rms(effects[:, 0], 6.05, 6.5) < 1e-6


def test_a_whoosh_follows_its_length_and_side() -> None:
    effects = render_effects((SoundCue(kind=CueKind.WHOOSH, t=3.0, duration_s=0.4, pan=-1.0),), 6.0)

    assert rms(effects[:, 1], 2.0, 4.0) < 1e-6
    assert rms(effects[:, 0], 2.5, 3.1) > 0
    assert rms(effects[:, 0], 2.0, 2.6) < 1e-6


def test_repeated_taps_rotate_through_the_takes() -> None:
    first = render_effects((SoundCue(kind=CueKind.TAP, t=1.0),), 2.0)
    pair = render_effects(
        (SoundCue(kind=CueKind.TAP, t=0.5), SoundCue(kind=CueKind.TAP, t=1.0)), 2.0
    )

    assert not np.allclose(first[dsp.seconds(0.9) :], pair[dsp.seconds(0.9) :])


def test_a_cue_that_starts_before_zero_is_cut_rather_than_rejected() -> None:
    effects = render_effects((SoundCue(kind=CueKind.WHOOSH, t=0.1),), 2.0)

    assert effects.shape == (dsp.seconds(2.0), 2)
    assert np.max(np.abs(effects)) > 0


def test_the_mix_leaves_headroom_and_keeps_speech_audible() -> None:
    bed = render_ambience(PLAN)
    effects = render_effects((SoundCue(kind=CueKind.THUD, t=3.0),), 15.0)
    voice = SpokenClip(1.0, (0.2 * np.sin(np.arange(dsp.seconds(1.5)) / 20)).astype(np.float32))

    mixed = mix(bed, effects, [voice])

    assert mixed.shape == bed.shape
    assert np.max(np.abs(mixed)) <= 0.7 + 1e-6
    assert rms(mixed[:, 0], 1.2, 2.2) > 0.05
