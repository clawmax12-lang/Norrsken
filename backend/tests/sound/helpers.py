"""Test-only builders: a composition spec, a silent video and a stand-in voice."""

import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from preflight.contracts import CompositionSpec
from preflight.generation.compose import compose
from preflight.ports import SpeechClip
from preflight.sound.audio import float_to_pcm16
from tests.factories import make_brief, make_concept

needs_ffmpeg = pytest.mark.skipif(
    shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None,
    reason="ffmpeg and ffprobe are required",
)


def make_spec(**concept_overrides: object) -> CompositionSpec:
    """The spec of the standard 5-scene, 15 s test concept (scenes of 3 s)."""
    return compose(make_brief(), make_concept(**concept_overrides), ())


def silent_video(path: Path, seconds: float = 15.0, size: str = "1080x1920") -> Path:
    """A real 30 fps H.264 file (1080x1920 unless ``size`` says otherwise) with no audio."""
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
         f"color=c=0xf5f5f7:s={size}:r=30:d={seconds}", "-c:v", "libx264",
         "-pix_fmt", "yuv420p", str(path)],
        check=True,
    )  # fmt: skip
    return path


def tone_clip(seconds: float, *, lead_silence_s: float = 0.2, rate: int = 24_000) -> SpeechClip:
    """A stand-in 'voice': a 180 Hz tone with syllable-like amplitude bumps, padded by silence."""
    t = np.arange(int(seconds * rate)) / rate
    voiced = np.sin(2 * np.pi * 180 * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 4 * t)) * 0.4
    pad = np.zeros(int(lead_silence_s * rate), dtype=np.float32)
    samples = np.concatenate([pad, voiced.astype(np.float32), pad])
    return SpeechClip(float_to_pcm16(samples), rate, input_tokens=7, output_tokens=40)
