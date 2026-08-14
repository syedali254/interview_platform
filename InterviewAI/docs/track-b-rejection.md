# Rejection of the Trained-Classifier Evaluation Track (M6 Track B)

**Status:** Track B removed from the codebase on 9 August 2026.
**Purpose of this note:** preserve the evidence that justified the removal, so the
dissertation can present it as a reasoned methodological rejection supported by
measurement rather than as an unexplained descoping.

---

## 1. What Track B was

The proposal specified Module 6 as a dual-track answer evaluator:

- **Track A** — LLM-as-Judge: Gemini scores each answer against a generated
  reference answer using a four-criterion rubric.
- **Track B** — a trained supervised model: Sentence-BERT embeddings and five
  hand-crafted linguistic features feeding an XGBoost regressor, with SHAP
  values computed per prediction for explainability.

The two tracks were to be compared on agreement with human ratings (quadratic
weighted Cohen's Kappa, Spearman's ρ), consistency under paraphrase, and
explanation quality. The proposal's abstract names this comparison as the
project's primary research contribution.

Track A was implemented and is the system's live evaluator. Track B was
implemented (`core/evaluator/track_b.py`, 269 lines) together with a training
pipeline (`core/evaluator/train_model.py`, 256 lines), and a model was trained
and saved. It was never wired into the running pipeline.

### Track B feature set

| # | Feature | Definition |
|---|---------|-----------|
| 1 | `semantic_similarity` | Cosine similarity between S-BERT embeddings (all-MiniLM-L6-v2, 384-dim) of the candidate answer and the reference answer |
| 2 | `keyword_coverage` | Fraction of non-stopword reference terms appearing in the answer |
| 3 | `word_count_norm` | Word count, normalised so 200 words maps to 1.0 |
| 4 | `sentence_count` | Number of sentences |
| 5 | `specificity_score` | 1 − (filler words / total words) |
| 6 | `fluency_score` | Composite of mean sentence length and type-token ratio |

---

## 2. Evidence

### 2.1 The saved model was orphaned from its training script

The model artefact on disk was not produced by the training script that
accompanied it. Hyperparameters disagree:

| Parameter | Saved `answer_scorer_xgb.joblib` | `train_model.py` as last written |
|---|---|---|
| `n_estimators` | 100 | 200 |
| `max_depth` | 4 | 3 |
| `learning_rate` | 0.1 | 0.08 |
| `reg_lambda` | unset (`None`) | 1.0 |

File timestamps corroborate this. The model was written at **2026-08-01
18:40:07**; `train_model.py` was last modified at **2026-08-01 20:19:07**, one
hour and thirty-nine minutes later.

The change made in that interval is documented in the training script's own
docstring: an earlier version used the *strong answer as its own reference*, so
every strong training sample carried a semantic similarity of exactly 1.0 — a
value unattainable at inference time. The saved model is the output of that
earlier, defective pipeline.

### 2.2 No training run was recorded

`train_model.py` writes `training_data.json` and `training_metrics.json`
alongside the model. Neither file existed. There was therefore no record of the
training corpus, no held-out R², and no MAE — the model's performance was
entirely unmeasured.

The model file was additionally excluded from version control by
`.gitignore:15` (`core/evaluator/models/*.joblib`), so it was never committed
and existed only on the development machine.

### 2.3 Feature importance shows the leaked feature dominating

Gain-based feature importances from the saved model:

| Feature | Importance |
|---|---|
| `semantic_similarity` | **0.5434** |
| `word_count_norm` | 0.1947 |
| `keyword_coverage` | 0.1847 |
| `sentence_count` | 0.0391 |
| `specificity_score` | 0.0217 |
| `fluency_score` | 0.0164 |

One feature carries more weight than the other five combined — the signature of
a model that has learned the training artefact described in §2.1 rather than the
underlying construct.

### 2.4 Behavioural probe: the model scores excellent answers as failures

Three answers were scored against a fixed reference answer on machine learning.

| Case | Semantic similarity | Model score | System verdict |
|---|---|---|---|
| Answer identical to the reference | 1.000 | **64.7 / 100** | weak |
| Strong paraphrase, correct and complete | 0.907 | **39.2 / 100** | **gap** |
| Deliberately vague, incorrect answer | 0.362 | 29.5 / 100 | gap |

Two failures are visible:

1. A **perfect** answer — textually identical to the reference — scores 64.7,
   never approaching the 70-point strong threshold.
2. A **strong, correct paraphrase** scores 39.2, falling below
   `SCORE_WEAK_THRESHOLD = 40` and therefore reported as a *gap*, the worst
   available verdict.

The model separates a strong paraphrase from a deliberately weak answer by only
9.7 points, while separating a verbatim match from a 90.7%-similar paraphrase by
25.5 points. Discriminative power sits almost entirely in the region above
similarity 0.9, which real candidate answers do not reach. The scorer is not
usable, and its failure mode would systematically penalise candidates who
express correct ideas in their own words.

---

## 3. Why the comparison was rejected, not merely deferred

Three arguments, in order of weight.

### 3.1 The comparison was circular by construction

Proposal §4.3 sourced training labels from prompting an LLM to generate answers
at pre-defined quality levels (strong, medium, weak), with scores drawn from
bands attached to those levels. The classifier's ground truth was therefore the
language model's own judgement of answer quality.

Training a model on LLM-authored labels and then comparing it against an LLM
judge cannot validate the judge. Agreement is manufactured by the experimental
design; disagreement measures only the representational poverty of six
hand-crafted surface features. The experiment as specified could not answer the
research question it was constructed to answer.

