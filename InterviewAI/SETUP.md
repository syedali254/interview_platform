# InterviewAI — Setup & Run Guide

## Prerequisites

1. **Python 3.11+** → https://www.python.org/downloads/ (CHECK "Add Python to PATH")
2. **Node.js 18+** → https://nodejs.org/ (LTS version)
3. **3 Free API Keys:**

| Key | Get it from | Purpose |
|-----|-------------|---------|
| GEMINI_API_KEY | https://aistudio.google.com/apikey | AI brain |
| DEEPGRAM_API_KEY | https://console.deepgram.com/signup | Voice → text |
| ELEVENLABS_API_KEY | https://elevenlabs.io/ | AI voice |

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
| Agent not speaking | Check API keys in .env |
| Camera blocked | Allow in browser (click lock icon in address bar) |
| Port 8000 in use | Restart computer |

---

## System Requirements

- Windows 10/11, 4GB+ RAM, Internet, Chrome/Edge, Mic + Camera
