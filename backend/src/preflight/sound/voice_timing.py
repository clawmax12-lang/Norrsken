"""Voice-led timing: scene lengths follow the narration, not the other way round (PRD §9.3).

Each scene's voice line is spoken once (the clip is cached, so the sound stage reuses it at no
cost) and measured. A scene lasts at least as long as its line needs; the time left over is
shared out in proportion to the planner's lengths. Boundaries snap to the 120 BPM half-second
beat, so cuts land on the music. The 3 s end card is never moved.
"""

import asyncio
from collections.abc import Sequence

from preflight.contracts import CreativeConcept
from preflight.contracts._base import VIDEO_DURATION_S
from preflight.ports import SpeechSynthesizer
from preflight.timing import END_CARD_S, SPEECH_GAP_S, SPEECH_LEAD_S

from .audio import pcm16_to_float, trim_silence

BEAT_S = 0.5
MIN_SCENE_S = 1.5
# Speech may be played this much faster than delivered before a scene must grow.
COMFORT_SPEEDUP = 1.1
_CONCURRENCY = 2


async def spoken_seconds(speech: SpeechSynthesizer, lines: Sequence[str]) -> list[float]:
    """Length in seconds of each line as the narrator speaks it (0 for an empty line)."""
    gate = asyncio.Semaphore(_CONCURRENCY)

    async def measure(text: str) -> float:
        if not text.strip():
            return 0.0
        async with gate:
            clip = await speech.synthesize(text)
        samples = trim_silence(pcm16_to_float(clip.pcm))
        return len(samples) / clip.sample_rate

    return list(await asyncio.gather(*(measure(line) for line in lines)))


async def time_to_voice(concept: CreativeConcept, speech: SpeechSynthesizer) -> CreativeConcept:
    """Return ``concept`` with scene lengths that fit its voice lines.

    Raises:
        ProviderError, SoundError: the narrator could not speak a line.
    """
    body = concept.scenes[:-1]
    if not any(scene.voice for scene in body):
        return concept
    spoken = await spoken_seconds(speech, [scene.voice or "" for scene in body])
    planned = [scene.t_end - scene.t_start for scene in body]
    lengths = fit_to_voice(planned, spoken, VIDEO_DURATION_S - END_CARD_S)
    return retime(concept, lengths)


def fit_to_voice(planned: Sequence[float], spoken: Sequence[float], total: float) -> list[float]:
    """Scene lengths summing to ``total``: each fits its line, the rest follows ``planned``."""
    need = [
        max(MIN_SCENE_S, seconds / COMFORT_SPEEDUP + SPEECH_LEAD_S + SPEECH_GAP_S)
        if seconds
        else MIN_SCENE_S
        for seconds in spoken
    ]
    if sum(need) >= total:
        raw = [total * n / sum(need) for n in need]
    else:
        spare = total - sum(need)
        weights = [max(p, 0.1) for p in planned]
        raw = [n + spare * w / sum(weights) for n, w in zip(need, weights, strict=True)]
    return snap_to_beats(raw, total)


def snap_to_beats(lengths: Sequence[float], total: float) -> list[float]:
    """Round ``lengths`` to whole beats (largest remainder) so they still sum to ``total``."""
    beats_total = round(total / BEAT_S)
    min_beats = max(1, round(MIN_SCENE_S / BEAT_S) - 1)
    shares = [length / BEAT_S for length in lengths]
    beats = [max(min_beats, int(share)) for share in shares]
    while sum(beats) > beats_total:
        beats[beats.index(max(beats))] -= 1
    order = sorted(range(len(shares)), key=lambda i: shares[i] - int(shares[i]), reverse=True)
    for index in order[: max(0, beats_total - sum(beats))]:
        beats[index] += 1
    return [b * BEAT_S for b in beats]


def retime(concept: CreativeConcept, body_lengths: Sequence[float]) -> CreativeConcept:
    """Apply new body scene lengths; the end card keeps the last :data:`END_CARD_S` seconds."""
    scenes = []
    start = 0.0
    for scene, length in zip(concept.scenes[:-1], body_lengths, strict=True):
        scenes.append(scene.model_copy(update={"t_start": start, "t_end": start + length}))
        start += length
    last = concept.scenes[-1]
    scenes.append(last.model_copy(update={"t_start": start, "t_end": float(concept.duration_s)}))
    return concept.model_copy(update={"scenes": tuple(scenes)})
