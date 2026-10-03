"""Sound synthesis primitives: every effect and instrument is generated, nothing is sampled.

All functions return mono ``float32`` at :data:`SAMPLE_RATE` and are deterministic: noise
comes from a generator seeded by the sound's name, never from global random state.
"""

import hashlib

import numpy as np
from numpy.typing import NDArray

SAMPLE_RATE = 48_000
Signal = NDArray[np.float32]

_STFT_FRAME = 2048
_STFT_HOP = 512
_HANN_OVERLAP_GAIN = 1.5  # sum of a Hann window overlapped at hop = frame / 4


def seconds(duration_s: float) -> int:
    """Samples in ``duration_s``."""
    return round(duration_s * SAMPLE_RATE)


def _time(samples: int) -> NDArray[np.float64]:
    return np.arange(samples) / SAMPLE_RATE


def noise(name: str, samples: int) -> NDArray[np.float64]:
    """White noise in [-1, 1], identical for a given ``name`` and length."""
    seed = int.from_bytes(hashlib.sha256(name.encode()).digest()[:8], "big")
    return np.random.default_rng(seed).uniform(-1.0, 1.0, samples)


def decay(samples: int, tau_s: float) -> NDArray[np.float64]:
    """Exponential decay from 1 with time constant ``tau_s``."""
    return np.exp(-_time(samples) / tau_s)


def fade(signal: NDArray[np.float64], in_s: float = 0.0, out_s: float = 0.0) -> NDArray[np.float64]:
    """Linear fade-in and fade-out over the first and last seconds."""
    shaped = signal.copy()
    fade_in, fade_out = min(seconds(in_s), len(signal)), min(seconds(out_s), len(signal))
    if fade_in:
        shaped[:fade_in] *= np.linspace(0.0, 1.0, fade_in)
    if fade_out:
        shaped[-fade_out:] *= np.linspace(1.0, 0.0, fade_out)
    return shaped


def _as_signal(signal: NDArray[np.float64]) -> Signal:
    return signal.astype(np.float32)


def sine_sweep(f_start: float, f_end: float, duration_s: float) -> NDArray[np.float64]:
    """Sine whose frequency moves exponentially from ``f_start`` to ``f_end``."""
    samples = seconds(duration_s)
    frequency = f_start * (f_end / f_start) ** (np.arange(samples) / samples)
    return np.sin(2.0 * np.pi * np.cumsum(frequency) / SAMPLE_RATE)


def sweep_filter(
    source: NDArray[np.float64], f_start: float, f_end: float, sharpness: float = 2.5
) -> NDArray[np.float64]:
    """Band-pass ``source`` around a centre that glides from ``f_start`` to ``f_end`` Hz.

    Short-time Fourier filtering: each windowed frame keeps a bell of frequencies (in octaves,
    ``sharpness`` narrows it) around the centre for that moment, then frames are overlap-added.
    """
    length = len(source)
    padded = np.pad(source, (_STFT_FRAME, _STFT_FRAME))
    starts = np.arange(0, len(padded) - _STFT_FRAME + 1, _STFT_HOP)
    frame_index = starts[:, None] + np.arange(_STFT_FRAME)[None, :]
    window = np.hanning(_STFT_FRAME)
    spectrum = np.fft.rfft(padded[frame_index] * window, axis=1)
    octaves = np.log2(np.fft.rfftfreq(_STFT_FRAME, 1.0 / SAMPLE_RATE) + 1e-9)
    progress = np.clip((starts + _STFT_FRAME / 2 - _STFT_FRAME) / max(length, 1), 0.0, 1.0)
    centres = np.log2(f_start * (f_end / f_start) ** progress)
    gain = np.exp(-0.5 * ((octaves[None, :] - centres[:, None]) * sharpness) ** 2)
    frames = np.fft.irfft(spectrum * gain, n=_STFT_FRAME, axis=1) * window
    output = np.zeros(len(padded))
    np.add.at(output, frame_index, frames)
    return output[_STFT_FRAME : _STFT_FRAME + length] / _HANN_OVERLAP_GAIN


def low_pass(source: NDArray[np.float64], cutoff_hz: float) -> NDArray[np.float64]:
    """One-pole low-pass by convolution with a decaying exponential (about 6 dB/octave)."""
    kernel = np.exp(-2.0 * np.pi * cutoff_hz * _time(max(int(SAMPLE_RATE / cutoff_hz * 6), 8)))
    return np.convolve(source, kernel / kernel.sum())[: len(source)]


