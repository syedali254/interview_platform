"""M12 — Final interview report assembly.

Takes the outputs of every evaluation module and produces one structured
report: overall score and recommendation, per-answer detail with the judge's
rubric breakdown, per-skill verdicts, integrity assessment, and the judge
self-consistency statistics for the session.

Self-consistency matters because the scores come from an LLM judge. Each
answer is scored twice under different rubric orderings; the spread between
those two calls is the evidence for how stable the score is. A session where
the judge disagreed with itself is reported as such rather than presented as
a confident assessment.
"""

from core.config import SCORE_STRONG_THRESHOLD, SCORE_WEAK_THRESHOLD


def judge_reliability(evaluations: list) -> dict:
    """Self-consistency statistics for the LLM judge across the session."""
    spreads = [
        e["judge"]["spread"] for e in evaluations
        if e.get("judge") and e["judge"].get("spread") is not None
    ]

    result = {
        "n": len(spreads),
        "mean_spread": None,
        "max_spread": None,
        "consistency_distribution": {"high": 0, "moderate": 0, "low": 0},
        "flagged_for_review": 0,
        "note": None,
    }

    if not spreads:
        result["note"] = "No answers were scored in this session."
        return result

    result["mean_spread"] = round(sum(spreads) / len(spreads), 2)
    result["max_spread"] = round(max(spreads), 1)

    for evaluation in evaluations:
        judge = evaluation.get("judge") or {}
        level = judge.get("consistency")
        if level in result["consistency_distribution"]:
            result["consistency_distribution"][level] += 1
        if evaluation.get("flagged"):
            result["flagged_for_review"] += 1

    if result["consistency_distribution"]["low"] > 0:
        result["note"] = (
            f"{result['consistency_distribution']['low']} answer(s) scored "
            "inconsistently across the two rubric orderings and are flagged "
            "for human review."
        )

    return result


def build_report(
    evaluations: list,
    exchanges: list,
    skill_states: dict,
    integrity: dict,
    fusion: dict,
    graph_data: dict = None,
    meta: dict = None,
) -> dict:
    """Assemble the final candidate report."""
    graph_data = graph_data or {}
    meta = meta or {}

    scored = [e for e in evaluations if e.get("final_score") is not None]
    overall = round(sum(e["final_score"] for e in scored) / len(scored), 1) if scored else 0.0

    # Per-skill breakdown, worst first so gaps surface at the top.
    breakdown = []
    for skill, node in (skill_states.get("skills") or {}).items():
        if node.get("questions_asked", 0) == 0:
            continue
        breakdown.append({
            "skill": skill,
            "status": node["status"],
            "avg_score": round(node["avg_score"], 1),
            "best_score": round(node["best_score"], 1),
            "questions_answered": node["questions_asked"],
        })
    breakdown.sort(key=lambda s: s["avg_score"])

    answers = []
    for evaluation in evaluations:
        judge = evaluation.get("judge") or {}
        answers.append({
            "skill": evaluation.get("skill"),
            "kind": evaluation.get("kind"),
            "question": evaluation.get("question"),
            "answer": evaluation.get("candidate_answer"),
            "reference_answer": evaluation.get("reference_answer"),
            "final_score": evaluation.get("final_score"),
            "verdict": evaluation.get("verdict"),
            "flagged": evaluation.get("flagged", False),
            "response_time_sec": evaluation.get("response_time_sec"),
            "note": evaluation.get("note"),
            "error": evaluation.get("error"),
            "judge": {
                "score": judge.get("score"),
                "criterion_scores": judge.get("criterion_scores"),
                "feedback": judge.get("feedback"),
                "call_scores": judge.get("call_scores"),
                "spread": judge.get("spread"),
                "consistency": judge.get("consistency"),
            },
        })

    strengths = [s["skill"] for s in breakdown if s["avg_score"] >= SCORE_STRONG_THRESHOLD]
    gaps = [s["skill"] for s in breakdown if s["avg_score"] < SCORE_WEAK_THRESHOLD]
    developing = [
        s["skill"] for s in breakdown
        if SCORE_WEAK_THRESHOLD <= s["avg_score"] < SCORE_STRONG_THRESHOLD
    ]

    return {
        "report_title": "InterviewAI — Final Assessment Report",
        "generated_at": meta.get("generated_at"),
        "overall_score": overall,
        "recommendation": fusion.get("recommendation"),
        "label": fusion.get("label"),
        "confidence": fusion.get("confidence"),
        "fusion": fusion,
        "integrity": integrity,
        "judge_reliability": judge_reliability(evaluations),
        "skill_states": skill_states,
        "breakdown": breakdown,
        "strengths": strengths,
        "needs_development": developing,
        "gaps": gaps,
        "answers": answers,
        "skill_match": {
            "match_percentage": (graph_data.get("gaps") or {}).get("match_percentage"),
            "missing_required": (graph_data.get("gaps") or {}).get("missing_required", []),
        },
        "counts": {
            "total_exchanges": meta.get("total_exchanges", len(exchanges)),
            "scored_answers": len(scored),
            "flagged_answers": sum(1 for e in evaluations if e.get("flagged")),
            "skills_assessed": len(breakdown),
        },
        "duration_mins": meta.get("duration_mins"),
        "summary_text": _summary_text(overall, fusion, strengths, gaps),
    }


def _summary_text(overall: float, fusion: dict, strengths: list, gaps: list) -> str:
    parts = [
        f"Overall score {overall:.1f}/100 — {fusion.get('label', 'no recommendation')} "
        f"({fusion.get('confidence', 'unknown')} confidence)."
    ]
    if strengths:
        parts.append(f"Strongest areas: {', '.join(strengths[:5])}.")
    if gaps:
        parts.append(f"Areas of concern: {', '.join(gaps[:5])}.")
    return " ".join(parts)
