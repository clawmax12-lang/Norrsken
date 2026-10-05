"""Decide what the soundtrack contains, as a pure function of the rendered spec.

Narration reads the scenes' voice lines. When the spec carries beats (taps, glides, words
landing), every effect sits on the frame the picture marks; older specs get effects on scene
changes. The ambience lifts into the locked 3 s end card. Scene edges sit on a 0.5 s grid.
"""

from dataclasses import dataclass

from preflight.contracts import (
    Beat,
    BeatKind,
    BriefField,
    CompositionSpec,
    CueKind,
    NarrationLine,
    SoundCue,
    Transition,
)
from preflight.motion.scene import MotionSpec
from preflight.timing import END_CARD_S, SPEECH_GAP_S, SPEECH_LEAD_S, SPEECH_TAIL_S

BPM = 120
BEAT_S = 60.0 / BPM
BAR_S = 4 * BEAT_S

_TEXT_TICK_DELAY_S = 0.12
# Rough words/second for fitting a line into its scene window.
_WORDS_PER_S = 2.6
# A glide is loudest just past its middle, and its air lingers a little after the device lands.
_MOVE_PEAK = 0.6
_WHOOSH_TAIL_S = 0.25
# Counter ticks speed up towards the final number (shares of the count's length).
_COUNT_TICKS = (0.0, 0.3, 0.52, 0.68, 0.8, 0.9)
_CTA_RISER_S = 0.9
# Keep equal to the CTA card's ARROW_DELAY_S: the button springs in here.
_CTA_BUTTON_S = 0.28


@dataclass(frozen=True)
class SoundPlan:
    """What to say, which effects to play where, and where the ambience shifts.

    ``drop_s`` is the first scene change and ``outro_s`` where the end card starts and the
    ambience lifts (both on beats). ``duration_s`` is the video length.
    """

    duration_s: float
    drop_s: float
    outro_s: float
    lines: tuple[NarrationLine, ...]
    cues: tuple[SoundCue, ...]


@dataclass(frozen=True)
class _Beat:
    start_s: float
    text: str
    source_field: BriefField
    transition: Transition | None
    voice: str | None = None


@dataclass(frozen=True)
class _Copy:
    headline: str
    headline_field: BriefField
    cta: str
    cta_field: BriefField
    end_voice: str | None = None


def plan_soundtrack(spec: CompositionSpec) -> SoundPlan:
    """Plan narration, effects and ambience for a Showcase ``CompositionSpec``."""
    duration_s = spec.duration_frames / spec.fps
    cta_s = duration_s - END_CARD_S
    body = spec.scenes[:-1] or spec.scenes
    beats = tuple(
        _Beat(
            start_s=scene.start_frame / spec.fps,
            text=scene.text,
            source_field=scene.source_field,
            transition=None if index == 0 else scene.transition_in,
            voice=scene.voice,
        )
        for index, scene in enumerate(body)
    )
    copy = _Copy(
        spec.headline,
        spec.headline_source_field,
        spec.cta,
        spec.cta_source_field,
        spec.end_voice,
    )
    cues = beat_cues(spec) if spec.beats else None
    return _plan(duration_s, beats, copy, cta_s, cues)


def plan_motion_soundtrack(spec: MotionSpec) -> SoundPlan:
    """Plan narration against the 60 fps motion timeline that was actually rendered."""
    duration_s = spec.duration_frames / spec.fps
    cta_s = duration_s - END_CARD_S
    body = spec.shots[:-1] or spec.shots
    beats = tuple(
        _Beat(
            start_s=shot.start_frame / spec.fps,
            text=shot.text,
            source_field=shot.source_field,
            transition=None if index == 0 else Transition.FADE,
        )
        for index, shot in enumerate(body)
    )
    copy = _Copy(spec.headline, spec.headline_source_field, spec.cta, spec.cta_source_field)
    return _plan(duration_s, beats, copy, cta_s)


