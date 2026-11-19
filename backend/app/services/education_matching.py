
import re


DEGREE_LEVELS = {
    "phd": 4,
    "doctorate": 4,
    "doctoral": 4,
    "master": 3,
    "masters": 3,
    "m.tech": 3,
    "m.e": 3,
    "m.sc": 3,
    "mba": 3,
    "mca": 3,
    "bachelor": 2,
    "bachelors": 2,
    "b.e": 2,
    "b.tech": 2,
    "b.sc": 2,
    "bca": 2,
    "diploma": 1,
}


def normalize_education(text: str) -> str:
    return " ".join(text.casefold().strip().split())


def get_degree_level(text: str) -> int | None:
    normalized = normalize_education(text)

    # Check longer terms first to avoid partial matches.
    for degree, level in sorted(
        DEGREE_LEVELS.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    ):
        pattern = r"(?<![a-z])" + re.escape(degree) + r"(?![a-z])"

        if re.search(pattern, normalized):
            return level

    return None


def match_education(
    required_education: list[str],
    candidate_education: list[str],
) -> dict:
    """
    Compare required qualifications with candidate education.

    A candidate meets a requirement when their recognized
    degree level is equal to or higher than the required level.

    Requirements without a recognized degree level are
    compared using normalized text matching.
    """
    required = list(dict.fromkeys(
        item.strip()
        for item in required_education
        if isinstance(item, str) and item.strip()
    ))

    candidate = list(dict.fromkeys(
        item.strip()
        for item in candidate_education
        if isinstance(item, str) and item.strip()
    ))

    if not required:
        return {
            "score": None,
            "matched_education": [],
            "missing_education": [],
            "status": "not_specified",
        }

    if not candidate:
        return {
            "score": None,
            "matched_education": [],
            "missing_education": required,
            "status": "unavailable",
        }

    matched = []
    missing = []

    candidate_levels = [
        (item, get_degree_level(item))
        for item in candidate
    ]

    for requirement in required:
        required_level = get_degree_level(requirement)

        if required_level is not None:
            is_match = any(
                candidate_level is not None
                and candidate_level >= required_level
                for _, candidate_level in candidate_levels
            )
        else:
            normalized_requirement = normalize_education(requirement)
            is_match = any(
                normalized_requirement in normalize_education(item)
                or normalize_education(item) in normalized_requirement
                for item in candidate
            )

        if is_match:
            matched.append(requirement)
        else:
            missing.append(requirement)

    score = round(len(matched) / len(required) * 100, 2)

    return {
        "score": score,
        "matched_education": matched,
        "missing_education": missing,
        "status": "evaluated",
    }
