"""Tests for session-scoped history API."""

from fastapi.testclient import TestClient


def test_history_session_scoping_and_clearing(client: TestClient, cover_image_bytes: bytes) -> None:
    # 1. Initially empty
    res0 = client.get("/api/v1/history")
    assert res0.status_code == 200
    assert len(res0.json()["operations"]) == 0

    # 2. Perform an embed operation
    client.post(
        "/api/v1/stego/embed",
        data={
            "password": "Password123!",
            "payload_type": "text",
            "payload_text": "History check",
        },
        files={"cover_file": ("cover.png", cover_image_bytes, "image/png")},
    )

    # 3. Check history contains 1 operation
    res1 = client.get("/api/v1/history")
    assert res1.status_code == 200
    ops = res1.json()["operations"]
    assert len(ops) == 1
    assert ops[0]["operation_type"] == "embed"
    assert ops[0]["cover_filename"] == "cover.png"

    # 4. Another client with a different session cookie sees empty history
    with TestClient(client.app) as other_client:
        other_client.cookies.set("stegashield_session", "different-session-uuid-999")
        other_res = other_client.get("/api/v1/history")
        assert other_res.status_code == 200
        assert len(other_res.json()["operations"]) == 0

    # 5. Clear history on first client
    del_res = client.delete("/api/v1/history")
    assert del_res.status_code == 200
    assert del_res.json()["cleared"] is True
    assert del_res.json()["deleted_count"] == 1

    # 6. Verify now empty
    res2 = client.get("/api/v1/history")
    assert res2.status_code == 200
    assert len(res2.json()["operations"]) == 0
