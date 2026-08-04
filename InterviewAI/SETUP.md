# InterviewAI — Setup & Run Guide

## Prerequisites

**Python and Node.js install themselves.** `run.bat` checks for them and, if
they are missing, installs them via `winget` (built into Windows 10 1709+ and
all Windows 11). If winget is unavailable it tells you exactly what to install.

After an automatic install, close the window and double-click `run.bat` once
more so Windows picks up the new PATH.

**You do need API keys.** `run.bat` creates `.env` for you and opens it in
Notepad — just paste the values in:

| Key | Get it from | Required? |
|-----|-------------|-----------|
| GEMINI_API_KEY | https://aistudio.google.com/apikey | **Yes** — parsing, questions, scoring |
| DEEPGRAM_API_KEY | https://console.deepgram.com/signup | **Yes** — speech-to-text + fallback voice |
| ELEVENLABS_API_KEY | https://elevenlabs.io/ | No — preferred voice; falls back to Deepgram |

---

## How to Run

From the project root folder, double-click **`run.bat`** or type:

```
run.bat
```

First time: sets up everything automatically + asks for API keys.  
Every other time: just starts the server.

Open browser: **http://localhost:8000**

---

## Two Interview Modes

On the Setup screen you choose how to answer:

| | Voice interview | Text interview |
|---|---|---|
| Answering | Speak out loud | Type in a chat |
| Needs | Camera + microphone | Camera only |
| Attention & posture | Tracked | Tracked |
| Vocal delivery | Measured | Not applicable |
| Extra integrity check | Speech hesitation | Pasted answers flagged |
| Questions & report | **Identical** | **Identical** |

Both modes use the same interviewer, the same questions in the same order,
the same time and question limits, and produce the same report.

---

## Manual Setup (If run.bat Fails)

```bash
cd InterviewAI
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cd frontend
npm install
npm run build
cd ..
copy .env.example .env
# Edit .env with your API keys
python server.py
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| "python not found" | Reinstall Python with "Add to PATH" checked |
| "node not found" | Install Node.js from nodejs.org |
| **Agent speaks a few words then goes silent** | **ElevenLabs free quota is exhausted.** The agent now detects this and falls back to Deepgram automatically — check `agent_debug.log` for `Voice provider:`. To restore ElevenLabs, top up the account. |
| Header shows "text only" | No voice provider worked. Questions still display and the interview still scores normally. Check both `ELEVENLABS_API_KEY` and `DEEPGRAM_API_KEY`. |
| Agent not speaking at all | Check the 3 keys in `.env`, then read `agent_debug.log` |
| No attention/posture in report | Run `cd frontend && npm run vision-assets` |
| Camera blocked | Allow in browser (click lock icon in address bar) |
| Port 8000 in use | Restart computer |

### Checking your ElevenLabs quota

```bash
curl -X POST "https://api.elevenlabs.io/v1/text-to-speech/JBFqnCBsd6RMkjVDRZzb" \
  -H "xi-api-key: YOUR_KEY" -H "Content-Type: application/json" \
  -d '{"text":"test","model_id":"eleven_turbo_v2_5"}'
```

A `quota_exceeded` response means the account is out of credits. The interview
will still run — it falls back to Deepgram's voice.

---

## System Requirements

- Windows 10/11, 4GB+ RAM, Internet, Chrome/Edge, Mic + Camera
