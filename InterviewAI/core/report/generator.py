"""M11-M12: Final interview report generator.

Produces a structured report with:
  - Overall score and verdict
  - Per-skill breakdown (score, verdict, feedback)
  - Strength/gap analysis
  - Recommendation
"""

from datetime import datetime
from typing import Optional

from core.config import SCORE_STRONG_THRESHOLD, SCORE_WEAK_THRESHOLD
from core.pipeline.interview_loop import InterviewLoop


def generate_report(loop: InterviewLoop) -> dict:
    summary = loop.get_summary()
    state_summary = summary["state"]
    answers = summary["answer_history"]

    # Compute overall score
    scores = [a["score"] for a in answers]
    overall_score = sum(scores) / len(scores) if scores else 0.0

    # Per-skill breakdown
    skill_breakdown = []
    for skill_name, node_info in state_summary["skills"].items():
        skill_answers = [a for a in answers if a["skill"] == skill_name]
        skill_breakdown.append({
            "skill": skill_name,
            "status": node_info["status"],
            "avg_score": round(node_info["avg_score"], 1),
            "best_score": round(node_info["best_score"], 1),
            "questions_answered": node_info["questions_asked"],
            "feedback": [a.get("track_a", {}).get("feedback", "") for a in skill_answers],
        })

    # Verdict
    if overall_score >= SCORE_STRONG_THRESHOLD:
        verdict = "strong_hire"
        label = "Strong Hire"
    elif overall_score >= SCORE_WEAK_THRESHOLD:
        verdict = "weak_hire"
        label = "Weak Hire — Needs Development"
    else:
        verdict = "no_hire"
        label = "No Hire — Significant Gaps"

    strengths = [s["skill"] for s in skill_breakdown if s["avg_score"] >= SCORE_STRONG_THRESHOLD]
    gaps = [s["skill"] for s in skill_breakdown if s["avg_score"] < SCORE_WEAK_THRESHOLD]
    development = [s["skill"] for s in skill_breakdown if SCORE_WEAK_THRESHOLD <= s["avg_score"] < SCORE_STRONG_THRESHOLD]

    return {
        "report_title": "InterviewAI — Final Assessment Report",
        "generated_at": datetime.now().isoformat(),
        "overall_score": round(overall_score, 1),
        "verdict": verdict,
        "label": label,
        "total_questions": summary["total_questions_asked"],
        "skills_evaluated": len(skill_breakdown),
        "breakdown": sorted(skill_breakdown, key=lambda x: x["avg_score"]),
        "strengths": strengths,
        "gaps": gaps,
        "needs_development": development,
        "feedback_summary": _generate_summary_text(overall_score, verdict, strengths, gaps),
        "answer_log": [
            {
                "question": a["question"],
                "answer": a["answer"],
                "score": a["score"],
                "verdict": a["verdict"],
                "skill": a["skill"],
            }
            for a in answers
        ],
    }


def _generate_summary_text(score: float, verdict: str, strengths: list, gaps: list) -> str:
    parts = [f"Overall Score: {score:.1f}/100 — Verdict: {verdict.replace('_', ' ').title()}."]

    if strengths:
        parts.append(f"Strengths: {', '.join(strengths[:5])}.")
    if gaps:
        parts.append(f"Gaps to address: {', '.join(gaps[:5])}.")

    parts.append("See breakdown below for details.")
    return " ".join(parts)


def get_score_label(score: float) -> str:
    if score >= SCORE_STRONG_THRESHOLD:
        return "Strong"
    elif score >= SCORE_WEAK_THRESHOLD:
        return "Needs Improvement"
    return "Significant Gap"
