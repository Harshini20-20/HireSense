
import io

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from docx import Document

from backend.app.main import app
from backend.app.database.base import Base
from backend.app.database.connection import get_db
from backend.app import models
from backend.app.models.candidate import Candidate
from backend.app.models.resume import Resume
from backend.app.models.candidate_skill import CandidateSkill
from backend.app.services import resume_upload


@pytest.fixture
def client(tmp_path, monkeypatch):
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
    )

    Base.metadata.create_all(bind=test_engine)

    monkeypatch.setattr(
        resume_upload,
        "STORAGE_DIR",
        tmp_path / "resumes",
    )

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


def create_docx_resume(name, email, skills):
    document = Document()
    document.add_paragraph(name)
    document.add_paragraph("Python Developer")
    document.add_paragraph(f"Email: {email}")
    document.add_paragraph("Skills: " + skills)

    buffer = io.BytesIO()
    document.save(buffer)
    buffer.seek(0)

    return buffer


def test_upload_single_resume(client):
    resume = create_docx_resume(
        "Test Candidate",
        "test@example.com",
        "Python, FastAPI, SQL",
    )

    response = client.post(
        "/api/resumes/upload",
        files=[
            (
                "files",
                (
                    "resume.docx",
                    resume,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                ),
            )
        ],
    )

    assert response.status_code == 200

    data = response.json()
    print("\nUPLOAD RESPONSE:", data)

    assert data["total_files"] == 1
    assert data["successful"] == 1
    assert data["failed"] == 0
    assert data["results"][0]["name"] == "Test Candidate"


def test_upload_multiple_resumes(client):
    resume1 = create_docx_resume(
        "Candidate One",
        "one@example.com",
        "Python, FastAPI",
    )

    resume2 = create_docx_resume(
        "Candidate Two",
        "two@example.com",
        "Java, SQL",
    )

    response = client.post(
        "/api/resumes/upload",
        files=[
            ("files", ("one.docx", resume1, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")),
            ("files", ("two.docx", resume2, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")),
        ],
    )

    assert response.status_code == 200
    assert response.json()["total_files"] == 2
    assert response.json()["successful"] == 2
    assert response.json()["failed"] == 0


def test_duplicate_candidate_email(client):
    for filename in ["first.docx", "second.docx"]:
        resume = create_docx_resume(
            "Duplicate Candidate",
            "duplicate@example.com",
            "Python, FastAPI",
        )

        response = client.post(
            "/api/resumes/upload",
            files=[
                ("files", (filename, resume, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"))
            ],
        )

        assert response.json()["successful"] == 1

    with TestClient(app) as test_client:
        pass

    db_override = app.dependency_overrides[get_db]
    db = next(db_override())

    try:
        candidate_count = db.scalar(
            select(func.count()).select_from(Candidate)
        )
        resume_count = db.scalar(
            select(func.count()).select_from(Resume)
        )

        assert candidate_count == 1
        assert resume_count == 2
    finally:
        db.close()


def test_invalid_file_rejected(client):
    response = client.post(
        "/api/resumes/upload",
        files=[
            ("files", ("resume.txt", b"Invalid resume", "text/plain"))
        ],
    )

    assert response.status_code == 200
    assert response.json()["successful"] == 0
    assert response.json()["failed"] == 1


def test_corrupted_pdf_rejected(client):
    response = client.post(
        "/api/resumes/upload",
        files=[
            ("files", ("resume.pdf", b"Not a real PDF", "application/pdf"))
        ],
    )

    assert response.status_code == 200
    assert response.json()["successful"] == 0
    assert response.json()["failed"] == 1


def test_uploaded_resume_and_skills_saved(client):
    resume = create_docx_resume(
        "Database Candidate",
        "database@example.com",
        "Python, FastAPI, SQL",
    )

    response = client.post(
        "/api/resumes/upload",
        files=[
            ("files", ("candidate.docx", resume, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"))
        ],
    )

    assert response.json()["successful"] == 1

    db = next(app.dependency_overrides[get_db]())

    try:
        candidate = db.scalar(
            select(Candidate).where(
                Candidate.email == "database@example.com"
            )
        )

        assert candidate is not None
        assert len(candidate.resumes) == 1
        assert len(candidate.skills) >= 1

    finally:
        db.close()


def test_empty_file_rejected(client):
    response = client.post(
        "/api/resumes/upload",
        files=[
            ("files", ("empty.docx", b"", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"))
        ],
    )

    assert response.status_code == 200
    assert response.json()["successful"] == 0
    assert response.json()["failed"] == 1
