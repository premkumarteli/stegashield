"""Comprehensive Unit Tests for StegaShield Steganography Core Module.

Covers capacity pre-checks, sequential prefix salt, PRNG permutation, LSB replacement,
LSB matching, image format conversions, and uniform error handling on extraction.
"""

from __future__ import annotations

import io
import numpy as np
import pytest
from PIL import Image

from app.core.crypto import (
    WRONG_PASSWORD_OR_NO_DATA,
    StegaShieldError,
)
from app.core.stego import (
    HEADER_OVERHEAD_BITS,
    METHOD_LSB_MATCHING,
    METHOD_LSB_REPLACEMENT,
    calculate_capacity,
    embed,
    extract,
    validate_cover_image,
)


def test_capacity_calculation_exact(small_cover_png: Image.Image) -> None:
    """Asserts calculate_capacity matches exact formula: floor((W * H * 3 - 400) / 8)."""
    cap = calculate_capacity(small_cover_png)
    total_channels = 64 * 64 * 3  # 12288
    expected_usable_bits = total_channels - HEADER_OVERHEAD_BITS  # 12288 - 400 = 11888
    expected_usable_bytes = expected_usable_bits // 8  # 1486

    assert cap["total_channels"] == total_channels
    assert cap["overhead_bits"] == HEADER_OVERHEAD_BITS
    assert cap["usable_bits"] == expected_usable_bits
    assert cap["usable_bytes"] == expected_usable_bytes


def test_capacity_rejection_before_allocation(small_cover_png: Image.Image, test_password: str) -> None:
    """Asserts payload exceeding calculated capacity raises ValueError before allocation."""
    cap = calculate_capacity(small_cover_png)
    oversized_payload = b"X" * (cap["usable_bytes"] + 1)

    with pytest.raises(ValueError, match="Payload requires"):
        embed(small_cover_png, oversized_payload, test_password)


def test_empty_payload_rejection(small_cover_png: Image.Image, test_password: str) -> None:
    """Asserts embedding b'' raises ValueError('Payload cannot be empty')."""
    with pytest.raises(ValueError, match="Payload cannot be empty"):
        embed(small_cover_png, b"", test_password)


def test_image_dimension_guards(test_password: str) -> None:
    """Asserts image > 16MP and image < 400 channels are rejected."""
    # > 16 Megapixels
    huge_img = Image.new("RGB", (4001, 4000))
    with pytest.raises(ValueError, match="Cover image exceeds 16 megapixels limit"):
        validate_cover_image(huge_img)

    # < 400 channels (10x10x3 = 300)
    tiny_img = Image.new("RGB", (10, 10))
    with pytest.raises(ValueError, match="Cover image too small"):
        embed(tiny_img, b"data", test_password)


def test_cover_format_png_lossless(small_cover_png: Image.Image, test_password: str, small_text_payload: bytes) -> None:
    """Tests PNG input produces lossless PNG output that extracts identically."""
    stego_img, metrics = embed(small_cover_png, small_text_payload, test_password)

    # Save to in-memory PNG and reload
    buf = io.BytesIO()
    stego_img.save(buf, format="PNG")
    buf.seek(0)
    reloaded = Image.open(buf)

    data, is_file, fn = extract(reloaded, test_password)
    assert data == small_text_payload
    assert is_file is False
    assert fn == ""


def test_cover_format_jpeg_converted_to_png(cover_jpeg: Image.Image, test_password: str, small_text_payload: bytes) -> None:
    """Tests JPEG input is decoded and stego output is strictly saved as lossless PNG."""
    stego_img, _ = embed(cover_jpeg, small_text_payload, test_password)
    assert stego_img.mode == "RGB"

    buf = io.BytesIO()
    stego_img.save(buf, format="PNG")
    buf.seek(0)
    reloaded = Image.open(buf)

    data, is_file, fn = extract(reloaded, test_password)
    assert data == small_text_payload


