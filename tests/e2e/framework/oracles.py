"""
StegaShield E2E Authoritative Reference Oracles.
Implements the exact ground-truth mathematical models for Chi-square steganalysis
(Westfeld & Pfitzmann, 2000) and RS Analysis (Fridrich, Goljan, Du, 2001) as mined in Survey 3.
Used for progressive test validation and independent cross-oracle assertion verification.
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
from PIL import Image
from scipy import stats


def chi_square_oracle(image: Image.Image) -> Dict[str, Any]:
    """
    Computes Westfeld & Pfitzmann (2000) Chi-square attack.
    Returns: {"chi2": float, "p_value": float, "df": int, "classification": str}
    """
    arr = np.array(image.convert("RGB"), dtype=np.uint8)
    flat = arr.flatten()

    counts = np.bincount(flat, minlength=256)
    k = np.arange(128)
    even = counts[2 * k].astype(np.float64)
    odd = counts[2 * k + 1].astype(np.float64)

    expected = (even + odd) / 2.0
    valid = expected > 5.0

    valid_count = int(np.sum(valid))
    if valid_count <= 1:
        return {"chi2": 0.0, "p_value": 0.0, "df": 0, "classification": "clean"}

    df = valid_count - 1
    diff_sq = (even[valid] - odd[valid]) ** 2
    # chi2 statistic = sum( (even - odd)^2 / (2 * expected) )
    chi2_stat = float(np.sum(diff_sq / (2.0 * expected[valid])))

    p_value = float(stats.chi2.sf(chi2_stat, df))

    classification = "clean"
    if p_value > 0.50:
        classification = "likely_stego"
    elif p_value > 0.05:
        classification = "suspicious"

    return {
        "chi2": round(chi2_stat, 4),
        "p_value": p_value,
        "df": df,
        "classification": classification,
    }


def _flipping(val: np.ndarray, mode: int) -> np.ndarray:
    """Flipping function: 0: F0, 1: F1, -1: F-1."""
    if mode == 0:
        return val.copy()
    if mode == 1:
        return val ^ 1
    if mode == -1:
        # F-1: even -> even-1, odd -> odd+1 (clipped to 0..255)
        res = np.where(val % 2 == 0, val.astype(int) - 1, val.astype(int) + 1)
        return np.clip(res, 0, 255).astype(np.uint8)
    raise ValueError(f"Unknown mode: {mode}")


def _variation(g: np.ndarray) -> np.ndarray:
    """Computes variation across 4-pixel groups (axis 1): sum(|g[i+1] - g[i]|)."""
    return np.sum(np.abs(np.diff(g.astype(np.int32), axis=1)), axis=1)


def rs_analysis_oracle(image: Image.Image) -> Dict[str, Any]:
    """
    Computes Fridrich, Goljan, Du (2001) RS Analysis.
    Returns: {"estimated_payload_ratio": float, "regular_m": float, "singular_m": float, ...}
    """
    arr = np.array(image.convert("RGB"), dtype=np.uint8)
    flat = arr.flatten()

    num_pixels = len(flat)
    num_groups = num_pixels // 4
    if num_groups < 16:
        return {"estimated_payload_ratio": 0.0, "regular_m": 0.0, "singular_m": 0.0, "classification": "clean"}

    groups = flat[: num_groups * 4].reshape(num_groups, 4)
    v_orig = _variation(groups)

    # Masks
    m_mask = np.array([0, 1, 1, 0])
    neg_m_mask = np.array([0, -1, -1, 0])

    # Apply M
    g_m = np.zeros_like(groups)
    for col in range(4):
        g_m[:, col] = _flipping(groups[:, col], int(m_mask[col]))
    v_m = _variation(g_m)

    # Apply -M
    g_neg_m = np.zeros_like(groups)
    for col in range(4):
        g_neg_m[:, col] = _flipping(groups[:, col], int(neg_m_mask[col]))
    v_neg_m = _variation(g_neg_m)

    r_m = float(np.sum(v_m > v_orig)) / num_groups
    s_m = float(np.sum(v_m < v_orig)) / num_groups

    r_neg_m = float(np.sum(v_neg_m > v_orig)) / num_groups
    s_neg_m = float(np.sum(v_neg_m < v_orig)) / num_groups

    # Inverted groups with F1 on all pixels
    g_all1 = groups ^ 1
    v_all1 = _variation(g_all1)

    g_m_all1 = np.zeros_like(groups)
    for col in range(4):
        g_m_all1[:, col] = _flipping(g_all1[:, col], int(m_mask[col]))
    v_m_all1 = _variation(g_m_all1)

    g_neg_m_all1 = np.zeros_like(groups)
    for col in range(4):
        g_neg_m_all1[:, col] = _flipping(g_all1[:, col], int(neg_m_mask[col]))
    v_neg_m_all1 = _variation(g_neg_m_all1)

    r_m_inv = float(np.sum(v_m_all1 > v_all1)) / num_groups
    s_m_inv = float(np.sum(v_m_all1 < v_all1)) / num_groups

    r_neg_m_inv = float(np.sum(v_neg_m_all1 > v_all1)) / num_groups
    s_neg_m_inv = float(np.sum(v_neg_m_all1 < v_all1)) / num_groups

    d0 = r_m - s_m
    d1 = r_neg_m - s_neg_m

    denom = d1 + d0
    if abs(denom) < 1e-6:
        est_ratio = 0.0
    else:
        est_ratio = max(0.0, min(1.0, float((d1 - d0) / denom)))

    classification = "clean"
    if est_ratio > 0.30:
        classification = "likely_stego"
    elif est_ratio > 0.15:
        classification = "suspicious"

    return {
        "estimated_payload_ratio": round(est_ratio, 4),
        "regular_m": round(r_m, 4),
        "singular_m": round(s_m, 4),
        "regular_neg_m": round(r_neg_m, 4),
        "singular_neg_m": round(s_neg_m, 4),
        "classification": classification,
    }


def calibrate_thresholds_oracle(clean_images: List[Image.Image]) -> Dict[str, Any]:
    """Computes 95th and 99th percentiles across clean image dataset."""
    chi2_p_values = []
    rs_ratios = []

    for img in clean_images:
        c_res = chi_square_oracle(img)
        r_res = rs_analysis_oracle(img)
        chi2_p_values.append(c_res["p_value"])
        rs_ratios.append(r_res["estimated_payload_ratio"])

    chi2_95 = float(np.percentile(chi2_p_values, 95)) if chi2_p_values else 0.05
    chi2_99 = float(np.percentile(chi2_p_values, 99)) if chi2_p_values else 0.50

    rs_95 = float(np.percentile(rs_ratios, 95)) if rs_ratios else 0.08
    rs_99 = float(np.percentile(rs_ratios, 99)) if rs_ratios else 0.25

    return {
        "chi_square": {
            "suspicious_threshold": round(chi2_95, 4),
            "likely_stego_threshold": round(max(chi2_99, chi2_95 + 0.01), 4),
        },
        "rs_analysis": {
            "suspicious_threshold": round(rs_95, 4),
            "likely_stego_threshold": round(max(rs_99, rs_95 + 0.01), 4),
        },
    }
