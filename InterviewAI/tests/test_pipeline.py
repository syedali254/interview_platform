"""Integration test — verifies the complete pipeline works."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.agents.cv_agent import parse_cv_text
from core.agents.jd_agent import parse_job_description
from core.graph.skill_graph import build_graph


SAMPLE_CV = """
Sarah Khan — Full Stack Developer | London
Skills: Python, JavaScript, React, Node.js, PostgreSQL, Docker, AWS, Git,
REST APIs, TypeScript, MongoDB, Redis, CI/CD, Pandas, Machine Learning basics

Experience:
- Software Developer at DataFlow Ltd (2021-Present): Built microservices with FastAPI
- Junior Developer at WebCraft (2019-2021): React frontend development

Education: BSc Computer Science, University of Manchester, 2019
Projects: Task Manager (React + Node.js), Stock Predictor (Python + scikit-learn)
"""

SAMPLE_JD = """
Backend Engineer — Requirements:
- 3+ years Python backend experience
- PostgreSQL and database design
- Docker and Kubernetes
- Microservices architecture
- Kafka or RabbitMQ
- CI/CD pipelines
- AWS or GCP
Nice to have: Go, Terraform, GraphQL
"""


def main():
    print("\n[M1] CV Agent...")
    cv = parse_cv_text(SAMPLE_CV)
    assert len(cv.get("skills", [])) > 5
    print(f"     => {len(cv['skills'])} skills parsed")

    print("[M2] JD Agent...")
    jd = parse_job_description(SAMPLE_JD)
    assert len(jd.get("required_skills", [])) > 3
    print(f"     => {len(jd['required_skills'])} requirements found")

    print("[M3] Skill Graph...")
    sg = build_graph(cv, jd)
    gaps = sg.analyse_gaps()
    topics = sg.get_interview_topics()
    print(f"     => Match: {gaps['match_percentage']}% | Topics: {len(topics)}")

    print("\n[OK] All modules working.\n")


if __name__ == "__main__":
    main()
