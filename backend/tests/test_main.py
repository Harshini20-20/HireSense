
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["application"] == "HireSense"


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

from backend.app.api import matching as matching_api


def test_matching_endpoint_success(client, monkeypatch):
    monkeypatch.setattr(
        matching_api,
        "evaluate_job_candidates",
        lambda db, job_id: {
            "job_id": job_id,
            "job_title": "AI Engineer",
            "total_candidates": 1,
            "candidates": [],
        },
    )

    response = client.post("/api/matching/1/evaluate")

    assert response.status_code == 200
    assert response.json()["job_id"] == 1
    assert response.json()["total_candidates"] == 1


def test_matching_endpoint_job_not_found(client, monkeypatch):
    def raise_not_found(db, job_id):
        raise ValueError("Job not found.")

    monkeypatch.setattr(
        matching_api,
        "evaluate_job_candidates",
        raise_not_found,
    )

    response = client.post("/api/matching/999/evaluate")

    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found."


def test_matching_endpoint_handles_internal_error(client, monkeypatch):
    def raise_error(db, job_id):
        raise RuntimeError("Unexpected database error")

    monkeypatch.setattr(
        matching_api,
        "evaluate_job_candidates",
        raise_error,
    )

    response = client.post("/api/matching/1/evaluate")

    assert response.status_code == 500
    assert response.json()["detail"] == "Candidate evaluation failed."
