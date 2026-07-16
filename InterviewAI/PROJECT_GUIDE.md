# InterviewAI — Complete Project Guide

## What Is This?

InterviewAI is a smart interview platform. You upload someone's CV (resume) and a job
description, and the system:

1. Reads the CV and understands the person's skills
2. Reads the job description and understands what skills are needed
3. Compares both to find skill gaps
4. Generates interview questions based on those gaps
5. Conducts a live interview (text or voice)
6. Evaluates the answers and gives a final report

---

## Project Structure (File by File)

```
InterviewAI/
├── app.py                      ★ MAIN FILE — run this to start
├── requirements.txt            List of libraries needed
├── .env                        Your secret API keys (never share this)
├── .gitignore                  Files that should NOT go on GitHub
├── README.md                   Old instructions (use this guide instead)
├── PROEJCT_GUIDE.md            This file — full explanation
│
├── core/                       ★ All the brain / backend logic
│   ├── config.py               Settings — reads API keys, set limits
│   ├── llm.py                  Talks to AI models (Gemini or Ollama)
│   ├── agents/                 Smart AI modules (each does one job)
│   │   ├── cv_agent.py         Reads CV → extracts skills, experience
│   │   ├── jd_agent.py         Reads job ad → extracts requirements
│   │   └── question_agent.py   Creates interview questions from topics
│   ├── graph/                  Knowledge graph (skill connections)
│   │   ├── skill_graph.py      Builds a map of 1200+ skills
│   │   ├── state.py            Tracks which skills are asked/verified
│   │   ├── traversal.py        Decides which skill to ask next
│   │   └── visualize.py        Draws skill graphs as images
│   ├── evaluator/
│   │   └── evaluator.py        Scores answers (LLM-as-Judge)
│   ├── pipeline/
│   │   └── interview_loop.py   Runs the live interview step by step
│   ├── report/
│   │   └── generator.py        Creates final result report
│   ├── interview/
│   │   └── room_components.py  HTML templates for the interview page
│   └── livekit/                Voice calling system (optional)
│       ├── voice.py            Speech-to-text + text-to-speech
│       ├── whisper_server.py   Mini web server for voice features
│       ├── launcher.py         Starts voice system from the app
│       ├── run_agent.py        Voice agent that speaks questions
│       ├── client.html         Browser page for voice interview
│       └── livekit.yaml        Settings for voice server
│
├── frontend/                   Extra UI files (not used anymore)
│
├── data/                       Sample files
│   ├── sample_jd.txt           Example job description for testing
│   └── esco/                   Skill database (CSV files)
│
└── tests/
    └── test_pipeline.py        Test script
```

---

## How Each File Works (Simple English)

### APP.PY — The Main Screen
This is the only file you run. It opens a webpage with 7 tabs:

| Tab | What It Does |
|-----|-------------|
| **Tab 1 — Upload** | Paste CV text or upload PDF + paste job description. Press "Run Full Pipeline" |
| **Tab 2 — Analysis** | Shows what the AI extracted from CV and Job Description |
| **Tab 3 — Skill Graph** | Shows bar charts comparing candidate skills vs job needs |
| **Tab 4 — Questions** | Generates interview questions from the skill gaps |
| **Tab 5 — Live Interview** | The actual interview — 3 modes: Text, Voice, or LiveKit (video call) |
| **Tab 6 — Report** | Shows final scores and hiring recommendation |
| **Tab 7 — Logs** | Debug log of everything that happened |

### CORE/CONFIG.PY — Settings File
Stores all settings:
- Which AI model to use (Gemini or Ollama)
- How many questions to ask (max 3)
- Score thresholds (70+ = strong, below 40 = weak)
- LiveKit server address

### CORE/LLM.PY — AI Brain
This file talks to the AI. It can use:
- **Gemini** — Google's AI (cloud, needs API key)
- **Ollama** — Local AI (runs on your own computer)

Functions:
- `call_llm(prompt)` — sends text to AI, gets text back
- `call_llm_json(prompt)` — sends text, gets JSON data back

### CORE/AGENTS/CV_AGENT.PY — Reads CV
When you upload a CV, this file:
1. Reads the text (or extracts text from PDF using PyMuPDF)
2. Asks Gemini AI to pull out: name, skills, experience, education, projects
3. Returns all that info as structured data

### CORE/AGENTS/JD_AGENT.PY — Reads Job Description
Works the same as CV agent but for job ads. Extracts:
- Job title, required skills, nice-to-have skills
- Experience level, domain/industry

### CORE/AGENTS/QUESTION_AGENT.PY — Makes Questions
Takes the skill gaps and generates interview questions. Two modes:
- **Static** — generates all questions at once (Tab 4)
- **Live** — generates one question at a time during interview (Tab 5)

### CORE/GRAPH/SKILL_GRAPH.PY — Skill Map
Builds a map of 1200+ skills from ESCO (a European skill database).
- Matches CV skills to the map
- Matches job skills to the map
- Finds gaps (what the job needs but candidate is missing)
- Returns match percentage and interview topics

### CORE/GRAPH/STATE.PY — Interview Progress
For each skill, tracks: was it asked? was it answered? what score? status?
Statuses: pending → verified_strong / verified_weak / confirmed_gap / skipped

### CORE/GRAPH/TRAVERSAL.PY — Next Question Chooser
Decides which skill to ask next. Has 4 strategies:
- **Adaptive** — picks the weakest skill first
- **BFS** — goes through skills one by one
- **DFS** — keeps asking about the same skill until done
- **Spaced** — asks about skills that haven't been asked much

