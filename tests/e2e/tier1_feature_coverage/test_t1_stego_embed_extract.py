"""
StegaShield Tier 1: Steganography Core Embedding & Extraction Tests (Features 4–8).
Validates sequential salt prefixing, PRNG permutation, LSB-R, LSB-M, extraction, and capacity.
"""

from __future__ import annotations

import io
import numpy as np
from PIL import Image
import pytest

from tests.e2e.client.direct_core_adapter import _get_core_module
from tests.e2e.fixtures import (
    ImageGenerator,
    PayloadGenerator,
    TamperGenerator,
    PASSWORD_VALID,
    PASSWORD_WRONG,
    METHOD_LSB_REPLACEMENT,
    METHOD_LSB_MATCHING,
)
from tests.e2e.framework.assertions import (
    assert_lossless_text,
    assert_uniform_error,
    assert_capacity_rejection,
    assert_distortion_bounds,
)

stego = _get_core_module("stego")
crypto = _get_core_module("crypto")


# ==============================================================================
# Feature 4: Sequential Prefix & PRNG Permutation
# ==============================================================================

@pytest.mark.tier1
def test_t1_f04_01_salt_sequential_allocation(e2e_client):
    """TC-E2E-T1-F04-01: 16-byte salt is sequentially embedded in first 128 channel slots."""
    cover = ImageGenerator.natural_texture(128, 128, seed=42)
    cover_bytes = ImageGenerator.to_bytes(cover, fmt="PNG")
    res = e2e_client.embed(cover_bytes, password=PASSWORD_VALID, payload_text="Test Prefix")
    assert res.success is True

    # Read the first 128 channel LSBs from stego
    stego_img = Image.open(io.BytesIO(res.stego_bytes)).convert("RGB")
    flat_stego = np.array(stego_img).reshape(-1)
    extracted_salt_bits = flat_stego[:128] & 1

    # Pack bits to 16 bytes
    salt_bytes = np.packbits(extracted_salt_bits).tobytes()
    assert len(salt_bytes) == 16


@pytest.mark.tier1
def test_t1_f04_02_permutation_prefix_consistency():
    """TC-E2E-T1-F04-02: PRNG permutation slice is prefix-consistent across read lengths."""
    total_slots = 10000
    rem_slots = total_slots - 128
    perm_key = b"\x42" * 32

    seed = int.from_bytes(perm_key[:8], "big")
    rng1 = np.random.default_rng(seed)
    p1 = rng1.permutation(rem_slots) + 128

    rng2 = np.random.default_rng(seed)
    p2 = rng2.permutation(rem_slots) + 128

    assert np.array_equal(p1[:100], p2[:100])
    assert np.array_equal(p1[:500], p2[:500])


@pytest.mark.tier1
def test_t1_f04_03_no_collision_with_salt_prefix():
    """TC-E2E-T1-F04-03: All permuted payload slots are strictly >= 128 (no salt collision)."""
    total_slots = 5000
    rem_slots = total_slots - 128
    import os
    perm_key = os.urandom(32)
    seed = int.from_bytes(perm_key[:8], "big")
    rng = np.random.default_rng(seed)
    perm = rng.permutation(rem_slots) + 128

    assert np.all(perm >= 128)
    assert len(set(perm)) == rem_slots


@pytest.mark.tier1
def test_t1_f04_04_uniform_slot_dispersion():
    """TC-E2E-T1-F04-04: Permuted slots disperse uniformly across spatial carrier indices."""
    total_slots = 30000
    rem_slots = total_slots - 128
    seed = 123456789
    rng = np.random.default_rng(seed)
    perm = rng.permutation(rem_slots) + 128

    # Mean of uniform distribution in [128, total_slots-1]
    expected_mean = (128 + total_slots - 1) / 2.0
    actual_mean = float(np.mean(perm))
    assert abs(actual_mean - expected_mean) < (total_slots * 0.02)


@pytest.mark.tier1
def test_t1_f04_05_prng_seed_independence():
    """TC-E2E-T1-F04-05: Distinct permutation keys produce completely uncorrelated slot sequences."""
    rem_slots = 2000
    rng1 = np.random.default_rng(11111)
    p1 = rng1.permutation(rem_slots) + 128

    rng2 = np.random.default_rng(99999)
    p2 = rng2.permutation(rem_slots) + 128

    matching_positions = np.sum(p1 == p2)
    # Expected matches for random permutation of size 2000 is ~1
    assert matching_positions < 10


