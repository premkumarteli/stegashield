"""Tests for Attack Lab matrix experimentation API, mutex locking, and CSV exports."""

import time
from fastapi.testclient import TestClient

from app.db.repositories import ExperimentRepository
from app.services.experiment_service import experiment_service
from tests.api.conftest import TestingSessionLocal


def test_attack_lab_run_and_export_lifecycle(client: TestClient) -> None:
    # 1. Start a small experiment
    res = client.post(
        "/api/v1/attack-lab/run",
        json={
            "methods": ["lsb_replacement"],
            "ratios": [0.1],
            "detectors": ["chi_square"],
        },
    )
    assert res.status_code == 200
    data = res.json()
    exp_id = data["experiment_id"]
    assert data["status"] == "running"

    # Wait for background execution to complete
    for _ in range(50):
        time.sleep(0.2)
        with TestingSessionLocal() as db:
            exp = ExperimentRepository.get_by_id(db, exp_id)
            if exp and exp.status in ("completed", "failed"):
                break

    # 2. Check SSE progress endpoint (should report completed or events)
    with client.stream("GET", f"/api/v1/attack-lab/progress/{exp_id}") as stream:
        lines = []
        for line in stream.iter_lines():
            if line:
                lines.append(line)
            if len(lines) >= 2:
                break
        assert any("progress" in line_item or "data" in line_item for line_item in lines)

    # 3. Check CSV Export
    csv_res = client.get(f"/api/v1/attack-lab/export/{exp_id}")
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers.get("Content-Type", "")
    csv_content = csv_res.text
    assert "image_name,method,payload_ratio,chi2_score,chi2_p_value,rs_estimated_ratio,detected_as_stego" in csv_content
    assert "lsb_replacement" in csv_content


def test_attack_lab_mutex_409_conflict(client: TestClient) -> None:
    # Manually acquire the lock to simulate an active running experiment
    experiment_service._active_experiment_id = "test-active-id"

    try:
        conflict_res = client.post(
            "/api/v1/attack-lab/run",
            json={
                "methods": ["lsb_replacement"],
                "ratios": [0.05],
                "detectors": ["chi_square"],
            },
        )
        assert conflict_res.status_code == 409
        assert "already in progress" in conflict_res.json()["detail"]
    finally:
        experiment_service._active_experiment_id = None


def test_export_nonexistent_experiment_404(client: TestClient) -> None:
    res = client.get("/api/v1/attack-lab/export/nonexistent-uuid-1234")
    assert res.status_code == 404
