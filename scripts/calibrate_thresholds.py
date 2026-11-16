"""StegaShield Detector Threshold Calibration Script.

Scores a corpus of clean natural images using Chi-Square and RS Analysis detectors,
derives empirical 95th (suspicious) and 99th (likely_stego) percentiles, and writes
the calibrated threshold configuration to config/thresholds.json.

Can be run directly via CLI:
    python scripts/calibrate_thresholds.py [--corpus-dir DIR] [--output PATH]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Sequence

import numpy as np
from PIL import Image

# Ensure backend is on pythonpath when script is executed directly
repo_root = Path(__file__).resolve().parent.parent
backend_dir = repo_root / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.detect import (  # noqa: E402
    DEFAULT_THRESHOLDS,
    chi_square_attack,
    rs_analysis,
)


def calibrate_thresholds(clean_images: Sequence[Image.Image]) -> dict[str, Any]:
    """Computes calibrated detector thresholds from a corpus of clean images.

    Args:
        clean_images: Sequence of clean PIL images to evaluate.

    Returns:
        dict matching the config/thresholds.json schema.
    """
    if not clean_images or len(clean_images) < 2:
        return {
            "chi_square": {
                "suspicious_threshold": DEFAULT_THRESHOLDS["chi_square"]["suspicious_threshold"],
                "likely_stego_threshold": DEFAULT_THRESHOLDS["chi_square"]["likely_stego_threshold"],
            },
            "rs_analysis": {
                "suspicious_threshold": DEFAULT_THRESHOLDS["rs_analysis"]["suspicious_threshold"],
                "likely_stego_threshold": DEFAULT_THRESHOLDS["rs_analysis"]["likely_stego_threshold"],
            },
        }

    chi2_p_values: list[float] = []
    rs_ratios: list[float] = []

    for img in clean_images:
        c_res = chi_square_attack(img)
        r_res = rs_analysis(img)
        chi2_p_values.append(float(c_res.get("p_value", 0.0)))
        rs_ratios.append(float(r_res.get("estimated_payload_ratio", 0.0)))

    chi2_95 = float(np.percentile(chi2_p_values, 95))
    chi2_99 = float(np.percentile(chi2_p_values, 99))
    rs_95 = float(np.percentile(rs_ratios, 95))
    rs_99 = float(np.percentile(rs_ratios, 99))

    # Enforce strict monotonic ordering
    chi2_99 = max(chi2_99, chi2_95 + 0.01)
    rs_99 = max(rs_99, rs_95 + 0.01)

    return {
        "chi_square": {
            "suspicious_threshold": round(chi2_95, 4),
            "likely_stego_threshold": round(chi2_99, 4),
        },
        "rs_analysis": {
            "suspicious_threshold": round(rs_95, 4),
            "likely_stego_threshold": round(rs_99, 4),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Calibrate StegaShield detector thresholds on clean images.")
    parser.add_argument(
        "--corpus-dir",
        type=str,
        default=None,
        help="Path to directory containing clean natural images (PNG, JPEG, BMP).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(repo_root / "config" / "thresholds.json"),
        help="Path to output thresholds.json configuration file.",
    )
    args = parser.parse_args(argv)

    images: list[Image.Image] = []
    if args.corpus_dir and os.path.isdir(args.corpus_dir):
        valid_exts = {".png", ".jpg", ".jpeg", ".bmp"}
        corpus_path = Path(args.corpus_dir)
        for f in corpus_path.iterdir():
            if f.suffix.lower() in valid_exts:
                try:
                    img = Image.open(f).convert("RGB")
                    images.append(img)
                except Exception as e:
                    print(f"Skipping {f.name}: {e}", file=sys.stderr)

    thresholds = calibrate_thresholds(images)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(thresholds, f, indent=2)

    print(f"Calibrated thresholds saved to {out_path}:")
    print(json.dumps(thresholds, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
