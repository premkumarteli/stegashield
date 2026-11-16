"""
StegaShield Tier 1: Attack Lab Automated Experiments & Reporting Tests (Features 13–14).
Validates experiment matrix runner, detection evaluation curves, and standardized CSV export.
"""

from __future__ import annotations

import csv
import io
import pytest

from tests.e2e.fixtures import (
    ImageGenerator,
    METHOD_LSB_REPLACEMENT,
    METHOD_LSB_MATCHING,
    EXPERIMENT_RATIOS,
    EXPERIMENT_DETECTORS,
)


# ==============================================================================
# Feature 13: Attack Lab Automated Experiments
# ==============================================================================

@pytest.mark.tier1
def test_t1_f13_01_payload_ratio_sweep(e2e_client):
    """TC-E2E-T1-F13-01: Attack Lab sweeps across ratios {0.05, 0.10, 0.25, 0.50, 1.00}."""
    cover = ImageGenerator.natural_texture(64, 64, seed=1)
    cover_bytes = ImageGenerator.to_bytes(cover, fmt="PNG")

    res = e2e_client.run_attack_lab(
        cover_images=[("cover_1.png", cover_bytes)],
        methods=[METHOD_LSB_REPLACEMENT],
        ratios=EXPERIMENT_RATIOS,
        detectors=["chi_square"],
    )

    assert res.success is True
    assert res.status_code == 200
    assert "ratios" in res.summary
    assert res.summary["ratios"] == EXPERIMENT_RATIOS


@pytest.mark.tier1
def test_t1_f13_02_multi_method_matrix(e2e_client):
    """TC-E2E-T1-F13-02: Attack Lab runs matrix across both LSB-R and LSB-M."""
    cover = ImageGenerator.gradient(64, 64)
    cover_bytes = ImageGenerator.to_bytes(cover, fmt="PNG")

    methods = [METHOD_LSB_REPLACEMENT, METHOD_LSB_MATCHING]
    ratios = [0.10, 0.50]
    res = e2e_client.run_attack_lab(
        cover_images=[("cover.png", cover_bytes)],
        methods=methods,
        ratios=ratios,
        detectors=["chi_square", "rs_analysis"],
    )

    assert res.success is True
    # 1 image * 2 methods * 2 ratios = 4 experiment items
    assert res.summary.get("total_items", len(res.summary.get("items", []))) == 4


@pytest.mark.tier1
def test_t1_f13_03_experiment_summary_structure(e2e_client):
    """TC-E2E-T1-F13-03: Attack Lab summary dictionary contains required schema fields."""
    cover = ImageGenerator.natural_texture(64, 64, seed=2)
    cover_bytes = ImageGenerator.to_bytes(cover, fmt="PNG")

    res = e2e_client.run_attack_lab(
        cover_images=[("cover.png", cover_bytes)],
        methods=[METHOD_LSB_REPLACEMENT],
        ratios=[0.05],
        detectors=["chi_square"],
    )

    summary = res.summary
    assert "methods" in summary
    assert "ratios" in summary
    assert "detectors" in summary
    assert "items" in summary
    assert len(summary["items"]) >= 1


@pytest.mark.tier1
def test_t1_f13_04_false_positive_rate_on_clean_images(e2e_client):
    """TC-E2E-T1-F13-04: Attack Lab records detection on clean images (ratio 0.0)."""
    clean_cover = ImageGenerator.natural_texture(64, 64, seed=99)
    clean_bytes = ImageGenerator.to_bytes(clean_cover, fmt="PNG")

    res = e2e_client.run_attack_lab(
        cover_images=[("clean.png", clean_bytes)],
        methods=[METHOD_LSB_REPLACEMENT],
        ratios=[0.0],  # Clean baseline
        detectors=["chi_square"],
    )

    assert res.success is True
    items = res.summary.get("items", [])
    assert len(items) == 1
    assert items[0]["payload_ratio"] == 0.0


@pytest.mark.tier1
def test_t1_f13_05_experiment_completion_state(e2e_client):
    """TC-E2E-T1-F13-05: Experiment run completes with a valid experiment_id and status 200."""
    cover = ImageGenerator.flat(64, 64)
    cover_bytes = ImageGenerator.to_bytes(cover, fmt="PNG")

    res = e2e_client.run_attack_lab(
        cover_images=[("flat.png", cover_bytes)],
        methods=[METHOD_LSB_REPLACEMENT],
        ratios=[0.10],
        detectors=["chi_square"],
    )

    assert res.success is True
    assert res.status_code == 200
    assert res.experiment_id is not None
    assert len(res.experiment_id) > 0


# ==============================================================================
# Feature 14: Attack Lab Reporting & CSV Export
# ==============================================================================

