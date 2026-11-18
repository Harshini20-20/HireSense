
from backend.app.services.education_matching import match_education


def test_bachelors_requirement_matches_btech():
    result = match_education(
        ["Bachelor's degree"],
        ["B.Tech Computer Science"],
    )

    assert result["score"] == 100.0


def test_bachelors_requirement_matches_be():
    result = match_education(
        ["Bachelor's degree"],
        ["B.E. Artificial Intelligence and Data Science"],
    )

    assert result["score"] == 100.0


def test_masters_requirement_matches_phd():
    result = match_education(
        ["Master's degree"],
        ["PhD Computer Science"],
    )

    assert result["score"] == 100.0


def test_masters_requirement_does_not_match_bachelors():
    result = match_education(
        ["Master's degree"],
        ["B.Tech Computer Science"],
    )

    assert result["score"] == 0.0


def test_multiple_education_requirements():
    result = match_education(
        ["Bachelor's degree", "Master's degree"],
        ["B.Tech Computer Science"],
    )

    assert result["score"] == 50.0
    assert len(result["matched_education"]) == 1
    assert len(result["missing_education"]) == 1


def test_missing_candidate_education():
    result = match_education(
        ["Bachelor's degree"],
        [],
    )

    assert result["score"] is None
    assert result["status"] == "unavailable"


def test_no_education_requirement():
    result = match_education([], ["B.Tech Computer Science"])

    assert result["score"] is None
    assert result["status"] == "not_specified"


def test_unrecognized_education_text():
    result = match_education(
        ["Computer Science certification"],
        ["Computer Science certification from XYZ"],
    )

    assert result["score"] == 100.0
