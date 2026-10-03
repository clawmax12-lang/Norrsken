import contextlib

import pytest
from hypothesis import given
from hypothesis import strategies as st

from preflight.errors import PreflightValidationError
from preflight.intake.images import MAX_IMAGE_BYTES, validate_image
from tests.intake.imaging import image_bytes, jpeg, png


def test_png_and_jpeg_are_accepted_by_content():
    assert validate_image(png(), label="s").extension == "png"
    assert validate_image(jpeg(), label="s").extension == "jpg"


@pytest.mark.parametrize("image_format", ["GIF", "WEBP", "BMP", "TIFF"])
def test_other_image_formats_are_rejected(image_format):
    with pytest.raises(PreflightValidationError, match="screenshot 1 is not a readable PNG or JPG"):
        validate_image(image_bytes(image_format), label="screenshot 1")


def test_text_is_rejected_whatever_it_is_called():
    with pytest.raises(PreflightValidationError, match="not a readable"):
        validate_image(b"<svg xmlns='http://www.w3.org/2000/svg'/>", label="logo")


def test_empty_upload_is_rejected():
    with pytest.raises(PreflightValidationError, match="is empty"):
        validate_image(b"", label="screenshot 2")


def test_oversized_upload_is_rejected_before_decoding():
    with pytest.raises(PreflightValidationError, match="larger than 10 MB"):
        validate_image(b"\x89PNG" + b"0" * MAX_IMAGE_BYTES, label="screenshot 1")


def test_a_file_at_the_size_limit_is_not_called_too_large():
    with pytest.raises(PreflightValidationError, match="not a readable"):
        validate_image(b"0" * MAX_IMAGE_BYTES, label="screenshot 1")


def test_truncated_image_is_rejected():
    with pytest.raises(PreflightValidationError, match="not a readable"):
        validate_image(png((400, 400))[:-40], label="screenshot 3")


def test_too_many_pixels_are_rejected_without_decoding():
    flat = image_bytes("PNG", (6000, 5000), mode="L")
    assert len(flat) < MAX_IMAGE_BYTES
    with pytest.raises(PreflightValidationError, match="30,000,000 pixels"):
        validate_image(flat, label="screenshot 1")


def test_decompression_bomb_is_rejected():
    bomb = image_bytes("PNG", (20000, 20000), mode="1")
    assert len(bomb) < MAX_IMAGE_BYTES
    with pytest.raises(PreflightValidationError):
        validate_image(bomb, label="screenshot 1")


@given(st.binary(max_size=2048))
def test_arbitrary_bytes_only_ever_fail_with_a_validation_error(data):
    with contextlib.suppress(PreflightValidationError):
        validate_image(data, label="upload")
