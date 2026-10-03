"""Decide what the soundtrack contains, as a pure function of the composition spec.

Everything is derived from the spec the renderer drew: narration reads the on-screen copy,
effects land on scene changes (by transition style) and the music's drop and outro follow the
scene and end-card boundaries. At 120 BPM a beat is half a second, so the whole-second scene
lengths the planner produces fall on beats and every cut lands on the music.
"""

from dataclasses import dataclass

from preflight.contracts import CompositionSpec, CueKind, NarrationLine, SoundCue, Transition

BPM = 120
BEAT_S = 60.0 / BPM
BAR_S = 4 * BEAT_S

# The CTA end card covers the tail of the last scene. Mirrors CTA_CARD_MAX_FRAMES and
# CTA_CARD_SCENE_SHARE in workers/renderer/src/composition/tokens.ts.
_CTA_MAX_FRAMES = 60
_CTA_SCENE_SHARE = 0.6

_SPEECH_LEAD_S = 0.3  # a line starts once its scene has settled
_SPEECH_GAP_S = 0.12  # air left before the next line
_SPEECH_TAIL_S = 0.2  # the last line must end before the video does
_TEXT_TICK_DELAY_S = 0.12
_BEAT_SNAP_S = 0.06


@dataclass(frozen=True)
class SoundPlan:
    """What to say, which effects to play where, and how the music is structured.

    ``drop_s`` is where the music's drums and bass enter and ``outro_s`` where they leave
    (both on beats). ``duration_s`` is the video length.
    """

    duration_s: float
    drop_s: float
    outro_s: float
    lines: tuple[NarrationLine, ...]
    cues: tuple[SoundCue, ...]


def plan_soundtrack(spec: CompositionSpec) -> SoundPlan:
    """Plan narration, effects and music structure for ``spec``."""
    duration_s = spec.duration_frames / spec.fps
    cta_s = _cta_start_s(spec)
    scene_starts = [scene.start_frame / spec.fps for scene in spec.scenes]
    outro_s = _snap_down(cta_s)
    drop_s = _snap(scene_starts[1]) if len(scene_starts) > 1 else 0.0
    return SoundPlan(
        duration_s=duration_s,
        drop_s=min(drop_s, outro_s),
        outro_s=outro_s,
        lines=_narration(spec, scene_starts, cta_s, duration_s),
        cues=_cues(spec, scene_starts, cta_s),
    )


def _cta_start_s(spec: CompositionSpec) -> float:
    last = spec.scenes[-1]
    length = last.end_frame - last.start_frame
    card = min(_CTA_MAX_FRAMES, max(1, int(length * _CTA_SCENE_SHARE)))
    return (last.end_frame - card) / spec.fps


def _snap(t: float) -> float:
    """Nearest beat."""
    return round(t / BEAT_S) * BEAT_S


def _snap_down(t: float) -> float:
    """Latest beat at or before ``t`` (a small tolerance keeps float noise from losing a beat)."""
    return int(t / BEAT_S + 1e-6) * BEAT_S


def _narration(
    spec: CompositionSpec, scene_starts: list[float], cta_s: float, duration_s: float
) -> tuple[NarrationLine, ...]:
    """One line per distinct on-screen text, then the call to action on its end card."""
    spoken: list[tuple[str, object, float, float]] = []
    seen: set[str] = set()
    boundaries = [*scene_starts[1:], cta_s]
    for scene, start, next_start in zip(spec.scenes, scene_starts, boundaries, strict=True):
        if scene.text.casefold() not in seen:
            seen.add(scene.text.casefold())
            spoken.append((scene.text, scene.source_field, start + _SPEECH_LEAD_S, next_start))
    if spec.cta.casefold() not in seen:
        spoken.append((spec.cta, spec.cta_source_field, cta_s + _SPEECH_LEAD_S, duration_s))
    lines = []
    for index, (text, field, start, limit) in enumerate(spoken):
        is_last = index == len(spoken) - 1
        end = limit - (_SPEECH_TAIL_S if is_last else _SPEECH_GAP_S)
        if end - start > 0:
            lines.append(
                NarrationLine(text=text, source_field=field, start_s=start, window_s=end - start)
            )
    return tuple(lines)


def _cues(spec: CompositionSpec, scene_starts: list[float], cta_s: float) -> tuple[SoundCue, ...]:
    cues: list[SoundCue] = [SoundCue(kind=CueKind.SHIMMER, t=0.1)]
    for index, (scene, start) in enumerate(zip(spec.scenes, scene_starts, strict=True)):
        cues.append(SoundCue(kind=CueKind.TICK, t=start + _TEXT_TICK_DELAY_S))
        if index > 0:
            cues.extend(_transition_cues(scene.transition_in, start))
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
