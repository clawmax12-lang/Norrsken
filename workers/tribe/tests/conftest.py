import shutil
import subprocess
from pathlib import Path

import pytest

from tribe_worker.config import WorkerSettings

needs_ffmpeg = pytest.mark.skipif(
    shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None,
    reason="ffmpeg/ffprobe are required to build and validate test videos",
)


def make_video(path: Path, *, seconds: int = 3, with_audio: bool = False) -> Path:
    """Write a tiny real MP4 (test pattern, optional sine tone)."""
    command = ["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i"]
    command += [f"testsrc=duration={seconds}:size=64x64:rate=10"]
    if with_audio:
        command += ["-f", "lavfi", "-i", f"sine=duration={seconds}", "-c:a", "aac"]
    command += ["-pix_fmt", "yuv420p", "-shortest", str(path)]
    subprocess.run(command, check=True)  # noqa: S603
    return path


@pytest.fixture(scope="session")
def silent_video(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return make_video(tmp_path_factory.mktemp("videos") / "silent.mp4")


@pytest.fixture(scope="session")
def audio_video(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return make_video(tmp_path_factory.mktemp("videos") / "audio.mp4", with_audio=True)


@pytest.fixture
def settings(tmp_path: Path) -> WorkerSettings:
    return WorkerSettings(data_dir=tmp_path / "data", queue_size=1, preload_model=False)
