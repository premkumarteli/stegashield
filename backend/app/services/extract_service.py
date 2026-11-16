"""Service handling steganographic extraction with uniform error suppression."""

import io
from pathlib import Path

from fastapi import HTTPException, status
from PIL import Image, UnidentifiedImageError
from sqlalchemy.orm import Session

from app.core.crypto import StegaShieldError, WRONG_PASSWORD_OR_NO_DATA
from app.core.stego import extract, validate_cover_image
from app.db.repositories import OperationRepository
from app.schemas.stego import ExtractResponse
from app.services.file_store import file_store


class ExtractService:
    """Coordinates stego image decoding, cryptographic extraction, and error suppression."""

    def extract_payload(
        self,
        db: Session,
        session_id: str,
        stego_filename: str,
        stego_bytes: bytes,
        password: str,
    ) -> ExtractResponse:
        """Extract hidden payload from stego image with strict timing/uniform error protection."""
        if not password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=WRONG_PASSWORD_OR_NO_DATA,
            )

        try:
            raw_img = Image.open(io.BytesIO(stego_bytes))
            stego_img = validate_cover_image(raw_img)
        except (UnidentifiedImageError, ValueError, OSError) as err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=WRONG_PASSWORD_OR_NO_DATA,
            ) from err

        try:
            data, is_file, filename = extract(stego_img, password)
        except StegaShieldError as err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=WRONG_PASSWORD_OR_NO_DATA,
            ) from err

        safe_stego_name = Path(stego_filename).name

        if is_file:
            safe_payload_name = Path(filename).name or "extracted.bin"
            saved_file = file_store.save_bytes(
                db=db,
                session_id=session_id,
                filename=safe_payload_name,
                content=data,
            )
            op = OperationRepository.create(
                db=db,
                session_id=session_id,
                operation_type="extract",
                stego_filename=safe_stego_name,
                payload_type="file",
            )
            return ExtractResponse(
                operation_id=op.id,
                payload_type="file",
                filename=safe_payload_name,
                download_url=f"/api/v1/files/{saved_file.id}",
                size_bytes=len(data),
            )
        else:
            payload_text = data.decode("utf-8", errors="replace")
            op = OperationRepository.create(
                db=db,
                session_id=session_id,
                operation_type="extract",
                stego_filename=safe_stego_name,
                payload_type="text",
            )
            return ExtractResponse(
                operation_id=op.id,
                payload_type="text",
                payload_text=payload_text,
                size_bytes=len(data),
            )


extract_service = ExtractService()
