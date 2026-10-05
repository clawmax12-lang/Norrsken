"""PCM and WAV helpers: decoding speech, resampling, trimming and writing the mix."""

import wave
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from . import dsp

_INT16_FULL_SCALE = 32768.0
_SILENCE_FLOOR = 10 ** (-45 / 20)  # relative to the clip's peak
_TRIM_MARGIN_S = 0.03
_CLIP_PEAK = 0.95
_GLITCH_HOP_S = 0.012
_GLITCH_MAX_S = 0.08
_FADE_IN_S = 0.012
_FADE_OUT_S = 0.05


def pcm16_to_float(pcm: bytes) -> NDArray[np.float32]:
    """Decode little-endian mono 16-bit PCM to floats in [-1, 1]."""
    return (np.frombuffer(pcm, dtype="<i2").astype(np.float32) / _INT16_FULL_SCALE).astype(
        np.float32
    )


def float_to_pcm16(samples: NDArray[np.float32]) -> bytes:
    """Encode floats (clipped to [-1, 1]) as little-endian 16-bit PCM."""
    scaled = np.clip(samples, -1.0, 1.0) * (_INT16_FULL_SCALE - 1)
    return scaled.astype("<i2").tobytes()


def resample(samples: NDArray[np.float32], from_hz: int, to_hz: int) -> NDArray[np.float32]:
    """Band-limited resampling by cutting or zero-padding the spectrum."""
    if from_hz == to_hz or len(samples) == 0:
        return samples
    target = round(len(samples) * to_hz / from_hz)
    spectrum = np.fft.rfft(samples)
    resized = np.zeros(target // 2 + 1, dtype=complex)
    keep = min(len(spectrum), len(resized))
    resized[:keep] = spectrum[:keep]
    return (np.fft.irfft(resized, n=target) * (target / len(samples))).astype(np.float32)


def trim_silence(samples: NDArray[np.float32]) -> NDArray[np.float32]:
    """Drop leading and trailing silence (TTS pads both) but keep a short natural margin."""
    loud = np.flatnonzero(
        np.abs(samples) > _SILENCE_FLOOR * max(float(np.max(np.abs(samples), initial=0.0)), 1e-9)
    )
    if loud.size == 0:
        return samples[:0]
    margin = dsp.seconds(_TRIM_MARGIN_S)
    return samples[max(loud[0] - margin, 0) : loud[-1] + margin]


def spoken(pcm: bytes, sample_rate: int) -> NDArray[np.float32]:
    """The voiced part of a TTS clip exactly as the mix plays it: padding and tail glitch gone."""
    return deglitch_tail(trim_silence(pcm16_to_float(pcm)), sample_rate)


def deglitch_tail(samples: NDArray[np.float32], sample_rate: int) -> NDArray[np.float32]:
    """Drop a clipped burst some TTS streams append after the last phoneme."""
    hop = max(int(_GLITCH_HOP_S * sample_rate), 1)
    max_cut = int(_GLITCH_MAX_S * sample_rate)
    if len(samples) < max_cut + hop:
        return samples
    body = samples[:-max_cut]
    body_rms = float(np.sqrt(np.mean(np.square(body)))) or 1e-9
    body_peak = float(np.max(np.abs(body)))
    out = samples
    cut = 0
    while cut + hop <= max_cut:
        tail = out[-hop:]
        tail_peak = float(np.max(np.abs(tail)))
        tail_rms = float(np.sqrt(np.mean(np.square(tail))))
        louder = tail_rms > body_rms * 1.2
        clipped = tail_peak >= _CLIP_PEAK and (louder or tail_peak > body_peak * 1.15)
        if not clipped:
            break
        out = out[:-hop]
        cut += hop
    return out


def fade_edges(
    samples: NDArray[np.float32],
    sample_rate: int,
    *,
    in_s: float = _FADE_IN_S,
    out_s: float = _FADE_OUT_S,
) -> NDArray[np.float32]:
    """Fade the first and last samples to zero so a hard TTS cut does not click."""
    if len(samples) == 0:
        return samples
    shaped = samples.copy()
    fade_in = min(int(in_s * sample_rate), len(shaped))
    fade_out = min(int(out_s * sample_rate), len(shaped))
    if fade_in:
        shaped[:fade_in] *= np.linspace(0.0, 1.0, fade_in, dtype=np.float32)
    if fade_out:
        shaped[-fade_out:] *= np.linspace(1.0, 0.0, fade_out, dtype=np.float32)
    return shaped


def rms_normalise(samples: NDArray[np.float32], target_dbfs: float) -> NDArray[np.float32]:
    """Scale so the clip's RMS is ``target_dbfs``, leaving at least 1 dB below full scale."""
    rms = float(np.sqrt(np.mean(np.square(samples)))) if len(samples) else 0.0
    if rms == 0.0:
        return samples
    gain = 10 ** (target_dbfs / 20) / rms
    peak = float(np.max(np.abs(samples)))
    return (samples * min(gain, 0.89 / peak)).astype(np.float32)


def write_wav(path: Path, samples: NDArray[np.float32], sample_rate: int) -> None:
    """Write 16-bit PCM WAV; ``samples`` is ``(n,)`` mono or ``(n, 2)`` stereo."""
    channels = 1 if samples.ndim == 1 else samples.shape[1]
    _write_frames(path, float_to_pcm16(samples.reshape(-1)), sample_rate, channels)


def write_pcm_wav(path: Path, pcm: bytes, sample_rate: int) -> None:
    """Write mono 16-bit PCM as a WAV file, replacing ``path`` atomically."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    _write_frames(temporary, pcm, sample_rate, 1)
    temporary.replace(path)


def _write_frames(path: Path, pcm: bytes, sample_rate: int, channels: int) -> None:
    with wave.open(str(path), "wb") as file:
        file.setnchannels(channels)
        file.setsampwidth(2)
        file.setframerate(sample_rate)
        file.writeframes(pcm)


def read_wav_mono_pcm(path: Path) -> tuple[bytes, int]:
    """Return the PCM frames and sample rate of a mono 16-bit WAV file."""
    with wave.open(str(path), "rb") as file:
        return file.readframes(file.getnframes()), file.getframerate()
