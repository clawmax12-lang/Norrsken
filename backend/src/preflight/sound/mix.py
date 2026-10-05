"""Combine narration, the ambience bed and effects into one stereo mix ready for mastering.

The bed ducks under speech (a smoothed side-chain, computed once at a coarse rate). Every
effect is placed so its loudest moment lands on its cue: recorded takes rotate so a sound
never repeats back to back, and whooshes and risers are synthesized to the length of the
motion they follow and panned with it. The sum is peak-limited to leave headroom; final
loudness is set afterwards by ffmpeg's loudnorm so it is measured, not guessed.
"""

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from preflight.contracts import CueKind, SoundCue

from . import dsp
from .samples import SAMPLE_KINDS, peak_offset_s, takes

Stereo = NDArray[np.float32]

_DUCK_DEPTH_DB = -7.0
_DUCK_ATTACK_S = 0.06
_DUCK_RELEASE_S = 0.35
_DUCK_RATE_HZ = 1000
_PEAK_CEILING = 0.7  # about -3 dBFS before mastering

_CUE_GAIN_DB = {
    CueKind.IMPACT: -7.0,
    CueKind.WHOOSH: -12.0,
    CueKind.SHIMMER: -17.0,
    CueKind.TICK: -22.0,
    CueKind.RISER: -15.0,
    CueKind.TAP: -11.0,
    CueKind.POP: -10.0,
    CueKind.SELECT: -20.0,
    CueKind.CONFIRM: -13.0,
    CueKind.THUD: -8.0,
}
_CUE_PAN = {
    CueKind.WHOOSH: 0.25,
    CueKind.SHIMMER: -0.2,
    CueKind.TICK: 0.15,
    CueKind.TAP: 0.1,
    CueKind.POP: -0.1,
    CueKind.SELECT: 0.0,
    CueKind.CONFIRM: 0.0,
}
_WHOOSH_S = 0.9
_WHOOSH_PEAK_FRACTION = 0.8  # the swell peaks at 80 % of the whoosh
_RISER_S = 1.0
# A short whoosh is a flick, not a sweep: it sits lower in the mix.
_SHORT_WHOOSH_S = 0.4
_SHORT_WHOOSH_DB = -5.0


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
    used: dict[CueKind, int] = {}
    for cue in cues:
        sound, peak_s, gain_db = _voice(cue, used)
        start = dsp.seconds(cue.t - peak_s)
        position = cue.pan if cue.pan is not None else _CUE_PAN.get(cue.kind, 0.0)
        left, right = _pan(position)
        _add(bus, sound * _db(gain_db), start, left, right)
    return bus.astype(np.float32)


def _voice(cue: SoundCue, used: dict[CueKind, int]) -> tuple[dsp.Signal, float, float]:
    """The sound for ``cue``, where its peak is (seconds in), and its level."""
    gain = _CUE_GAIN_DB[cue.kind]
    if cue.kind in SAMPLE_KINDS:
        options = takes(cue.kind)
        index = used.get(cue.kind, -1) + 1
        used[cue.kind] = index
        sound = options[index % len(options)]
        return sound, peak_offset_s(sound), gain
    synth = _SYNTHS[cue.kind]
    duration = cue.duration_s or _DEFAULT_S.get(cue.kind, 0.0)
    sound = synth(duration)
    if cue.kind is CueKind.WHOOSH:
        if duration <= _SHORT_WHOOSH_S:
            gain += _SHORT_WHOOSH_DB
        return sound, duration * _WHOOSH_PEAK_FRACTION, gain
    if cue.kind is CueKind.RISER:
        return sound, duration, gain
    return sound, 0.0, gain


_SYNTHS: dict[CueKind, Callable[[float], dsp.Signal]] = {
    CueKind.IMPACT: lambda _: dsp.impact(),
    CueKind.WHOOSH: dsp.whoosh,
    CueKind.SHIMMER: lambda _: dsp.shimmer(),
    CueKind.RISER: dsp.riser,
}
_DEFAULT_S = {CueKind.WHOOSH: _WHOOSH_S, CueKind.RISER: _RISER_S}


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
    """Gain (<= 1) per sample that lowers the bed while someone is speaking."""
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


def mix(bed: Stereo, effects: Stereo, speech: list[SpokenClip]) -> Stereo:
    """Sum the three buses (speech arrives already level-matched); peak is at most about -3 dBFS."""
    length = len(bed)
    ducked = bed * duck_curve(speech, length)[:, None]
    voice = np.zeros((length, 2))
    for clip in speech:
        _add(voice, clip.samples, dsp.seconds(clip.start_s), 1.0, 1.0)
    total = ducked + effects + voice
    peak = float(np.max(np.abs(total), initial=0.0))
    return (total * (_PEAK_CEILING / peak) if peak > _PEAK_CEILING else total).astype(np.float32)
