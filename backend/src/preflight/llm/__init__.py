"""Gemini access through Condense, with measured usage (FR-10).

Generations go through the Condense proxy to Gemini's OpenAI-compatible endpoint (verified
live with our keys; see :mod:`preflight.llm.condense_proxy`), falling back to calling Gemini
directly on any proxy failure. Large text context marked ``compressible`` is also shortened
with ``/v1/compress``; see :mod:`preflight.llm.condense`.
"""

from .backend import GeminiBackend
from .client import GeminiClient, Measured
from .condense import CondenseCompressor, ContextCompressor
from .condense_proxy import CondenseProxyBackend, condense_session_id
from .factory import build_gemini_client
from .genai_backend import GenAIBackend
from .ledger import CallUsage, TokenLedger
from .parts import MediaPart, Part, TextPart, data_block

__all__ = [
    "CallUsage",
    "CondenseCompressor",
    "CondenseProxyBackend",
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
    "condense_session_id",
    "data_block",
]
