"""StegaShield Image Quality & Distortion Metrics Module.

Provides MSE, PSNR, SSIM (Wang et al. 2004 via scipy), amplified difference
heatmaps, LSB bitplane visualizations, and Pairs-of-Values (PoV) histograms.
"""

from __future__ import annotations

import math
from typing import Any, Final

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

# Wang et al. (2004) Structural Similarity constants
SSIM_K1: Final[float] = 0.01
SSIM_K2: Final[float] = 0.03
SSIM_L: Final[float] = 255.0  # Dynamic range for 8-bit images
SSIM_SIGMA: Final[float] = 1.5
SSIM_C1: Final[float] = (SSIM_K1 * SSIM_L) ** 2  # 6.5025
SSIM_C2: Final[float] = (SSIM_K2 * SSIM_L) ** 2  # 58.5225


def calculate_metrics(cover: Image.Image, stego: Image.Image) -> dict[str, float]:
    """Calculates MSE, PSNR, and SSIM between cover and stego images.

    Args:
        cover: Original cover PIL Image.
        stego: Steganographic modified PIL Image.

    Returns:
        dict[str, float]: {"mse": float, "psnr": float, "ssim": float}
        When images are identical, returns mse=0.0, psnr=float('inf'), ssim=1.0.

    Raises:
        ValueError: If image dimensions do not match.
    """
    c_img = cover.convert("RGB")
    s_img = stego.convert("RGB")

    if c_img.size != s_img.size:
        raise ValueError(
            f"Image dimensions do not match: cover={c_img.size}, stego={s_img.size}"
        )

    # Cast to float64 to prevent NumPy 2.x integer overflow/underflow
    c_arr = np.array(c_img, dtype=np.float64)
    s_arr = np.array(s_img, dtype=np.float64)

    # 1. Mean Squared Error (MSE) across RGB channels
    diff = c_arr - s_arr
    mse = float(np.mean(diff**2))

    # 2. Peak Signal-to-Noise Ratio (PSNR)
    if mse == 0.0:
        psnr = float("inf")
    else:
        psnr = float(20.0 * math.log10(SSIM_L) - 10.0 * math.log10(mse))

    # 3. Structural Similarity Index (SSIM) - Wang et al. (2004)
    # Vectorized 3D Gaussian filtering across spatial axes (0, 1) without color blurring
    sigmas = (SSIM_SIGMA, SSIM_SIGMA, 0.0)
    mu1 = gaussian_filter(c_arr, sigma=sigmas, mode="reflect")
    mu2 = gaussian_filter(s_arr, sigma=sigmas, mode="reflect")

    mu1_sq = mu1 * mu1
    mu2_sq = mu2 * mu2
    mu1_mu2 = mu1 * mu2

    sigma1_sq = gaussian_filter(c_arr * c_arr, sigma=sigmas, mode="reflect") - mu1_sq
    sigma2_sq = gaussian_filter(s_arr * s_arr, sigma=sigmas, mode="reflect") - mu2_sq
    sigma12 = gaussian_filter(c_arr * s_arr, sigma=sigmas, mode="reflect") - mu1_mu2

    numerator = (2.0 * mu1_mu2 + SSIM_C1) * (2.0 * sigma12 + SSIM_C2)
    denominator = (mu1_sq + mu2_sq + SSIM_C1) * (sigma1_sq + sigma2_sq + SSIM_C2)

    ssim_map = numerator / denominator
    ssim = float(np.mean(ssim_map))

    return {
        "mse": round(mse, 6),
        "psnr": psnr if math.isinf(psnr) else round(psnr, 4),
        "ssim": round(ssim, 6),
    }


