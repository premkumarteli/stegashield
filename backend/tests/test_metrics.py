"""Comprehensive Unit Tests for StegaShield Distortion & Image Quality Metrics.

Covers MSE, PSNR (including infinity edge case), SSIM (vectorized Wang et al. 2004),
amplified difference heatmaps, LSB bitplane visualizations, and PoV histograms.
"""

from __future__ import annotations

import math
import numpy as np
import pytest
from PIL import Image

from app.core.metrics import (
    calculate_metrics,
    calculate_pov_histogram,
    generate_bitplane,
    generate_diff_heatmap,
)


def test_calculate_metrics_identical_images(small_cover_png: Image.Image) -> None:
    """Verifies identical images yield MSE=0.0, PSNR=inf, and SSIM=1.0."""
    res = calculate_metrics(small_cover_png, small_cover_png)
    assert res["mse"] == 0.0
    assert math.isinf(res["psnr"])
    assert res["ssim"] == 1.0


def test_calculate_metrics_single_bit_flip(small_cover_png: Image.Image) -> None:
    """Flips 1 bit in 1 pixel; verifies metrics change by very small epsilon."""
    arr = np.array(small_cover_png, dtype=np.uint8)
    arr[0, 0, 0] ^= 1  # Flip 1 LSB
    stego = Image.fromarray(arr, mode="RGB")

    res = calculate_metrics(small_cover_png, stego)
    assert 0.0 < res["mse"] < 0.001
    assert res["psnr"] > 80.0
    assert 0.9999 <= res["ssim"] <= 1.0


def test_calculate_metrics_uniform_noise(small_cover_png: Image.Image) -> None:
    """Verifies mathematical consistency of PSNR formula under noise."""
    arr = np.array(small_cover_png, dtype=np.int16)
    noise = np.random.choice([-1, 1], size=arr.shape)
    noisy_arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    noisy_img = Image.fromarray(noisy_arr, mode="RGB")

    res = calculate_metrics(small_cover_png, noisy_img)
    expected_psnr = 20.0 * math.log10(255.0) - 10.0 * math.log10(res["mse"])
    assert math.isclose(res["psnr"], expected_psnr, rel_tol=1e-3)


def test_calculate_metrics_black_vs_white() -> None:
    """Compares all-0 image with all-255 image: MSE=65025.0, PSNR=0.0, SSIM ~ 0.0."""
    black = Image.new("RGB", (32, 32), color=(0, 0, 0))
    white = Image.new("RGB", (32, 32), color=(255, 255, 255))

    res = calculate_metrics(black, white)
    assert res["mse"] == 65025.0
    assert res["psnr"] == 0.0
    assert res["ssim"] < 0.001


def test_calculate_metrics_dimension_mismatch() -> None:
    """Asserts images with differing dimensions raise ValueError."""
    img1 = Image.new("RGB", (32, 32))
    img2 = Image.new("RGB", (32, 33))
    with pytest.raises(ValueError, match="Image dimensions do not match"):
        calculate_metrics(img1, img2)


def test_calculate_metrics_mode_conversion(small_cover_png: Image.Image) -> None:
    """Passes RGBA and Grayscale (mode L) images; verifies automatic conversion to RGB."""
    rgba = small_cover_png.convert("RGBA")
    gray = small_cover_png.convert("L")

    res_rgba = calculate_metrics(small_cover_png, rgba)
    assert res_rgba["mse"] == 0.0
    assert res_rgba["ssim"] == 1.0

    res_gray = calculate_metrics(small_cover_png, gray)
    assert "mse" in res_gray and "psnr" in res_gray and "ssim" in res_gray


def test_diff_heatmap_identical_images(small_cover_png: Image.Image) -> None:
    """Asserts heatmap between identical images is completely black (all 0s)."""
    heatmap = generate_diff_heatmap(small_cover_png, small_cover_png)
    arr = np.array(heatmap)
    assert arr.shape == (64, 64, 3)
    assert np.all(arr == 0)


def test_diff_heatmap_single_channel_modification(small_cover_png: Image.Image) -> None:
    """Modifies Red channel by 1; asserts modified pixel is (255, 0, 0) and others are 0."""
    arr = np.array(small_cover_png, dtype=np.uint8)
    arr[10, 10, 0] = (int(arr[10, 10, 0]) + 1) % 256
    stego = Image.fromarray(arr, mode="RGB")

    heatmap = generate_diff_heatmap(small_cover_png, stego)
    h_arr = np.array(heatmap)
    assert np.array_equal(h_arr[10, 10], [255, 0, 0])
    # Remaining pixels should be black
    h_arr[10, 10] = [0, 0, 0]
    assert np.all(h_arr == 0)


