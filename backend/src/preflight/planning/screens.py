"""Device mockups among the screenshots (FR-03 picture quality).

Founders often upload a phone rendered on a backdrop instead of a raw screenshot. Shown whole,
the backdrop becomes a grey box in the film and the screen ends up small and upscaled. The
planner reports a rough ``device_box`` for such images; this module snaps it to the device's
own edge so the renderer can cut the device out. Drop shadows and glows are smooth gradients,
while a device frame is a hard step in brightness, so the first hard step from each side is
the edge.
"""

import io
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from PIL import Image

from preflight.contracts import FocusBox

_EDGE_STEP = 50
# Share of a line that must step sharply for it to be the device edge (corners are rounded).
_EDGE_SHARE = 0.3
_SEARCH_MARGIN = 0.04
# A "device" covering nearly the whole image is a plain screenshot, not a mockup.
_MAX_DEVICE_SHARE = 0.9
_MIN_DEVICE_SHARE = 0.02
# Phone frame plus bezel as a share of the device width (modern phones: about 4-5 %).
_TYPICAL_BEZEL = 0.05
_MAX_BEZEL = 0.09


@dataclass(frozen=True)
class ScreenImage:
    """Pixel size of a screenshot and, for a mockup, the box of the device's display in it."""

    width: int
    height: int
    crop: FocusBox | None = None

    @property
    def product_width_px(self) -> int:
        """Width in source pixels of what the film actually shows."""
        return round(self.width * (self.crop[2] if self.crop else 1.0))


def inspect_screen(data: bytes, device_box: list[int] | None) -> ScreenImage:
    """Size of the image and, for a mockup, the display to cut out (``None`` otherwise)."""
    with Image.open(io.BytesIO(data)) as opened:
        pixels = np.asarray(opened.convert("RGB"), dtype=np.int16)
    height, width = pixels.shape[:2]
    if not device_box or len(device_box) != 4:
        return ScreenImage(width, height)
    device = refine_device_box(pixels, device_box)
    if device is None:
        return ScreenImage(width, height)
    return ScreenImage(width, height, screen_of_device(pixels, device))


def refine_device_box(pixels: NDArray[np.int16], box_2d: list[int]) -> FocusBox | None:
    """Snap Gemini's ``[ymin, xmin, ymax, xmax]`` (0-1000) to the device's edge."""
    height, width = pixels.shape[:2]
    ymin, xmin, ymax, xmax = (min(max(v, 0), 1000) / 1000 for v in box_2d)
    if xmax <= xmin or ymax <= ymin:
        return None
    rows = slice(int(ymin * height), max(int(ymax * height), int(ymin * height) + 1))
    cols = slice(int(xmin * width), max(int(xmax * width), int(xmin * width) + 1))
    # step_x[y, x] compares column x with x + 1; step_y[y, x] compares row y with y + 1.
    step_x = np.abs(np.diff(pixels, axis=1)).max(axis=2) > _EDGE_STEP
    step_y = np.abs(np.diff(pixels, axis=0)).max(axis=2) > _EDGE_STEP
    column_edges = step_x[rows].mean(axis=0) >= _EDGE_SHARE
    row_edges = step_y[:, cols].mean(axis=1) >= _EDGE_SHARE
    left = _first(column_edges, xmin, width, inward=True)
    right = _first(column_edges, xmax, width, inward=False)
    top = _first(row_edges, ymin, height, inward=True)
    bottom = _first(row_edges, ymax, height, inward=False)
    if right <= left or bottom <= top:
        return None
    box = (left / width, top / height, (right - left) / width, (bottom - top) / height)
    if not _MIN_DEVICE_SHARE <= box[2] * box[3] <= _MAX_DEVICE_SHARE:
        return None
    return box


def _first(edges: NDArray[np.bool_], guess: float, size: int, *, inward: bool) -> int:
    """Pixel coordinate of the outermost edge near ``guess``; ``guess`` when none is found.

    ``edges[i]`` marks a step between pixel ``i`` and ``i + 1``. Scanning starts outside the
    guess and moves toward the centre, so the first hit is the device's outer edge.
    """
    margin = int(_SEARCH_MARGIN * size)
    centre = int(guess * size)
    if inward:
        for index in range(max(0, centre - margin), min(len(edges), centre + margin)):
            if edges[index]:
                return index + 1
    else:
        for index in range(min(len(edges) - 1, centre + margin), max(-1, centre - margin), -1):
            if edges[index]:
                return index + 1
    return centre


def screen_of_device(pixels: NDArray[np.int16], device: FocusBox) -> FocusBox:
    """The display inside a phone's bezel, as a box of the whole image.

    The bezel is a near-black ring of roughly the same thickness on every side. Its inner edge
    is a hard step into the screen; when the screen is dark too (no step), a typical bezel
    width is used instead.
    """
    height, width = pixels.shape[:2]
    x, y, w, h = device
    left, top = round(x * width), round(y * height)
    right, bottom = round((x + w) * width), round((y + h) * height)
    region = pixels[top:bottom, left:right]
    if region.shape[0] < 20 or region.shape[1] < 20:
        return device
    rw = region.shape[1]
    limit = max(2, int(rw * _MAX_BEZEL))
    step_x = np.abs(np.diff(region, axis=1)).max(axis=2) > _EDGE_STEP
    step_y = np.abs(np.diff(region, axis=0)).max(axis=2) > _EDGE_STEP
    middle_rows = slice(region.shape[0] // 4, 3 * region.shape[0] // 4)
    middle_cols = slice(rw // 4, 3 * rw // 4)
    cols = step_x[middle_rows].mean(axis=0) >= _EDGE_SHARE
    rows = step_y[:, middle_cols].mean(axis=1) >= _EDGE_SHARE
    default = max(1, round(rw * _TYPICAL_BEZEL))
    inset_left = _inner_step(cols[:limit]) or default
    inset_right = _inner_step(cols[::-1][:limit]) or default
    inset_top = _inner_step(rows[:limit]) or default
    inset_bottom = _inner_step(rows[::-1][:limit]) or default
    inner_left, inner_top = left + inset_left, top + inset_top
    inner_right, inner_bottom = right - inset_right, bottom - inset_bottom
    if inner_right - inner_left < 10 or inner_bottom - inner_top < 10:
        return device
    return (
        inner_left / width,
        inner_top / height,
        (inner_right - inner_left) / width,
        (inner_bottom - inner_top) / height,
    )


def _inner_step(edges: NDArray[np.bool_]) -> int | None:
    """Offset just past the last hard step within the bezel band, or ``None``."""
    hits = np.flatnonzero(edges)
    if hits.size == 0:
        return None
    inset = int(hits[-1]) + 2
    return inset if inset >= 2 else None


def crop_focus(focus: FocusBox | None, crop: FocusBox | None) -> FocusBox | None:
    """Re-express a focus box given on the whole image in the coordinates of ``crop``."""
    if focus is None or crop is None:
        return focus
    cx, cy, cw, ch = crop
    fx, fy, fw, fh = focus
    left = min(max((fx - cx) / cw, 0.0), 1.0)
    top = min(max((fy - cy) / ch, 0.0), 1.0)
    right = min(max((fx + fw - cx) / cw, 0.0), 1.0)
    bottom = min(max((fy + fh - cy) / ch, 0.0), 1.0)
    if right - left < 0.08 or bottom - top < 0.05:
        return None
    return (left, top, right - left, bottom - top)
