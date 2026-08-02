"""M11: Weighted Fusion Engine — Final recommendation generator.

Combines the scores produced by every evaluation module:
  - M6:      answer quality (LLM-as-Judge)
  - M3:      skill coverage from the graph gap analysis
  - M9:      behavioural integrity (Isolation Forest)
  - M7/M8/M10: presence — visual attention, posture and vocal delivery

Produces a final weighted recommendation with a confidence level, and
returns the full arithmetic so every number on the report can be traced
back to its inputs.
"""

from datetime import datetime
from typing import Optional


# Top-level weights (sum = 1.0)
WEIGHTS = {
    "answer_quality": 0.50,       # M6: what the candidate actually said
    "skill_coverage": 0.20,       # M3: CV-to-role fit
    "behavioral_integrity": 0.15, # M9: was the session clean
    "engagement": 0.15,           # M7 + M8 + M10: how they presented
}

# Sub-weights inside the engagement component (sum = 1.0)
ENGAGEMENT_WEIGHTS = {
    "attention": 0.45,   # M7: gaze held on the interview
    "posture": 0.20,     # M8: upright, stable body language
    "voice": 0.35,       # M10: vocal projection, fluency, composure
}

# Each distraction event costs this many engagement points.
DISTRACTION_PENALTY = 4.0
MAX_DISTRACTION_PENALTY = 30.0


def compute_engagement(
    vision: Optional[dict] = None,
    voice: Optional[dict] = None,
    distraction_count: int = 0,
    fallback: float = 75.0,
) -> dict:
    """Derive the engagement component from the presence modules.

    Falls back to the caller's estimate when neither MediaPipe nor the audio
    analyser produced usable data, so a browser that could not run them still
    yields a complete report — flagged as estimated rather than measured.
    """
    parts = {}

    if vision and vision.get("avg_attention") is not None:
        parts["attention"] = max(0.0, min(100.0, vision["avg_attention"] * 100))
    if vision and vision.get("avg_posture") is not None:
        parts["posture"] = max(0.0, min(100.0, vision["avg_posture"] * 100))
    if voice and voice.get("vocal_confidence") is not None:
        parts["voice"] = max(0.0, min(100.0, float(voice["vocal_confidence"])))

    if parts:
        total_weight = sum(ENGAGEMENT_WEIGHTS[k] for k in parts)
        raw = sum(parts[k] * ENGAGEMENT_WEIGHTS[k] for k in parts) / total_weight
        measured = True
    else:
        raw = fallback
        measured = False

    penalty = min(distraction_count * DISTRACTION_PENALTY, MAX_DISTRACTION_PENALTY)
    score = max(0.0, min(100.0, raw - penalty))

    return {
        "score": round(score, 1),
        "measured": measured,
        "before_penalty": round(raw, 1),
        "distraction_penalty": round(penalty, 1),
        "sources": {k: round(v, 1) for k, v in parts.items()},
        "weights": {k: ENGAGEMENT_WEIGHTS[k] for k in parts} if parts else {},
    }

# Recommendation thresholds
STRONG_HIRE_THRESHOLD = 72
HIRE_THRESHOLD = 55
CONSIDER_THRESHOLD = 40


