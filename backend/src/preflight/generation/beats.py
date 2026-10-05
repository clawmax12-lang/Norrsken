"""The shared clock: when each headline word lands and which beats picture and sound both hit.

A scene's voice line starts ``SPEECH_LEAD_S`` in and plays faster only when it overruns its
window, exactly as the sound studio plays it, so a word's frame here is the frame it is heard.
The headline appears as the narrator starts; its keyword (the emphasis, or a number) lands
the moment it is spoken, a finger then taps the screen's focus and the camera punches in. In
a long scene a second PUNCH pulls the camera back out, so the picture never holds still.
"""

import re
from collections.abc import Sequence
from dataclasses import dataclass

from preflight.contracts import Beat, BeatKind, Scene
from preflight.timing import SPEECH_GAP_S, SPEECH_LEAD_S, SPEECH_MAX_SPEEDUP

# Keep equal to the renderer's shots.MOVE_FRAMES: the device glide the whoosh follows.
MOVE_FRAMES = 18
HOOK_FRAMES = 8
WORD_FRAMES = 6
COUNT_FRAMES = 15
TAP_FRAMES = 8
PUNCH_FRAMES = 10
# Frames between headline words as they appear, and before a scene without a voice shows text.
WORD_STAGGER = 2
TEXT_DELAY = 4
# The headline is complete at least this long before the scene ends, so it can be read.
READ_FRAMES = 30
TAP_AFTER_WORD = 10
TAP_EARLIEST = 24
TAP_LATEST_BEFORE_END = 36
PUNCH_AFTER_TAP = 4
# A second PUNCH pulls the camera back out when a scene would otherwise hold still this long.
RELEASE_AFTER_FRAMES = 54
RELEASE_FRAMES = 14
# A finger presses the end card's button this long after the card lands (1.2 s).
CTA_TAP_AFTER = 36
# The finished ad taps through up to three elements per scene, at least this far apart.
AD_TAP_SPACING = 24
# The last tap's punch has this long to land and settle before the scene ends.
AD_LAST_TAP_BEFORE_END = 20

_NUMBER = re.compile(r"^\d+([.,]\d+)?$")
_NUMBER_WORDS = {
    "noll": 0, "en": 1, "ett": 1, "två": 2, "tre": 3, "fyra": 4, "fem": 5, "sex": 6, "sju": 7,
    "åtta": 8, "nio": 9, "tio": 10, "elva": 11, "tolv": 12, "femton": 15, "tjugo": 20,
    "trettio": 30, "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "twelve": 12, "fifteen": 15,
    "twenty": 20, "thirty": 30,
}  # fmt: skip


@dataclass(frozen=True)
class SceneClock:
    """One scene's frames: its edges, where its keyword lands, and its headline word frames."""

    start: int
    end: int
    keyword: int | None
    keyword_is_number: bool
    text_frames: tuple[int, ...]
    voice_start: int | None


def scene_clock(
    scene: Scene, start: int, end: int, fps: int, *, timed: bool, instant: bool = False
) -> SceneClock:
    """Frames for ``scene`` spanning ``[start, end)``.

    ``timed`` is false for the end card (its copy is the CTA card's). An ``instant`` scene (the
    hook) is readable on its first frame: every word is there at once and the keyword only
    pulses when it is spoken.
    """
    words = scene.text.split()
    heard = heard_frames(scene, start, end, fps) if timed else ()
    first = start if instant else (heard[0] if heard else start + TEXT_DELAY)
    latest = max(first, end - READ_FRAMES)
    key_index = keyword_index(scene)
    keyword: int | None = None
    if key_index is not None and heard:
        spoken = _spoken_at(words[key_index], scene.voice or "", heard)
        if spoken is not None:
            keyword = min(max(spoken, first + key_index * WORD_STAGGER), latest)
    stagger = 0 if instant else WORD_STAGGER
    frames = [min(first + i * stagger, latest) for i in range(len(words))]
    if keyword is not None and key_index is not None and not instant:
        frames[key_index] = keyword
    is_number = not instant and key_index is not None and _number_of(words[key_index]) is not None
    return SceneClock(
        start, end, keyword, is_number, tuple(frames) if timed else (), heard[0] if heard else None
    )


def heard_frames(scene: Scene, start: int, end: int, fps: int) -> tuple[int, ...]:
    """Frame at which each word of ``scene.voice`` is heard (empty when it was not measured)."""
    if not scene.voice_words or scene.voice_s is None:
        return ()
    line_start = start / fps + SPEECH_LEAD_S
    window = end / fps - SPEECH_GAP_S - line_start
    if window <= 0:
        return ()
    ratio = min(max(scene.voice_s / window, 1.0), SPEECH_MAX_SPEEDUP)
    return tuple(round((line_start + t / ratio) * fps) for t in scene.voice_words)