def _normalised(signal: NDArray[np.float64], peak: float) -> NDArray[np.float64]:
    top = float(np.max(np.abs(signal))) or 1.0
    return signal * (peak / top)


def kick() -> Signal:
    """Four-on-the-floor kick: a falling sine plus a short click."""
    samples = seconds(0.4)
    body = sine_sweep(140.0, 48.0, 0.4) * decay(samples, 0.11)
    click = noise("kick-click", samples) * decay(samples, 0.004) * 0.35
    return _as_signal(np.tanh(1.4 * (body + click)))


def hat() -> Signal:
    """Closed hi-hat: differentiated noise with a very short decay."""
    samples = seconds(0.09)
    bright = np.diff(noise("hat", samples + 1))
    return _as_signal(bright * decay(samples, 0.018) * 0.5)


def bass_note(frequency: float, duration_s: float) -> Signal:
    """Warm sub-bass: fundamental plus a saturated second harmonic."""
    t = _time(seconds(duration_s))
    tone = np.sin(2.0 * np.pi * frequency * t) + 0.35 * np.sin(4.0 * np.pi * frequency * t)
    return _as_signal(np.tanh(tone) * fade(np.ones_like(t), 0.006, 0.08))


def pluck(frequency: float, duration_s: float = 0.3) -> Signal:
    """Short plucked note for the arpeggio."""
    t = _time(seconds(duration_s))
    tone = np.sin(2.0 * np.pi * frequency * t) + 0.4 * np.sin(6.0 * np.pi * frequency * t)
    return _as_signal(tone * decay(len(t), 0.09) * fade(np.ones_like(t), 0.002, 0.0))


def pad(frequencies: tuple[float, ...], duration_s: float, detune: float) -> Signal:
    """Soft chord pad: each note is a few low harmonics, slightly detuned by ``detune``."""
    t = _time(seconds(duration_s))
    tone = np.zeros_like(t)
    for frequency in frequencies:
        for harmonic in range(1, 7):
            tone += np.sin(2.0 * np.pi * harmonic * frequency * (1.0 + detune) * t) / harmonic**1.4
    return _as_signal(_normalised(tone, 0.5) * fade(np.ones_like(t), 0.35, 0.45))


def whoosh(duration_s: float, *, rising: bool = True) -> Signal:
    """Air sweep that swells to its loudest moment at 80 % and ends quickly."""
    samples = seconds(duration_s)
    low, high = (350.0, 4200.0) if rising else (4200.0, 350.0)
    air = sweep_filter(noise("whoosh", samples), low, high)
    swell = np.where(
        np.arange(samples) < 0.8 * samples,
        (np.arange(samples) / (0.8 * samples)) ** 2,
        np.maximum(1.0 - (np.arange(samples) - 0.8 * samples) / (0.2 * samples), 0.0) ** 1.5,
    )
    return _as_signal(_normalised(air * swell, 0.9))


def riser(duration_s: float) -> Signal:
    """Rising noise that builds into a drop; it stops abruptly at its end."""
    samples = seconds(duration_s)
    air = sweep_filter(noise("riser", samples), 250.0, 7000.0, sharpness=1.6)
    return _as_signal(_normalised(air * (np.arange(samples) / samples) ** 1.8, 0.8))


def impact() -> Signal:
    """Soft hit: a low thump under a short, dark noise burst."""
    samples = seconds(0.5)
    thump = sine_sweep(95.0, 38.0, 0.5) * decay(samples, 0.12)
    burst = low_pass(noise("impact", samples), 900.0) * decay(samples, 0.03) * 2.0
    return _as_signal(_normalised(np.tanh(thump + burst), 0.9))


def tick() -> Signal:
    """Very short, quiet text-reveal tick."""
    samples = seconds(0.03)
    t = _time(samples)
    click = (np.sin(2.0 * np.pi * 2400.0 * t) + 0.4 * noise("tick", samples)) * decay(
        samples, 0.0045
    )
    return _as_signal(_normalised(click, 0.8))


def shimmer() -> Signal:
    """Airy chime: four high partials with a gentle tremolo, fading over ~1.3 s."""
    samples = seconds(1.3)
    t = _time(samples)
    partials = (1318.5, 1661.2, 1975.5, 2637.0)
    tone = sum(
        np.sin(2.0 * np.pi * f * t) * decay(samples, 0.5 + 0.12 * i) for i, f in enumerate(partials)
    )
    tremolo = 1.0 + 0.2 * np.sin(2.0 * np.pi * 5.0 * t)
    return _as_signal(_normalised(tone * tremolo * fade(np.ones_like(t), 0.004), 0.7))
