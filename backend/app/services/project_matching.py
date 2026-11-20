
from backend.app.services.candidate_extractor import extract_skills
from backend.app.services.semantic_matching import calculate_semantic_match
from backend.app.services.skill_matching import match_skills


def calculate_project_relevance(
    job_description: str,
    projects: list[str],
    required_skills: list[str],
    preferred_skills: list[str],
    unspecified_skills: list[str] | None = None,
) -> dict:
    """
    Evaluate project entries independently against a job description.

    Each project entry receives:
        60% semantic relevance
        40% required/preferred skill coverage

    The candidate's project score is the average of the
    top three project scores.

    Unspecified skills are reported but do not affect scoring.
    """

    if not isinstance(job_description, str) or not job_description.strip():
        raise ValueError("Job description cannot be empty.")

    if not isinstance(projects, list):
        raise TypeError("Projects must be a list.")

    if not all(isinstance(project, str) for project in projects):
        raise TypeError("Every project must be a string.")

    if not isinstance(required_skills, list):
        raise TypeError("Required skills must be a list.")

    if not isinstance(preferred_skills, list):
        raise TypeError("Preferred skills must be a list.")

    if unspecified_skills is not None and not isinstance(
        unspecified_skills, list
    ):
        raise TypeError("Unspecified skills must be a list or None.")

    unspecified_skills = unspecified_skills or []

    valid_projects = [
        project.strip()
        for project in projects
        if project.strip()
    ]

    if not valid_projects:
        return {
            "score": None,
            "semantic_score": None,
            "skill_score": None,
            "project_skills": [],
            "matched_required_skills": [],
            "missing_required_skills": required_skills.copy(),
            "matched_preferred_skills": [],
            "missing_preferred_skills": preferred_skills.copy(),
            "matched_unspecified_skills": [],
            "missing_unspecified_skills": unspecified_skills.copy(),
            "evaluated_projects": [],
            "status": "unavailable",
        }

    evaluated_projects = []

    for project in valid_projects:

        # Semantic relevance of this individual project entry.
        semantic_score = calculate_semantic_match(
            job_description,
            project,
        )

        # Skills demonstrated in this project entry.
        project_skills = extract_skills(project)

        skill_results = match_skills(
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            candidate_skills=project_skills,
            unspecified_skills=unspecified_skills,
        )

        skill_score = skill_results["score"]

        # Redistribute the unavailable skill component.
        if skill_score is None:
            project_score = semantic_score

        else:
            project_score = (
                semantic_score * 0.60
                + skill_score * 0.40
            )

        evaluated_projects.append({
            "description": project,
            "score": round(project_score, 2),
            "semantic_score": semantic_score,
            "skill_score": skill_score,
            "project_skills": project_skills,
            "matched_required_skills": skill_results[
                "matched_required_skills"
            ],
            "missing_required_skills": skill_results[
                "missing_required_skills"
            ],
            "matched_preferred_skills": skill_results[
                "matched_preferred_skills"
            ],
            "missing_preferred_skills": skill_results[
                "missing_preferred_skills"
            ],
            "matched_unspecified_skills": skill_results[
                "matched_unspecified_skills"
            ],
            "missing_unspecified_skills": skill_results[
                "missing_unspecified_skills"
            ],
        })

    # Highest-scoring project entries first.
    evaluated_projects.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    # Only the top three entries contribute to the score.
    selected_projects = evaluated_projects[:3]

    overall_project_score = round(
        sum(item["score"] for item in selected_projects)
        / len(selected_projects),
        2,
    )

    semantic_scores = [
        item["semantic_score"]
        for item in selected_projects
        if item["semantic_score"] is not None
    ]

    skill_scores = [
        item["skill_score"]
        for item in selected_projects
        if item["skill_score"] is not None
    ]

    average_semantic_score = (
        round(sum(semantic_scores) / len(semantic_scores), 2)
        if semantic_scores
        else None
    )

    average_skill_score = (
        round(sum(skill_scores) / len(skill_scores), 2)
        if skill_scores
        else None
    )

    # Collect skills demonstrated across all project entries.
    all_project_skills = list(dict.fromkeys(
        skill
        for item in evaluated_projects
        for skill in item["project_skills"]
    ))

    all_matched_required = set(
        skill
        for item in evaluated_projects
        for skill in item["matched_required_skills"]
    )

    all_matched_preferred = set(
        skill
        for item in evaluated_projects
        for skill in item["matched_preferred_skills"]
    )

    all_matched_unspecified = set(
        skill
        for item in evaluated_projects
        for skill in item["matched_unspecified_skills"]
    )

    return {
        "score": overall_project_score,
        "semantic_score": average_semantic_score,
        "skill_score": average_skill_score,
        "project_skills": all_project_skills,

        "matched_required_skills": [
            skill for skill in required_skills
            if skill in all_matched_required
        ],
        "missing_required_skills": [
            skill for skill in required_skills
            if skill not in all_matched_required
        ],

        "matched_preferred_skills": [
            skill for skill in preferred_skills
            if skill in all_matched_preferred
        ],
        "missing_preferred_skills": [
            skill for skill in preferred_skills
            if skill not in all_matched_preferred
        ],

        "matched_unspecified_skills": [
            skill for skill in unspecified_skills
            if skill in all_matched_unspecified
        ],
        "missing_unspecified_skills": [
            skill for skill in unspecified_skills
            if skill not in all_matched_unspecified
        ],

        "evaluated_projects": evaluated_projects,
        "selected_projects": selected_projects,
        "status": "evaluated",
    }
