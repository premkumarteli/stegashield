"""Unit Tests for StegaShield Steganalysis Detectors (Chi-Square and RS Analysis).

Tests statistical detection performance, edge cases, channel slicing, and verdict classification.
"""

from __future__ import annotations

import numpy as np
import pytest
from PIL import Image

from app.core.detect import (
    VERDICT_CLEAN,
    VERDICT_LIKELY_STEGO,
    VERDICT_SUSPICIOUS,
    chi_square_attack,
    classify_verdict,
    rs_analysis,
)
from app.core.stego import METHOD_LSB_MATCHING, METHOD_LSB_REPLACEMENT, embed


@pytest.fixture
def gradient_image() -> Image.Image:
    """Generates a synthetic textured RGB image with natural non-equalized pixel pairs."""
    width, height = 120, 120
    y, x = np.mgrid[0:height, 0:width]
    r = ((x * 2 + y) % 200 + 20).astype(np.uint8)
    g = ((x * 3 + y) % 200 + 20).astype(np.uint8)
    b = ((x * 2 + y * 2) % 200 + 20).astype(np.uint8)
    arr = np.stack([r, g, b], axis=-1)
    return Image.fromarray(arr, mode="RGB")


@pytest.fixture
def full_stego_replacement(gradient_image: Image.Image, monkeypatch: pytest.MonkeyPatch) -> Image.Image:
    """Creates a high-payload (96%) LSB-replacement stego image to trigger chi-square detection."""
    monkeypatch.setattr("os.urandom", lambda n: b"0123456789abcdef"[:n])
    # Capacity = 120*120*3 = 43200 bits = 5400 bytes. Overhead = 50 bytes.
    payload_data = b"X" * 5200
    stego_img, _ = embed(
        gradient_image,
        payload=payload_data,
        password="TestDetectorPassword123!",
        method=METHOD_LSB_REPLACEMENT,
    )
    return stego_img


@pytest.fixture
def full_stego_matching(gradient_image: Image.Image, monkeypatch: pytest.MonkeyPatch) -> Image.Image:
    """Creates a high-payload (96%) LSB-matching stego image to test detector evasion."""
    monkeypatch.setattr("os.urandom", lambda n: b"0123456789abcdef"[:n])
    payload_data = b"X" * 5200
    stego_img, _ = embed(
        gradient_image,
        payload=payload_data,
        password="TestDetectorPassword123!",
        method=METHOD_LSB_MATCHING,
    )
    return stego_img


# --- Chi-Square Attack Tests ---

def test_chi_square_clean_image(gradient_image: Image.Image) -> None:
    """Clean image with natural variation should have low p-value (not equalized)."""
    result = chi_square_attack(gradient_image)
    assert "chi2" in result
    assert "p_value" in result
    assert "df" in result
    assert "valid_pairs" in result
    assert "score" in result
    assert result["valid_pairs"] > 10
    # Clean image pairs of values are naturally unequal, so p-value should be close to 0.0
    assert result["score"] < 0.1


def test_chi_square_full_replacement_stego(full_stego_replacement: Image.Image) -> None:
    """High-payload LSB replacement equalizes pairs of values, resulting in elevated p-value."""
    result = chi_square_attack(full_stego_replacement)
    assert result["score"] > 0.05
    assert result["classification"] in (VERDICT_SUSPICIOUS, VERDICT_LIKELY_STEGO)


def test_chi_square_100_percent_replacement(gradient_image: Image.Image) -> None:
    """100% simulated LSB replacement equalizes PoVs and produces p-value > 0.50 (likely_stego)."""
    arr = np.asarray(gradient_image)
    rng = np.random.default_rng(42)
    stego_100 = Image.fromarray((arr & 0xFE) | rng.integers(0, 2, arr.shape, dtype=np.uint8), mode="RGB")
    result = chi_square_attack(stego_100)
    assert result["score"] > 0.50
    assert result["classification"] == VERDICT_LIKELY_STEGO


def test_chi_square_matching_evasion(full_stego_matching: Image.Image) -> None:
    """LSB matching does not equalize pairs of values, evading Chi-Square detection."""
    result = chi_square_attack(full_stego_matching)
    # LSB matching avoids the pairs-of-values equalization trap
    assert result["score"] < 0.2


