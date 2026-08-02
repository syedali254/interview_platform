"""Post-interview evaluation pipeline — ties M6, M9, M11 and M12 together.

The live interview (M5) produces a transcript plus client-side behavioural
telemetry. This module turns that raw material into the assessment the
proposal describes:

  1. Pair the transcript into question/answer exchanges.
  2. Classify each pair (technical / behavioural / logistics) and attach the
     skill it probes, so greetings and sign-offs are not scored.
  3. Score every substantive answer through M6's LLM-as-Judge evaluator, in
     parallel, recording each answer's rubric breakdown and how consistent
     the judge was with itself.
  4. Feed the scores into the M6a skill-state tracker to get per-skill
     verdicts and flag skills that were under-probed.
  5. Derive behavioural features and run M9 integrity detection.
  6. Fuse everything into a weighted recommendation (M11).
  7. Assemble the final report (M12).
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from core.evaluator.evaluator import evaluate_answer
from core.evaluator.fusion import compute_fusion_score
from core.evaluator.integrity import assess_integrity
from core.graph.state import InterviewState
from core.graph.traversal import decide_follow_up
from core.llm import call_llm_json
from core.report.generator import build_report

# Only replies below this are treated as non-answers ("yes", "okay") rather
# than something to score. Everything longer is evaluated.
MIN_ANSWER_WORDS = 3

# How many answers to evaluate concurrently. Each evaluation is three LLM
# calls (one reference answer, two rubric orderings), so this is a
# throughput/rate-limit trade-off.
MAX_WORKERS = 4

# Proportion of an interview a candidate can naturally spend looking away —
# thinking, glancing at notes — before it reads as disengagement.
NATURAL_GAZE_SHIFT = 0.20


def pair_exchanges(conversation: list) -> list:
    """Collapse a role-tagged transcript into question/answer exchanges.

    Consecutive messages from the same speaker are joined, so an interviewer
    who asks a question across two utterances still produces one exchange.
    """
    exchanges = []
    pending_q = None

    for msg in conversation or []:
        role = msg.get("role")
        text = (msg.get("text") or "").strip()
        if not text:
            continue
        time_s = msg.get("time")

        if role == "agent":
            if pending_q and pending_q.get("answer") is None:
                # Interviewer spoke twice in a row — treat it as one question.
                pending_q["question"] = f"{pending_q['question']} {text}".strip()
                continue
            if pending_q:
                exchanges.append(pending_q)
            pending_q = {"question": text, "answer": None,
                         "q_time": time_s, "a_time": None}
        elif role == "candidate" and pending_q:
            if pending_q["answer"] is None:
                pending_q["answer"] = text
                pending_q["a_time"] = time_s
            else:
                pending_q["answer"] = f"{pending_q['answer']} {text}".strip()

    if pending_q:
        exchanges.append(pending_q)

    return [e for e in exchanges if e.get("answer")]


def classify_exchanges(exchanges: list, topics: list) -> list:
    """Label each exchange with a skill and a kind.

    Uses one LLM call for the whole session. Falls back to a keyword match
    against the target skills if that call fails, so evaluation never depends
    on the classification succeeding.
    """
    if not exchanges:
        return exchanges

    skills = [t.get("skill", "") for t in (topics or []) if t.get("skill")]
    skill_list = ", ".join(skills) if skills else "General"

    numbered = "\n".join(
        f'{i}. Interviewer: "{e["question"][:300]}"\n   Candidate: "{(e["answer"] or "")[:300]}"'
        for i, e in enumerate(exchanges)
    )

    prompt = f"""You are analysing an interview transcript.

TARGET SKILLS FOR THIS ROLE: {skill_list}

EXCHANGES:
{numbered}

For each exchange, decide:
- "kind": "technical" if it probes technical knowledge, "behavioural" if it
  probes experience or soft skills, "logistics" if it is a greeting, a
  readiness check, small talk, a sign-off, or anything not being assessed.
- "skill": the single closest skill from the target list. If none fit, use the
  general topic in two or three words. Use "General" for logistics exchanges.

