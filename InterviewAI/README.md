# InterviewAI

Multi-Agent AI Interview Platform with adaptive voice interviews, emotion detection, and behavioral integrity monitoring.

## Prerequisites

- **Python 3.11+**
- **API Keys** (see `.env.example` below)
- A modern browser with camera/microphone access

## Quick Start

1. **Install dependencies:**
   ```bash
   cd InterviewAI
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Linux/Mac:
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Create `.env`** in the project root:
   ```env
   GEMINI_API_KEY=your_gemini_api_key
   GEMINI_MODEL=gemini-2.5-flash
   DEEPGRAM_API_KEY=your_deepgram_api_key
   ELEVENLABS_API_KEY=your_elevenlabs_api_key
   ```

   Optional (auto-configured for local development):
   ```env
   LIVEKIT_URL=ws://localhost:7880
   LIVEKIT_API_KEY=devkey
   LIVEKIT_API_SECRET=secret
   MAX_INTERVIEW_QUESTIONS=15
   MIN_INTERVIEW_QUESTIONS=5
   INTERVIEW_TIME_BUDGET_MINS=30
   ```

3. **Run:**
   ```bash
   streamlit run app.py
   ```

4. **Live Voice Interview:**
   - Complete Steps 1-4 in the Streamlit app (upload CV, paste JD, build graph, generate questions)
   - In Step 5, click "Launch Live Interview"
   - The LiveKit server binary auto-downloads on first run
   - Opens `http://localhost:18765/livekit` — allow camera & mic
   - Setup screen verifies devices → Begin Interview → Adaptive Q&A → Dashboard

## API Keys Required

| Service | Purpose | Get it at |
|---------|---------|-----------|
| Gemini | LLM (question gen, evaluation, adaptive interviewer) | https://aistudio.google.com/apikey |
| Deepgram | Speech-to-Text (real-time) | https://console.deepgram.com |
| ElevenLabs | Text-to-Speech (AI voice) | https://elevenlabs.io |

## Architecture

### Live Interview Flow
```
Setup Screen (cam/mic check)
    → Greeting (AI introduces itself)
    → Adaptive Q&A (LLM generates next question based on previous answer)
    → Emotion Detection (face-api.js, continuous)
    → Distraction Monitoring (tab switch, no face, multi-face)
    → End Condition (topics covered / time budget / candidate action)
    → Dashboard (transcript, emotion chart, distraction log)
```

### Adaptive Questioning
The live interviewer uses Gemini to generate each question adaptively:
- Strong answer → probe deeper or move to harder topic
- Weak answer → simpler follow-up or clarifying question
- Off-topic → redirect firmly
- Session ends based on: time budget (30 min default), max questions (15), or topic coverage

### Emotion Detection
- Client-side via `face-api.js` (TinyFaceDetector + FaceExpressionNet)
- Runs every 2.5s, non-blocking
- Detects: happy, sad, angry, surprised, fearful, disgusted, neutral
- Results feed into dashboard timeline and agent data channel

## Project Structure

```
app.py                  # Streamlit entry point (Steps 1-6)
core/
  config.py             # Configuration & env vars
  llm.py                # Gemini LLM wrapper
  agents/               # CV parsing, JD parsing, question generation
  evaluator/            # Answer evaluation (LLM-as-judge, dual-call)
  graph/                # ESCO skill knowledge graph + state + traversal
  livekit/              # LiveKit voice agent + web server + client UI
    run_agent.py        # Adaptive AI interviewer agent
    launcher.py         # LiveKit server lifecycle manager
    whisper_server.py   # HTTP server (token, client page, transcript save)
    client.html         # Full interview UI (setup → interview → dashboard)
    livekit.yaml        # LiveKit server config
  pipeline/             # Interview loop orchestrator (text mode)
  report/               # Report generation
data/esco/              # ESCO taxonomy CSV data
```
