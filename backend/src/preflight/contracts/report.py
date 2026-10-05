"""FR-06, FR-08, FR-10: reasons, token savings and the exported report."""

from typing import Annotated, Self

from pydantic import Field, computed_field, model_validator

from ._base import Contract
from .concept import VariantId

_DERIVED_FIELDS = frozenset({"tokens_saved", "percent"})


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

    @model_validator(mode="before")
    @classmethod
    def _drop_derived_fields(cls, data: object) -> object:
        """Accept our own serialised form: derived fields are written out but never input."""
        if isinstance(data, dict):
            return {k: v for k, v in data.items() if k not in _DERIVED_FIELDS}
        return data

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


class PlanNotes(Contract):
    """What the planner observed that the customer should act on (``plan_notes.json``).

    ``excluded_screenshots`` are zero-based indexes left out of every video because they do
    not show the customer's product; ``messages`` are shown in the log and the report.
    """

    excluded_screenshots: tuple[Annotated[int, Field(ge=0)], ...] = ()
    messages: tuple[Annotated[str, Field(min_length=1)], ...] = ()
    smallest_screen_px: (
        Annotated[
            int,
            Field(
                ge=1, description="Width in source pixels of the smallest screen the videos use."
            ),
        ]
        | None
    ) = None


class Production(Contract):
    """A known production limit that caps the absolute score; it never changes the order.

    Every variant uses the same screenshots, so ``factor`` is the same for all of them.
    """

    factor: Annotated[float, Field(ge=0, le=1)]
    reasons: tuple[Annotated[str, Field(min_length=1)], ...] = ()


class Craft(Contract):
    """Measured pace and sound of one cut: how often something happens and how it is heard.

    ``events_per_s`` counts the spec's beats (cuts, landing words, taps, punch-ins) over the
    body before the end card; ``longest_still_s`` is the longest stretch between two of them.
    ``voice_coverage`` and ``integrated_lufs`` come from the finished soundtrack, when there
    is one. ``issues`` are advice lines in the brief's language for anything off target.
    """

    events_per_s: Annotated[float, Field(ge=0)]
    longest_still_s: Annotated[float, Field(ge=0)]
    voice_coverage: Annotated[float, Field(ge=0, le=1)] | None = None
    integrated_lufs: float | None = None
    issues: tuple[Annotated[str, Field(min_length=1)], ...] = ()


class Report(Contract):
    """What the founder downloads as ``report.json`` (PRD §10.3 ``Report``)."""

    winner: VariantId
    runner_up: VariantId | None
    reasons: dict[VariantId, tuple[Reason, ...]]
    next_time: tuple[Annotated[str, Field(min_length=1)], ...]
    token_savings: TokenSavings
    brain_sim: Annotated[bool, Field(description="False renders as 'Brain sim off'.")]
    production: Production | None = None
    craft: dict[VariantId, Craft] = Field(default_factory=dict)
