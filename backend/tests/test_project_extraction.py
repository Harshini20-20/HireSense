
from backend.app.services.candidate_extractor import (
    extract_candidate_information,
    extract_projects,
)


def test_extract_projects_from_standard_section():
    resume = """
    Aarav Mehta
    PROJECTS
    Resume Screening System
    Built a Python application using FastAPI and NLP.
    Developed a machine learning model for candidate ranking.
    EDUCATION
    B.Tech Computer Science
    """

    projects = extract_projects(resume)

    assert len(projects) == 1
    assert "Resume Screening System" in projects[0]
    assert "FastAPI and NLP" in projects[0]
    assert "machine learning model" in projects[0]


def test_extract_projects_from_personal_projects_heading():
    resume = """
    PERSONAL PROJECTS
    AI Chatbot
    Developed a chatbot using Python and NLP.
    SKILLS
    Python, Java, SQL
    """

    projects = extract_projects(resume)

    assert len(projects) == 1
    assert "AI Chatbot" in projects[0]
    assert "Python and NLP" in projects[0]


def test_extract_projects_from_academic_projects_heading():
    resume = """
    ACADEMIC PROJECTS
    Student Management System
    Created a database application using SQL.
    EXPERIENCE
    Software Developer Intern
    """

    projects = extract_projects(resume)

    assert len(projects) == 1
    assert "Student Management System" in projects[0]
    assert "database application using SQL" in projects[0]


def test_project_extraction_stops_at_next_section():
    resume = """
    PROJECTS
    Fraud Detection Model
    Built using Python and Machine Learning.
    EDUCATION
    B.Tech Artificial Intelligence
    College of Engineering
    """

    projects = extract_projects(resume)

    assert len(projects) == 1
    assert "Fraud Detection Model" in projects[0]
    assert "Machine Learning" in projects[0]
    assert not any("B.Tech" in project for project in projects)
    assert not any("College" in project for project in projects)


def test_extract_projects_removes_bullet_markers():
    resume = """
    PROJECTS
    - AI Resume Analyzer
    • Built using Python.
    * Implemented semantic matching.
    CERTIFICATIONS
    Python Certification
    """

    projects = extract_projects(resume)

    assert len(projects) == 1
    assert projects[0] == (
        "AI Resume Analyzer "
        "Built using Python. "
        "Implemented semantic matching."
    )


def test_extract_projects_returns_empty_when_section_missing():
    resume = """
    Aarav Mehta
    EDUCATION
    B.Tech Computer Science
    SKILLS
    Python, SQL, FastAPI
    """

    assert extract_projects(resume) == []


def test_extract_projects_returns_empty_for_empty_text():
    assert extract_projects("") == []


def test_candidate_information_includes_projects():
    resume = """
    Aarav Mehta
    aarav@example.com
    PROJECTS
    AI Resume Analyzer
    Developed using Python and NLP.
    EDUCATION
    B.Tech Computer Science
    """

    candidate = extract_candidate_information(resume)

    assert "projects" in candidate
    assert len(candidate["projects"]) == 1
    assert "AI Resume Analyzer" in candidate["projects"][0]
    assert "Python and NLP" in candidate["projects"][0]


def test_extract_projects_supports_key_projects_heading():
    resume = """
    KEY PROJECTS
    Inventory Management System
    Built with Python and SQL.
    EXPERIENCE
    Python Developer
    """

    projects = extract_projects(resume)

    assert len(projects) == 1
    assert "Inventory Management System" in projects[0]
    assert "Python and SQL" in projects[0]


def test_extract_projects_supports_colon_separated_titles():
    resume = """
    PROJECTS
    Customer Churn Prediction: trained Logistic Regression models.
    Resume Q&A API: built a FastAPI service with REST endpoints.
    EDUCATION
    B.Tech Computer Science
    """

    projects = extract_projects(resume)

    assert len(projects) == 2
    assert "Customer Churn Prediction" in projects[0]
    assert "Logistic Regression" in projects[0]
    assert "Resume Q&A API" in projects[1]
    assert "REST endpoints" in projects[1]


def test_extract_projects_combines_wrapped_pdf_descriptions():
    resume = """
    PROJECTS
    AR Code Debugger: OCR-based real-time code extraction and debugging assistance using Python,
    CSVision: AI-powered CSV analyzer with visualization, automated reporting and intelligent
    APIs.
    Dreamweaver: GenAI application for generating images and videos from text prompts using AI
    OpenCV and EasyOCR.
    insights.
    EDUCATION
    B.E. Artificial Intelligence and Data Science
    """

    projects = extract_projects(resume)

    assert len(projects) == 3
    assert "AR Code Debugger" in projects[0]
    assert "Python" in projects[0]
    assert "CSVision" in projects[1]
    assert "intelligent APIs" in projects[1]
    assert "Dreamweaver" in projects[2]
    assert "OpenCV and EasyOCR" in projects[2]


def test_extract_projects_splits_multiple_titles_on_same_line():
    resume = """
    PROJECTS
    Sentiment Classification: trained an LSTM text classifier. FAQ Retrieval: created a semantic search prototype for support questions.
    EDUCATION
    B.Tech Computer Science
    """

    projects = extract_projects(resume)

    assert len(projects) == 2
    assert "Sentiment Classification" in projects[0]
    assert "LSTM text classifier" in projects[0]
    assert "FAQ Retrieval" in projects[1]
    assert "semantic search prototype" in projects[1]


def test_extract_projects_splits_multiple_inline_projects():
    resume = """
    PROJECTS
    Invoice Processing API: built file upload and validation endpoints. Log Monitor: wrote Python automation to identify recurring application errors.
    EDUCATION
    B.Tech Computer Science
    """

    projects = extract_projects(resume)

    assert len(projects) == 2
    assert "Invoice Processing API" in projects[0]
    assert "validation endpoints" in projects[0]
    assert "Log Monitor" in projects[1]
    assert "Python automation" in projects[1]


def test_extract_projects_does_not_split_normal_description_sentences():
    resume = """
    PROJECTS
    Fraud Detection: built a model using Python. Evaluated accuracy and precision.
    EDUCATION
    B.Tech Computer Science
    """

    projects = extract_projects(resume)

    assert len(projects) == 1
    assert "Fraud Detection" in projects[0]
    assert "Evaluated accuracy and precision" in projects[0]


def test_extract_projects_supports_semicolon_separated_titles():
    resume = """
    PROJECTS
    Inventory API: created CRUD endpoints; Deployment Tool: automated Docker builds.
    EDUCATION
    B.Tech Computer Science
    """

    projects = extract_projects(resume)

    assert len(projects) == 2
    assert "Inventory API" in projects[0]
    assert "CRUD endpoints" in projects[0]
    assert "Deployment Tool" in projects[1]
    assert "Docker builds" in projects[1]
