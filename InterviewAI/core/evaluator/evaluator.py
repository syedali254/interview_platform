"""M6: Answer evaluation — LLM-as-Judge.

Every answer is scored by Gemini against a generated reference answer using a
four-criterion rubric (technical accuracy, completeness, clarity, relevance).

To mitigate the positional bias reported by Stureborg et al. (2024), each
answer is scored twice with the rubric criteria presented in a different
order, and the two scores are averaged. The spread between the two calls is
kept as a self-consistency signal: a wide spread means the judge was unstable
on that answer, so it is flagged for human review rather than reported as a
confident score.

The judge is the system's only answer scorer. A second, trained-classifier
track (S-BERT + XGBoost + SHAP) was implemented and then rejected: its
training labels were themselves LLM-generated, which made the intended
comparison circular, and the trained model scored a correct paraphrase of the
reference answer at 39/100. The evidence and the argument are recorded in
docs/track-b-rejection.md.
"""

from datetime import datetime

from core.config import (
    MIN_ANSWER_WORDS,
    SCORE_STRONG_THRESHOLD,
    SCORE_WEAK_THRESHOLD,
)
from core.llm import call_llm, call_llm_json

# Spread between the two rubric orderings, in points.
CONSISTENCY_HIGH = 8
CONSISTENCY_MODERATE = 16

CRITERIA = {
    "technical_accuracy": (
        "Is everything the candidate actually said correct? Deduct only for "
        "statements that are wrong, misleading or confused. Do NOT deduct for "
        "things they did not mention — omissions belong to completeness. A "
        "short answer containing nothing incorrect scores highly here."
    ),
    "completeness": (
        "Does the answer cover the essential points in the reference? Deduct "
        "only for genuinely important concepts that are missing. Do NOT "
        "penalise brevity or different wording — a focused 80 word answer "
        "hitting the core concepts scores higher than 200 words of filler."
    ),
    "clarity": "Is it clearly explained, well structured and easy to follow?",
    "relevance": "Does it directly address the question that was asked?",
}

# Two presentation orders. Averaging across them cancels the judge's tendency
# to over-weight whichever criterion it reads first.
CRITERIA_ORDERS = [
    ["technical_accuracy", "completeness", "clarity", "relevance"],
    ["clarity", "relevance", "technical_accuracy", "completeness"],
]

JUDGE_SYSTEM_PROMPT = (
    "You are a technical interviewer evaluating a candidate's spoken answer "
    "against a reference answer. The reference shows what a strong answer "
    "covers; it is not a script the candidate must reproduce.\n\n"
    "Scoring rules you must follow:\n"
    "- Score each of the four criteria independently. A weakness in one "
    "criterion must not drag down the others: an answer can be entirely "
    "accurate yet incomplete, or thorough yet unclear.\n"
    "- Judge the substance, not the phrasing. Different wording that conveys "
    "the same concept is fully credited.\n"
    "- This is speech, not writing. Ignore filler words, false starts and "
    "informal grammar unless they genuinely obscure the meaning.\n"
    "- Do not reward padding. Length is not a proxy for quality.\n"
    "- Clarity and relevance measure how well the candidate communicated a "
    "real answer. If the response contains essentially no substantive "
    "content, clarity and relevance must also be low — a candidate cannot "
    "clearly or relevantly explain nothing.\n"
    "- Do not inflate scores to be kind. An answer that demonstrates no "
    "understanding scores near zero.\n\n"
    "Interpreting the total (the sum of the four criteria):\n"
    "- 70-100: a genuinely strong answer covering the core concepts\n"
    "- 40-69: real but partial understanding, clearly incomplete or with "
    "some incorrect detail\n"
    "- 0-39: very weak, largely wrong, or showing minimal understanding\n\n"
    "Return only valid JSON, no explanation outside the JSON."
)


def generate_reference_answer(question: str, skill: str) -> str:
    """Generate the ideal answer the candidate's response is scored against."""
    prompt = (
        "You are a senior technical expert generating a reference answer for "
        "interview evaluation purposes.\n"
        "Write a concise ideal answer as a strong candidate would speak it in "
        "a real interview.\n"
        "Rules:\n"
        "- Cover essential points only, no padding\n"
        "- Maximum 100 words\n"
        "- Write conversationally as someone speaking\n"
        "- Do not write an exhaustive academic explanation\n"
        "- A strong interview answer is clear and concise, not lengthy\n"
        "Return only the answer text, no preamble.\n\n"
        f"Question: {question}\n"
        f"Skill being tested: {skill}\n\n"
        "Generate the ideal expert answer to this question."
    )
    return call_llm(prompt, temperature=0.1)


