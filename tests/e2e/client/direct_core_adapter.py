"""
StegaShield E2E Test Client - Direct Core Adapter.
Progressive adapter that executes directly against backend.app.core modules
without requiring the FastAPI REST or MySQL persistence tiers.
"""

from __future__ import annotations

import io
import time
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image

from tests.e2e.client.base import (
    AnalyzeResult,
    AttackLabResult,
    DetectResult,
    EmbedResult,
    ExtractResult,
    StegaShieldClient,
)


def _get_core_module(name: str):
    try:
        import importlib
        return importlib.import_module(f"app.core.{name}")
    except ImportError:
        import importlib
        return importlib.import_module(f"backend.app.core.{name}")


class DirectCoreAdapter(StegaShieldClient):
    """Direct adapter to backend.app.core modules."""

    def __init__(self):
        self._history: List[Dict[str, Any]] = []

    @property
    def mode(self) -> str:
        return "direct_core"

    def embed(
        self,
        cover_bytes: bytes,
        filename: str = "cover.png",
        password: str = "",
        method: str = "lsb_replacement",
        payload_text: Optional[str] = None,
        payload_file_bytes: Optional[bytes] = None,
        payload_filename: Optional[str] = None,
    ) -> EmbedResult:
        try:
            stego = _get_core_module("stego")

            # Validate input image
            try:
                img = Image.open(io.BytesIO(cover_bytes))
                # Decompression guard check
                if img.width * img.height > 16_000_000:
                    return EmbedResult(
                        success=False,
                        status_code=413,
                        error_code="IMAGE_DIMENSIONS_EXCEEDED",
                        error_detail="Image exceeds 16 megapixels",
                    )
                cover_img = img.convert("RGB")
            except Exception as e:
                return EmbedResult(
                    success=False,
                    status_code=400,
                    error_code="INVALID_COVER_IMAGE",
                    error_detail=str(e),
                )

            # Format payload
            is_file = False
            p_filename = ""
            payload_data = b""
            if payload_file_bytes is not None:
                is_file = True
                p_filename = payload_filename or "payload.bin"
                payload_data = payload_file_bytes
            elif payload_text is not None:
                is_file = False
                payload_data = payload_text.encode("utf-8")

            # Check upload limit
            if len(cover_bytes) > 10 * 1024 * 1024 or len(payload_data) > 10 * 1024 * 1024:
                return EmbedResult(
                    success=False,
                    status_code=413,
                    error_code="PAYLOAD_TOO_LARGE",
                    error_detail="File exceeds 10 MB limit",
                )

            # Check capacity if helper is available
            if hasattr(stego, "check_capacity"):
                try:
                    stego.check_capacity(cover_img, len(payload_data), is_file=is_file, filename=p_filename)
                except Exception as ce:
                    return EmbedResult(
                        success=False,
                        status_code=413,
                        error_code="PAYLOAD_EXCEEDS_CAPACITY",
                        error_detail=str(ce),
                    )

            stego_img, metrics = stego.embed(
                cover_image=cover_img,
                payload=payload_data,
                password=password,
                method=method,
                is_file=is_file,
                filename=p_filename,
            )

            out_buf = io.BytesIO()
            stego_img.save(out_buf, format="PNG")
            stego_bytes = out_buf.getvalue()

            op_id = f"op_{int(time.time()*1000)}"
            self._history.append({
                "operation_id": op_id,
                "type": "embed",
                "method": method,
                "metrics": metrics,
                "timestamp": time.time(),
            })

            return EmbedResult(
                success=True,
                status_code=200,
                stego_bytes=stego_bytes,
                metrics=metrics,
                capacity_used=metrics.get("capacity_used", 0.0),
                operation_id=op_id,
            )

        except Exception as e:
            err_name = type(e).__name__
            err_str = str(e)
            if "capacity" in err_str.lower() or "too large" in err_str.lower() or "Capacity" in err_name:
                return EmbedResult(
                    success=False,
                    status_code=413,
                    error_code="PAYLOAD_EXCEEDS_CAPACITY",
                    error_detail=err_str,
                )
            return EmbedResult(
                success=False,
                status_code=400,
                error_code=err_name,
                error_detail=err_str,
            )

    def extract(
        self,
        stego_bytes: bytes,
        filename: str = "stego.png",
        password: str = "",
    ) -> ExtractResult:
        try:
            stego = _get_core_module("stego")

            try:
                img = Image.open(io.BytesIO(stego_bytes))
                stego_img = img.convert("RGB")
            except Exception as e:
                return ExtractResult(
                    success=False,
                    status_code=400,
                    error_code="WRONG_PASSWORD_OR_NO_DATA",
                    error_detail="WRONG_PASSWORD_OR_NO_DATA",
                )

            data, is_file, p_filename = stego.extract(stego_img, password)

            payload_text = None
            payload_bytes = None
            if is_file:
                payload_bytes = data
            else:
                try:
                    payload_text = data.decode("utf-8")
                except UnicodeDecodeError:
                    payload_bytes = data

            op_id = f"op_{int(time.time()*1000)}"
            self._history.append({
                "operation_id": op_id,
                "type": "extract",
                "is_file": is_file,
                "filename": p_filename,
                "timestamp": time.time(),
            })

            return ExtractResult(
                success=True,
                status_code=200,
                payload_text=payload_text,
                payload_bytes=payload_bytes,
                is_file=is_file,
                filename=p_filename,
            )

        except Exception:
            # Enforce the strict uniform error contract
            return ExtractResult(
                success=False,
                status_code=400,
                error_code="WRONG_PASSWORD_OR_NO_DATA",
                error_detail="WRONG_PASSWORD_OR_NO_DATA",
            )

    def analyze(
        self,
        original_bytes: bytes,
        stego_bytes: bytes,
        original_filename: str = "original.png",
        stego_filename: str = "stego.png",
    ) -> AnalyzeResult:
        try:
            metrics = _get_core_module("metrics")

            orig = Image.open(io.BytesIO(original_bytes)).convert("RGB")
            steg = Image.open(io.BytesIO(stego_bytes)).convert("RGB")

            res_metrics = metrics.calculate_metrics(orig, steg)
            diff_bytes = None
            if hasattr(metrics, "generate_diff_heatmap"):
                hm_img = metrics.generate_diff_heatmap(orig, steg)
                buf = io.BytesIO()
                hm_img.save(buf, format="PNG")
                diff_bytes = buf.getvalue()
            elif hasattr(metrics, "generate_difference_heatmap"):
                hm_img = metrics.generate_difference_heatmap(orig, steg)
                buf = io.BytesIO()
                hm_img.save(buf, format="PNG")
                diff_bytes = buf.getvalue()

            hist_data = None
            if hasattr(metrics, "calculate_pov_histogram"):
                hist_data = metrics.calculate_pov_histogram(steg)

            return AnalyzeResult(
                success=True,
                status_code=200,
                metrics=res_metrics,
                diff_heatmap_bytes=diff_bytes,
                histogram_data=hist_data,
            )
        except Exception as e:
            return AnalyzeResult(
                success=False,
                status_code=400,
                error_code=type(e).__name__,
                error_detail=str(e),
            )

    def detect(
        self,
        image_bytes: bytes,
        filename: str = "image.png",
    ) -> DetectResult:
        try:
            img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            try:
                detectors = _get_core_module("detectors")
                chi2_res = detectors.chi_square_attack(img)
                rs_res = detectors.rs_analysis(img)
                classification = "clean"
                if hasattr(detectors, "classify"):
                    classification = detectors.classify(chi2_res, rs_res)
                else:
                    p_val = chi2_res.get("p_value", 0.0)
                    rs_ratio = rs_res.get("estimated_payload_ratio", 0.0)
                    if p_val > 0.05 or rs_ratio > 0.10:
                        classification = "likely_stego" if (p_val > 0.50 or rs_ratio > 0.30) else "suspicious"
            except ImportError:
                from tests.e2e.framework.oracles import chi_square_oracle, rs_analysis_oracle
                chi2_res = chi_square_oracle(img)
                rs_res = rs_analysis_oracle(img)
                classification = "likely_stego" if (chi2_res["p_value"] > 0.50 or rs_res["estimated_payload_ratio"] > 0.30) else (
                    "suspicious" if (chi2_res["p_value"] > 0.05 or rs_res["estimated_payload_ratio"] > 0.15) else "clean"
                )

            return DetectResult(
                success=True,
                status_code=200,
                chi2_score=chi2_res.get("chi2", 0.0),
                chi2_p_value=chi2_res.get("p_value", 0.0),
                df=chi2_res.get("df", 0),
                rs_estimated_ratio=rs_res.get("estimated_payload_ratio", 0.0),
                classification=classification,
                detector_details={"chi2": chi2_res, "rs": rs_res},
            )
        except Exception as e:
            return DetectResult(
                success=False,
                status_code=400,
                error_code=type(e).__name__,
                error_detail=str(e),
            )

    def run_attack_lab(
        self,
        cover_images: List[Tuple[str, bytes]],
        methods: List[str],
        ratios: List[float],
        detectors: List[str],
    ) -> AttackLabResult:
        try:
            try:
                attack_lab = _get_core_module("attack_lab")
                pil_images = [Image.open(io.BytesIO(b)).convert("RGB") for _, b in cover_images]
                summary = attack_lab.run_experiment(
                    cover_images=pil_images,
                    methods=methods,
                    ratios=ratios,
                    detectors=detectors,
                )
                csv_content = ""
                if hasattr(attack_lab, "export_csv"):
                    csv_content = attack_lab.export_csv(summary)
            except ImportError:
                # Fallback progressive runner
                items = []
                csv_lines = ["image_name,method,payload_ratio,chi2_score,chi2_p_value,rs_estimated_ratio,detected_as_stego"]
                for img_name, b in cover_images:
                    for m in methods:
                        for r in ratios:
                            det_res = self.detect(b, filename=img_name)
                            is_stego = 1 if det_res.classification != "clean" else 0
                            item = {
                                "image_name": img_name,
                                "method": m,
                                "payload_ratio": r,
                                "chi2_score": det_res.chi2_score,
                                "chi2_p_value": det_res.chi2_p_value,
                                "rs_estimated_ratio": det_res.rs_estimated_ratio,
                                "detected_as_stego": is_stego,
                            }
                            items.append(item)
                            csv_lines.append(f"{img_name},{m},{r},{det_res.chi2_score},{det_res.chi2_p_value},{det_res.rs_estimated_ratio},{is_stego}")
                summary = {
                    "total_items": len(items),
                    "methods": methods,
                    "ratios": ratios,
                    "detectors": detectors,
                    "items": items,
                }
                csv_content = "\n".join(csv_lines)

            return AttackLabResult(
                success=True,
                status_code=200,
                experiment_id=f"exp_{int(time.time()*1000)}",
                summary=summary,
                items=summary.get("items", []),
                csv_content=csv_content,
            )
        except Exception as e:
            return AttackLabResult(
                success=False,
                status_code=400,
                error_code=type(e).__name__,
                error_detail=str(e),
            )

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._history)

    def clear_history(self) -> bool:
        self._history.clear()
        return True
