"""FR-04: the single boundary every simulator speaks (PRD §10.2, §10.3 ``SimulationResult``).

Scoring, explanations and the UI read only these models. Provider-specific output
(TRIBE arrays, Gemini JSON) is translated at the simulator adapter and goes no further.
"""

from enum import StrEnum
from typing import Annotated, Any, Literal, Self

from pydantic import Field, model_validator

from ._base import SHA256_PATTERN, Contract
from .concept import VariantId


class SimulatorName(StrEnum):
    """Known simulators. Adding one adds a member here and an adapter; nothing else."""

    TRIBE_V2 = "tribe_v2"
    GEMINI_PANEL = "gemini_panel"


class EventType(StrEnum):
    """A moment worth explaining: viewers hold or drop."""

    HOLD = "hold"
    DROP = "drop"


class SimEvent(Contract):
    """A hold or drop moment at second ``t`` with a short factual label."""

    t: Annotated[float, Field(ge=0)]
    type: EventType
    label: Annotated[str, Field(min_length=1)]


class BrainArtifact(Contract):
    """Pointer to the genuine per-vertex TRIBE prediction stored beside the video.

    ``activity_path`` is a little-endian float16 ``.npy`` of shape
    ``(len(timestamps_s), n_vertices)`` ordered left hemisphere first, then right,
    matching the ``fsaverage5`` mesh. ``groups_path`` maps each region group to its vertices.
    """

    mesh: Literal["fsaverage5"] = "fsaverage5"
    n_vertices: Annotated[int, Field(gt=0)]
    activity_path: Annotated[str, Field(min_length=1)]
    atlas: Annotated[str, Field(min_length=1)]
    groups_path: Annotated[str, Field(min_length=1)]


class SimulationResult(Contract):
    """One simulator's response to one rendered variant.

    ``primary_series`` names the one per-second series (values in ``[0, 1]``) the simulator
    offers for ranking; scoring never has to know which provider produced it.
    ``timestamps_s`` gives the start second of each sample (samples may be missing for
    silent stretches, so never assume index == second).
    """

    variant_id: VariantId
    simulator: SimulatorName
    version: Annotated[str, Field(min_length=1)]
    hz: Annotated[float, Field(gt=0)] = 1.0
    video_sha256: Annotated[str, Field(pattern=SHA256_PATTERN)]
    duration_s: Annotated[float, Field(gt=0)]
    timestamps_s: tuple[float, ...]
    series: dict[str, tuple[float, ...]]
    primary_series: Annotated[str, Field(min_length=1)]
    events: tuple[SimEvent, ...] = ()
    precomputed: bool = False
    brain: BrainArtifact | None = None
    meta: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _series_are_aligned(self) -> Self:
        if self.primary_series not in self.series:
            raise ValueError("primary_series must be one of the series")
        for name, values in self.series.items():
            if len(values) != len(self.timestamps_s):
                raise ValueError(f"series {name!r} length differs from timestamps_s")
        if any(not 0.0 <= v <= 1.0 for v in self.series[self.primary_series]):
            raise ValueError("primary_series values must be within [0, 1]")
        if any(not 0.0 <= e.t <= self.duration_s for e in self.events):
            raise ValueError("event outside the video")
        return self