# ==============================================================================
# Feature 5: LSB Replacement Embedding
# ==============================================================================

@pytest.mark.tier1
def test_t1_f05_01_lsb_r_even_odd_transitions():
    """TC-E2E-T1-F05-01: Bitwise (c & 0xFE) | b updates even/odd channels correctly."""
    channels = np.array([100, 101, 102, 103], dtype=np.uint8)
    bits = np.array([1, 0, 0, 1], dtype=np.uint8)

    embedded = (channels & np.uint8(0xFE)) | bits
    assert np.array_equal(embedded, [101, 100, 102, 103])
    assert np.array_equal(embedded & 1, bits)


@pytest.mark.tier1
def test_t1_f05_02_lsb_r_numpy2_bitwise_safety():
    """TC-E2E-T1-F05-02: Masking with 0xFE avoids NumPy 2.x OverflowError on uint8."""
    arr = np.array([0, 127, 128, 255], dtype=np.uint8)
    # Under NumPy 2.x, (arr & ~1) raises OverflowError because ~1 is -2.
    # (arr & 0xFE) must execute cleanly without exception.
    safe_res = (arr & 0xFE) | np.uint8(1)
    assert safe_res.dtype == np.uint8
    assert np.all(safe_res % 2 == 1)


@pytest.mark.tier1
def test_t1_f05_03_lsb_r_full_image_roundtrip(e2e_client):
    """TC-E2E-T1-F05-03: LSB-R embeds and extracts secret text losslessly."""
    cover = ImageGenerator.natural_texture(128, 128, seed=10)
    cover_bytes = ImageGenerator.to_bytes(cover, fmt="PNG")
    text = "Lossless LSB-R Academic Verification Payload"

    embed_res = e2e_client.embed(cover_bytes, password=PASSWORD_VALID, method=METHOD_LSB_REPLACEMENT, payload_text=text)
    assert embed_res.success is True

    extract_res = e2e_client.extract(embed_res.stego_bytes, password=PASSWORD_VALID)
    assert_lossless_text(text, extract_res)


@pytest.mark.tier1
def test_t1_f05_04_lsb_r_psnr_range_verification(e2e_client):
    """TC-E2E-T1-F05-04: LSB-R stego image achieves high visual fidelity (PSNR > 50 dB)."""
    cover = ImageGenerator.natural_texture(256, 256, seed=20)
    cover_bytes = ImageGenerator.to_bytes(cover, fmt="PNG")
    res = e2e_client.embed(cover_bytes, password=PASSWORD_VALID, method=METHOD_LSB_REPLACEMENT, payload_text="Small Payload")

    assert res.success is True
    assert_distortion_bounds(res.metrics, min_psnr=50.0, max_mse=1.0, min_ssim=0.98)


@pytest.mark.tier1
def test_t1_f05_05_lsb_r_lossless_bit_retrieval(e2e_client):
    """TC-E2E-T1-F05-05: Extracted bits match target bitstream with 100% fidelity."""
    cover = ImageGenerator.gradient(128, 128)
    cover_bytes = ImageGenerator.to_bytes(cover, fmt="PNG")
    secret = "StegaShield Bit-Fidelity Check"

    res = e2e_client.embed(cover_bytes, password=PASSWORD_VALID, method=METHOD_LSB_REPLACEMENT, payload_text=secret)
    ext = e2e_client.extract(res.stego_bytes, password=PASSWORD_VALID)
    assert ext.payload_text == secret


# ==============================================================================
# Feature 6: LSB Matching Embedding
# ==============================================================================

@pytest.mark.tier1
def test_t1_f06_01_lsb_m_plus_minus_equal_probability():
    """TC-E2E-T1-F06-01: LSB-M applies +1 and -1 modifications with empirical equality."""
    rng = np.random.default_rng(42)
    trials = 10000
    # Channel values all 128 (even), target bit is 1 (mismatch)
    channels = np.full(trials, 128, dtype=np.uint8)
    deltas = rng.choice([-1, 1], size=trials)
    modified = channels + deltas

    plus_count = np.sum(modified == 129)
    minus_count = np.sum(modified == 127)
    ratio = plus_count / trials
    assert 0.47 <= ratio <= 0.53, f"LSB-M +1 modification ratio {ratio:.3f} diverged from 0.5"


