"""
StegaShield E2E Test Client - Live HTTP Network Client.
Exercises StegaShield as a complete black-box over network HTTP REST endpoints.
"""

from __future__ import annotations

import io
from typing import Any, Dict, List, Optional, Tuple
import httpx

from tests.e2e.client.base import (
    AnalyzeResult,
    AttackLabResult,
    DetectResult,
    EmbedResult,
    ExtractResult,
    StegaShieldClient,
)


class LiveHttpClient(StegaShieldClient):
    """Full black-box network client using httpx.Client."""

    def __init__(self, base_url: str = "http://127.0.0.1:8000", timeout: float = 60.0):
        self.base_url = base_url.rstrip("/")
        self._session = httpx.Client(base_url=self.base_url, timeout=timeout, follow_redirects=True)

    @property
    def mode(self) -> str:
        return "live_http"

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
        files = {
            "cover": (filename, cover_bytes, "image/png"),
        }
        data: Dict[str, Any] = {
            "password": password,
            "method": method,
        }
        if payload_text is not None:
            data["payload_text"] = payload_text
        if payload_file_bytes is not None:
            p_name = payload_filename or "payload.bin"
            files["payload_file"] = (p_name, payload_file_bytes, "application/octet-stream")

        try:
            resp = self._session.post("/api/v1/stego/embed", data=data, files=files)
            if resp.status_code == 200:
                body = resp.json()
                stego_bytes = None
                # Check if response directly contains binary image or a download URL
                if "download_url" in body:
                    img_resp = self._session.get(body["download_url"])
                    if img_resp.status_code == 200:
                        stego_bytes = img_resp.content
                elif "stego_image_base64" in body:
                    import base64
                    stego_bytes = base64.b64decode(body["stego_image_base64"])

                return EmbedResult(
                    success=True,
                    status_code=resp.status_code,
                    stego_bytes=stego_bytes,
                    metrics=body.get("metrics", {}),
                    capacity_used=body.get("capacity_used"),
                    operation_id=body.get("operation_id"),
                )
            else:
                err_detail = None
                err_code = None
                try:
                    err_json = resp.json()
                    err_detail = err_json.get("detail", str(err_json))
                    err_code = err_json.get("code", err_detail)
                except Exception:
                    err_detail = resp.text
                    err_code = f"HTTP_{resp.status_code}"
                return EmbedResult(
                    success=False,
                    status_code=resp.status_code,
                    error_code=str(err_code),
                    error_detail=str(err_detail),
                )
        except Exception as e:
            return EmbedResult(
                success=False,
                status_code=0,
                error_code="CONNECTION_ERROR",
                error_detail=str(e),
            )

    def extract(
        self,
        stego_bytes: bytes,
        filename: str = "stego.png",
        password: str = "",
    ) -> ExtractResult:
        files = {
            "stego_image": (filename, stego_bytes, "image/png"),
        }
        data = {
            "password": password,
        }
        try:
            resp = self._session.post("/api/v1/stego/extract", data=data, files=files)
            if resp.status_code == 200:
                body = resp.json()
                payload_text = body.get("payload_text")
                is_file = body.get("is_file", False)
                p_filename = body.get("filename")
                payload_bytes = None
                if is_file and "download_url" in body:
                    dl_resp = self._session.get(body["download_url"])
                    if dl_resp.status_code == 200:
                        payload_bytes = dl_resp.content
                return ExtractResult(
                    success=True,
                    status_code=resp.status_code,
                    payload_text=payload_text,
                    payload_bytes=payload_bytes,
                    is_file=is_file,
                    filename=p_filename,
                )
            else:
                err_detail = None
                err_code = None
                try:
                    err_json = resp.json()
                    err_detail = err_json.get("detail", str(err_json))
                    err_code = err_json.get("code", err_detail)
                except Exception:
                    err_detail = resp.text
                    err_code = f"HTTP_{resp.status_code}"
                return ExtractResult(
                    success=False,
                    status_code=resp.status_code,
                    error_code=str(err_code),
                    error_detail=str(err_detail),
                )
        except Exception as e:
            return ExtractResult(
                success=False,
                status_code=0,
                error_code="CONNECTION_ERROR",
                error_detail=str(e),
            )

    def analyze(
        self,
        original_bytes: bytes,
        stego_bytes: bytes,
        original_filename: str = "original.png",
        stego_filename: str = "stego.png",
    ) -> AnalyzeResult:
        files = {
            "original_image": (original_filename, original_bytes, "image/png"),
            "stego_image": (stego_filename, stego_bytes, "image/png"),
        }
        try:
            resp = self._session.post("/api/v1/stego/analyze", files=files)
            if resp.status_code == 200:
                body = resp.json()
                diff_bytes = None
                if "diff_heatmap_url" in body:
                    hm_resp = self._session.get(body["diff_heatmap_url"])
                    if hm_resp.status_code == 200:
                        diff_bytes = hm_resp.content
                return AnalyzeResult(
                    success=True,
                    status_code=resp.status_code,
                    metrics=body.get("metrics", {}),
                    diff_heatmap_bytes=diff_bytes,
                    histogram_data=body.get("histogram_data"),
                )
            else:
                return AnalyzeResult(
                    success=False,
                    status_code=resp.status_code,
                    error_code=f"HTTP_{resp.status_code}",
                    error_detail=resp.text,
                )
        except Exception as e:
            return AnalyzeResult(
                success=False,
                status_code=0,
                error_code="CONNECTION_ERROR",
                error_detail=str(e),
            )

    def detect(
        self,
        image_bytes: bytes,
        filename: str = "image.png",
    ) -> DetectResult:
        files = {
            "image": (filename, image_bytes, "image/png"),
        }
        try:
            resp = self._session.post("/api/v1/stego/detect", files=files)
            if resp.status_code == 200:
                body = resp.json()
                return DetectResult(
                    success=True,
                    status_code=resp.status_code,
                    chi2_score=float(body.get("chi2_score", body.get("chi2", 0.0))),
                    chi2_p_value=float(body.get("chi2_p_value", body.get("p_value", 0.0))),
                    df=int(body.get("df", 0)),
                    rs_estimated_ratio=float(body.get("rs_estimated_ratio", body.get("estimated_payload_ratio", 0.0))),
                    classification=body.get("classification", "clean"),
                    detector_details=body.get("details", body),
                )
            else:
                return DetectResult(
                    success=False,
                    status_code=resp.status_code,
                    error_code=f"HTTP_{resp.status_code}",
                    error_detail=resp.text,
                )
        except Exception as e:
            return DetectResult(
                success=False,
                status_code=0,
                error_code="CONNECTION_ERROR",
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
            payload: Dict[str, Any] = {
                "methods": methods,
                "ratios": ratios,
                "detectors": detectors,
                "image_names": [name for name, _ in cover_images],
            }
            resp = self._session.post("/api/v1/attack-lab/run", json=payload)
            if resp.status_code in (200, 202):
                body = resp.json()
                exp_id = body.get("experiment_id")
                # Wait for or poll completion if needed, or fetch report
                summary = body.get("summary", {})
                csv_content = None
                if exp_id:
                    csv_resp = self._session.get(f"/api/v1/attack-lab/experiments/{exp_id}/export")
                    if csv_resp.status_code == 200:
                        csv_content = csv_resp.text
                return AttackLabResult(
                    success=True,
                    status_code=resp.status_code,
                    experiment_id=exp_id,
                    summary=summary,
                    csv_content=csv_content,
                )
            else:
                return AttackLabResult(
                    success=False,
                    status_code=resp.status_code,
                    error_code=f"HTTP_{resp.status_code}",
                    error_detail=resp.text,
                )
        except Exception as e:
            return AttackLabResult(
                success=False,
                status_code=0,
                error_code="CONNECTION_ERROR",
                error_detail=str(e),
            )

    def get_history(self) -> List[Dict[str, Any]]:
        try:
            resp = self._session.get("/api/v1/history")
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list):
                    return data
                return data.get("operations", [])
            return []
        except Exception:
            return []

    def clear_history(self) -> bool:
        try:
            resp = self._session.delete("/api/v1/history")
            return resp.status_code in (200, 204)
        except Exception:
            return False

    def close(self):
        self._session.close()
