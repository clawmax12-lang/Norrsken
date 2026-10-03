"""A synthesized 120 BPM backing track shaped by the video's structure.

Intro (pad and a riser into the drop) -> main (kick, bass, hats, arpeggio, pad pumping with
the kick) -> outro (pad only, resolving on the last chord). Chords cycle F - Am - C - G, one
per bar. Drums and bass play only between ``drop_s`` and ``outro_s``.
"""

import numpy as np
from numpy.typing import NDArray

from . import dsp
from .plan import BAR_S, BEAT_S, SoundPlan

# Hz of each chord's voicing, and its bass root: F, Am, C, G.
_CHORDS = (
    (174.61, 220.00, 261.63, 329.63),
    (220.00, 261.63, 329.63, 392.00),
    (196.00, 261.63, 329.63, 392.00),
    (196.00, 246.94, 293.66, 392.00),
)
_BASS_ROOTS = (87.31, 110.00, 130.81, 98.00)
_BASS_BEATS = (0.0, 1.5, 2.5)  # offsets in beats within a bar
_PAD_DETUNE = 0.0009
_PAD_OVERLAP_S = 0.45
_PUMP_DEPTH = 0.4
_PUMP_TAU_S = 0.14
_FINAL_FADE_S = 0.06
_RISER_S = 2.0

Stereo = NDArray[np.float32]


def render_music(plan: SoundPlan) -> Stereo:
    """Return the track as ``(samples, 2)`` float32, exactly ``plan.duration_s`` long."""
    length = dsp.seconds(plan.duration_s)
    pad_left, pad_right = np.zeros(length), np.zeros(length)
    centre = np.zeros(length)
    _lay_pad(pad_left, pad_right, plan)
    beats = _main_beats(plan)
    pad_gain = 1.0 - _PUMP_DEPTH * _kick_envelope(length, beats)
    _lay_drums_and_bass(centre, plan, beats)
    _lay_arpeggio(centre, beats)
    riser_s = min(_RISER_S, plan.drop_s)
    if riser_s > 0:
        _place(centre, dsp.riser(riser_s), plan.drop_s - riser_s, 0.35)
    stereo = np.stack(
        [pad_left * pad_gain * 0.5 + centre, pad_right * pad_gain * 0.5 + centre], axis=1
    )
    stereo[-dsp.seconds(_FINAL_FADE_S) :] *= np.linspace(1.0, 0.0, dsp.seconds(_FINAL_FADE_S))[
        :, None
    ]
    return stereo.astype(np.float32)


def _bar_chord(bar: int) -> int:
    return bar % len(_CHORDS)


def _lay_pad(left: NDArray[np.float64], right: NDArray[np.float64], plan: SoundPlan) -> None:
    bars = int(np.ceil(plan.duration_s / BAR_S))
    for bar in range(bars):
        chord = _CHORDS[_bar_chord(bar)]
        length = BAR_S + _PAD_OVERLAP_S
        _place(left, dsp.pad(chord, length, -_PAD_DETUNE), bar * BAR_S, 1.0)
        _place(right, dsp.pad(chord, length, _PAD_DETUNE), bar * BAR_S, 1.0)


def _main_beats(plan: SoundPlan) -> list[float]:
    """Start times of every beat that has drums, from the drop up to the outro."""
    count = round((plan.outro_s - plan.drop_s) / BEAT_S)
    return [plan.drop_s + i * BEAT_S for i in range(max(count, 0))]


def _kick_envelope(length: int, beats: list[float]) -> NDArray[np.float64]:
    """1 right after each kick, relaxing to 0: the pad is lowered by this much (side-chain)."""
    envelope = np.zeros(length)
    t = np.arange(length) / dsp.SAMPLE_RATE
    for beat in beats:
        since = t - beat
        envelope = np.maximum(envelope, np.where(since >= 0, np.exp(-since / _PUMP_TAU_S), 0.0))
    return envelope


def _lay_drums_and_bass(centre: NDArray[np.float64], plan: SoundPlan, beats: list[float]) -> None:
    kick, hat = dsp.kick(), dsp.hat()
    for index, beat in enumerate(beats):
        _place(centre, kick, beat, 0.85 if index == 0 else 0.7)
        _place(centre, hat, beat + BEAT_S / 2, 0.16)
    first_bar = int(plan.drop_s / BAR_S)
    for bar in range(first_bar, int(np.ceil(plan.outro_s / BAR_S))):
        root = _BASS_ROOTS[_bar_chord(bar)]
        for offset in _BASS_BEATS:
            start = bar * BAR_S + offset * BEAT_S
            if plan.drop_s <= start < plan.outro_s:
                _place(centre, dsp.bass_note(root, 0.42), start, 0.5)


def _lay_arpeggio(centre: NDArray[np.float64], beats: list[float]) -> None:
    for index, beat in enumerate(beats):
        chord = _CHORDS[_bar_chord(int(beat / BAR_S))]
        for step in (0, 1):
            note = chord[(index * 2 + step * 2 + step) % len(chord)] * 2
            _place(centre, dsp.pluck(note), beat + step * BEAT_S / 2, 0.1)


def _place(
    buffer: NDArray[np.float64], sound: NDArray[np.float32], at_s: float, gain: float
) -> None:
    """Add ``sound * gain`` into ``buffer`` starting at ``at_s``; anything past the end is cut."""
    start = dsp.seconds(max(at_s, 0.0))
    if start >= len(buffer):
        return
    end = min(start + len(sound), len(buffer))
    buffer[start:end] += sound[: end - start] * gain
