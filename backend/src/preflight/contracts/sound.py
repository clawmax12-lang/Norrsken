"""PRD §9.3: what was added to a finished video after it was pretested.

The pretest ran on the silent render. Sound is added to the exported cut afterwards, so
:class:`SoundRecord` keeps both hashes and says what was added; nothing here is, or may be
presented as, a simulated-viewer result.
"""

from enum import StrEnum
from typing import Annotated

from pydantic import Field

from ._base import SHA256_PATTERN, Contract
from .brief import BriefField, NonEmpty
from .concept import VariantId


class CueKind(StrEnum):
    """Synthesized sound effects."""

    IMPACT = "impact"
    WHOOSH = "whoosh"
    SHIMMER = "shimmer"
    TICK = "tick"


class SoundCue(Contract):
    """A sound effect whose loudest moment is at second ``t`` of the video."""

    kind: CueKind
    t: Annotated[float, Field(ge=0)]


class NarrationLine(Contract):
    """One spoken line. ``text`` is on-screen copy, so it is traceable via ``source_field``."""

    text: NonEmpty
    source_field: BriefField
    start_s: Annotated[float, Field(ge=0)]
    window_s: Annotated[float, Field(gt=0, description="Time available before the next line")]


class SoundRecord(Contract):
    """Persisted as ``sound/{variant}.json`` next to the final video.

    ``tested_video_sha256`` is the silent render the simulated viewers watched;
    ``final_video_sha256`` is the exported cut with sound. ``narrated`` is false when the
    voice step was off or failed, in which case ``note`` says why; the cut then has music and
    sound effects only. Loudness values are measured on the encoded file.
    """

    variant_id: VariantId
    tested_video_sha256: Annotated[str, Field(pattern=SHA256_PATTERN)]
    final_video_sha256: Annotated[str, Field(pattern=SHA256_PATTERN)]
    final_video_path: NonEmpty
    narrated: bool
    voice: str | None = None
    tts_model: str | None = None
    narration: tuple[NarrationLine, ...] = ()
    cues: tuple[SoundCue, ...] = ()
    bpm: Annotated[int, Field(gt=0)]
    integrated_lufs: float
    true_peak_dbtp: float
    tts_input_tokens: Annotated[int, Field(ge=0)] = 0
    tts_output_tokens: Annotated[int, Field(ge=0)] = 0
    note: str | None = None
