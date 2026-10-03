"""FR-01: the customer's brief (PRD §10.3 ``Brief``)."""

from enum import StrEnum
from typing import Annotated

from pydantic import Field, field_validator

from ._base import Contract

MAX_ONE_LINER_CHARS = 140
MIN_SCREENSHOTS = 3
MAX_SCREENSHOTS = 6

NonEmpty = Annotated[str, Field(min_length=1)]


class Goal(StrEnum):
    """What the founder wants viewers to do."""

    SIGNUPS = "signups"
    DOWNLOADS = "downloads"
    UNDERSTAND = "understand"
    PURCHASE = "purchase"


class BriefField(StrEnum):
    """Brief fields that on-screen copy may be sourced from (``source_field``)."""

    PRODUCT_NAME = "product_name"
    ONE_LINER = "one_liner"
    GOAL_NOTE = "goal_note"
    AUDIENCE = "audience"


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
    brand_color: Annotated[str, Field(pattern=r"^#[0-9a-fA-F]{6}$")] | None = None
    logo: str | None = None

    @field_validator("screenshots")
    @classmethod
    def _unique_screenshots(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(set(value)) != len(value):
            raise ValueError("screenshots must be distinct files")
        return value

    def field_text(self, field: BriefField) -> str:
        """Return the text of a sourceable brief field ('' when optional and unset)."""
        return getattr(self, field.value) or ""
