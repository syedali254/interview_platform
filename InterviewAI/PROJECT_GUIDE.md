# InterviewAI — Project Guide

> A Multi-Agent AI Interview Platform that conducts real-time voice interviews,
> builds skill graphs, and evaluates candidates using LLMs, speech AI, and emotion detection.

---

## What This Project Does (Simple Version)

1. **You upload a CV** (PDF) and **paste a Job Description**.
2. The system **parses both** using an LLM (Gemini) to extract skills, experience, and requirements.
3. It builds a **Skill Graph** — showing which skills match, which are missing, and which are extra.
4. It **generates interview questions** tailored to the candidate and role.
5. A **live AI voice interview** starts — the AI interviewer speaks questions aloud, listens to your answers via microphone, and adapts follow-up questions in real time.
6. During the interview, the system **detects your facial emotions** (happy, nervous, neutral, etc.) and **tracks distractions** (tab switching, face not visible).
7. After the interview, you get a **full report** with transcript, emotion timeline, distraction log, and metrics.

---

## How It Works (Architecture)

```
┌─────────────────────────────────────────────────────────┐
│                    React Frontend                        │
│  Upload → Graph → Questions → Setup → Interview → Report│
└────────────────────────┬────────────────────────────────┘
                         │ HTTP API
┌────────────────────────▼────────────────────────────────┐
│                  FastAPI Backend (server.py)              │
│  /api/parse-cv, /api/parse-jd, /api/build-graph,        │
│  /api/generate-questions, /api/launch-interview, /token  │
└────────────────────────┬────────────────────────────────┘
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
    ┌──────────┐  ┌───────────┐  ┌──────────┐
    │ Gemini   │  │ LiveKit   │  │ ESCO     │
    │ LLM API  │  │ Server    │  │ Skill DB │
    └──────────┘  └─────┬─────┘  └──────────┘
                        │
              ┌─────────▼─────────┐
              │   Voice Agent     │
              │ (run_agent.py)    │
              │                   │
              │ Deepgram STT ←──── Microphone
              │ Gemini LLM ──────→ Questions
              │ ElevenLabs TTS ──→ Speaker
              └───────────────────┘
```

---

## Project Structure

```
InterviewAI/
├── server.py                  ← Main backend (FastAPI) — all API endpoints
├── requirements.txt           ← Python dependencies
├── .env                       ← API keys (never commit this)
├── .env.example               ← Template for API keys
├── README.md                  ← Setup instructions
│
├── core/                      ← All backend logic
│   ├── config.py              ← Environment variables and settings
│   ├── llm.py                 ← Gemini API wrapper (call_llm, call_llm_json)
│   │
│   ├── agents/                ← LLM-powered agents
│   │   ├── cv_agent.py        ← Parses CVs (extracts skills, experience, education)
│   │   ├── jd_agent.py        ← Parses job descriptions (extracts requirements)
│   │   └── question_agent.py  ← Generates interview questions from skill analysis
│   │
│   ├── graph/                 ← Skill graph engine
│   │   ├── skill_graph.py     ← ESCO-based skill matching (matched/missing/extra)
│   │   ├── state.py           ← Interview state tracking
│   │   ├── traversal.py       ← Graph traversal for topic selection
│   │   └── visualize.py       ← Matplotlib graph visualization
│   │
│   ├── livekit/               ← Voice interview system
│   │   ├── run_agent.py       ← The AI interviewer voice agent
│   │   ├── launcher.py        ← Starts/stops LiveKit server
│   │   └── livekit.yaml       ← LiveKit server config
│   │
│   ├── evaluator/
│   │   └── evaluator.py       ← Answer scoring using LLM
│   │
│   ├── pipeline/
│   │   └── interview_loop.py  ← Interview state machine
│   │
│   └── report/
│       └── generator.py       ← Final report generator
│
├── data/
│   └── esco/                  ← ESCO skill taxonomy database
│
└── frontend/                  ← React + Vite + Tailwind
    ├── index.html             ← Entry point (loads face-api.js)
    ├── package.json           ← JS dependencies
    └── src/
        ├── App.jsx            ← Main app with step navigation
        ├── components/
        │   └── Sidebar.jsx    ← Step sidebar navigation
        └── screens/
            ├── UploadStep.jsx      ← Step 1: Upload CV + paste JD
            ├── GraphStep.jsx       ← Step 2: Skill graph visualization
            ├── QuestionsStep.jsx   ← Step 3: Generated interview questions
            ├── SetupScreen.jsx     ← Step 4: Camera/mic check
            ├── InterviewScreen.jsx ← Step 5: Live voice interview
            └── DashboardScreen.jsx ← Step 6: Interview report
```

---

## What Each Module Does

### `server.py` — The Backend
The single FastAPI server that handles everything. It serves the React frontend, exposes REST API endpoints for each step, and spawns the voice agent subprocess when an interview starts.

### `core/llm.py` — Gemini API Wrapper
Makes HTTP calls to Google's Gemini API. Used by CV parser, JD parser, question generator, and evaluator. Has `call_llm()` for plain text and `call_llm_json()` for structured JSON responses.

### `core/agents/cv_agent.py` — CV Parser
Takes a PDF or text CV → sends it to Gemini → returns structured data: name, skills, experience, education, projects. Uses PyMuPDF (`fitz`) to extract text from PDFs.

