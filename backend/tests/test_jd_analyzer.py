
from backend.app.services.jd_analyzer import (
    extract_skills,
    extract_experience,
    extract_education,
    analyze_job_description,
)


def test_extract_skills():
    text = "Python, FastAPI, SQL and Docker"

    skills = extract_skills(text)

    assert "Python" in skills
    assert "FastAPI" in skills
    assert "SQL" in skills
    assert "Docker" in skills


def test_extract_experience():
    text = "At least 3 years of relevant experience"

    assert extract_experience(text) == 3


def test_extract_education():
    text = "Bachelor's degree in Computer Science"

    assert extract_education(text) == "Bachelor's"


def test_analyze_job_description():
    text = """
    Python and FastAPI are mandatory.
    Docker is preferred.
    At least 2 years of experience.
    Bachelor's degree required.
    """

    result = analyze_job_description(text)

    assert "Python" in result["skills"]
    assert "FastAPI" in result["skills"]
    assert result["minimum_experience"] == 2
    assert result["education"] == "Bachelor's"


# Experience extraction regression tests


def test_extract_experience_range_uses_minimum():
    assert extract_experience("1-3 years of experience") == 1


def test_extract_experience_with_plus():
    assert extract_experience("2+ years of relevant experience") == 2


def test_extract_preferred_experience():
    text = "Minimum 1 year of experience. 3 years preferred."

    assert extract_experience(text) == 1


def test_extract_fresher_requirement():
    assert extract_experience("Freshers welcome") == 0


def test_extract_no_experience_required():
    assert extract_experience("No prior experience required") == 0
