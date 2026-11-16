"""File storage service managing temporary files with 30-minute expiration TTL."""

from datetime import datetime, timedelta, timezone
import io
from pathlib import Path
import uuid

from PIL import Image
from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import TempFile
from app.db.repositories import TempFileRepository


def _ensure_utc(dt: datetime) -> datetime:
    """Ensure datetime is timezone-aware in UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class FileStoreService:
    """Manages temporary files on disk and in database with automatic TTL expiration."""

    def __init__(self) -> None:
        self.storage_dir = settings.resolved_storage_dir

    def save_bytes(
        self,
        db: Session,
        session_id: str,
        filename: str,
        content: bytes,
        content_type: str = "application/octet-stream",
    ) -> TempFile:
        """Persist raw byte payload to disk and track in DB."""
        file_id = str(uuid.uuid4())
        safe_name = Path(filename).name or "file.bin"
        disk_filename = f"{file_id}_{safe_name}"
        target_path = self.storage_dir / disk_filename

        target_path.write_bytes(content)

        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.FILE_TTL_MINUTES)
        tf = TempFileRepository.create(
            db=db,
            session_id=session_id,
            filename=safe_name,
            file_path=str(target_path),
            content_type=content_type,
            size_bytes=len(content),
            expires_at=expires_at,
        )
        return tf

    def save_image(
        self,
        db: Session,
        session_id: str,
        filename: str,
        image: Image.Image,
        format_type: str = "PNG",
    ) -> TempFile:
        """Persist PIL Image as PNG to disk and track in DB."""
        buf = io.BytesIO()
        image.save(buf, format=format_type)
        content = buf.getvalue()
        content_type = "image/png" if format_type.upper() == "PNG" else "image/jpeg"
        return self.save_bytes(
            db=db,
            session_id=session_id,
            filename=filename,
            content=content,
            content_type=content_type,
        )

    def get_file(self, db: Session, file_id: str) -> tuple[TempFile, Path] | None:
        """Retrieve file metadata and verified disk path if not expired."""
        tf = TempFileRepository.get_by_id(db, file_id)
        if tf is None:
            return None

        # Check TTL expiration
        now = datetime.now(timezone.utc)
        if _ensure_utc(tf.expires_at) <= now:
            self.delete_file(db, file_id)
            return None

        path = Path(tf.file_path)
        if not path.is_file():
            TempFileRepository.delete(db, file_id)
            return None

        return tf, path

    def delete_file(self, db: Session, file_id: str) -> bool:
        """Delete file from disk and database."""
        tf = TempFileRepository.get_by_id(db, file_id)
        if tf is None:
            return False

        path = Path(tf.file_path)
        if path.is_file():
            try:
                path.unlink()
            except OSError:
                pass

        return TempFileRepository.delete(db, file_id)

    def cleanup_expired_files(self, db: Session) -> int:
        """Periodic background task: purge files older than TTL."""
        now = datetime.now(timezone.utc)
        expired_files = TempFileRepository.get_expired(db, now)
        count = 0
        for tf in expired_files:
            p = Path(tf.file_path)
            if p.is_file():
                try:
                    p.unlink()
                except OSError:
                    pass
            count += 1
        TempFileRepository.delete_expired(db, now)
        return count


file_store = FileStoreService()
