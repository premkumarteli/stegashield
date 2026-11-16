"""Temporary file delivery API router with TTL validation."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services.file_store import file_store

router = APIRouter(prefix="/files", tags=["Files"])


@router.get("/{file_id}")
def download_temp_file(
    file_id: str,
    db: Session = Depends(get_db),
) -> FileResponse:
    """Download temporary artifact with 30-minute expiration check."""
    result = file_store.get_file(db, file_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File '{file_id}' not found or has expired.",
        )

    tf, path = result
    return FileResponse(
        path=str(path),
        media_type=tf.content_type,
        filename=tf.filename,
    )
