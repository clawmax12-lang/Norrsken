import subprocess

import numpy as np
import pytest

from preflight.errors import SoundError
from preflight.sound import dsp
from preflight.sound import ffmpeg as ffmpeg_module
from preflight.sound.audio import float_to_pcm16, pcm16_to_float, write_wav
from preflight.sound.ffmpeg import TARGET_LUFS, Ffmpeg, Loudness
from tests.sound.helpers import needs_ffmpeg, silent_video

pytestmark = needs_ffmpeg


def noise_bed(seconds: float, level: float = 0.2) -> np.ndarray:
    t = np.arange(dsp.seconds(seconds)) / dsp.SAMPLE_RATE
    tone = level * np.sin(2 * np.pi * 220 * t) * (0.6 + 0.4 * np.sin(2 * np.pi * 2 * t))
    return np.stack([tone, tone], axis=1).astype(np.float32)


async def test_mixing_adds_loudness_normalised_aac_and_leaves_the_picture_alone(tmp_path) -> None:
    video = silent_video(tmp_path / "v.mp4")
    write_wav(tmp_path / "bed.wav", noise_bed(15.0), dsp.SAMPLE_RATE)
    ffmpeg = Ffmpeg()

    loudness = await ffmpeg.master_and_mux(video, tmp_path / "bed.wav", tmp_path / "out.mp4")

    info = await ffmpeg.probe(tmp_path / "out.mp4")
    original = await ffmpeg.probe(video)
    assert (info.video_codec, info.width, info.height) == ("h264", 1080, 1920)
    assert info.audio_codec == "aac"
    assert info.audio_duration_s == pytest.approx(info.video_duration_s, abs=0.1)
    assert loudness.integrated_lufs == pytest.approx(TARGET_LUFS, abs=0.7)
    assert loudness.true_peak_dbtp <= -1.0
    assert original.audio_codec is None
    assert _video_checksum(video) == _video_checksum(tmp_path / "out.mp4")  # stream copy


def _video_checksum(path) -> str:
    result = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-map", "0:v", "-c", "copy", "-f", "md5", "-"],
        capture_output=True, text=True, check=True,
    )  # fmt: skip
    return result.stdout.strip()


async def test_a_quiet_bed_is_brought_up_and_a_hot_one_down_to_the_same_loudness(tmp_path) -> None:
    video = silent_video(tmp_path / "v.mp4", 6.0)
    ffmpeg = Ffmpeg()
    levels = []
    for name, level in (("quiet", 0.01), ("hot", 0.9)):
        write_wav(tmp_path / f"{name}.wav", noise_bed(6.0, level), dsp.SAMPLE_RATE)
        measured = await ffmpeg.master_and_mux(
            video, tmp_path / f"{name}.wav", tmp_path / f"{name}.mp4"
        )
        levels.append(measured.integrated_lufs)

    assert levels[0] == pytest.approx(levels[1], abs=1.0)


async def test_a_missing_binary_is_a_sound_error_not_a_crash(tmp_path) -> None:
    with pytest.raises(SoundError, match="cannot start"):
        await Ffmpeg("/no/such/ffmpeg", "/no/such/ffprobe").probe(tmp_path / "x.mp4")


async def test_a_corrupt_input_is_reported_with_ffmpegs_own_message(tmp_path) -> None:
    (tmp_path / "bad.mp4").write_bytes(b"not a video")

    with pytest.raises(SoundError, match="ffprobe failed"):
        await Ffmpeg().probe(tmp_path / "bad.mp4")


async def test_audio_longer_than_the_video_is_rejected(tmp_path) -> None:
    video = silent_video(tmp_path / "v.mp4", 4.0)
    write_wav(tmp_path / "long.wav", noise_bed(8.0), dsp.SAMPLE_RATE)

    with pytest.raises(SoundError, match="lengths differ"):
        # -shortest is not used on purpose: a mismatch must be caught, not hidden.
        await Ffmpeg().master_and_mux(video, tmp_path / "long.wav", tmp_path / "out.mp4")


async def test_stretching_speeds_speech_up_without_changing_its_pitch(tmp_path) -> None:
    t = np.arange(24_000 * 2) / 24_000
    tone = (0.5 * np.sin(2 * np.pi * 300 * t)).astype(np.float32)
    faster = pcm16_to_float(await Ffmpeg().stretch(float_to_pcm16(tone), 24_000, 1.25))

    assert len(faster) == pytest.approx(len(tone) / 1.25, rel=0.05)
    peak_hz = np.argmax(np.abs(np.fft.rfft(faster))) * 24_000 / len(faster)
    assert peak_hz == pytest.approx(300, abs=8)


class ScriptedFfmpeg(Ffmpeg):
    """Test-only: records the limiter ceilings and returns scripted true peaks (no real ffmpeg)."""

    def __init__(self, peaks: list[float]) -> None:
        super().__init__()
        self.peaks = peaks
        self.ceilings: list[float] = []

    async def _measure(self, source, ceiling_dbtp):
        self.ceilings.append(ceiling_dbtp)
        return {
            "input_i": "-20",
            "input_tp": "-3",
            "input_lra": "5",
            "input_thresh": "-30",
            "target_offset": "0",
        }

    async def _run(self, *command, capture_stderr=False):
        return ""

    async def _verify(self, source, output):
        return Loudness(-14.0, self.peaks.pop(0))


async def test_a_true_peak_over_the_limit_lowers_the_ceiling_and_encodes_again(tmp_path) -> None:
    ffmpeg = ScriptedFfmpeg(peaks=[-0.4, -1.3])

    result = await ffmpeg.master_and_mux(tmp_path / "v.mp4", tmp_path / "a.wav", tmp_path / "o.mp4")

    assert result.true_peak_dbtp == -1.3
    assert ffmpeg.ceilings == pytest.approx([-2.0, -2.0 - (-0.4 + 1.0 + 0.2)])


async def test_the_encode_is_repeated_at_most_three_times(tmp_path) -> None:
    ffmpeg = ScriptedFfmpeg(peaks=[-0.5, -0.5, -0.5])

    result = await ffmpeg.master_and_mux(tmp_path / "v.mp4", tmp_path / "a.wav", tmp_path / "o.mp4")

    assert len(ffmpeg.ceilings) == 3
    assert result.true_peak_dbtp == -0.5  # reported honestly, not hidden


async def test_a_hung_process_is_killed_and_reported(tmp_path, monkeypatch) -> None:
    script = tmp_path / "slow"
    script.write_text("#!/bin/sh\nsleep 5\n")
    script.chmod(0o755)
    monkeypatch.setattr(ffmpeg_module, "_TIMEOUT_S", 0.2)

    with pytest.raises(SoundError, match="timed out"):
        await Ffmpeg(str(script), str(script)).probe(tmp_path / "x.mp4")


async def test_a_picture_that_changed_during_muxing_is_rejected(tmp_path) -> None:
    video = silent_video(tmp_path / "v.mp4", 3.0)
    other = silent_video(tmp_path / "o.mp4", 3.0, size="540x960")

    with pytest.raises(SoundError, match="changed the video"):
        await Ffmpeg()._verify(video, other)


async def test_a_file_without_audio_is_rejected(tmp_path) -> None:
    video = silent_video(tmp_path / "v.mp4", 3.0)

    with pytest.raises(SoundError, match="no AAC audio"):
        await Ffmpeg()._verify(video, video)
