
def match_experience(
    required_years: float | None,
    candidate_years: float | None,
) -> dict:
    """
    Compare candidate experience against the minimum
    years required by a job.

    Missing information is represented by None.
    Scores are capped at 100.
    """
    if required_years is not None and required_years < 0:
        raise ValueError("Required experience cannot be negative.")

    if candidate_years is not None and candidate_years < 0:
        raise ValueError("Candidate experience cannot be negative.")

    if required_years is None:
        return {
            "score": None,
            "required_years": None,
            "candidate_years": candidate_years,
            "status": "not_specified",
        }

    if candidate_years is None:
        return {
            "score": None,
            "required_years": required_years,
            "candidate_years": None,
            "status": "unavailable",
        }

    if required_years == 0:
        score = 100.0
    else:
        score = min(candidate_years / required_years, 1.0) * 100

    return {
        "score": round(score, 2),
        "required_years": required_years,
        "candidate_years": candidate_years,
        "status": "evaluated",
    }
