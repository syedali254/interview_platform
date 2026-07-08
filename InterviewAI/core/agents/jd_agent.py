"""Module 2 — Job Description Agent. Extracts requirements from a JD."""

from core.llm import call_llm_json

PROMPT_TEMPLATE = """You are a job description analyst. Extract structured requirements.

JOB DESCRIPTION:
{jd_text}

Return JSON with:
- "job_title": role title
- "company": company name if mentioned, else null
- "required_skills": list of mandatory skills (strings)
- "nice_to_have": list of preferred/bonus skills (strings)
- "responsibilities": list of key duties (strings)
- "role_level": one of "junior", "mid", "senior", "lead"
- "domain": industry domain (e.g. "fintech", "healthcare", "e-commerce")
- "experience_years": estimated years needed (integer)

Only include skills explicitly stated or strongly implied."""


def parse_job_description(jd_text: str) -> dict:
    """Parse job description text into structured requirements."""
    if not jd_text.strip():
        raise ValueError("Job description text is empty.")
    return call_llm_json(PROMPT_TEMPLATE.format(jd_text=jd_text))
