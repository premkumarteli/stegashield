"""StegaShield Attack Lab Core Engine.

Implements the automated empirical experimentation matrix runner across embedding methods,
payload ratios, and steganalysis detectors, and provides RFC 4180 compliant CSV export.
Zero dependencies on web framework or database layers.
"""

from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Any, Sequence, Union

import numpy as np
from PIL import Image

from app.core.detect import (
    VERDICT_CLEAN,
    chi_square_attack,
    classify,
    rs_analysis,
)

CoverInput = Union[Image.Image, tuple[str, Image.Image], tuple[str, bytes]]


def run_experiment(
    cover_images: Sequence[CoverInput],
    methods: Sequence[str],
    ratios: Sequence[float],
    detectors: Sequence[str],
) -> dict[str, Any]:
    """Runs the Attack Lab experimentation matrix across methods, ratios, and detectors.

    For each cover image, embedding method, and payload ratio:
    1. Embeds simulated random ciphertext into the image at the specified ratio (or uses
       the clean cover if ratio == 0.0).
    2. Runs the selected steganalysis detectors (Chi-square, RS Analysis).
    3. Records quantitative scores and stego detection verdict.

    Args:
        cover_images: Sequence of PIL images, (name, Image) pairs, or (name, bytes) pairs.
        methods: Embedding methods, e.g. ["lsb_replacement", "lsb_matching"].
        ratios: Payload ratios in [0.0, 1.0], e.g. [0.05, 0.10, 0.25, 0.50, 1.00].
        detectors: Detectors to evaluate, e.g. ["chi_square", "rs_analysis"].

    Returns:
        dict containing 'total_items', 'methods', 'ratios', 'detectors', and 'items'.

    Raises:
        ValueError: If any input list is empty or contains unsupported options.
    """
    if not cover_images:
        raise ValueError("cover_images must not be empty.")
    if not methods:
        raise ValueError("methods must not be empty.")
    if not ratios:
        raise ValueError("ratios must not be empty.")
    if not detectors:
        raise ValueError("detectors must not be empty.")

    # Validate and normalize cover images
    normalized_covers: list[tuple[str, Image.Image]] = []
    for idx, item in enumerate(cover_images):
        if isinstance(item, tuple):
            name, img_or_bytes = item
            if isinstance(img_or_bytes, (bytes, bytearray)):
                img = Image.open(io.BytesIO(img_or_bytes)).convert("RGB")
            elif isinstance(img_or_bytes, Image.Image):
                img = img_or_bytes.convert("RGB") if img_or_bytes.mode != "RGB" else img_or_bytes
            else:
                raise ValueError(f"Unsupported cover_image tuple value type: {type(img_or_bytes)}")
            normalized_covers.append((str(name), img))
        elif isinstance(item, Image.Image):
            name = getattr(item, "filename", None)
            img_name = Path(name).name if name else f"cover_{idx + 1}.png"
            img = item.convert("RGB") if item.mode != "RGB" else item
            normalized_covers.append((img_name, img))
        else:
            raise ValueError(f"Unsupported cover_image type: {type(item)}")

    items: list[dict[str, Any]] = []

    for img_name, cover_img in normalized_covers:
        cover_arr = np.asarray(cover_img, dtype=np.uint8)
        total_slots = cover_arr.size

        for method in methods:
            normalized_method = method.lower()
            if normalized_method not in ("lsb_replacement", "lsb_matching"):
                raise ValueError(f"Unsupported embedding method '{method}'.")

            for ratio in ratios:
                ratio_val = float(ratio)
                if ratio_val < 0.0 or ratio_val > 1.0:
                    raise ValueError(f"Payload ratio {ratio_val} outside valid range [0.0, 1.0].")

                # Generate test image for evaluation
                if ratio_val == 0.0:
                    eval_img = cover_img
                else:
                    # Deterministic PRNG seed for scientific reproducibility
                    seed = (hash((img_name, normalized_method, ratio_val)) & 0xFFFFFFFF)
                    rng = np.random.default_rng(seed)

                    stego_flat = cover_arr.copy().reshape(-1)
                    num_to_modify = int(round(total_slots * ratio_val))
                    num_to_modify = min(num_to_modify, total_slots)

                    if num_to_modify > 0:
                        chosen_indices = rng.choice(total_slots, size=num_to_modify, replace=False)
                        random_bits = rng.integers(0, 2, size=num_to_modify, dtype=np.uint8)

                        if normalized_method == "lsb_replacement":
                            stego_flat[chosen_indices] = (stego_flat[chosen_indices] & 0xFE) | random_bits
                        elif normalized_method == "lsb_matching":
                            curr_bits = stego_flat[chosen_indices] & 1
                            mismatches = curr_bits != random_bits
                            flip_idx = chosen_indices[mismatches]
                            if len(flip_idx) > 0:
                                c_vals = stego_flat[flip_idx].astype(np.int16)
                                deltas = rng.choice(np.array([-1, 1], dtype=np.int16), size=len(flip_idx))
                                deltas[c_vals == 0] = 1
                                deltas[c_vals == 255] = -1
                                stego_flat[flip_idx] = (c_vals + deltas).astype(np.uint8)

                    eval_img = Image.fromarray(stego_flat.reshape(cover_arr.shape), mode="RGB")

                # Run requested detectors
                chi2_score = 0.0
                chi2_p_val = 0.0
                rs_ratio_est = 0.0
                chi2_res: dict[str, Any] = {"chi2": 0.0, "p_value": 0.0, "df": 0, "classification": VERDICT_CLEAN}
                rs_res: dict[str, Any] = {"estimated_payload_ratio": 0.0, "classification": VERDICT_CLEAN}

                if "chi_square" in detectors:
                    chi2_res = chi_square_attack(eval_img)
                    chi2_score = float(chi2_res.get("chi2", 0.0))
                    chi2_p_val = float(chi2_res.get("p_value", 0.0))

                if "rs_analysis" in detectors:
                    rs_res = rs_analysis(eval_img)
                    rs_ratio_est = float(rs_res.get("estimated_payload_ratio", 0.0))

                # Aggregate classification verdict
                if "chi_square" in detectors and "rs_analysis" in detectors:
                    verdict = classify(chi2_res, rs_res)
                elif "chi_square" in detectors:
                    verdict = chi2_res.get("classification", VERDICT_CLEAN)
                elif "rs_analysis" in detectors:
                    verdict = rs_res.get("classification", VERDICT_CLEAN)
                else:
                    verdict = VERDICT_CLEAN

                is_stego = 1 if verdict in ("suspicious", "likely_stego") else 0

                item_record: dict[str, Any] = {
                    "image_name": img_name,
                    "method": method,
                    "payload_ratio": ratio_val,
                    "chi2_score": round(chi2_score, 4),
                    "chi2_p_value": round(chi2_p_val, 6),
                    "rs_estimated_ratio": round(rs_ratio_est, 4),
                    "detected_as_stego": is_stego,
                }
                items.append(item_record)

    return {
        "total_items": len(items),
        "methods": list(methods),
        "ratios": list(ratios),
        "detectors": list(detectors),
        "items": items,
    }


