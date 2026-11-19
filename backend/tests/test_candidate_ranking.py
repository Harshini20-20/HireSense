
import pytest

from backend.app.services.candidate_ranking import rank_candidates


def test_candidates_ranked_highest_first():
    candidates = [
        {"candidate_id": 1, "overall_score": 65},
        {"candidate_id": 2, "overall_score": 92},
        {"candidate_id": 3, "overall_score": 78},
    ]

    result = rank_candidates(candidates)

    assert [item["candidate_id"] for item in result] == [2, 3, 1]


def test_rank_numbers_assigned():
    candidates = [
        {"candidate_id": 1, "overall_score": 90},
        {"candidate_id": 2, "overall_score": 80},
    ]

    result = rank_candidates(candidates)

    assert [item["rank"] for item in result] == [1, 2]


def test_equal_scores_use_candidate_id():
    candidates = [
        {"candidate_id": 3, "overall_score": 85},
        {"candidate_id": 1, "overall_score": 85},
        {"candidate_id": 2, "overall_score": 85},
    ]

    result = rank_candidates(candidates)

    assert [item["candidate_id"] for item in result] == [1, 2, 3]


def test_missing_scores_appear_last():
    candidates = [
        {"candidate_id": 1, "overall_score": None},
        {"candidate_id": 2, "overall_score": 75},
    ]

    result = rank_candidates(candidates)

    assert [item["candidate_id"] for item in result] == [2, 1]


def test_all_scores_missing():
    candidates = [
        {"candidate_id": 2, "overall_score": None},
        {"candidate_id": 1, "overall_score": None},
    ]

    result = rank_candidates(candidates)

    assert [item["candidate_id"] for item in result] == [1, 2]


def test_empty_candidate_list():
    assert rank_candidates([]) == []


def test_original_candidates_are_not_modified():
    candidates = [
        {"candidate_id": 1, "overall_score": 80}
    ]

    rank_candidates(candidates)

    assert "rank" not in candidates[0]


def test_invalid_score_rejected():
    with pytest.raises(ValueError):
        rank_candidates([
            {"candidate_id": 1, "overall_score": 120}
        ])


def test_boolean_score_rejected():
    with pytest.raises(TypeError):
        rank_candidates([
            {"candidate_id": 1, "overall_score": True}
        ])


def test_missing_candidate_id_rejected():
    with pytest.raises(ValueError):
        rank_candidates([
            {"overall_score": 80}
        ])
