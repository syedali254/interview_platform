# InterviewAI — Project Documentation

## What This Project Is

InterviewAI is a Multi-Agent AI Interview Platform built as a CMP7200 Masters Dissertation project. It conducts real voice-based technical interviews with candidates, evaluates their answers using two different methods (AI judgement AND machine learning), detects if they're cheating, and produces a detailed report with a hiring recommendation.

The system has **12 modules** organized into **4 phases**:
- Phase 1: Pre-Interview (parse CV, understand job, build skill graph, generate questions)
- Phase 2: Live Interview (voice conversation, face tracking, emotion detection)
- Phase 3: Evaluation (score answers, detect cheating)
- Phase 4: Report (combine everything, make recommendation)

---

## How It Works (End-to-End Flow)

```
User uploads CV (PDF) + pastes Job Description
        ↓
M1: CV Parser extracts skills, experience, education
M2: JD Parser extracts required skills, responsibilities
        ↓
M3: Skill Graph compares CV vs JD
    → Shows: matched skills, missing skills, extra skills
        ↓
M4: Question Generator creates technical + behavioral questions
    → Questions target the skill gaps specifically
        ↓
M5: Voice Interview starts (AI speaks questions, listens to answers)
M7: Camera tracks face (attention monitoring)
M10: Detects emotions (confident, nervous, neutral)
        ↓
M6: Every answer is scored TWO ways:
    Track A: LLM reads the answer and judges it (like a human would)
    Track B: ML model extracts features and predicts a score
    → If they disagree by >20 points, answer gets flagged
        ↓
M9: Behavioral integrity checks for cheating patterns
    (tab switching, copy-paste timing, long pauses)
        ↓
M11: Fusion Engine combines ALL scores:
    - 50% answer quality
    - 20% skill coverage
    - 15% behavioral integrity
    - 15% engagement/emotion
        ↓
M12: Final Report with recommendation
    (Strong Hire / Hire / Consider / No Hire / Disqualified)
```

---

## Module Details (What Each File Does)

### Phase 1: Pre-Interview Setup

#### M1 — CV Parsing (`core/agents/cv_agent.py`)
- Takes a PDF or text CV
- Sends it to Gemini LLM with a prompt asking to extract structured data
- Returns: name, skills, experience, education, projects
- Uses PyMuPDF to read PDF files

#### M2 — JD Understanding (`core/agents/jd_agent.py`)
- Takes job description text
- LLM extracts: required skills, nice-to-have skills, responsibilities, seniority level
- Returns structured JSON

#### M3 — Skill Graph (`core/graph/skill_graph.py`)
- Uses NetworkX library to build a graph of skills
- Maps skills to ESCO taxonomy (European standard skill classification)
- Compares candidate skills vs job requirements
- Outputs: matched skills, missing skills, extra skills, match percentage
- Also identifies skill relationships (e.g., Python → Machine Learning → Deep Learning)

#### M4 — Question Generation (`core/agents/question_agent.py`)
- Takes the skill graph topics (especially gaps)
- LLM generates questions that target weak areas
- Creates: opening questions, technical questions, behavioral questions, closing
- Questions are adaptive — focused on what needs to be tested

### Phase 2: Live Interview

#### M5 — Voice Interview (`core/livekit/run_agent.py`)
- Uses LiveKit framework for real-time audio
- Deepgram API converts candidate speech → text
- ElevenLabs API converts AI text → speech
- Gemini LLM generates responses and follow-up questions
- The AI interviewer has a personality — greets candidate, asks follow-ups, handles off-topic
- Interview ends after all questions or when candidate says "end interview"

#### M7 — Vision Monitor (frontend: `InterviewScreen.jsx`)
- Uses face-api.js library in the browser
- Detects if face is present (attention monitoring)
- Only reports "no face" after 10+ consecutive misses (avoids false alarms)
- Tracks real tab switches only (not window resize or console clicks)

#### M10 — Emotion Detection (frontend: `InterviewScreen.jsx`)
- Same face-api.js library
- Detects: happy, sad, angry, fearful, disgusted, surprised, neutral
- Records emotions with timestamps throughout interview
- Used in the engagement score calculation

### Phase 3: Evaluation

#### M6 Track A — LLM-as-Judge (`core/evaluator/evaluator.py`)
- For each answer, first generates an ideal "reference answer"
- Then asks LLM to score candidate answer against reference
- Scores on 4 criteria (each 0-25): technical accuracy, completeness, clarity, relevance
- Runs evaluation TWICE with different criteria order (to avoid positional bias)
- Final score = average of both runs

