"""Accessible colour maths for the video theme (WCAG 2.x contrast)."""

import colorsys

_CHANNELS = 3


def hex_to_rgb(color: str) -> tuple[float, float, float]:
    """Parse ``#rrggbb`` into channels in ``[0, 1]``."""
    value = int(color.removeprefix("#"), 16)
    return ((value >> 16) & 255) / 255, ((value >> 8) & 255) / 255, (value & 255) / 255


def rgb_to_hex(red: float, green: float, blue: float) -> str:
    """Format channels in ``[0, 1]`` as lowercase ``#rrggbb``."""
    channels = (round(min(max(c, 0.0), 1.0) * 255) for c in (red, green, blue))
    return "#" + "".join(f"{c:02x}" for c in channels)


def _linear(channel: float) -> float:
    return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4


def relative_luminance(color: str) -> float:
    """WCAG relative luminance of a ``#rrggbb`` colour."""
    red, green, blue = (_linear(c) for c in hex_to_rgb(color))
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast_ratio(first: str, second: str) -> float:
    """WCAG contrast ratio, from 1 (identical) to 21 (black on white)."""
    lighter, darker = sorted((relative_luminance(first), relative_luminance(second)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


def hue_saturation_lightness(color: str) -> tuple[float, float, float]:
    """Return ``(hue, saturation, lightness)``, each in ``[0, 1]``."""
    red, green, blue = hex_to_rgb(color)
    hue, lightness, saturation = colorsys.rgb_to_hls(red, green, blue)
    return hue, saturation, lightness


def from_hsl(hue: float, saturation: float, lightness: float) -> str:
    """Build ``#rrggbb`` from hue, saturation and lightness in ``[0, 1]``."""
    return rgb_to_hex(*colorsys.hls_to_rgb(hue, lightness, saturation))