def _plan(
    duration_s: float,
    beats: tuple[_Beat, ...],
    copy: _Copy,
    cta_s: float,
    cues: tuple[SoundCue, ...] | None = None,
) -> SoundPlan:
    scene_starts = [beat.start_s for beat in beats]
    outro_s = _snap_down(cta_s)
    drop_s = _snap(scene_starts[1]) if len(scene_starts) > 1 else 0.0
    return SoundPlan(
        duration_s=duration_s,
        drop_s=min(drop_s, outro_s),
        outro_s=outro_s,
        lines=_narration(beats, copy, cta_s, duration_s),
        cues=cues if cues is not None else _cues(beats, cta_s),
    )


def beat_cues(spec: CompositionSpec) -> tuple[SoundCue, ...]:
    """One effect (or a short figure) per beat of ``spec``, on the frame the picture marks it.

    The headline's first word gets a soft select as it appears; the end card is announced by a
    riser that stops on its first frame, where the thud and the button's pop follow.
    """
    fps = spec.fps
    cues: list[SoundCue] = []
    for index, scene in enumerate(spec.scenes):
        if index > 0 and scene.text_frames:
            cues.append(SoundCue(kind=CueKind.SELECT, t=scene.text_frames[0] / fps))
    for beat in spec.beats:
        cues += _beat_figure(beat, fps)
    return tuple(sorted(cues, key=lambda cue: (cue.t, cue.kind.value)))


def _beat_figure(beat: Beat, fps: int) -> list[SoundCue]:
    t = beat.frame / fps
    length = beat.frames / fps
    figure: list[SoundCue] = []
    match beat.kind:
        case BeatKind.HOOK:
            figure = [SoundCue(kind=CueKind.THUD, t=t), SoundCue(kind=CueKind.SHIMMER, t=t + 0.05)]
        case BeatKind.MOVE:
            side = 0.5 if beat.scene % 2 else -0.5
            figure = [
                SoundCue(
                    kind=CueKind.WHOOSH,
                    t=t + length * _MOVE_PEAK,
                    duration_s=round(length + _WHOOSH_TAIL_S, 3),
                    pan=side,
                )
            ]
        case BeatKind.WORD:
            figure = [SoundCue(kind=CueKind.POP, t=t)]
        case BeatKind.COUNT:
            figure = [
                *(SoundCue(kind=CueKind.TICK, t=t + length * at) for at in _COUNT_TICKS),
                SoundCue(kind=CueKind.CONFIRM, t=t + length),
            ]
        case BeatKind.TAP:
            pan = round((beat.point[0] - 0.5) * 0.6, 3) if beat.point else None
            figure = [SoundCue(kind=CueKind.TAP, t=t, pan=pan)]
        case BeatKind.PUNCH:
            figure = [
                SoundCue(kind=CueKind.WHOOSH, t=t + length * _MOVE_PEAK, duration_s=0.3, pan=0.0)
            ]
        case BeatKind.CTA:
            figure = [
                SoundCue(kind=CueKind.RISER, t=t, duration_s=_CTA_RISER_S),
                SoundCue(kind=CueKind.THUD, t=t),
                SoundCue(kind=CueKind.SHIMMER, t=t + 0.15),
                SoundCue(kind=CueKind.POP, t=t + _CTA_BUTTON_S),
            ]
    return figure


def _snap(t: float) -> float:
    """Nearest beat."""
    return round(t / BEAT_S) * BEAT_S


def _snap_down(t: float) -> float:
    """Latest beat at or before ``t`` (a small tolerance keeps float noise from losing a beat)."""
    return int(t / BEAT_S + 1e-6) * BEAT_S


