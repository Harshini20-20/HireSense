
import re

from backend.app.services.skill_taxonomy import SKILL_TAXONOMY


EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)

PHONE_PATTERN = re.compile(
    r"(?<!\w)(?:\+?\d{1,3}[-.\s]?)?"
    r"(?:\d{3}[-.\s]?\d{3}[-.\s]?\d{4}|\d{10})"
    r"(?!\w)"
)

EXPERIENCE_PATTERN = re.compile(
    r"(\d+(?:\.\d+)?)\s*\+?\s*"
    r"(?:years?|yrs?)(?:\s+of)?\s+"
    r"(?:experience|exp)",
    re.IGNORECASE,
)

EDUCATION_KEYWORDS = [
    "bachelor", "master", "b.tech", "m.tech",
    "b.e", "m.e", "b.sc", "m.sc",
    "bca", "mca", "phd", "diploma",
    "degree", "university", "college",
]


def extract_email(text: str) -> str | None:
    match = EMAIL_PATTERN.search(text)
    return match.group(0) if match else None


def extract_phone(text: str) -> str | None:
    match = PHONE_PATTERN.search(text)
    return match.group(0).strip() if match else None


def extract_name(text: str) -> str | None:
    """Heuristically identify a candidate name from the opening lines."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    for line in lines[:5]:
        if EMAIL_PATTERN.search(line) or PHONE_PATTERN.search(line):
            continue

        if len(line) > 60 or any(char.isdigit() for char in line):
            continue

        if any(word in line.lower() for word in [
            "resume", "curriculum vitae", "portfolio",
            "linkedin", "github", "developer", "engineer"
        ]):
            continue

        words = line.split()

        if 2 <= len(words) <= 4 and all(
            re.fullmatch(r"[A-Za-z][A-Za-z'.-]*", word)
            for word in words
        ):
            return line

    return None


def extract_skills(text: str) -> list[str]:
    """Extract canonical skills using the shared skill taxonomy."""
    normalized_text = text.lower()
    matched_skills = []

    for skill, aliases in SKILL_TAXONOMY.items():
        terms = [skill.lower(), *[alias.lower() for alias in aliases]]

        for term in terms:
            pattern = (
                r"(?<![a-z0-9+#.])"
                + re.escape(term)
                + r"(?![a-z0-9+#.])"
            )

            if re.search(pattern, normalized_text):
                matched_skills.append(skill)
                break

    return sorted(set(matched_skills))


def extract_education(text: str) -> list[str]:
    """Collect resume lines that appear to contain education details."""
    education = []

    for line in text.splitlines():
        cleaned_line = line.strip()

        if not cleaned_line:
            continue

        if any(
            keyword in cleaned_line.lower()
            for keyword in EDUCATION_KEYWORDS
        ):
            education.append(cleaned_line)

    return list(dict.fromkeys(education))


def extract_experience(text: str) -> float | None:
    """Extract explicitly stated years of experience."""
    matches = EXPERIENCE_PATTERN.findall(text)

    if not matches:
        return None

    return max(float(value) for value in matches)


def extract_candidate_information(text: str) -> dict:
    """Extract structured information from resume text."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Resume text cannot be empty.")

    return {
        "name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "skills": extract_skills(text),
        "education": extract_education(text),
        "experience_years": extract_experience(text),
    }
