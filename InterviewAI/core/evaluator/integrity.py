"""M9: Behavioral Integrity Detection using Isolation Forest.

Detects anomalous interview behavior by analyzing:
  - Response timing patterns (too fast = copied, too slow = searching)
  - Tab switch frequency  
  - Inactivity periods
  - Answer length consistency
  - Speech hesitation patterns

The model learns "normal" behavior from baseline sessions and flags
sessions that deviate significantly.
"""

import numpy as np
from datetime import datetime
from typing import Optional

# Lazy-loaded model
_iso_forest = None


def _get_model():
    """Load or create Isolation Forest model."""
    global _iso_forest
    if _iso_forest is not None:
        return _iso_forest

    from pathlib import Path
    model_path = Path(__file__).parent / "models" / "integrity_iso_forest.joblib"

    if model_path.exists():
        try:
            import joblib
            _iso_forest = joblib.load(model_path)
            return _iso_forest
        except Exception:
            pass

    # Create default model trained on synthetic normal behavior
    _iso_forest = _train_default_model()
    return _iso_forest


def _train_default_model():
    """Train on synthetic normal interview behavior for demo."""
    from sklearn.ensemble import IsolationForest

    np.random.seed(42)
    n_samples = 200

    # Generate "normal" interview behavior patterns
    normal_data = np.column_stack([
        np.random.normal(8.0, 3.0, n_samples),    # avg_response_time_sec (5-15s normal)
        np.random.normal(2.0, 1.5, n_samples),    # response_time_std
        np.random.poisson(1, n_samples),           # tab_switches (0-3 normal)
        np.random.normal(0.05, 0.03, n_samples),   # inactivity_ratio (low)
        np.random.normal(50, 20, n_samples),       # avg_answer_length_words
        np.random.normal(0.15, 0.08, n_samples),   # answer_length_variance_coeff
        np.random.normal(0.1, 0.05, n_samples),    # hesitation_ratio
        np.random.uniform(0.7, 1.0, n_samples),    # engagement_score
    ])

    # Clip to realistic ranges
    normal_data = np.clip(normal_data, 0, None)

    model = IsolationForest(
        n_estimators=100,
        contamination=0.1,
        random_state=42,
        max_samples='auto',
    )
    model.fit(normal_data)

    # Save model
    try:
        import joblib
        from pathlib import Path
        model_dir = Path(__file__).parent / "models"
        model_dir.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, model_dir / "integrity_iso_forest.joblib")
    except Exception:
        pass

    return model


def extract_behavioral_features(session_data: dict) -> dict:
    """Extract behavioral features from interview session data.
    
    Expected session_data keys:
      - response_times: list of seconds per answer
      - tab_switches: int count
      - inactivity_periods: list of seconds of inactivity
      - answer_lengths: list of word counts per answer
      - total_duration: total interview seconds
      - hesitations: list of hesitation counts per answer
    """
    response_times = session_data.get("response_times", [])
    tab_switches = session_data.get("tab_switches", 0)
    inactivity_periods = session_data.get("inactivity_periods", [])
    answer_lengths = session_data.get("answer_lengths", [])
    total_duration = session_data.get("total_duration", 300)
    hesitations = session_data.get("hesitations", [])

    # Compute features
    avg_response_time = np.mean(response_times) if response_times else 8.0
    response_time_std = np.std(response_times) if len(response_times) > 1 else 2.0

    total_inactivity = sum(inactivity_periods)
    inactivity_ratio = total_inactivity / max(total_duration, 1)

    avg_answer_length = np.mean(answer_lengths) if answer_lengths else 50
    if answer_lengths and np.mean(answer_lengths) > 0:
        length_variance_coeff = np.std(answer_lengths) / np.mean(answer_lengths)
    else:
        length_variance_coeff = 0.15

    hesitation_ratio = np.mean(hesitations) / max(avg_answer_length, 1) if hesitations else 0.1

    # Engagement: inverse of long pauses + tab switches
    engagement = 1.0 - min(1.0, (tab_switches * 0.1 + inactivity_ratio))

    return {
        "avg_response_time_sec": round(float(avg_response_time), 2),
        "response_time_std": round(float(response_time_std), 2),
        "tab_switches": int(tab_switches),
        "inactivity_ratio": round(float(inactivity_ratio), 4),
        "avg_answer_length_words": round(float(avg_answer_length), 1),
        "answer_length_variance_coeff": round(float(length_variance_coeff), 4),
        "hesitation_ratio": round(float(hesitation_ratio), 4),
        "engagement_score": round(float(engagement), 4),
    }


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


def assess_integrity(session_data: dict) -> dict:
    """Run behavioral integrity assessment on interview session.
    
    Returns:
      - integrity_score: 0-100 (100 = normal, 0 = highly anomalous)
      - verdict: "normal" | "suspicious" | "flagged"
      - anomaly_score: raw Isolation Forest score
      - features: extracted behavioral features
      - risk_factors: list of concerning behaviors
    """
    features = extract_behavioral_features(session_data)
    model = _get_model()

    # Build feature vector
    feat_vec = np.array([[features[f] for f in FEATURE_ORDER]])

    # Isolation Forest: decision_function returns anomaly score
    # More negative = more anomalous
    raw_score = float(model.decision_function(feat_vec)[0])
    prediction = int(model.predict(feat_vec)[0])  # 1 = normal, -1 = anomaly

    # Convert to 0-100 integrity score
    # decision_function typically ranges from -0.5 to 0.5
    integrity_score = max(0, min(100, (raw_score + 0.5) * 100))

    # Determine verdict
    if integrity_score >= 60:
        verdict = "normal"
    elif integrity_score >= 35:
        verdict = "suspicious"
    else:
        verdict = "flagged"

    # Identify specific risk factors
    risk_factors = []
    if features["avg_response_time_sec"] < 3:
        risk_factors.append("Unusually fast responses (possible copy-paste)")
    if features["avg_response_time_sec"] > 30:
        risk_factors.append("Very slow responses (possible external help)")
    if features["tab_switches"] > 5:
        risk_factors.append(f"High tab-switch count ({features['tab_switches']})")
    if features["inactivity_ratio"] > 0.3:
        risk_factors.append("Extended inactivity periods detected")
    if features["answer_length_variance_coeff"] > 0.8:
        risk_factors.append("Inconsistent answer lengths (possible mixed sources)")
    if features["engagement_score"] < 0.4:
        risk_factors.append("Low engagement throughout session")

    return {
        "integrity_score": round(integrity_score, 1),
        "verdict": verdict,
        "anomaly_score": round(raw_score, 4),
        "is_anomaly": prediction == -1,
        "features": features,
        "risk_factors": risk_factors,
        "timestamp": datetime.now().isoformat(),
    }
