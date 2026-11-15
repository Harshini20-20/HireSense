
import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.main import app
from backend.app.database.base import Base
from backend.app.database.connection import get_db
from backend.app import models


# Create an isolated in-memory test database
@pytest.fixture
def client():
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine
    )

    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


def test_create_job(client):
    response = client.post(
        "/api/jobs/",
        json={
            "title": "Python Developer",
            "description": (
                "Looking for a Python developer with experience "
                "in FastAPI, SQL and REST API development."
            )
        }
    )

    assert response.status_code == 201
    assert response.json()["title"] == "Python Developer"
    assert response.json()["id"] is not None


def test_get_job(client):
    create_response = client.post(
        "/api/jobs/",
        json={
            "title": "Data Scientist",
            "description": (
                "Looking for a data scientist with experience "
                "in Python, machine learning and data analytics."
            )
        }
    )

    job_id = create_response.json()["id"]

    response = client.get(f"/api/jobs/{job_id}")

    assert response.status_code == 200
    assert response.json()["title"] == "Data Scientist"


def test_job_not_found(client):
    response = client.get("/api/jobs/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"


def test_invalid_job_input(client):
    response = client.post(
        "/api/jobs/",
        json={
            "title": "A",
            "description": "Short"
        }
    )

    assert response.status_code == 422