def test_chi_square_per_channel(gradient_image: Image.Image) -> None:
    """Test channel filtering for Chi-Square."""
    res_r = chi_square_attack(gradient_image, channel="r")
    res_g = chi_square_attack(gradient_image, channel="g")
    res_b = chi_square_attack(gradient_image, channel="b")
    assert res_r["valid_pairs"] > 0
    assert res_g["valid_pairs"] > 0
    assert res_b["valid_pairs"] > 0


def test_chi_square_invalid_channel(gradient_image: Image.Image) -> None:
    """Passing an invalid channel name raises ValueError."""
    with pytest.raises(ValueError, match="Invalid channel"):
        chi_square_attack(gradient_image, channel="invalid_ch")


def test_chi_square_flat_image() -> None:
    """A completely flat single-color image has at most 1 populated pair, testing the Cochran guard."""
    flat_arr = np.full((50, 50, 3), 128, dtype=np.uint8)
    flat_img = Image.fromarray(flat_arr, mode="RGB")
    result = chi_square_attack(flat_img)
    assert result["valid_pairs"] <= 1
    assert result["score"] == 0.0
    assert result["df"] == 0


def test_chi_square_grayscale_converted(gradient_image: Image.Image) -> None:
    """Grayscale images converted to RGB should process without error."""
    gray = gradient_image.convert("L")
    result = chi_square_attack(gray)
    assert "score" in result


# --- RS Analysis Tests ---

def test_rs_analysis_clean_image(gradient_image: Image.Image) -> None:
    """Clean image should produce a low estimated payload ratio."""
    result = rs_analysis(gradient_image)
    assert "estimated_payload_ratio" in result
    assert "score" in result
    assert "channel_scores" in result
    assert 0.0 <= result["score"] <= 1.0
    # Clean image should have low estimated payload
    assert result["score"] < 0.25


def test_rs_analysis_full_replacement(full_stego_replacement: Image.Image) -> None:
    """RS analysis detects LSB replacement with a high estimated payload ratio."""
    result = rs_analysis(full_stego_replacement)
    assert 0.0 <= result["score"] <= 1.0
    # On high LSB replacement, RS detects significant embedding
    assert result["score"] > 0.40


def test_rs_analysis_100_percent_replacement_sinusoid() -> None:
    """Verifies that 100% LSB replacement produces estimated_payload_ratio > 0.85

    across a multi-frequency sinusoidal texture without channels collapsing to 0.0.
    """
    y, x = np.mgrid[0:256, 0:256]
    r = (128 + 50 * np.sin(x / 15.0) * np.cos(y / 20.0)).astype(np.uint8)
    g = (128 + 40 * np.cos(x / 25.0) * np.sin(y / 18.0)).astype(np.uint8)
    b = (128 + 45 * np.sin((x + y) / 30.0)).astype(np.uint8)
    img = Image.fromarray(np.stack([r, g, b], axis=-1), mode="RGB")
    arr = np.asarray(img)
    rng = np.random.default_rng(2026)
    stego_arr = (arr & 0xFE) | rng.integers(0, 2, arr.shape, dtype=np.uint8)
    stego_img = Image.fromarray(stego_arr, mode="RGB")
    res = rs_analysis(stego_img)

    assert res["estimated_payload_ratio"] > 0.85
    assert res["classification"] == VERDICT_LIKELY_STEGO
    for ch, ratio in res["channel_ratios"].items():
        assert ratio > 0.80, f"Channel {ch} ratio {ratio} falsely collapsed"


def test_rs_analysis_100_percent_replacement_gradient(gradient_image: Image.Image) -> None:
    """Verifies that 100% LSB replacement on gradient texture produces ratio > 0.85

    and individual channel ratios do not falsely report clean.
    """
    arr = np.asarray(gradient_image)
    rng = np.random.default_rng(42)
    stego_arr = (arr & 0xFE) | rng.integers(0, 2, arr.shape, dtype=np.uint8)
    stego_img = Image.fromarray(stego_arr, mode="RGB")
    res = rs_analysis(stego_img)

    assert res["estimated_payload_ratio"] > 0.85
    assert res["classification"] == VERDICT_LIKELY_STEGO
    for ch, ratio in res["channel_ratios"].items():
        assert ratio > 0.80, f"Channel {ch} ratio {ratio} falsely collapsed"