@pytest.mark.tier1
def test_t1_f14_01_csv_export_content(e2e_client):
    """TC-E2E-T1-F14-01: Attack Lab returns non-empty CSV export string."""
    cover = ImageGenerator.gradient(64, 64)
    cover_bytes = ImageGenerator.to_bytes(cover, fmt="PNG")

    res = e2e_client.run_attack_lab(
        cover_images=[("test.png", cover_bytes)],
        methods=[METHOD_LSB_REPLACEMENT],
        ratios=[0.05, 0.25],
        detectors=["chi_square", "rs_analysis"],
    )

    assert res.success is True
    assert res.csv_content is not None
    assert len(res.csv_content.strip()) > 0


@pytest.mark.tier1
def test_t1_f14_02_csv_header_columns(e2e_client):
    """TC-E2E-T1-F14-02: Exported CSV headers match the exact required schema."""
    cover = ImageGenerator.gradient(64, 64)
    cover_bytes = ImageGenerator.to_bytes(cover, fmt="PNG")

    res = e2e_client.run_attack_lab(
        cover_images=[("test.png", cover_bytes)],
        methods=[METHOD_LSB_REPLACEMENT],
        ratios=[0.05],
        detectors=["chi_square"],
    )

    reader = csv.reader(io.StringIO(res.csv_content))
    header = next(reader)
    required_cols = [
        "image_name",
        "method",
        "payload_ratio",
        "chi2_score",
        "chi2_p_value",
        "rs_estimated_ratio",
        "detected_as_stego",
    ]
    for col in required_cols:
        assert col in header, f"Required column '{col}' missing from CSV headers: {header}"


@pytest.mark.tier1
def test_t1_f14_03_csv_data_row_count(e2e_client):
    """TC-E2E-T1-F14-03: CSV row count equals the total items evaluated in the experiment."""
    cover = ImageGenerator.gradient(64, 64)
    cover_bytes = ImageGenerator.to_bytes(cover, fmt="PNG")

    ratios = [0.05, 0.10, 0.25]
    methods = [METHOD_LSB_REPLACEMENT, METHOD_LSB_MATCHING]
    res = e2e_client.run_attack_lab(
        cover_images=[("test.png", cover_bytes)],
        methods=methods,
        ratios=ratios,
        detectors=["chi_square"],
    )

    reader = csv.reader(io.StringIO(res.csv_content.strip()))
    rows = list(reader)
    # Header row + (2 methods * 3 ratios = 6 data rows)
    data_rows = rows[1:]
    assert len(data_rows) == 6


@pytest.mark.tier1
def test_t1_f14_04_csv_numerical_fidelity(e2e_client):
    """TC-E2E-T1-F14-04: Numerical data in CSV matches summary item values."""
    cover = ImageGenerator.natural_texture(64, 64, seed=5)
    cover_bytes = ImageGenerator.to_bytes(cover, fmt="PNG")

    res = e2e_client.run_attack_lab(
        cover_images=[("test_fid.png", cover_bytes)],
        methods=[METHOD_LSB_REPLACEMENT],
        ratios=[0.10],
        detectors=["chi_square"],
    )

    reader = csv.DictReader(io.StringIO(res.csv_content.strip()))
    rows = list(reader)
    assert len(rows) == 1
    csv_row = rows[0]

    item = res.summary["items"][0]
    assert float(csv_row["payload_ratio"]) == pytest.approx(item["payload_ratio"], abs=1e-4)
    assert float(csv_row["chi2_score"]) == pytest.approx(item["chi2_score"], abs=1e-4)
    assert float(csv_row["chi2_p_value"]) == pytest.approx(item["chi2_p_value"], abs=1e-4)


@pytest.mark.tier1
def test_t1_f14_05_honest_reporting_no_fabrication(e2e_client):
    """TC-E2E-T1-F14-05: CSV data contains honest, real calculated values without NaN or fabricated nulls."""
    cover = ImageGenerator.natural_texture(64, 64, seed=6)
    cover_bytes = ImageGenerator.to_bytes(cover, fmt="PNG")

    res = e2e_client.run_attack_lab(
        cover_images=[("test_honest.png", cover_bytes)],
        methods=[METHOD_LSB_REPLACEMENT],
        ratios=[0.05, 0.25],
        detectors=["chi_square", "rs_analysis"],
    )

    reader = csv.DictReader(io.StringIO(res.csv_content.strip()))
    for row in reader:
        for k, v in row.items():
            assert v is not None and v != ""
            assert v.lower() != "nan", f"Fabricated/invalid NaN value found for column {k}"
            assert v.lower() != "null", f"Null placeholder found for column {k}"
