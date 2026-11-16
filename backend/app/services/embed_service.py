"""Service handling steganographic embedding, distortion metric calculation, and persistence."""

import io
import math
from pathlib import Path

from fastapi import HTTPException, status
from PIL import Image, UnidentifiedImageError
from sqlalchemy.orm import Session

from app.core.stego import (
    METHOD_LSB_REPLACEMENT,
    SUPPORTED_METHODS,
    calculate_capacity,
    embed,
    validate_cover_image,
)
from app.db.repositories import OperationRepository
from app.schemas.stego import DistortionMetrics, EmbedResponse
from app.services.file_store import file_store


class EmbedService:
    """Coordinates cover validation, cryptographic/steganographic embedding, and persistence."""

    def embed_payload(
        self,
        db: Session,
        session_id: str,
        cover_filename: str,
        cover_bytes: bytes,
        password: str,
        method: str = METHOD_LSB_REPLACEMENT,
        payload_type: str = "text",
        payload_text: str | None = None,
        payload_filename: str | None = None,
        payload_bytes: bytes | None = None,
    ) -> EmbedResponse:
        """Embed text or file payload into cover image."""
        if not password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password cannot be empty.",
            )

        if method not in SUPPORTED_METHODS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported method '{method}'. Supported methods: {', '.join(SUPPORTED_METHODS)}.",
            )

        # 1. Parse and validate payload
        final_payload: bytes
        is_file = False
        target_payload_filename = ""

        if payload_type == "text":
            if not payload_text:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="payload_text is required when payload_type is 'text'.",
                )
            final_payload = payload_text.encode("utf-8")
        elif payload_type == "file":
            if not payload_bytes:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="payload_file content is required when payload_type is 'file'.",
                )
            final_payload = payload_bytes
            is_file = True
            target_payload_filename = Path(payload_filename or "payload.bin").name
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported payload_type '{payload_type}'. Must be 'text' or 'file'.",
            )

        # 2. Decode and validate cover image
        try:
            raw_img = Image.open(io.BytesIO(cover_bytes))
            cover_img = validate_cover_image(raw_img)
        except (UnidentifiedImageError, ValueError, OSError) as err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid cover image: {err}",
            ) from err

        # 3. Capacity verification
        capacity = calculate_capacity(cover_img)
        # Check against payload bits (rough pre-check)
        if len(final_payload) > capacity["usable_bytes"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Payload size ({len(final_payload)} bytes) exceeds cover usable capacity "
                    f"({capacity['usable_bytes']} bytes)."
                ),
            )

        # 4. Perform steganographic embedding
        try:
            stego_img, metrics_data = embed(
                cover_image=cover_img,
                payload=final_payload,
                password=password,
                method=method,
                is_file=is_file,
                filename=target_payload_filename,
            )
        except ValueError as err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(err),
            ) from err

        # 5. Persist stego image to file store
        safe_cover_stem = Path(cover_filename).stem or "image"
        stego_filename = f"stego_{safe_cover_stem}.png"
        saved_file = file_store.save_image(
            db=db,
            session_id=session_id,
            filename=stego_filename,
            image=stego_img,
            format_type="PNG",
        )

        # 6. Record operation in database (NEVER store password or secret data)
        mse_val = float(metrics_data.get("mse", 0.0))
        psnr_val = float(metrics_data.get("psnr", 0.0))
        if math.isinf(psnr_val) or math.isnan(psnr_val):
            psnr_val = 100.0
        ssim_val = float(metrics_data.get("ssim", 0.0))

        op = OperationRepository.create(
            db=db,
            session_id=session_id,
            operation_type="embed",
            cover_filename=Path(cover_filename).name,
            stego_filename=stego_filename,
            payload_type=payload_type,
            method=method,
            mse=mse_val,
            psnr=psnr_val,
            ssim=ssim_val,
        )

        return EmbedResponse(
            operation_id=op.id,
            download_url=f"/api/v1/files/{saved_file.id}",
            filename=stego_filename,
            metrics=DistortionMetrics(
                mse=mse_val,
                psnr=psnr_val,
                ssim=ssim_val,
            ),
            capacity_stats={
                "capacity_total_bits": metrics_data.get("capacity_total_bits"),
                "payload_bits": metrics_data.get("payload_bits"),
                "capacity_used_ratio": metrics_data.get("capacity_used_ratio"),
            },
        )


embed_service = EmbedService()
