# InterviewAI

> Multi-Agent AI Interview Platform — CMP7200 Masters Dissertation Project

An intelligent platform that conducts voice-based technical interviews using LLMs, evaluates candidates with dual-track scoring (LLM + ML classifier), detects behavioral anomalies, and produces explainable hiring recommendations.

## Architecture (12 Modules)

| Phase | Module | Function | Technology |
|-------|--------|----------|------------|
| 1 | M1 | CV Parsing | Gemini LLM |
| 1 | M2 | JD Understanding | Gemini LLM |
| 1 | M3 | Skill Graph | NetworkX + ESCO |
| 1 | M4 | Question Generation | LLM + Graph Traversal |
| 2 | M5 | Voice Interview | Deepgram STT + ElevenLabs TTS |
| 2 | M7 | Vision Monitor | face-api.js |
| 2 | M10 | Emotion Detection | face-api.js expressions |
| 3 | M6 | Answer Evaluation | LLM-as-Judge + S-BERT/XGBoost |
| 3 | M9 | Behavioral Integrity | Isolation Forest |
| 4 | M11 | Recommendation Fusion | Weighted scoring engine |
| 4 | M12 | Report Generation | Dashboard + templates |

## Quick Start

### Prerequisites
- **Python 3.11+** — [Download](https://www.python.org/downloads/) (check "Add to PATH")
- **Node.js 18+** — [Download](https://nodejs.org/)

### Setup (Windows)

```bash
git clone https://github.com/syedali254/interview_platform.git
cd interview_platform/InterviewAI
setup.bat
```

`setup.bat` handles everything: venv, packages, frontend build, and API key configuration.

### Run

```bash
run.bat
```

Open **http://localhost:8000** in Chrome/Edge.

### Update Dependencies

```bash
update.bat
```

## API Keys (Free)

| Service | Purpose | Get Key |
|---------|---------|---------|
| Google Gemini | LLM | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| Deepgram | Speech-to-Text | [console.deepgram.com](https://console.deepgram.com/signup) |
| ElevenLabs | Text-to-Speech | [elevenlabs.io](https://elevenlabs.io/) |

## Project Structure

```
InterviewAI/
├── setup.bat / run.bat / update.bat   ← Windows scripts
├── server.py                          ← FastAPI backend (all endpoints)
├── .env.example                       ← Environment template
├── requirements.txt                   ← Python dependencies
│
├── core/
│   ├── agents/                        ← M1, M2, M4 (CV/JD/Question agents)
│   ├── graph/                         ← M3 (Skill graph + ESCO matching)
│   ├── livekit/                       ← M5 (Voice interview agent)
│   ├── evaluator/
│   │   ├── evaluator.py              ← M6 orchestrator (dual-track)
│   │   ├── track_b.py                ← M6 Track B (S-BERT + XGBoost)
│   │   ├── integrity.py             ← M9 (Isolation Forest)
│   │   ├── fusion.py                ← M11 (Weighted recommendation)
│   │   ├── train_model.py           ← Training script for XGBoost
│   │   └── models/                   ← Saved model files
│   ├── pipeline/                      ← Interview loop state machine
│   ├── report/                        ← M12 (Report generator)
│   ├── config.py                      ← Configuration
│   └── llm.py                         ← Gemini API wrapper
│
├── frontend/                          ← React + Vite app
│   └── src/screens/                   ← UI screens (Upload→Graph→Questions→Interview→Dashboard)
│
└── proposal/                          ← Dissertation proposal (Word doc + diagrams)
```

## Key Features

- **Dual-Track Evaluation (M6)**: Every answer scored by both LLM-as-Judge AND trained XGBoost classifier with SHAP explanations. Disagreements flagged for review.
- **Behavioral Integrity (M9)**: Isolation Forest detects anomalous patterns (tab-switching, timing, hesitation).
- **Adaptive Interview**: Questions adapt based on skill graph gaps and candidate responses.
- **Real-time Emotion**: face-api.js tracks facial expressions during interview.
- **Weighted Fusion (M11)**: Final recommendation combines answer quality (50%), skill match (20%), integrity (15%), engagement (15%).

## Training the ML Model

```bash
cd InterviewAI
venv\Scripts\activate
python -m core.evaluator.train_model
```

Generates synthetic training data via LLM, extracts S-BERT features, trains XGBoost regressor.

## Manual Setup (If bat files fail)

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cd frontend && npm install && npm run build && cd ..
copy .env.example .env
# Edit .env with your API keys
python server.py
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `python not found` | Reinstall with "Add to PATH" checked |
| `npm not found` | Install Node.js from nodejs.org |
| Agent not speaking | Check API keys in `.env` |
| Port 8000 in use | Close other apps or restart |
| Camera/mic blocked | Allow in browser (lock icon) |

## License

Academic project — Birmingham City University, CMP7200.
