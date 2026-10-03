"""ffmpeg and ffprobe: master the mix to broadcast loudness, mux it, verify the result.

The video stream is copied bit for bit (``-c:v copy``), so the exported picture is exactly the
render that was pretested. Loudness is mastered with ffmpeg's two-pass ``loudnorm`` (measure,
then apply a linear gain) and measured again on the encoded file, so the numbers in the
:class:`~preflight.contracts.SoundRecord` are measurements, not targets.
"""

import asyncio
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from preflight.errors import SoundError

TARGET_LUFS = -14.0
MAX_TRUE_PEAK_DBTP = -1.0
# AAC encoding overshoots the limiter by a fraction of a dB, so the first attempt aims lower;
# if the encoded file still exceeds MAX_TRUE_PEAK_DBTP the ceiling drops by the overshoot.
FIRST_LIMITER_DBTP = -2.0
_MAX_ATTEMPTS = 3
_CEILING_MARGIN_DB = 0.2
_LOUDNORM_RANGE = 11.0
_AUDIO_BITRATE = "192k"
_TIMEOUT_S = 180.0
_STDERR_TAIL_CHARS = 500
_DURATION_TOLERANCE_S = 0.1
_JSON_BLOCK = re.compile(r"\{[^{}]*\}")


@dataclass(frozen=True)
class Loudness:
    """Loudness of an audio stream: integrated LUFS and true peak in dBTP."""

    integrated_lufs: float
    true_peak_dbtp: float


@dataclass(frozen=True)
class MediaInfo:
    """What ffprobe reports about the first video and audio streams."""

    video_codec: str
    width: int
    height: int
    video_duration_s: float
    audio_codec: str | None
    audio_duration_s: float | None


