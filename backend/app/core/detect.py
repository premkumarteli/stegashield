"""StegaShield Steganalysis Core Module.

Implements statistical detection algorithms from primary literature:
1. Chi-Square Attack (Westfeld & Pfitzmann, 2000)
   Reference: A. Westfeld and A. Pfitzmann, "Attacks on Steganographic Systems",
   Information Hiding, LNCS 1768, pp. 61-76, 2000.
2. RS Analysis (Fridrich, Goljan, Du, 2001)
   Reference: J. Fridrich, M. Goljan, R. Du, "Detecting LSB Steganography in Color
   and Gray-Scale Images", IEEE Multimedia, vol. 8, no. 4, pp. 22-28, 2001.

Provides pure Python / NumPy / SciPy implementations with zero external framework dependencies.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Final, Optional

import numpy as np
import scipy.stats  # type: ignore[import-untyped]
from PIL import Image

VERDICT_CLEAN: Final[str] = "clean"
VERDICT_SUSPICIOUS: Final[str] = "suspicious"
VERDICT_LIKELY_STEGO: Final[str] = "likely_stego"

DEFAULT_THRESHOLDS: Final[dict[str, dict[str, float]]] = {
    "chi_square": {
        "suspicious_threshold": 0.05,
        "likely_stego_threshold": 0.50,
    },
    "rs_analysis": {
        "suspicious_threshold": 0.20,
        "likely_stego_threshold": 0.35,
    },
}


def _extract_channel_pixels(image: Image.Image, channel: Optional[str] = None) -> np.ndarray:
    """Extracts raw pixel array from a PIL Image normalized to RGB."""
    if image.mode != "RGB":
        rgb_image = image.convert("RGB")
    else:
        rgb_image = image

    arr = np.asarray(rgb_image, dtype=np.uint8)

    if channel is None or channel == "all":
        return arr
    elif channel.lower() == "r":
        return arr[:, :, 0]
    elif channel.lower() == "g":
        return arr[:, :, 1]
    elif channel.lower() == "b":
        return arr[:, :, 2]
    else:
        raise ValueError(f"Invalid channel '{channel}'. Expected None, 'all', 'r', 'g', or 'b'.")


def chi_square_attack(
    image: Image.Image,
    channel: Optional[str] = "all",
) -> dict[str, Any]:
    """Performs the Chi-Square statistical steganalysis attack (Westfeld & Pfitzmann, 2000).

    In natural images, adjacent intensity values in Pairs of Values (2k, 2k+1) have
    unequal frequencies due to natural texture and gradients. Random or encrypted LSB
    replacement equalizes the observed frequencies towards their arithmetic mean.

    Statistic = sum((observed - expected)^2 / (2 * expected)) for pairs where expected >= 4.
    Degrees of freedom df = valid_pairs - 1.
    p = scipy.stats.chi2.sf(statistic, df).

    A p-value near 1.0 indicates equalized pairs, suggesting LSB replacement embedding.

    Args:
        image: Cover or stego image.
        channel: Optional channel ('r', 'g', 'b', or 'all'/None for combined RGB).

    Returns:
        dict containing 'chi2', 'p_value', 'df', 'classification', 'score', 'valid_pairs', and 'details'.
    """
    arr = _extract_channel_pixels(image, channel)
    flat = arr.ravel()

    # Histogram of all 256 pixel intensity levels [0..255]
    counts = np.bincount(flat, minlength=256)

    # Pairs of Values (2k, 2k+1) for k in [0..127]
    observed_even = counts[0::2].astype(np.float64)
    observed_odd = counts[1::2].astype(np.float64)
    expected = (observed_even + observed_odd) / 2.0

    # Cochran's rule: filter pairs with expected frequency >= 4.0
    valid = expected >= 4.0
    valid_count = int(np.sum(valid))

    if valid_count <= 1:
        return {
            "chi2": 0.0,
            "p_value": 0.0,
            "df": 0,
            "classification": VERDICT_CLEAN,
            "score": 0.0,
            "valid_pairs": valid_count,
            "details": {
                "valid_pairs": valid_count,
                "total_pairs": 128,
                "expected_mean": 0.0,
            },
        }

    obs_even = observed_even[valid]
    obs_odd = observed_odd[valid]
    exp = expected[valid]

    # Chi-square statistic across valid pairs: sum((even - odd)^2 / (2 * expected))
    diff_sq = (obs_even - obs_odd) ** 2
    statistic = float(np.sum(diff_sq / (2.0 * exp)))
    dof = valid_count - 1
    p_value = float(scipy.stats.chi2.sf(statistic, dof))

    # Clamp score to [0.0, 1.0] and handle NaN/infinite
    if math.isnan(p_value) or math.isinf(p_value):
        p_value = 0.0
    p_value = max(0.0, min(1.0, p_value))

    # Threshold-based classification
    if p_value >= 0.50:
        classification = VERDICT_LIKELY_STEGO
    elif p_value >= 0.05:
        classification = VERDICT_SUSPICIOUS
    else:
        classification = VERDICT_CLEAN

    return {
        "chi2": round(statistic, 4),
        "p_value": round(p_value, 6),
        "df": dof,
        "classification": classification,
        "score": round(p_value, 6),
        "valid_pairs": valid_count,
        "details": {
            "valid_pairs": valid_count,
            "total_pairs": 128,
            "expected_mean": float(np.mean(exp)),
        },
    }


def _rs_channel_vectorized(flat: np.ndarray) -> tuple[float, float, float, float, float]:
    """Performs fully vectorized RS analysis on a flattened 1D pixel channel array.

    Evaluates non-overlapping 4-pixel groups with masks M = [0, 1, 1, 0] and -M = [0, -1, -1, 0].
    Uses the exact Fridrich, Goljan, Du (2001) quadratic model to solve for payload ratio.

    Returns:
        (estimated_ratio, regular_m, singular_m, regular_neg_m, singular_neg_m)
    """
    n_groups = len(flat) // 4
    if n_groups < 16:
        return 0.0, 0.0, 0.0, 0.0, 0.0

    groups = flat[: n_groups * 4].reshape(n_groups, 4).astype(np.int32)
    v0 = np.sum(np.abs(np.diff(groups, axis=1)), axis=1)

    # Vectorized dual flipping F_{-1}: even -> max(0, x-1), odd -> min(255, x+1)
    def f_neg1(v: np.ndarray) -> np.ndarray:
        return np.where((v & 1) == 0, np.maximum(0, v - 1), np.minimum(255, v + 1))

    # Standard mask M = [0, 1, 1, 0]
    gm = groups.copy()
    gm[:, 1] ^= 1
    gm[:, 2] ^= 1
    vm = np.sum(np.abs(np.diff(gm, axis=1)), axis=1)

    # Negative mask -M = [0, -1, -1, 0]
    gnm = groups.copy()
    gnm[:, 1] = f_neg1(groups[:, 1])
    gnm[:, 2] = f_neg1(groups[:, 2])
    vnm = np.sum(np.abs(np.diff(gnm, axis=1)), axis=1)

    r_m = float(np.mean(vm > v0))
    s_m = float(np.mean(vm < v0))
    r_nm = float(np.mean(vnm > v0))
    s_nm = float(np.mean(vnm < v0))

    d0 = r_m - s_m
    d_nm0 = r_nm - s_nm

    # Inverted carrier (all bits flipped via F1)
    g1 = groups ^ 1
    v1 = np.sum(np.abs(np.diff(g1, axis=1)), axis=1)

    gm1 = g1.copy()
    gm1[:, 1] ^= 1
    gm1[:, 2] ^= 1
    vm1 = np.sum(np.abs(np.diff(gm1, axis=1)), axis=1)

    gnm1 = g1.copy()
    gnm1[:, 1] = f_neg1(g1[:, 1])
    gnm1[:, 2] = f_neg1(g1[:, 2])
    vnm1 = np.sum(np.abs(np.diff(gnm1, axis=1)), axis=1)

    r_m1 = float(np.mean(vm1 > v1))
    s_m1 = float(np.mean(vm1 < v1))
    r_nm1 = float(np.mean(vnm1 > v1))
    s_nm1 = float(np.mean(vnm1 < v1))

    d1 = r_m1 - s_m1
    d_nm1 = r_nm1 - s_nm1

    # Quadratic equation: 2(d1 + d0)x^2 + (d_{-0} - d_{-1} - d1 - 3d0)x + (d0 - d_{-0}) = 0
    a = 2.0 * (d1 + d0)
    b = d_nm0 - d_nm1 - d1 - 3.0 * d0
    c = d0 - d_nm0

    if abs(a) < 1e-4:
        if abs(b) > 1e-8:
            x = -c / b
        else:
            x = 0.0
    else:
        disc = b * b - 4.0 * a * c
        if disc < 0:
            if abs(b) > 1e-8:
                x = -c / b
            else:
                x = 0.0
        else:
            sqrt_disc = math.sqrt(disc)
            x1 = (-b + sqrt_disc) / (2.0 * a)
            x2 = (-b - sqrt_disc) / (2.0 * a)
            # pick root with smaller absolute value or closest to physical range
            if abs(x1) <= abs(x2):
                x = x1
            else:
                x = x2

    # Conversion to payload ratio p = |x / (x - 0.5)|
    if abs(x - 0.5) < 1e-6:
        p = 0.0
    else:
        p = abs(x / (x - 0.5))

    if math.isnan(p) or math.isinf(p):
        p = 0.0

    p = float(np.clip(p, 0.0, 1.0))
    return p, r_m, s_m, r_nm, s_nm


def rs_analysis(
    image: Image.Image,
    channel: Optional[str] = None,
) -> dict[str, Any]:
    """Performs RS Steganalysis (Fridrich, Goljan, Du, 2001).

    Estimates the percentage of LSB-flipped pixels by evaluating Regular and Singular
    groups under dual flipping masks M and -M, solving a quadratic equation to estimate
    the embedded fraction p.

    Vectorized across horizontal groups of 4 consecutive pixels with zero pixel loops.
    Returns the mean estimated payload ratio across active channels, clipped to [0, 1].

    Args:
        image: Cover or stego image.
        channel: Specific channel ('r', 'g', 'b') or None/'all' for active channel mean.

    Returns:
        dict containing 'estimated_payload_ratio', 'regular_m', 'singular_m',
        'regular_neg_m', 'singular_neg_m', 'classification', 'channel_ratios',
        'score', and 'channel_scores'.
    """
    if image.mode != "RGB":
        rgb_image = image.convert("RGB")
    else:
        rgb_image = image

    arr = np.asarray(rgb_image, dtype=np.uint8)

    if channel is not None and channel.lower() in ("r", "g", "b"):
        idx = {"r": 0, "g": 1, "b": 2}[channel.lower()]
        p_val, rm, sm, rnm, snm = _rs_channel_vectorized(arr[:, :, idx].ravel())
        ch_key = channel.lower()
        classification = (
            VERDICT_LIKELY_STEGO
            if p_val >= 0.35
            else (VERDICT_SUSPICIOUS if p_val >= 0.20 else VERDICT_CLEAN)
        )
        return {
            "estimated_payload_ratio": round(p_val, 4),
            "regular_m": round(rm, 4),
            "singular_m": round(sm, 4),
            "regular_neg_m": round(rnm, 4),
            "singular_neg_m": round(snm, 4),
            "classification": classification,
            "channel_ratios": {ch_key: round(p_val, 4)},
            "score": round(p_val, 4),
            "channel_scores": {ch_key: round(p_val, 4)},
        }

    # Evaluate each RGB channel separately and average
    p_r, rm_r, sm_r, rnm_r, snm_r = _rs_channel_vectorized(arr[:, :, 0].ravel())
    p_g, rm_g, sm_g, rnm_g, snm_g = _rs_channel_vectorized(arr[:, :, 1].ravel())
    p_b, rm_b, sm_b, rnm_b, snm_b = _rs_channel_vectorized(arr[:, :, 2].ravel())

    mean_p = float(np.clip((p_r + p_g + p_b) / 3.0, 0.0, 1.0))
    mean_rm = float((rm_r + rm_g + rm_b) / 3.0)
    mean_sm = float((sm_r + sm_g + sm_b) / 3.0)
    mean_rnm = float((rnm_r + rnm_g + rnm_b) / 3.0)
    mean_snm = float((snm_r + snm_g + snm_b) / 3.0)

    classification = (
        VERDICT_LIKELY_STEGO
        if mean_p >= 0.35
        else (VERDICT_SUSPICIOUS if mean_p >= 0.20 else VERDICT_CLEAN)
    )

    channel_dict = {
        "r": round(p_r, 4),
        "g": round(p_g, 4),
        "b": round(p_b, 4),
    }

    return {
        "estimated_payload_ratio": round(mean_p, 4),
        "regular_m": round(mean_rm, 4),
        "singular_m": round(mean_sm, 4),
        "regular_neg_m": round(mean_rnm, 4),
        "singular_neg_m": round(mean_snm, 4),
        "classification": classification,
        "channel_ratios": channel_dict,
        "score": round(mean_p, 4),
        "channel_scores": channel_dict,
    }


def classify(
    chi2_res: dict[str, Any],
    rs_res: dict[str, Any],
    thresholds: Optional[dict[str, Any]] = None,
) -> str:
    """Classifies an image based on Chi-square and RS Analysis detector outputs.

    Args:
        chi2_res: Output dictionary from chi_square_attack.
        rs_res: Output dictionary from rs_analysis.
        thresholds: Optional dictionary mapping detector names to suspicious and
            likely_stego thresholds. If omitted, attempts to load from config/thresholds.json,
            falling back to safe defaults.

    Returns:
        One of VERDICT_CLEAN, VERDICT_SUSPICIOUS, or VERDICT_LIKELY_STEGO.
    """
    if thresholds is None:
        cfg_path = Path(__file__).resolve().parent.parent.parent.parent / "config" / "thresholds.json"
        if cfg_path.is_file():
            try:
                with open(cfg_path, "r", encoding="utf-8") as f:
                    thresholds = json.load(f)
            except Exception:
                thresholds = DEFAULT_THRESHOLDS
        else:
            thresholds = DEFAULT_THRESHOLDS

    chi_thresh = thresholds.get("chi_square", DEFAULT_THRESHOLDS["chi_square"])
    rs_thresh = thresholds.get("rs_analysis", DEFAULT_THRESHOLDS["rs_analysis"])

    chi_susp = chi_thresh.get("suspicious_threshold", 0.05)
    chi_likely = chi_thresh.get("likely_stego_threshold", 0.50)

    rs_susp = rs_thresh.get("suspicious_threshold", 0.20)
    rs_likely = rs_thresh.get("likely_stego_threshold", 0.35)

    chi_p = float(chi2_res.get("p_value", 0.0))
    rs_ratio = float(rs_res.get("estimated_payload_ratio", 0.0))

    if chi_p >= chi_likely:
        verdict_chi = VERDICT_LIKELY_STEGO
    elif chi_p >= chi_susp:
        verdict_chi = VERDICT_SUSPICIOUS
    else:
        verdict_chi = VERDICT_CLEAN

    if rs_ratio >= rs_likely:
        verdict_rs = VERDICT_LIKELY_STEGO
    elif rs_ratio >= rs_susp:
        verdict_rs = VERDICT_SUSPICIOUS
    else:
        verdict_rs = VERDICT_CLEAN

    rank = {VERDICT_CLEAN: 0, VERDICT_SUSPICIOUS: 1, VERDICT_LIKELY_STEGO: 2}
    return verdict_chi if rank[verdict_chi] >= rank[verdict_rs] else verdict_rs


def classify_verdict(
    score: float,
    threshold_suspicious: float,
    threshold_likely: float,
) -> str:
    """Classifies a detection score into 'clean', 'suspicious', or 'likely_stego'.

    Args:
        score: Estimated detector score in [0.0, 1.0].
        threshold_suspicious: 95th percentile baseline score on clean images.
        threshold_likely: 99th percentile baseline score on clean images.

    Returns:
        One of VERDICT_CLEAN, VERDICT_SUSPICIOUS, or VERDICT_LIKELY_STEGO.
    """
    if score <= threshold_suspicious:
        return VERDICT_CLEAN
    elif score <= threshold_likely:
        return VERDICT_SUSPICIOUS
    else:
        return VERDICT_LIKELY_STEGO
