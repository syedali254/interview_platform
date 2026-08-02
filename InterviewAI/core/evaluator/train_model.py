"""Train the XGBoost answer scorer for M6 Track B.

NOT PART OF THE RUNNING SYSTEM. Answer evaluation uses the Gemini
LLM-as-Judge; this trainer exists for the optional trained-classifier
comparison described in core/evaluator/track_b.py. It needs the optional
extras: pip install sentence-transformers xgboost shap

Run: python -m core.evaluator.train_model  [--regenerate]

Pipeline:
  1. Generate synthetic interview data with an LLM — for each question a
     separate reference answer plus strong/medium/weak candidate answers.
  2. Extract Track B features for every candidate answer, scored against the
     reference answer (never against itself).
  3. Train an XGBoost regressor and report held-out performance.
  4. Save the model and its metrics.

Why the reference answer is generated separately: an earlier version used the
strong answer as its own reference, so every strong training sample had a
semantic similarity of exactly 1.0 — a value that can never occur at
inference time. The model learned to key off that artefact and scored good
real answers far too low. Training and inference must see the same feature
distribution.
"""

import json
import sys

import numpy as np

from core.evaluator.track_b import extract_features, FEATURE_NAMES, MODEL_DIR
from core.llm import call_llm_json

TRAINING_DATA_PATH = MODEL_DIR / "training_data.json"
METRICS_PATH = MODEL_DIR / "training_metrics.json"
MODEL_PATH = MODEL_DIR / "answer_scorer_xgb.joblib"

RANDOM_SEED = 42

TOPICS = [
    "Python", "JavaScript", "SQL", "REST APIs", "Docker",
    "Machine Learning", "React", "Node.js", "Git", "CI/CD",
    "Object-Oriented Programming", "Data Structures", "Algorithms",
    "Cloud Computing", "Microservices", "Testing", "Security",
    "Database Design", "System Design", "Agile Methodology",
    "TypeScript", "Linux", "Networking", "Authentication",
    "Caching", "Message Queues", "GraphQL", "Kubernetes",
    "Design Patterns", "Performance Optimization",
]

# Score bands for each synthetic quality level.
SCORE_BANDS = {
    "strong": (75, 95),
    "medium": (40, 65),
    "weak": (10, 35),
}


def generate_synthetic_data() -> list:
    """Generate synthetic interview Q&A with quality labels using an LLM."""
    print(f"[1/4] Generating synthetic training data for {len(TOPICS)} topics...")
    rng = np.random.default_rng(RANDOM_SEED)
    samples = []

    for topic in TOPICS:
        prompt = f"""Generate one technical interview question about {topic},
then provide a reference answer and three candidate answers.

IMPORTANT: the reference answer and the strong answer must be written
independently. The strong answer should be an excellent answer phrased
differently from the reference — a real strong candidate would not reproduce
the reference word for word.

Return ONLY this JSON (no markdown, no explanation):
{{
  "question": "the interview question",
  "skill": "{topic}",
  "reference_answer": "The ideal model answer an expert would give (80-140 words)",
  "strong_answer": "An excellent answer, worded differently from the reference (80-150 words)",
  "medium_answer": "A partially correct but incomplete answer (40-80 words)",
  "weak_answer": "A vague, incorrect, or barely relevant answer (15-40 words)"
}}"""
        try:
            data = call_llm_json(prompt, temperature=0.7)
            required = ("question", "reference_answer", "strong_answer",
                        "medium_answer", "weak_answer")
            if not all(data.get(k) for k in required):
                print(f"  Skipped {topic}: incomplete response")
                continue

            samples.append({
                "question": data["question"],
                "skill": data.get("skill", topic),
                "reference_answer": data["reference_answer"],
                "answers": {
                    level: {
                        "text": data[f"{level}_answer"],
                        "score": round(float(rng.uniform(*SCORE_BANDS[level])), 1),
                    }
                    for level in ("strong", "medium", "weak")
                },
            })
            print(f"  Generated: {topic}")
        except Exception as exc:
            print(f"  Failed for {topic}: {exc}")

    return samples


def build_training_set(samples: list):
    """Extract features against the reference answer and build X, y."""
    print(f"[2/4] Extracting features from {len(samples)} questions "
          f"({len(samples) * 3} samples)...")

    X, y, groups = [], [], []
    for i, sample in enumerate(samples):
        reference = sample["reference_answer"]
        for level, answer in sample["answers"].items():
            features = extract_features(answer["text"], reference)
            X.append([features[f] for f in FEATURE_NAMES])
            y.append(answer["score"])
            groups.append(i)

    return np.array(X), np.array(y), np.array(groups)


