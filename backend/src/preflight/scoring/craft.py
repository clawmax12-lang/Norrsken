"""PRD §16: measured pace and sound of each cut, reported next to the score (never in it).

Pace comes from the spec's beats, the clock the picture and the effects both play to, so it
is exactly what a viewer sees; voice coverage and loudness come from the finished soundtrack.
"""

from preflight.advice import advice
from preflight.contracts import BeatKind, CompositionSpec, Craft, SoundRecord

# Longer than this with nothing new on screen and a feed viewer scrolls on.
MAX_STILL_S = 2.0
MIN_VOICE_COVERAGE = 0.5
LUFS_RANGE = (-16.0, -12.0)


def craft_for(spec: CompositionSpec, sound: SoundRecord | None, language: str | None) -> Craft:
    """Events per second and the longest still stretch before the end card, plus the mix."""
    fps = spec.fps
    cta = next((b.frame for b in spec.beats if b.kind is BeatKind.CTA), spec.duration_frames)
    body = sorted((b for b in spec.beats if b.kind is not BeatKind.CTA), key=lambda b: b.frame)
    edges = [(b.frame, b.frame + b.frames) for b in body if b.frame < cta]
    still_frames, still_at, busy_until = 0, 0, 0
    for start, end in [*edges, (cta, cta)]:
        if start - busy_until > still_frames:
            still_frames, still_at = start - busy_until, busy_until
        busy_until = max(busy_until, end)
    body_s = cta / fps
    craft = Craft(
        events_per_s=round(len(edges) / body_s, 2) if body_s > 0 else 0.0,
        longest_still_s=round(still_frames / fps, 2),
        voice_coverage=sound.voice_coverage if sound else None,
        integrated_lufs=sound.integrated_lufs if sound else None,
    )
    if not spec.beats:
        return craft
    return craft.model_copy(
        update={"issues": _issues(spec.variant_id, craft, still_at / fps, language)}
    )


def _issues(variant: str, craft: Craft, still_at_s: float, language: str | None) -> tuple[str, ...]:
    issues: list[str] = []
    if craft.longest_still_s > MAX_STILL_S:
        issues.append(
            advice(
                "craft_still",
                language,
                variant=variant,
                seconds=f"{craft.longest_still_s:.1f}",
                at=f"0:{still_at_s:04.1f}",
                limit=f"{MAX_STILL_S:.0f}",
            )
        )
    if craft.voice_coverage is not None and craft.voice_coverage < MIN_VOICE_COVERAGE:
        issues.append(
            advice(
                "craft_voice", language, variant=variant, percent=round(craft.voice_coverage * 100)
            )
        )
    low, high = LUFS_RANGE
    if craft.integrated_lufs is not None and not low <= craft.integrated_lufs <= high:
        issues.append(
            advice(
                "craft_loudness",
                language,
                variant=variant,
                lufs=f"{craft.integrated_lufs:.1f}",
                low=f"{low:.0f}",
                high=f"{high:.0f}",
            )
        )
    return tuple(issues)