def keyword_index(scene: Scene) -> int | None:
    """The headline word that lands on its own: a number first, else the emphasis word."""
    words = scene.text.split()
    for index, word in enumerate(words):
        if _NUMBER.match(_bare(word)):
            return index
    if scene.emphasis:
        for index, word in enumerate(words):
            if _bare(word) == _bare(scene.emphasis):
                return index
    return None


def scene_beats(index: int, clock: SceneClock, scene: Scene, *, last: bool) -> list[Beat]:
    """The beats of one scene, in frame order."""
    if last:
        beats = [Beat(kind=BeatKind.CTA, frame=clock.start, frames=HOOK_FRAMES, scene=index)]
        press = clock.start + CTA_TAP_AFTER
        if press + TAP_FRAMES < clock.end:
            beats.append(Beat(kind=BeatKind.TAP, frame=press, frames=TAP_FRAMES, scene=index))
        return beats
    beats = [
        Beat(kind=BeatKind.HOOK, frame=0, frames=HOOK_FRAMES, scene=index)
        if index == 0
        else Beat(kind=BeatKind.MOVE, frame=clock.start, frames=MOVE_FRAMES, scene=index)
    ]
    if clock.keyword is not None:
        kind, frames = (
            (BeatKind.COUNT, COUNT_FRAMES)
            if clock.keyword_is_number
            else (BeatKind.WORD, WORD_FRAMES)
        )
        beats.append(Beat(kind=kind, frame=clock.keyword, frames=frames, scene=index))
    if scene.focus is not None:
        after = clock.keyword + TAP_AFTER_WORD if clock.keyword is not None else 0
        tap = min(max(clock.start + TAP_EARLIEST, after), clock.end - TAP_LATEST_BEFORE_END)
        if tap > clock.start:
            x, y, w, h = scene.focus
            point = (round(x + w / 2, 4), round(y + h / 2, 4))
            beats.append(
                Beat(kind=BeatKind.TAP, frame=tap, frames=TAP_FRAMES, scene=index, point=point)
            )
            punch = tap + PUNCH_AFTER_TAP
            beats.append(Beat(kind=BeatKind.PUNCH, frame=punch, frames=PUNCH_FRAMES, scene=index))
            held = clock.end - (punch + PUNCH_FRAMES)
            if held > RELEASE_AFTER_FRAMES:
                release = punch + PUNCH_FRAMES + held // 2 - RELEASE_FRAMES // 2
                beats.append(
                    Beat(kind=BeatKind.PUNCH, frame=release, frames=RELEASE_FRAMES, scene=index)
                )
    return beats


def tap_run(
    index: int, start: int, end: int, keyword: int | None, points: Sequence[tuple[float, float]]
) -> list[Beat]:
    """The finished ad's taps: the finger works through ``points``, punching in on each.

    A scene never holds one framing for long. The first tap follows the keyword as in the
    pretested cut; points that no longer fit before ``end`` are dropped. Points are shares of
    the scene's shown region.
    """
    after = keyword + TAP_AFTER_WORD if keyword is not None else 0
    first = min(max(start + TAP_EARLIEST, after), end - TAP_LATEST_BEFORE_END)
    if first <= start or not points:
        return []
    last = end - AD_LAST_TAP_BEFORE_END - PUNCH_AFTER_TAP - PUNCH_FRAMES
    fits = 1 + max(0, (last - first) // AD_TAP_SPACING)
    chosen = points[: max(1, min(len(points), fits))]
    gap = (last - first) // (len(chosen) - 1) if len(chosen) > 1 else 0
    beats: list[Beat] = []
    for n, (x, y) in enumerate(chosen):
        tap = first + n * gap
        point = (round(x, 4), round(y, 4))
        beats += [
            Beat(kind=BeatKind.TAP, frame=tap, frames=TAP_FRAMES, scene=index, point=point),
            Beat(
                kind=BeatKind.PUNCH, frame=tap + PUNCH_AFTER_TAP, frames=PUNCH_FRAMES, scene=index
            ),
        ]
    return beats


def ordered(beats: Sequence[Beat]) -> tuple[Beat, ...]:
    """Beats by frame (ties keep the order they were made in)."""
    return tuple(sorted(beats, key=lambda beat: beat.frame))


def _spoken_at(word: str, voice: str, heard: tuple[int, ...]) -> int | None:
    """Frame at which ``word`` (or the same number written out) is spoken in ``voice``."""
    target = _bare(word)
    number = _number_of(word)
    for spoken, frame in zip(voice.split(), heard, strict=False):
        bare = _bare(spoken)
        if bare == target or (number is not None and _number_of(spoken) == number):
            return frame
    return None


def _number_of(word: str) -> float | None:
    bare = _bare(word)
    if _NUMBER.match(bare):
        return float(bare.replace(",", "."))
    value = _NUMBER_WORDS.get(bare)
    return float(value) if value is not None else None


def _bare(word: str) -> str:
    return re.sub(r"^[^\w]+|[^\w]+$", "", word).casefold()
