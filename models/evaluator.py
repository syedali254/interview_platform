"""M6: Core evaluation module — Track A LLM-as-Judge. Track B placeholder for V2."""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
from utils.llm_client import call_llm, call_llm_json


def generate_reference_answer(question, skill):
    prompt = (
        f"You are a senior technical expert. Generate a concise, accurate "
        f"ideal answer to the interview question provided. The answer should:\n"
        f"- Be technically accurate and complete\n"
        f"- Be 150-250 words maximum\n"
        f"- Cover the key points an expert would mention\n"
        f"- Be written as if a strong candidate is speaking\n"
        f"Return only the answer text, no preamble, no explanation."
    )
    user = f"Question: {question}\nSkill being tested: {skill}\n\nGenerate the ideal expert answer to this question."
    return call_llm(prompt, user, temperature=0.1)


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
        ("completeness", "Does it cover the key points of the question?"),
        ("clarity", "Is it clearly explained and easy to follow?"),
        ("relevance", "Does it directly address what was asked?"),
    ]
    criteria_order_2 = [
        ("clarity", "Is it clearly explained and easy to follow?"),
        ("relevance", "Does it directly address what was asked?"),
        ("technical_accuracy", "Is the information technically correct?"),
        ("completeness", "Does it cover the key points of the question?"),
    ]

    required = ["technical_accuracy", "completeness", "clarity", "relevance", "total", "one_line_feedback"]

    def run_eval(criteria_order):
        user = _build_eval_prompt(question, skill, reference_answer, candidate_answer, criteria_order)
        return call_llm_json(system, user, required, temperature=0.1)

    raw1 = run_eval(criteria_order_1)
    raw2 = run_eval(criteria_order_2)

    score1 = raw1["total"]
    score2 = raw2["total"]
    avg_score = (score1 + score2) / 2.0

    print(f"  Call 1 score: {score1} | Call 2 score: {score2} | Averaged: {avg_score:.1f}")

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


def evaluate_answer(question, candidate_answer, skill):
    words = candidate_answer.strip().split()
    if len(words) < 10:
        now = datetime.now().isoformat()
        return {
            "skill": skill,
            "question": question,
            "candidate_answer": candidate_answer,
            "reference_answer": "",
            "final_score": 0.0,
            "verdict": "gap",
            "track_a": None,
            "track_b": None,
            "flagged": False,
            "timestamp": now,
        }

    reference = generate_reference_answer(question, skill)
    track_a_result = track_a_evaluate(question, candidate_answer, skill, reference)
    final_score = track_a_result["score"]

    if final_score >= config.SCORE_STRONG_THRESHOLD:
        verdict = "strong"
    elif final_score >= config.SCORE_WEAK_THRESHOLD:
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
        "track_b": None,
        "flagged": False,
        "timestamp": datetime.now().isoformat(),
    }


def get_score_label(score):
    if score >= config.SCORE_STRONG_THRESHOLD:
        return "Strong"
    elif score >=config.SCORE_WEAK_THRESHOLD:
        return "Needs Improvement"
    return "Significant Gap"


if __name__ == "__main__":
    TEST_CASES = [
        {
            "skill": "Python",
            "question": "What are the trade-offs between using threading and multiprocessing in Python for CPU-bound tasks?",
            "expected": "strong",
            "candidate_answer": """
            In Python, the GIL (Global Interpreter Lock) prevents
            multiple threads from executing Python bytecode simultaneously.
            This means threading is not effective for CPU-bound tasks
            because threads cannot run in true parallel on multiple cores.
            For CPU-bound work, multiprocessing is better because each
            process has its own Python interpreter and GIL, allowing
            true parallelism across CPU cores. However multiprocessing
            has higher memory overhead since each process gets its own
            memory space. Threading is still useful for I/O-bound tasks
            where threads spend time waiting for network or disk operations,
            and the GIL is released during I/O waits.
            """,
        },
        {
            "skill": "Django",
            "question": "How would you use Django signals in a project and when would you avoid them?",
            "expected": "weak",
            "candidate_answer": """
            Django signals are used to send notifications when something
            happens in the application. You can use post_save signal to
            do something after a model is saved. I have used them to send
            emails after user registration. Sometimes they can make code
            hard to debug because the signal handler runs separately from
            the main code flow.
            """,
        },
        {
            "skill": "FastAPI",
            "question": "Are you familiar with FastAPI? Can you explain what it is used for?",
            "expected": "gap",
            "candidate_answer": """
            I think FastAPI is some kind of web framework.
            I have not used it much but I believe it is used
            for building APIs. That is all I know about it.
            """,
        },
    ]

    for case in TEST_CASES:
        print(f"\n{'=' * 50}")
        print(f"Testing: {case['skill']} (expected: {case['expected']})")
        print(f"Question: {case['question'][:80]}...")
        print(f"Candidate Answer: {case['candidate_answer'].strip()[:100]}...")

        result = evaluate_answer(
            question=case["question"],
            candidate_answer=case["candidate_answer"].strip(),
            skill=case["skill"],
        )

        print(f"\nReference Answer Preview: {result['reference_answer'][:150]}...")
        print(f"\nTrack A Results:")
        print(f"  Score: {result['final_score']:.1f}/100")
        print(f"  Verdict: {result['verdict']}")
        print(f"  Label: {get_score_label(result['final_score'])}")
        print(f"  Technical Accuracy: {result['track_a']['criterion_scores']['technical_accuracy']:.1f}/25")
        print(f"  Completeness: {result['track_a']['criterion_scores']['completeness']:.1f}/25")
        print(f"  Clarity: {result['track_a']['criterion_scores']['clarity']:.1f}/25")
        print(f"  Relevance: {result['track_a']['criterion_scores']['relevance']:.1f}/25")
        print(f"  Feedback: {result['track_a']['feedback']}")
        print(f"  Expected verdict: {case['expected']}")

        if result["verdict"] == case["expected"]:
            print(f"  VERDICT CHECK: PASS")
        else:
            print(f"  VERDICT CHECK: FAIL (got {result['verdict']}, expected {case['expected']})")

    print("\nEvaluator: All tests complete")
