"""Unit Tests for StegaShield Attack Lab Core Engine.

Validates the experiment matrix runner across embedding methods, payload ratios,
and steganalysis detectors, as well as RFC 4180 CSV export.
"""

from __future__ import annotations

import csv
import io
import numpy as np
import pytest
from PIL import Image

from app.core.attack_lab import export_csv, run_experiment
from app.core.stego import METHOD_LSB_MATCHING, METHOD_LSB_REPLACEMENT


@pytest.fixture
def test_cover_img() -> Image.Image:
    """Creates a 64x64 textured test image."""
    arr = np.zeros((64, 64, 3), dtype=np.uint8)
    for y in range(64):
        for x in range(64):
            arr[y, x] = [(x * 3) % 256, (y * 5) % 256, ((x + y) * 2) % 256]
    return Image.fromarray(arr, mode="RGB")


@pytest.fixture
def test_cover_bytes(test_cover_img: Image.Image) -> bytes:
    """Returns PNG bytes of the test image."""
    buf = io.BytesIO()
    test_cover_img.save(buf, format="PNG")
    return buf.getvalue()


def test_run_experiment_basic(test_cover_img: Image.Image) -> None:
    """Runs a minimal 1-image, 1-method, 1-ratio, 1-detector experiment."""
    summary = run_experiment(
        cover_images=[test_cover_img],
        methods=[METHOD_LSB_REPLACEMENT],
        ratios=[0.10],
        detectors=["chi_square"],
    )
    assert summary["total_items"] == 1
    assert len(summary["items"]) == 1
    item = summary["items"][0]
    assert item["method"] == METHOD_LSB_REPLACEMENT
    assert item["payload_ratio"] == 0.10
    assert "chi2_score" in item
    assert "chi2_p_value" in item
    assert "detected_as_stego" in item
    assert item["detected_as_stego"] in (0, 1)


def test_run_experiment_matrix(test_cover_img: Image.Image) -> None:
    """Runs a 1-image * 2-methods * 3-ratios = 6 items experiment matrix."""
    methods = [METHOD_LSB_REPLACEMENT, METHOD_LSB_MATCHING]
    ratios = [0.0, 0.25, 0.50]
    detectors = ["chi_square", "rs_analysis"]

    summary = run_experiment(
        cover_images=[("my_cover.png", test_cover_img)],
        methods=methods,
        ratios=ratios,
        detectors=detectors,
    )

    assert summary["total_items"] == 6
    assert len(summary["items"]) == 6
    assert summary["methods"] == methods
    assert summary["ratios"] == ratios
    assert summary["detectors"] == detectors

    # Ratio 0.0 baseline should be clean
    baseline_items = [it for it in summary["items"] if it["payload_ratio"] == 0.0]
    assert len(baseline_items) == 2
    for it in baseline_items:
        assert it["image_name"] == "my_cover.png"


def test_run_experiment_cover_input_formats(
    test_cover_img: Image.Image, test_cover_bytes: bytes
) -> None:
    """Accepts Image.Image, (name, Image), and (name, bytes) input formats."""
    cover_images = [
        test_cover_img,
        ("named_img.png", test_cover_img),
        ("named_bytes.png", test_cover_bytes),
    ]

    summary = run_experiment(
        cover_images=cover_images,
        methods=[METHOD_LSB_REPLACEMENT],
        ratios=[0.05],
        detectors=["chi_square"],
    )
    assert summary["total_items"] == 3
    names = [it["image_name"] for it in summary["items"]]
    assert "named_img.png" in names
    assert "named_bytes.png" in names


def test_run_experiment_single_detector_branches(test_cover_img: Image.Image) -> None:
    """Tests evaluating chi_square only and rs_analysis only."""
    res_chi = run_experiment(
        cover_images=[test_cover_img],
        methods=[METHOD_LSB_REPLACEMENT],
        ratios=[0.50],
        detectors=["chi_square"],
    )
    assert res_chi["items"][0]["chi2_score"] >= 0.0

    res_rs = run_experiment(
        cover_images=[test_cover_img],
        methods=[METHOD_LSB_REPLACEMENT],
        ratios=[0.50],
        detectors=["rs_analysis"],
    )
    assert res_rs["items"][0]["rs_estimated_ratio"] >= 0.0


