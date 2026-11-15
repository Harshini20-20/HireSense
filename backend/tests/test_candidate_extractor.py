
import pytest

from backend.app.services.candidate_extractor import (
    extract_name,
    extract_email,
    extract_phone,
    extract_skills,
    extract_education,
    extract_experience,
    extract_candidate_information,
)


SAMPLE_RESUME = """
Harshini G
Python Developer

Email: harshini@example.com
Phone: +91 9876543210

SUMMARY
Experienced Python developer with 2 years of experience.

SKILLS
Python, FastAPI, SQL, Machine Learning, Pandas, NumPy

EDUCATION
Bachelor of Engineering in Artificial Intelligence
Visvesvaraya Technological University
"""


def test_extract_name():
    assert extract_name(SAMPLE_RESUME) == "Harshini G"


def test_extract_email():
    assert extract_email(SAMPLE_RESUME) == "harshini@example.com"


def test_extract_phone():
    assert extract_phone(SAMPLE_RESUME) == "+91 9876543210"


def test_extract_skills():
    skills = extract_skills(SAMPLE_RESUME)

    assert "Python" in skills
    assert "FastAPI" in skills
    assert "SQL" in skills
    assert "Machine Learning" in skills
    assert "Pandas" in skills
    assert "NumPy" in skills


def test_extract_education():
    education = extract_education(SAMPLE_RESUME)

    assert any("Bachelor of Engineering" in item for item in education)
    assert any("University" in item for item in education)


def test_extract_experience():
    assert extract_experience(SAMPLE_RESUME) == 2.0


def test_missing_information():
    text = "Looking for opportunities to learn Python."

    assert extract_email(text) is None
    assert extract_phone(text) is None
    assert extract_experience(text) is None


def test_empty_resume():
    with pytest.raises(ValueError):
        extract_candidate_information("")


def test_complete_candidate_extraction():
    result = extract_candidate_information(SAMPLE_RESUME)

    assert result["name"] == "Harshini G"
    assert result["email"] == "harshini@example.com"
    assert result["phone"] == "+91 9876543210"
    assert result["experience_years"] == 2.0
    assert "Python" in result["skills"]
    assert len(result["education"]) >= 1
