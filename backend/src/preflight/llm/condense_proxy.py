"""Gemini through the Condense proxy (FR-10), verified live with our keys on 2026-10-03.

Condense's OpenAI-dialect route compacts each request and forwards it to Gemini's
OpenAI-compatible endpoint when ``X-Condense-Upstream-Url`` points there. Verified: text,
PNG and MP4 parts (as ``image_url`` data URIs) and ``response_format`` JSON schemas all
round-trip, and ``prompt_tokens`` drops against the same request sent directly.

The proxy rewrites user content: all text parts are concatenated without separators and all
media moves after the text (observed by echoing what it forwards). So the user message is
built in that shape already, joined with blank lines and with each media part referenced by
its position, and interleaved labels such as "Screenshot index 0:" keep their meaning.

Condense reports no savings, so they are measured. Before each call the original request is
counted with Gemini's free ``countTokens``; the proxied answer's ``prompt_tokens`` is what was
sent. Measured live, ``countTokens`` equals what Gemini bills for text and images but
overcounts video, so requests with video are recorded as Condense calls that saved nothing.

Any proxy failure falls back to the direct backend, so Condense can never stop a run.
"""

import base64
import logging
import uuid
from collections.abc import Sequence
from dataclasses import replace
from typing import Any

import httpx
from pydantic import SecretStr

from .backend import BackendResponse, GeminiBackend, JsonSchema
from .genai_backend import INLINE_LIMIT_BYTES
from .parts import MediaPart, Part, TextPart

logger = logging.getLogger(__name__)

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_UPSTREAM_URL = f"{GEMINI_API_BASE}/openai"
_SESSION_NAMESPACE = uuid.UUID("6f1d3c52-8a3e-4c7b-9a51-2f0e5b7d9c11")


def condense_session_id(project_id: str | None) -> str:
    """UUID grouping one project's requests in the Condense dashboard (fresh if no project)."""
    if project_id is None:
        return str(uuid.uuid4())
    return str(uuid.uuid5(_SESSION_NAMESPACE, project_id))


