"""PRD §16: a deterministic production factor that caps the absolute score, never the order.

The simulated viewer panel watches a downscaled video, so it cannot see a soft product image.
Facts the pipeline already measured can: a screen narrower than ``SHARP_SCREEN_PX`` source
pixels is enlarged into blur in a 1080 px video. Every variant uses the same screenshots,
so the factor is the same for all of them and the ranking is unchanged.
"""

from preflight.advice import advice
from preflight.contracts import PlanNotes, Production

SHARP_SCREEN_PX = 600
MIN_FACTOR = 0.5


def production_for(notes: PlanNotes, language: str | None) -> Production | None:
    """The factor for the smallest screen the videos show, or ``None`` when it is unknown.

    ``clamp(width / SHARP_SCREEN_PX, MIN_FACTOR, 1)``: 284 px gives 0.5, 600 px or more gives 1.
    """
    width = notes.smallest_screen_px
    if width is None:
        return None
    factor = round(min(1.0, max(MIN_FACTOR, width / SHARP_SCREEN_PX)), 3)
    if factor >= 1:
        return Production(factor=1.0)
    reason = advice(
        "production", language, px=width, percent=round(factor * 100), sharp=SHARP_SCREEN_PX
    )
    return Production(factor=factor, reasons=(reason,))
