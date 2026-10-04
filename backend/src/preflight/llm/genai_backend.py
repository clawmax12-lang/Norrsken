"""The only module that imports ``google-genai`` (installed: 2.28.0).

Built on ``client.aio.models.generate_content``, ``count_tokens`` and the Files API, all
verified present in the installed SDK. Google's docs recommend the Interactions API for new
work; ``client.aio.interactions`` also exists, but its request and response are untyped
(``Any``), so a future move is one new class implementing :class:`GeminiBackend`.
"""

import asyncio
import io
import logging
import re
from collections.abc import Awaitable, Callable, Iterator, Sequence
from contextlib import contextmanager

import httpx
from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from preflight.errors import ProviderError, TransientProviderError

from .backend import BackendResponse, JsonSchema, SpeechAudio
from .parts import MediaPart, Part, TextPart

logger = logging.getLogger(__name__)

INLINE_LIMIT_BYTES = 20 * 1024 * 1024
DEFAULT_SPEECH_RATE_HZ = 24_000
_TRANSIENT_STATUS = frozenset({408, 429})
_SERVER_ERROR_FLOOR = 500


@contextmanager
def _mapped_provider_errors() -> Iterator[None]:
    """Translate SDK and transport failures into ``preflight.errors`` (no SDK type escapes)."""
    try:
        yield
    except genai_errors.APIError as exc:
        transient = exc.code in _TRANSIENT_STATUS or exc.code >= _SERVER_ERROR_FLOOR
        error_type = TransientProviderError if transient else ProviderError
        raise error_type(f"Gemini API error {exc.code}: {exc.message}") from exc
    except (httpx.TransportError, TimeoutError) as exc:
        raise TransientProviderError(f"Gemini request failed: {type(exc).__name__}") from exc


class GenAIBackend:
    """:class:`GeminiBackend` over the ``google-genai`` async client."""

    def __init__(
        self,
        client: genai.Client,
        *,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
        poll_interval_s: float = 2.0,
        max_polls: int = 60,
    ) -> None:
        """Wrap an injected SDK client; ``sleep`` is injectable so tests do not wait."""
        self._client = client
        self._sleep = sleep
        self._poll_interval_s = poll_interval_s
        self._max_polls = max_polls

    @classmethod
    def from_api_key(cls, api_key: str, *, timeout_s: float = 120.0) -> "GenAIBackend":
        """Build the production backend; ``timeout_s`` bounds every HTTP request."""
        options = types.HttpOptions(timeout=int(timeout_s * 1000))
        return cls(genai.Client(api_key=api_key, http_options=options))

    async def generate(
        self,
        *,
        model: str,
        system: str,
        parts: Sequence[Part],
        response_schema: JsonSchema,
        temperature: float,
    ) -> BackendResponse:
        """Ask for JSON matching ``response_schema``; media over 20 MB goes through Files."""
        contents = types.Content(role="user", parts=[await self._sdk_part(p) for p in parts])
        config = types.GenerateContentConfig(
            system_instruction=system,
            temperature=temperature,
            response_mime_type="application/json",
            response_json_schema=response_schema,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )
        with _mapped_provider_errors():
            response = await self._client.aio.models.generate_content(
                model=model, contents=contents, config=config
            )
        return _to_backend_response(response)

    async def synthesize_speech(
        self, *, model: str, text: str, voice: str, style: str | None = None
    ) -> SpeechAudio:
        """Speak ``text`` with a prebuilt voice; Gemini answers with raw 16-bit mono PCM."""
        prebuilt = types.PrebuiltVoiceConfig(voice_name=voice)
        part = types.Part(
            text=text,
            speech_metadata=types.SpeechMetadata(style=style) if style else None,
        )
        contents = types.Content(role="user", parts=[part])
        config = types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(prebuilt_voice_config=prebuilt)
            ),
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )
        with _mapped_provider_errors():
            response = await self._client.aio.models.generate_content(
                model=model, contents=contents, config=config
            )
        return _to_speech_audio(response)

    async def count_text_tokens(self, *, model: str, text: str) -> int:
        """Count ``text`` with the Gemini tokenizer (a free, side-effect-free API call)."""
        with _mapped_provider_errors():
            counted = await self._client.aio.models.count_tokens(model=model, contents=text)
        if counted.total_tokens is None:
            raise ProviderError("Gemini count_tokens returned no total")
        return counted.total_tokens

    async def _sdk_part(self, part: Part) -> types.Part:
        if isinstance(part, TextPart):
            return types.Part.from_text(text=part.text)
        if len(part.data) <= INLINE_LIMIT_BYTES:
            return types.Part.from_bytes(data=part.data, mime_type=part.mime_type)
        return types.Part.from_uri(file_uri=await self._upload(part), mime_type=part.mime_type)

    async def _upload(self, media: MediaPart) -> str:
        """Upload through the Files API and wait until Gemini has processed the file."""
        config = types.UploadFileConfig(mime_type=media.mime_type)
        with _mapped_provider_errors():
            uploaded = await self._client.aio.files.upload(
                file=io.BytesIO(media.data), config=config
            )
            for _ in range(self._max_polls):
                if uploaded.state != types.FileState.PROCESSING:
                    break
                await self._sleep(self._poll_interval_s)
                uploaded = await self._client.aio.files.get(name=_required(uploaded.name))
            else:
                raise TransientProviderError("uploaded file still processing after the poll limit")
        if uploaded.state == types.FileState.FAILED:
            raise ProviderError("Gemini could not process the uploaded file")
        return _required(uploaded.uri)


