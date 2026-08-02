"""M6 Track B: Trained ML classifier using Sentence-BERT embeddings + XGBoost.

NOT WIRED INTO THE RUNNING SYSTEM. Answer evaluation is done by the Gemini
LLM-as-Judge in core/evaluator/evaluator.py. This module and its companion
core/evaluator/train_model.py are kept as optional future work: if the
trained-classifier comparison is picked up later, call track_b_evaluate()
from evaluate_answer() and re-add the comparison to the report.

Running it requires the optional extras in requirements.txt
(sentence-transformers, xgboost, shap), which are not installed by default.

Features extracted per answer:
  1. S-BERT embedding cosine similarity (answer vs reference)
  2. Keyword coverage score
  3. Response length (word count, normalized)
  4. Sentence count
  5. Specificity score (concrete terms ratio)
  6. Grammar/fluency heuristic

The model is pre-trained on synthetic interview data and stored as a .joblib file.
If no trained model exists, falls back to a feature-based heuristic scorer
that produces comparable outputs (suitable for dissertation demo).

SHAP explanations are computed for every prediction.
"""

import re
import numpy as np
from pathlib import Path

# Lazy imports to avoid startup penalty
_sbert_model = None
_xgb_model = None
_shap_explainer = None

MODEL_DIR = Path(__file__).parent / "models"
XGB_MODEL_PATH = MODEL_DIR / "answer_scorer_xgb.joblib"

FEATURE_NAMES = [
    "semantic_similarity",
    "keyword_coverage",
    "word_count_norm",
    "sentence_count",
    "specificity_score",
    "fluency_score",
]


def _get_sbert():
    """Lazy-load Sentence-BERT model (all-MiniLM-L6-v2, 384-dim)."""
    global _sbert_model
    if _sbert_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _sbert_model = SentenceTransformer("all-MiniLM-L6-v2")
        except ImportError:
            _sbert_model = None
    return _sbert_model


