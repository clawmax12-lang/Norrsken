"""A living background without music: soft air that drifts across the stereo field.

Two decorrelated bands of pink noise (one per side) breathe slowly out of phase, under a faint
low room tone. The bed opens over the first half second and lifts into the end card. It never
carries a melody or a beat; the effects mark the moments and the voice carries the message.
"""

import numpy as np
from numpy.typing import NDArray

from . import dsp
from .plan import SoundPlan

Stereo = NDArray[np.float32]

_AIR_BAND_HZ = (140.0, 7000.0)
_AIR_RMS = 10 ** (-30 / 20)
_ROOM_HZ = 52.0
_ROOM_LEVEL = 10 ** (-34 / 20)
_BREATH_HZ = 0.11
_BREATH_DEPTH = 0.3
_OPEN_S = 0.5
_LIFT = 1.45
_LIFT_S = 0.8
_FADE_OUT_S = 0.35


def render_ambience(plan: SoundPlan) -> Stereo:
    """Return the bed as ``(samples, 2)`` float32, exactly ``plan.duration_s`` long."""
    length = dsp.seconds(plan.duration_s)
    t = np.arange(length) / dsp.SAMPLE_RATE
    breath = 2.0 * np.pi * _BREATH_HZ * t
    left = air("ambience-left", length) * (1.0 - _BREATH_DEPTH * (0.5 + 0.5 * np.sin(breath)))
    right = air("ambience-right", length) * (1.0 - _BREATH_DEPTH * (0.5 - 0.5 * np.sin(breath)))
    room = _ROOM_LEVEL * np.sin(2.0 * np.pi * _ROOM_HZ * t) * (0.7 + 0.3 * np.sin(breath * 0.6))
    shape = _shape(t, plan)
    stereo = np.stack([(left + room) * shape, (right + room) * shape], axis=1)
    return stereo.astype(np.float32)


def air(name: str, length: int) -> NDArray[np.float64]:
    """Band-limited pink noise at the bed's level, identical for a given ``name``."""
    if length == 0:
        return np.zeros(0)
    spectrum = np.fft.rfft(dsp.noise(name, length))
    frequencies = np.fft.rfftfreq(length, 1.0 / dsp.SAMPLE_RATE)
    low, high = _AIR_BAND_HZ
    pink = 1.0 / np.sqrt(np.maximum(frequencies, low))
    band = (
        1.0 / (1.0 + (low / np.maximum(frequencies, 1e-9)) ** 4) / (1.0 + (frequencies / high) ** 4)
    )
    shaped = np.fft.irfft(spectrum * pink * band, n=length)
    rms = float(np.sqrt(np.mean(np.square(shaped)))) or 1.0
    return shaped * (_AIR_RMS / rms)


def _shape(t: NDArray[np.float64], plan: SoundPlan) -> NDArray[np.float64]:
    """Open over the first half second, lift into the end card, fade out at the very end."""
    opening = np.clip(t / _OPEN_S, 0.0, 1.0) ** 2
    lift = 1.0 + (_LIFT - 1.0) * np.clip((t - (plan.outro_s - _LIFT_S)) / _LIFT_S, 0.0, 1.0)
    closing = np.clip((plan.duration_s - t) / _FADE_OUT_S, 0.0, 1.0)
    return opening * lift * closing
