"""When each word of a spoken line starts, measured on the clip itself.

Gemini text-to-speech returns audio without timestamps. Speech dips between many words and
pauses clearly at commas, so the words are spread over the line's voiced time in proportion to
their syllables, and each start then snaps to the nearest onset of sound within reach.
"""

import re

import numpy as np
from numpy.typing import NDArray

_FRAME_S = 0.01
_SILENCE_DB = -30.0  # relative to the loudest frame
_MIN_GAP_S = 0.04
_SNAP_S = 0.1
_VOWELS = re.compile(r"[aeiouyåäöæøéèüáà]+", re.IGNORECASE)
_DIGITS = re.compile(r"\d")


def word_starts(text: str, samples: NDArray[np.float32], sample_rate: int) -> tuple[float, ...]:
    """Seconds from the clip's first sample to the start of each word of ``text``."""
    words = text.split()
    if not words:
        return ()
    length_s = len(samples) / sample_rate
    segments = voiced_segments(samples, sample_rate)
    if not segments:
        return tuple(round(length_s * i / len(words), 3) for i in range(len(words)))
    weights = [syllables(word) for word in words]
    total = sum(weights)
    voiced_s = sum(end - start for start, end in segments)
    onsets = [start for start, _ in segments]
    starts: list[float] = []
    before = 0.0
    for weight in weights:
        guess = _along(segments, voiced_s * before / total)
        starts.append(_snap(guess, onsets, starts[-1] if starts else 0.0))
        before += weight
    starts[0] = onsets[0]
    return tuple(round(t, 3) for t in starts)


def voiced_segments(samples: NDArray[np.float32], sample_rate: int) -> list[tuple[float, float]]:
    """``(start, end)`` seconds of each run of sound, merging dips shorter than a syllable gap."""
    hop = max(int(_FRAME_S * sample_rate), 1)
    count = len(samples) // hop
    if count == 0:
        return []
    frames = samples[: count * hop].astype(np.float64).reshape(count, hop)
    rms = np.sqrt(np.mean(np.square(frames), axis=1))
    peak = float(np.max(rms))
    if peak <= 0.0:
        return []
    loud = 20 * np.log10(np.maximum(rms, 1e-12) / peak) > _SILENCE_DB
    segments: list[tuple[float, float]] = []
    index = 0
    while index < count:
        if not loud[index]:
            index += 1
            continue
        end = index
        while end < count and loud[end]:
            end += 1
        start_s, end_s = index * _FRAME_S, end * _FRAME_S
        if segments and start_s - segments[-1][1] < _MIN_GAP_S:
            segments[-1] = (segments[-1][0], end_s)
        else:
            segments.append((start_s, end_s))
        index = end
    return segments


def syllables(word: str) -> int:
    """Rough syllable count: vowel groups, and two per digit (numbers are spoken as words)."""
    return max(1, len(_VOWELS.findall(word)) + 2 * len(_DIGITS.findall(word)))


def _along(segments: list[tuple[float, float]], voiced_s: float) -> float:
    """Clip time at which ``voiced_s`` seconds of sound have passed."""
    for start, end in segments:
        if voiced_s <= end - start:
            return start + voiced_s
        voiced_s -= end - start
    return segments[-1][1]


def _snap(guess: float, onsets: list[float], floor: float) -> float:
    """The onset nearest ``guess`` within reach, never earlier than the previous word."""
    near = [t for t in onsets if abs(t - guess) <= _SNAP_S and t >= floor]
    best = min(near, key=lambda t: abs(t - guess)) if near else guess
    return max(best, floor)
