"""Module 4 — Question Generator Agent.

Generates the interview question set from the skill-graph topics, then orders
it so the highest-priority skill gaps are probed first.
"""

from core.llm import call_llm_json


def generate_interview_questions(topics: list, cv_data: dict, jd_data: dict) -> dict:
    """Generate a full interview question set from skill graph topics."""
    candidate_name = cv_data.get("name", "the candidate")
    job_title = jd_data.get("job_title", "the role")
    role_level = jd_data.get("role_level", "mid")

    topic_lines = []
    for t in topics:
        topic_lines.append(f"- {t['skill']} ({t['priority']} priority): {t['reason']}")
    topics_text = "\n".join(topic_lines)

    skills_text = ", ".join(cv_data.get("skills", [])[:15])

    prompt = f"""You are a senior technical interviewer preparing questions for a {role_level}-level 
{job_title} position.

CANDIDATE PROFILE:
- Name: {candidate_name}
- Key Skills: {skills_text}

INTERVIEW TOPICS (from skill gap analysis):
{topics_text}

Generate a structured interview question set. Return JSON with:

{{
    "opening": [
        {{
            "question": "...",
            "purpose": "warm-up / rapport building",
            "expected_duration_mins": 2
        }}
    ],
    "technical": [
        {{
            "question": "...",
            "skill": "the skill being tested",
            "difficulty": "easy|medium|hard",
            "follow_up": "a follow-up probe if answer is good",
            "expected_duration_mins": 3
        }}
    ],
    "behavioural": [
        {{
            "question": "...",
            "competency": "what it tests (e.g. problem-solving, teamwork)",
            "follow_up": "...",
            "expected_duration_mins": 3
        }}
    ],
    "closing": [
        {{
            "question": "...",
            "purpose": "closing / candidate questions"
        }}
    ]
}}

RULES:
- Generate 2 opening questions (brief warm-up)
- Generate 2-3 technical questions per HIGH priority topic
- Generate 1-2 technical questions per MEDIUM priority topic
- Generate 3 behavioural questions total (STAR format)
- Generate 2 closing questions
- Questions should be conversational, not robotic
- Difficulty should match {role_level} level
- Technical questions should require explanation, not just yes/no
- Total interview should be 25-35 minutes"""

    result = call_llm_json(prompt)

    result["total_questions"] = (
        len(result.get("opening", [])) +
        len(result.get("technical", [])) +
        len(result.get("behavioural", [])) +
        len(result.get("closing", []))
    )

    total_mins = 0
    for q in result.get("opening", []):
        total_mins += q.get("expected_duration_mins", 2)
    for q in result.get("technical", []):
        total_mins += q.get("expected_duration_mins", 3)
    for q in result.get("behavioural", []):
        total_mins += q.get("expected_duration_mins", 3)
    for q in result.get("closing", []):
        total_mins += 2
    result["estimated_duration_mins"] = total_mins

    return result


PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}


def build_interview_flow(questions: dict, topics: list = None) -> list:
    """Flatten the question set into the order the interview should follow.

    Technical questions are ordered by the priority the skill graph assigned
    to their skill, so the questions that probe genuine gaps are asked while
    there is still time budget left. This is the graph-traversal step of
    Objective 2: question targeting is driven by the graph, not by the order
    the LLM happened to emit.
    """
    priority_by_skill = {
        t["skill"].lower(): PRIORITY_RANK.get(t.get("priority", "medium"), 1)
        for t in (topics or []) if t.get("skill")
    }

    def technical_rank(question: dict) -> tuple:
        skill = (question.get("skill") or "").lower()
        # Unknown skills sort after graph-derived ones but before nothing.
        return (priority_by_skill.get(skill, 1.5), skill)

    flow = []

    for q in questions.get("opening", []):
        flow.append({"type": "opening", "question": q["question"],
                     "purpose": q.get("purpose", ""),
                     "duration": q.get("expected_duration_mins", 2)})

    for q in sorted(questions.get("technical", []), key=technical_rank):
        skill = q.get("skill", "")
        flow.append({"type": "technical", "question": q["question"],
                     "skill": skill,
                     "priority": next(
                         (t.get("priority") for t in (topics or [])
                          if t.get("skill", "").lower() == skill.lower()),
                         "medium",
                     ),
                     "difficulty": q.get("difficulty", "medium"),
                     "follow_up": q.get("follow_up", ""),
                     "duration": q.get("expected_duration_mins", 3)})

    for q in questions.get("behavioural", []):
        flow.append({"type": "behavioural", "question": q["question"],
                     "competency": q.get("competency", ""),
                     "follow_up": q.get("follow_up", ""),
                     "duration": q.get("expected_duration_mins", 3)})

    for q in questions.get("closing", []):
        flow.append({"type": "closing", "question": q["question"],
                     "purpose": q.get("purpose", ""), "duration": 2})

    return flow
