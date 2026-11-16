"""Test fixtures for FastAPI API testing."""

from collections.abc import Generator
import io
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from PIL import Image
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.deps import get_db
from app.db.models import Base
import app.db.session as app_session
from app.main import app

TEST_DB_FILE = Path("./test_api_suite.db")
TEST_DB_URL = f"sqlite:///{TEST_DB_FILE}"

test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db() -> Generator[Session, None, None]:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_test_db() -> Generator[None, None, None]:
    """Create all tables in file-backed SQLite before each test and drop them afterwards."""
    orig_session_local = app_session.SessionLocal
    orig_engine = app_session.engine

    app_session.SessionLocal = TestingSessionLocal
    app_session.engine = test_engine

    Base.metadata.create_all(bind=test_engine)
    app.dependency_overrides[get_db] = override_get_db

    yield

    Base.metadata.drop_all(bind=test_engine)
    app.dependency_overrides.clear()
    app_session.SessionLocal = orig_session_local
    app_session.engine = orig_engine

    test_engine.dispose()
    if TEST_DB_FILE.exists():
        try:
            TEST_DB_FILE.unlink()
        except OSError:
            pass


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def cover_image_bytes() -> bytes:
    """Create a 64x64 synthetic PNG image for API tests."""
    arr = np.zeros((64, 64, 3), dtype=np.uint8)
    for y in range(64):
        for x in range(64):
            arr[y, x] = [x * 4, y * 4, (x + y) * 2]
    img = Image.fromarray(arr, mode="RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
