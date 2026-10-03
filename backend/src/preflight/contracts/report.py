"""FR-06, FR-08, FR-10: reasons, token savings and the exported report."""

from typing import Annotated, Self

from pydantic import Field, computed_field, model_validator

from ._base import Contract
from .concept import VariantId


class Reason(Contract):
    """A timestamped reason tied to a scene that is on screen at that moment."""

    t: Annotated[float, Field(ge=0)]
    scene_index: Annotated[int, Field(ge=0)]
    text: Annotated[str, Field(min_length=1)]


class TokenSavings(Contract):
    """Measured Condense usage. Never estimated; zero calls means zero savings."""

    calls: Annotated[int, Field(ge=0)] = 0
    input_tokens_original: Annotated[int, Field(ge=0)] = 0
    input_tokens_sent: Annotated[int, Field(ge=0)] = 0
    output_tokens: Annotated[int, Field(ge=0)] = 0

    @model_validator(mode="after")
    def _sent_not_above_original(self) -> Self:
        if self.input_tokens_sent > self.input_tokens_original:
            raise ValueError("sent tokens cannot exceed original tokens")
        return self

    @computed_field  # type: ignore[prop-decorator]
    @property
    def tokens_saved(self) -> int:
        """Input tokens that were not sent thanks to compression."""
        return self.input_tokens_original - self.input_tokens_sent

    @computed_field  # type: ignore[prop-decorator]
    @property
    def percent(self) -> float:
        """Share of input tokens saved, 0-100 (0 when nothing was sent)."""
        if self.input_tokens_original == 0:
            return 0.0
        return round(100.0 * self.tokens_saved / self.input_tokens_original, 1)


class Report(Contract):
    """What the founder downloads as ``report.json`` (PRD §10.3 ``Report``)."""

    winner: VariantId
    runner_up: VariantId | None
    reasons: dict[VariantId, tuple[Reason, ...]]
    next_time: tuple[Annotated[str, Field(min_length=1)], ...]
    token_savings: TokenSavings
    brain_sim: Annotated[bool, Field(description="False renders as 'Brain sim off'.")]
