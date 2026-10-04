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
from .audio import (
    deglitch_tail,
    fade_edges,
    float_to_pcm16,
    pcm16_to_float,
    resample,
    rms_normalise,
    trim_silence,
    write_wav,
)
from .ffmpeg import Ffmpeg
from .mix import SpokenClip, Stereo, mix, render_effects
from .music import render_music
from .plan import BPM, SoundPlan, plan_motion_soundtrack, plan_soundtrack

_LOG = logging.getLogger(__name__)
_SPEECH_CONCURRENCY = 1
_MAX_SPEEDUP = 1.5  # beyond this the line is trimmed to the window instead of dropped
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
        plan = (
            plan_motion_soundtrack(request.motion_spec)
            if request.motion_spec is not None
            else plan_soundtrack(request.spec)
        )
        if request.allow_narration:
            narration, note = await self._narrate(plan)
        else:
            narration, note = _NO_NARRATION, "Narration disabled."
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
            spoken = await self._speak(self._speech, plan.lines)
        except (ProviderError, SoundError) as exc:
            _LOG.warning("narration unavailable, using music and effects only: %s", exc)
            return _NO_NARRATION, f"Narration unavailable: {exc}"
        return spoken, None

    async def _speak(
        self, speech: SpeechSynthesizer, lines: tuple[NarrationLine, ...]
    ) -> _Narration:
        gate = asyncio.Semaphore(_SPEECH_CONCURRENCY)

        async def speak_one(line: NarrationLine) -> tuple[NarrationLine, SpeechClip]:
            async with gate:
                return line, await speech.synthesize(line.text)

        outcomes = await asyncio.gather(
            *(speak_one(line) for line in lines), return_exceptions=True
        )
        kept: list[tuple[NarrationLine, SpeechClip]] = []
        tokens_in = 0
        tokens_out = 0
        last_error: Exception | None = None
        for line, outcome in zip(lines, outcomes, strict=True):
            if isinstance(outcome, Exception):
                last_error = outcome
                _LOG.warning("line %r unspoken (%s); keeping the rest", line.text, outcome)
                continue
            spoken_line, clip = outcome
            kept.append((spoken_line, clip))
            tokens_in += clip.input_tokens
            tokens_out += clip.output_tokens
        if not kept:
            if last_error is not None:
                raise last_error
            return _NO_NARRATION
        fitted = await asyncio.gather(*(self._fit(line, clip) for line, clip in kept))
        spoken = [
            (line, audio)
            for (line, _), audio in zip(kept, fitted, strict=True)
            if audio is not None
        ]
        if not spoken:
            return _NO_NARRATION
        return _Narration(
            clips=[SpokenClip(line.start_s, audio) for line, audio in spoken],
            lines=tuple(line for line, _ in spoken),
            input_tokens=tokens_in,
            output_tokens=tokens_out,
        )

    async def _fit(self, line: NarrationLine, clip: SpeechClip) -> NDArray[np.float32] | None:
        """Trim, level and resample a clip; speed or trim it so it stays inside its window."""
        samples = deglitch_tail(trim_silence(pcm16_to_float(clip.pcm)), clip.sample_rate)
        duration_s = len(samples) / clip.sample_rate
        if duration_s == 0.0:
            return None
        if duration_s > line.window_s:
            ratio = min(duration_s / line.window_s, _MAX_SPEEDUP)
            faster = await self._ffmpeg.stretch(float_to_pcm16(samples), clip.sample_rate, ratio)
            samples = pcm16_to_float(faster)
        levelled = rms_normalise(
            resample(samples, clip.sample_rate, dsp.SAMPLE_RATE), _SPEECH_LEVEL_DBFS
        )
        faded = fade_edges(levelled, dsp.SAMPLE_RATE)
        max_samples = max(1, int(line.window_s * dsp.SAMPLE_RATE))
        if len(faded) > max_samples:
            faded = fade_edges(faded[:max_samples], dsp.SAMPLE_RATE)
        return faded


def _render_bed(plan: SoundPlan, speech: list[SpokenClip]) -> Stereo:
    """CPU-bound synthesis and mixing; runs in a worker thread."""
    return mix(render_music(plan), render_effects(plan.cues, plan.duration_s), speech)
