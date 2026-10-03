"""What Gemini returns for the viewer panel, and the checks that need the video length.

These are provider output models: they stop at the adapter and are translated into the shared
``SimulationResult`` (see :mod:`.aggregate`).
"""

import re
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from preflight.contracts import EventType

PERSONA_COUNT = 3
MAX_MOMENTS = 6
_TIMESTAMP = re.compile(r"^(\d{1,2}):([0-5]\d)$")

Rating = Annotated[float, Field(ge=0.0, le=1.0)]


class _Output(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


class Persona(_Output):
    """A fictional archetype of the audience. Never a real person."""

    label: Annotated[str, Field(min_length=1, max_length=60)]
    description: Annotated[str, Field(min_length=1, max_length=400)]
    looks_for: Annotated[str, Field(min_length=1, max_length=200)]


class PersonaSet(_Output):
    """Exactly :data:`PERSONA_COUNT` personas derived from the audience text."""

    personas: Annotated[
        tuple[Persona, ...], Field(min_length=PERSONA_COUNT, max_length=PERSONA_COUNT)
    ]


class SecondRating(_Output):
    """One simulated viewer's rating of the second ``[second, second + 1)``."""

    second: Annotated[int, Field(ge=0)]
    goal_fit: Rating
    clarity: Rating


class MomentFlag(_Output):
    """A moment where the simulated viewer would hold on or drop off."""

    timestamp: Annotated[str, Field(description="mm:ss from the start of the video")]
    kind: EventType
    label: Annotated[str, Field(min_length=1, max_length=120)]


class PersonaRating(_Output):
    """One persona's whole answer for one video."""

    seconds: tuple[SecondRating, ...]
    moments: Annotated[tuple[MomentFlag, ...], Field(max_length=MAX_MOMENTS)]


def parse_timestamp(text: str) -> int | None:
    """Seconds for an ``mm:ss`` timestamp, or ``None`` when it is not one."""
    match = _TIMESTAMP.fullmatch(text.strip())
    return int(match.group(1)) * 60 + int(match.group(2)) if match else None


def rating_problems(rating: PersonaRating, duration_s: int) -> list[str]:
    """Reasons ``rating`` cannot be used for a ``duration_s``-second video, phrased for repair."""
    problems: list[str] = []
    seconds = sorted(entry.second for entry in rating.seconds)
    if seconds != list(range(duration_s)):
        problems.append(
            f"seconds must contain exactly one rating for each of 0..{duration_s - 1}, "
            f"got {seconds}"
        )
    for moment in rating.moments:
        at = parse_timestamp(moment.timestamp)
        if at is None or at > duration_s:
            problems.append(
                f'moment timestamp "{moment.timestamp}" must be mm:ss within the first '
                f"{duration_s} seconds"
            )
    return problems
