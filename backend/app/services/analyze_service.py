"""Service providing image quality comparison metrics, visualizers, and steganalysis detection."""

import io
import json
import math
from pathlib import Path

from fastapi import HTTPException, status
from PIL import Image, UnidentifiedImageError
from sqlalchemy.orm import Session

from app.core.detect import chi_square_attack, classify, rs_analysis
from app.core.metrics import (
    calculate_metrics,
    calculate_pov_histogram,
    generate_bitplane,
    generate_diff_heatmap,
)
from app.core.stego import validate_cover_image
from app.db.repositories import DetectionRepository, OperationRepository
from app.schemas.stego import AnalyzeResponse, DetectResponse
from app.services.file_store import file_store


class AnalyzeService:
    """Coordinates distortion comparison and statistical steganalysis detection."""

    def compare_images(
        self,
        db: Session,
        session_id: str,
        cover_filename: str,
        cover_bytes: bytes,
        stego_filename: str,
        stego_bytes: bytes,
    ) -> AnalyzeResponse:
        """Calculate distortion metrics, difference heatmap, bitplane slice, and PoV histogram."""
        try:
            c_raw = Image.open(io.BytesIO(cover_bytes))
            cover_img = validate_cover_image(c_raw)
        except (UnidentifiedImageError, ValueError, OSError) as err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid cover image: {err}",
            ) from err

        try:
            s_raw = Image.open(io.BytesIO(stego_bytes))
            stego_img = validate_cover_image(s_raw)
        except (UnidentifiedImageError, ValueError, OSError) as err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid stego image: {err}",
            ) from err

        if cover_img.size != stego_img.size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Image dimensions do not match: cover={cover_img.size}, stego={stego_img.size}",
            )

        # 1. Distortion metrics
        metrics_dict = calculate_metrics(cover_img, stego_img)
        mse_val = float(metrics_dict["mse"])
        psnr_val = float(metrics_dict["psnr"])
        if math.isinf(psnr_val) or math.isnan(psnr_val):
            psnr_val = 100.0
        ssim_val = float(metrics_dict["ssim"])

        # 2. Difference heatmap
        heatmap_img = generate_diff_heatmap(cover_img, stego_img)
        safe_stego_stem = Path(stego_filename).stem or "stego"
        heatmap_file = file_store.save_image(
            db=db,
            session_id=session_id,
            filename=f"heatmap_{safe_stego_stem}.png",
            image=heatmap_img,
            format_type="PNG",
        )

        # 3. Bitplane visualizer
        bitplane_img = generate_bitplane(stego_img, channel="combined")
        bitplane_file = file_store.save_image(
            db=db,
            session_id=session_id,
            filename=f"bitplane_{safe_stego_stem}.png",
            image=bitplane_img,
            format_type="PNG",
        )

        # 4. PoV histogram
        pov_dict = calculate_pov_histogram(stego_img, channel="all")

        # 5. Record operation
        op = OperationRepository.create(
            db=db,
            session_id=session_id,
            operation_type="analyze",
            cover_filename=Path(cover_filename).name,
            stego_filename=Path(stego_filename).name,
            mse=mse_val,
            psnr=psnr_val,
            ssim=ssim_val,
        )

        return AnalyzeResponse(
            operation_id=op.id,
            mse=mse_val,
            psnr=psnr_val,
            ssim=ssim_val,
            heatmap_url=f"/api/v1/files/{heatmap_file.id}",
            bitplane_url=f"/api/v1/files/{bitplane_file.id}",
            pov_histogram=pov_dict,
        )

    def detect_steganography(
        self,
        db: Session,
        session_id: str,
        image_filename: str,
        image_bytes: bytes,
    ) -> DetectResponse:
        """Run Chi-Square and RS Analysis statistical steganalysis against candidate image."""
        try:
            raw_img = Image.open(io.BytesIO(image_bytes))
            img = validate_cover_image(raw_img)
        except (UnidentifiedImageError, ValueError, OSError) as err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid candidate image: {err}",
            ) from err

        chi2_res = chi_square_attack(img, channel="all")
        rs_res = rs_analysis(img)
        verdict = classify(chi2_res, rs_res)

        # Record operation
        op = OperationRepository.create(
            db=db,
            session_id=session_id,
            operation_type="detect",
            cover_filename=Path(image_filename).name,
        )

        # Record detection details
        details_str = json.dumps({"chi_square": chi2_res, "rs_analysis": rs_res})
        DetectionRepository.create(
            db=db,
            session_id=session_id,
            chi2_stat=float(chi2_res.get("chi2", 0.0)),
            p_value=float(chi2_res.get("p_value", 0.0)),
            rs_payload_ratio=float(rs_res.get("estimated_payload_ratio", 0.0)),
            classification=verdict,
            details_json=details_str,
            operation_id=op.id,
        )

        return DetectResponse(
            operation_id=op.id,
            chi_square=chi2_res,
            rs_analysis=rs_res,
            classification=verdict,
        )


analyze_service = AnalyzeService()
