"""Wiring for the production Gemini client (FR-10)."""

from typing import TYPE_CHECKING

import httpx

from preflight.config import Settings
from preflight.errors import ProviderError

from .client import GeminiClient
from .condense import CondenseCompressor
from .condense_proxy import CondenseProxyBackend, condense_session_id
from .genai_backend import GenAIBackend
from .ledger import TokenLedger

if TYPE_CHECKING:
    from .backend import GeminiBackend


def build_gemini_client(
    settings: Settings,
    *,
    ledger: TokenLedger,
    http_client: httpx.AsyncClient,
    project_id: str | None = None,
    proxy: bool = True,
) -> GeminiClient:
    """Create a client for a component; the caller owns ``http_client``'s lifetime.

    With ``CONDENSE_API_KEY`` set, generations go through the Condense proxy (unless
    ``CONDENSE_PROXY`` is off or ``proxy`` is False) and ``compressible`` text is also
    compressed; requests are grouped per ``project_id`` in the Condense dashboard. Without
    the key the client still works and the ledger reports zero savings.

    ``proxy=False`` calls Gemini directly (used for comparisons). Give every client the
    same ``ledger`` so one report covers the whole run.

    Raises:
        ProviderError: ``GEMINI_API_KEY`` is not configured, so the UI can show "not configured".
    """
    if settings.gemini_api_key is None:
        raise ProviderError("GEMINI_API_KEY is not set")
    session_id = condense_session_id(project_id)
    direct = GenAIBackend.from_api_key(settings.gemini_api_key.get_secret_value())
    backend: GeminiBackend = direct
    if proxy and settings.condense_api_key is not None and settings.condense_proxy:
        backend = CondenseProxyBackend(
            http_client,
            fallback=direct,
            condense_api_key=settings.condense_api_key,
            gemini_api_key=settings.gemini_api_key,
            base_url=settings.condense_base_url,
            upstream_url=settings.condense_upstream_url,
            session_id=session_id,
        )
    compressor = CondenseCompressor(
        http_client,
        api_key=settings.condense_api_key,
        base_url=settings.condense_base_url,
        compression_rate=settings.condense_compression_rate,
        session_id=session_id,
    )
    return GeminiClient(
        backend,
        settings.gemini_model,
        ledger=ledger,
        compressor=compressor,
        fallback_models=settings.gemini_fallback_models,
    )