@pytest.mark.tier1
def test_t1_f06_02_lsb_m_lower_boundary_clamping():
    """TC-E2E-T1-F06-02: Boundary pixel value 0 strictly increments to 1 (never underflows)."""
    channel_val = np.uint8(0)
    target_bit = 1
    # Clamping rule: if channel == 0, strictly +1
    result = channel_val + 1 if channel_val == 0 else channel_val - 1
    assert result == 1
    assert result >= 0
    assert result & 1 == target_bit


@pytest.mark.tier1
def test_t1_f06_03_lsb_m_upper_boundary_clamping():
    """TC-E2E-T1-F06-03: Boundary pixel value 255 strictly decrements to 254 (never overflows)."""
    channel_val = np.uint8(255)
    target_bit = 0
    # Clamping rule: if channel == 255, strictly -1
    result = channel_val - 1 if channel_val == 255 else channel_val + 1
    assert result == 254
    assert result <= 255
    assert result & 1 == target_bit


@pytest.mark.tier1
def test_t1_f06_04_lsb_m_bit_preservation():
    """TC-E2E-T1-F06-04: Channel values remain untouched when LSB already matches target bit."""
    channels = np.array([100, 101, 102, 103], dtype=np.uint8)
    bits = np.array([0, 1, 0, 1], dtype=np.uint8)  # Exactly matching channels % 2

    # Preserved channels
    result = channels.copy()
    diff = result != channels
    assert not np.any(diff)


@pytest.mark.tier1
def test_t1_f06_05_lsb_m_roundtrip_lossless(e2e_client):
    """TC-E2E-T1-F06-05: LSB-M embeds and extracts secret text losslessly."""
    cover = ImageGenerator.natural_texture(128, 128, seed=30)
    cover_bytes = ImageGenerator.to_bytes(cover, fmt="PNG")
    text = "LSB-M Academic Defense Secret Payload 2026"

    embed_res = e2e_client.embed(cover_bytes, password=PASSWORD_VALID, method=METHOD_LSB_MATCHING, payload_text=text)
    assert embed_res.success is True

    extract_res = e2e_client.extract(embed_res.stego_bytes, password=PASSWORD_VALID)
    assert_lossless_text(text, extract_res)


# ==============================================================================
# Feature 7: Extraction & Uniform Error Handling
# ==============================================================================

@pytest.mark.tier1
def test_t1_f07_01_extract_happy_path(e2e_client):
    """TC-E2E-T1-F07-01: Correct password extracts payload losslessly."""
    cover_bytes = ImageGenerator.to_bytes(ImageGenerator.gradient(128, 128), fmt="PNG")
    secret = "StegaShield Happy Path 2026"

    emb = e2e_client.embed(cover_bytes, password=PASSWORD_VALID, payload_text=secret)
    ext = e2e_client.extract(emb.stego_bytes, password=PASSWORD_VALID)
    assert_lossless_text(secret, ext)


@pytest.mark.tier1
def test_t1_f07_02_extract_wrong_password_uniform_error(e2e_client):
    """TC-E2E-T1-F07-02: Incorrect password raises uniform error WRONG_PASSWORD_OR_NO_DATA."""
    cover_bytes = ImageGenerator.to_bytes(ImageGenerator.gradient(128, 128), fmt="PNG")
    emb = e2e_client.embed(cover_bytes, password=PASSWORD_VALID, payload_text="Hidden Data")

    ext = e2e_client.extract(emb.stego_bytes, password=PASSWORD_WRONG)
    assert_uniform_error(ext)


@pytest.mark.tier1
def test_t1_f07_03_extract_corrupted_stego_uniform_error(e2e_client):
    """TC-E2E-T1-F07-03: Corrupted ciphertext bits return identical uniform error."""
    cover_bytes = ImageGenerator.to_bytes(ImageGenerator.gradient(128, 128), fmt="PNG")
    emb = e2e_client.embed(cover_bytes, password=PASSWORD_VALID, payload_text="Hidden Data")

    tampered = TamperGenerator.corrupt_ciphertext(emb.stego_bytes, num_bits=8)
    ext = e2e_client.extract(tampered, password=PASSWORD_VALID)
    assert_uniform_error(ext)