def compute_fusion_score(
    answer_scores: list,
    skill_match_pct: float,
    integrity_score: float = 100.0,
    engagement_score: float = 75.0,
    emotion_data: Optional[dict] = None,
    vision_summary: Optional[dict] = None,
    voice_summary: Optional[dict] = None,
    distraction_count: int = 0,
) -> dict:
    """Compute the weighted fusion of all module outputs.

    Args:
        answer_scores:     per-answer final scores from M6 (0-100)
        skill_match_pct:   M3 skill graph match percentage (0-100)
        integrity_score:   M9 integrity score (0-100)
        engagement_score:  fallback engagement when the presence modules
                           produced nothing (0-100)
        emotion_data:      facial emotion summary
        vision_summary:    M7/M8 attention and posture summary
        voice_summary:     M10 vocal delivery summary
        distraction_count: number of recorded distraction events

    Returns:
        The fusion result, including the full breakdown behind every number.
    """
    avg_answer = sum(answer_scores) / len(answer_scores) if answer_scores else 0.0
    skill_norm = min(100, max(0, skill_match_pct))
    integrity_norm = min(100, max(0, integrity_score))

    engagement = compute_engagement(
        vision=vision_summary,
        voice=voice_summary,
        distraction_count=distraction_count,
        fallback=engagement_score,
    )
    engagement_norm = engagement["score"]

    # Weighted combination
    fusion_score = (
        avg_answer * WEIGHTS["answer_quality"] +
        skill_norm * WEIGHTS["skill_coverage"] +
        integrity_norm * WEIGHTS["behavioral_integrity"] +
        engagement_norm * WEIGHTS["engagement"]
    )

    # Determine recommendation
    if integrity_norm < 30:
        # Override: integrity failure overrides other scores
        recommendation = "disqualified"
        label = "Session Integrity Compromised"
        confidence = "high"
    elif fusion_score >= STRONG_HIRE_THRESHOLD:
        recommendation = "strong_hire"
        label = "Strong Hire"
        confidence = "high" if fusion_score >= 80 else "moderate"
    elif fusion_score >= HIRE_THRESHOLD:
        recommendation = "hire"
        label = "Hire — Meets Requirements"
        confidence = "moderate"
    elif fusion_score >= CONSIDER_THRESHOLD:
        recommendation = "consider"
        label = "Consider — Development Needed"
        confidence = "moderate"
    else:
        recommendation = "no_hire"
        label = "No Hire — Significant Gaps"
        confidence = "high" if fusion_score < 25 else "moderate"

    # Component breakdown
    components = {
        "answer_quality": {
            "score": round(avg_answer, 1),
            "weight": WEIGHTS["answer_quality"],
            "weighted_contribution": round(avg_answer * WEIGHTS["answer_quality"], 1),
        },
        "skill_coverage": {
            "score": round(skill_norm, 1),
            "weight": WEIGHTS["skill_coverage"],
            "weighted_contribution": round(skill_norm * WEIGHTS["skill_coverage"], 1),
        },
        "behavioral_integrity": {
            "score": round(integrity_norm, 1),
            "weight": WEIGHTS["behavioral_integrity"],
            "weighted_contribution": round(integrity_norm * WEIGHTS["behavioral_integrity"], 1),
        },
        "engagement": {
            "score": round(engagement_norm, 1),
            "weight": WEIGHTS["engagement"],
            "weighted_contribution": round(engagement_norm * WEIGHTS["engagement"], 1),
            "breakdown": engagement,
        },
    }

    # Strengths and concerns
    strengths = []
    concerns = []

    if avg_answer >= 70:
        strengths.append("Strong technical answers")
    elif avg_answer < 40:
        concerns.append("Weak technical answers")

    if skill_norm >= 70:
        strengths.append("Good skill match for role")
    elif skill_norm < 40:
        concerns.append("Significant skill gaps")

    if integrity_norm >= 80:
        strengths.append("Clean session behavior")
    elif integrity_norm < 50:
        concerns.append("Behavioral anomalies detected")

    if engagement_norm >= 70:
        strengths.append("High engagement throughout")
    elif engagement_norm < 40:
        concerns.append("Low engagement/attention")

    # Presence detail from the vision and voice modules.
    if vision_summary:
        if (vision_summary.get("looking_away_ratio") or 0) > 0.25:
            concerns.append("Frequently looked away from the screen")
        for flag in vision_summary.get("posture_flags") or []:
            concerns.append(f"Posture: {flag.get('flag', flag)}")
    if voice_summary:
        for indicator in (voice_summary.get("indicators") or [])[:2]:
            concerns.append(indicator)
        if (voice_summary.get("vocal_confidence") or 0) >= 75:
            strengths.append("Confident vocal delivery")

    # Emotion summary
    emotion_summary = None
    if emotion_data:
        dominant = emotion_data.get("dominant_emotion", "neutral")
        avg_conf = emotion_data.get("avg_confidence", 0)
        emotion_summary = {
            "dominant_emotion": dominant,
            "confidence": round(avg_conf, 2),
            "interpretation": _interpret_emotion(dominant),
        }

    return {
        "fusion_score": round(fusion_score, 1),
        "recommendation": recommendation,
        "label": label,
        "confidence": confidence,
        "components": components,
        "strengths": strengths,
        "concerns": concerns,
        "emotion_summary": emotion_summary,
        "vision_summary": vision_summary,
        "voice_summary": voice_summary,
        "weights_used": WEIGHTS,
        "engagement_weights": ENGAGEMENT_WEIGHTS,
        "timestamp": datetime.now().isoformat(),
    }


def _interpret_emotion(emotion: str) -> str:
    """Provide brief interpretation of dominant emotion."""
    interpretations = {
        "happy": "Candidate appeared confident and positive",
        "neutral": "Candidate maintained composure throughout",
        "sad": "Candidate may have felt uncertain or stressed",
        "angry": "Candidate showed signs of frustration",
        "fearful": "Candidate appeared anxious or nervous",
        "surprised": "Candidate showed unexpected reactions",
        "disgusted": "Candidate showed negative reactions to questions",
    }
    return interpretations.get(emotion, "Emotion patterns inconclusive")
