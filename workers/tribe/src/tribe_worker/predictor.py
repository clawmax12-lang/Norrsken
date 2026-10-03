"""The seam between the worker and the TRIBE v2 library.

Everything outside ``tribev2_predictor`` talks to :class:`TribePredictor`, so the HTTP layer,
reduction and caching are testable without a GPU and no provider type leaks upwards.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class Prediction:
    """Genuine model output for one video, exactly as the model returned it.

    ``activity`` has shape ``(n_samples, n_vertices)`` on fsaverage5 (left hemisphere first).
    ``start_times_s[i]`` is the start second, within the video, of the segment that produced
    row ``i``; segments without events are dropped by the model, so never assume row == second.
    The model's own five-second hemodynamic compensation is already applied; nothing here
    shifts it again.
    """

    activity: NDArray[np.float32]
    start_times_s: tuple[float, ...]
    hz: float


@dataclass(frozen=True)
class PredictorInfo:
    """What ``GET /health`` and the result ``meta`` report about the model and machine."""

    loaded: bool
    device: str
    gpu_name: str | None
    vram_total_mb: int | None
    torch_version: str | None
    tribev2_revision: str
    checkpoint_revision: str | None
    load_seconds: float | None

    @property
    def revision(self) -> str | None:
        """Cache-key revision of code + checkpoint; ``None`` until the checkpoint is known."""
        if self.checkpoint_revision is None:
            return None
        return f"{self.tribev2_revision[:12]}+{self.checkpoint_revision[:12]}"


class TribePredictor(Protocol):
    """Runs the brain-encoding model on one video file."""

    def info(self) -> PredictorInfo:
        """Report load state and environment without loading the model."""
        ...

    def load(self) -> None:
        """Load the model onto the device; idempotent and safe to call from a thread."""
        ...

    def predict(self, video_path: Path) -> Prediction:
        """Run inference. Blocks for as long as the GPU needs; call from a worker thread."""
        ...
