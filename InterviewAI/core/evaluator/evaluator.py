"""M6: Core evaluation module — Track A LLM-as-Judge."""

from datetime import datetime

from core.config import SCORE_STRONG_THRESHOLD, SCORE_WEAK_THRESHOLD
from core.llm import call_llm, call_llm_json


def generate_reference_answer(question: str, skill: str) -> str:
    prompt = (
        "You are a senior technical expert generating a "
        "reference answer for interview evaluation purposes.\n"
        "Write a concise ideal answer as a strong candidate "
        "would speak it in a real interview.\n"
        "Rules:\n"
        "- Cover essential points only, no padding\n"
        "- Maximum 100 words\n"
        "- Write conversationally as someone speaking\n"
        "- Do not write an exhaustive academic explanation\n"
        "- A strong interview answer is clear and concise "
        "not lengthy and exhaustive\n"
        "Return only the answer text, no preamble."
    )
    user = f"Question: {question}\nSkill being tested: {skill}\n\nGenerate the ideal expert answer to this question."
    full_prompt = f"{prompt}\n\n{user}"
    return call_llm(full_prompt, temperature=0.1)


def _build_eval_prompt(question, skill, reference_answer, candidate_answer, criteria):
    lines = [
        f"You are evaluating a candidate's answer to this interview question.\n",
        f"Question: {question}",
        f"Skill being tested: {skill}",
        f"Reference ideal answer: {reference_answer}",
        f"Candidate's answer: {candidate_answer}\n",
        f"Score the candidate's answer on these 4 criteria (each 0-25):",
    ]
    for i, (name, desc) in enumerate(criteria, 1):
        lines.append(f"{i}. {name} (0-25): {desc}")
    lines.append("")
    lines.append('Return ONLY this JSON:')
    lines.append('{')
    lines.append('  "technical_accuracy": <score 0-25>,')
    lines.append('  "completeness": <score 0-25>,')
    lines.append('  "clarity": <score 0-25>,')
    lines.append('  "relevance": <score 0-25>,')
    lines.append('  "total": <sum of all 4 scores>,')
    lines.append('  "one_line_feedback": "<one sentence explaining the main strength or weakness>"')
    lines.append('}')
    return "\n".join(lines)


def track_a_evaluate(question, candidate_answer, skill, reference_answer):
    system = (
        "You are a strict technical interviewer evaluating a candidate's answer "
        "against an ideal reference answer.\n\n"
        "Scoring rules you must follow:\n"
        "- Compare the candidate's answer directly against the reference answer\n"
        "- If candidate answer is significantly shorter or less detailed "
        "than the reference -> completeness score must be below 15/25\n"
        "- If candidate answer is missing key technical points from the "
        "reference -> technical_accuracy must be below 15/25\n"
        "- A score of 70+ means the answer is genuinely strong and covers "
        "most points in the reference answer\n"
        "- A score of 40-69 means the answer shows basic understanding "
        "but is clearly incomplete or partially incorrect\n"
        "- A score below 40 means the answer is very weak, wrong, or "
        "shows minimal understanding\n"
        "- Do not inflate scores to be kind\n"
        "- A short answer that misses key technical points cannot score "
        "above 65 regardless of what it gets right\n"
        "- Always compare length and depth of candidate answer vs "
        "reference answer before scoring completeness\n"
        "Return only valid JSON, no explanation outside the JSON."
    )

    criteria_order_1 = [
        ("technical_accuracy", "Is the information technically correct?"),
        ("completeness", "completeness (0-25): Does the answer cover the essential points needed to demonstrate genuine understanding? Award full marks for concise answers that hit the key concepts. Do NOT penalize for brevity — a focused 80 word answer covering core concepts scores higher than a 200 word answer with filler. Only deduct points if genuinely important concepts are completely missing."),
        ("clarity", "Is it clearly explained and easy to follow?"),
        ("relevance", "Does it directly address what was asked?"),
    ]
    criteria_order_2 = [
        ("clarity", "Is it clearly explained and easy to follow?"),
        ("relevance", "Does it directly address what was asked?"),
        ("technical_accuracy", "Is the information technically correct?"),
        ("completeness", "completeness (0-25): Does the answer cover the essential points needed to demonstrate genuine understanding? Award full marks for concise answers that hit the key concepts. Do NOT penalize for brevity — a focused 80 word answer covering core concepts scores higher than a 200 word answer with filler. Only deduct points if genuinely important concepts are completely missing."),
    ]

    def run_eval(criteria_order):
        user = _build_eval_prompt(question, skill, reference_answer, candidate_answer, criteria_order)
        full = f"{system}\n\n{user}"
        return call_llm_json(full, temperature=0.1)

    raw1 = run_eval(criteria_order_1)
    raw2 = run_eval(criteria_order_2)

    score1 = raw1["total"]
    score2 = raw2["total"]
    avg_score = (score1 + score2) / 2.0

    criterion_scores = {}
    for key in ["technical_accuracy", "completeness", "clarity", "relevance"]:
        criterion_scores[key] = (raw1.get(key, 0) + raw2.get(key, 0)) / 2.0

    feedback = f"Call 1: {raw1.get('one_line_feedback', '')} | Call 2: {raw2.get('one_line_feedback', '')}"

    return {
        "score": avg_score,
        "criterion_scores": criterion_scores,
        "feedback": feedback,
        "raw_call_1": raw1,
        "raw_call_2": raw2,
        "method": "llm_as_judge",
    }


def evaluate_answer(question: str, candidate_answer: str, skill: str) -> dict:
    words = candidate_answer.strip().split()
    if len(words) < 10:
        return {
            "skill": skill,
            "question": question,
            "candidate_answer": candidate_answer,
            "reference_answer": "",
            "final_score": 0.0,
            "verdict": "gap",
            "track_a": None,
            "flagged": False,
            "timestamp": datetime.now().isoformat(),
        }

    reference = generate_reference_answer(question, skill)
    track_a_result = track_a_evaluate(question, candidate_answer, skill, reference)
    final_score = track_a_result["score"]

    if final_score >= SCORE_STRONG_THRESHOLD:
        verdict = "strong"
    elif final_score >= SCORE_WEAK_THRESHOLD:
        verdict = "weak"
    else:
        verdict = "gap"

    return {
        "skill": skill,
        "question": question,
        "candidate_answer": candidate_answer,
        "reference_answer": reference,
        "final_score": final_score,
        "verdict": verdict,
        "track_a": track_a_result,
        "flagged": False,
        "timestamp": datetime.now().isoformat(),
    }