def test_cover_format_bmp_converted_to_png(cover_bmp: Image.Image, test_password: str, small_text_payload: bytes) -> None:
    """Tests BMP input is decoded and stego output is strictly saved as lossless PNG."""
    stego_img, _ = embed(cover_bmp, small_text_payload, test_password)
    assert stego_img.mode == "RGB"

    data, is_file, fn = extract(stego_img, test_password)
    assert data == small_text_payload


def test_cover_format_rgba_alpha_discarded(cover_rgba: Image.Image, test_password: str, small_text_payload: bytes) -> None:
    """Asserts alpha channel is not modified or used for embedding; stego image is RGB."""
    assert cover_rgba.mode == "RGBA"
    stego_img, _ = embed(cover_rgba, small_text_payload, test_password)
    assert stego_img.mode == "RGB"

    data, is_file, fn = extract(stego_img, test_password)
    assert data == small_text_payload


def test_cover_format_grayscale_converted_to_rgb(cover_grayscale: Image.Image, test_password: str, small_text_payload: bytes) -> None:
    """Tests Grayscale (mode L) image is converted to RGB before embedding."""
    assert cover_grayscale.mode == "L"
    stego_img, _ = embed(cover_grayscale, small_text_payload, test_password)
    assert stego_img.mode == "RGB"

    data, is_file, fn = extract(stego_img, test_password)
    assert data == small_text_payload


def test_salt_sequential_prefix_slots(small_cover_png: Image.Image, test_password: str, small_text_payload: bytes) -> None:
    """Validates that slots [0 .. 127] contain the exact 16 bytes of salt."""
    stego_img, _ = embed(small_cover_png, small_text_payload, test_password)
    arr = np.array(stego_img, dtype=np.uint8).reshape(-1)
    prefix_bits = arr[:128] & 1
    extracted_salt = np.packbits(prefix_bits).tobytes()

    assert len(extracted_salt) == 16
    assert isinstance(extracted_salt, bytes)


def test_permutation_prefix_consistency(medium_cover_png: Image.Image, test_password: str, large_text_payload: bytes) -> None:
    """Asserts slot sequence used for header matches the first sequence for full payload."""
    stego_img, _ = embed(medium_cover_png, large_text_payload, test_password)
    data, is_file, fn = extract(stego_img, test_password)
    assert data == large_text_payload


def test_lsb_replacement_roundtrip_text(small_cover_png: Image.Image, test_password: str, small_text_payload: bytes) -> None:
    """Embeds and extracts text payload via lsb_replacement; verifies lossless recovery."""
    stego_img, metrics = embed(
        small_cover_png,
        small_text_payload,
        test_password,
        method=METHOD_LSB_REPLACEMENT,
        is_file=False,
    )
    data, is_file, fn = extract(stego_img, test_password)
    assert data == small_text_payload
    assert is_file is False
    assert fn == ""
    assert metrics["method"] == METHOD_LSB_REPLACEMENT


def test_lsb_replacement_roundtrip_file(medium_cover_png: Image.Image, test_password: str, binary_file_payload: bytes, sample_filename: str) -> None:
    """Embeds and extracts binary file payload via lsb_replacement; verifies filename and content match."""
    stego_img, metrics = embed(
        medium_cover_png,
        binary_file_payload,
        test_password,
        method=METHOD_LSB_REPLACEMENT,
        is_file=True,
        filename=sample_filename,
    )
    data, is_file, fn = extract(stego_img, test_password)
    assert data == binary_file_payload
    assert is_file is True
    assert fn == sample_filename


def test_lsb_replacement_pixel_bounds(small_cover_png: Image.Image, test_password: str, small_text_payload: bytes) -> None:
    """Asserts pixel values differ by at most 1, and (stego_val & 0xFE) == (cover_val & 0xFE)."""
    stego_img, _ = embed(
        small_cover_png,
        small_text_payload,
        test_password,
        method=METHOD_LSB_REPLACEMENT,
    )
    c_arr = np.array(small_cover_png, dtype=np.int16)
    s_arr = np.array(stego_img, dtype=np.int16)

    diff = np.abs(c_arr - s_arr)
    assert np.all(diff <= 1)
    # LSB replacement strictly preserves upper 7 bits
    assert np.all((c_arr.astype(np.uint8) & 0xFE) == (s_arr.astype(np.uint8) & 0xFE))


