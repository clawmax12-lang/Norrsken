import numpy as np
import pytest

from preflight.sound.alignment import syllables, voiced_segments, word_starts

RATE = 24_000


def bursts(*spans: tuple[float, float], length_s: float = 1.6) -> np.ndarray:
    """A clip that sounds only during each ``(start, end)`` span."""
    samples = np.zeros(int(length_s * RATE), dtype=np.float32)
    t = np.arange(len(samples)) / RATE
    for start, end in spans:
        inside = (t >= start) & (t < end)
        samples[inside] = 0.5 * np.sin(2 * np.pi * 220 * t[inside])
    return samples


def test_each_word_starts_on_the_burst_of_sound_it_belongs_to() -> None:
    clip = bursts((0.2, 0.5), (0.6, 0.9), (1.0, 1.3))

    assert word_starts("cat dog sun", clip, RATE) == pytest.approx((0.2, 0.6, 1.0), abs=0.011)


def test_a_dip_shorter_than_a_syllable_gap_does_not_split_a_word() -> None:
    clip = bursts((0.2, 0.5), (0.52, 0.8))

    segments = voiced_segments(clip, RATE)

    assert len(segments) == 1
    assert segments[0][0] == pytest.approx(0.2, abs=0.011)


def test_longer_words_take_more_of_the_line() -> None:
    clip = bursts((0.0, 1.5))

    starts = word_starts("go extraordinarily now", clip, RATE)

    assert starts[0] == 0.0
    assert starts[2] - starts[1] > 3 * (starts[1] - starts[0])


def test_starts_never_go_back_in_time() -> None:
    clip = bursts((0.1, 0.3), (0.35, 0.4), (0.9, 1.4))

    starts = word_starts("a b c d e f g", clip, RATE)

    assert list(starts) == sorted(starts)


def test_a_silent_clip_spreads_the_words_evenly() -> None:
    assert word_starts("one two", np.zeros(RATE, dtype=np.float32), RATE) == (0.0, 0.5)
    assert word_starts("", np.zeros(RATE, dtype=np.float32), RATE) == ()


def test_numbers_count_as_the_words_they_are_spoken_as() -> None:
    assert syllables("tyst") == 1
    assert syllables("banana") == 3
    assert syllables("40%") == 4
