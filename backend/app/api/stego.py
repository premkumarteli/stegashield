"""Steganography and steganalysis API router."""

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_session_id
from app.schemas.stego import (
    AnalyzeResponse,
    DetectResponse,
    EmbedResponse,
    ExtractResponse,
)
from app.services.analyze_service import analyze_service
from app.services.embed_service import embed_service
from app.services.extract_service import extract_service

router = APIRouter(prefix="/stego", tags=["Steganography"])


@router.post("/embed", response_model=EmbedResponse)
async def embed_steganography(
    cover_file: Annotated[UploadFile, File(...)],
    password: Annotated[str, Form(...)],
    payload_type: Annotated[str, Form()] = "text",
    payload_text: Annotated[str | None, Form()] = None,
    payload_file: Annotated[UploadFile | None, File()] = None,
    method: Annotated[str, Form()] = "lsb_replacement",
    session_id: str = Depends(get_session_id),
    db: Session = Depends(get_db),
) -> EmbedResponse:
    """Embed payload (text or file) into cover image using authenticated encryption & LSB embedding."""
    cover_bytes = await cover_file.read()
    cover_filename = cover_file.filename or "cover.png"

    payload_filename: str | None = None
    p_bytes: bytes | None = None
    if payload_file is not None:
        payload_filename = payload_file.filename
        p_bytes = await payload_file.read()

    return embed_service.embed_payload(
        db=db,
        session_id=session_id,
        cover_filename=cover_filename,
        cover_bytes=cover_bytes,
        password=password,
        method=method,
        payload_type=payload_type,
        payload_text=payload_text,
        payload_filename=payload_filename,
        payload_bytes=p_bytes,
    )


@router.post("/extract", response_model=ExtractResponse)
async def extract_steganography(
    stego_file: Annotated[UploadFile, File(...)],
    password: Annotated[str, Form(...)],
    session_id: str = Depends(get_session_id),
    db: Session = Depends(get_db),
) -> ExtractResponse:
    """Extract and decrypt payload from stego image with uniform error suppression."""
    stego_bytes = await stego_file.read()
    stego_filename = stego_file.filename or "stego.png"

    return extract_service.extract_payload(
        db=db,
        session_id=session_id,
        stego_filename=stego_filename,
        stego_bytes=stego_bytes,
        password=password,
    )


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_comparison(
    cover_file: Annotated[UploadFile, File(...)],
    stego_file: Annotated[UploadFile, File(...)],
    session_id: str = Depends(get_session_id),
    db: Session = Depends(get_db),
) -> AnalyzeResponse:
    """Compare cover and stego images, generating MSE, PSNR, SSIM, heatmap, bitplane, and PoV histogram."""
    cover_bytes = await cover_file.read()
    stego_bytes = await stego_file.read()

    return analyze_service.compare_images(
        db=db,
        session_id=session_id,
        cover_filename=cover_file.filename or "cover.png",
        cover_bytes=cover_bytes,
        stego_filename=stego_file.filename or "stego.png",
        stego_bytes=stego_bytes,
    )


@router.post("/detect", response_model=DetectResponse)
async def detect_stego(
    image_file: Annotated[UploadFile, File(...)],
    session_id: str = Depends(get_session_id),
    db: Session = Depends(get_db),
) -> DetectResponse:
    """Run Chi-Square attack and RS Analysis statistical steganalysis on candidate image."""
    image_bytes = await image_file.read()

    return analyze_service.detect_steganography(
        db=db,
        session_id=session_id,
        image_filename=image_file.filename or "candidate.png",
        image_bytes=image_bytes,
    )
