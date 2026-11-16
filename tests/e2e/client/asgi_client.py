"""
StegaShield E2E Test Client - In-Memory ASGI TestClient Adapter.
Executes HTTP requests directly against FastAPI app without requiring a network socket.
"""

from __future__ import annotations

import base64
from typing import Any, Dict, List, Optional, Tuple
from starlette.testclient import TestClient

from tests.e2e.client.base import (
    AnalyzeResult,
    AttackLabResult,
    DetectResult,
    EmbedResult,
    ExtractResult,
    StegaShieldClient,
)


class AsgiClient(StegaShieldClient):
    """In-memory ASGI client wrapping the FastAPI application."""

    def __init__(self, app: Optional[Any] = None):
        if app is None:
            from backend.app.main import app as fastapi_app
            self.app = fastapi_app
        else:
            self.app = app
        self._client = TestClient(self.app, base_url="http://testserver", cookies={})

    @property
    def mode(self) -> str:
        return "asgi_testclient"

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
            resp = self._client.post("/api/v1/stego/embed", data=data, files=files)
            if resp.status_code == 200:
                body = resp.json()
                stego_bytes = None
                if "download_url" in body:
                    img_resp = self._client.get(body["download_url"])
                    if img_resp.status_code == 200:
                        stego_bytes = img_resp.content
                elif "stego_image_base64" in body:
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
                error_code="ASGI_ERROR",
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
            resp = self._client.post("/api/v1/stego/extract", data=data, files=files)
            if resp.status_code == 200:
                body = resp.json()
                payload_text = body.get("payload_text")
                is_file = body.get("is_file", False)
                p_filename = body.get("filename")
                payload_bytes = None
                if is_file and "download_url" in body:
                    dl_resp = self._client.get(body["download_url"])
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
                error_code="ASGI_ERROR",
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
            resp = self._client.post("/api/v1/stego/analyze", files=files)
            if resp.status_code == 200:
                body = resp.json()
                diff_bytes = None
                if "diff_heatmap_url" in body:
                    hm_resp = self._client.get(body["diff_heatmap_url"])
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
                error_code="ASGI_ERROR",
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
            resp = self._client.post("/api/v1/stego/detect", files=files)
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
                error_code="ASGI_ERROR",
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
            resp = self._client.post("/api/v1/attack-lab/run", json=payload)
            if resp.status_code in (200, 202):
                body = resp.json()
                exp_id = body.get("experiment_id")
                summary = body.get("summary", {})
                csv_content = None
                if exp_id:
                    csv_resp = self._client.get(f"/api/v1/attack-lab/experiments/{exp_id}/export")
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
                error_code="ASGI_ERROR",
                error_detail=str(e),
            )

    def get_history(self) -> List[Dict[str, Any]]:
        try:
            resp = self._client.get("/api/v1/history")
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
            resp = self._client.delete("/api/v1/history")
            return resp.status_code in (200, 204)
        except Exception:
            return False
