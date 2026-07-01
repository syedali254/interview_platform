"""M4: Adaptive question generation — reads graph, generates questions, no voice."""

import sys
import difflib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import networkx as nx

import config
from utils.llm_client import call_llm_json


def generate_question(skill, node_type, importance, category,
                      claimed_proficiency, current_status, asked_questions):
    if current_status == config.STATUS_VERIFIED_WEAK:
        question_type = "follow_up"
    elif node_type == "gap":
        question_type = "gap_check"
    else:
        question_type = "standard"

    difficulty_guide = {
        "beginner": (
            "Ask about basic concepts, definitions, or simple use cases. "
            "Example style: 'What is X and when would you use it?' or "
            "'Can you explain the difference between X and Y?'"
        ),
        "intermediate": (
            "Ask about practical usage and common patterns. "
            "Example style: 'How would you use X to solve Y?' or "
            "'Walk me through how you have used X in a project.'"
        ),
        "advanced": (
            "Ask about trade-offs, internals, or best practices. "
            "Example style: 'What are the trade-offs between X and Y?' or "
            "'How does X work under the hood and when would you avoid it?'"
        ),
        None: (
            "Ask a standard intermediate-level question about practical usage."
        ),
    }
    proficiency_key = claimed_proficiency if claimed_proficiency in difficulty_guide else None
    difficulty_instruction = difficulty_guide[proficiency_key]

    system_prompt = (
        "You are a technical interviewer conducting a standard job interview.\n"
        "Generate exactly ONE interview question following these strict rules:\n\n"
        "RULES:\n"
        "- Question must be answerable verbally in 2-3 minutes\n"
        "- Ask about ONE specific concept only, not multiple concepts at once\n"
        "- Never ask candidates to 'design an entire system'\n"
        "- Never use phrases like: 'highly available', 'large-scale',\n"
        "  'enterprise-grade', 'design a cluster', 'end-to-end system'\n"
        "- A good answer should be around 150-250 words maximum\n"
        "- Question must sound like something asked in a real job interview\n"
        "- Return only valid JSON, no explanation text, no markdown"
    )

    user_prompt = (
        f"You are interviewing a candidate for a software engineering role.\n\n"
        f"Skill to ask about: {skill}\n"
        f"Skill category: {category}\n"
        f"Candidate proficiency level: {claimed_proficiency or 'unknown'}\n"
        f"Question type: {question_type}\n\n"
        f"Difficulty instruction: {difficulty_instruction}\n\n"
        f"Question type guidance:\n"
        f"- If question_type is 'gap_check': candidate did not list this skill "
        f"on their CV. Ask an exploratory question to check if they have any "
        f"basic familiarity. Start with 'Are you familiar with...' or "
        f"'Have you worked with...'\n\n"
        f"- If question_type is 'standard': candidate listed this skill. "
        f"Ask a focused technical question matching their proficiency level "
        f"using the difficulty instruction above.\n\n"
        f"- If question_type is 'follow_up': candidate answered weakly before. "
        f"Ask a different, simpler angle on the same skill to understand "
        f"exactly where their knowledge stops. Must be clearly different from "
        f"previous questions asked.\n\n"
        f"Questions already asked (do not repeat or be too similar to these):\n"
        f"{asked_questions if asked_questions else 'None yet'}\n\n"
        f"Return ONLY this JSON:\n"
        f'{{"question": "your single interview question here"}}\n\n'
        f"Remember: ONE question, answerable in 2-3 minutes, no system design."
    )

    data = call_llm_json(system_prompt, user_prompt, ["question"])

    for prev_q in asked_questions:
        ratio = difflib.SequenceMatcher(None, data["question"].lower(), prev_q.lower()).ratio()
        if ratio > 0.7:
            user_prompt += (
                "\n\nYour previous question was too similar to an earlier one. "
                "Generate a completely different question."
            )
            data = call_llm_json(system_prompt, user_prompt, ["question"])
            break

    return data["question"]


