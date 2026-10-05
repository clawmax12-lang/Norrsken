"""Test doubles for the Gemini seam. Used only by tests."""

from collections.abc import Sequence
from typing import TYPE_CHECKING

from preflight.llm.backend import BackendResponse, JsonSchema
from preflight.llm.parts import MediaPart, Part, TextPart

if TYPE_CHECKING:
    from preflight.errors import ProviderError


class FakeGeminiBackend:
    """Replays scripted answers (or raises scripted errors) and records every call."""

    def __init__(self, *script: BackendResponse | Exception | str) -> None:
        self._script = list(script)
        self.calls: list[tuple[str, tuple[Part, ...]]] = []
        self.models: list[str] = []
        self.counted: list[str] = []
        self.count_error: ProviderError | None = None

    async def generate(
        self,
        *,
        model: str,
        system: str,
        parts: Sequence[Part],
        response_schema: JsonSchema,
        temperature: float,
    ) -> BackendResponse:
        self.calls.append((system, tuple(parts)))
        self.models.append(model)
        step = self._script.pop(0)
        if isinstance(step, Exception):
            raise step
        if isinstance(step, str):
            return BackendResponse(step, input_tokens=100, output_tokens=20)
        return step

    async def count_text_tokens(self, *, model: str, text: str) -> int:
        self.counted.append(text)
        if self.count_error:
            raise self.count_error
        return len(text.split())

    def texts(self, call: int = 0) -> list[str]:
        """Text parts of the ``call``-th generate call."""
        return [p.text for p in self.calls[call][1] if isinstance(p, TextPart)]

    def media(self, call: int = 0) -> list[MediaPart]:
        """Media parts of the ``call``-th generate call."""
        return [p for p in self.calls[call][1] if isinstance(p, MediaPart)]


class FakeCompressor:
    """Returns a fixed compression result and records what it was asked to shorten."""

    def __init__(self, result: str | None) -> None:
        self.result = result
        self.seen: list[str] = []

    async def compress(self, text: str) -> str | None:
        self.seen.append(text)
        return self.result