### CORE/EVALUATOR/EVALUATOR.PY — Answer Scorer
When the candidate gives an answer:
1. First generates a "reference answer" (what a good answer looks like)
2. Then calls the AI twice (with shuffled criteria) to score the answer
3. Scores on: technical_accuracy, completeness, clarity, relevance
4. Final score 0-100, verdict: Strong / Weak / Gap

### CORE/PIPELINE/INTERVIEW_LOOP.PY — Interview Manager
This is the conductor. It:
1. Picks the next skill to ask (using traversal.py)
2. Generates a question (using question_agent.py)
3. Takes the answer
4. Evaluates it (using evaluator.py)
5. Decides if follow-up needed
6. Repeats until all skills covered or max questions reached

### CORE/REPORT/GENERATOR.PY — Final Report Maker
Takes all questions + answers + scores and creates:
- Overall score (weighted average)
- Per-skill breakdown
- List of strengths, gaps, development areas
- Hiring verdict: Strong Hire / Weak Hire / No Hire
- Narrative summary explaining the result

### CORE/INTERVIEW/ROOM_COMPONENTS.PY — Interview Screen
Provides the HTML/CSS for the interview page inside the app:
- Device check (mic + camera test)
- Question display card (dark themed)
- Recording status bar

---

## Voice System (Core/Livekit/)

These files handle the voice/video interview (Tab 5, third option):

### VOICE.PY — Voice Helpers
Two simple functions:
- `transcribe_audio(audio_bytes)` — sends audio to Deepgram AI → returns text
- `synthesize_speech(text)` — sends text to ElevenLabs AI → returns audio

### WHISPER_SERVER.PY — Voice Web Server
A mini web server (port 18765) that:
- Creates room tokens for LiveKit
- Serves the client webpage
- Transcribes audio files
- Saves interview transcripts
- Starts the voice agent

### LAUNCHER.PY — Voice Starter
Called from app.py when you click "Launch Live Interview":
- Starts the LiveKit server (livekit-server.exe)
- Starts the web server
- Starts the voice agent
- Returns the URL to open

### RUN_AGENT.PY — Voice Interviewer
The AI agent that:
- Connects to a LiveKit room
- Speaks questions aloud (via ElevenLabs TTS)
- Listens to answers (via Deepgram STT)
- Saves the transcript

### CLIENT.HTML — Browser Call Page
A web page you open in Chrome. It:
- Shows your webcam
- Connects to the LiveKit room
- Displays questions and transcripts
- Lets you speak answers

### LIVEKIT.YAML — Server Settings
Tells the LiveKit server: port 7880, use devkey/secret for testing.

---

## How to Run

```bash
# Step 1: Go to the project folder
cd InterviewAI

# Step 2: Install dependencies (one-time)
pip install -r requirements.txt

# Step 3: Create .env file with your API keys
# (see .env.example or ask your friend for the keys)

# Step 4: Run the app
streamlit run app.py
```

---

## What Each API Key Is For

| Key | Service | What It Does |
|-----|---------|-------------|
| GEMINI_API_KEY | Google Gemini | Powers the AI brain — reads CV, generates questions, scores answers |
| DEEPGRAM_API_KEY | Deepgram | Converts speech to text (when you speak into mic) |
| ELEVENLABS_API_KEY | ElevenLabs | Converts text to speech (when the AI talks back) |

These keys are stored in `.env` file which is NOT uploaded to GitHub.

---

## Simple Flow Diagram

```
                 ┌─────────────┐
                 │  You Upload  │
                 │  CV + Job    │
                 │  Description │
                 └──────┬──────┘
                        ▼
              ┌─────────────────┐
              │  Tab 1: Upload  │
              │  → cv_agent.py  │  Reads your CV
              │  → jd_agent.py  │  Reads job description
              └──────┬──────────┘
                     ▼
              ┌─────────────────┐
              │  Tab 2: Parse   │
              │  Shows results  │
              └──────┬──────────┘
                     ▼
              ┌─────────────────────────┐
              │  Tab 3: Skill Graph     │
              │  → skill_graph.py       │  Compares skills
              │  → visualize.py         │  Draws charts
              │  Shows match % + gaps   │
              └──────┬──────────────────┘
                     ▼
              ┌─────────────────────────┐
              │  Tab 4: Questions       │
              │  → question_agent.py    │  Generates questions
              └──────┬──────────────────┘
                     ▼
        ┌──────────────────────────────┐
        │  Tab 5: Live Interview        │
        │  ┌──────┐┌─────┐┌──────────┐ │
        │  │ Text ││Voice││ LiveKit  │ │
        │  │ type ││speak││ video    │ │
        │  │ ans  ││ans  ││ call     │ │
        │  └──┬───┘└──┬──┘└────┬─────┘ │
        │     │       │        │        │
        │     ▼       ▼        ▼        │
        │  interview_loop.py            │
        │  evaluator.py                  │
        └──────────┬───────────────────┘
                   ▼
        ┌──────────────────────┐
        │  Tab 6: Report       │
        │  → generator.py      │
        │  Shows scores +      │
        │  hiring decision     │
        └──────────────────────┘
```

---

## Tips for Your Friend

1. **Run it:** Just `streamlit run app.py`
2. **Must have:** A `.env` file with the 3 API keys
3. **Voice needs:** LiveKit server binary downloaded (auto-download on first run)
4. **Graphs don't show?** Install `matplotlib` — `pip install matplotlib`
5. **Any error?** Check Tab 7 (Logs) — it shows everything
6. **Need help?** Search the code for the function name mentioned in the error
