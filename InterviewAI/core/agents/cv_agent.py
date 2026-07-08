"""Module 1 — CV Parsing Agent. Extracts structured data from CV text/PDF."""

import fitz  # PyMuPDF
from core.llm import call_llm_json

PROMPT_TEMPLATE = """You are a professional CV parser. Extract structured data from this CV.

CV TEXT:
{cv_text}

Return JSON with:
- "name": candidate full name
- "email": email if present, else null
- "summary": one-sentence profile summary
- "skills": list of all technical and soft skills (strings)
- "experience": list of {{"title", "company", "duration", "highlights"}}
- "education": list of {{"degree", "institution", "year"}}
- "projects": list of {{"name", "technologies", "description"}}

Be thorough — extract every skill mentioned or implied."""


def parse_cv_text(cv_text: str) -> dict:
    """Parse CV from plain text."""
    if not cv_text.strip():
        raise ValueError("CV text is empty.")
    return call_llm_json(PROMPT_TEMPLATE.format(cv_text=cv_text))


def parse_cv_pdf(pdf_bytes: bytes) -> dict:
    """Parse CV from uploaded PDF bytes."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    if not text.strip():
        raise ValueError("Could not extract text from PDF. It may be image-based.")
    return parse_cv_text(text)
