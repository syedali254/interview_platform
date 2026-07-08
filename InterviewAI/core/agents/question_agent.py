"""Module 4 + M8 — Question Generator Agent.

M4:  Generates full interview question set from skill graph topics (static).
M8:  Generates position-aware questions on the fly during live interview.
"""

from core.llm import call_llm, call_llm_json


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


def generate_position_question(
    skill: str,
    difficulty: str = "medium",
    cv_data: dict = None,
    jd_data: dict = None,
    is_follow_up: bool = False,
) -> str:
    """Generate a single position-aware question for a given skill on the fly."""
    job_title = (jd_data or {}).get("job_title", "the role")
    role_level = (jd_data or {}).get("role_level", "mid")
    cv_skills = ", ".join((cv_data or {}).get("skills", [])[:10])

    q_type = "follow-up" if is_follow_up else "main"
    prompt = f"""You are a senior technical interviewer for a {role_level} {job_title} position.

Candidate's known skills: {cv_skills}

Generate ONE {q_type} {difficulty}-difficulty interview question testing the skill: "{skill}".

Rules:
- Be conversational, not robotic
- Require explanation, not yes/no
- Match {role_level} level
- Max 2 sentences
{"- This is a follow-up — probe deeper into a previous answer, ask for an example" if is_follow_up else "- This is the first question on this skill — ask a broad question to gauge depth"}
Return ONLY the question text, no preamble or label."""

    return call_llm(prompt, temperature=0.3)


def build_interview_flow(questions: dict) -> list:
    """Build a flat ordered list of all questions for the interview session."""
    flow = []

    for q in questions.get("opening", []):
        flow.append({"type": "opening", "question": q["question"],
                     "purpose": q.get("purpose", ""), "duration": q.get("expected_duration_mins", 2)})

    for q in questions.get("technical", []):
        flow.append({"type": "technical", "question": q["question"],
                     "skill": q.get("skill", ""), "difficulty": q.get("difficulty", "medium"),
                     "follow_up": q.get("follow_up", ""), "duration": q.get("expected_duration_mins", 3)})

    for q in questions.get("behavioural", []):
        flow.append({"type": "behavioural", "question": q["question"],
                     "competency": q.get("competency", ""), "follow_up": q.get("follow_up", ""),
                     "duration": q.get("expected_duration_mins", 3)})

    for q in questions.get("closing", []):
        flow.append({"type": "closing", "question": q["question"],
                     "purpose": q.get("purpose", ""), "duration": 2})

    return flow
