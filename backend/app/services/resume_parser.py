
from pathlib import Path

import pymupdf
from docx import Document


SUPPORTED_EXTENSIONS = {".pdf", ".docx"}


class ResumeParsingError(Exception):
    """Raised when a resume cannot be parsed."""


def extract_pdf_text(file_path: str | Path) -> str:
    """Extract text from a PDF resume."""
    try:
        with pymupdf.open(file_path) as pdf:
            text = "\n".join(page.get_text() for page in pdf)

        if not text.strip():
            raise ResumeParsingError(
                "PDF contains no extractable text."
            )

        return text.strip()

    except ResumeParsingError:
        raise
    except Exception as exc:
        raise ResumeParsingError(
            f"Unable to read PDF: {exc}"
        ) from exc


def extract_docx_text(file_path: str | Path) -> str:
    """Extract paragraphs and table content from a DOCX resume."""
    try:
        document = Document(file_path)

        paragraphs = [
            paragraph.text.strip()
            for paragraph in document.paragraphs
            if paragraph.text.strip()
        ]

        table_text = []
        for table in document.tables:
            for row in table.rows:
                cells = [
                    cell.text.strip()
                    for cell in row.cells
                    if cell.text.strip()
                ]
                if cells:
                    table_text.append(" | ".join(cells))

        text = "\n".join(paragraphs + table_text)

        if not text.strip():
            raise ResumeParsingError(
                "DOCX contains no extractable text."
            )

        return text.strip()

    except ResumeParsingError:
        raise
    except Exception as exc:
        raise ResumeParsingError(
            f"Unable to read DOCX: {exc}"
        ) from exc


def extract_resume_text(file_path: str | Path) -> str:
    """Extract text based on the resume file extension."""
    path = Path(file_path)

    if not path.is_file():
        raise ResumeParsingError("Resume file does not exist.")

    extension = path.suffix.lower()

    if extension == ".pdf":
        return extract_pdf_text(path)

    if extension == ".docx":
        return extract_docx_text(path)

    raise ResumeParsingError(
        f"Unsupported file format: {extension or 'unknown'}"
    )