def test_lsb_matching_roundtrip_text(small_cover_png: Image.Image, test_password: str, small_text_payload: bytes) -> None:
    """Embeds and extracts text payload via lsb_matching; verifies lossless recovery."""
    stego_img, metrics = embed(
        small_cover_png,
        small_text_payload,
        test_password,
        method=METHOD_LSB_MATCHING,
        is_file=False,
    )
    data, is_file, fn = extract(stego_img, test_password)
    assert data == small_text_payload
    assert is_file is False
    assert fn == ""
    assert metrics["method"] == METHOD_LSB_MATCHING


def test_lsb_matching_roundtrip_file(medium_cover_png: Image.Image, test_password: str, binary_file_payload: bytes, sample_filename: str) -> None:
    """Embeds and extracts binary file payload via lsb_matching; verifies filename and content match."""
    stego_img, metrics = embed(
        medium_cover_png,
        binary_file_payload,
        test_password,
        method=METHOD_LSB_MATCHING,
        is_file=True,
        filename=sample_filename,
    )
    data, is_file, fn = extract(stego_img, test_password)
    assert data == binary_file_payload
    assert is_file is True
    assert fn == sample_filename


def test_lsb_matching_pixel_bounds(small_cover_png: Image.Image, test_password: str, small_text_payload: bytes) -> None:
    """Asserts modified pixels differ by +-1 without underflow (<0) or overflow (>255)."""
    stego_img, _ = embed(
        small_cover_png,
        small_text_payload,
        test_password,
        method=METHOD_LSB_MATCHING,
    )
    c_arr = np.array(small_cover_png, dtype=np.int16)
    s_arr = np.array(stego_img, dtype=np.int16)

    diff = np.abs(c_arr - s_arr)
    assert np.all(diff <= 1)
    assert np.all((s_arr >= 0) & (s_arr <= 255))


def test_extract_wrong_password_uniform_error(small_cover_png: Image.Image, test_password: str, wrong_password: str, small_text_payload: bytes) -> None:
    """Asserts extracting with wrong password raises StegaShieldError(WRONG_PASSWORD_OR_NO_DATA)."""
    stego_img, _ = embed(small_cover_png, small_text_payload, test_password)

    with pytest.raises(StegaShieldError) as exc_info:
        extract(stego_img, wrong_password)
    assert str(exc_info.value) == WRONG_PASSWORD_OR_NO_DATA
    assert exc_info.value.__cause__ is None


def test_extract_clean_cover_uniform_error(small_cover_png: Image.Image, test_password: str) -> None:
    """Asserts attempting to extract from an unmodified clean cover image raises uniform error."""
    with pytest.raises(StegaShieldError) as exc_info:
        extract(small_cover_png, test_password)
    assert str(exc_info.value) == WRONG_PASSWORD_OR_NO_DATA
    assert exc_info.value.__cause__ is None


def test_extract_tampered_salt_uniform_error(small_cover_png: Image.Image, test_password: str, small_text_payload: bytes) -> None:
    """Asserts flipping 1 bit in slots [0 .. 127] raises StegaShieldError(WRONG_PASSWORD_OR_NO_DATA)."""
    stego_img, _ = embed(small_cover_png, small_text_payload, test_password)

    arr = np.array(stego_img, dtype=np.uint8)
    flat = arr.reshape(-1)
    flat[0] ^= 1  # Corrupt salt
    tampered_img = Image.fromarray(arr, mode="RGB")

    with pytest.raises(StegaShieldError) as exc_info:
        extract(tampered_img, test_password)
    assert str(exc_info.value) == WRONG_PASSWORD_OR_NO_DATA


