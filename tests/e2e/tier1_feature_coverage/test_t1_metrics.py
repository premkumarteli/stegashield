"""
StegaShield Tier 1: Distortion Metrics & Visualizations Tests (Feature 9).
Validates MSE, PSNR, SSIM, amplified difference heatmaps, bitplane, and PoV histograms.
"""

from __future__ import annotations

import math
import numpy as np
from PIL import Image
import pytest

from tests.e2e.client.direct_core_adapter import _get_core_module
from tests.e2e.fixtures import ImageGenerator, PASSWORD_VALID

metrics = _get_core_module("metrics")
stego = _get_core_module("stego")


# ==============================================================================
# Feature 9: Distortion Metrics & Visualizations
# ==============================================================================

@pytest.mark.tier1
def test_t1_f09_01_mse_and_psnr_computation():
    """TC-E2E-T1-F09-01: Identical images yield MSE=0, PSNR=inf; modified yields finite values."""
    img1 = ImageGenerator.natural_texture(128, 128, seed=1)
    img2 = img1.copy()

    # Identical images
    res_ident = metrics.calculate_metrics(img1, img2)
    assert res_ident["mse"] == 0.0
    assert math.isinf(res_ident["psnr"])
    assert res_ident["ssim"] == 1.0

    # 1-bit modified stego image
    stego_img, _ = stego.embed(img1, b"Short Secret", PASSWORD_VALID)
    res_mod = metrics.calculate_metrics(img1, stego_img)

    assert res_mod["mse"] > 0.0
    assert not math.isinf(res_mod["psnr"])
    assert res_mod["psnr"] > 50.0  # High fidelity steganography


@pytest.mark.tier1
def test_t1_f09_02_ssim_structural_similarity():
    """TC-E2E-T1-F09-02: SSIM between cover and slightly embedded stego is >= 0.98."""
    cover = ImageGenerator.natural_texture(256, 256, seed=2)
    stego_img, _ = stego.embed(cover, b"Academic Testing SSIM", PASSWORD_VALID)

    res = metrics.calculate_metrics(cover, stego_img)
    ssim = res["ssim"]
    assert 0.98 <= ssim <= 1.0, f"SSIM {ssim} was lower than expected for minimal embedding"


@pytest.mark.tier1
def test_t1_f09_03_amplified_difference_heatmap():
    """TC-E2E-T1-F09-03: Amplified diff heatmap highlights modified pixel coordinates."""
    cover = ImageGenerator.flat(64, 64, color=(128, 128, 128))
    stego_img, _ = stego.embed(cover, b"Secret Diff Data", PASSWORD_VALID)

    heatmap = metrics.generate_diff_heatmap(cover, stego_img)
    assert isinstance(heatmap, Image.Image)
    assert heatmap.size == cover.size
    assert heatmap.mode == "RGB"

    arr = np.array(heatmap)
    # Modified coordinates must be saturated to 255
    non_zero_pixels = np.sum(arr > 0)
    assert non_zero_pixels > 0, "Difference heatmap should contain amplified non-zero pixels"
    # Unmodified coordinates must be exactly 0
    zero_pixels = np.sum(arr == 0)
    assert zero_pixels > 0


@pytest.mark.tier1
def test_t1_f09_04_lsb_bitplane_visualizer():
    """TC-E2E-T1-F09-04: LSB bitplane produces high-contrast binary visualization in {0, 255}."""
    img = ImageGenerator.gradient(128, 128)
    bitplane = metrics.generate_bitplane(img, channel="combined")

    assert isinstance(bitplane, Image.Image)
    assert bitplane.size == img.size
    arr = np.array(bitplane)

    # Values must strictly be 0 or 255
    unique_vals = set(np.unique(arr))
    assert unique_vals.issubset({0, 255}), f"Unexpected bitplane values: {unique_vals}"


@pytest.mark.tier1
def test_t1_f09_05_pairs_of_values_histogram():
    """TC-E2E-T1-F09-05: PoV histogram extracts exactly 128 pairs for 8-bit channels."""
    img = ImageGenerator.step_wedge(256, 256, num_steps=16)
    hist = metrics.calculate_pov_histogram(img, channel="all")

    assert "bins" in hist
    assert "total_samples" in hist
    assert hist["total_samples"] == 256 * 256 * 3
    assert len(hist["bins"]) == 128

    # Verify first and last bins
    bin0 = hist["bins"][0]
    assert bin0["k"] == 0
    assert bin0["even_val"] == 0
    assert bin0["odd_val"] == 1

    bin127 = hist["bins"][127]
    assert bin127["k"] == 127
    assert bin127["even_val"] == 254
    assert bin127["odd_val"] == 255
