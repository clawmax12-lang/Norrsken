"""Condense context compression (FR-10) over the documented ``POST /v1/compress`` endpoint.

What is verified (Condense docs, researched 2026-10-03): ``/v1/compress`` takes
``{"model", "messages", "compression_rate"}`` with header ``X-Condense-Auth-Token`` and
returns the same number of messages with surviving text verbatim. What is NOT verified:
Condense documents proxy routes for Anthropic and OpenAI only, with no Gemini route, no
statement about image or video parts, and no usage fields in any response. So Gemini calls
are not proxied; only large text context is compressed here and then sent to Gemini
directly, and savings are measured by us (see :class:`TokenLedger`).

Compression is an optimisation, never a dependency: with no key, a short text, an HTTP
error, a timeout or a malformed answer, the caller gets ``None`` and sends the original.
"""

import logging
from typing import Protocol

import httpx
from pydantic import SecretStr

logger = logging.getLogger(__name__)

COMPRESS_MODEL = "helene-1"
DEFAULT_MIN_CHARS = 1500
_AUTH_HEADER = "X-Condense-Auth-Token"


class ContextCompressor(Protocol):
    """Shortens one text; ``None`` means "send the original"."""

    async def compress(self, text: str) -> str | None:
        """Return the shortened text, or ``None`` when it was not compressed."""
        ...


class CondenseCompressor:
    """:class:`ContextCompressor` backed by Condense's ``/v1/compress`` endpoint."""

    def __init__(
        self,
        http_client: httpx.AsyncClient,
        *,
        api_key: SecretStr | None,
        base_url: str,
        compression_rate: float,
        min_chars: int = DEFAULT_MIN_CHARS,
    ) -> None:
        """Use an injected (caller-owned) HTTP client; texts shorter than ``min_chars`` skip."""
        self._http = http_client
        self._api_key = api_key
        self._url = f"{base_url.rstrip('/')}/v1/compress"
        self._compression_rate = compression_rate
        self._min_chars = min_chars

    async def compress(self, text: str) -> str | None:
        """Return the compressed text, or ``None`` when it was not (or could not be) compressed."""
        if self._api_key is None or len(text) < self._min_chars:
            return None
        try:
            response = await self._http.post(
                self._url,
                headers={_AUTH_HEADER: self._api_key.get_secret_value()},
                json={
                    "model": COMPRESS_MODEL,
                    "compression_rate": self._compression_rate,
                    "messages": [{"role": "user", "content": text}],
                },
            )
            response.raise_for_status()
            return _compressed_text(response.json())
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("Condense compression skipped, sending original: %s", _describe(exc))
            return None


def _compressed_text(payload: object) -> str:
    """Extract the single compressed message; anything else is a malformed answer."""
    messages = payload.get("messages") if isinstance(payload, dict) else None
    first = messages[0] if isinstance(messages, list) and len(messages) == 1 else None
    content = first.get("content") if isinstance(first, dict) else None
    if not isinstance(content, str) or not content.strip():
        raise ValueError("unexpected /v1/compress response shape")
    return content


def _describe(exc: Exception) -> str:
    """A log line that never contains request headers (and so never the key)."""
    if isinstance(exc, httpx.HTTPStatusError):
        retry_after = exc.response.headers.get("Retry-After")
        suffix = f", retry-after {retry_after}" if retry_after else ""
        return f"HTTP {exc.response.status_code}{suffix}"
    return type(exc).__name__
