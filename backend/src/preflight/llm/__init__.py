"""Gemini access with Condense context compression and measured usage (FR-10).

Gemini routing through Condense is UNVERIFIED with the vendor: Condense documents Anthropic
and OpenAI proxy routes only. We therefore call Gemini directly and use Condense's
``/v1/compress`` endpoint for large text context; see :mod:`preflight.llm.condense`.
"""

from .backend import GeminiBackend
from .client import GeminiClient, Measured
from .condense import CondenseCompressor, ContextCompressor
from .factory import build_gemini_client
from .genai_backend import GenAIBackend
from .ledger import CallUsage, TokenLedger
from .parts import MediaPart, Part, TextPart, data_block

__all__ = [
    "CallUsage",
    "CondenseCompressor",
    "ContextCompressor",
    "GeminiBackend",
    "GeminiClient",
    "GenAIBackend",
    "Measured",
    "MediaPart",
    "Part",
    "TextPart",
    "TokenLedger",
    "build_gemini_client",
    "data_block",
]
