
import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.analysis import Analysis
from backend.app.models.analysis_detail import AnalysisDetail
from backend.app.models.candidate import Candidate
from backend.app.models.job import Job
from backend.app.models.resume import Resume
from backend.app.models.job_candidate import JobCandidate

from backend.app.services.candidate_extractor import (
    extract_candidate_information,
)
from backend.app.services.candidate_ranking import (
    generate_candidate_explanation,
    rank_candidates,
)
from backend.app.services.education_matching import match_education
from backend.app.services.experience_matching import match_experience
from backend.app.services.hybrid_scoring import calculate_hybrid_score
from backend.app.services.jd_analyzer import analyze_job_description
from backend.app.services.project_matching import (
    calculate_project_relevance,
)
from backend.app.services.semantic_matching import calculate_semantic_match
from backend.app.services.skill_matching import match_skills


def evaluate_job_candidates(db: Session, job_id: int) -> dict:
    """
    Evaluate candidates against a job description.

    Uses each candidate's latest uploaded resume.
    Evaluates semantic relevance, skills, experience,
    education and project relevance.
    Persists evaluation results and returns ranked candidates.
    """

    job = db.get(Job, job_id)

    if job is None:
        raise ValueError("Job not found.")

    job_analysis = analyze_job_description(job.description)

    mandatory_skills = job_analysis["mandatory_skills"]
    preferred_skills = job_analysis["preferred_skills"]
    unspecified_skills = job_analysis["unspecified_skills"]

    # Retrieve the latest resume for each candidate.
    resumes = db.scalars(
        select(Resume)
        .where(Resume.extracted_text.is_not(None))
        .order_by(
            Resume.uploaded_at.desc(),
            Resume.id.desc(),
        )
    ).all()

    latest_resumes = {}

    for resume in resumes:
        latest_resumes.setdefault(resume.candidate_id, resume)

    applied_links = db.scalars(
        select(JobCandidate).where(JobCandidate.job_id == job.id)
    ).all()
    applied_ids = {link.candidate_id for link in applied_links}

    applied_candidates = []
    recommended_candidates = []

    for candidate_id, resume in latest_resumes.items():

        if not resume.extracted_text or not resume.extracted_text.strip():
            continue

        candidate = db.get(Candidate, candidate_id)

        if candidate is None:
            continue

        candidate_data = extract_candidate_information(
            resume.extracted_text
        )

        # 1. Semantic matching
        semantic_score = calculate_semantic_match(
            job.description,
            resume.extracted_text,
        )

        # 2. Skill matching
        skill_results = match_skills(
            required_skills=mandatory_skills,
            preferred_skills=preferred_skills,
            candidate_skills=candidate_data["skills"],
            unspecified_skills=unspecified_skills,
        )

        # 3. Experience matching
        experience_results = match_experience(
            required_years=job_analysis["minimum_experience"],
            candidate_years=candidate_data["experience_years"],
        )

        # 4. Education matching
        required_education = (
            [job_analysis["education"]]
            if job_analysis["education"]
            else []
        )

        education_results = match_education(
            required_education=required_education,
            candidate_education=candidate_data["education"],
        )

        # 5. Project relevance matching
        project_results = calculate_project_relevance(
            job_description=job.description,
            projects=candidate_data["projects"],
            required_skills=mandatory_skills,
            preferred_skills=preferred_skills,
            unspecified_skills=unspecified_skills,
        )

        project_score = project_results["score"]

        # 6. Hybrid scoring
        scoring_results = calculate_hybrid_score(
            semantic_score=semantic_score,
            skill_score=skill_results["score"],
            experience_score=experience_results["score"],
            education_score=education_results["score"],
            project_score=project_score,
        )

        matched_skills = {
            "required": skill_results["matched_required_skills"],
            "preferred": skill_results["matched_preferred_skills"],
            "unspecified": skill_results["matched_unspecified_skills"],
        }

        missing_skills = {
            "required": skill_results["missing_required_skills"],
            "preferred": skill_results["missing_preferred_skills"],
            "unspecified": skill_results["missing_unspecified_skills"],
        }

        candidate_result = {
            "candidate_id": candidate.id,
            "candidate_name": candidate.name,
            "email": candidate.email,
            "resume_id": resume.id,
            "resume_name": resume.file_name,

            "overall_score": scoring_results["overall_score"],
            "component_scores": scoring_results["component_scores"],
            "effective_weights": scoring_results["effective_weights"],
            "unavailable_components": scoring_results[
                "unavailable_components"
            ],

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

            "unspecified_skills": unspecified_skills,
            "additional_skills": skill_results["additional_skills"],

            "experience": experience_results,
            "education": education_results,

            "project_relevance": project_results,
        }

        explanation = generate_candidate_explanation(candidate_result)
        candidate_result["explanation"] = explanation

        # Find an existing evaluation for this job and candidate.
        existing_analysis = db.scalar(
            select(Analysis).where(
                Analysis.job_id == job.id,
                Analysis.candidate_id == candidate.id,
            )
        )

        if existing_analysis is None:
            existing_analysis = Analysis(
                job_id=job.id,
                candidate_id=candidate.id,
                resume_id=resume.id,
                overall_score=scoring_results["overall_score"],
            )

            db.add(existing_analysis)
            db.flush()

        else:
            existing_analysis.resume_id = resume.id
            existing_analysis.overall_score = scoring_results["overall_score"]

        detail = existing_analysis.details

        if detail is None:
            detail = AnalysisDetail(
                analysis_id=existing_analysis.id,
                semantic_score=semantic_score,
                skill_score=skill_results["score"],
                experience_score=experience_results["score"],
                education_score=education_results["score"],
                project_score=project_score,
                matched_skills=matched_skills,
                missing_skills=missing_skills,
                effective_weights=scoring_results["effective_weights"],
                unavailable_components=scoring_results[
                    "unavailable_components"
                ],
                explanation=json.dumps(explanation),
            )

            db.add(detail)

        else:
            detail.semantic_score = semantic_score
            detail.skill_score = skill_results["score"]
            detail.experience_score = experience_results["score"]
            detail.education_score = education_results["score"]
            detail.project_score = project_score
            detail.matched_skills = matched_skills
            detail.missing_skills = missing_skills
            detail.effective_weights = scoring_results["effective_weights"]
            detail.unavailable_components = scoring_results[
                "unavailable_components"
            ]
            detail.explanation = json.dumps(explanation)

        candidate_result["source"] = (
            "APPLIED" if candidate.id in applied_ids else "AI_RECOMMENDED"
        )
        if candidate.id in applied_ids:
            applied_candidates.append(candidate_result)
        elif scoring_results["overall_score"] is not None and scoring_results["overall_score"] >= 60:
            score = scoring_results["overall_score"]
            candidate_result["match_level"] = (
                "Strong Match" if score >= 80
                else "Good Match" if score >= 70
                else "Potential Match"
            )
            recommended_candidates.append(candidate_result)

    ranked_applied = rank_candidates(applied_candidates)
    ranked_recommended = rank_candidates(recommended_candidates)
    ranked_candidates = rank_candidates(ranked_applied + ranked_recommended)

    db.commit()

    return {
        "job_id": job.id,
        "job_title": job.title,
        "total_candidates": len(ranked_candidates),
        "applied_count": len(ranked_applied),
        "recommended_count": len(ranked_recommended),
        "job_requirements": job_analysis,
        "applied_candidates": ranked_applied,
        "recommended_candidates": ranked_recommended,
        "candidates": ranked_candidates,
    }