class CondenseProxyBackend:
    """:class:`GeminiBackend` that sends every generation through the Condense proxy."""

    def __init__(  # noqa: PLR0913 - two keys, two URLs, a session and the fallback
        self,
        http_client: httpx.AsyncClient,
        *,
        fallback: GeminiBackend,
        condense_api_key: SecretStr,
        gemini_api_key: SecretStr,
        base_url: str,
        upstream_url: str = DEFAULT_UPSTREAM_URL,
        session_id: str | None = None,
    ) -> None:
        """Use an injected (caller-owned) HTTP client; ``fallback`` calls Gemini directly."""
        self._http = http_client
        self._fallback = fallback
        self._condense_key = condense_api_key
        self._gemini_key = gemini_api_key
        self._url = f"{base_url.rstrip('/')}/openai/v1/chat/completions"
        self._upstream_url = upstream_url
        self._session_id = session_id

    async def generate(
        self,
        *,
        model: str,
        system: str,
        parts: Sequence[Part],
        response_schema: JsonSchema,
        temperature: float,
    ) -> BackendResponse:
        """Generate through Condense; on any proxy failure, generate directly instead."""
        if any(isinstance(p, MediaPart) and len(p.data) > INLINE_LIMIT_BYTES for p in parts):
            return await self._direct(model, system, parts, response_schema, temperature)
        try:
            answer = await self._proxied(model, system, parts, response_schema, temperature)
        except (httpx.HTTPError, ValueError, LookupError, TypeError) as exc:
            logger.warning("Condense proxy failed, calling Gemini directly: %s", _describe(exc))
            return await self._direct(model, system, parts, response_schema, temperature)
        original = await self._original_input_tokens(model, system, parts, response_schema)
        return replace(answer, uncompressed_input_tokens=original or answer.input_tokens)

    async def count_text_tokens(self, *, model: str, text: str) -> int:
        """Count with the direct backend; counting is free and never proxied."""
        return await self._fallback.count_text_tokens(model=model, text=text)

    async def _direct(
        self,
        model: str,
        system: str,
        parts: Sequence[Part],
        response_schema: JsonSchema,
        temperature: float,
    ) -> BackendResponse:
        return await self._fallback.generate(
            model=model,
            system=system,
            parts=parts,
            response_schema=response_schema,
            temperature=temperature,
        )

    async def _proxied(
        self,
        model: str,
        system: str,
        parts: Sequence[Part],
        response_schema: JsonSchema,
        temperature: float,
    ) -> BackendResponse:
        headers = {
            "X-Condense-Auth-Token": self._condense_key.get_secret_value(),
            "Authorization": f"Bearer {self._gemini_key.get_secret_value()}",
            "X-Condense-Upstream-Url": self._upstream_url,
        }
        if self._session_id:
            headers["X-Condense-Session-Id"] = self._session_id
        body = {
            "model": model,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": _openai_content(parts)},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "answer", "schema": response_schema},
            },
        }
        response = await self._http.post(self._url, headers=headers, json=body)
        response.raise_for_status()
        return _to_backend_response(response.json())

    async def _original_input_tokens(
        self, model: str, system: str, parts: Sequence[Part], response_schema: JsonSchema
    ) -> int | None:
        """What the request would cost sent directly, or ``None`` when it cannot be known."""
        if any(isinstance(p, MediaPart) and p.mime_type.startswith("video/") for p in parts):
            return None
        request = {
            "model": f"models/{model}",
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [_gemini_part(p) for p in parts]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseJsonSchema": response_schema,
            },
        }
        try:
            response = await self._http.post(
                f"{GEMINI_API_BASE}/models/{model}:countTokens",
                headers={"x-goog-api-key": self._gemini_key.get_secret_value()},
                json={"generateContentRequest": request},
            )
            response.raise_for_status()
            total = response.json()["totalTokens"]
        except (httpx.HTTPError, ValueError, LookupError, TypeError) as exc:
            logger.warning("Could not measure the uncompressed request: %s", _describe(exc))
            return None
        return total if isinstance(total, int) else None


def _openai_content(parts: Sequence[Part]) -> list[dict[str, Any]]:
    """One text part with numbered media references, then the media in the same order."""
    texts: list[str] = []
    media: list[MediaPart] = []
    for part in parts:
        if isinstance(part, TextPart):
            texts.append(part.text)
        else:
            media.append(part)
            kind = "video" if part.mime_type.startswith("video/") else "image"
            texts.append(f"[Attachment {len(media)}: the {_ordinal(len(media))} {kind} attached]")
    attachments = [{"type": "image_url", "image_url": {"url": _data_uri(m)}} for m in media]
    return [{"type": "text", "text": "\n\n".join(texts)}, *attachments]


def _ordinal(n: int) -> str:
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def _gemini_part(part: Part) -> dict[str, Any]:
    if isinstance(part, TextPart):
        return {"text": part.text}
    data = base64.b64encode(part.data).decode("ascii")
    return {"inlineData": {"mimeType": part.mime_type, "data": data}}


def _data_uri(media: MediaPart) -> str:
    return f"data:{media.mime_type};base64,{base64.b64encode(media.data).decode('ascii')}"


def _to_backend_response(payload: Any) -> BackendResponse:  # noqa: ANN401 - raw JSON
    """Parse an OpenAI-shaped answer; anything unexpected raises so the caller falls back."""
    text = payload["choices"][0]["message"]["content"]
    usage = payload["usage"]
    prompt, total = usage["prompt_tokens"], usage["total_tokens"]
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Condense proxy returned no text")
    if not isinstance(prompt, int) or not isinstance(total, int):
        raise ValueError("Condense proxy returned no usage")
    return BackendResponse(text, input_tokens=prompt, output_tokens=max(total - prompt, 0))


def _describe(exc: Exception) -> str:
    """A log line that never contains request headers (and so never a key)."""
    if isinstance(exc, httpx.HTTPStatusError):
        return f"HTTP {exc.response.status_code}"
    return type(exc).__name__
