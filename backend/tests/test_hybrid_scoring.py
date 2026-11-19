
import pytest

from backend.app.services.hybrid_scoring import (
    calculate_hybrid_score,
)


def test_all_components_available():
    result = calculate_hybrid_score(
        semantic_score=90,
        skill_score=80,
        experience_score=70,
        education_score=100,
        project_score=80,
    )

    expected = (
        90 * 0.30
        + 80 * 0.35
        + 70 * 0.20
        + 100 * 0.10
        + 80 * 0.05
    )

    assert result["overall_score"] == expected
    assert result["status"] == "evaluated"


def test_missing_project_score_redistributes_weight():
    result = calculate_hybrid_score(
        semantic_score=80,
        skill_score=90,
        experience_score=70,
        education_score=100,
        project_score=None,
    )

    assert result["overall_score"] == 83.68
    assert "projects" in result["unavailable_components"]
    assert "projects" not in result["effective_weights"]


def test_only_one_component_available():
    result = calculate_hybrid_score(
        semantic_score=None,
        skill_score=85,
        experience_score=None,
        education_score=None,
        project_score=None,
    )

    assert result["overall_score"] == 85.0
    assert result["effective_weights"] == {"skills": 100.0}


def test_all_components_unavailable():
    result = calculate_hybrid_score(
        semantic_score=None,
        skill_score=None,
        experience_score=None,
        education_score=None,
        project_score=None,
    )

    assert result["overall_score"] is None
    assert result["status"] == "insufficient_data"


def test_zero_scores_are_valid():
    result = calculate_hybrid_score(
        semantic_score=0,
        skill_score=0,
        experience_score=0,
        education_score=0,
        project_score=0,
    )

    assert result["overall_score"] == 0.0
    assert result["status"] == "evaluated"


@pytest.mark.parametrize(
    "invalid_score",
    [-1, 101],
)
def test_out_of_range_score_rejected(invalid_score):
    with pytest.raises(ValueError):
        calculate_hybrid_score(
            semantic_score=invalid_score,
            skill_score=80,
            experience_score=70,
            education_score=90,
            project_score=80,
        )


def test_boolean_score_rejected():
    with pytest.raises(TypeError):
        calculate_hybrid_score(
            semantic_score=True,
            skill_score=80,
            experience_score=70,
            education_score=90,
            project_score=80,
        )


def test_string_score_rejected():
    with pytest.raises(TypeError):
        calculate_hybrid_score(
            semantic_score="high",
            skill_score=80,
            experience_score=70,
            education_score=90,
            project_score=80,
        )


def test_effective_weights_sum_to_100():
    result = calculate_hybrid_score(
        semantic_score=80,
        skill_score=90,
        experience_score=None,
        education_score=70,
        project_score=None,
    )

    assert sum(result["effective_weights"].values()) == pytest.approx(100)


def test_component_scores_preserved():
    result = calculate_hybrid_score(
        semantic_score=80,
        skill_score=90,
        experience_score=70,
        education_score=None,
        project_score=60,
    )

    assert result["component_scores"]["education"] is None
    assert result["component_scores"]["semantic"] == 80
