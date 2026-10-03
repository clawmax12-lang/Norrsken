"""Content-based validation of uploaded images (FR-01).

File extensions and client-declared types are attacker-controlled, so an upload counts as an
image only if Pillow decodes it as PNG or JPEG. Size and pixel caps bound memory use before any
pixel is decoded, which blocks decompression bombs.
"""

import io
from dataclasses import dataclass

from PIL import Image, UnidentifiedImageError

from preflight.errors import PreflightValidationError

MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_IMAGE_PIXELS = 25_000_000

_EXTENSION_BY_FORMAT = {"PNG": "png", "JPEG": "jpg"}
_DECODE_FAILURES = (UnidentifiedImageError, Image.DecompressionBombError, OSError, SyntaxError)


@dataclass(frozen=True)
class ValidatedImage:
    """Bytes that decoded as a supported image, with the extension we store them under."""

    content: bytes
    extension: str


def validate_image(content: bytes, *, label: str) -> ValidatedImage:
    """Return ``content`` as a :class:`ValidatedImage` or raise ``PreflightValidationError``.

    Args:
        content: The raw upload.
        label: Human-readable name used in error messages, such as ``"screenshot 2"``. The
            client's filename is deliberately never used.
    """
    if not content:
        raise PreflightValidationError(f"{label} is empty")
    if len(content) > MAX_IMAGE_BYTES:
        raise PreflightValidationError(f"{label} is larger than {MAX_IMAGE_BYTES // 2**20} MB")
    try:
        with Image.open(io.BytesIO(content), formats=list(_EXTENSION_BY_FORMAT)) as image:
            _require_reasonable_size(image, label)
            image.load()
            extension = _EXTENSION_BY_FORMAT[image.format or ""]
    except _DECODE_FAILURES as exc:
        raise PreflightValidationError(f"{label} is not a readable PNG or JPG image") from exc
    return ValidatedImage(content=content, extension=extension)


def _require_reasonable_size(image: Image.Image, label: str) -> None:
    width, height = image.size
    if width * height > MAX_IMAGE_PIXELS:
        raise PreflightValidationError(
            f"{label} has {width * height:,} pixels; the limit is {MAX_IMAGE_PIXELS:,}"
        )
