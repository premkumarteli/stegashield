"""Benchmark script generating the Phase 1 Detector Scores Table.

Evaluates Chi-Square and RS Analysis on clean images and at
5%, 10%, 25%, 50%, and 100% payload ratios for both
LSB Replacement and LSB Matching.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
from PIL import Image

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.core.detect import chi_square_attack, rs_analysis  # noqa: E402
from app.core.stego import (  # noqa: E402
    HEADER_OVERHEAD_BITS,
    METHOD_LSB_MATCHING,
    METHOD_LSB_REPLACEMENT,
    embed,
)


def get_benchmark_cover() -> Image.Image:
    """Loads a representative standard cover image from skimage.data (or synthetic fallback)."""
    try:
        import skimage.data as skdata

        arr = skdata.astronaut()
        # Resize to 256x256 for consistent benchmarking
        img = Image.fromarray(arr).resize((256, 256), Image.Resampling.LANCZOS)
        return img.convert("RGB")
    except Exception:
        # High-texture gradient
        x = np.linspace(20, 235, 256, dtype=np.uint8)
        xx, yy = np.meshgrid(x, x)
        arr = np.stack([xx, yy, ((xx.astype(int) + yy.astype(int)) // 2).astype(np.uint8)], axis=-1)
        return Image.fromarray(arr, mode="RGB")


def run_benchmark() -> None:
    cover = get_benchmark_cover()
    width, height = cover.size
    total_slots = width * height * 3  # e.g., 256*256*3 = 196608 bits
    usable_bits = total_slots - HEADER_OVERHEAD_BITS
    usable_bytes = usable_bits // 8

    print(f"Cover Image: {width}x{height} RGB ({total_slots} total slots, {usable_bytes} max payload bytes)\n")

    # Clean image scores
    clean_chi = chi_square_attack(cover)
    clean_rs = rs_analysis(cover)

    results: list[dict[str, str | float]] = []

    # Clean row
    results.append({
        "Method": "clean",
        "Payload %": "0%",
        "Payload Bytes": 0,
        "Chi-Square (p-val)": clean_chi["score"],
        "Chi2 Stat": clean_chi["chi2"],
        "RS Est. Ratio": clean_rs["score"],
        "PSNR (dB)": "inf",
    })

    payload_ratios = [0.05, 0.10, 0.25, 0.50, 1.00]
    methods = [
        ("replacement", METHOD_LSB_REPLACEMENT),
        ("matching", METHOD_LSB_MATCHING),
    ]

    rng = np.random.default_rng(seed=1337)
    fixed_password = "BenchmarkMasterPassword2026!"

    for method_label, method_const in methods:
        for r in payload_ratios:
            target_bytes = max(1, int(usable_bytes * r))
            # Generate random payload bytes (simulates encrypted ciphertext)
            payload_data = rng.bytes(target_bytes)

            try:
                stego_img, metrics = embed(
                    cover,
                    payload=payload_data,
                    password=fixed_password,
                    method=method_const,
                )
                chi_res = chi_square_attack(stego_img)
                rs_res = rs_analysis(stego_img)

                results.append({
                    "Method": method_label,
                    "Payload %": f"{int(r * 100)}%",
                    "Payload Bytes": target_bytes,
                    "Chi-Square (p-val)": chi_res["score"],
                    "Chi2 Stat": chi_res["chi2"],
                    "RS Est. Ratio": rs_res["score"],
                    "PSNR (dB)": round(metrics.get("psnr", 0.0), 2),
                })
            except Exception as e:
                print(f"Error on {method_label} at {r*100}%: {e}")

    # Print Markdown Table
    print("| Method | Payload % | Payload Size | Chi-Square (p-val) | Chi2 Stat | RS Analysis (Est. Ratio) | PSNR (dB) |")
    print("|:---|:---:|:---:|:---:|:---:|:---:|:---:|")
    for row in results:
        psnr_str = "∞" if row["PSNR (dB)"] == "inf" else f"{row['PSNR (dB)']} dB"
        print(
            f"| `{row['Method']}` | **{row['Payload %']}** | {row['Payload Bytes']} B | "
            f"**{row['Chi-Square (p-val)']:.6f}** | {row['Chi2 Stat']:.2f} | "
            f"**{row['RS Est. Ratio']:.4f}** | {psnr_str} |"
        )


if __name__ == "__main__":
    run_benchmark()