def test_extract_tampered_stego_bits_uniform_error(small_cover_png: Image.Image, test_password: str, small_text_payload: bytes) -> None:
    """Asserts flipping 1 bit in permuted payload slots raises StegaShieldError(WRONG_PASSWORD_OR_NO_DATA)."""
    stego_img, _ = embed(small_cover_png, small_text_payload, test_password)

    arr = np.array(stego_img, dtype=np.uint8)
    flat = arr.reshape(-1)

    # Derive salt and perm_key to locate the exact first permuted slot
    salt = np.packbits(flat[:128] & 1).tobytes()
    from app.core.crypto import derive_keys
    _, perm_key = derive_keys(test_password, salt)
    rng = np.random.default_rng(int.from_bytes(perm_key[:8], "big"))
    perm = rng.permutation(len(flat) - 128)

    # Corrupt the first payload slot
    target_slot = perm[0] + 128
    flat[target_slot] ^= 1
    tampered_img = Image.fromarray(arr, mode="RGB")

    with pytest.raises(StegaShieldError) as exc_info:
        extract(tampered_img, test_password)
    assert str(exc_info.value) == WRONG_PASSWORD_OR_NO_DATA


def test_embed_returns_metrics_dict(small_cover_png: Image.Image, test_password: str, small_text_payload: bytes) -> None:
    """Verifies embed() returns (stego_image, metrics_dict) with MSE, PSNR, SSIM, and capacity."""
    stego_img, metrics = embed(small_cover_png, small_text_payload, test_password)

    assert isinstance(stego_img, Image.Image)
    assert "mse" in metrics and isinstance(metrics["mse"], float)
    assert "psnr" in metrics and isinstance(metrics["psnr"], float)
    assert "ssim" in metrics and isinstance(metrics["ssim"], float)
    assert metrics["capacity_total_bits"] == 64 * 64 * 3
    assert metrics["payload_bits"] == HEADER_OVERHEAD_BITS + 8 * len(small_text_payload)
    assert 0.0 < metrics["capacity_used_ratio"] < 1.0


def test_stego_additional_edge_cases(small_cover_png: Image.Image, test_password: str) -> None:
    """Tests unsupported methods, invalid filenames, unsupported modes, and small extract image."""
    # 1. Unsupported embedding method
    with pytest.raises(ValueError, match="Unsupported embedding method 'invalid_method'"):
        embed(small_cover_png, b"payload", test_password, method="invalid_method")

    # 2. Filename exceeds 255 bytes
    long_fn = "x" * 256
    with pytest.raises(ValueError, match="Filename exceeds maximum of 255 UTF-8 bytes"):
        embed(small_cover_png, b"payload", test_password, is_file=True, filename=long_fn)

    # 3. Unsupported cover mode in validate_cover_image
    cmyk_img = Image.new("CMYK", (40, 40))
    with pytest.raises(ValueError, match="Unsupported image mode 'CMYK'"):
        validate_cover_image(cmyk_img)

    # 4. Extract with unsupported mode
    with pytest.raises(StegaShieldError) as exc_info:
        extract(cmyk_img, test_password)
    assert str(exc_info.value) == WRONG_PASSWORD_OR_NO_DATA

    # 5. Extract with image having < 400 channels
    tiny_img = Image.new("RGB", (10, 10))
    with pytest.raises(StegaShieldError) as exc_info:
        extract(tiny_img, test_password)
    assert str(exc_info.value) == WRONG_PASSWORD_OR_NO_DATA

    # 6. Extract with bad image object raising generic exception
    class BadImage:
        mode = "RGB"

        def __array__(self, dtype=None, copy=None):
            raise RuntimeError("Unexpected buffer fault")

    with pytest.raises(StegaShieldError) as exc_info:
        extract(BadImage(), test_password)  # type: ignore[arg-type]
    assert str(exc_info.value) == WRONG_PASSWORD_OR_NO_DATA