def _build_eval_prompt(question, skill, reference_answer, candidate_answer, order):
    lines = [
        "You are evaluating a candidate's answer to this interview question.\n",
        f"Question: {question}",
        f"Skill being tested: {skill}",
        f"Reference ideal answer: {reference_answer}",
        f"Candidate's answer: {candidate_answer}\n",
        "Score the candidate's answer on these 4 criteria (each 0-25):",
    ]
    for i, name in enumerate(order, 1):
        lines.append(f"{i}. {name} (0-25): {CRITERIA[name]}")
    lines += [
        "",
        "Return ONLY this JSON:",
        "{",
        '  "technical_accuracy": <score 0-25>,',
        '  "completeness": <score 0-25>,',
        '  "clarity": <score 0-25>,',
        '  "relevance": <score 0-25>,',
        '  "total": <sum of all 4 scores>,',
        '  "one_line_feedback": "<one sentence explaining the main strength or weakness>"',
        "}",
    ]
    return "\n".join(lines)


def _total(raw: dict) -> float:
    """Trust the criterion scores over the model's own arithmetic."""
    parts = [float(raw.get(name, 0) or 0) for name in CRITERIA]
    summed = sum(parts)
    stated = raw.get("total")
    if isinstance(stated, (int, float)) and abs(float(stated) - summed) <= 2:
        return float(stated)
    return summed


def judge_answer(question, candidate_answer, skill, reference_answer) -> dict:
    """Score one answer twice, under two rubric orderings, and average."""
    calls = []
    for order in CRITERIA_ORDERS:
        prompt = _build_eval_prompt(
            question, skill, reference_answer, candidate_answer, order
        )
        raw = call_llm_json(f"{JUDGE_SYSTEM_PROMPT}\n\n{prompt}", temperature=0.1)
        raw["_total"] = _total(raw)
        calls.append(raw)

    call_scores = [c["_total"] for c in calls]
    score = sum(call_scores) / len(call_scores)
    spread = abs(call_scores[0] - call_scores[1])

    if spread < CONSISTENCY_HIGH:
        consistency = "high"
    elif spread < CONSISTENCY_MODERATE:
        consistency = "moderate"
    else:
        consistency = "low"

    criterion_scores = {
        name: round(sum(float(c.get(name, 0) or 0) for c in calls) / len(calls), 1)
        for name in CRITERIA
    }

    feedback = " | ".join(
        c.get("one_line_feedback", "").strip()
        for c in calls if c.get("one_line_feedback")
    )

    return {
        "score": round(score, 1),
        "criterion_scores": criterion_scores,
        "feedback": feedback,
        "call_scores": [round(s, 1) for s in call_scores],
        "spread": round(spread, 1),
        "consistency": consistency,
        "method": "llm_as_judge",
    }


def evaluate_answer(question: str, candidate_answer: str, skill: str) -> dict:
    """Evaluate a single answer and return its score, verdict and rationale."""
    words = (candidate_answer or "").strip().split()

    if len(words) < MIN_ANSWER_WORDS:
        return {
            "skill": skill,
            "question": question,
            "candidate_answer": candidate_answer,
            "reference_answer": "",
            "final_score": 0.0,
            "verdict": "gap",
            "judge": None,
            "flagged": False,
            "note": "Answer too short to evaluate",
            "timestamp": datetime.now().isoformat(),
        }

    reference = generate_reference_answer(question, skill)
    judged = judge_answer(question, candidate_answer, skill, reference)
    score = judged["score"]

    if score >= SCORE_STRONG_THRESHOLD:
        verdict = "strong"
    elif score >= SCORE_WEAK_THRESHOLD:
        verdict = "weak"
    else:
        verdict = "gap"

    return {
        "skill": skill,
        "question": question,
        "candidate_answer": candidate_answer,
        "reference_answer": reference,
        "final_score": round(score, 1),
        "verdict": verdict,
        "judge": judged,
        # An unstable judge is not a confident score — send it to a human.
        "flagged": judged["consistency"] == "low",
        "timestamp": datetime.now().isoformat(),
    }
