
from backend.app.services.candidate_ranking import (
    generate_candidate_explanation,
)


def test_explanation_identifies_matched_and_missing_skills():
    candidate = {
        "component_scores": {
            "semantic": 90,
            "skills": 80,
            "experience": 40,
            "education": None,
        },
        "matched_required_skills": ["Python", "SQL"],
        "missing_required_skills": ["Docker"],
        "matched_preferred_skills": ["Git"],
        "missing_preferred_skills": ["AWS"],
    }

    result = generate_candidate_explanation(candidate)

    assert "Matches 2 required skill(s)." in result["summary"]
    assert "Missing 1 required skill(s)." in result["summary"]
    assert result["strengths"] == ["semantic", "skills"]
    assert result["gaps"] == ["experience"]
    assert result["unavailable_components"] == ["education"]


def test_explanation_handles_no_skill_evidence():
    candidate = {
        "component_scores": {},
    }

    result = generate_candidate_explanation(candidate)

    assert result["summary"] == (
        "No skill-match evidence is available."
    )


def test_explanation_preserves_skill_details():
    candidate = {
        "component_scores": {},
        "matched_required_skills": ["Python"],
        "missing_required_skills": ["SQL"],
    }

    result = generate_candidate_explanation(candidate)

    assert result["matched_required_skills"] == ["Python"]
    assert result["missing_required_skills"] == ["SQL"]