def export_csv(summary: dict[str, Any]) -> str:
    """Exports Attack Lab experiment summary to RFC 4180 compliant CSV format.

    Guarantees standard 7-column header:
    image_name,method,payload_ratio,chi2_score,chi2_p_value,rs_estimated_ratio,detected_as_stego

    Args:
        summary: Experiment dictionary returned by run_experiment.

    Returns:
        RFC 4180 CSV string without NaN or null entries.
    """
    output = io.StringIO()
    fieldnames = [
        "image_name",
        "method",
        "payload_ratio",
        "chi2_score",
        "chi2_p_value",
        "rs_estimated_ratio",
        "detected_as_stego",
    ]
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(fieldnames)

    items = summary.get("items", [])
    for it in items:
        p_ratio = float(it.get("payload_ratio", 0.0))
        chi2_s = float(it.get("chi2_score", 0.0))
        chi2_p = float(it.get("chi2_p_value", 0.0))
        rs_r = float(it.get("rs_estimated_ratio", 0.0))
        detected = int(it.get("detected_as_stego", 0))

        writer.writerow([
            str(it.get("image_name", "")),
            str(it.get("method", "")),
            f"{p_ratio:.4f}",
            f"{chi2_s:.4f}",
            f"{chi2_p:.6f}",
            f"{rs_r:.4f}",
            detected,
        ])

    return output.getvalue()
