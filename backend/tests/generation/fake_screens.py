"""Test-only synthetic app screenshots (never shipped, never shown as product output).

Pillow draws plausible UI (cards, charts, lists) so renders in tests and visual checks have
realistic pixels to frame. All text is placeholder copy that exists only inside these images.
"""

from collections.abc import Callable
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

PHONE = (1170, 2532)
DESKTOP = (2400, 1500)
_INK = (28, 28, 34)
_MUTED = (130, 134, 146)
_CARD = (255, 255, 255)


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    return ImageFont.load_default(size=size)


def _status_bar(draw: ImageDraw.ImageDraw, width: int) -> None:
    draw.text((90, 70), "9:41", fill=_INK, font=_font(44))
    draw.rounded_rectangle((width - 210, 78, width - 90, 108), radius=14, fill=_INK)


def _card(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    draw.rounded_rectangle(box, radius=44, fill=_CARD, outline=(232, 234, 240), width=3)


def dashboard(accent: tuple[int, int, int]) -> Image.Image:
    """A metrics dashboard: header, hero card with bar chart, two stat cards."""
    image = Image.new("RGB", PHONE, (244, 245, 250))
    draw = ImageDraw.Draw(image)
    _status_bar(draw, PHONE[0])
    draw.text((90, 190), "Today", fill=_INK, font=_font(96))
    draw.text((90, 310), "Tuesday, 3 October", fill=_MUTED, font=_font(46))
    _card(draw, (60, 440, 1110, 1260))
    draw.text((120, 500), "Bookings", fill=_MUTED, font=_font(46))
    draw.text((120, 580), "128", fill=_INK, font=_font(150))
    heights = (180, 260, 220, 340, 300, 420, 500)
    for i, h in enumerate(heights):
        x = 140 + i * 140
        shade = tuple(min(255, c + (len(heights) - i) * 12) for c in accent)
        draw.rounded_rectangle((x, 1200 - h, x + 90, 1200), radius=26, fill=shade)
    for col, label in enumerate(("Covers", "Wait")):
        left = 60 + col * 535
        _card(draw, (left, 1310, left + 515, 1760))
        draw.text((left + 50, 1370), label, fill=_MUTED, font=_font(44))
        draw.text((left + 50, 1450), "46" if col == 0 else "12m", fill=_INK, font=_font(120))
        draw.rounded_rectangle((left + 50, 1620, left + 465, 1660), radius=20, fill=(228, 230, 238))
        draw.rounded_rectangle((left + 50, 1620, left + 300, 1660), radius=20, fill=accent)
    draw.rounded_rectangle((60, 1830, 1110, 2010), radius=90, fill=accent)
    draw.text((420, 1880), "New booking", fill=(255, 255, 255), font=_font(64))
    return image


def listing(accent: tuple[int, int, int]) -> Image.Image:
    """A list screen with avatars and status pills."""
    image = Image.new("RGB", PHONE, (250, 250, 252))
    draw = ImageDraw.Draw(image)
    _status_bar(draw, PHONE[0])
    draw.text((90, 190), "Tables", fill=_INK, font=_font(96))
    for row in range(7):
        top = 400 + row * 270
        _card(draw, (60, top, 1110, top + 230))
        shade = tuple((c + row * 28) % 256 for c in accent)
        draw.ellipse((110, top + 40, 260, top + 190), fill=shade)
        draw.text((300, top + 50), f"Table {row + 1}", fill=_INK, font=_font(60))
        draw.text((300, top + 130), "Seats 4 - Window", fill=_MUTED, font=_font(40))
        pill = accent if row % 2 == 0 else (225, 228, 236)
        draw.rounded_rectangle((850, top + 80, 1050, top + 150), radius=35, fill=pill)
    return image


def conversation(accent: tuple[int, int, int]) -> Image.Image:
    """A chat screen with alternating bubbles."""
    image = Image.new("RGB", PHONE, (255, 255, 255))
    draw = ImageDraw.Draw(image)
    _status_bar(draw, PHONE[0])
    draw.text((90, 190), "Messages", fill=_INK, font=_font(96))
    for i in range(8):
        mine = i % 2 == 1
        width = 520 + (i * 97) % 300
        left = 1110 - width if mine else 60
        top = 400 + i * 230
        fill = accent if mine else (238, 240, 246)
        draw.rounded_rectangle((left, top, left + width, top + 170), radius=60, fill=fill)
        draw.rounded_rectangle(
            (left + 50, top + 60, left + width - 80, top + 90),
            radius=15,
            fill=(255, 255, 255) if mine else (200, 204, 214),
        )
    return image


def desktop(accent: tuple[int, int, int]) -> Image.Image:
    """A wide web-app screen with sidebar and chart tiles."""
    image = Image.new("RGB", DESKTOP, (246, 247, 251))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 420, DESKTOP[1]), fill=(255, 255, 255))
    for i in range(6):
        draw.rounded_rectangle(
            (50, 140 + i * 130, 370, 220 + i * 130),
            radius=24,
            fill=accent if i == 0 else (240, 241, 246),
        )
    for col in range(3):
        left = 500 + col * 620
        _card(draw, (left, 140, left + 580, 560))
        draw.text(
            (left + 50, 190), ("Revenue", "Guests", "Rating")[col], fill=_MUTED, font=_font(44)
        )
        draw.text((left + 50, 270), ("$12.4k", "1,204", "4.9")[col], fill=_INK, font=_font(120))
    _card(draw, (500, 620, 2340, 1400))
    points = [(560 + i * 150, 1300 - (i * 53 % 380) - i * 20) for i in range(12)]
    draw.line(points, fill=accent, width=12, joint="curve")
    return image


SCREEN_MAKERS: tuple[Callable[[tuple[int, int, int]], Image.Image], ...] = (
    dashboard,
    listing,
    conversation,
    desktop,
)


def write_screens(directory: Path, accent: tuple[int, int, int] = (91, 91, 214)) -> tuple[str, ...]:
    """Write one PNG per maker into ``directory`` and return their file names."""
    directory.mkdir(parents=True, exist_ok=True)
    names = []
    for index, maker in enumerate(SCREEN_MAKERS, start=1):
        name = f"{index}.png"
        maker(accent).save(directory / name)
        names.append(name)
    return tuple(names)
