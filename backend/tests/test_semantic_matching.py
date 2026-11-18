
import pytest

from backend.app.services import semantic_matching


def test_high_semantic_similarity(monkeypatch):
    monkeypatch.setattr(
        semantic_matching,
        "calculate_similarity",
        lambda a, b: 0.92,
    )

    score = semantic_matching.calculate_semantic_match(
        "Python backend developer with FastAPI experience",
        "Experienced Python developer building APIs using FastAPI",
    )

    assert score == 92.0


def test_low_semantic_similarity(monkeypatch):
    monkeypatch.setattr(
        semantic_matching,
        "calculate_similarity",
        lambda a, b: 0.25,
    )

    score = semantic_matching.calculate_semantic_match(
        "Python backend developer",
        "Graphic designer with illustration experience",
    )

    assert score == 25.0


def test_negative_similarity_is_clamped(monkeypatch):
    monkeypatch.setattr(
        semantic_matching,
        "calculate_similarity",
        lambda a, b: -0.2,
    )

    score = semantic_matching.calculate_semantic_match(
        "Python developer",
        "Unrelated resume",
    )

    assert score == 0.0


def test_similarity_above_one_is_clamped(monkeypatch):
    monkeypatch.setattr(
        semantic_matching,
        "calculate_similarity",
        lambda a, b: 1.2,
    )

    score = semantic_matching.calculate_semantic_match(
        "Python developer",
        "Python developer",
    )

    assert score == 100.0


def test_empty_job_description_rejected():
    with pytest.raises(ValueError):
        semantic_matching.calculate_semantic_match(
            "",
            "Python developer resume",
        )


def test_empty_resume_rejected():
    with pytest.raises(ValueError):
        semantic_matching.calculate_semantic_match(
            "Python developer job description",
            "",
        )
