"""Tests for temporary file storage and 30-minute TTL expiration."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from fastapi.testclient import TestClient

from app.db.repositories import TempFileRepository
from app.services.file_store import file_store
from tests.api.conftest import TestingSessionLocal


def test_file_download_and_ttl_expiration(client: TestClient) -> None:
    # 1. Nonexistent file returns 404
    res_404 = client.get("/api/v1/files/nonexistent-uuid-000")
    assert res_404.status_code == 404

    # 2. Save a test file via file_store
    with TestingSessionLocal() as db:
        tf = file_store.save_bytes(
            db=db,
            session_id="test-session-123",
            filename="document.txt",
            content=b"Hello StegaShield temporary file store!",
            content_type="text/plain",
        )
        file_id = tf.id

    # 3. Download active file
    dl_res = client.get(f"/api/v1/files/{file_id}")
    assert dl_res.status_code == 200
    assert dl_res.content == b"Hello StegaShield temporary file store!"
    assert "text/plain" in dl_res.headers.get("Content-Type", "")

    # 4. Simulate expiration by manually rewinding expires_at in DB
    with TestingSessionLocal() as db:
        record = TempFileRepository.get_by_id(db, file_id)
        assert record is not None
        record.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        db.commit()

    # 5. Attempting to download expired file returns 404
    exp_res = client.get(f"/api/v1/files/{file_id}")
    assert exp_res.status_code == 404


def test_file_store_periodic_cleanup() -> None:
    with TestingSessionLocal() as db:
        # Create expired file
        tf = file_store.save_bytes(
            db=db,
            session_id="sess-cleanup",
            filename="old.txt",
            content=b"Expired bytes",
        )
        tf.expires_at = datetime.now(timezone.utc) - timedelta(minutes=5)
        db.commit()
        old_id = tf.id
        old_path = Path(tf.file_path)
        assert old_path.exists()

        # Run cleanup
        cleaned_count = file_store.cleanup_expired_files(db)
        assert cleaned_count >= 1
        assert not old_path.exists()
        assert TempFileRepository.get_by_id(db, old_id) is None
