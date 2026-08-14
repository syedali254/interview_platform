"""M9: Behavioural Integrity Detection using an Isolation Forest.

Flags interview sessions whose behaviour departs from a normal baseline:
  - Response timing (implausibly fast = pre-written, very long = searching)
  - Tab-switch frequency and inactivity
  - Answer length consistency
  - Speech hesitation patterns

The baseline is synthetic and must match what the system actually measures.
"response time" here is the interval from the interviewer's question starting
to the candidate's answer finishing, so it includes the question being spoken
and the answer being delivered — typically 20-60 seconds, not the 5-15 a
"thinking time" reading would suggest. An earlier baseline assumed the latter
and flagged every ordinary session as anomalous.

The raw Isolation Forest decision function is not a score a person can read,
so it is calibrated against the baseline distribution at training time: the
1st percentile of normal sessions maps to 50/100 and the 99th to 100/100,
with anomalies falling away below that.
"""

import numpy as np
from datetime import datetime
from pathlib import Path

MODEL_PATH = Path(__file__).parent / "models" / "integrity_iso_forest.joblib"
MODEL_VERSION = 2

FEATURE_ORDER = [
    "avg_response_time_sec",
    "response_time_std",
    "tab_switches",
    "inactivity_ratio",
    "avg_answer_length_words",
    "answer_length_variance_coeff",
    "hesitation_ratio",
    "engagement_score",
]

# Verdict thresholds on the calibrated 0-100 integrity score.
NORMAL_THRESHOLD = 60
SUSPICIOUS_THRESHOLD = 35

_bundle = None


def _get_model() -> dict:
    """Load the calibrated model bundle, training it if absent or outdated."""
    global _bundle
    if _bundle is not None:
        return _bundle

    if MODEL_PATH.exists():
        try:
            import joblib
            loaded = joblib.load(MODEL_PATH)
            # Reject bundles from before calibration existed, otherwise the
            # old miscalibrated baseline silently keeps being used.
            if isinstance(loaded, dict) and loaded.get("version") == MODEL_VERSION:
                _bundle = loaded
                return _bundle
        except Exception:
            pass

    _bundle = _train_default_model()
    return _bundle


def _train_default_model() -> dict:
    """Fit the baseline on synthetic normal interview behaviour."""
    from sklearn.ensemble import IsolationForest

    rng = np.random.default_rng(42)
    n = 400

    # Distributions chosen to match what extract_behavioral_features()
    # actually produces for a genuine, well-behaved interview.
    normal_data = np.column_stack([
        rng.normal(32, 11, n),        # avg_response_time_sec
        rng.normal(14, 6, n),         # response_time_std
        rng.poisson(0.7, n),          # tab_switches
        rng.normal(0.04, 0.03, n),    # inactivity_ratio
        rng.normal(48, 18, n),        # avg_answer_length_words
        rng.normal(0.45, 0.18, n),    # answer_length_variance_coeff
        rng.normal(0.04, 0.03, n),    # hesitation_ratio
        rng.uniform(0.6, 1.0, n),     # engagement_score
    ])
    normal_data = np.clip(normal_data, 0, None)

    model = IsolationForest(
        n_estimators=200,
        contamination=0.05,
        random_state=42,
        max_samples="auto",
    )
    model.fit(normal_data)

    baseline_scores = model.decision_function(normal_data)
    bundle = {
        "version": MODEL_VERSION,
        "model": model,
        "feature_order": FEATURE_ORDER,
        "calibration": {
            "p01": float(np.percentile(baseline_scores, 1)),
            "p99": float(np.percentile(baseline_scores, 99)),
        },
    }

    try:
        import joblib
        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(bundle, MODEL_PATH)
    except Exception:
        pass

    return bundle


