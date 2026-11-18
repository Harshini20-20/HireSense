
from functools import lru_cache

import numpy as np


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def load_embedding_model():
    """Load and cache the embedding model only when needed."""
    try:
        from sentence_transformers import SentenceTransformer
    except (ImportError, OSError) as exc:
        raise RuntimeError(
            "The embedding model could not be loaded. "
            "Check the PyTorch installation and Windows security policy."
        ) from exc

    return SentenceTransformer(MODEL_NAME)


def generate_embedding(text: str) -> np.ndarray:
    """Convert text into a normalized numerical embedding."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Input text cannot be empty.")

    model = load_embedding_model()

    embedding = model.encode(
        text.strip(),
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    return np.asarray(embedding, dtype=np.float32)


def calculate_similarity(text_a: str, text_b: str) -> float:
    """Calculate cosine similarity between two text inputs."""
    embedding_a = generate_embedding(text_a)
    embedding_b = generate_embedding(text_b)

    return float(
        np.clip(np.dot(embedding_a, embedding_b), -1.0, 1.0)
    )
