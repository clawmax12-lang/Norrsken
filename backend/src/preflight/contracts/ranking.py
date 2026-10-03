"""FR-05: goal-aligned scores, ranking and confidence (PRD §10.3 ``Ranking``)."""

from enum import StrEnum
from typing import Annotated

from pydantic import Field

from ._base import Contract
from .concept import VariantId
from .simulation import SimulatorName


class Confidence(StrEnum):
    """High when the simulators agree on the winner, low otherwise (or with one simulator)."""

    HIGH = "high"
    LOW = "low"


class Ranking(Contract):
    """Deterministic ordering of the variants that were fully simulated.

    ``per_simulator`` keeps each simulator's normalised sub-score so a reader can see
    *why* the order came out as it did. ``excluded`` lists variants left out and why.
    """

    order: tuple[VariantId, ...]
    scores: dict[VariantId, Annotated[float, Field(ge=0, le=1)]]
    per_simulator: dict[SimulatorName, dict[VariantId, Annotated[float, Field(ge=0, le=1)]]]
    confidence: Confidence
    rule: Annotated[str, Field(min_length=1)]
    excluded: dict[VariantId, str] = Field(default_factory=dict)
