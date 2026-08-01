"""Train XGBoost answer scorer on synthetic interview data.

Run: python -m core.evaluator.train_model

This script:
1. Generates synthetic training data (strong/medium/weak answers)
2. Extracts S-BERT features for each sample
3. Trains XGBoost regressor
4. Saves model to core/evaluator/models/answer_scorer_xgb.joblib
5. Reports training metrics
"""

import json
import numpy as np
from pathlib import Path

from core.evaluator.track_b import extract_features, FEATURE_NAMES, MODEL_DIR
from core.llm import call_llm

TRAINING_DATA_PATH = MODEL_DIR / "training_data.json"
NUM_QUESTIONS = 30  # Questions to generate


def generate_synthetic_data() -> list:
    """Generate synthetic interview Q&A with quality labels using LLM."""
    print("[1/4] Generating synthetic training data...")

    topics = [
        "Python", "JavaScript", "SQL", "REST APIs", "Docker",
        "Machine Learning", "React", "Node.js", "Git", "CI/CD",
        "Object-Oriented Programming", "Data Structures", "Algorithms",
        "Cloud Computing", "Microservices", "Testing", "Security",
        "Database Design", "System Design", "Agile Methodology",
        "TypeScript", "Linux", "Networking", "Authentication",
        "Caching", "Message Queues", "GraphQL", "Kubernetes",
        "Design Patterns", "Performance Optimization",
    ]

    samples = []

    for topic in topics[:NUM_QUESTIONS]:
        prompt = f"""Generate one technical interview question about {topic}, 
then provide 3 answers at different quality levels.

Return ONLY this JSON (no markdown, no explanation):
{{
  "question": "the interview question",
  "skill": "{topic}",
  "strong_answer": "A comprehensive, technically accurate answer (80-150 words)",
  "medium_answer": "A partially correct but incomplete answer (40-80 words)",
  "weak_answer": "A vague, incorrect, or barely relevant answer (15-40 words)"
}}"""
        try:
            from core.llm import call_llm_json
            data = call_llm_json(prompt, temperature=0.7)
            if data and "question" in data:
                samples.append({
                    "question": data["question"],
                    "skill": data["skill"],
                    "strong": {"text": data["strong_answer"], "score": np.random.uniform(75, 95)},
                    "medium": {"text": data["medium_answer"], "score": np.random.uniform(40, 65)},
                    "weak": {"text": data["weak_answer"], "score": np.random.uniform(10, 35)},
                })
                print(f"  Generated Q for: {topic}")
        except Exception as e:
            print(f"  Failed for {topic}: {e}")
            continue

    return samples


def build_training_set(samples: list) -> tuple:
    """Extract features and build X, y arrays."""
    print(f"[2/4] Extracting features from {len(samples)} questions ({len(samples)*3} samples)...")

    X_list = []
    y_list = []

    for sample in samples:
        question = sample["question"]
        # Use strong answer as reference for all comparisons
        reference = sample["strong"]["text"]

        for level in ("strong", "medium", "weak"):
            answer_text = sample[level]["text"]
            target_score = sample[level]["score"]

            features = extract_features(answer_text, reference)
            feature_vec = [features[f] for f in FEATURE_NAMES]
            X_list.append(feature_vec)
            y_list.append(target_score)

    return np.array(X_list), np.array(y_list)


def train_model(X: np.ndarray, y: np.ndarray):
    """Train XGBoost regressor."""
    print(f"[3/4] Training XGBoost on {len(X)} samples...")

    from xgboost import XGBRegressor
    from sklearn.model_selection import cross_val_score
    import joblib

    model = XGBRegressor(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        objective="reg:squarederror",
    )

    # Cross-validation
    scores = cross_val_score(model, X, y, cv=5, scoring="r2")
    print(f"  Cross-val R² scores: {scores.round(3)}")
    print(f"  Mean R²: {scores.mean():.3f} ± {scores.std():.3f}")

    # Train on full data
    model.fit(X, y)

    # Save
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_DIR / "answer_scorer_xgb.joblib")
    print(f"  Model saved to: {MODEL_DIR / 'answer_scorer_xgb.joblib'}")

    return model


def main():
    print("=" * 60)
    print("  InterviewAI — Training Answer Evaluation Model (M6 Track B)")
    print("=" * 60)
    print()

    # Check if training data already exists
    if TRAINING_DATA_PATH.exists():
        print(f"Loading existing training data from {TRAINING_DATA_PATH}")
        samples = json.loads(TRAINING_DATA_PATH.read_text())
    else:
        samples = generate_synthetic_data()
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        TRAINING_DATA_PATH.write_text(json.dumps(samples, indent=2))
        print(f"  Saved {len(samples)} samples to {TRAINING_DATA_PATH}")

    if len(samples) < 5:
        print("ERROR: Not enough training data generated. Check your GEMINI_API_KEY.")
        return

    X, y = build_training_set(samples)
    model = train_model(X, y)

    # Quick test
    print()
    print("[4/4] Quick verification...")
    test_features = extract_features(
        "Machine learning is a subset of AI that learns from data using algorithms like neural networks.",
        "Machine learning is a field of artificial intelligence where models learn patterns from data to make predictions without explicit programming."
    )
    feat_vec = np.array([[test_features[f] for f in FEATURE_NAMES]])
    pred = model.predict(feat_vec)[0]
    print(f"  Test prediction: {pred:.1f}/100")
    print()
    print("✅ Training complete!")


if __name__ == "__main__":
    main()
