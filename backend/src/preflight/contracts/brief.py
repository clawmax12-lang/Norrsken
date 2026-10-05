"""FR-01: the customer's brief (PRD §10.3 ``Brief``)."""

import re
from enum import StrEnum
from typing import Annotated

from pydantic import Field, field_validator

from ._base import Contract

MAX_ONE_LINER_CHARS = 140
MAX_BUYER_CTA_CHARS = 40
MAX_PROOF_POINTS_CHARS = 400
MIN_SCREENSHOTS = 3
MAX_SCREENSHOTS = 6

NonEmpty = Annotated[str, Field(min_length=1)]

# A form's character counter pasted along with the text: "(99/140 tecken)", "(38/40)".
_COUNTER = re.compile(
    r"\s*(?:\(\s*(\d{1,4})\s*/\s*(\d{2,4})\s*(?:tecken|characters?|chars?)?\s*\)"
    r"|\b(\d{1,4})\s*/\s*(\d{2,4})\s*(?:tecken|characters?|chars?)\b)",
    re.IGNORECASE,
)


def strip_counters(text: str) -> str:
    """``text`` without pasted character counters; "24/7" and other fractions stay."""

    def drop(match: re.Match[str]) -> str:
        used, limit = (int(n) for n in (match.group(1, 2) if match.group(1) else match.group(3, 4)))
        return "" if used <= limit else match.group(0)

    return _COUNTER.sub(drop, text).strip()


class Goal(StrEnum):
    """What the founder wants viewers to do."""

    SIGNUPS = "signups"
    DOWNLOADS = "downloads"
    UNDERSTAND = "understand"
    PURCHASE = "purchase"


class RenderMode(StrEnum):
    """Which picture track to try. Default is the FR-03 Showcase template."""

    SHOWCASE = "showcase"
    GENERATIVE_MOTION = "generative_motion"


class BriefField(StrEnum):
    """Brief fields that on-screen copy may be sourced from (``source_field``)."""

    PRODUCT_NAME = "product_name"
    ONE_LINER = "one_liner"
    GOAL_NOTE = "goal_note"
    AUDIENCE = "audience"
    BUYER_CTA = "buyer_cta"
    PROOF_POINTS = "proof_points"


class Brief(Contract):
    """Validated customer input. Screenshot and logo paths are relative to the project dir."""

    project_id: NonEmpty
    product_name: NonEmpty
    one_liner: Annotated[str, Field(min_length=1, max_length=MAX_ONE_LINER_CHARS)]
    screenshots: Annotated[
        tuple[NonEmpty, ...], Field(min_length=MIN_SCREENSHOTS, max_length=MAX_SCREENSHOTS)
    ]
    goal: Goal
    goal_note: str | None = None
    audience: NonEmpty
    buyer_cta: Annotated[str, Field(max_length=MAX_BUYER_CTA_CHARS)] | None = Field(
        default=None,
        description="The action the buyer (the audience) should take, e.g. 'Kom igång gratis'.",
    )
    proof_points: Annotated[str, Field(max_length=MAX_PROOF_POINTS_CHARS)] | None = Field(
        default=None,
        description="Facts the customer asserts (numbers, integrations, customers); the only "
        "source a video may take a statistic or proof from.",
    )
    brand_color: Annotated[str, Field(pattern=r"^#[0-9a-fA-F]{6}$")] | None = None
    logo: str | None = None
    render_mode: RenderMode = RenderMode.SHOWCASE

    @field_validator(
        "one_liner", "goal_note", "audience", "buyer_cta", "proof_points", mode="before"
    )
    @classmethod
    def _without_counters(cls, value: object) -> object:
        return strip_counters(value) if isinstance(value, str) else value

    @field_validator("screenshots")
    @classmethod
    def _unique_screenshots(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(set(value)) != len(value):
            raise ValueError("screenshots must be distinct files")
        return value

    def field_text(self, field: BriefField) -> str:
        """Return the text of a sourceable brief field ('' when optional and unset)."""
        return getattr(self, field.value) or ""
