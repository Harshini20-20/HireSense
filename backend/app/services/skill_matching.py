
def normalize_skill(skill: str) -> str:
    """Normalize skill names for case-insensitive comparison."""
    return " ".join(skill.casefold().strip().split())


def unique_skills(skills: list[str]) -> dict[str, str]:
    """Remove duplicates while preserving original skill names."""
    result = {}

    for skill in skills:
        if not isinstance(skill, str) or not skill.strip():
            continue

        normalized = normalize_skill(skill)
        result.setdefault(normalized, skill.strip())

    return result


def match_skills(
    required_skills: list[str],
    preferred_skills: list[str],
    candidate_skills: list[str],
    unspecified_skills: list[str] | None = None,
) -> dict:
    """
    Compare candidate skills against job requirements.

    Required skills contribute 80%.
    Preferred skills contribute 20%.
    Unspecified skills are reported but do not affect scoring.
    """

    required = unique_skills(required_skills)
    preferred = unique_skills(preferred_skills)
    unspecified = unique_skills(unspecified_skills or [])
    candidate = unique_skills(candidate_skills)

    candidate_set = set(candidate)

    matched_required = required.keys() & candidate_set
    missing_required = required.keys() - candidate_set

    matched_preferred = preferred.keys() & candidate_set
    missing_preferred = preferred.keys() - candidate_set

    matched_unspecified = unspecified.keys() & candidate_set
    missing_unspecified = unspecified.keys() - candidate_set

    matched_required_names = [
        required[key] for key in required if key in matched_required
    ]
    missing_required_names = [
        required[key] for key in required if key in missing_required
    ]

    matched_preferred_names = [
        preferred[key] for key in preferred if key in matched_preferred
    ]
    missing_preferred_names = [
        preferred[key] for key in preferred if key in missing_preferred
    ]

    matched_unspecified_names = [
        unspecified[key] for key in unspecified if key in matched_unspecified
    ]
    missing_unspecified_names = [
        unspecified[key] for key in unspecified if key in missing_unspecified
    ]

    all_job_skills = (
        set(required) | set(preferred) | set(unspecified)
    )

    additional_skills = [
        candidate[key]
        for key in candidate
        if key not in all_job_skills
    ]

    if not required and not preferred:
        score = None
    else:
        required_coverage = (
            len(matched_required) / len(required)
            if required else None
        )

        preferred_coverage = (
            len(matched_preferred) / len(preferred)
            if preferred else None
        )

        if required and preferred:
            score = (
                required_coverage * 80
                + preferred_coverage * 20
            )
        elif required:
            score = required_coverage * 100
        else:
            score = preferred_coverage * 100

        score = round(score, 2)

    return {
        "score": score,
        "matched_required_skills": matched_required_names,
        "missing_required_skills": missing_required_names,
        "matched_preferred_skills": matched_preferred_names,
        "missing_preferred_skills": missing_preferred_names,
        "matched_unspecified_skills": matched_unspecified_names,
        "missing_unspecified_skills": missing_unspecified_names,
        "additional_skills": additional_skills,
    }