def test_rs_analysis_channels(gradient_image: Image.Image) -> None:
    """RS analysis on specific single channels."""
    res_r = rs_analysis(gradient_image, channel="r")
    assert "r" in res_r["channel_scores"]
    assert 0.0 <= res_r["score"] <= 1.0


def test_rs_analysis_tiny_image() -> None:
    """Images with fewer than 16 groups (<64 pixels) return 0.0 safely."""
    tiny_arr = np.zeros((4, 4, 3), dtype=np.uint8)
    tiny_img = Image.fromarray(tiny_arr, mode="RGB")
    result = rs_analysis(tiny_img)
    assert result["score"] == 0.0


def test_rs_analysis_flat_image() -> None:
    """Completely flat image triggers the linear degeneracy / zero-gradient guard."""
    flat_arr = np.full((32, 32, 3), 100, dtype=np.uint8)
    flat_img = Image.fromarray(flat_arr, mode="RGB")
    result = rs_analysis(flat_img)
    assert result["score"] == 0.0


# --- Verdict Classification Tests ---

def test_classify_verdict() -> None:
    """Verifies mapping of numerical scores to calibrated verdicts."""
    t_suspicious = 0.15
    t_likely = 0.50

    assert classify_verdict(0.05, t_suspicious, t_likely) == VERDICT_CLEAN
    assert classify_verdict(0.15, t_suspicious, t_likely) == VERDICT_CLEAN
    assert classify_verdict(0.16, t_suspicious, t_likely) == VERDICT_SUSPICIOUS
    assert classify_verdict(0.50, t_suspicious, t_likely) == VERDICT_SUSPICIOUS
    assert classify_verdict(0.51, t_suspicious, t_likely) == VERDICT_LIKELY_STEGO
    assert classify_verdict(0.99, t_suspicious, t_likely) == VERDICT_LIKELY_STEGO


def test_embed_and_formats_canonical_exports() -> None:
    """Verifies that canonical aliases in embed.py and formats.py re-export correctly."""
    from app.core.embed import (
        HEADER_OVERHEAD_BITS,
        METHOD_LSB_MATCHING,
        METHOD_LSB_REPLACEMENT,
        calculate_capacity,
        embed as embed_alias,
        extract as extract_alias,
    )
    from app.core.formats import (
        CONTAINER_MAGIC,
        KEY_SIZE_BYTES,
        NONCE_SIZE_BYTES,
        SALT_SIZE_BYTES,
        TAG_SIZE_BYTES,
    )

    assert CONTAINER_MAGIC == b"STGS"
    assert SALT_SIZE_BYTES == 16
    assert NONCE_SIZE_BYTES == 12
    assert TAG_SIZE_BYTES == 16
    assert KEY_SIZE_BYTES == 32
    assert HEADER_OVERHEAD_BITS == 400
    assert METHOD_LSB_REPLACEMENT == "lsb_replacement"
    assert METHOD_LSB_MATCHING == "lsb_matching"
    assert callable(embed_alias)
    assert callable(extract_alias)
    assert callable(calculate_capacity)



# --- Extended Classifier & Edge Case Tests ---

def test_classify_multi_detector_aggregation() -> None:
    """Verifies classify() aggregates Chi-square and RS scores correctly."""
    from app.core.detect import classify

    # Both clean
    c_clean = {"p_value": 0.01}
    r_clean = {"estimated_payload_ratio": 0.02}
    assert classify(c_clean, r_clean) == VERDICT_CLEAN

    # Chi suspicious, RS clean -> suspicious
    c_susp = {"p_value": 0.10}
    assert classify(c_susp, r_clean) == VERDICT_SUSPICIOUS

    # RS suspicious, Chi clean -> suspicious
    r_susp = {"estimated_payload_ratio": 0.22}
    assert classify(c_clean, r_susp) == VERDICT_SUSPICIOUS

    # Either likely_stego -> likely_stego
    c_stego = {"p_value": 0.85}
    r_stego = {"estimated_payload_ratio": 0.60}
    assert classify(c_stego, r_clean) == VERDICT_LIKELY_STEGO
    assert classify(c_clean, r_stego) == VERDICT_LIKELY_STEGO
    assert classify(c_stego, r_stego) == VERDICT_LIKELY_STEGO

    # Custom thresholds
    custom_thresh = {
        "chi_square": {"suspicious_threshold": 0.20, "likely_stego_threshold": 0.70},
        "rs_analysis": {"suspicious_threshold": 0.30, "likely_stego_threshold": 0.80},
    }
    assert classify({"p_value": 0.15}, {"estimated_payload_ratio": 0.15}, custom_thresh) == VERDICT_CLEAN
    assert classify({"p_value": 0.25}, {"estimated_payload_ratio": 0.15}, custom_thresh) == VERDICT_SUSPICIOUS
    assert classify({"p_value": 0.75}, {"estimated_payload_ratio": 0.15}, custom_thresh) == VERDICT_LIKELY_STEGO