def test_diff_heatmap_clamping(small_cover_png: Image.Image) -> None:
    """Modifies channel by 10; asserts amplified value clamps to 255 without overflow."""
    arr = np.array(small_cover_png, dtype=np.uint8)
    arr[5, 5, 1] = (int(arr[5, 5, 1]) + 10) % 256
    stego = Image.fromarray(arr, mode="RGB")

    heatmap = generate_diff_heatmap(small_cover_png, stego)
    h_arr = np.array(heatmap)
    assert np.array_equal(h_arr[5, 5], [0, 255, 0])


def test_diff_heatmap_dimensions(small_cover_png: Image.Image) -> None:
    """Verifies output image dimensions match input images and mode is strictly RGB."""
    heatmap = generate_diff_heatmap(small_cover_png, small_cover_png)
    assert heatmap.size == small_cover_png.size
    assert heatmap.mode == "RGB"


def test_diff_heatmap_dimension_mismatch() -> None:
    """Asserts differing image sizes raise ValueError."""
    img1 = Image.new("RGB", (40, 40))
    img2 = Image.new("RGB", (40, 50))
    with pytest.raises(ValueError, match="Image dimensions do not match"):
        generate_diff_heatmap(img1, img2)


def test_bitplane_combined(small_cover_png: Image.Image) -> None:
    """Verifies output of generate_bitplane(img, 'combined') is RGB with values in {0, 255}."""
    bp = generate_bitplane(small_cover_png, "combined")
    assert bp.mode == "RGB"
    arr = np.array(bp)
    unique_vals = np.unique(arr)
    for val in unique_vals:
        assert val in (0, 255)


def test_bitplane_individual_channels(small_cover_png: Image.Image) -> None:
    """Tests 'r', 'g', 'b' channels; verifies 3-channel visual grayscale representation."""
    for ch in ("r", "g", "b"):
        bp = generate_bitplane(small_cover_png, ch)
        assert bp.mode == "RGB"
        arr = np.array(bp)
        # In visual grayscale RGB, R == G == B across all pixels
        assert np.array_equal(arr[:, :, 0], arr[:, :, 1])
        assert np.array_equal(arr[:, :, 1], arr[:, :, 2])
        for val in np.unique(arr):
            assert val in (0, 255)


def test_bitplane_invalid_channel(small_cover_png: Image.Image) -> None:
    """Asserts invalid channel name raises ValueError."""
    with pytest.raises(ValueError, match="Unsupported channel 'alpha'"):
        generate_bitplane(small_cover_png, "alpha")


def test_pov_histogram_structure(small_cover_png: Image.Image) -> None:
    """Asserts return dict contains channel, total_samples, and 128 bins."""
    res = calculate_pov_histogram(small_cover_png, "all")
    assert res["channel"] == "all"
    assert res["total_samples"] == 64 * 64 * 3
    assert len(res["bins"]) == 128

    b0 = res["bins"][0]
    assert b0["k"] == 0
    assert b0["even_val"] == 0
    assert b0["odd_val"] == 1
    assert "even_count" in b0 and "odd_count" in b0 and "diff" in b0


def test_pov_histogram_sample_conservation(small_cover_png: Image.Image) -> None:
    """Asserts sum of (even_count + odd_count) equals total_samples."""
    for ch in ("all", "r", "g", "b"):
        res = calculate_pov_histogram(small_cover_png, ch)
        total_in_bins = sum(b["even_count"] + b["odd_count"] for b in res["bins"])
        assert total_in_bins == res["total_samples"]


def test_pov_histogram_equalization_effect(small_cover_png: Image.Image) -> None:
    """Compares clean gradient image with simulated high-capacity LSB replacement."""
    clean_hist = calculate_pov_histogram(small_cover_png, "all")
    clean_total_diff = sum(b["diff"] for b in clean_hist["bins"])

    # Simulate LSB replacement with random bits across all pixels
    arr = np.array(small_cover_png, dtype=np.uint8)
    flat = arr.reshape(-1)
    random_bits = np.random.randint(0, 2, size=len(flat), dtype=np.uint8)
    flat[:] = (flat & 0xFE) | random_bits

    stego_img = Image.fromarray(arr, mode="RGB")
    stego_hist = calculate_pov_histogram(stego_img, "all")
    stego_total_diff = sum(b["diff"] for b in stego_hist["bins"])

    # PoV equalization dramatically reduces pair difference
    assert clean_total_diff > 0
    assert stego_total_diff < clean_total_diff * 0.2


def test_pov_histogram_invalid_channel(small_cover_png: Image.Image) -> None:
    """Asserts invalid channel name raises ValueError."""
    with pytest.raises(ValueError, match="Unsupported channel 'xyz'"):
        calculate_pov_histogram(small_cover_png, "xyz")
