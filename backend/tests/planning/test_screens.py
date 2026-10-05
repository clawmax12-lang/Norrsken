import io

import pytest
from PIL import Image, ImageDraw, ImageFilter

from preflight.planning.screens import crop_focus, inspect_screen

WIDTH, HEIGHT = 1000, 700
# The phone body (frame) and the display inside its bezel, in pixels.
BODY = (400, 50, 700, 650)
SCREEN = (415, 65, 685, 635)


def mockup(screen_colour: str = "#f4f6fa") -> bytes:
    """A phone on a grey backdrop with a soft drop shadow, like a design-tool export."""
    image = Image.new("RGB", (WIDTH, HEIGHT), "#e4e8ea")
    shadow = Image.new("L", (WIDTH, HEIGHT), 0)
    ImageDraw.Draw(shadow).rounded_rectangle((380, 70, 730, 680), 60, fill=150)
    image.paste(
        Image.new("RGB", (WIDTH, HEIGHT), "#80868a"),
        mask=shadow.filter(ImageFilter.GaussianBlur(24)),
    )
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(BODY, 48, fill="#dcdcd8")
    draw.rounded_rectangle((BODY[0] + 4, BODY[1] + 4, BODY[2] - 4, BODY[3] - 4), 44, fill="#050505")
    draw.rounded_rectangle(SCREEN, 34, fill=screen_colour)
    draw.rectangle((450, 200, 650, 260), fill="#222222")
    buffer = io.BytesIO()
    image.save(buffer, "PNG")
    return buffer.getvalue()


def rough_box() -> list[int]:
    """Gemini's box is a few per cent off: here too wide and too short."""
    return [90, 380, 920, 720]


def as_pixels(box: tuple[float, float, float, float]) -> tuple[int, int, int, int]:
    x, y, w, h = box
    return round(x * WIDTH), round(y * HEIGHT), round((x + w) * WIDTH), round((y + h) * HEIGHT)


def test_a_mockup_is_cut_down_to_the_display_inside_the_bezel() -> None:
    screen = inspect_screen(mockup(), rough_box())

    assert screen.crop is not None
    left, top, right, bottom = as_pixels(screen.crop)
    assert left == pytest.approx(SCREEN[0], abs=6)
    assert right == pytest.approx(SCREEN[2], abs=6)
    assert top == pytest.approx(SCREEN[1], abs=6)
    assert bottom == pytest.approx(SCREEN[3], abs=6)
    assert screen.product_width_px == pytest.approx(SCREEN[2] - SCREEN[0], abs=10)


def test_a_dark_display_falls_back_to_a_typical_bezel() -> None:
    screen = inspect_screen(mockup("#0b1426"), rough_box())

    assert screen.crop is not None
    left, _, right, _ = as_pixels(screen.crop)
    assert BODY[0] < left < SCREEN[0] + 20
    assert SCREEN[2] - 20 < right < BODY[2]


def test_a_plain_screenshot_has_no_crop() -> None:
    screen = inspect_screen(mockup(), [])

    assert screen.crop is None
    assert (screen.width, screen.height) == (WIDTH, HEIGHT)
    assert screen.product_width_px == WIDTH


def test_a_box_covering_the_whole_image_is_not_a_mockup() -> None:
    assert inspect_screen(mockup(), [0, 0, 1000, 1000]).crop is None


def test_focus_is_re_expressed_inside_the_crop() -> None:
    crop = (0.4, 0.1, 0.25, 0.8)

    assert crop_focus((0.45, 0.3, 0.1, 0.2), crop) == pytest.approx((0.2, 0.25, 0.4, 0.25))
    assert crop_focus((0.0, 0.0, 0.1, 0.1), crop) is None
    assert crop_focus(None, crop) is None
    assert crop_focus((0.1, 0.1, 0.2, 0.2), None) == (0.1, 0.1, 0.2, 0.2)


def test_a_focus_box_mostly_outside_the_display_is_dropped() -> None:
    crop = (0.4, 0.1, 0.25, 0.8)

    assert crop_focus((0.3, 0.3, 0.2, 0.1), crop) is None
    assert crop_focus((0.42, 0.3, 0.2, 0.1), crop) is not None
