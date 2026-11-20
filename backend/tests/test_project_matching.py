
import pytest

from backend.app.services.project_matching import (
    calculate_project_relevance,
)


def test_project_relevance_with_semantic_and_skill_scores(monkeypatch):
    monkeypatch.setattr(
        "backend.app.services.project_matching.calculate_semantic_match",
        lambda job, project: 80.0,
    )

    result = calculate_project_relevance(
        job_description="Python Machine Learning Developer",
        projects=[
            "Built a Machine Learning application using Python."
        ],
        required_skills=["Python", "Machine Learning"],
        preferred_skills=[],
    )

    assert result["semantic_score"] == 80.0
    assert result["skill_score"] == 100.0
    assert result["score"] == 88.0
    assert result["status"] == "evaluated"


def test_project_relevance_with_no_projects():
    result = calculate_project_relevance(
        job_description="Python Developer",
        projects=[],
        required_skills=["Python"],
        preferred_skills=[],
    )

    assert result["score"] is None
    assert result["status"] == "unavailable"
    assert result["project_skills"] == []


def test_project_relevance_with_empty_project_text():
    result = calculate_project_relevance(
        job_description="Python Developer",
        projects=["", "   "],
        required_skills=["Python"],
        preferred_skills=[],
    )

    assert result["score"] is None
    assert result["status"] == "unavailable"


def test_project_relevance_without_skill_requirements(monkeypatch):
    monkeypatch.setattr(
        "backend.app.services.project_matching.calculate_semantic_match",
        lambda job, project: 75.0,
    )

    result = calculate_project_relevance(
        job_description="Software Developer",
        projects=["Built a software application."],
        required_skills=[],
        preferred_skills=[],
    )

    assert result["semantic_score"] == 75.0
    assert result["skill_score"] is None
    assert result["score"] == 75.0


def test_project_relevance_detects_missing_required_skills(monkeypatch):
    monkeypatch.setattr(
        "backend.app.services.project_matching.calculate_semantic_match",
        lambda job, project: 70.0,
    )

    result = calculate_project_relevance(
        job_description="Python and Machine Learning Developer",
        projects=["Built a website using HTML and CSS."],
        required_skills=["Python", "Machine Learning"],
        preferred_skills=[],
    )

    assert result["missing_required_skills"] == [
        "Python",
        "Machine Learning",
    ]
    assert result["skill_score"] == 0.0


def test_project_relevance_reports_unspecified_skills(monkeypatch):
    monkeypatch.setattr(
        "backend.app.services.project_matching.calculate_semantic_match",
        lambda job, project: 80.0,
    )

    result = calculate_project_relevance(
        job_description="Python Developer",
        projects=["Built a service using Python and FastAPI."],
        required_skills=["Python"],
        preferred_skills=[],
        unspecified_skills=["FastAPI", "SQL"],
    )

    assert result["matched_required_skills"] == ["Python"]
    assert result["matched_unspecified_skills"] == ["FastAPI"]
    assert result["missing_unspecified_skills"] == ["SQL"]


def test_project_relevance_selects_top_three_entries(monkeypatch):
    scores = iter([20.0, 90.0, 60.0, 80.0])

    monkeypatch.setattr(
        "backend.app.services.project_matching.calculate_semantic_match",
        lambda job, project: next(scores),
    )

    result = calculate_project_relevance(
        job_description="Python Developer",
        projects=["Project A", "Project B", "Project C", "Project D"],
        required_skills=[],
        preferred_skills=[],
    )

    assert len(result["evaluated_projects"]) == 4
    assert len(result["selected_projects"]) == 3

    assert [
        item["semantic_score"]
        for item in result["selected_projects"]
    ] == [90.0, 80.0, 60.0]

    assert result["score"] == 76.67


def test_project_relevance_rejects_empty_job_description():
    with pytest.raises(ValueError):
        calculate_project_relevance(
            job_description="",
            projects=["Built an application."],
            required_skills=["Python"],
            preferred_skills=[],
        )


def test_project_relevance_rejects_invalid_projects():
    with pytest.raises(TypeError):
        calculate_project_relevance(
            job_description="Python Developer",
            projects="Built an application",
            required_skills=["Python"],
            preferred_skills=[],
        )


def test_project_relevance_rejects_non_string_project():
    with pytest.raises(TypeError):
        calculate_project_relevance(
            job_description="Python Developer",
            projects=["Valid project", 123],
            required_skills=["Python"],
            preferred_skills=[],
        )
