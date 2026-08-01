"""M11: Weighted Fusion Engine — Final recommendation generator.

Combines scores from all evaluation modules:
  - M6: Answer evaluation scores (Track A + Track B)
  - M9: Behavioral integrity score
  - M10: Emotion/engagement indicators
  - M3: Skill gap analysis

Produces a final weighted recommendation with confidence level.
"""

from datetime import datetime
from typing import Optional


# Weight configuration (sum = 1.0)
WEIGHTS = {
    "answer_quality": 0.50,      # M6: Technical answer scores
    "skill_coverage": 0.20,      # M3: Skill match percentage
    "behavioral_integrity": 0.15, # M9: Integrity score
    "engagement": 0.15,          # M10: Emotion/engagement
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
) -> dict:
    """Compute weighted fusion of all module outputs.
    
    Args:
        answer_scores: List of per-answer final scores (0-100)
        skill_match_pct: Skill graph match percentage (0-100)
        integrity_score: M9 integrity score (0-100)
        engagement_score: M10 engagement/attention (0-100)
        emotion_data: Optional emotion summary from M10
    
    Returns:
        Complete fusion result with recommendation
    """
    # Normalize inputs to 0-100 scale
    avg_answer = sum(answer_scores) / len(answer_scores) if answer_scores else 0.0
    skill_norm = min(100, max(0, skill_match_pct))
    integrity_norm = min(100, max(0, integrity_score))
    engagement_norm = min(100, max(0, engagement_score))

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
        "weights_used": WEIGHTS,
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
