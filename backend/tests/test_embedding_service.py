
import numpy as np
import pytest

from backend.app.services import embedding_service


class FakeEmbeddingModel:
    def encode(self, text, convert_to_numpy, normalize_embeddings):
        if "python" in text.lower():
            return np.array([1.0, 0.0, 0.0], dtype=np.float32)

        return np.array([0.0, 1.0, 0.0], dtype=np.float32)


def test_generate_embedding(monkeypatch):
    monkeypatch.setattr(
        embedding_service,
        "load_embedding_model",
        lambda: FakeEmbeddingModel(),
    )

    result = embedding_service.generate_embedding("Python developer")

    assert isinstance(result, np.ndarray)
    assert result.shape == (3,)
    assert np.isclose(np.linalg.norm(result), 1.0)


def test_empty_text_rejected():
    with pytest.raises(ValueError):
        embedding_service.generate_embedding("")


def test_similarity_between_identical_embeddings(monkeypatch):
    monkeypatch.setattr(
        embedding_service,
        "load_embedding_model",
        lambda: FakeEmbeddingModel(),
    )

    score = embedding_service.calculate_similarity(
        "Python developer",
        "Python engineer",
    )

    assert score == pytest.approx(1.0)


def test_similarity_between_different_embeddings(monkeypatch):
    monkeypatch.setattr(
        embedding_service,
        "load_embedding_model",
        lambda: FakeEmbeddingModel(),
    )

    score = embedding_service.calculate_similarity(
        "Python developer",
        "Java developer",
    )

    assert score == pytest.approx(0.0)


def test_similarity_rejects_empty_text():
    with pytest.raises(ValueError):
        embedding_service.calculate_similarity(
            "",
            "Python developer",
        )