### `core/agents/jd_agent.py` — Job Description Parser
Takes raw job description text → sends it to Gemini → returns: job title, company, required skills, nice-to-have skills, responsibilities, difficulty level.

### `core/agents/question_agent.py` — Question Generator
Takes the skill analysis results → generates tailored interview questions grouped by: opening, technical, behavioural, and closing. Questions target the candidate's specific skill gaps and strengths.

### `core/graph/skill_graph.py` — Skill Graph Engine
The most unique part of the project. Uses the **ESCO** (European Skills, Competences, Qualifications) taxonomy to:
- Map candidate skills and job requirements to standardised skill URIs
- Build a NetworkX knowledge graph of skill relationships
- Perform **gap analysis**: matched skills, missing skills, extra skills
- Generate prioritised interview topics based on gaps

### `core/livekit/run_agent.py` — Voice Interview Agent
The AI interviewer that runs as a separate process. Uses:
- **Deepgram** (Speech-to-Text) — converts candidate's voice to text in real-time
- **Google Gemini** (LLM) — generates adaptive questions and responses
- **ElevenLabs** (Text-to-Speech) — speaks the interviewer's words aloud
- Runs inside a **LiveKit** room for real-time audio streaming

### `core/livekit/launcher.py` — LiveKit Server Manager
Auto-downloads and starts the LiveKit server binary. LiveKit handles the real-time audio/video transport between the browser and the voice agent.

### `core/evaluator/evaluator.py` — Answer Evaluator
Scores candidate answers using LLM-based evaluation. Considers relevance, depth, accuracy, and communication quality.

### `frontend/src/screens/InterviewScreen.jsx` — Live Interview UI
The interview screen that:
- Connects to the LiveKit room via WebSocket
- Publishes microphone + camera tracks
- Receives and plays agent audio
- Runs **face-api.js** for real-time emotion detection (happy, sad, neutral, angry, etc.)
- Detects distractions (tab switching, face not visible)
- Shows live transcript, current question, timer, and emotion badge

### `frontend/src/screens/DashboardScreen.jsx` — Interview Report
Shows the complete interview summary:
- Metrics: questions asked, duration, distractions, dominant emotion
- Emotion timeline chart (how emotions changed during the interview)
- Emotion distribution (percentage breakdown)
- Full Q&A transcript with timestamps and response times
- Distraction event log with severity levels

---

## Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Frontend | React + Vite + Tailwind CSS | UI framework |
| Backend | FastAPI (Python) | REST API server |
| LLM | Google Gemini API | CV parsing, question generation, evaluation |
| Speech-to-Text | Deepgram Nova-3 | Real-time voice transcription |
| Text-to-Speech | ElevenLabs Flash v2.5 | AI interviewer voice |
| Real-time Audio | LiveKit | WebRTC audio streaming |
| Skill Taxonomy | ESCO Database | Standardised skill matching |
| Skill Graph | NetworkX | Knowledge graph building |
| Emotion Detection | face-api.js | Browser-side facial expression recognition |
| Voice Agent | livekit-agents SDK | Orchestrates STT → LLM → TTS pipeline |

---

## API Keys You Need

| Key | Where to Get It | What It's For |
|-----|----------------|---------------|
| `GEMINI_API_KEY` | [Google AI Studio](https://aistudio.google.com/apikey) | LLM for parsing, questions, evaluation |
| `DEEPGRAM_API_KEY` | [Deepgram Console](https://console.deepgram.com) | Speech-to-text during interview |
| `ELEVENLABS_API_KEY` | [ElevenLabs](https://elevenlabs.io) | Text-to-speech for AI interviewer voice |

LiveKit runs locally with built-in dev credentials (`devkey`/`secret`) — no API key needed for local development.

---

## How to Run

```bash
# 1. Backend setup
cd InterviewAI
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt

# 2. Create .env file (copy from .env.example and add your keys)
cp .env.example .env

# 3. Frontend build
cd frontend
npm install
npm run build
cd ..

# 4. Run
python server.py
# Open http://localhost:8000
```

---

## Interview Flow (Step by Step)

1. **Upload** — Upload CV (PDF) + paste job description → click "Analyze"
2. **Graph** — Click "Build Graph" → see 3 skill graphs (matched, missing, extra)
3. **Questions** — Click "Generate Questions" → review technical + behavioral questions
4. **Setup** — Camera and mic check → must pass before proceeding
5. **Interview** — AI greets you → asks questions via voice → listens to your answers → adapts next questions → detects emotions → tracks distractions
6. **Report** — Full transcript, emotion timeline, distraction log, metrics

---

## Key Design Decisions (For Dissertation)

- **Multi-Agent Architecture**: Separate agents for CV parsing, JD parsing, question generation, and live interviewing — each with a focused LLM prompt.
- **ESCO Skill Taxonomy**: Using EU's standardised skill database instead of raw text matching — more accurate and academically rigorous.
- **Adaptive Questioning**: Questions aren't fixed — the LLM adapts based on each answer's strength.
- **Multimodal Analysis**: Combines voice (STT), language (LLM), and visual (face-api.js) signals.
- **Real-time Pipeline**: LiveKit enables sub-second audio streaming — feels like talking to a real person.
