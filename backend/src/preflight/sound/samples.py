"""Recorded interface and impact sounds: CC0 packs by Kenney (see ``samples/LICENSE-*``).

Each effect has a few takes, so a tap never sounds identical twice in a row. Files are mono
48 kHz WAV named ``{kind}_{n}.wav``; they are loaded once and peak-normalised.
"""

from functools import cache
from pathlib import Path

import numpy as np

from preflight.contracts import CueKind

from . import dsp
from .audio import pcm16_to_float, read_wav_mono_pcm

SAMPLE_KINDS = (
    CueKind.TAP,
    CueKind.POP,
    CueKind.SELECT,
    CueKind.CONFIRM,
    CueKind.TICK,
    CueKind.THUD,
)
_DIR = Path(__file__).parent / "samples"
_PEAK = 0.9
_ENVELOPE_S = 0.004


@cache
def takes(kind: CueKind) -> tuple[dsp.Signal, ...]:
    """Every take of ``kind``, in file order."""
    loaded = []
    for path in sorted(_DIR.glob(f"{kind.value}_*.wav")):
        pcm, rate = read_wav_mono_pcm(path)
        if rate != dsp.SAMPLE_RATE:
            raise ValueError(f"{path.name} is {rate} Hz, expected {dsp.SAMPLE_RATE}")
        samples = pcm16_to_float(pcm)
        peak = float(np.max(np.abs(samples), initial=0.0)) or 1.0
        loaded.append((samples * (_PEAK / peak)).astype(np.float32))
    if not loaded:
        raise FileNotFoundError(f"no samples for {kind.value} in {_DIR}")
    return tuple(loaded)


def peak_offset_s(sound: dsp.Signal) -> float:
    """Seconds from the start of ``sound`` to its loudest moment (a short smoothed envelope)."""
    window = max(1, dsp.seconds(_ENVELOPE_S))
    envelope = np.convolve(np.abs(sound), np.ones(window) / window, mode="same")
    return float(np.argmax(envelope)) / dsp.SAMPLE_RATE
