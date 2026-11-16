"""Tests for Health, Root, and Middleware Security Headers."""

from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient) -> None:
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "StegaShield API"
    assert data["version"] == "1.0.0"


def test_health_endpoint(client: TestClient) -> None:
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["version"] == "1.0.0"
    assert data["database"] == "connected"


def test_security_headers_and_session_cookie(client: TestClient) -> None:
    res = client.get("/api/v1/health")
    assert res.status_code == 200

    # Security headers
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "DENY"
    assert "default-src 'self'" in res.headers.get("Content-Security-Policy", "")

    # Session cookie set on initial request
    assert "stegashield_session" in res.cookies
