import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database.base import Base
import backend.app.models  # Register all models


@pytest.fixture
def db_session():
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=test_engine)

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
    )

    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)
        test_engine.dispose()

from types import SimpleNamespace

from backend.app.services import candidate_evaluation as evaluation


@pytest.fixture
def mock_evaluation_services(monkeypatch):
    job_analysis = {
        "mandatory_skills": ["Python"],
        "preferred_skills": ["Machine Learning"],
        "unspecified_skills": [],
        "minimum_experience": 2,
        "education": None,
    }

    candidate_data = {
        "skills": ["Python", "Machine Learning"],
        "experience_years": 2.0,
        "education": [],
        "projects": ["Python machine learning project"],
    }

    skill_results = {
        "score": 100.0,
        "matched_required_skills": ["Python"],
        "missing_required_skills": [],
        "matched_preferred_skills": ["Machine Learning"],
        "missing_preferred_skills": [],
        "matched_unspecified_skills": [],
        "missing_unspecified_skills": [],
        "additional_skills": [],
    }

    experience_results = {
        "score": 100.0,
        "required_years": 2,
        "candidate_years": 2.0,
        "status": "evaluated",
    }

    education_results = {
        "score": None,
        "matched_education": [],
        "missing_education": [],
        "status": "not_specified",
    }

    project_results = {
        "score": 80.0,
        "evaluated_projects": [],
    }

    scoring_results = {
        "overall_score": 95.0,
        "component_scores": {
            "semantic": 90.0,
            "skills": 100.0,
            "experience": 100.0,
            "education": None,
            "projects": 80.0,
        },
        "effective_weights": {
            "semantic": 31.58,
            "skills": 36.84,
            "experience": 21.05,
            "projects": 10.53,
        },
        "unavailable_components": ["education"],
    }

    explanation = {
        "summary": "Strong candidate match.",
        "strengths": ["skills", "experience"],
        "gaps": [],
        "unavailable_components": ["education"],
    }

    monkeypatch.setattr(evaluation, "analyze_job_description", lambda description: job_analysis)
    monkeypatch.setattr(evaluation, "extract_candidate_information", lambda text: candidate_data)
    monkeypatch.setattr(evaluation, "calculate_semantic_match", lambda *args: 90.0)
    monkeypatch.setattr(evaluation, "match_skills", lambda **kwargs: skill_results)
    monkeypatch.setattr(evaluation, "match_experience", lambda **kwargs: experience_results)
    monkeypatch.setattr(evaluation, "match_education", lambda **kwargs: education_results)
    monkeypatch.setattr(evaluation, "calculate_project_relevance", lambda **kwargs: project_results)
    monkeypatch.setattr(evaluation, "calculate_hybrid_score", lambda **kwargs: scoring_results)
    monkeypatch.setattr(evaluation, "generate_candidate_explanation", lambda result: explanation)
    monkeypatch.setattr(evaluation, "rank_candidates", lambda candidates: candidates)

    return SimpleNamespace(
        job_analysis=job_analysis,
        candidate_data=candidate_data,
        skill_results=skill_results,
        experience_results=experience_results,
        education_results=education_results,
        project_results=project_results,
        scoring_results=scoring_results,
        explanation=explanation,
    )

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.database.connection import get_db


@pytest.fixture
def client():
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

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=test_engine)
        test_engine.dispose()
