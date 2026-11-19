
from collections.abc import Mapping


COMPONENT_WEIGHTS = {
    "semantic": 30.0,
    "skills": 35.0,
    "experience": 20.0,
    "education": 10.0,
    "projects": 5.0,
}


def calculate_hybrid_score(
    semantic_score: float | None,
    skill_score: float | None,
    experience_score: float | None,
    education_score: float | None,
    project_score: float | None,
) -> dict:
    """
    Calculate an explainable hybrid candidate score.

    Unavailable components (None) are excluded and their
    weights are proportionally redistributed.

    All supplied component scores must be between 0 and 100.
    """

    component_scores = {
        "semantic": semantic_score,
        "skills": skill_score,
        "experience": experience_score,
        "education": education_score,
        "projects": project_score,
    }

    available = {}

    for component, score in component_scores.items():
        if score is None:
            continue

        if isinstance(score, bool) or not isinstance(score, (int, float)):
            raise TypeError(
                f"{component} score must be numeric or None."
            )

        if not 0 <= score <= 100:
            raise ValueError(
                f"{component} score must be between 0 and 100."
            )

        available[component] = float(score)

    if not available:
        return {
            "overall_score": None,
            "component_scores": component_scores,
            "effective_weights": {},
            "unavailable_components": list(COMPONENT_WEIGHTS),
            "status": "insufficient_data",
        }

    available_weight = sum(
        COMPONENT_WEIGHTS[name] for name in available
    )

    effective_weights = {
        name: round(
            COMPONENT_WEIGHTS[name] / available_weight * 100,
            2,
        )
        for name in available
    }

    overall_score = sum(
        available[name]
        * COMPONENT_WEIGHTS[name]
        / available_weight
        for name in available
    )

    unavailable = [
        name
        for name in COMPONENT_WEIGHTS
        if name not in available
    ]

    return {
        "overall_score": round(overall_score, 2),
        "component_scores": component_scores,
        "effective_weights": effective_weights,
        "unavailable_components": unavailable,
        "status": "evaluated",
    }
