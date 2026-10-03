"""Video file handling: content hash, ffprobe validation and the silent-audio normalisation."""

import asyncio
import hashlib
import json
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO

_CHUNK_BYTES = 1024 * 1024
_MP4_FORMATS = {"mp4", "mov"}
_SILENCE_FILTER = "anullsrc=channel_layout=stereo:sample_rate=44100"


class InvalidVideoError(ValueError):
    """The upload is not a usable MP4 video."""


class UploadTooLargeError(ValueError):
    """The upload exceeds the configured size limit."""


@dataclass(frozen=True)
class StoredUpload:
    """An uploaded file on disk and its content hash."""

    path: Path
    sha256: str


@dataclass(frozen=True)
class VideoProbe:
    """Facts ffprobe reports about a validated video."""

    duration_s: float
    width: int
    height: int
    has_audio: bool


def store_upload(source: BinaryIO, directory: Path, *, max_bytes: int) -> StoredUpload:
    """Copy ``source`` into ``directory`` as ``<sha256>.mp4`` while hashing it in one pass.

    Blocking: call it from a worker thread. The file is named by content, so identical uploads
    share one file. It is not yet validated; run :func:`probe_video` on the result.

    Raises:
        UploadTooLargeError: more than ``max_bytes`` were sent (nothing is left on disk).
    """
    directory.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    received = 0
    with tempfile.NamedTemporaryFile(dir=directory, suffix=".part", delete=False) as partial:
        try:
            while chunk := source.read(_CHUNK_BYTES):
                received += len(chunk)
                if received > max_bytes:
                    raise UploadTooLargeError(f"upload is larger than {max_bytes} bytes")
                digest.update(chunk)
                partial.write(chunk)
        except UploadTooLargeError:
            Path(partial.name).unlink()
            raise
    final = directory / f"{digest.hexdigest()}.mp4"
    Path(partial.name).replace(final)
    return StoredUpload(path=final, sha256=digest.hexdigest())


async def probe_video(path: Path, *, max_duration_s: float) -> VideoProbe:
    """Validate with ffprobe that ``path`` is a real MP4 video of acceptable length.

    Raises:
        InvalidVideoError: unreadable, not an MP4/MOV container, no video stream, or a
            duration outside ``(0, max_duration_s]``.
    """
    report = await _ffprobe_json(path)
    format_names = set(str(report.get("format", {}).get("format_name", "")).split(","))
    if not format_names & _MP4_FORMATS:
        raise InvalidVideoError("upload is not an MP4 file")
    streams: list[dict[str, Any]] = report.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    if video is None:
        raise InvalidVideoError("upload has no video stream")
    duration_s = float(report["format"].get("duration", 0.0))
    if not 0.0 < duration_s <= max_duration_s:
        raise InvalidVideoError(f"video duration {duration_s:.1f}s is outside 0-{max_duration_s}s")
    return VideoProbe(
        duration_s=duration_s,
        width=int(video.get("width", 0)),
        height=int(video.get("height", 0)),
        has_audio=any(s.get("codec_type") == "audio" for s in streams),
    )


async def ensure_audio_track(video: Path, probe: VideoProbe, output: Path) -> Path:
    """Return a video the model can read audio from.

    tribev2 extracts the audio track from the video and transcribes it. Renders from the
    template may have no audio stream at all, so a silent stereo track is muxed in (video is
    stream-copied, not re-encoded). The model then sees genuine silence instead of failing on a
    missing track. Videos that already have audio are returned untouched.
    """
    if probe.has_audio:
        return video
    await _run(
        "ffmpeg", "-y", "-v", "error", "-i", str(video), "-f", "lavfi", "-i", _SILENCE_FILTER,
        "-c:v", "copy", "-c:a", "aac", "-shortest", str(output),
    )  # fmt: skip
    return output


async def _ffprobe_json(path: Path) -> dict[str, Any]:
    try:
        stdout = await _run(
            "ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams",
            str(path),
        )  # fmt: skip
        report: dict[str, Any] = json.loads(stdout)
    except (RuntimeError, json.JSONDecodeError) as error:
        raise InvalidVideoError("upload is not a readable video") from error
    return report


async def _run(*command: str) -> bytes:
    process = await asyncio.create_subprocess_exec(
        *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        raise RuntimeError(f"{command[0]} failed: {stderr.decode(errors='replace').strip()}")
    return stdout