#### M6 Track B — Trained ML Classifier (`core/evaluator/track_b.py`)
- Extracts 6 numerical features from each answer:
  1. Semantic similarity (S-BERT embedding distance from reference)
  2. Keyword coverage (how many key terms are mentioned)
  3. Word count (normalized)
  4. Sentence count
  5. Specificity (ratio of concrete terms vs filler words)
  6. Fluency (sentence length, word repetition)
- Feeds features to XGBoost model → predicts score 0-100
- Computes SHAP values (explains WHY it gave that score)
- If no trained model available, uses weighted heuristic formula

#### M6 Comparison (in `evaluator.py`)
- Compares Track A and Track B scores
- If disagreement > 20 points → flags answer for human review
- Final score = 60% Track A + 40% Track B

#### M9 — Behavioral Integrity (`core/evaluator/integrity.py`)
- Uses Isolation Forest (unsupervised anomaly detection)
- Trained on "normal" interview behavior patterns
- Analyzes: response timing, tab switches, inactivity, answer length consistency
- Returns integrity score (0-100) and specific risk factors
- Verdicts: normal / suspicious / flagged

### Phase 4: Reporting

#### M11 — Fusion Engine (`core/evaluator/fusion.py`)
- Weighted combination of all module outputs:
  - Answer quality: 50%
  - Skill match: 20%
  - Integrity: 15%
  - Engagement: 15%
- If integrity < 30 → automatic disqualification (overrides other scores)
- Lists strengths and concerns
- Confidence level: high / moderate

#### M12 — Report & Dashboard (frontend: `DashboardScreen.jsx`)
- Shows complete interview report
- Emotion timeline (canvas chart showing emotions over time)
- Transcript with Q&A pairs and response times
- Distraction/warning events with severity badges
- Final recommendation with score breakdown

---

## Technology Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| Backend | FastAPI (Python) | Fast, async, auto-generates API docs |
| Frontend | React + Vite | Modern SPA, fast builds |
| LLM | Google Gemini | Free tier, good quality, fast |
| Speech-to-Text | Deepgram | Real-time, accurate, $200 free credit |
| Text-to-Speech | ElevenLabs | Natural voice, low latency |
| Voice Pipeline | LiveKit | Real-time audio framework |
| Skill Graph | NetworkX + ESCO | Standard library for graphs |
| ML Classifier | XGBoost | Fast, interpretable, works with SHAP |
| Embeddings | Sentence-BERT (all-MiniLM-L6-v2) | 384-dim semantic vectors |
| Explainability | SHAP | Feature attribution for predictions |
| Anomaly Detection | Isolation Forest (scikit-learn) | Unsupervised, no labels needed |
| Face/Emotion | face-api.js | Browser-based, no server needed |

---

## File Structure

```
interview_platform/
├── run.bat                     ← One-click setup + run (from repo root)
├── proposal/                   ← Dissertation proposal document + diagrams
│
└── InterviewAI/                ← Main project
    ├── setup.bat               ← Setup script (inside project folder)
    ├── run.bat                 ← Run script (inside project folder)
    ├── update.bat              ← Update dependencies script
    ├── server.py               ← FastAPI server (all API endpoints)
    ├── .env.example            ← Template for API keys
    ├── requirements.txt        ← Python packages
    │
    ├── core/
    │   ├── config.py           ← Environment variables, thresholds
    │   ├── llm.py              ← Gemini API wrapper (call_llm, call_llm_json)
    │   │
    │   ├── agents/
    │   │   ├── cv_agent.py     ← M1: CV parsing
    │   │   ├── jd_agent.py     ← M2: JD parsing
    │   │   └── question_agent.py ← M4: Question generation
    │   │
    │   ├── graph/
    │   │   ├── skill_graph.py  ← M3: Skill graph builder + ESCO matching
    │   │   ├── state.py        ← Interview state tracker per skill
    │   │   ├── traversal.py    ← Adaptive skill selection logic
    │   │   └── visualize.py    ← Graph visualization helpers
    │   │
    │   ├── livekit/
    │   │   ├── run_agent.py    ← M5: Voice interview agent (main file)
    │   │   ├── launcher.py     ← LiveKit server launcher
    │   │   └── livekit.yaml    ← LiveKit config
    │   │
    │   ├── evaluator/
    │   │   ├── evaluator.py    ← M6: Dual-track orchestrator
    │   │   ├── track_b.py      ← M6 Track B: S-BERT + XGBoost
    │   │   ├── integrity.py    ← M9: Isolation Forest
    │   │   ├── fusion.py       ← M11: Weighted fusion
    │   │   ├── train_model.py  ← Training script for XGBoost
    │   │   └── models/         ← Saved .joblib model files
    │   │
    │   ├── pipeline/
    │   │   └── interview_loop.py ← Interview state machine
    │   │
    │   └── report/
    │       └── generator.py    ← M12: Report generation
    │
    ├── data/
    │   └── esco/               ← ESCO taxonomy data (skill classifications)
    │
    └── frontend/
        ├── package.json        ← JS dependencies
        └── src/
            ├── App.jsx         ← Main app (step navigation)
            ├── screens/
            │   ├── UploadStep.jsx      ← CV upload + JD paste
            │   ├── GraphStep.jsx       ← 3 skill graphs visualization
            │   ├── QuestionsStep.jsx   ← Generated questions display
            │   ├── SetupScreen.jsx     ← Camera/mic device setup
            │   ├── InterviewScreen.jsx ← Live interview + emotion + distraction
            │   └── DashboardScreen.jsx ← Final report + charts
            ├── components/     ← Shared UI components
            └── styles/         ← CSS
```