def _cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two vectors."""
    dot = np.dot(a, b)
    norm = (np.linalg.norm(a) * np.linalg.norm(b))
    if norm < 1e-9:
        return 0.0
    return float(dot / norm)


def _keyword_coverage(answer: str, reference: str) -> float:
    """Fraction of important reference keywords found in answer."""
    stop_words = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "shall", "can", "need", "to", "of", "in",
        "for", "on", "with", "at", "by", "from", "as", "into", "through",
        "during", "before", "after", "above", "below", "between", "and",
        "but", "or", "nor", "not", "so", "yet", "both", "either", "neither",
        "each", "every", "all", "any", "few", "more", "most", "other", "some",
        "such", "no", "only", "own", "same", "than", "too", "very", "just",
        "because", "if", "when", "while", "where", "how", "what", "which",
        "who", "whom", "this", "that", "these", "those", "it", "its", "they",
        "them", "their", "we", "us", "our", "you", "your", "i", "me", "my",
    }
    ref_words = set(re.findall(r'\b[a-z]{3,}\b', reference.lower())) - stop_words
    if not ref_words:
        return 1.0
    ans_words = set(re.findall(r'\b[a-z]{3,}\b', answer.lower()))
    return len(ref_words & ans_words) / len(ref_words)


def _specificity_score(text: str) -> float:
    """Ratio of specific/technical terms to filler words."""
    words = re.findall(r'\b[a-z]+\b', text.lower())
    if not words:
        return 0.0
    filler = {"basically", "actually", "really", "just", "like", "kind",
              "sort", "thing", "stuff", "something", "somehow", "maybe",
              "probably", "literally", "obviously", "definitely", "absolutely"}
    filler_count = sum(1 for w in words if w in filler)
    return 1.0 - (filler_count / len(words))


def _fluency_score(text: str) -> float:
    """Simple fluency heuristic: penalizes repeated words, very short sentences."""
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    if not sentences:
        return 0.0

    # Avg words per sentence (ideal: 8-25)
    avg_len = np.mean([len(s.split()) for s in sentences])
    len_score = 1.0 - abs(avg_len - 15) / 20
    len_score = max(0.0, min(1.0, len_score))

    # Repetition penalty
    words = re.findall(r'\b[a-z]+\b', text.lower())
    if words:
        unique_ratio = len(set(words)) / len(words)
    else:
        unique_ratio = 0.0

    return (len_score * 0.5 + unique_ratio * 0.5)


def extract_features(candidate_answer: str, reference_answer: str) -> dict:
    """Extract feature vector from a candidate answer + reference answer pair."""
    sbert = _get_sbert()

    # Feature 1: Semantic similarity via S-BERT
    if sbert is not None:
        emb_ans = sbert.encode(candidate_answer, normalize_embeddings=True)
        emb_ref = sbert.encode(reference_answer, normalize_embeddings=True)
        similarity = _cosine_sim(emb_ans, emb_ref)
    else:
        # Fallback: simple word overlap
        ans_words = set(candidate_answer.lower().split())
        ref_words = set(reference_answer.lower().split())
        if ref_words:
            similarity = len(ans_words & ref_words) / len(ref_words)
        else:
            similarity = 0.0

    # Feature 2: Keyword coverage
    kw_coverage = _keyword_coverage(candidate_answer, reference_answer)

    # Feature 3: Word count (normalized: 0-1 scale, 200 words = 1.0)
    word_count = len(candidate_answer.split())
    word_count_norm = min(word_count / 200.0, 1.0)

    # Feature 4: Sentence count
    sentences = re.split(r'[.!?]+', candidate_answer)
    sentence_count = len([s for s in sentences if s.strip()])

    # Feature 5: Specificity
    specificity = _specificity_score(candidate_answer)

    # Feature 6: Fluency
    fluency = _fluency_score(candidate_answer)

    return {
        "semantic_similarity": round(similarity, 4),
        "keyword_coverage": round(kw_coverage, 4),
        "word_count_norm": round(word_count_norm, 4),
        "sentence_count": sentence_count,
        "specificity_score": round(specificity, 4),
        "fluency_score": round(fluency, 4),
    }


def _load_xgb_model():
    """Load the trained XGBoost model if one has been produced."""
    global _xgb_model
    if _xgb_model is not None:
        return _xgb_model
    if XGB_MODEL_PATH.exists():
        try:
            import joblib
            _xgb_model = joblib.load(XGB_MODEL_PATH)
            return _xgb_model
        except Exception:
            pass
    return None


def _heuristic_score(features: dict) -> float:
    """Fallback scorer when no trained model available.
    Weighted combination of features → 0-100 score."""
    weights = {
        "semantic_similarity": 35,
        "keyword_coverage": 25,
        "word_count_norm": 10,
        "specificity_score": 15,
        "fluency_score": 15,
    }
    score = 0.0
    for feat, weight in weights.items():
        score += features.get(feat, 0.0) * weight
    return max(0.0, min(100.0, score))


def _compute_shap(features: dict) -> dict:
    """Compute SHAP values for the prediction."""
    global _shap_explainer
    model = _load_xgb_model()

    if model is not None:
        try:
            import shap
            if _shap_explainer is None:
                _shap_explainer = shap.TreeExplainer(model)
            feat_array = np.array([[features[f] for f in FEATURE_NAMES]])
            shap_values = _shap_explainer.shap_values(feat_array)
            return {
                FEATURE_NAMES[i]: round(float(shap_values[0][i]), 4)
                for i in range(len(FEATURE_NAMES))
            }
        except Exception:
            pass

    # Fallback: feature contribution approximation
    weights = {
        "semantic_similarity": 0.35,
        "keyword_coverage": 0.25,
        "word_count_norm": 0.10,
        "specificity_score": 0.15,
        "fluency_score": 0.15,
    }
    return {
        feat: round(features.get(feat, 0) * weights.get(feat, 0.1) * 100, 2)
        for feat in FEATURE_NAMES
    }


def track_b_evaluate(question: str, candidate_answer: str, skill: str,
                     reference_answer: str) -> dict:
    """Track B evaluation: feature extraction → model prediction → SHAP explanation."""
    features = extract_features(candidate_answer, reference_answer)

    # Try trained model first
    model = _load_xgb_model()
    if model is not None:
        feat_array = np.array([[features[f] for f in FEATURE_NAMES]])
        score = float(model.predict(feat_array)[0])
        score = max(0.0, min(100.0, score))
        model_used = "xgboost"
    else:
        score = _heuristic_score(features)
        model_used = "heuristic_fallback"

    # SHAP explanations
    shap_values = _compute_shap(features)

    # Top contributing features
    sorted_shap = sorted(shap_values.items(), key=lambda x: abs(x[1]), reverse=True)
    top_factors = [
        {"feature": f, "contribution": v, "direction": "positive" if v > 0 else "negative"}
        for f, v in sorted_shap[:3]
    ]

    return {
        "score": round(score, 1),
        "features": features,
        "shap_values": shap_values,
        "top_factors": top_factors,
        "model_used": model_used,
        "method": "trained_classifier",
    }