class Ffmpeg:
    """Async wrapper over the ``ffmpeg`` and ``ffprobe`` binaries."""

    def __init__(self, ffmpeg: str = "ffmpeg", ffprobe: str = "ffprobe") -> None:
        """Use these executables (resolved through ``PATH`` when not absolute)."""
        self._ffmpeg = ffmpeg
        self._ffprobe = ffprobe

    async def master_and_mux(self, video: Path, mix_wav: Path, output: Path) -> Loudness:
        """Loudness-normalise ``mix_wav``, add it to ``video`` and return the measured result.

        Raises:
            SoundError: ffmpeg is missing or fails, or the output has no matching audio track.
        """
        ceiling = FIRST_LIMITER_DBTP
        for attempt in range(_MAX_ATTEMPTS):
            measured = await self._measure(mix_wav, ceiling)
            await self._run(
                self._ffmpeg, "-y", "-v", "error", "-i", str(video), "-i", str(mix_wav),
                "-filter_complex", f"[1:a]{_loudnorm(measured, ceiling)}[a]",
                "-map", "0:v:0", "-map", "[a]", "-c:v", "copy", "-c:a", "aac",
                "-b:a", _AUDIO_BITRATE, "-ar", "48000", "-movflags", "+faststart", str(output),
            )  # fmt: skip
            result = await self._verify(video, output)
            if result.true_peak_dbtp <= MAX_TRUE_PEAK_DBTP or attempt == _MAX_ATTEMPTS - 1:
                return result
            ceiling -= result.true_peak_dbtp - MAX_TRUE_PEAK_DBTP + _CEILING_MARGIN_DB
        raise AssertionError("unreachable")  # pragma: no cover

    async def stretch(self, pcm: bytes, sample_rate: int, ratio: float) -> bytes:
        """Speed mono 16-bit PCM up by ``ratio`` (> 1) without changing its pitch."""
        process = await self._spawn(
            self._ffmpeg, "-v", "error", "-f", "s16le", "-ar", str(sample_rate), "-ac", "1",
            "-i", "pipe:0", "-filter:a", f"atempo={ratio:.4f}", "-f", "s16le", "pipe:1",
        )  # fmt: skip
        stdout, stderr = await _communicate(process, pcm)
        if process.returncode != 0:
            raise SoundError(f"ffmpeg could not change the speech tempo: {_tail(stderr)}")
        return stdout

    async def probe(self, path: Path) -> MediaInfo:
        """Describe the first video and audio streams of ``path``."""
        output = await self._run(
            self._ffprobe, "-v", "error", "-print_format", "json", "-show_streams", str(path)
        )
        streams = json.loads(output)["streams"]
        video = next((s for s in streams if s["codec_type"] == "video"), None)
        audio = next((s for s in streams if s["codec_type"] == "audio"), None)
        if video is None:
            raise SoundError(f"{path.name} has no video stream")
        return MediaInfo(
            video_codec=video["codec_name"],
            width=int(video["width"]),
            height=int(video["height"]),
            video_duration_s=float(video.get("duration", 0.0)),
            audio_codec=audio["codec_name"] if audio else None,
            audio_duration_s=float(audio["duration"]) if audio and "duration" in audio else None,
        )

    async def _measure(self, source: Path, ceiling_dbtp: float) -> dict[str, Any]:
        """First loudnorm pass: ffmpeg prints the stream's measured loudness as JSON."""
        stderr = await self._run(
            self._ffmpeg, "-hide_banner", "-nostats", "-i", str(source), "-map", "0:a:0",
            "-af", f"{_loudnorm_target(ceiling_dbtp)}:print_format=json",
            "-f", "null", "-", capture_stderr=True,
        )  # fmt: skip
        blocks = _JSON_BLOCK.findall(stderr)
        if not blocks:
            raise SoundError("ffmpeg loudnorm printed no measurements")
        measured: dict[str, Any] = json.loads(blocks[-1])
        return measured

    async def _verify(self, source: Path, output: Path) -> Loudness:
        """Check the muxed file keeps the picture and carries AAC audio of the same length."""
        before, after = await self.probe(source), await self.probe(output)
        if (after.video_codec, after.width, after.height) != (
            before.video_codec,
            before.width,
            before.height,
        ):
            raise SoundError("muxing changed the video stream")
        if after.audio_codec != "aac" or after.audio_duration_s is None:
            raise SoundError("the output has no AAC audio track")
        if abs(after.audio_duration_s - after.video_duration_s) > _DURATION_TOLERANCE_S:
            raise SoundError("audio and video lengths differ")
        measured = await self._measure(output, FIRST_LIMITER_DBTP)
        return Loudness(float(measured["input_i"]), float(measured["input_tp"]))

    async def _spawn(self, *command: str) -> asyncio.subprocess.Process:
        try:
            return await asyncio.create_subprocess_exec(
                *command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except OSError as exc:
            raise SoundError(f"cannot start {command[0]}: {exc}") from exc

    async def _run(self, *command: str, capture_stderr: bool = False) -> str:
        """Run to completion; return stdout (or stderr, where loudnorm prints)."""
        process = await self._spawn(*command)
        stdout, stderr = await _communicate(process, None)
        if process.returncode != 0:
            raise SoundError(f"{Path(command[0]).name} failed: {_tail(stderr)}")
        return (stderr if capture_stderr else stdout).decode(errors="replace")


async def _communicate(
    process: asyncio.subprocess.Process, data: bytes | None
) -> tuple[bytes, bytes]:
    try:
        return await asyncio.wait_for(process.communicate(data), timeout=_TIMEOUT_S)
    except TimeoutError as exc:
        process.kill()
        await process.wait()
        raise SoundError("ffmpeg timed out") from exc
    except asyncio.CancelledError:
        process.kill()
        await process.wait()
        raise


def _loudnorm_target(ceiling_dbtp: float) -> str:
    return f"loudnorm=I={TARGET_LUFS}:TP={ceiling_dbtp:.2f}:LRA={_LOUDNORM_RANGE}"


def _loudnorm(measured: dict[str, Any], ceiling_dbtp: float) -> str:
    """Second loudnorm pass: apply the measured values so the gain is a single linear step."""
    return (
        f"{_loudnorm_target(ceiling_dbtp)}"
        f":measured_I={measured['input_i']}:measured_TP={measured['input_tp']}"
        f":measured_LRA={measured['input_lra']}:measured_thresh={measured['input_thresh']}"
        f":offset={measured['target_offset']}:linear=true"
    )


def _tail(stderr: bytes) -> str:
    return stderr.decode(errors="replace").strip()[-_STDERR_TAIL_CHARS:]
