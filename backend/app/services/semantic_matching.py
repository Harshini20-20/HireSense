
from backend.app.services.embedding_service import calculate_similarity


def calculate_semantic_match(
    job_description: str,
    resume_text: str,
) -> float:
    """
    Calculate semantic relevance between a job description
    and a candidate resume.

    Returns a score between 0 and 100.
    """
    if not isinstance(job_description, str) or not job_description.strip():
        raise ValueError("Job description cannot be empty.")

    if not isinstance(resume_text, str) or not resume_text.strip():
        raise ValueError("Resume text cannot be empty.")

    similarity = calculate_similarity(
        job_description,
        resume_text,
    )

    # Convert cosine similarity into a 0–100 score.
    normalized_score = max(0.0, min(1.0, similarity)) * 100

    return round(normalized_score, 2)