def test_detectors_alias_module() -> None:
    """Verifies detectors.py backward-compatibility alias re-exports correctly."""
    import app.core.detectors as detectors

    assert callable(detectors.chi_square_attack)
    assert callable(detectors.rs_analysis)
    assert callable(detectors.classify)
    assert callable(detectors.classify_verdict)
    assert detectors.VERDICT_CLEAN == "clean"
    assert detectors.VERDICT_SUSPICIOUS == "suspicious"
    assert detectors.VERDICT_LIKELY_STEGO == "likely_stego"
    assert "chi_square" in detectors.DEFAULT_THRESHOLDS


def test_rs_analysis_odd_dimensions_and_rgba(gradient_image: Image.Image) -> None:
    """Tests RS analysis on odd dimensions (65x65) and RGBA images."""
    # Odd dimension 65x65 has 4225 pixels (not divisible by 4, leaves 1 trailing pixel)
    odd_arr = np.zeros((65, 65, 3), dtype=np.uint8)
    for y in range(65):
        for x in range(65):
            odd_arr[y, x] = [x * 3, y * 3, (x + y)]
    odd_img = Image.fromarray(odd_arr, mode="RGB")
    res_odd = rs_analysis(odd_img)
    assert "estimated_payload_ratio" in res_odd
    assert "regular_m" in res_odd
    assert "singular_m" in res_odd
    assert "regular_neg_m" in res_odd
    assert "singular_neg_m" in res_odd
    assert "channel_ratios" in res_odd

    # RGBA image converts and evaluates RGB channels
    rgba_img = gradient_image.convert("RGBA")
    res_rgba = rs_analysis(rgba_img)
    assert res_rgba["classification"] in (VERDICT_CLEAN, VERDICT_SUSPICIOUS, VERDICT_LIKELY_STEGO)


def test_rs_analysis_negative_discriminant_and_linear_branches() -> None:
    """Exercises edge branches in _rs_channel_vectorized directly."""
    from app.core.detect import _rs_channel_vectorized

    # Array of length 100 with alternating pattern to exercise quadratic roots
    pattern = np.array([10, 20, 30, 40] * 25, dtype=np.uint8)
    p, rm, sm, rnm, snm = _rs_channel_vectorized(pattern)
    assert 0.0 <= p <= 1.0

    # Short array < 64 pixels (< 16 groups)
    p_short, _, _, _, _ = _rs_channel_vectorized(np.zeros(32, dtype=np.uint8))
    assert p_short == 0.0


def test_classify_loads_default_config_file() -> None:
    """Verifies classify() loads thresholds from config/thresholds.json when thresholds=None."""
    from app.core.detect import classify

    c = {"p_value": 0.01}
    r = {"estimated_payload_ratio": 0.01}
    # Passing thresholds=None triggers reading config/thresholds.json
    verdict = classify(c, r, thresholds=None)
    assert verdict == VERDICT_CLEAN