def test_run_experiment_input_validation(test_cover_img: Image.Image) -> None:
    """Validates error checking on invalid input parameters."""
    with pytest.raises(ValueError, match="cover_images must not be empty"):
        run_experiment([], [METHOD_LSB_REPLACEMENT], [0.1], ["chi_square"])

    with pytest.raises(ValueError, match="methods must not be empty"):
        run_experiment([test_cover_img], [], [0.1], ["chi_square"])

    with pytest.raises(ValueError, match="ratios must not be empty"):
        run_experiment([test_cover_img], [METHOD_LSB_REPLACEMENT], [], ["chi_square"])

    with pytest.raises(ValueError, match="detectors must not be empty"):
        run_experiment([test_cover_img], [METHOD_LSB_REPLACEMENT], [0.1], [])

    with pytest.raises(ValueError, match="Unsupported embedding method"):
        run_experiment([test_cover_img], ["invalid_method"], [0.1], ["chi_square"])

    with pytest.raises(ValueError, match="outside valid range"):
        run_experiment([test_cover_img], [METHOD_LSB_REPLACEMENT], [-0.1], ["chi_square"])

    with pytest.raises(ValueError, match="outside valid range"):
        run_experiment([test_cover_img], [METHOD_LSB_REPLACEMENT], [1.5], ["chi_square"])

    with pytest.raises(ValueError, match="Unsupported cover_image type"):
        run_experiment([12345], [METHOD_LSB_REPLACEMENT], [0.1], ["chi_square"])  # type: ignore

    with pytest.raises(ValueError, match="Unsupported cover_image tuple value type"):
        run_experiment([("name", 12345)], [METHOD_LSB_REPLACEMENT], [0.1], ["chi_square"])  # type: ignore


def test_export_csv_schema_and_fidelity(test_cover_img: Image.Image) -> None:
    """Validates that export_csv produces RFC 4180 format with 7 required columns."""
    summary = run_experiment(
        cover_images=[("bench.png", test_cover_img)],
        methods=[METHOD_LSB_REPLACEMENT, METHOD_LSB_MATCHING],
        ratios=[0.10, 0.50],
        detectors=["chi_square", "rs_analysis"],
    )

    csv_text = export_csv(summary)
    assert len(csv_text.strip()) > 0

    reader = csv.DictReader(io.StringIO(csv_text.strip()))
    expected_headers = [
        "image_name",
        "method",
        "payload_ratio",
        "chi2_score",
        "chi2_p_value",
        "rs_estimated_ratio",
        "detected_as_stego",
    ]
    assert reader.fieldnames == expected_headers

    rows = list(reader)
    assert len(rows) == 4

    for row, item in zip(rows, summary["items"]):
        assert row["image_name"] == item["image_name"]
        assert row["method"] == item["method"]
        assert float(row["payload_ratio"]) == pytest.approx(item["payload_ratio"], abs=1e-4)
        assert float(row["chi2_score"]) == pytest.approx(item["chi2_score"], abs=1e-4)
        assert float(row["chi2_p_value"]) == pytest.approx(item["chi2_p_value"], abs=1e-4)
        assert float(row["rs_estimated_ratio"]) == pytest.approx(item["rs_estimated_ratio"], abs=1e-4)
        assert int(row["detected_as_stego"]) == item["detected_as_stego"]

        for col, val in row.items():
            assert val != ""
            assert val.lower() != "nan"
            assert val.lower() != "null"


def test_export_csv_empty_items() -> None:
    """export_csv on an empty experiment summary yields the header row cleanly."""
    empty_summary = {"items": []}
    csv_text = export_csv(empty_summary)
    lines = csv_text.strip().split("\n")
    assert len(lines) == 1
    assert "image_name" in lines[0]