def extract_behavioral_features(session_data: dict) -> dict:
    """Derive the M9 feature vector from a session's timing and telemetry.

    Expected keys:
      response_times      seconds from question start to answer end, per answer
      tab_switches        count of times the candidate left the tab
      inactivity_periods  list of idle stretches, in seconds
      answer_lengths      word count per answer
      total_duration      whole session length, in seconds
      hesitations         filler-word count per answer
    """
    response_times = session_data.get("response_times") or []
    tab_switches = session_data.get("tab_switches", 0)
    inactivity_periods = session_data.get("inactivity_periods") or []
    answer_lengths = session_data.get("answer_lengths") or []
    total_duration = session_data.get("total_duration", 300)
    hesitations = session_data.get("hesitations") or []

    avg_response_time = float(np.mean(response_times)) if response_times else 32.0
    response_time_std = float(np.std(response_times)) if len(response_times) > 1 else 14.0

    inactivity_ratio = sum(inactivity_periods) / max(total_duration, 1)

    avg_answer_length = float(np.mean(answer_lengths)) if answer_lengths else 48.0
    if answer_lengths and avg_answer_length > 0:
        length_variance_coeff = float(np.std(answer_lengths)) / avg_answer_length
    else:
        length_variance_coeff = 0.45

    hesitation_ratio = (
        float(np.mean(hesitations)) / max(avg_answer_length, 1) if hesitations else 0.04
    )

    engagement = 1.0 - min(1.0, tab_switches * 0.1 + inactivity_ratio)

    return {
        "avg_response_time_sec": round(avg_response_time, 2),
        "response_time_std": round(response_time_std, 2),
        "tab_switches": int(tab_switches),
        "inactivity_ratio": round(float(inactivity_ratio), 4),
        "avg_answer_length_words": round(avg_answer_length, 1),
        "answer_length_variance_coeff": round(length_variance_coeff, 4),
        "hesitation_ratio": round(hesitation_ratio, 4),
        "engagement_score": round(float(engagement), 4),
    }


def _identify_risk_factors(features: dict) -> list:
    """Name the specific behaviours that make a session look irregular."""
    risks = []
    if features["avg_response_time_sec"] < 6:
        risks.append("Implausibly fast responses (possible pre-written answers)")
    if features["avg_response_time_sec"] > 90:
        risks.append("Very long response times (possible external assistance)")
    if features["tab_switches"] > 5:
        risks.append(f"High tab-switch count ({features['tab_switches']})")
    if features["inactivity_ratio"] > 0.3:
        risks.append("Extended inactivity during the session")
    if features["answer_length_variance_coeff"] > 1.2:
        risks.append("Highly inconsistent answer lengths (possible mixed sources)")
    if features["engagement_score"] < 0.4:
        risks.append("Low engagement throughout the session")
    return risks


def assess_integrity(session_data: dict) -> dict:
    """Assess behavioural integrity for one interview session.

    Returns the calibrated integrity score, a verdict, the raw anomaly score,
    the features behind it, and the specific risk factors — never a bare
    "flagged" with nothing to justify it.
    """
    features = extract_behavioral_features(session_data)
    bundle = _get_model()
    model = bundle["model"]
    calibration = bundle["calibration"]

    vector = np.array([[features[f] for f in FEATURE_ORDER]])
    raw_score = float(model.decision_function(vector)[0])
    is_anomaly = int(model.predict(vector)[0]) == -1

    # Map the baseline's 1st..99th percentile onto 50..100.
    low, high = calibration["p01"], calibration["p99"]
    span = max(high - low, 1e-9)
    integrity_score = max(0.0, min(100.0, 50.0 + (raw_score - low) / span * 50.0))

    risk_factors = _identify_risk_factors(features)

    if integrity_score >= NORMAL_THRESHOLD:
        verdict = "normal"
    elif integrity_score >= SUSPICIOUS_THRESHOLD:
        verdict = "suspicious"
    else:
        verdict = "flagged"

    # A verdict the recruiter cannot act on is worse than no verdict, so
    # always explain what drove an adverse outcome.
    if verdict != "normal" and not risk_factors:
        risk_factors.append(
            "Overall behaviour pattern differs from the baseline, though no "
            "single indicator crossed its threshold — review the session "
            "before drawing conclusions."
        )

    return {
        "integrity_score": round(integrity_score, 1),
        "verdict": verdict,
        "anomaly_score": round(raw_score, 4),
        "is_anomaly": is_anomaly,
        "features": features,
        "risk_factors": risk_factors,
        "timestamp": datetime.now().isoformat(),
    }
