"""Narration through Gemini text-to-speech, with an on-disk cache.

The text sent is on-screen copy only (see :mod:`preflight.sound.plan`). A cache hit makes no
API call, so a resumed run never pays twice for the same line, and reports zero tokens for it.
"""

import asyncio
import hashlib
import logging
from pathlib import Path

from preflight.errors import TransientProviderError
from preflight.llm import SpeechAudio, SpeechBackend
from preflight.ports import SpeechClip

from .audio import read_wav_mono_pcm, write_pcm_wav

# Gemini 3.8 TTS recites ``text`` verbatim. Delivery belongs in speech_metadata.style, not
# in the transcript, or the model speaks the stage direction and the line no longer fits.
DELIVERY = "energetic, concise young woman, selling a short launch ad"
_RETRY_WAIT_S = (0.0, 2.0, 6.0)

_LOG = logging.getLogger(__name__)


class GeminiSpeech:
    """:class:`preflight.ports.SpeechSynthesizer` over a Gemini TTS model and one voice."""

    def __init__(self, backend: SpeechBackend, *, model: str, voice: str, cache_dir: Path) -> None:
        """Speak with ``voice`` of ``model``; cached lines live in ``cache_dir``."""
        self._backend = backend
        self._model = model
        self._voice = voice
        self._cache_dir = cache_dir

    async def synthesize(self, text: str) -> SpeechClip:
        """Return the spoken ``text``, from the cache when this exact line was spoken before."""
        cached = self._cache_path(text)
        if cached.is_file():
            pcm, rate = read_wav_mono_pcm(cached)
            return SpeechClip(pcm, rate)
        audio = await self._call(text)
        write_pcm_wav(cached, audio.pcm, audio.sample_rate)
        return SpeechClip(audio.pcm, audio.sample_rate, audio.input_tokens, audio.output_tokens)

    async def _call(self, text: str) -> SpeechAudio:
        last: TransientProviderError | None = None
        for wait_s in _RETRY_WAIT_S:
            if wait_s:
                await asyncio.sleep(wait_s)
            try:
                return await self._backend.synthesize_speech(
                    model=self._model, text=text, voice=self._voice, style=DELIVERY
                )
            except TransientProviderError as exc:
                last = exc
                _LOG.warning("speech retry after %s: %s", type(exc).__name__, exc)
        if last is not None:
            raise last
        raise TransientProviderError("speech failed without a provider error")

    def _cache_path(self, text: str) -> Path:
        key = hashlib.sha256(f"{self._model}|{self._voice}|{DELIVERY}|{text}".encode()).hexdigest()
        return self._cache_dir / f"{key[:32]}.wav"
