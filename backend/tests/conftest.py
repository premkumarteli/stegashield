"""StegaShield Pytest Fixtures and Test Helpers."""

from __future__ import annotations

import io
import numpy as np
import pytest
from PIL import Image

from app.core.crypto import derive_keys


@pytest.fixture(scope="session")
def test_password() -> str:
    return "StegaShieldSecurePassword2026!"


@pytest.fixture(scope="session")
def wrong_password() -> str:
    return "IncorrectAttackerPassword999!"


@pytest.fixture(scope="session")
def fixed_salt() -> bytes:
    return b"0123456789abcdef"


@pytest.fixture(scope="session")
def derived_test_keys(test_password: str, fixed_salt: bytes) -> tuple[bytes, bytes]:
    """Pre-derives keys once per session to accelerate stego tests."""
    return derive_keys(test_password, fixed_salt)


@pytest.fixture
def small_text_payload() -> bytes:
    return b"StegaShield Milestone 1 verified payload content."


@pytest.fixture
def large_text_payload() -> bytes:
    return b"StegaShield payload " * 1000  # 20 KB


@pytest.fixture
def binary_file_payload() -> bytes:
    # Includes all byte values from 0x00 to 0xFF repeatedly
    return bytes(range(256)) * 16  # 4 KB


@pytest.fixture
def sample_filename() -> str:
    return "secret_document.pdf"


@pytest.fixture
def small_cover_png() -> Image.Image:
    """Creates a 64x64 RGB gradient image."""
    arr = np.zeros((64, 64, 3), dtype=np.uint8)
    for y in range(64):
        for x in range(64):
            arr[y, x] = [x * 4, y * 4, (x + y) * 2]
    return Image.fromarray(arr, mode="RGB")


@pytest.fixture
def medium_cover_png() -> Image.Image:
    """Creates a 256x256 RGB image with realistic texture."""
    np.random.seed(42)
    arr = np.random.randint(20, 235, (256, 256, 3), dtype=np.uint8)
    return Image.fromarray(arr, mode="RGB")


@pytest.fixture
def cover_jpeg(medium_cover_png: Image.Image) -> Image.Image:
    buf = io.BytesIO()
    medium_cover_png.save(buf, format="JPEG", quality=95)
    buf.seek(0)
    return Image.open(buf)


@pytest.fixture
def cover_bmp(small_cover_png: Image.Image) -> Image.Image:
    buf = io.BytesIO()
    small_cover_png.save(buf, format="BMP")
    buf.seek(0)
    return Image.open(buf)


@pytest.fixture
def cover_rgba(small_cover_png: Image.Image) -> Image.Image:
    return small_cover_png.convert("RGBA")


@pytest.fixture
def cover_grayscale(small_cover_png: Image.Image) -> Image.Image:
    return small_cover_png.convert("L")
