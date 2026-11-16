"""StegaShield Steganographic Core Module.

Implements carrier capacity calculation, sequential salt prefixing, PRNG channel
permutation, LSB replacement and LSB matching embedding, and lossless extraction.
"""

from __future__ import annotations

import os
import struct
from typing import Any, Final

import numpy as np
from PIL import Image

from app.core.crypto import (
    NONCE_SIZE_BYTES,
    SALT_SIZE_BYTES,
    StegaShieldError,
    WRONG_PASSWORD_OR_NO_DATA,
    decrypt_payload,
    derive_keys,
    encrypt_payload,
)
from app.core.metrics import calculate_metrics

# --- Constants ---
PROTOCOL_VERSION: Final[int] = 1
MAX_IMAGE_PIXELS: Final[int] = 16_000_000  # 16 Megapixels (e.g. 4000x4000)
MAX_FILE_SIZE_BYTES: Final[int] = 10 * 1024 * 1024  # 10 MB
SALT_SLOTS: Final[int] = SALT_SIZE_BYTES * 8  # 128 channel slots
HEADER_OVERHEAD_BITS: Final[int] = 400  # 128 salt + 96 nonce + 32 len + 128 tag + 16 header
MIN_CIPHERTEXT_BYTES: Final[int] = 18  # 1 byte type + 1 byte fn_len + 16 bytes tag

SUPPORTED_MODES: Final[tuple[str, ...]] = ("RGB", "RGBA", "L")
METHOD_LSB_REPLACEMENT: Final[str] = "lsb_replacement"
METHOD_LSB_MATCHING: Final[str] = "lsb_matching"
SUPPORTED_METHODS: Final[tuple[str, ...]] = (
    METHOD_LSB_REPLACEMENT,
    METHOD_LSB_MATCHING,
)


def validate_cover_image(cover_image: Image.Image) -> Image.Image:
    """Validates cover image dimensions and mode, returning a clean RGB image.

    Args:
        cover_image: Pillow Image to validate.

    Returns:
        Image.Image: Normalized RGB Image.

    Raises:
        ValueError: If resolution exceeds 16 MP or mode is unsupported.
    """
    total_pixels = cover_image.width * cover_image.height
    if total_pixels > MAX_IMAGE_PIXELS:
        raise ValueError(
            f"Cover image exceeds 16 megapixels limit: {cover_image.width}x"
            f"{cover_image.height} ({total_pixels} pixels, max {MAX_IMAGE_PIXELS})"
        )

    if cover_image.mode not in SUPPORTED_MODES:
        raise ValueError(
            f"Unsupported image mode '{cover_image.mode}'. Supported modes: "
            f"{', '.join(SUPPORTED_MODES)}"
        )

    if cover_image.mode != "RGB":
        return cover_image.convert("RGB")
    return cover_image.copy()


def calculate_capacity(cover_image: Image.Image) -> dict[str, int]:
    """Calculates carrier channel capacity and protocol overhead for a cover image.

    Args:
        cover_image: Cover image to inspect.

    Returns:
        dict[str, int]: Capacity metrics including total_channels, overhead_bits,
                        usable_bits, and usable_bytes.
    """
    total_slots = cover_image.width * cover_image.height * 3
    usable_bits = max(0, total_slots - HEADER_OVERHEAD_BITS)
    usable_bytes = usable_bits // 8

    return {
        "total_channels": total_slots,
        "overhead_bits": HEADER_OVERHEAD_BITS,
        "usable_bits": usable_bits,
        "usable_bytes": usable_bytes,
        "max_resolution_pixels": MAX_IMAGE_PIXELS,
    }


