from datetime import datetime

from sqlalchemy import func, select

from backend.app.models.analysis import Analysis
from backend.app.models.analysis_detail import AnalysisDetail
from backend.app.models.candidate import Candidate
from backend.app.models.job import Job
from backend.app.models.resume import Resume
from backend.app.services import candidate_evaluation as evaluation


def create_test_records(db):
    job = Job(
        title="AI Engineer",
        description="Python and Machine Learning. Minimum 2 years experience.",
    )

    candidate = Candidate(
        name="Integration Candidate",
        email="integration@example.com",
        phone="9876543210",
    )

    db.add_all([job, candidate])
    db.flush()

    resume = Resume(
        candidate_id=candidate.id,
        file_name="candidate.pdf",
        file_path="candidate.pdf",
        extracted_text="Python developer with 2 years of experience.",
        uploaded_at=datetime(2026, 1, 1, 10, 0, 0),
    )

    db.add(resume)
    db.commit()

    return job, candidate, resume


def test_evaluation_persists_analysis_and_detail(
    db_session,
    mock_evaluation_services,
):
    job, candidate, resume = create_test_records(db_session)

    result = evaluation.evaluate_job_candidates(
        db_session,
        job.id,
    )

    assert result["total_candidates"] == 1

    analysis = db_session.scalar(
        select(Analysis).where(
            Analysis.job_id == job.id,
            Analysis.candidate_id == candidate.id,
        )
    )

    assert analysis is not None
    assert analysis.resume_id == resume.id
    assert analysis.overall_score == 95.0

    detail = db_session.scalar(
        select(AnalysisDetail).where(
            AnalysisDetail.analysis_id == analysis.id
        )
    )

    assert detail is not None
    assert detail.semantic_score == 90.0
    assert detail.skill_score == 100.0
    assert detail.experience_score == 100.0
    assert detail.education_score is None
    assert detail.project_score == 80.0

    assert detail.matched_skills["required"] == ["Python"]
    assert detail.missing_skills["required"] == []

    assert db_session.scalar(
        select(func.count()).select_from(Analysis)
    ) == 1

    assert db_session.scalar(
        select(func.count()).select_from(AnalysisDetail)
    ) == 1


def test_evaluation_updates_existing_database_records(
    db_session,
    mock_evaluation_services,
    monkeypatch,
):
    job, candidate, resume = create_test_records(db_session)

    evaluation.evaluate_job_candidates(db_session, job.id)

    original_analysis = db_session.scalar(
        select(Analysis).where(
            Analysis.job_id == job.id,
            Analysis.candidate_id == candidate.id,
        )
    )

    original_analysis_id = original_analysis.id
    original_detail_id = original_analysis.details.id

    mock_evaluation_services.scoring_results["overall_score"] = 88.0

    monkeypatch.setattr(
        evaluation,
        "calculate_semantic_match",
        lambda *args: 75.0,
    )

    evaluation.evaluate_job_candidates(db_session, job.id)

    db_session.expire_all()

    updated_analysis = db_session.scalar(
        select(Analysis).where(
            Analysis.job_id == job.id,
            Analysis.candidate_id == candidate.id,
        )
    )

    assert updated_analysis.id == original_analysis_id
    assert updated_analysis.overall_score == 88.0

    assert updated_analysis.details.id == original_detail_id
    assert updated_analysis.details.semantic_score == 75.0

    assert db_session.scalar(
        select(func.count()).select_from(Analysis)
    ) == 1

    assert db_session.scalar(
        select(func.count()).select_from(AnalysisDetail)
    ) == 1


def test_evaluation_selects_latest_resume_from_database(
    db_session,
    mock_evaluation_services,
):
    job = Job(
        title="AI Engineer",
        description="Python and Machine Learning.",
    )

    candidate = Candidate(
        name="Multiple Resume Candidate",
        email="multiple@example.com",
    )

    db_session.add_all([job, candidate])
    db_session.flush()

    older_resume = Resume(
        candidate_id=candidate.id,
        file_name="old_resume.pdf",
        file_path="old_resume.pdf",
        extracted_text="Old resume content.",
        uploaded_at=datetime(2025, 1, 1, 10, 0, 0),
    )

    latest_resume = Resume(
        candidate_id=candidate.id,
        file_name="latest_resume.pdf",
        file_path="latest_resume.pdf",
        extracted_text="Latest resume content.",
        uploaded_at=datetime(2026, 1, 1, 10, 0, 0),
    )

    db_session.add_all([older_resume, latest_resume])
    db_session.commit()

    result = evaluation.evaluate_job_candidates(
        db_session,
        job.id,
    )

    assert result["total_candidates"] == 1

    evaluated_candidate = result["candidates"][0]

    assert evaluated_candidate["resume_id"] == latest_resume.id
    assert evaluated_candidate["resume_name"] == "latest_resume.pdf"

    analysis = db_session.scalar(
        select(Analysis).where(
            Analysis.job_id == job.id,
            Analysis.candidate_id == candidate.id,
        )
    )

    assert analysis.resume_id == latest_resume.id
