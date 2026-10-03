"""Theme derivation: a light "stage" look, tinted by the brand colour when there is one.

The foreground/background pair always meets WCAG AAA body contrast and the accent always
meets the 3:1 contrast WCAG asks of graphical objects, whatever brand colour is supplied.
"""

from preflight.contracts import Theme

from .color import contrast_ratio, from_hsl, hue_saturation_lightness

FONT_FAMILY = "Inter"
DEFAULT_THEME = Theme(
    background="#f5f5f7", foreground="#1d1d1f", accent="#5b5bd6", font_family=FONT_FAMILY
)

MIN_TEXT_CONTRAST = 7.0
MIN_GRAPHIC_CONTRAST = 3.0
_STAGE_LIGHTNESS = 0.965
_INK_LIGHTNESS = 0.11
_MAX_TINT = 0.28
_INK_SATURATION = 0.22
_LIGHTNESS_STEP = 0.02


def theme_for(brand_color: str | None) -> Theme:
    """Return the video theme for an optional ``#rrggbb`` brand colour."""
    if brand_color is None:
        return DEFAULT_THEME
    hue, saturation, _ = hue_saturation_lightness(brand_color)
    background = from_hsl(hue, min(saturation, _MAX_TINT), _STAGE_LIGHTNESS)
    foreground = _readable_ink(hue, min(saturation, _INK_SATURATION), background)
    return Theme(
        background=background,
        foreground=foreground,
        accent=_visible_accent(brand_color, background),
        font_family=FONT_FAMILY,
    )


def _readable_ink(hue: float, saturation: float, background: str) -> str:
    """Darken the tinted ink until it clears AAA contrast on the stage colour."""
    lightness = _INK_LIGHTNESS
    ink = from_hsl(hue, saturation, lightness)
    while contrast_ratio(ink, background) < MIN_TEXT_CONTRAST and lightness > 0:
        lightness = max(0.0, lightness - _LIGHTNESS_STEP)
        ink = from_hsl(hue, saturation, lightness)
    return ink


def _visible_accent(brand_color: str, background: str) -> str:
    """Keep the brand hue but darken it until it stands out from the stage colour."""
    hue, saturation, lightness = hue_saturation_lightness(brand_color)
    accent = brand_color
    while contrast_ratio(accent, background) < MIN_GRAPHIC_CONTRAST and lightness > 0:
        lightness = max(0.0, lightness - _LIGHTNESS_STEP)
        accent = from_hsl(hue, saturation, lightness)
    return accent