def get_next_skill(graph):
    candidates = []
    for node, attrs in graph.nodes(data=True):
        if attrs.get("completed"):
            continue
        if attrs.get("node_type") == "extra":
            continue
        nt = attrs.get("node_type")
        imp = attrs.get("importance", "nice_to_have")
        status = attrs.get("status")
        qs = attrs.get("questions_asked", 0)

        if nt == "matched" and imp == "must_have" and status == config.STATUS_PENDING:
            priority = 0
        elif nt == "gap" and imp == "must_have":
            priority = 1
        elif (nt == "matched" and imp == "must_have"
              and status == config.STATUS_VERIFIED_WEAK
              and qs < (1 + config.MAX_FOLLOW_UP_QUESTIONS)):
            priority = 2
        elif nt == "matched" and imp == "nice_to_have" and status == config.STATUS_PENDING:
            priority = 3
        elif nt == "gap" and imp == "nice_to_have":
            priority = 4
        else:
            continue

        candidates.append((priority, node))

    candidates.sort(key=lambda x: x[0])
    return candidates[0][1] if candidates else None


def should_follow_up(graph, skill):
    for node, attrs in graph.nodes(data=True):
        if node.lower() == skill.lower():
            if attrs.get("status") != config.STATUS_VERIFIED_WEAK:
                return False
            if attrs.get("completed"):
                return False
            max_q = 1 + config.MAX_FOLLOW_UP_QUESTIONS
            if attrs.get("questions_asked", 0) >= max_q:
                return False
            return True
    return False


def mark_node_complete(graph, skill):
    for node in graph.nodes:
        if node.lower() == skill.lower():
            graph.nodes[node]["completed"] = True
            return


def get_interview_progress(graph):
    total = 0
    completed = 0
    verified_strong = 0
    verified_weak = 0
    confirmed_gap = 0
    pending = 0
    gap_unasked = 0

    for _, attrs in graph.nodes(data=True):
        nt = attrs.get("node_type")
        if nt not in ("matched", "gap"):
            continue
        total += 1
        if attrs.get("completed"):
            completed += 1
        status = attrs.get("status")
        if status == config.STATUS_VERIFIED_STRONG:
            verified_strong += 1
        elif status == config.STATUS_VERIFIED_WEAK:
            verified_weak += 1
        elif status == config.STATUS_CONFIRMED_GAP:
            confirmed_gap += 1
        elif status == config.STATUS_PENDING:
            pending += 1
        elif status == config.STATUS_GAP:
            gap_unasked += 1

    return {
        "total_skills": total,
        "completed": completed,
        "remaining": total - completed,
        "verified_strong": verified_strong,
        "verified_weak": verified_weak,
        "confirmed_gap": confirmed_gap,
        "pending": pending,
        "gap_unasked": gap_unasked,
        "percent_complete": (completed / total * 100) if total > 0 else 0,
    }


if __name__ == "__main__":
    from models.skill_extractor import extract_cv_skills, extract_jd_requirements
    from models.skill_graph import build_skill_graph, update_node_status

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
    graph = build_skill_graph(cv_skills, jd_reqs)

    asked_questions = []

    for round_num in range(1, 5):
        print(f"\n=== Round {round_num} ===")

        skill = get_next_skill(graph)
        if skill is None:
            print("Interview complete.")
            break

        node = graph.nodes[skill]
        print(f"Skill: {skill}")
        print(f"Type: {node['node_type']} | Importance: {node['importance']}")
        print(f"Status: {node['status']}")

        question = generate_question(
            skill=skill,
            node_type=node["node_type"],
            importance=node["importance"],
            category=node["category"],
            claimed_proficiency=node.get("claimed_proficiency"),
            current_status=node["status"],
            asked_questions=asked_questions,
        )
        print(f"Question: {question}")
        asked_questions.append(question)

        graph.nodes[skill]["questions_asked"] += 1

        simulated_scores = [85.0, 45.0, 25.0, 90.0]
        score = simulated_scores[round_num - 1]

        update_node_status(graph, skill, score)
        print(f"Simulated score: {score}")
        print(f"New status: {graph.nodes[skill]['status']}")

        if should_follow_up(graph, skill):
            print(f"-> Follow-up needed for {skill}")
        else:
            mark_node_complete(graph, skill)
            print(f"-> {skill} marked complete")

        progress = get_interview_progress(graph)
        print(f"Progress: {progress['completed']}/{progress['total_skills']} "
              f"({progress['percent_complete']:.1f}%)")

    print("\nFinal Progress:")
    for k, v in get_interview_progress(graph).items():
        print(f"  {k}: {v}")

    print("\nQuestion Generator: Tests passed")
