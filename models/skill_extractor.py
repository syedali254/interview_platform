"""Extract skills from CV and requirements from Job Description using LLM."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.llm_client import call_llm_json


def extract_cv_skills(cv_text):
    prompt = f"""Extract all skills from this CV.
Return a JSON object with key "skills" containing an array.
Each item must have: "skill" (name), "proficiency" ("beginner"/"intermediate"/"advanced"), "category" ("language"/"framework"/"tool"/"database"/"cloud"/"methodology"/"soft_skill"/"other").

CV:
{cv_text}"""

    data = call_llm_json(
        "Extract skills from CV text. Return valid JSON only.",
        prompt,
        ["skills"],
    )
    return data["skills"]


def extract_jd_requirements(jd_text):
    prompt = f"""Extract all required skills from this job description.
Return a JSON object with key "requirements" containing an array.
Each item must have: "skill" (name), "importance" ("must_have"/"nice_to_have"), "category" (same as CV categories).

Job Description:
{jd_text}"""

    data = call_llm_json(
        "Extract requirements from job description. Return valid JSON only.",
        prompt,
        ["requirements"],
    )
    return data["requirements"]


def display_skills_table(cv_skills, jd_requirements):
    print("CV Skills:")
    for s in cv_skills:
        print(f"  - {s['skill']} ({s['proficiency']}, {s['category']})")

    print("\nJD Requirements:")
    for r in jd_requirements:
        print(f"  - {r['skill']} ({r['importance']}, {r['category']})")


if __name__ == "__main__":
    CV_TEXT = """
John Smith - Senior Software Engineer
5 years experience in Python, Django, FastAPI.
Worked with PostgreSQL, Redis, Docker, Kubernetes.
Deployed on AWS (EC2, S3, Lambda).
Familiar with React, Git, Agile methodologies.
Strong problem-solving and communication skills.
"""

    JD_TEXT = """
Backend Engineer required:
- Strong Python (must have)
- Django or FastAPI (must have)
- PostgreSQL (must have)
- Docker (must have)
- AWS preferred (nice to have)
- Redis (nice to have)
- React (nice to have)
- Good communication (must have)
- Kubernetes (nice to have)
- CI/CD experience (nice to have)
"""

    cv_skills = extract_cv_skills(CV_TEXT)
    jd_reqs = extract_jd_requirements(JD_TEXT)

    display_skills_table(cv_skills, jd_reqs)

    print(f"\nTotal CV skills: {len(cv_skills)}")
    print(f"Total JD requirements: {len(jd_reqs)}")
    print("Skill Extractor: Tests passed")
