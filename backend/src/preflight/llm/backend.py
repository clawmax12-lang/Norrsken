"""The one seam between Preflight and a Gemini SDK.

``GeminiClient`` talks only to :class:`GeminiBackend`. Swapping SDK generations (for
example ``generate_content`` to the Interactions API) means writing another backend; no
other module imports the SDK.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Protocol

from .parts import Part

JsonSchema = dict[str, Any]


@dataclass(frozen=True)
class BackendResponse:
    """One model answer with the token counts the provider reported for it.

    ``output_tokens`` includes thinking tokens because the provider bills them as output.
    """

    text: str
    input_tokens: int
    output_tokens: int


class GeminiBackend(Protocol):
    """Provider operations GeminiClient needs; errors surface as ``preflight.errors``."""

    async def generate(
        self,
        *,
        model: str,
        system: str,
        parts: Sequence[Part],
        response_schema: JsonSchema,
        temperature: float,
    ) -> BackendResponse:
        """Return JSON text conforming to ``response_schema`` (not yet validated)."""
        ...

    async def count_text_tokens(self, *, model: str, text: str) -> int:
        """Count ``text`` with the model's own tokenizer."""
        ...