### 3.2 The metric that gave the comparison meaning was unobtainable

Agreement with *human* ratings was the anchor that would have made the
comparison informative. Proposal §4.3 required a ~200-answer manually labelled
validation set with two independent raters, and §4.7 committed to obtaining BCU
ethical approval before involving human participants. That approval was not
sought and no raters were recruited.

Without a human gold standard, the comparison reduces to two automated scorers
disagreeing with no arbiter — a result from which no conclusion about accuracy
can be drawn.

### 3.3 The implemented artefact demonstrated the approach was fragile

§2.4 shows the trained track failing on the simplest possible test. The failure
traces to a single subtle data-handling error in the construction of the
training set. That fragility is itself a finding: a six-feature surface model
scoring open-ended technical speech is highly sensitive to how its reference
distribution is built, and offers no way to detect such an error from its own
outputs. The LLM judge, by contrast, is auditable at the point of use — it
returns a per-criterion breakdown and a natural-language rationale that a human
reader can immediately recognise as wrong.

---

## 4. What replaces it

The research question moves from *comparing two scorers* to *making one scorer
trustworthy*:

> Can an LLM-as-Judge evaluation pipeline be made sufficiently reliable and
> transparent for high-stakes assessment, through rubric-order randomisation,
> self-consistency measurement, and calibrated escalation to human review?

Every mechanism this requires is already implemented in `core/evaluator/`:

| Mechanism | Location | Addresses |
|---|---|---|
| Dual rubric orderings, scores averaged | `evaluator.py` `CRITERIA_ORDERS` | Positional bias (Stureborg et al., 2024) |
| Explicit anti-verbosity rubric rules | `evaluator.py` `JUDGE_SYSTEM_PROMPT` | Verbosity bias (Wang et al., 2024) |
| Per-answer spread between the two calls | `evaluator.py` `judge_answer()` | Self-consistency quantification |
| Consistency banding (high / moderate / low) | `evaluator.py` `CONSISTENCY_*` | Reliability classification |
| Escalation of unstable scores to a human | `evaluator.py` `flagged` | Calibrated human-in-the-loop |
| Session-level reliability statistics | `report/generator.py` `judge_reliability()` | Transparency of aggregate reliability |

**On explainability.** SHAP is lost. It is replaced by a four-criterion rubric
breakdown, the reference answer displayed alongside the candidate answer, a
natural-language rationale per answer, and a stability figure. For the actual
user — a recruiter deciding whether to trust a score — this is more actionable
than SHAP attributions over six abstract linguistic features, which cannot be
interpreted without knowing how each feature was defined.

---

## 5. Revised objectives

**Objective 4 (was: train a classifier and compare it to an LLM judge)**

> Design and implement a bias-mitigated LLM-as-Judge answer evaluation pipeline
> that scores each response against a generated reference answer under a
> four-criterion rubric, and empirically quantify its positional-bias
> sensitivity and self-consistency using repeated measurement under permuted
> rubric orderings.

**Objective 6 (was: evaluate scoring agreement, consistency and SHAP quality)**

> Evaluate the evaluation pipeline through four controlled experiments:
> discriminant validity against known answer-quality bands (Spearman's ρ and
> quadratic weighted Cohen's Kappa); invariance under paraphrase; a
> positional-bias ablation comparing single-ordering against averaged scoring;
> and rubric criterion-independence analysis testing for halo effect.

Both statistical measures named in the proposal — Cohen's Kappa and Spearman's ρ
— are retained. They are applied between repeated judge runs and against
quality-band labels, rather than between two scoring tracks.

---

## 6. What was removed

| Path | Lines | Note |
|---|---|---|
| `core/evaluator/track_b.py` | 269 | Feature extraction, model loading, SHAP, `track_b_evaluate()` |
| `core/evaluator/train_model.py` | 256 | Synthetic data generation, grouped-CV training, verification |
| `core/evaluator/models/answer_scorer_xgb.joblib` | 138 KB | Untracked by git; never committed |

Nothing in the running system imported either module. `train_model.py` was the
sole importer of `track_b.py`. `server.py`, `core/pipeline/post_interview.py`,
`core/report/report_builder.py` and `core/evaluator/score_fusion.py` never referenced them,
so removal is behaviour-preserving.

**Retained:** `core/evaluator/behavioural_integrity.py` (M9, Isolation Forest) together with
`scikit-learn` and `joblib`. M9 defines its own model path and has no dependency
on Track B.

---

## 7. Reproducing the evidence

The measurements in §2.3 and §2.4 were taken from the saved model before
deletion. To reproduce them, restore the two source files and the `.joblib` from
git history (source files only — the model artefact was never committed) and
run:

```python
import joblib, numpy as np
from core.evaluator.track_b import FEATURE_NAMES, extract_features

model = joblib.load("core/evaluator/models/answer_scorer_xgb.joblib")
print(dict(zip(FEATURE_NAMES, model.feature_importances_)))

reference = ("Machine learning is a field of artificial intelligence where models "
             "learn patterns from data to make predictions without being explicitly "
             "programmed with rules.")
features = extract_features(candidate_answer, reference)
vector = np.array([[features[name] for name in FEATURE_NAMES]])
print(float(model.predict(vector)[0]))
```

The three probe answers are recorded verbatim in §2.4 of this note and in
`verify()` within the removed `train_model.py`, recoverable from git history at
commit `1df2491` or earlier.
