import re

from backend.app.services.skill_taxonomy import SKILL_TAXONOMY


def extract_skills(text: str) -> list[str]:
    normalized_text = text.lower()
    matched_skills = []

    for canonical, aliases in SKILL_TAXONOMY.items():
        for alias in aliases:
            pattern = (
                r"(?<![a-z0-9+#.])"
                + re.escape(alias.lower())
                + r"(?![a-z0-9+#.])"
            )

            if re.search(pattern, normalized_text):
                matched_skills.append(canonical)
                break

    return sorted(set(matched_skills))


def extract_experience(text: str):
    patterns = [
        r"(\d+)\s*\+?\s*(?:years?|yrs?)\s+"
        r"(?:of\s+)?(?:relevant\s+)?experience",
        r"minimum\s+(?:of\s+)?(\d+)\s*"
        r"(?:years?|yrs?)"
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            return int(match.group(1))

    return None


def extract_education(text: str):
    education_levels = [
        ("PhD", ["phd", "doctorate"]),
        ("Master's", ["master's", "masters", "m.tech", "m.sc"]),
        ("Bachelor's", ["bachelor", "b.e.", "b.tech", "b.sc"])
    ]

    normalized_text = text.lower()

    for level, keywords in education_levels:
        if any(keyword in normalized_text for keyword in keywords):
            return level

    return None


def classify_skill_importance(text: str, skill: str) -> str:
    normalized_text = text.lower()
    position = normalized_text.find(skill.lower())

    if position == -1:
        return "preferred"

    context = normalized_text[
        max(0, position - 100):position + len(skill) + 100
    ]

    if any(word in context for word in [
        "required",
        "mandatory",
        "must have",
        "essential"
    ]):
        return "mandatory"

    if any(word in context for word in [
        "preferred",
        "nice to have",
        "good to have",
        "optional"
    ]):
        return "preferred"

    return "unspecified"


def analyze_job_description(text: str) -> dict:
    skills = extract_skills(text)

    mandatory = []
    preferred = []
    unspecified = []

    for skill in skills:
        importance = classify_skill_importance(text, skill)

        if importance == "mandatory":
            mandatory.append(skill)
        elif importance == "preferred":
            preferred.append(skill)
        else:
            unspecified.append(skill)

    return {
        "skills": skills,
        "mandatory_skills": mandatory,
        "preferred_skills": preferred,
        "unspecified_skills": unspecified,
        "minimum_experience": extract_experience(text),
        "education": extract_education(text)
    }