def _required(value: str | None) -> str:
    if not value:
        raise ProviderError("Gemini Files API response is missing a name or uri")
    return value


def _to_backend_response(response: types.GenerateContentResponse) -> BackendResponse:
    if not response.text:
        raise ProviderError(f"Gemini returned no text ({_empty_reason(response)})")
    usage = response.usage_metadata
    if usage is None:
        logger.warning("Gemini response carried no usage metadata; recording zero tokens")
        return BackendResponse(response.text, 0, 0)
    output = (usage.candidates_token_count or 0) + (usage.thoughts_token_count or 0)
    return BackendResponse(response.text, usage.prompt_token_count or 0, output)


def _to_speech_audio(response: types.GenerateContentResponse) -> SpeechAudio:
    """Extract the PCM part; its mime type (``audio/L16;rate=24000``) carries the sample rate."""
    inline = next(
        (p.inline_data for p in _response_parts(response) if p.inline_data and p.inline_data.data),
        None,
    )
    if inline is None or not inline.data:
        raise ProviderError(f"Gemini returned no audio ({_empty_reason(response)})")
    usage = response.usage_metadata
    return SpeechAudio(
        pcm=inline.data,
        sample_rate=_sample_rate(inline.mime_type),
        input_tokens=(usage.prompt_token_count or 0) if usage else 0,
        output_tokens=(usage.candidates_token_count or 0) if usage else 0,
    )


def _response_parts(response: types.GenerateContentResponse) -> list[types.Part]:
    candidates = response.candidates or []
    content = candidates[0].content if candidates else None
    return (content.parts or []) if content else []


def _sample_rate(mime_type: str | None) -> int:
    """Rate from ``audio/L16;codec=pcm;rate=24000``; Gemini TTS documents 24 kHz as the default."""
    match = re.search(r"rate=(\d+)", mime_type or "")
    return int(match.group(1)) if match else DEFAULT_SPEECH_RATE_HZ


def _empty_reason(response: types.GenerateContentResponse) -> str:
    feedback = response.prompt_feedback
    if feedback is not None and feedback.block_reason is not None:
        return f"prompt blocked: {feedback.block_reason}"
    if response.candidates and response.candidates[0].finish_reason is not None:
        return f"finish reason: {response.candidates[0].finish_reason}"
    return "no candidates"