def _narration(
    beats: tuple[_Beat, ...],
    copy: _Copy,
    cta_s: float,
    duration_s: float,
) -> tuple[NarrationLine, ...]:
    """The planner's voice-over when it wrote one; else one line per distinct on-screen text."""
    if any(beat.voice for beat in beats):
        return _voice_over(beats, copy, cta_s, duration_s)
    starts = [beat.start_s for beat in beats]
    boundaries = [*starts[1:], cta_s]
    spoken: list[tuple[str, BriefField, float, float]] = []
    seen: set[str] = set()
    for beat, start, next_start in zip(beats, starts, boundaries, strict=True):
        key = beat.text.casefold()
        if key and key not in seen:
            seen.add(key)
            spoken.append((beat.text, beat.source_field, start + SPEECH_LEAD_S, next_start))
    cta_text = copy.headline or copy.cta
    if cta_text.casefold() not in seen:
        spoken.append((cta_text, copy.headline_field, cta_s + SPEECH_LEAD_S, duration_s))
    lines: list[NarrationLine] = []
    for index, (text, field, start, limit) in enumerate(spoken):
        is_last = index == len(spoken) - 1
        end = limit - (SPEECH_TAIL_S if is_last else SPEECH_GAP_S)
        window = end - start
        if window <= 0 or not text.strip():
            continue
        fitted = _fit(text, window)
        if fitted:
            lines.append(
                NarrationLine(text=fitted, source_field=field, start_s=start, window_s=window)
            )
    return tuple(lines)


def _voice_over(
    beats: tuple[_Beat, ...], copy: _Copy, cta_s: float, duration_s: float
) -> tuple[NarrationLine, ...]:
    """Every scene's own voice line in full, then the end-card line.

    Lines are never shortened here: scene lengths were already fitted to the spoken lines
    (voice-led timing), and the studio speeds up a line that still runs long.
    """
    starts = [beat.start_s for beat in beats]
    boundaries = [*starts[1:], cta_s]
    lines: list[NarrationLine] = []
    for beat, start, next_start in zip(beats, starts, boundaries, strict=True):
        window = next_start - SPEECH_GAP_S - (start + SPEECH_LEAD_S)
        if beat.voice and beat.voice.strip() and window > 0:
            lines.append(
                NarrationLine(
                    text=beat.voice.strip(),
                    source_field=beat.source_field,
                    start_s=start + SPEECH_LEAD_S,
                    window_s=window,
                )
            )
    closing = (copy.end_voice or copy.headline or copy.cta).strip()
    window = duration_s - SPEECH_TAIL_S - (cta_s + SPEECH_LEAD_S)
    if closing and window > 0:
        lines.append(
            NarrationLine(
                text=closing,
                source_field=copy.headline_field,
                start_s=cta_s + SPEECH_LEAD_S,
                window_s=window,
            )
        )
    return tuple(lines)


def _fit(text: str, window_s: float) -> str:
    """Trim ``text`` to roughly fit ``window_s``; empty when nothing fits."""
    words = text.split()
    if not words:
        return ""
    budget = max(1, int(window_s * _WORDS_PER_S))
    return " ".join(words[:budget])


def _cues(beats: tuple[_Beat, ...], cta_s: float) -> tuple[SoundCue, ...]:
    cues: list[SoundCue] = [SoundCue(kind=CueKind.SHIMMER, t=0.1)]
    for beat in beats:
        cues.append(SoundCue(kind=CueKind.TICK, t=beat.start_s + _TEXT_TICK_DELAY_S))
        if beat.transition is not None:
            cues.extend(_transition_cues(beat.transition, beat.start_s))
    cues += [SoundCue(kind=CueKind.IMPACT, t=cta_s), SoundCue(kind=CueKind.SHIMMER, t=cta_s)]
    return tuple(sorted(cues, key=lambda cue: (cue.t, cue.kind.value)))


def _transition_cues(transition: Transition, t: float) -> list[SoundCue]:
    """Effects that mark a scene change; the loudest moment is the change itself."""
    match transition:
        case Transition.CUT:
            return [SoundCue(kind=CueKind.IMPACT, t=t)]
        case Transition.PUSH:
            return [SoundCue(kind=CueKind.WHOOSH, t=t)]
        case Transition.SCALE:
            return [SoundCue(kind=CueKind.WHOOSH, t=t), SoundCue(kind=CueKind.IMPACT, t=t)]
        case Transition.FADE:
            return [SoundCue(kind=CueKind.SHIMMER, t=t)]
