"""Give a rendered video its sound: narration, effects and music, mixed and muxed.

Order of work: plan the soundtrack from the spec, speak the lines (if narration is on), render
music and effects, mix, then let ffmpeg master and mux. Narration is the one step that depends
on an external service, so a failure there degrades to a music-and-effects cut rather than no
sound at all; anything else failing raises :class:`~preflight.errors.SoundError`.
"""

import asyncio
import logging
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from preflight.contracts import NarrationLine, SoundRecord
from preflight.errors import ProviderError, SoundError
from preflight.hashing import sha256_file
from preflight.ports import SoundRequest, SpeechClip, SpeechSynthesizer

from . import dsp
from .audio import float_to_pcm16, pcm16_to_float, resample, rms_normalise, trim_silence, write_wav
from .ffmpeg import Ffmpeg
from .mix import SpokenClip, Stereo, mix, render_effects
from .music import render_music
from .plan import BPM, SoundPlan, plan_soundtrack

_LOG = logging.getLogger(__name__)
_SPEECH_CONCURRENCY = 3
_MAX_SPEEDUP = 1.3  # beyond this speech stops sounding natural; the line is left out instead
_SPEECH_LEVEL_DBFS = -19.0
_MIX_FILE = "mix.wav"


@dataclass(frozen=True)
class _Narration:
    """The lines that were actually spoken, ready to mix, with what they cost."""

    clips: list[SpokenClip]
    lines: tuple[NarrationLine, ...]
    input_tokens: int
    output_tokens: int


_NO_NARRATION = _Narration([], (), 0, 0)


class SoundStudio:
    """Implements :class:`preflight.ports.SoundFinisher`."""

    def __init__(
        self,
        ffmpeg: Ffmpeg,
        speech: SpeechSynthesizer | None,
        *,
        voice: str | None = None,
        tts_model: str | None = None,
    ) -> None:
        """``speech=None`` means narration is off; ``voice`` and ``tts_model`` are recorded."""
        self._ffmpeg = ffmpeg
        self._speech = speech
        self._voice = voice
        self._tts_model = tts_model

    async def finish(self, request: SoundRequest) -> SoundRecord:
        """Produce ``request.output_path``: the same picture with sound.

        Raises:
            SoundError: ffmpeg is missing or fails, or the result does not verify.
        """
        plan = plan_soundtrack(request.spec)
        narration, note = await self._narrate(plan)
        bed = await asyncio.to_thread(_render_bed, plan, narration.clips)
        request.work_dir.mkdir(parents=True, exist_ok=True)
        mix_path = request.work_dir / _MIX_FILE
        await asyncio.to_thread(write_wav, mix_path, bed, dsp.SAMPLE_RATE)
        loudness = await self._ffmpeg.master_and_mux(
            request.video_path, mix_path, request.output_path
        )
        spoken = bool(narration.lines)
        return SoundRecord(
            variant_id=request.spec.variant_id,
            tested_video_sha256=request.video_sha256,
            final_video_sha256=await asyncio.to_thread(sha256_file, request.output_path),
            final_video_path=request.output_path.name,
            narrated=spoken,
            voice=self._voice if spoken else None,
            tts_model=self._tts_model if spoken else None,
            narration=narration.lines,
            cues=plan.cues,
            bpm=BPM,
            integrated_lufs=loudness.integrated_lufs,
            true_peak_dbtp=loudness.true_peak_dbtp,
            tts_input_tokens=narration.input_tokens,
            tts_output_tokens=narration.output_tokens,
            note=note or (None if spoken else "No line fit its scene; music and effects only."),
        )

    async def _narrate(self, plan: SoundPlan) -> tuple[_Narration, str | None]:
        """Speak the lines; on a provider or ffmpeg failure return no narration and say why."""
        if self._speech is None:
            return _NO_NARRATION, "Narration is off."
        try:
            return await self._speak(self._speech, plan.lines), None
        except (ProviderError, SoundError) as exc:
            _LOG.warning("narration unavailable, using music and effects only: %s", exc)
            return _NO_NARRATION, f"Narration unavailable: {exc}"

    async def _speak(
        self, speech: SpeechSynthesizer, lines: tuple[NarrationLine, ...]
    ) -> _Narration:
        gate = asyncio.Semaphore(_SPEECH_CONCURRENCY)

        async def speak_one(line: NarrationLine) -> SpeechClip:
            async with gate:
                return await speech.synthesize(line.text)

        clips = await asyncio.gather(*(speak_one(line) for line in lines))
        fitted = await asyncio.gather(
            *(self._fit(line, clip) for line, clip in zip(lines, clips, strict=True))
        )
        spoken = [
            (line, audio) for line, audio in zip(lines, fitted, strict=True) if audio is not None
        ]
        return _Narration(
            clips=[SpokenClip(line.start_s, audio) for line, audio in spoken],
            lines=tuple(line for line, _ in spoken),
            input_tokens=sum(clip.input_tokens for clip in clips),
            output_tokens=sum(clip.output_tokens for clip in clips),
        )

    async def _fit(self, line: NarrationLine, clip: SpeechClip) -> NDArray[np.float32] | None:
        """Trim, level and resample a clip; speed it up to fit its window, or drop it."""
        samples = trim_silence(pcm16_to_float(clip.pcm))
        duration_s = len(samples) / clip.sample_rate
        if duration_s == 0.0:
            return None
        if duration_s > line.window_s:
            ratio = duration_s / line.window_s
            if ratio > _MAX_SPEEDUP:
                _LOG.warning("line %r needs %.2fx speed to fit; leaving it out", line.text, ratio)
                return None
            faster = await self._ffmpeg.stretch(float_to_pcm16(samples), clip.sample_rate, ratio)
            samples = pcm16_to_float(faster)
        return rms_normalise(
            resample(samples, clip.sample_rate, dsp.SAMPLE_RATE), _SPEECH_LEVEL_DBFS
        )


def _render_bed(plan: SoundPlan, speech: list[SpokenClip]) -> Stereo:
    """CPU-bound synthesis and mixing; runs in a worker thread."""
    return mix(render_music(plan), render_effects(plan.cues, plan.duration_s), speech)
