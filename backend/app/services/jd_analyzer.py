
import re

from backend.app.services.skill_taxonomy import SKILL_TAXONOMY


def extract_skills(text: str) -> list[str]:
    """Extract canonical skills using the shared skill taxonomy."""

    normalized_text = text.lower()
    matched_skills = []

    for canonical, aliases in SKILL_TAXONOMY.items():
        terms = [canonical.lower(), *[alias.lower() for alias in aliases]]

        for term in terms:
            pattern = (
                r"(?<![a-z0-9+#])"
                + re.escape(term)
                + r"(?![a-z0-9+#])"
            )

            if re.search(pattern, normalized_text):
                matched_skills.append(canonical)
                break

    return sorted(set(matched_skills))


def extract_experience(text: str):
    """Extract the minimum explicitly stated experience requirement."""

    normalized = text.lower()

    # Explicit zero-experience requirements.
    zero_experience_patterns = [
        r"\bfreshers?\s+(?:are\s+)?welcome\b",
        r"\bno\s+(?:prior|previous|professional|work)\s+"
        r"experience\s+(?:is\s+)?required\b",
        r"\bno\s+experience\s+required\b",
        r"\b(?:entry[- ]level|fresher)\s+position\b",
    ]

    if any(
        re.search(pattern, normalized)
        for pattern in zero_experience_patterns
    ):
        return 0

    # Explicit minimum or at-least requirements.
    minimum_patterns = [
        r"\b(?:minimum|at least|required)\s+(?:of\s+)?"
        r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)\s+"
        r"(?:of\s+)?(?:relevant\s+)?experience\b",

        r"\b(?:preferred|required|minimum)\s+experience"
        r"\s+(?:is|of|:)?\s*(\d+(?:\.\d+)?)\s*\+?\s*"
        r"(?:years?|yrs?)\b",
    ]

    for pattern in minimum_patterns:
        match = re.search(pattern, normalized)

        if match:
            value = float(match.group(1))
            return int(value) if value.is_integer() else value

    # Experience ranges: use the lower bound.
    range_pattern = (
        r"\b(\d+(?:\.\d+)?)\s*[-–—]\s*"
        r"(\d+(?:\.\d+)?)\s*(?:years?|yrs?)\s+"
        r"(?:of\s+)?(?:relevant\s+)?experience\b"
    )

    match = re.search(range_pattern, normalized)

    if match:
        value = float(match.group(1))
        return int(value) if value.is_integer() else value

    # Single explicit experience requirement.
    single_pattern = (
        r"\b(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)\s+"
        r"(?:of\s+)?(?:relevant\s+)?experience\b"
    )

    match = re.search(single_pattern, normalized)

    if match:
        value = float(match.group(1))
        return int(value) if value.is_integer() else value

    return None

def extract_education(text: str):
    """Identify the highest education level mentioned."""

    education_levels = [
        ("PhD", ["phd", "doctorate"]),
        ("Master's", ["master's", "masters", "m.tech", "m.sc"]),
        ("Bachelor's", ["bachelor", "b.e.", "b.tech", "b.sc"]),
    ]

    normalized_text = text.lower()

    for level, keywords in education_levels:
        if any(keyword in normalized_text for keyword in keywords):
            return level

    return None


def classify_skill_importance(text: str, skill: str) -> str:
    """Classify skill importance using nearby textual context."""

    normalized_text = text.lower()
    position = normalized_text.find(skill.lower())

    if position == -1:
        return "unspecified"

    # Restrict classification to the current sentence and nearby words.
    sentence_start = max(
        normalized_text.rfind(".", 0, position),
        normalized_text.rfind(";", 0, position),
        normalized_text.rfind("\n", 0, position),
    ) + 1

    context_start = max(sentence_start, position - 35)
    context_end = min(len(normalized_text), position + len(skill) + 30)

    context = normalized_text[context_start:context_end]

    preferred_indicators = [
        "preferred",
        "nice to have",
        "good to have",
        "optional",
        "bonus",
    ]

    mandatory_indicators = [
        "required",
        "mandatory",
        "must have",
        "essential",
        "strong",
        "proficient",
        "proficiency",
        "expertise",
        "hands-on experience",
        "experience in",
        "experience with",
        "knowledge of",
    ]

    if any(word in context for word in preferred_indicators):
        return "preferred"

    if any(word in context for word in mandatory_indicators):
        return "mandatory"

    return "unspecified"


def analyze_job_description(text: str) -> dict:
    """Analyze skills, experience and education requirements."""

    if not isinstance(text, str) or not text.strip():
        raise ValueError("Job description cannot be empty.")

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
        "education": extract_education(text),
    }
