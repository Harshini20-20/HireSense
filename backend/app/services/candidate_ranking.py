
def rank_candidates(candidates: list[dict]) -> list[dict]:
    """
    Rank candidates by overall score, highest first.

    Candidates without an overall score appear last.
    Equal scores are resolved using candidate_id for
    deterministic ordering.
    """

    validated = []

    for candidate in candidates:
        if not isinstance(candidate, dict):
            raise TypeError("Each candidate must be a dictionary.")

        score = candidate.get("overall_score")
        candidate_id = candidate.get("candidate_id")

        if candidate_id is None:
            raise ValueError("Every candidate must have a candidate_id.")

        if score is not None:
            if isinstance(score, bool) or not isinstance(score, (int, float)):
                raise TypeError("Candidate score must be numeric or None.")

            if not 0 <= score <= 100:
                raise ValueError("Candidate score must be between 0 and 100.")

        validated.append(candidate.copy())

    validated.sort(
        key=lambda item: (
            item["overall_score"] is None,
            -(item["overall_score"] or 0),
            str(item["candidate_id"]),
        )
    )

    for position, candidate in enumerate(validated, start=1):
        candidate["rank"] = position

    return validated


def generate_candidate_explanation(candidate: dict) -> dict:
    """
    Generate an evidence-based explanation from matching results.
    Does not infer missing candidate information.
    """

    component_scores = candidate.get("component_scores", {})

    matched_required = candidate.get("matched_required_skills", [])
    missing_required = candidate.get("missing_required_skills", [])

    matched_preferred = candidate.get("matched_preferred_skills", [])
    missing_preferred = candidate.get("missing_preferred_skills", [])

    matched_unspecified = candidate.get(
        "matched_unspecified_skills", []
    )
    missing_unspecified = candidate.get(
        "missing_unspecified_skills", []
    )

    strengths = []
    gaps = []
    unavailable = []

    for component, score in component_scores.items():
        if score is None:
            unavailable.append(component)
        elif score >= 80:
            strengths.append(component)
        elif score < 50:
            gaps.append(component)

    summary_parts = []

    # Mandatory skill matches
    if matched_required:
        summary_parts.append(
            f"Matches {len(matched_required)} required skill(s)."
        )

    if missing_required:
        summary_parts.append(
            f"Missing {len(missing_required)} required skill(s)."
        )

    # Preferred skill matches
    if matched_preferred:
        summary_parts.append(
            f"Matches {len(matched_preferred)} preferred skill(s)."
        )

    if missing_preferred:
        summary_parts.append(
            f"Missing {len(missing_preferred)} preferred skill(s)."
        )

    # Unspecified skills are reported separately.
    # They do not contribute to the skill score.
    if matched_unspecified:
        summary_parts.append(
            f"Matches {len(matched_unspecified)} unspecified skill(s)."
        )

    if missing_unspecified:
        summary_parts.append(
            f"Missing {len(missing_unspecified)} unspecified skill(s)."
        )

    if not summary_parts:
        summary_parts.append(
            "No skill-match evidence is available."
        )

    return {
        "summary": " ".join(summary_parts),
        "strengths": strengths,
        "gaps": gaps,
        "unavailable_components": unavailable,

        "matched_required_skills": matched_required,
        "missing_required_skills": missing_required,

        "matched_preferred_skills": matched_preferred,
        "missing_preferred_skills": missing_preferred,

        "matched_unspecified_skills": matched_unspecified,
        "missing_unspecified_skills": missing_unspecified,
    }
