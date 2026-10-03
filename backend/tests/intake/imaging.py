"""Test-only synthetic images. Nothing here is a real customer screenshot."""

import io

from PIL import Image


def image_bytes(
    image_format: str = "PNG", size: tuple[int, int] = (64, 128), mode: str = "RGB"
) -> bytes:
    """Encode a flat-colour image; ``image_format`` is any Pillow format name."""
    buffer = io.BytesIO()
    Image.new(mode, size, "white" if mode != "1" else 1).save(buffer, format=image_format)
    return buffer.getvalue()


def png(size: tuple[int, int] = (64, 128)) -> bytes:
    """A small valid PNG."""
    return image_bytes("PNG", size)


def jpeg(size: tuple[int, int] = (64, 128)) -> bytes:
    """A small valid JPEG."""
    return image_bytes("JPEG", size)


def three_screenshots() -> list[bytes]:
    """The minimum valid set of screenshots."""
    return [png(), jpeg(), png()]
