# InterviewAI

Multi-Agent AI Interview Platform with adaptive voice interviews, skill graph analysis, emotion detection, and behavioral integrity monitoring.

## Prerequisites

- **Python 3.11+**
- **Node.js 18+** (for frontend build)
- **API Keys** (see table below)
- Modern browser (Chrome/Edge recommended) with camera & microphone

## Setup & Run

### 1. Clone & install Python dependencies

```bash
cd InterviewAI
python -m venv venv

# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Create `.env` file

Copy `.env.example` to `.env` and fill in your keys:

```env
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash
DEEPGRAM_API_KEY=your_deepgram_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key
```

### 3. Build frontend

```bash
cd frontend
npm install
npm run build
cd ..
```

### 4. Run the application

```bash
python server.py
```

Open **http://localhost:8000** in your browser.

> **Note:** The LiveKit server binary auto-downloads on first interview launch (~50 MB).

### Development mode (hot-reload frontend)

```bash
# Terminal 1 — backend
python server.py

# Terminal 2 — frontend dev server (proxies API to port 8000)
cd frontend
npm run dev
```

Then open **http://localhost:5173** for hot-reloading.

---

## API Keys Required

| Service | Purpose | Get it at |
|---------|---------|-----------|
| **Gemini** | LLM — question generation, evaluation, adaptive interviewer | https://aistudio.google.com/apikey |
| **Deepgram** | Real-time Speech-to-Text | https://console.deepgram.com |
| **ElevenLabs** | Text-to-Speech (AI interviewer voice) | https://elevenlabs.io |

---

## Application Flow

```
Step 1: Upload CV (PDF/text) + Paste Job Description
Step 2: Build Skill Graph (matches skills, finds gaps)
Step 3: Generate Adaptive Interview Questions
Step 4: Device Setup (camera + mic verification)
Step 5: Live Voice Interview (AI asks, you answer)
Step 6: Dashboard (transcript, scores, emotion timeline)
```

---

## Architecture

### Adaptive Live Interview
- AI interviewer powered by **Gemini LLM** generates questions adaptively
- Strong answer → deeper probe or harder topic
- Weak answer → simpler follow-up
- Real-time voice via **LiveKit** (Deepgram STT + ElevenLabs TTS)
- Configurable end conditions: time budget / max questions / topic coverage

### Emotion & Distraction Detection
- Client-side via **face-api.js** (every 2.5s, non-blocking)
- Detects: happy, sad, angry, surprised, fearful, neutral
- Distraction alerts: tab switch, no face, multiple faces
- All events logged and shown in dashboard

---

## Project Structure

```
InterviewAI/
├── server.py              # FastAPI backend (all API endpoints)
├── requirements.txt       # Python dependencies
├── .env.example           # Environment variable template
├── core/
│   ├── config.py          # Configuration & env vars
│   ├── llm.py             # Gemini LLM wrapper
│   ├── agents/
│   │   ├── cv_agent.py    # CV parsing (PDF + text)
│   │   ├── jd_agent.py    # Job description parsing
│   │   └── question_agent.py  # Interview question generation
│   ├── evaluator/
│   │   └── evaluator.py   # Answer evaluation (LLM-as-judge)
│   ├── graph/
│   │   ├── skill_graph.py # ESCO-based skill graph builder
│   │   ├── state.py       # Interview state tracking
│   │   ├── traversal.py   # Graph traversal for skill selection
│   │   └── visualize.py   # Graph visualization utilities
│   ├── livekit/
│   │   ├── run_agent.py   # Adaptive AI interviewer agent
│   │   ├── launcher.py    # LiveKit server lifecycle manager
│   │   └── livekit.yaml   # LiveKit server configuration
│   ├── pipeline/
│   │   └── interview_loop.py  # Interview orchestration logic
│   └── report/
│       └── generator.py   # Report generation
├── data/esco/             # ESCO taxonomy data (skill relationships)
└── frontend/              # React + Vite + Tailwind CSS
    ├── src/
    │   ├── App.jsx        # Main app (step navigation + state)
    │   ├── components/    # Sidebar
    │   └── screens/       # UploadStep, GraphStep, QuestionsStep,
    │                      # SetupScreen, InterviewScreen, DashboardScreen
    ├── package.json
    └── vite.config.js
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `GEMINI_API_KEY not set` | Ensure `.env` file exists with valid key |
| LiveKit won't start | First run downloads binary — needs internet. Check port 7880 is free |
| No audio in interview | Allow microphone permission in browser. Check Deepgram key is valid |
| Frontend 404 | Run `cd frontend && npm run build` to generate `dist/` folder |
| Camera not showing | Use Chrome/Edge. Some browsers block camera on `localhost` without HTTPS |