Return ONLY a JSON array, one object per exchange, in the same order:
[{{"index": 0, "kind": "logistics", "skill": "General"}}]"""

    labels = {}
    try:
        result = call_llm_json(prompt, temperature=0.1)
        rows = result if isinstance(result, list) else result.get("exchanges", [])
        for row in rows:
            idx = row.get("index")
            if isinstance(idx, int):
                labels[idx] = {
                    "kind": row.get("kind", "technical"),
                    "skill": row.get("skill") or "General",
                }
    except Exception:
        labels = {}

    for i, exchange in enumerate(exchanges):
        label = labels.get(i)
        if label is None:
            label = _fallback_label(exchange, skills)
        exchange["kind"] = label["kind"]
        exchange["skill"] = label["skill"]

        # Every substantive answer is evaluated, however short. A one-line
        # non-answer is a real result and must appear in the report with a
        # score, not be silently dropped for failing a length threshold.
        # Only logistics turns (greetings, readiness checks, sign-offs) and
        # genuinely empty replies are left unscored.
        word_count = len((exchange.get("answer") or "").split())
        exchange["scored"] = (
            exchange["kind"] in ("technical", "behavioural")
            and word_count >= MIN_ANSWER_WORDS
        )

    return exchanges


def _fallback_label(exchange: dict, skills: list) -> dict:
    """Keyword-based labelling, used only when the LLM classifier fails."""
    question = (exchange.get("question") or "").lower()
    for skill in skills:
        if skill.lower() in question:
            return {"kind": "technical", "skill": skill}
    # No question mark and a very short answer is almost always logistics.
    if "?" not in question and len((exchange.get("answer") or "").split()) < 15:
        return {"kind": "logistics", "skill": "General"}
    return {"kind": "technical", "skill": skills[0] if skills else "General"}


def score_exchanges(exchanges: list) -> list:
    """Run M6 evaluation over every scored exchange, in parallel."""
    targets = [e for e in exchanges if e.get("scored")]
    if not targets:
        return []

    def run(exchange):
        try:
            result = evaluate_answer(
                question=exchange["question"],
                candidate_answer=exchange["answer"],
                skill=exchange.get("skill", "General"),
            )
        except Exception as exc:
            return {
                "skill": exchange.get("skill", "General"),
                "question": exchange["question"],
                "candidate_answer": exchange["answer"],
                "error": str(exc),
                "final_score": None,
            }
        result["kind"] = exchange.get("kind", "technical")
        result["response_time_sec"] = _response_time(exchange)
        return result

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        return list(pool.map(run, targets))


def _response_time(exchange: dict):
    """Seconds between the question landing and the answer completing."""
    q_time, a_time = exchange.get("q_time"), exchange.get("a_time")
    if isinstance(q_time, (int, float)) and isinstance(a_time, (int, float)):
        return max(0, round(a_time - q_time, 1))
    return None


def build_skill_states(evaluations: list, topics: list) -> dict:
    """Track per-skill verdicts (M6a) and flag skills that need more probing."""
    skills = {t["skill"] for t in (topics or []) if t.get("skill")}
    skills.update(e["skill"] for e in evaluations if e.get("skill"))
    state = InterviewState([{"skill": s, "priority": "medium"} for s in sorted(skills)])

    for evaluation in evaluations:
        score = evaluation.get("final_score")
        if score is not None:
            state.record_answer(evaluation["skill"], score)

    summary = state.summary()
    summary["under_probed"] = sorted(
        skill for skill, node in state.nodes.items()
        if node.questions_asked > 0
        and decide_follow_up(state, skill, node.avg_score)
    )
    summary["never_probed"] = sorted(
        skill for skill, node in state.nodes.items() if node.questions_asked == 0
    )
    return summary


def derive_behaviour(exchanges: list, evaluations: list, telemetry: dict) -> dict:
    """Assemble the M9 feature inputs from transcript timing plus telemetry."""
    telemetry = telemetry or {}

    response_times = [t for t in (_response_time(e) for e in exchanges) if t is not None]
    answer_lengths = [len((e.get("answer") or "").split()) for e in exchanges if e.get("answer")]

    # Hesitation proxy: filler markers in the transcribed answers.
    fillers = ("um", "uh", "erm", "hmm", "like", "you know")
    hesitations = [
        sum((e.get("answer") or "").lower().count(f) for f in fillers)
        for e in exchanges if e.get("answer")
    ]

    # Sustained disengagement counts as inactivity, but ordinary glancing
    # away does not — people naturally break eye contact while thinking, so
    # only the portion above NATURAL_GAZE_SHIFT is treated as idle time.
    inactivity_periods = telemetry.get("inactivity_periods") or []
    vision = telemetry.get("vision") or {}
    if not inactivity_periods and vision.get("looking_away_ratio") is not None:
        total = telemetry.get("total_duration", 300)
        excess = max(0.0, vision["looking_away_ratio"] - NATURAL_GAZE_SHIFT)
        if excess > 0:
            inactivity_periods = [excess * total]

    return {
        "response_times": response_times,
        "tab_switches": telemetry.get("tab_switches", 0),
        "inactivity_periods": inactivity_periods,
        "answer_lengths": answer_lengths,
        "total_duration": telemetry.get("total_duration", 300),
        "hesitations": hesitations,
    }


def evaluate_session(
    conversation: list,
    graph_data: dict = None,
    telemetry: dict = None,
) -> dict:
    """Run the full post-interview assessment and return the M12 report."""
    graph_data = graph_data or {}
    telemetry = telemetry or {}
    topics = graph_data.get("topics", [])

    exchanges = pair_exchanges(conversation)
    exchanges = classify_exchanges(exchanges, topics)
    evaluations = score_exchanges(exchanges)

    scored = [e for e in evaluations if e.get("final_score") is not None]
    skill_states = build_skill_states(scored, topics)

    behaviour = derive_behaviour(exchanges, evaluations, telemetry)
    integrity = assess_integrity(behaviour)

    skill_match_pct = (graph_data.get("gaps") or {}).get("match_percentage", 0)
    fusion = compute_fusion_score(
        answer_scores=[e["final_score"] for e in scored],
        skill_match_pct=skill_match_pct,
        integrity_score=integrity["integrity_score"],
        engagement_score=telemetry.get("engagement_score", 75),
        emotion_data=telemetry.get("emotion_data"),
        vision_summary=telemetry.get("vision"),
        voice_summary=telemetry.get("voice"),
        distraction_count=telemetry.get("distraction_count", 0),
    )

    return build_report(
        evaluations=evaluations,
        exchanges=exchanges,
        skill_states=skill_states,
        integrity=integrity,
        fusion=fusion,
        graph_data=graph_data,
        meta={
            "generated_at": datetime.now().isoformat(),
            "total_exchanges": len(exchanges),
            "scored_exchanges": len(scored),
            "duration_mins": telemetry.get("duration_mins"),
        },
    )