def train_model(X, y, groups):
    """Train XGBoost and report held-out performance."""
    print(f"[3/4] Training XGBoost on {len(X)} samples...")

    import joblib
    from sklearn.model_selection import GroupKFold, cross_val_score
    from sklearn.metrics import mean_absolute_error, r2_score
    from xgboost import XGBRegressor

    def make_model():
        return XGBRegressor(
            n_estimators=200,
            max_depth=3,
            learning_rate=0.08,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_lambda=1.0,
            random_state=RANDOM_SEED,
            objective="reg:squarederror",
        )

    # Group by question so the three answers to one question never straddle a
    # fold boundary — otherwise the model sees the same reference at train and
    # test time and the score is optimistic.
    n_splits = min(5, len(set(groups)))
    cv = GroupKFold(n_splits=n_splits)

    r2_scores = cross_val_score(make_model(), X, y, groups=groups, cv=cv, scoring="r2")
    mae_scores = -cross_val_score(make_model(), X, y, groups=groups, cv=cv,
                                  scoring="neg_mean_absolute_error")

    print(f"  Grouped {n_splits}-fold CV R^2 : {r2_scores.round(3)}")
    print(f"  Mean R^2 : {r2_scores.mean():.3f} +/- {r2_scores.std():.3f}")
    print(f"  Mean MAE : {mae_scores.mean():.2f} points")

    model = make_model()
    model.fit(X, y)

    in_sample = model.predict(X)
    metrics = {
        "n_samples": int(len(X)),
        "n_questions": int(len(set(groups))),
        "features": FEATURE_NAMES,
        "cv_folds": int(n_splits),
        "cv_r2_mean": round(float(r2_scores.mean()), 4),
        "cv_r2_std": round(float(r2_scores.std()), 4),
        "cv_r2_per_fold": [round(float(s), 4) for s in r2_scores],
        "cv_mae_mean": round(float(mae_scores.mean()), 3),
        "in_sample_r2": round(float(r2_score(y, in_sample)), 4),
        "in_sample_mae": round(float(mean_absolute_error(y, in_sample)), 3),
        "feature_importance": {
            name: round(float(value), 4)
            for name, value in zip(FEATURE_NAMES, model.feature_importances_)
        },
    }

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    METRICS_PATH.write_text(json.dumps(metrics, indent=2))
    print(f"  Model saved   : {MODEL_PATH}")
    print(f"  Metrics saved : {METRICS_PATH}")

    return model, metrics


def verify(model):
    """Sanity check: a good answer should score well above a poor one."""
    print("[4/4] Verification...")
    reference = (
        "Machine learning is a field of artificial intelligence where models "
        "learn patterns from data to make predictions without being explicitly "
        "programmed with rules."
    )
    cases = [
        ("good", "Machine learning is a branch of AI where an algorithm learns "
                 "patterns directly from training data rather than following "
                 "hand written rules, and then generalises those patterns to "
                 "make predictions on data it has not seen before."),
        ("poor", "It is basically just some computer stuff that does things "
                 "automatically I think."),
    ]
    for label, answer in cases:
        features = extract_features(answer, reference)
        vector = np.array([[features[f] for f in FEATURE_NAMES]])
        print(f"  {label:5} answer -> {float(model.predict(vector)[0]):.1f}/100")


def main():
    regenerate = "--regenerate" in sys.argv

    print("=" * 62)
    print("  InterviewAI - Training Answer Evaluation Model (M6 Track B)")
    print("=" * 62)

    if TRAINING_DATA_PATH.exists() and not regenerate:
        samples = json.loads(TRAINING_DATA_PATH.read_text())
        # Reject data produced by the old schema, which lacked a separate
        # reference answer and would reintroduce the calibration bug.
        if samples and "reference_answer" in samples[0]:
            print(f"Loaded {len(samples)} cached samples from {TRAINING_DATA_PATH}")
        else:
            print("Cached data uses the old schema without a reference answer "
                  "- regenerating.")
            samples = []
    else:
        samples = []

    if not samples:
        samples = generate_synthetic_data()
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        TRAINING_DATA_PATH.write_text(json.dumps(samples, indent=2))
        print(f"  Saved {len(samples)} samples to {TRAINING_DATA_PATH}")

    if len(samples) < 5:
        print("ERROR: not enough training data. Check GEMINI_API_KEY.")
        return 1

    X, y, groups = build_training_set(samples)
    model, metrics = train_model(X, y, groups)
    verify(model)

    print()
    print(f"Training complete. Held-out R^2 = {metrics['cv_r2_mean']:.3f}, "
          f"MAE = {metrics['cv_mae_mean']:.2f} points.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
