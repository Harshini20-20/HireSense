
import pytest

from backend.app.services.experience_matching import match_experience


def test_candidate_meets_required_experience():
    result = match_experience(2, 3)
    assert result["score"] == 100.0
    assert result["status"] == "evaluated"


def test_candidate_has_partial_experience():
    result = match_experience(4, 2)
    assert result["score"] == 50.0


def test_candidate_has_no_experience():
    result = match_experience(2, 0)
    assert result["score"] == 0.0


def test_experience_not_required():
    result = match_experience(None, 3)
    assert result["score"] is None
    assert result["status"] == "not_specified"


def test_candidate_experience_unavailable():
    result = match_experience(2, None)
    assert result["score"] is None
    assert result["status"] == "unavailable"


def test_zero_years_required():
    result = match_experience(0, 0)
    assert result["score"] == 100.0


@pytest.mark.parametrize(
    "required,candidate",
    [(-1, 2), (2, -1)],
)
def test_negative_experience_rejected(required, candidate):
    with pytest.raises(ValueError):
        match_experience(required, candidate)
