
from pathlib import Path

import pymupdf
import pytest
from docx import Document

from backend.app.services.resume_parser import (
    ResumeParsingError,
    extract_pdf_text,
    extract_docx_text,
    extract_resume_text,
)


@pytest.fixture
def sample_pdf(tmp_path):
    file_path = tmp_path / "sample.pdf"

    with pymupdf.open() as pdf:
        page = pdf.new_page()
        page.insert_text(
            (72, 72),
            "Harshini G\nPython Developer\nFastAPI SQL Machine Learning"
        )
        pdf.save(file_path)

    return file_path


@pytest.fixture
def sample_docx(tmp_path):
    file_path = tmp_path / "sample.docx"

    document = Document()
    document.add_paragraph("Harshini G")
    document.add_paragraph("Python Developer")

    table = document.add_table(rows=1, cols=2)
    table.rows[0].cells[0].text = "Skills"
    table.rows[0].cells[1].text = "Python, FastAPI"

    document.save(file_path)
    return file_path


def test_extract_pdf_text(sample_pdf):
    text = extract_pdf_text(sample_pdf)

    assert "Harshini G" in text
    assert "Python Developer" in text
    assert "Machine Learning" in text


def test_extract_docx_text(sample_docx):
    text = extract_docx_text(sample_docx)

    assert "Harshini G" in text
    assert "Python Developer" in text
    assert "FastAPI" in text


def test_extract_resume_text_pdf(sample_pdf):
    text = extract_resume_text(sample_pdf)
    assert "Python Developer" in text


def test_extract_resume_text_docx(sample_docx):
    text = extract_resume_text(sample_docx)
    assert "FastAPI" in text


def test_unsupported_file_format(tmp_path):
    file_path = tmp_path / "resume.txt"
    file_path.write_text("Sample resume")

    with pytest.raises(ResumeParsingError):
        extract_resume_text(file_path)


def test_missing_file():
    with pytest.raises(ResumeParsingError):
        extract_resume_text("missing_resume.pdf")


def test_empty_pdf(tmp_path):
    file_path = tmp_path / "empty.pdf"

    with pymupdf.open() as pdf:
        pdf.new_page()
        pdf.save(file_path)

    with pytest.raises(ResumeParsingError):
        extract_pdf_text(file_path)


def test_empty_docx(tmp_path):
    file_path = tmp_path / "empty.docx"
    Document().save(file_path)

    with pytest.raises(ResumeParsingError):
        extract_docx_text(file_path)


def test_corrupted_pdf(tmp_path):
    file_path = tmp_path / "corrupted.pdf"
    file_path.write_text("This is not a valid PDF")

    with pytest.raises(ResumeParsingError):
        extract_pdf_text(file_path)