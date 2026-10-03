import numpy as np
import pytest

from preflight.sound import dsp


@pytest.mark.parametrize(
    "make",
    [
        dsp.kick,
        dsp.hat,
        dsp.impact,
        dsp.tick,
        dsp.shimmer,
        lambda: dsp.whoosh(0.9),
        lambda: dsp.riser(2.0),
    ],
)
def test_effects_are_finite_audible_and_never_clip(make) -> None:
    sound = make()

    assert sound.dtype == np.float32
    assert np.all(np.isfinite(sound))
    assert 0.2 < np.max(np.abs(sound)) <= 1.0


def test_synthesis_is_deterministic() -> None:
    assert np.array_equal(dsp.whoosh(0.9), dsp.whoosh(0.9))
    assert not np.array_equal(dsp.noise("a", 100), dsp.noise("b", 100))


def test_durations_match_the_request() -> None:
    assert len(dsp.whoosh(0.9)) == dsp.seconds(0.9)
    assert len(dsp.pad((220.0, 330.0), 2.4, 0.001)) == dsp.seconds(2.4)
    assert len(dsp.bass_note(87.3, 0.4)) == dsp.seconds(0.4)


def test_a_rising_whoosh_moves_energy_upward_in_frequency() -> None:
    sound = dsp.whoosh(1.0, rising=True).astype(np.float64)
    half = len(sound) // 2

    def centroid(part: np.ndarray) -> float:
        spectrum = np.abs(np.fft.rfft(part))
        freqs = np.fft.rfftfreq(len(part), 1 / dsp.SAMPLE_RATE)
        return float(np.sum(freqs * spectrum) / np.sum(spectrum))

    assert centroid(sound[half : half + 9600]) > centroid(sound[:9600])


def test_the_whoosh_is_loudest_at_eighty_percent() -> None:
    sound = np.abs(dsp.whoosh(1.0))
    window = dsp.SAMPLE_RATE // 50
    loudness = np.convolve(sound, np.ones(window) / window, mode="same")

    assert np.argmax(loudness) / len(sound) == pytest.approx(0.8, abs=0.05)


def test_fade_ramps_both_ends_without_touching_the_middle() -> None:
    faded = dsp.fade(np.ones(dsp.SAMPLE_RATE), 0.1, 0.1)

    assert faded[0] == 0.0 and faded[-1] == 0.0 and faded[dsp.SAMPLE_RATE // 2] == 1.0


def test_low_pass_removes_high_frequencies() -> None:
    t = np.arange(dsp.SAMPLE_RATE) / dsp.SAMPLE_RATE
    mixed = np.sin(2 * np.pi * 100 * t) + np.sin(2 * np.pi * 10_000 * t)

    filtered = dsp.low_pass(mixed, 500.0)
    spectrum = np.abs(np.fft.rfft(filtered))

    assert spectrum[100] > 10 * spectrum[10_000]  # a one-pole filter is gentle: ~6 dB/octave
