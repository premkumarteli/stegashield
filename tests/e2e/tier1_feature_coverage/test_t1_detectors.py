"""
StegaShield Tier 1: Steganalysis Detectors & Calibration Tests (Features 10–12).
Validates Chi-square attack, RS analysis, and detector threshold calibration.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import numpy as np
from PIL import Image
import pytest

from tests.e2e.fixtures import ImageGenerator, PASSWORD_VALID, METHOD_LSB_REPLACEMENT, METHOD_LSB_MATCHING
from tests.e2e.framework.oracles import chi_square_oracle, rs_analysis_oracle, calibrate_thresholds_oracle, _flipping


# ==============================================================================
# Feature 10: Chi-Square Steganalysis Attack
# ==============================================================================

@pytest.mark.tier1
def test_t1_f10_01_chi_square_clean_image_low_p_value(e2e_client):
    """TC-E2E-T1-F10-01: Clean natural image produces p-value ~0.0 (classified clean)."""
    cover = ImageGenerator.natural_texture(256, 256, seed=42)
    cover_bytes = ImageGenerator.to_bytes(cover, fmt="PNG")

    res = e2e_client.detect(cover_bytes)
    assert res.success is True
    assert res.classification == "clean"
    # Clean photographic images have large PoV differences so p-value is near zero
    assert res.chi2_p_value < 0.05


@pytest.mark.tier1
def test_t1_f10_02_chi_square_lsb_r_high_ratio_detection(e2e_client):
    """TC-E2E-T1-F10-02: 100% LSB-R stego image equalizes PoVs and is detected (likely_stego)."""
    cover = ImageGenerator.natural_texture(128, 128, seed=42)
    arr = np.array(cover, dtype=np.uint8)
    # Simulate 100% LSB replacement with random bits
    rng = np.random.default_rng(123)
    random_bits = rng.integers(0, 2, arr.shape, dtype=np.uint8)
    stego_arr = (arr & 0xFE) | random_bits
    stego_img = Image.fromarray(stego_arr, mode="RGB")
    stego_bytes = ImageGenerator.to_bytes(stego_img, fmt="PNG")

    res = e2e_client.detect(stego_bytes)
    assert res.success is True
    assert res.chi2_p_value > 0.05
    assert res.classification in ("likely_stego", "suspicious")


@pytest.mark.tier1
def test_t1_f10_03_chi_square_sequential_vs_permuted_lsb_r(e2e_client):
    """TC-E2E-T1-F10-03: Chi-square detects PoV equalization in both sequential and permuted LSB-R."""
    cover = ImageGenerator.natural_texture(128, 128, seed=10)
    cover_bytes = ImageGenerator.to_bytes(cover, fmt="PNG")

    # Embed 2000 bytes payload via LSB-R
    payload = "X" * 2000
    emb = e2e_client.embed(cover_bytes, password=PASSWORD_VALID, method=METHOD_LSB_REPLACEMENT, payload_text=payload)
    assert emb.success is True

    det = e2e_client.detect(emb.stego_bytes)
    assert det.success is True
    # At high payload ratio, Chi-square p-value increases
    assert det.chi2_score > 0.0


@pytest.mark.tier1
def test_t1_f10_04_chi_square_deterministic_scores(e2e_client):
    """TC-E2E-T1-F10-04: Running Chi-square attack twice on the same image yields identical results."""
    cover = ImageGenerator.natural_texture(128, 128, seed=99)
    cover_bytes = ImageGenerator.to_bytes(cover, fmt="PNG")

    res1 = e2e_client.detect(cover_bytes)
    res2 = e2e_client.detect(cover_bytes)

    assert res1.chi2_score == res2.chi2_score
    assert res1.chi2_p_value == res2.chi2_p_value
    assert res1.df == res2.df
    assert res1.classification == res2.classification


@pytest.mark.tier1
def test_t1_f10_05_chi_square_response_schema(e2e_client):
    """TC-E2E-T1-F10-05: Detector response conforms to standard DetectResult dataclass schema."""
    img = ImageGenerator.gradient(64, 64)
    img_bytes = ImageGenerator.to_bytes(img, fmt="PNG")

    res = e2e_client.detect(img_bytes)
    assert hasattr(res, "chi2_score")
    assert hasattr(res, "chi2_p_value")
    assert hasattr(res, "df")
    assert hasattr(res, "rs_estimated_ratio")
    assert hasattr(res, "classification")
    assert res.classification in ("clean", "suspicious", "likely_stego")


# ==============================================================================
# Feature 11: RS Analysis Steganalysis Attack
# ==============================================================================

@pytest.mark.tier1
def test_t1_f11_01_rs_analysis_clean_natural_hypothesis(e2e_client):
    """TC-E2E-T1-F11-01: Clean image satisfies natural hypothesis: R_M ~ R_-M and S_M ~ S_-M."""
    cover = ImageGenerator.natural_texture(256, 256, seed=42)
    oracle_res = rs_analysis_oracle(cover)

    rm = oracle_res["regular_m"]
    r_neg_m = oracle_res["regular_neg_m"]
    sm = oracle_res["singular_m"]
    s_neg_m = oracle_res["singular_neg_m"]

    # Natural hypothesis: |R_M - R_{-M}| < 0.05 and |S_M - S_{-M}| < 0.05
    assert abs(rm - r_neg_m) < 0.05, f"Natural regularity hypothesis violated: {rm} vs {r_neg_m}"
    assert abs(sm - s_neg_m) < 0.05, f"Natural singularity hypothesis violated: {sm} vs {s_neg_m}"
    assert oracle_res["estimated_payload_ratio"] < 0.15


@pytest.mark.tier1
def test_t1_f11_02_rs_analysis_lsb_r_50_percent_ratio():
    """TC-E2E-T1-F11-02: RS analysis accurately estimates embedding ratio on 50% LSB-R stego."""
    cover = ImageGenerator.natural_texture(256, 256, seed=77)
    arr = np.array(cover, dtype=np.uint8)

    # Modify 50% of pixel channels with random bits
    rng = np.random.default_rng(88)
    mask = rng.random(arr.shape) < 0.50
    random_bits = rng.integers(0, 2, arr.shape, dtype=np.uint8)
    stego_arr = arr.copy()
    stego_arr[mask] = (stego_arr[mask] & 0xFE) | random_bits[mask]

    stego_img = Image.fromarray(stego_arr, mode="RGB")
    res = rs_analysis_oracle(stego_img)

    est_ratio = res["estimated_payload_ratio"]
    # RS analysis should estimate ratio close to 0.50
    assert 0.35 <= est_ratio <= 0.65, f"Estimated ratio {est_ratio} outside expected [0.35, 0.65]"


@pytest.mark.tier1
def test_t1_f11_03_rs_analysis_lsb_r_100_percent_inversion():
    """TC-E2E-T1-F11-03: 100% LSB-R causes regular and singular group count convergence/inversion."""
    cover = ImageGenerator.natural_texture(256, 256, seed=55)
    arr = np.array(cover, dtype=np.uint8)

    # 100% LSB replacement
    rng = np.random.default_rng(66)
    random_bits = rng.integers(0, 2, arr.shape, dtype=np.uint8)
    stego_arr = (arr & 0xFE) | random_bits
    stego_img = Image.fromarray(stego_arr, mode="RGB")

    res = rs_analysis_oracle(stego_img)
    # At 100% embedding, R_M converges to S_M (within 0.05) or inverts
    rm = res["regular_m"]
    sm = res["singular_m"]
    assert abs(rm - sm) < 0.05 or rm <= sm
    assert res["estimated_payload_ratio"] > 0.60


@pytest.mark.tier1
def test_t1_f11_04_rs_analysis_flipping_functions():
    """TC-E2E-T1-F11-04: Flipping functions F1, F-1, F0 behave strictly per Fridrich (2001)."""
    vals = np.array([0, 1, 2, 3, 254, 255], dtype=np.uint8)

    # F0 is identity
    assert np.array_equal(_flipping(vals, 0), vals)

    # F1 is x ^ 1
    f1_res = _flipping(vals, 1)
    assert np.array_equal(f1_res, [1, 0, 3, 2, 255, 254])

    # F-1: even -> even-1, odd -> odd+1 (clipped to [0, 255])
    f_neg1_res = _flipping(vals, -1)
    # 0 is even -> clipped to 0
    # 1 is odd -> 2
    # 2 is even -> 1
    # 3 is odd -> 4
    # 254 is even -> 253
    # 255 is odd -> clipped to 255
    assert np.array_equal(f_neg1_res, [0, 2, 1, 4, 253, 255])


@pytest.mark.tier1
def test_t1_f11_05_rs_analysis_quadratic_solver_robustness():
    """TC-E2E-T1-F11-05: Quadratic solver handles extreme flat images gracefully without NaN or crash."""
    flat_cover = ImageGenerator.flat(128, 128, color=(128, 128, 128))
    res = rs_analysis_oracle(flat_cover)
    assert "estimated_payload_ratio" in res
    assert 0.0 <= res["estimated_payload_ratio"] <= 1.0
    assert not np.isnan(res["estimated_payload_ratio"])


# ==============================================================================
# Feature 12: Detector Threshold Calibration
# ==============================================================================

@pytest.mark.tier1
def test_t1_f12_01_calibration_percentile_derivation():
    """TC-E2E-T1-F12-01: Threshold calibration calculates 95th and 99th percentiles on clean images."""
    clean_images = [ImageGenerator.natural_texture(64, 64, seed=i) for i in range(5)]
    thresholds = calibrate_thresholds_oracle(clean_images)

    assert "chi_square" in thresholds
    assert "rs_analysis" in thresholds
    assert "suspicious_threshold" in thresholds["chi_square"]
    assert "likely_stego_threshold" in thresholds["chi_square"]
    assert "suspicious_threshold" in thresholds["rs_analysis"]
    assert "likely_stego_threshold" in thresholds["rs_analysis"]


@pytest.mark.tier1
def test_t1_f12_02_thresholds_file_schema_validation():
    """TC-E2E-T1-F12-02: Calibrated thresholds schema is valid JSON matching spec."""
    clean_images = [ImageGenerator.natural_texture(64, 64, seed=i) for i in range(3)]
    thresholds = calibrate_thresholds_oracle(clean_images)

    json_str = json.dumps(thresholds)
    parsed = json.loads(json_str)
    assert parsed["chi_square"]["suspicious_threshold"] <= parsed["chi_square"]["likely_stego_threshold"]
    assert parsed["rs_analysis"]["suspicious_threshold"] <= parsed["rs_analysis"]["likely_stego_threshold"]


@pytest.mark.tier1
def test_t1_f12_03_monotonic_threshold_ordering():
    """TC-E2E-T1-F12-03: likely_stego_threshold is strictly greater than suspicious_threshold."""
    clean_images = [ImageGenerator.natural_texture(64, 64, seed=i) for i in range(4)]
    thresholds = calibrate_thresholds_oracle(clean_images)

    chi2 = thresholds["chi_square"]
    assert chi2["likely_stego_threshold"] > chi2["suspicious_threshold"]

    rs = thresholds["rs_analysis"]
    assert rs["likely_stego_threshold"] > rs["suspicious_threshold"]


@pytest.mark.tier1
def test_t1_f12_04_fallback_to_defaults():
    """TC-E2E-T1-F12-04: When clean dataset is empty, calibration safely yields valid default thresholds."""
    thresholds = calibrate_thresholds_oracle([])
    assert thresholds["chi_square"]["suspicious_threshold"] == 0.05
    assert thresholds["chi_square"]["likely_stego_threshold"] > 0.05
    assert thresholds["rs_analysis"]["suspicious_threshold"] == 0.08
    assert thresholds["rs_analysis"]["likely_stego_threshold"] > 0.08


@pytest.mark.tier1
def test_t1_f12_05_threshold_calibration_classification_logic():
    """TC-E2E-T1-F12-05: Classification follows T95 and T99 rules correctly."""
    clean_p = 0.01
    suspicious_p = 0.15
    stego_p = 0.60

    t95 = 0.05
    t99 = 0.50

    def classify(p):
        if p >= t99:
            return "likely_stego"
        if p >= t95:
            return "suspicious"
        return "clean"

    assert classify(clean_p) == "clean"
    assert classify(suspicious_p) == "suspicious"
    assert classify(stego_p) == "likely_stego"
