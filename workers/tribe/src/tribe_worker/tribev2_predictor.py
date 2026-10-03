"""The real predictor: a thin adapter over upstream ``tribev2`` (vendor/tribev2).

This is the only module that touches the model library, and it imports it lazily so the rest of
the worker (and its tests) run without torch. It adds no model behaviour of its own.

Decisions about upstream behaviour, verified by reading ``vendor/tribev2`` (not by running it):

* ``TribeModel.predict`` returns only segments that contain events (``remove_empty_segments``
  defaults to ``True``). We keep that default: ``False`` would also return the padding of the last
  40-second batch, i.e. predictions for seconds that are not in the video. A video always
  contributes a ``Video`` event, so silent clips are not dropped; only padding is.
* Upstream documents predictions as already offset by five seconds to compensate the
  hemodynamic lag. We report each segment's own start time and never shift again.
* The segment's start time is read from ``segment.start`` (neuralset ``Segment``).
"""

import threading
import time
from pathlib import Path
from typing import Protocol, cast

import numpy as np
from numpy.typing import NDArray

from tribe_worker.predictor import Prediction, PredictorInfo

# Upstream commit vendored under vendor/tribev2 (chore(FR-04): vendor TRIBE v2 at upstream af58661).
VENDORED_TRIBEV2_COMMIT = "af58661791a351a448a489042a28f6c37e1c14b7"
CHECKPOINT_CONFIG_FILE = "config.yaml"
BYTES_PER_MB = 1024 * 1024


class _DataConfig(Protocol):
    @property
    def TR(self) -> float: ...  # noqa: N802 - upstream attribute name


class _Segment(Protocol):
    @property
    def start(self) -> float: ...


class _TribeModel(Protocol):
    """The slice of ``tribev2.TribeModel`` this adapter relies on."""

    @property
    def data(self) -> _DataConfig: ...

    def get_events_dataframe(self, *, video_path: str) -> object: ...

    def predict(
        self, events: object, verbose: bool = True
    ) -> tuple[NDArray[np.float32], list[_Segment]]: ...


class Tribev2Predictor:
    """Loads ``facebook/tribev2`` once and runs it on one video at a time."""

    def __init__(self, *, model_repo: str, cache_folder: Path, device: str) -> None:
        """Remember where to load from; nothing is downloaded or loaded until :meth:`load`."""
        self._model_repo = model_repo
        self._cache_folder = cache_folder
        self._device = device
        self._lock = threading.Lock()
        self._model: _TribeModel | None = None
        self._checkpoint_revision: str | None = None
        self._load_seconds: float | None = None

    def info(self) -> PredictorInfo:
        """Environment and load state; never triggers a load."""
        gpu_name, vram_mb, torch_version = _torch_environment(self._device)
        return PredictorInfo(
            loaded=self._model is not None,
            device=self._device,
            gpu_name=gpu_name,
            vram_total_mb=vram_mb,
            torch_version=torch_version,
            tribev2_revision=VENDORED_TRIBEV2_COMMIT,
            checkpoint_revision=self._checkpoint_revision,
            load_seconds=self._load_seconds,
        )

    def load(self) -> None:
        """Download (first time) and load weights; Llama-3.2-3B access must already be granted."""
        with self._lock:
            if self._model is not None:
                return
            from tribev2 import TribeModel  # noqa: PLC0415 - optional GPU dependency

            started = time.monotonic()
            model = TribeModel.from_pretrained(
                self._model_repo, cache_folder=str(self._cache_folder), device=self._device
            )
            self._checkpoint_revision = _checkpoint_revision(self._model_repo)
            self._load_seconds = round(time.monotonic() - started, 3)
            self._model = cast("_TribeModel", model)

    def predict(self, video_path: Path) -> Prediction:
        """Run the model on ``video_path`` and return its raw output (see module docstring)."""
        self.load()
        model = cast("_TribeModel", self._model)
        events = model.get_events_dataframe(video_path=str(video_path))
        activity, segments = model.predict(events=events, verbose=False)
        return Prediction(
            activity=np.asarray(activity, dtype=np.float32),
            start_times_s=tuple(float(segment.start) for segment in segments),
            hz=1.0 / float(model.data.TR),
        )


def _checkpoint_revision(model_repo: str) -> str:
    """Commit hash of the Hugging Face snapshot that was just loaded (read from the local cache)."""
    from huggingface_hub import hf_hub_download  # noqa: PLC0415 - optional GPU dependency

    config_path = hf_hub_download(model_repo, CHECKPOINT_CONFIG_FILE, local_files_only=True)
    return Path(config_path).parent.name


def _torch_environment(device: str) -> tuple[str | None, int | None, str | None]:
    """GPU name, total VRAM in MB and torch version; ``None`` where torch/CUDA is absent."""
    try:
        import torch  # noqa: PLC0415 - optional GPU dependency
    except ImportError:
        return None, None, None
    if not (device.startswith("cuda") and torch.cuda.is_available()):
        return None, None, str(torch.__version__)
    properties = torch.cuda.get_device_properties(torch.device(device))
    return properties.name, int(properties.total_memory // BYTES_PER_MB), str(torch.__version__)
