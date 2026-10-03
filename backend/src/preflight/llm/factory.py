"""Wiring for the production Gemini client (FR-10)."""

import httpx

from preflight.config import Settings
from preflight.errors import ProviderError

from .client import GeminiClient
from .condense import CondenseCompressor
from .genai_backend import GenAIBackend
from .ledger import TokenLedger


def build_gemini_client(
    settings: Settings, *, ledger: TokenLedger, http_client: httpx.AsyncClient
) -> GeminiClient:
    """Create the client every component shares; the caller owns ``http_client``'s lifetime.

    Condense compression is attached when ``CONDENSE_API_KEY`` is set; without it the client
    still works and the ledger reports zero savings.

    Raises:
        ProviderError: ``GEMINI_API_KEY`` is not configured, so the UI can show "not configured".
    """
    if settings.gemini_api_key is None:
        raise ProviderError("GEMINI_API_KEY is not set")
    compressor = CondenseCompressor(
        http_client,
        api_key=settings.condense_api_key,
        base_url=settings.condense_base_url,
        compression_rate=settings.condense_compression_rate,
    )
    return GeminiClient(
        GenAIBackend.from_api_key(settings.gemini_api_key.get_secret_value()),
        settings.gemini_model,
        ledger=ledger,
        compressor=compressor,
    )