def embed(
    cover_image: Image.Image,
    payload: bytes,
    password: str,
    method: str = METHOD_LSB_REPLACEMENT,
    is_file: bool = False,
    filename: str = "",
) -> tuple[Image.Image, dict[str, Any]]:
    """Embeds encrypted payload into cover image using sequential salt prefix + permuted remaining slots.

    Args:
        cover_image: Cover image (PNG, JPEG, BMP).
        payload: Raw payload bytes to encrypt and hide.
        password: Plaintext password for encryption key and permutation derivation.
        method: Embedding method ('lsb_replacement' or 'lsb_matching').
        is_file: True if payload represents a file, False for text.
        filename: Optional filename if is_file is True (max 255 bytes UTF-8).

    Returns:
        tuple[Image.Image, dict[str, Any]]: (stego_image, metrics_dict) where stego_image
        is an RGB PIL Image and metrics_dict contains MSE, PSNR, SSIM, and capacity stats.

    Raises:
        ValueError: If method is unsupported, payload is empty, filename exceeds 255 bytes,
                    cover image exceeds 16 MP, or payload exceeds available capacity.
    """
    if method not in SUPPORTED_METHODS:
        raise ValueError(
            f"Unsupported embedding method '{method}'. Supported methods: "
            f"{', '.join(SUPPORTED_METHODS)}"
        )

    if len(payload) == 0:
        raise ValueError("Payload cannot be empty")

    # 1. Validate and normalize cover image to RGB
    cover_rgb = validate_cover_image(cover_image)
    width, height = cover_rgb.size
    total_slots = width * height * 3

    if total_slots < HEADER_OVERHEAD_BITS:
        raise ValueError(
            f"Cover image too small: {total_slots} channels available, minimum "
            f"{HEADER_OVERHEAD_BITS} channels required"
        )

    # 2. Pre-allocation capacity bounds check
    fn_bytes = filename.encode("utf-8") if is_file else b""
    if len(fn_bytes) > 255:
        raise ValueError(f"Filename exceeds maximum of 255 UTF-8 bytes: {len(fn_bytes)}")

    required_bits = HEADER_OVERHEAD_BITS + 8 * (len(fn_bytes) + len(payload))
    if required_bits > total_slots:
        raise ValueError(
            f"Payload requires {required_bits} bits ({required_bits // 8} bytes), "
            f"but cover image capacity is {total_slots} bits ({total_slots // 8} bytes)"
        )

    # 3. Cryptographic derivation and authenticated encryption
    salt = os.urandom(SALT_SIZE_BYTES)
    enc_key, perm_key = derive_keys(password, salt)
    nonce, ct_with_tag = encrypt_payload(
        payload, enc_key, is_file=is_file, filename=filename
    )

    ct_len = len(ct_with_tag)
    perm_payload = nonce + struct.pack(">I", ct_len) + ct_with_tag
    perm_bits = np.unpackbits(np.frombuffer(perm_payload, dtype=np.uint8))
    salt_bits = np.unpackbits(np.frombuffer(salt, dtype=np.uint8))

    # 4. PRNG Permutation of remaining slots [128 .. total_slots - 1]
    n_remaining = total_slots - SALT_SLOTS
    seed = int.from_bytes(perm_key[:8], "big")
    rng = np.random.default_rng(seed)
    perm = rng.permutation(n_remaining).astype(np.int64)

    payload_indices = perm[: len(perm_bits)] + SALT_SLOTS
    all_indices = np.concatenate(
        [np.arange(SALT_SLOTS, dtype=np.int64), payload_indices]
    )
    all_bits = np.concatenate([salt_bits, perm_bits])

    # 5. Embedding
    arr = np.array(cover_rgb, dtype=np.uint8, copy=True)
    flat = arr.reshape(-1)

    if method == METHOD_LSB_REPLACEMENT:
        # NumPy 2.x bitwise safe: use 0xFE instead of ~1
        flat[all_indices] = (flat[all_indices] & 0xFE) | all_bits
    elif method == METHOD_LSB_MATCHING:
        target_channels = flat[all_indices]
        diff = (target_channels & 1) != all_bits
        if np.any(diff):
            diff_indices = all_indices[diff]
            c_vals = flat[diff_indices].astype(np.int16)
            choices = np.random.choice(
                np.array([-1, 1], dtype=np.int16), size=len(diff_indices)
            )
            choices[c_vals == 0] = 1
            choices[c_vals == 255] = -1
            flat[diff_indices] = (c_vals + choices).astype(np.uint8)

    stego_image = Image.fromarray(arr.reshape(height, width, 3), mode="RGB")

    # 6. Metrics Calculation
    metrics_result: dict[str, Any] = dict(calculate_metrics(cover_rgb, stego_image))
    metrics_result.update(
        {
            "capacity_total_bits": total_slots,
            "payload_bits": required_bits,
            "capacity_used_ratio": float(required_bits / total_slots),
            "method": method,
        }
    )

    return stego_image, metrics_result


def extract(stego_image: Image.Image, password: str) -> tuple[bytes, bool, str]:
    """Extracts payload from stego image. Raises StegaShieldError(WRONG_PASSWORD_OR_NO_DATA) on any failure.

    Args:
        stego_image: Stego image to extract from.
        password: Password used during embedding.

    Returns:
        tuple[bytes, bool, str]: (data, is_file, filename)

    Raises:
        StegaShieldError: If password is wrong, image has no payload, data is corrupted,
                          or image is too small. Uniform message: "WRONG_PASSWORD_OR_NO_DATA".
    """
    try:
        # 1. Validate image
        if stego_image.mode not in SUPPORTED_MODES:
            raise StegaShieldError(WRONG_PASSWORD_OR_NO_DATA)
        stego_rgb = (
            stego_image.convert("RGB")
            if stego_image.mode != "RGB"
            else stego_image
        )

        arr = np.array(stego_rgb, dtype=np.uint8)
        flat = arr.reshape(-1)
        total_slots = len(flat)

        if total_slots < HEADER_OVERHEAD_BITS:
            raise StegaShieldError(WRONG_PASSWORD_OR_NO_DATA)

        # 2. Extract salt from sequential prefix [0 .. 127]
        salt_bits = flat[:SALT_SLOTS] & 1
        salt = np.packbits(salt_bits).tobytes()

        # 3. Derive keys
        enc_key, perm_key = derive_keys(password, salt)

        # 4. PRNG Permutation of remaining slots
        n_remaining = total_slots - SALT_SLOTS
        seed = int.from_bytes(perm_key[:8], "big")
        rng = np.random.default_rng(seed)
        perm = rng.permutation(n_remaining).astype(np.int64)

        # 5. Extract header (12-byte nonce + 4-byte length = 128 bits)
        header_indices = perm[:128] + SALT_SLOTS
        header_bits = flat[header_indices] & 1
        header_bytes = np.packbits(header_bits).tobytes()

        nonce = header_bytes[:NONCE_SIZE_BYTES]
        ct_len = struct.unpack(">I", header_bytes[NONCE_SIZE_BYTES:16])[0]

        total_perm_bits = (16 + ct_len) * 8
        if ct_len < MIN_CIPHERTEXT_BYTES or total_perm_bits > n_remaining:
            raise StegaShieldError(WRONG_PASSWORD_OR_NO_DATA)

        # 6. Extract ciphertext with tag
        ct_indices = perm[128:total_perm_bits] + SALT_SLOTS
        ct_bits = flat[ct_indices] & 1
        ct_with_tag = np.packbits(ct_bits).tobytes()

        # 7. Decrypt authenticated payload
        return decrypt_payload(nonce, ct_with_tag, enc_key)

    except StegaShieldError:
        raise
    except Exception:
        raise StegaShieldError(WRONG_PASSWORD_OR_NO_DATA) from None