---

## What Is Done vs What Is Left

### ✅ Fully Implemented

| Module | Status | Notes |
|--------|--------|-------|
| M1 CV Parsing | ✅ Done | Works with PDF and text |
| M2 JD Understanding | ✅ Done | Extracts structured requirements |
| M3 Skill Graph | ✅ Done | ESCO-based, 3 graph views |
| M4 Question Generation | ✅ Done | Adaptive, targets gaps |
| M5 Voice Interview | ✅ Done | Full LiveKit pipeline |
| M6 Track A (LLM Judge) | ✅ Done | Dual-call anti-bias |
| M6 Track B (ML Classifier) | ✅ Done | S-BERT + XGBoost + SHAP |
| M6 Comparison | ✅ Done | Disagreement flagging |
| M7 Vision Monitor | ✅ Done | Face detection + attention |
| M9 Behavioral Integrity | ✅ Done | Isolation Forest |
| M10 Emotion Detection | ✅ Done | face-api.js expressions |
| M11 Fusion | ✅ Done | Weighted recommendation |
| M12 Report | ✅ Done | Dashboard with charts |
| Frontend (all screens) | ✅ Done | React + Vite |
| API endpoints | ✅ Done | FastAPI, all routes working |
| Setup automation | ✅ Done | bat files for Windows |

### ⚠️ Partially Done (Works but could be improved for dissertation)

| Item | Current State | For Higher Marks |
|------|---------------|-----------------|
| M6 Track B training | Uses heuristic fallback | Run `train_model.py` to train actual XGBoost |
| M8 Posture Analysis | Not implemented | Add MediaPipe Pose (optional per proposal) |
| M9 training data | Synthetic baseline | Collect real pilot data for better accuracy |
| Evaluation experiments | Code ready | Run comparison experiments (Cohen's Kappa) |
| SHAP visualization | Values computed | Add visual SHAP plots to dashboard |

### 📝 What's Left for Dissertation Writing

1. **Run experiments**: Use `train_model.py` to train XGBoost, then compare Track A vs Track B scores
2. **Collect metrics**: Cohen's Kappa, Spearman correlation, disagreement rate
3. **Write dissertation chapters**: Literature review, methodology, implementation, evaluation, conclusion
4. **Viva preparation**: System demo, explain architecture decisions

---

## Key Research Contribution

The main academic contribution is **Module 6** — comparing two answer evaluation approaches:

1. **LLM-as-Judge** (Track A): Flexible, contextual, but opaque and potentially biased
2. **Trained ML Classifier** (Track B): Measurable features, explainable via SHAP, but may miss nuance

The dissertation should answer: *Which approach agrees more with human ratings? Which is more consistent? Which is more explainable?*

---

## API Endpoints Summary

| Endpoint | Method | What It Does |
|----------|--------|-------------|
| `/api/parse-cv` | POST | Upload CV, get structured data |
| `/api/parse-jd` | POST | Parse job description |
| `/api/build-graph` | POST | Build skill graph from CV + JD |
| `/api/generate-questions` | POST | Generate interview questions |
| `/api/launch-interview` | POST | Start LiveKit voice interview |
| `/api/stop-interview` | POST | Stop interview session |
| `/api/evaluate` | POST | Evaluate a single answer (dual-track) |
| `/api/integrity` | POST | Assess behavioral integrity |
| `/api/fusion-report` | POST | Generate final weighted report |
| `/api/transcript` | GET | Get interview transcript |
| `/api/session` | GET | Get current session state |
| `/api/health` | GET | Health check |
| `/token` | GET | Get LiveKit token + start agent |
| `/save_transcript` | POST | Save transcript from frontend |