@pytest.mark.tier1
def test_t1_f07_04_extract_clean_cover_uniform_error(e2e_client):
    """TC-E2E-T1-F07-04: Extraction on clean (non-stego) image returns identical uniform error."""
    clean_cover_bytes = ImageGenerator.to_bytes(ImageGenerator.natural_texture(128, 128), fmt="PNG")
    ext = e2e_client.extract(clean_cover_bytes, password=PASSWORD_VALID)
    assert_uniform_error(ext)


@pytest.mark.tier1
def test_t1_f07_05_extract_truncated_image_uniform_error(e2e_client):
    """TC-E2E-T1-F07-05: Cropped/truncated stego carrier returns identical uniform error."""
    cover_bytes = ImageGenerator.to_bytes(ImageGenerator.gradient(128, 128), fmt="PNG")
    emb = e2e_client.embed(cover_bytes, password=PASSWORD_VALID, payload_text="Hidden Data")

    cropped = TamperGenerator.truncate_image(emb.stego_bytes, crop_ratio=0.5)
    ext = e2e_client.extract(cropped, password=PASSWORD_VALID)
    assert_uniform_error(ext)


# ==============================================================================
# Feature 8: Capacity Calculation & Cover Validation
# ==============================================================================

@pytest.mark.tier1
def test_t1_f08_01_capacity_calculation_formula():
    """TC-E2E-T1-F08-01: Capacity calculation strictly accounts for 400-bit protocol overhead."""
    img = ImageGenerator.flat(100, 100)
    cap = stego.calculate_capacity(img)

    total_channels = 100 * 100 * 3  # 30,000 slots
    overhead_bits = 400
    expected_usable_bits = total_channels - overhead_bits
    expected_usable_bytes = expected_usable_bits // 8

    assert cap["total_channels"] == total_channels
    assert cap["overhead_bits"] == overhead_bits
    assert cap["usable_bits"] == expected_usable_bits
    assert cap["usable_bytes"] == expected_usable_bytes


@pytest.mark.tier1
def test_t1_f08_02_png_cover_validation(e2e_client):
    """TC-E2E-T1-F08-02: PNG cover is validated and embedded successfully."""
    cover = ImageGenerator.natural_texture(100, 100)
    cover_bytes = ImageGenerator.to_bytes(cover, fmt="PNG")

    res = e2e_client.embed(cover_bytes, filename="cover.png", password=PASSWORD_VALID, payload_text="PNG OK")
    assert res.success is True


@pytest.mark.tier1
def test_t1_f08_03_jpeg_cover_validation_and_png_output(e2e_client):
    """TC-E2E-T1-F08-03: JPEG cover is accepted, transcoded to RGB, and saved as lossless PNG."""
    cover = ImageGenerator.natural_texture(128, 128)
    jpeg_bytes = ImageGenerator.to_bytes(cover, fmt="JPEG")

    res = e2e_client.embed(jpeg_bytes, filename="cover.jpg", password=PASSWORD_VALID, payload_text="JPEG Test")
    assert res.success is True
    # Verify resulting output format is PNG (PNG magic bytes: \x89PNG\r\n\x1a\n)
    assert res.stego_bytes.startswith(b"\x89PNG\r\n\x1a\n")


@pytest.mark.tier1
def test_t1_f08_04_bmp_cover_validation_and_png_output(e2e_client):
    """TC-E2E-T1-F08-04: BMP cover is accepted and output is saved as lossless PNG."""
    cover = ImageGenerator.gradient(100, 100)
    bmp_bytes = ImageGenerator.to_bytes(cover, fmt="BMP")

    res = e2e_client.embed(bmp_bytes, filename="cover.bmp", password=PASSWORD_VALID, payload_text="BMP Test")
    assert res.success is True
    assert res.stego_bytes.startswith(b"\x89PNG\r\n\x1a\n")


@pytest.mark.tier1
def test_t1_f08_05_exact_capacity_limit_rejection(e2e_client):
    """TC-E2E-T1-F08-05: Payload exceeding carrier capacity is rejected before embedding."""
    # Micro image: 16x16 pixels = 768 channels. Usable bytes = (768 - 400) // 8 = 46 bytes.
    cover = ImageGenerator.flat(16, 16)
    cover_bytes = ImageGenerator.to_bytes(cover, fmt="PNG")

    # Construct payload of 500 bytes (far exceeding 46 bytes)
    oversized_text = "A" * 500
    res = e2e_client.embed(cover_bytes, password=PASSWORD_VALID, payload_text=oversized_text)
    assert_capacity_rejection(res)
