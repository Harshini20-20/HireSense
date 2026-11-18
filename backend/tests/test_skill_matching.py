
import pytest

from backend.app.services.skill_matching import match_skills


def test_all_required_and_preferred_skills_matched():
    result = match_skills(
        required_skills=["Python", "SQL"],
        preferred_skills=["Docker"],
        candidate_skills=["Python", "SQL", "Docker"],
    )

    assert result["score"] == 100.0
    assert result["missing_required_skills"] == []
    assert result["missing_preferred_skills"] == []


def test_missing_required_skill():
    result = match_skills(
        required_skills=["Python", "SQL"],
        preferred_skills=["Docker"],
        candidate_skills=["Python", "Docker"],
    )

    assert result["score"] == 60.0
    assert result["matched_required_skills"] == ["Python"]
    assert result["missing_required_skills"] == ["SQL"]


def test_missing_preferred_skill():
    result = match_skills(
        required_skills=["Python"],
        preferred_skills=["Docker"],
        candidate_skills=["Python"],
    )

    assert result["score"] == 80.0
    assert result["missing_preferred_skills"] == ["Docker"]


def test_case_insensitive_matching():
    result = match_skills(
        required_skills=["PYTHON", "sql"],
        preferred_skills=[],
        candidate_skills=["Python", "SQL"],
    )

    assert result["score"] == 100.0


def test_duplicate_skills_are_removed():
    result = match_skills(
        required_skills=["Python", "Python"],
        preferred_skills=[],
        candidate_skills=["Python", "Python"],
    )

    assert result["score"] == 100.0
    assert result["matched_required_skills"] == ["Python"]


def test_additional_candidate_skills():
    result = match_skills(
        required_skills=["Python"],
        preferred_skills=["Docker"],
        candidate_skills=["Python", "Docker", "Java", "Linux"],
    )

    assert result["additional_skills"] == ["Java", "Linux"]


def test_only_required_skills():
    result = match_skills(
        required_skills=["Python", "SQL"],
        preferred_skills=[],
        candidate_skills=["Python"],
    )

    assert result["score"] == 50.0


def test_only_preferred_skills():
    result = match_skills(
        required_skills=[],
        preferred_skills=["Docker", "AWS"],
        candidate_skills=["Docker"],
    )

    assert result["score"] == 50.0


def test_no_job_skills_returns_none():
    result = match_skills(
        required_skills=[],
        preferred_skills=[],
        candidate_skills=["Python"],
    )

    assert result["score"] is None


def test_empty_candidate_skills():
    result = match_skills(
        required_skills=["Python"],
        preferred_skills=["Docker"],
        candidate_skills=[],
    )

    assert result["score"] == 0.0