def test_classify_config_file_fallback_branches(tmp_path: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verifies classify() falls back to DEFAULT_THRESHOLDS when config file is missing or corrupt."""
    from pathlib import Path
    from app.core.detect import DEFAULT_THRESHOLDS, classify

    # Nonexistent path fallback
    monkeypatch.setattr("pathlib.Path.is_file", lambda self: False)
    verdict = classify({"p_value": 0.01}, {"estimated_payload_ratio": 0.01}, thresholds=None)
    assert verdict == VERDICT_CLEAN

    # Point to corrupt file
    corrupt_file = Path(str(tmp_path)) / "corrupt_thresholds.json"
    corrupt_file.write_text("NOT_VALID_JSON", encoding="utf-8")
    monkeypatch.setattr("pathlib.Path.is_file", lambda self: True)
    monkeypatch.setattr("builtins.open", lambda *args, **kwargs: (_ for _ in ()).throw(ValueError("Corrupt JSON")))
    verdict_corrupt = classify({"p_value": 0.01}, {"estimated_payload_ratio": 0.01}, thresholds=None)
    assert verdict_corrupt == VERDICT_CLEAN
    assert "chi_square" in DEFAULT_THRESHOLDS


def test_rs_channel_vectorized_edge_branches(monkeypatch: pytest.MonkeyPatch) -> None:
    """Explicitly tests fallback branches in _rs_channel_vectorized:

    - Degenerate linear regime (|a| < 1e-4) with |b| <= 1e-8
    - Negative discriminant (disc < 0) with |b| <= 1e-8
    - Root selection (abs(x1) > abs(x2))
    - Singularity guard (|x - 0.5| < 1e-6)
    - NaN/Inf score protection
    """
    from app.core.detect import _rs_channel_vectorized

    # Short array < 64 pixels (< 16 groups)
    p_short, _, _, _, _ = _rs_channel_vectorized(np.zeros(20, dtype=np.uint8))
    assert p_short == 0.0

    # Flat array (0 variation)
    p_flat, _, _, _, _ = _rs_channel_vectorized(np.full(100, 100, dtype=np.uint8))
    assert p_flat == 0.0

    # Natural texture
    y, x = np.mgrid[0:128, 0:128]
    tex = (128 + 50 * np.sin(x / 15.0) * np.cos(y / 20.0)).astype(np.uint8).flatten()
    p_clean, _, _, _, _ = _rs_channel_vectorized(tex)
    assert 0.0 <= p_clean <= 0.10

    # 100% LSB randomized texture
    rng = np.random.default_rng(999)
    tex_stego = (tex & 0xFE) | rng.integers(0, 2, tex.shape, dtype=np.uint8)
    p_stego, _, _, _, _ = _rs_channel_vectorized(tex_stego)
    assert p_stego > 0.85

    dummy = np.zeros(64, dtype=np.uint8)

    # 1. disc < 0 and b == 0 (exercises line 231: x = 0.0)
    with monkeypatch.context() as m:
        mean_gen1 = iter([0.5, 0.0, 0.0, 0.0, 0.5, 0.0, 0.0, 2.0])
        m.setattr("numpy.mean", lambda arr: next(mean_gen1))
        p_disc_neg, _, _, _, _ = _rs_channel_vectorized(dummy)
        assert p_disc_neg == 0.0

    # 2. Pick root x2 where abs(x1) > abs(x2) (exercises line 240: x = x2)
    with monkeypatch.context() as m:
        mean_gen2 = iter([0.5, 0.0, 2.5, 0.0, 0.0, 0.0, 4.0, 0.0])
        m.setattr("numpy.mean", lambda arr: next(mean_gen2))
        p_x2, _, _, _, _ = _rs_channel_vectorized(dummy)
        assert 0.0 <= p_x2 <= 1.0

    # 3. Singularity guard |x - 0.5| < 1e-6 (exercises line 244: p = 0.0)
    with monkeypatch.context() as m:
        mean_gen3 = iter([0.0, 0.0, 0.0, 0.25, 0.5, 0.0, 0.25, 0.0])
        m.setattr("numpy.mean", lambda arr: next(mean_gen3))
        p_sing, _, _, _, _ = _rs_channel_vectorized(dummy)
        assert p_sing == 0.0

    # 4. NaN / Inf guard (exercises line 249: p = 0.0)
    with monkeypatch.context() as m:
        m.setattr("app.core.detect.math.isnan", lambda val: True)
        p_nan, _, _, _, _ = _rs_channel_vectorized(dummy)
        assert p_nan == 0.0


def test_chi_square_nan_guard(gradient_image: Image.Image, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verifies Chi-Square NaN/Inf guard resets p_value to 0.0."""
    monkeypatch.setattr("app.core.detect.math.isnan", lambda val: True)
    res = chi_square_attack(gradient_image)
    assert res["score"] == 0.0


def test_chi_square_suspicious_verdict(gradient_image: Image.Image, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verifies Chi-Square classifies as suspicious when 0.05 <= p_value < 0.50."""
    monkeypatch.setattr("scipy.stats.chi2.sf", lambda stat, df: 0.20)
    res = chi_square_attack(gradient_image)
    assert res["classification"] == VERDICT_SUSPICIOUS
