"""Combine narration, music and effects into one stereo bed ready for mastering.

Music ducks under speech (a smoothed side-chain, computed once at a coarse rate), effects sit
slightly left or right of centre, and the sum is peak-limited to leave headroom; final
loudness is set afterwards by ffmpeg's loudnorm so it is measured, not guessed.
"""

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from preflight.contracts import CueKind, SoundCue

from . import dsp

Stereo = NDArray[np.float32]

_MUSIC_GAIN_DB = -4.0
_DUCK_DEPTH_DB = -9.0
_DUCK_ATTACK_S = 0.06
_DUCK_RELEASE_S = 0.35
_DUCK_RATE_HZ = 1000
_PEAK_CEILING = 0.7  # about -3 dBFS before mastering

_CUE_GAIN_DB = {
    CueKind.IMPACT: -6.0,
    CueKind.WHOOSH: -11.0,
    CueKind.SHIMMER: -14.0,
    CueKind.TICK: -26.0,
}
_CUE_PAN = {CueKind.WHOOSH: 0.25, CueKind.SHIMMER: -0.2, CueKind.TICK: 0.15, CueKind.IMPACT: 0.0}
_WHOOSH_S = 0.9
_WHOOSH_PEAK_FRACTION = 0.8  # the swell peaks at 80 % of the whoosh


@dataclass(frozen=True)
class SpokenClip:
    """Narration audio (mono, at the mix rate) and when it starts."""

    start_s: float
    samples: NDArray[np.float32]


def _db(decibels: float) -> float:
    return 10 ** (decibels / 20)


def render_effects(cues: tuple[SoundCue, ...], duration_s: float) -> Stereo:
    """Place every cue so its loudest moment lands on ``cue.t``."""
    length = dsp.seconds(duration_s)
    bus = np.zeros((length, 2))
    sounds = {
        CueKind.IMPACT: dsp.impact(),
        CueKind.WHOOSH: dsp.whoosh(_WHOOSH_S),
        CueKind.SHIMMER: dsp.shimmer(),
        CueKind.TICK: dsp.tick(),
    }
    for cue in cues:
        sound = sounds[cue.kind]
        peak_offset = _WHOOSH_S * _WHOOSH_PEAK_FRACTION if cue.kind is CueKind.WHOOSH else 0.0
        start = dsp.seconds(cue.t - peak_offset)
        left, right = _pan(_CUE_PAN[cue.kind])
        _add(bus, sound * _db(_CUE_GAIN_DB[cue.kind]), start, left, right)
    return bus.astype(np.float32)


def _pan(position: float) -> tuple[float, float]:
    """Equal-power pan; -1 is hard left, +1 hard right."""
    angle = (position + 1.0) * np.pi / 4.0
    return float(np.cos(angle) * np.sqrt(2)), float(np.sin(angle) * np.sqrt(2))


def _add(
    bus: NDArray[np.float64], sound: NDArray[np.float32], start: int, left: float, right: float
) -> None:
    """Add ``sound`` at sample ``start`` (it may begin before 0 or run past the end)."""
    lo, hi = max(start, 0), min(start + len(sound), len(bus))
    if hi <= lo:
        return
    piece = sound[lo - start : hi - start]
    bus[lo:hi, 0] += piece * left
    bus[lo:hi, 1] += piece * right


def duck_curve(clips: list[SpokenClip], length: int) -> NDArray[np.float64]:
    """Gain (<= 1) per sample that lowers the music while someone is speaking."""
    steps = max(length * _DUCK_RATE_HZ // dsp.SAMPLE_RATE, 1)
    speaking = np.zeros(steps)
    for clip in clips:
        first = int(clip.start_s * _DUCK_RATE_HZ)
        speaking[first : first + int(len(clip.samples) / dsp.SAMPLE_RATE * _DUCK_RATE_HZ) + 1] = 1.0
    attack = 1.0 - np.exp(-1.0 / (_DUCK_ATTACK_S * _DUCK_RATE_HZ))
    release = 1.0 - np.exp(-1.0 / (_DUCK_RELEASE_S * _DUCK_RATE_HZ))
    level = np.zeros(steps)
    previous = 0.0
    for index, target in enumerate(speaking):
        previous += (attack if target > previous else release) * (target - previous)
        level[index] = previous
    gain = 1.0 - level * (1.0 - _db(_DUCK_DEPTH_DB))
    return np.interp(np.arange(length) / dsp.SAMPLE_RATE * _DUCK_RATE_HZ, np.arange(steps), gain)


def mix(music: Stereo, effects: Stereo, speech: list[SpokenClip]) -> Stereo:
    """Sum the three buses (speech arrives already level-matched); peak is at most about -3 dBFS."""
    length = len(music)
    bed = music * _db(_MUSIC_GAIN_DB) * duck_curve(speech, length)[:, None]
    voice = np.zeros((length, 2))
    for clip in speech:
        _add(voice, clip.samples, dsp.seconds(clip.start_s), 1.0, 1.0)
    total = bed + effects + voice
    peak = float(np.max(np.abs(total), initial=0.0))
    return (total * (_PEAK_CEILING / peak) if peak > _PEAK_CEILING else total).astype(np.float32)
