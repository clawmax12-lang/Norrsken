"""A routing fake Gemini backend for panel tests (never used by application code)."""

import asyncio
import json
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

from preflight.contracts import SimulationResult
from preflight.llm import GeminiClient
from preflight.llm.backend import BackendResponse, JsonSchema
from preflight.llm.parts import Part, TextPart
from preflight.ports import SimulationRequest
from preflight.simulators.gemini_panel import GeminiViewerPanel
from preflight.simulators.gemini_panel.prompts import PERSONA_SYSTEM_PROMPT
from tests.factories import SHA, make_brief, make_concept

LABELS = ("Skeptical founder", "Busy founder", "Curious founder")


def persona_set_json() -> str:
    personas = [
        {"label": label, "description": f"{label} description", "looks_for": f"{label} wants"}
        for label in LABELS
    ]
    return json.dumps({"personas": personas})


def rating_json(
    goal_fit: Callable[[int], float] = lambda s: 0.5,
    clarity: Callable[[int], float] = lambda s: 0.4,
    moments: Sequence[tuple[str, str, str]] = (),
    seconds: int = 15,
) -> str:
    return json.dumps(
        {
            "seconds": [
                {"second": s, "goal_fit": goal_fit(s), "clarity": clarity(s)}
                for s in range(seconds)
            ],
            "moments": [{"timestamp": t, "kind": k, "label": label} for t, k, label in moments],
        }
    )


class FakePanelBackend:
    """Answers persona derivation and per-persona ratings, keyed by persona label."""

    def __init__(self, ratings: Mapping[str, str | Exception] | None = None) -> None:
        default = {label: rating_json() for label in LABELS}
        self.ratings = {**default, **(ratings or {})}
        self.persona_calls = 0
        self.rating_calls: list[tuple[str, tuple[Part, ...]]] = []
        self.in_flight = 0
        self.max_in_flight = 0
        self.persona_error: Exception | None = None

    async def generate(
        self,
        *,
        model: str,
        system: str,
        parts: Sequence[Part],
        response_schema: JsonSchema,
        temperature: float,
    ) -> BackendResponse:
        if system == PERSONA_SYSTEM_PROMPT:
            self.persona_calls += 1
            if self.persona_error:
                raise self.persona_error
            return BackendResponse(persona_set_json(), 10, 5)
        self.rating_calls.append((system, tuple(parts)))
        self.in_flight += 1
        self.max_in_flight = max(self.max_in_flight, self.in_flight)
        try:
            await asyncio.sleep(0)
            return self._rating_for(parts)
        finally:
            self.in_flight -= 1

    def _rating_for(self, parts: Sequence[Part]) -> BackendResponse:
        text = "\n".join(p.text for p in parts if isinstance(p, TextPart))
        label = next(label for label in LABELS if f"label: {label}" in text)
        answer = self.ratings[label]
        if isinstance(answer, Exception):
            raise answer
        return BackendResponse(answer, 1000, 200)

    async def count_text_tokens(self, *, model: str, text: str) -> int:
        return len(text.split())


def make_panel(backend: FakePanelBackend, **kwargs) -> GeminiViewerPanel:
    return GeminiViewerPanel(GeminiClient(backend, "gemini-test", retry_delay_s=0), **kwargs)


def make_request(tmp_path: Path, variant_id: str = "A", **brief_overrides) -> SimulationRequest:
    video = tmp_path / f"{variant_id}.mp4"
    video.write_bytes(b"fake-mp4-bytes")
    return SimulationRequest(
        brief=make_brief(**brief_overrides),
        concept=make_concept(variant_id),
        video_path=video,
        video_sha256=SHA,
        artifacts_dir=tmp_path,
    )


def assert_valid(result: SimulationResult) -> None:
    """Round-trip through the contract to prove it is serialisable and strict-valid."""
    assert SimulationResult.model_validate_json(result.model_dump_json()) == result
