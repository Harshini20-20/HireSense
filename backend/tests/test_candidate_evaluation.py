
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from backend.app.models.analysis import Analysis
from backend.app.models.analysis_detail import AnalysisDetail
from backend.app.models.candidate import Candidate
from backend.app.models.job import Job
from backend.app.models.resume import Resume
from backend.app.services import candidate_evaluation as evaluation


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.scalars.return_value.all.return_value = []
    return db


@pytest.fixture
def job():
    return Job(
        id=1,
        title="AI Engineer",
        description="Python and Machine Learning. Minimum 2 years experience.",
    )


@pytest.fixture
def candidate():
    return Candidate(
        id=1,
        name="Test Candidate",
        email="candidate@example.com",
        phone="9876543210",
    )


@pytest.fixture
def resume(candidate):
    return Resume(
        id=1,
        candidate_id=candidate.id,
        file_name="candidate.pdf",
        file_path="candidate.pdf",
        extracted_text=(
            "WORK EXPERIENCE\n"
            "2 years of professional experience."
        ),
    )


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

    monkeypatch.setattr(
        evaluation,
        "analyze_job_description",
        lambda description: job_analysis,
    )

    monkeypatch.setattr(
        evaluation,
        "extract_candidate_information",
        lambda text: candidate_data,
    )

    monkeypatch.setattr(
        evaluation,
        "calculate_semantic_match",
        lambda *args: 90.0,
    )

    monkeypatch.setattr(
        evaluation,
        "match_skills",
        lambda **kwargs: skill_results,
    )

    monkeypatch.setattr(
        evaluation,
        "match_experience",
        lambda **kwargs: experience_results,
    )

    monkeypatch.setattr(
        evaluation,
        "match_education",
        lambda **kwargs: education_results,
    )

    monkeypatch.setattr(
        evaluation,
        "calculate_project_relevance",
        lambda **kwargs: project_results,
    )

    monkeypatch.setattr(
        evaluation,
        "calculate_hybrid_score",
        lambda **kwargs: scoring_results,
    )

    monkeypatch.setattr(
        evaluation,
        "generate_candidate_explanation",
        lambda result: explanation,
    )

    monkeypatch.setattr(
        evaluation,
        "rank_candidates",
        lambda candidates: candidates,
    )

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


def test_evaluation_raises_error_for_missing_job(mock_db):
    mock_db.get.return_value = None

    with pytest.raises(ValueError, match="Job not found"):
        evaluation.evaluate_job_candidates(mock_db, 999)

    mock_db.commit.assert_not_called()


def test_evaluation_returns_empty_result_when_no_candidates(
    mock_db,
    job,
    monkeypatch,
):
    mock_db.get.return_value = job

    monkeypatch.setattr(
        evaluation,
        "analyze_job_description",
        lambda description: {
            "mandatory_skills": [],
            "preferred_skills": [],
            "unspecified_skills": [],
            "minimum_experience": None,
            "education": None,
        },
    )

    result = evaluation.evaluate_job_candidates(mock_db, job.id)

    assert result["job_id"] == job.id
    assert result["job_title"] == job.title
    assert result["total_candidates"] == 0
    assert result["candidates"] == []

    mock_db.commit.assert_called_once()


def test_evaluation_creates_new_analysis(
    mock_db,
    job,
    candidate,
    resume,
    mock_evaluation_services,
):
    mock_db.get.side_effect = lambda model, object_id: {
        Job: job,
        Candidate: candidate,
    }.get(model)

    mock_db.scalars.return_value.all.return_value = [resume]
    mock_db.scalar.return_value = None

    result = evaluation.evaluate_job_candidates(mock_db, job.id)

    assert result["total_candidates"] == 1

    evaluated = result["candidates"][0]

    assert evaluated["candidate_id"] == candidate.id
    assert evaluated["overall_score"] == 95.0
    assert evaluated["experience"]["candidate_years"] == 2.0
    assert evaluated["experience"]["status"] == "evaluated"

    assert evaluated["component_scores"]["experience"] == 100.0
    assert evaluated["unavailable_components"] == ["education"]

    added_objects = [
        call.args[0]
        for call in mock_db.add.call_args_list
    ]

    analysis = next(
        item for item in added_objects
        if isinstance(item, Analysis)
    )

    detail = next(
        item for item in added_objects
        if isinstance(item, AnalysisDetail)
    )

    assert analysis.job_id == job.id
    assert analysis.candidate_id == candidate.id
    assert analysis.resume_id == resume.id
    assert analysis.overall_score == 95.0

    assert detail.semantic_score == 90.0
    assert detail.skill_score == 100.0
    assert detail.experience_score == 100.0
    assert detail.education_score is None
    assert detail.project_score == 80.0

    mock_db.flush.assert_called_once()
    mock_db.commit.assert_called_once()


def test_evaluation_updates_existing_analysis(
    mock_db,
    job,
    candidate,
    resume,
    mock_evaluation_services,
):
    existing_detail = MagicMock()

    existing_analysis = SimpleNamespace(
        id=10,
        details=existing_detail,
        resume_id=None,
        overall_score=None,
    )

    mock_db.get.side_effect = lambda model, object_id: {
        Job: job,
        Candidate: candidate,
    }.get(model)

    mock_db.scalars.return_value.all.return_value = [resume]
    mock_db.scalar.return_value = existing_analysis

    result = evaluation.evaluate_job_candidates(mock_db, job.id)

    assert result["total_candidates"] == 1

    assert existing_analysis.resume_id == resume.id
    assert existing_analysis.overall_score == 95.0

    assert existing_detail.semantic_score == 90.0
    assert existing_detail.skill_score == 100.0
    assert existing_detail.experience_score == 100.0
    assert existing_detail.project_score == 80.0

    mock_db.add.assert_not_called()
    mock_db.commit.assert_called_once()


def test_evaluation_uses_latest_resume_per_candidate(
    mock_db,
    job,
    candidate,
    mock_evaluation_services,
):
    older_resume = Resume(
        id=1,
        candidate_id=candidate.id,
        file_name="old.pdf",
        file_path="old.pdf",
        extracted_text="Old resume text.",
    )

    latest_resume = Resume(
        id=2,
        candidate_id=candidate.id,
        file_name="latest.pdf",
        file_path="latest.pdf",
        extracted_text="Latest resume text.",
    )

    mock_db.get.side_effect = lambda model, object_id: {
        Job: job,
        Candidate: candidate,
    }.get(model)

    # The query orders resumes newest first.
    mock_db.scalars.return_value.all.return_value = [
        latest_resume,
        older_resume,
    ]

    mock_db.scalar.return_value = None

    result = evaluation.evaluate_job_candidates(mock_db, job.id)

    assert result["total_candidates"] == 1

    evaluated = result["candidates"][0]

    assert evaluated["resume_id"] == latest_resume.id
    assert evaluated["resume_name"] == "latest.pdf"
    
    assert len(
        [
            call for call in mock_db.add.call_args_list
            if isinstance(call.args[0], Analysis)
        ]
    ) == 1