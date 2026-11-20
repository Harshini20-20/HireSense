
import re

from backend.app.services.skill_taxonomy import SKILL_TAXONOMY


EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)

PHONE_PATTERN = re.compile(
    r"(?<!\w)(?:\+?\d{1,3}[-.\s]?)?"
    r"(?:\d{5}[-.\s]?\d{5}|\d{10}|\d{3}[-.\s]?\d{3}[-.\s]?\d{4})"
    r"(?!\w)"
)


EDUCATION_KEYWORDS = [
    "bachelor", "master", "b.tech", "m.tech",
    "b.e", "m.e", "b.sc", "m.sc",
    "bca", "mca", "phd", "diploma",
    "degree", "university", "college",
]

PROJECT_SECTION_HEADERS = {
    "projects",
    "academic projects",
    "personal projects",
    "key projects",
    "project experience",
    "academic and personal projects",
}

NON_PROJECT_SECTION_HEADERS = {
    "education",
    "academic qualifications",
    "experience",
    "work experience",
    "professional experience",
    "skills",
    "technical skills",
    "certifications",
    "certificates",
    "achievements",
    "awards",
    "publications",
    "interests",
    "languages",
    "references",
    "contact",
    "contact information",
}


def normalize_heading(line: str) -> str:
    """Normalize a possible resume section heading."""

    return re.sub(r"[^a-z ]", "", line.lower()).strip()


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
                r"(?<![a-z0-9+#])"
                + re.escape(term)
                + r"(?![a-z0-9+#])"
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
    """
    Extract explicitly stated professional experience.

    Excludes project, academic and coursework durations.
    Supports years and months.
    """

    if not isinstance(text, str) or not text.strip():
        return None

    excluded_sections = PROJECT_SECTION_HEADERS | {
        "education",
        "academic qualifications",
    }

    experience_values = []
    current_section = None

    duration_pattern = re.compile(
        r"\b(\d+(?:\.\d+)?)\s*"
        r"(years?|yrs?|months?|mos?)\b",
        re.IGNORECASE,
    )

    exclusion_terms = (
        "project",
        "coursework",
        "academic",
        "curriculum",
    )

    for line in text.splitlines():
        cleaned_line = line.strip()

        if not cleaned_line:
            continue

        heading = normalize_heading(cleaned_line)

        if heading in excluded_sections:
            current_section = "excluded"
            continue

        if heading in NON_PROJECT_SECTION_HEADERS:
            current_section = heading
            continue

        if current_section == "excluded":
            continue

        normalized_line = cleaned_line.lower()

        if any(term in normalized_line for term in exclusion_terms):
            continue

        matches = duration_pattern.finditer(cleaned_line)

        for match in matches:
            value = float(match.group(1))
            unit = match.group(2).lower()

            if unit.startswith(("month", "mo")):
                value /= 12

            experience_values.append(value)

    if not experience_values:
        return None

    return round(max(experience_values), 2)


def extract_projects(text: str) -> list[str]:
    """
    Extract complete project descriptions from recognized project sections.

    Supports standalone titles, colon-separated titles, multiple projects
    on the same line, bullet markers and wrapped PDF descriptions.
    """

    projects = []
    current_project = None
    inside_projects_section = False

    continuation_starters = {
        "built", "developed", "created", "implemented",
        "designed", "trained", "used", "utilized",
        "integrated", "deployed", "automated", "applied",
        "analyzed", "worked", "leveraged", "using",
        "with", "for", "which", "that", "and",
        "including", "where",
    }

    project_title_pattern = re.compile(
        r"^([A-Z][A-Za-z0-9&()/+.,'’ -]{1,60}):\s*(.*)$"
    )

    inline_title_pattern = re.compile(
        r"(?<=[.!?;])\s+"
        r"(?=[A-Z][A-Za-z0-9&()/+,'’ -]{1,55}:\s)"
    )

    def save_current_project():
        nonlocal current_project

        if current_project:
            projects.append(current_project.strip())
            current_project = None

    def is_standalone_title(line: str) -> bool:
        """Identify likely project titles without a colon."""

        if len(line) > 80:
            return False

        if line.endswith((".", ",", ";", "!", "?")):
            return False

        words = line.split()

        if not 1 <= len(words) <= 10:
            return False

        if words[0].lower() in continuation_starters:
            return False

        return bool(re.match(r"^[A-Z]", line))

    def process_project_line(line: str):
        """
        Process one or more project entries found on a single line.
        """

        nonlocal current_project

        # Split at sentence boundaries followed by another project title.
        entries = inline_title_pattern.split(line)

        for entry in entries:
            entry = entry.strip()

            if not entry:
                continue

            match = project_title_pattern.match(entry)

            if match:
                save_current_project()

                title = match.group(1).strip()
                description = match.group(2).strip()

                current_project = title

                if description:
                    current_project += ": " + description

                continue

            if is_standalone_title(entry):
                save_current_project()
                current_project = entry
                continue

            if current_project:
                current_project += " " + entry
            else:
                current_project = entry

    for line in text.splitlines():
        cleaned_line = line.strip()

        if not cleaned_line:
            continue

        heading = normalize_heading(cleaned_line)

        if heading in PROJECT_SECTION_HEADERS:
            save_current_project()
            inside_projects_section = True
            continue

        if heading in NON_PROJECT_SECTION_HEADERS:
            save_current_project()
            inside_projects_section = False
            continue

        if not inside_projects_section:
            continue

        # Remove bullets and numbered-list prefixes.
        cleaned_line = re.sub(
            r"^(?:[\u2022•\-*]\s*|\d+[.)]\s*)",
            "",
            cleaned_line,
        ).strip()

        if cleaned_line:
            process_project_line(cleaned_line)

    save_current_project()

    return projects

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
        "projects": extract_projects(text),
    }