def generate_diff_heatmap(cover: Image.Image, stego: Image.Image) -> Image.Image:
    """Generates an amplified difference visual RGB Image: min(|I1 - I2| * 255, 255).

    Args:
        cover: Original cover PIL Image.
        stego: Steganographic modified PIL Image.

    Returns:
        Image.Image: Visual RGB Image with amplified differences.

    Raises:
        ValueError: If image dimensions do not match.
    """
    c_img = cover.convert("RGB")
    s_img = stego.convert("RGB")

    if c_img.size != s_img.size:
        raise ValueError(
            f"Image dimensions do not match: cover={c_img.size}, stego={s_img.size}"
        )

    c_arr = np.array(c_img, dtype=np.int16)
    s_arr = np.array(s_img, dtype=np.int16)

    # Amplified difference: min(|I1 - I2| * 255, 255)
    diff = np.abs(c_arr - s_arr)
    amplified = np.clip(diff * 255, 0, 255).astype(np.uint8)

    return Image.fromarray(amplified, mode="RGB")


def generate_bitplane(image: Image.Image, channel: str = "combined") -> Image.Image:
    """Generates an LSB bitplane visual RGB Image: (I & 1) * 255.

    Args:
        image: Source PIL Image.
        channel: 'combined' (all 3 channels), 'r', 'g', or 'b'.

    Returns:
        Image.Image: Visual RGB Image displaying the LSB plane.

    Raises:
        ValueError: If channel argument is unrecognized.
    """
    img = image.convert("RGB")
    arr = np.array(img, dtype=np.uint8)
    lsb = (arr & 1) * np.uint8(255)

    norm_ch = channel.lower().strip()
    if norm_ch in ("combined", "all"):
        return Image.fromarray(lsb, mode="RGB")
    elif norm_ch in ("r", "red"):
        ch_plane = lsb[:, :, 0]
        rgb_plane = np.stack([ch_plane, ch_plane, ch_plane], axis=-1)
        return Image.fromarray(rgb_plane, mode="RGB")
    elif norm_ch in ("g", "green"):
        ch_plane = lsb[:, :, 1]
        rgb_plane = np.stack([ch_plane, ch_plane, ch_plane], axis=-1)
        return Image.fromarray(rgb_plane, mode="RGB")
    elif norm_ch in ("b", "blue"):
        ch_plane = lsb[:, :, 2]
        rgb_plane = np.stack([ch_plane, ch_plane, ch_plane], axis=-1)
        return Image.fromarray(rgb_plane, mode="RGB")
    else:
        raise ValueError(
            f"Unsupported channel '{channel}'. Choose from 'combined', 'r', 'g', 'b'."
        )


def calculate_pov_histogram(image: Image.Image, channel: str = "all") -> dict[str, Any]:
    """Calculates Pairs-of-Values (PoV) histogram counts for (2k, 2k+1) across [0..255].

    Args:
        image: Source PIL Image.
        channel: 'all' (flattens R, G, B), 'r', 'g', or 'b'.

    Returns:
        dict[str, Any]: Structured dictionary with keys:
            - 'channel': str
            - 'total_samples': int
            - 'bins': list of 128 dicts with 'k', 'even_val', 'odd_val', 'even_count', 'odd_count', 'diff'

    Raises:
        ValueError: If channel argument is unrecognized.
    """
    img = image.convert("RGB")
    arr = np.array(img, dtype=np.uint8)

    norm_ch = channel.lower().strip()
    if norm_ch in ("all", "combined"):
        flat = arr.flatten()
    elif norm_ch in ("r", "red"):
        flat = arr[:, :, 0].flatten()
    elif norm_ch in ("g", "green"):
        flat = arr[:, :, 1].flatten()
    elif norm_ch in ("b", "blue"):
        flat = arr[:, :, 2].flatten()
    else:
        raise ValueError(
            f"Unsupported channel '{channel}'. Choose from 'all', 'r', 'g', 'b'."
        )

    counts = np.bincount(flat, minlength=256)
    even_counts = counts[0::2]  # 2k for k=0..127
    odd_counts = counts[1::2]  # 2k+1 for k=0..127

    bins: list[dict[str, int]] = []
    for k in range(128):
        e_c = int(even_counts[k])
        o_c = int(odd_counts[k])
        bins.append(
            {
                "k": k,
                "even_val": 2 * k,
                "odd_val": 2 * k + 1,
                "even_count": e_c,
                "odd_count": o_c,
                "diff": abs(e_c - o_c),
            }
        )

    return {
        "channel": norm_ch,
        "total_samples": int(len(flat)),
        "bins": bins,
    }
