"""``GeminiViewerPanel``: FR-04's Gemini simulator behind the shared ``Simulator`` port.

Three fictional personas are derived once per audience, then each one "watches" the rendered
MP4 through Gemini and rates every second. Their answers are aggregated into one
``SimulationResult``. The ratings come from a language model reacting to the video; they are a
simulated panel's judgement, not measured viewer behaviour.
"""

import asyncio
import hashlib
import logging

from preflight.contracts import Brief, SimulationResult, SimulatorName
from preflight.errors import PreflightError, ProviderError
from preflight.llm import CallUsage, GeminiClient, MediaPart
from preflight.ports import SimulationRequest

from .aggregate import PersonaReading, reading_from, to_result
from .prompts import (
    PANEL_PROMPT_VERSION,
    PERSONA_SYSTEM_PROMPT,
    RATING_SYSTEM_PROMPT,
    persona_parts,
    rating_parts,
)
from .schemas import Persona, PersonaRating, PersonaSet, rating_problems

logger = logging.getLogger(__name__)

DEFAULT_MAX_CONCURRENCY = 3


class GeminiViewerPanel:
    """Implements ``ports.Simulator`` with three Gemini personas."""

    name = SimulatorName.GEMINI_PANEL

    def __init__(
        self, client: GeminiClient, *, max_concurrency: int = DEFAULT_MAX_CONCURRENCY
    ) -> None:
        """``max_concurrency`` bounds simultaneous video calls across all variants."""
        self._client = client
        self._slots = asyncio.Semaphore(max_concurrency)
        self._personas: dict[str, tuple[Persona, ...]] = {}
        self._personas_lock = asyncio.Lock()

    @property
    def version(self) -> str:
        """Model id plus prompt version: results from different wording are not comparable."""
        return f"{self._client.model}+{PANEL_PROMPT_VERSION}"

    async def simulate(self, request: SimulationRequest) -> SimulationResult:
        """Rate ``request.video_path`` with every persona and aggregate the answers.

        A persona whose call or answer fails is logged and left out; the others still count.

        Raises:
            ProviderError: every persona failed to rate the video.
            PreflightValidationError: the video is not a supported media type, or the
                personas could not be derived.
        """
        video = await asyncio.to_thread(MediaPart.from_file, request.video_path)
        personas = await self._personas_for(request.brief)
        duration_s = int(request.concept.duration_s)
        outcomes = await asyncio.gather(
            *(
                self._rate(index, persona, request.brief, video, duration_s)
                for index, persona in enumerate(personas, start=1)
            )
        )
        rated = [outcome for outcome in outcomes if outcome is not None]
        if not rated:
            raise ProviderError("every viewer persona failed to rate the video")
        readings = [reading for reading, _ in rated]
        usage = sum((usage for _, usage in rated), CallUsage())
        return to_result(
            readings,
            variant_id=request.concept.variant_id,
            video_sha256=request.video_sha256,
            duration_s=float(duration_s),
            version=self.version,
            meta=_meta(personas, readings, usage),
        )

    async def _personas_for(self, brief: Brief) -> tuple[Persona, ...]:
        """Personas for ``brief.audience``, derived at most once however many variants ask."""
        key = _audience_hash(brief.audience, self.version)
        async with self._personas_lock:
            if key not in self._personas:
                derived = await self._client.generate_json(
                    PersonaSet, PERSONA_SYSTEM_PROMPT, persona_parts(brief)
                )
                self._personas[key] = derived.personas
            return self._personas[key]

    async def _rate(
        self, index: int, persona: Persona, brief: Brief, video: MediaPart, duration_s: int
    ) -> tuple[PersonaReading, CallUsage] | None:
        parts = rating_parts(brief, persona, video, duration_s)
        try:
            async with self._slots:
                measured = await self._client.generate_json_measured(
                    PersonaRating,
                    RATING_SYSTEM_PROMPT,
                    parts,
                    validate=lambda rating: rating_problems(rating, duration_s),
                )
        except PreflightError as exc:
            logger.warning(
                "Persona %d (%s) failed, continuing without it: %s", index, persona.label, exc
            )
            return None
        return reading_from(index, persona, measured.value), measured.usage


def _audience_hash(audience: str, version: str) -> str:
    return hashlib.sha256(f"{version}\0{audience}".encode()).hexdigest()


def _meta(
    personas: tuple[Persona, ...], readings: list[PersonaReading], usage: CallUsage
) -> dict[str, object]:
    rated = {reading.index for reading in readings}
    return {
        "personas": [
            {
                "index": index,
                "label": persona.label,
                "description": persona.description,
                "looks_for": persona.looks_for,
                "rated": index in rated,
            }
            for index, persona in enumerate(personas, start=1)
        ],
        "usage": {"input_tokens": usage.input_tokens, "output_tokens": usage.output_tokens},
    }
