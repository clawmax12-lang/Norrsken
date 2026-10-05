"""Narration through Gemini text-to-speech, with an on-disk cache.

The text sent is on-screen copy only (see :mod:`preflight.sound.plan`). A cache hit makes no
API call, so a resumed run never pays twice for the same line, and reports zero tokens for it.
"""

import asyncio
import hashlib
import logging
import re
from pathlib import Path

from preflight.errors import TransientProviderError
from preflight.llm import SpeechAudio, SpeechBackend
from preflight.ports import SpeechClip

from .audio import read_wav_mono_pcm, write_pcm_wav

# Gemini 3.8 TTS recites ``text`` verbatim. Delivery belongs in speech_metadata.style, not
# in the transcript, or the model speaks the stage direction and the line no longer fits.
DELIVERY = (
    "warm, calm and confident woman in her thirties at a steady conversational pace, sincere "
    "and gently persuasive like a premium brand ad; never loud or hyped"
)
# Gemini 2.5 and 3.1 TTS reject speech_metadata; they take the delivery as a spoken-style
# prompt and read only what follows the colon.
_PROMPTED_STYLE = ("gemini-2.5-", "gemini-3.1-")
_RETRY_WAIT_S = (0.0, 2.0, 6.0)
# A free-tier TTS model allows a few requests a minute and a few a day. A 429 that asks to
# retry within this many seconds is the minute's quota: wait on the same model rather than
# spending the fallbacks' daily quota. A longer wait means the day's quota is gone.
MAX_RATE_WAIT_S = 70.0
_RATE_WAITS = 4
_RETRY_IN = re.compile(r"retry in (?:(\d+)h)?(?:(\d+)m)?([\d.]+)s")

_LOG = logging.getLogger(__name__)


class GeminiSpeech:
    """:class:`preflight.ports.SpeechSynthesizer` over a Gemini TTS model and one voice."""

    def __init__(
        self,
        backend: SpeechBackend,
        *,
        model: str,
        voice: str,
        cache_dir: Path,
        fallback_models: tuple[str, ...] = (),
    ) -> None:
        """Speak with ``voice`` of ``model``; cached lines live in ``cache_dir``.

        When ``model`` fails transiently (quota spent, overloaded) the next of
        ``fallback_models`` speaks, and keeps speaking, so a film's lines share one model.
        """
        self._backend = backend
        self._models = (model, *(m for m in fallback_models if m != model))
        self._active = 0
        self._voice = voice
        self._cache_dir = cache_dir

    @property
    def model(self) -> str:
        """The model currently speaking."""
        return self._models[self._active]

    async def synthesize(self, text: str) -> SpeechClip:
        """Return the spoken ``text``, from the cache when this exact line was spoken before."""
        for model in self._models:
            cached = self._cache_path(model, text)
            if cached.is_file():
                pcm, rate = read_wav_mono_pcm(cached)
                return SpeechClip(pcm, rate)
        audio = await self._call(text)
        write_pcm_wav(self._cache_path(self.model, text), audio.pcm, audio.sample_rate)
        return SpeechClip(audio.pcm, audio.sample_rate, audio.input_tokens, audio.output_tokens)

    async def _call(self, text: str) -> SpeechAudio:
        last: TransientProviderError | None = None
        for wait_s in _RETRY_WAIT_S:
            if wait_s:
                await asyncio.sleep(wait_s)
            for index in range(self._active, len(self._models)):
                try:
                    audio = await self._paced(self._models[index], text)
                except TransientProviderError as exc:
                    last = exc
                    _LOG.warning("speech with %s failed: %s", self._models[index], exc)
                    continue
                if index != self._active:
                    _LOG.warning("narration falls back to %s", self._models[index])
                    self._active = index
                return audio
        if last is not None:
            raise last
        raise TransientProviderError("speech failed without a provider error")

    async def _paced(self, model: str, text: str) -> SpeechAudio:
        """``model`` speaks ``text``, waiting out its per-minute quota a few times."""
        for _ in range(_RATE_WAITS):
            try:
                return await self._speak(model, text)
            except TransientProviderError as exc:
                wait_s = rate_wait_s(exc)
                if wait_s is None:
                    raise
                _LOG.info("%s is at its per-minute quota; waiting %.0f s", model, wait_s)
                await asyncio.sleep(wait_s + 1)
        return await self._speak(model, text)

    async def _speak(self, model: str, text: str) -> SpeechAudio:
        if model.startswith(_PROMPTED_STYLE):
            return await self._backend.synthesize_speech(
                model=model, text=f"Say it like a {DELIVERY}: {text}", voice=self._voice
            )
        return await self._backend.synthesize_speech(
            model=model, text=text, voice=self._voice, style=DELIVERY
        )

    def _cache_path(self, model: str, text: str) -> Path:
        key = hashlib.sha256(f"{model}|{self._voice}|{DELIVERY}|{text}".encode()).hexdigest()
        return self._cache_dir / f"{key[:32]}.wav"


def rate_wait_s(error: Exception) -> float | None:
    """Seconds a 429 asks to wait, when that is a per-minute quota rather than the day's."""
    found = _RETRY_IN.search(str(error))
    if found is None:
        return None
    hours, minutes, seconds = found.groups()
    wait_s = int(hours or 0) * 3600 + int(minutes or 0) * 60 + float(seconds)
    return wait_s if wait_s <= MAX_RATE_WAIT_S else None
