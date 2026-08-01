# How to Setup InterviewAI

## What You Need First

1. **Python 3.11+** — Download from https://www.python.org/downloads/
   - IMPORTANT: Check the box "Add Python to PATH" during installation

2. **Node.js 18+** — Download from https://nodejs.org/ (LTS version)

3. **3 Free API Keys** (see below)

---

## Step-by-Step Setup

### 1. Get the code

```bash
git clone https://github.com/syedali254/interview_platform.git
cd interview_platform
```

### 2. Run the setup script

From the repo root folder, double-click `run.bat` or type:

```bash
run.bat
```

This will automatically:
- Check Python and Node.js are installed
- Create a virtual environment
- Install all Python packages
- Install frontend packages
- Build the React app
- Ask you for API keys (first time only)
- Start the server

### 3. Get Your API Keys (Free)

When the script asks, you need these 3 keys:

| Key | Where to get it | What it does |
|-----|----------------|--------------|
| GEMINI_API_KEY | https://aistudio.google.com/apikey | AI brain (generates questions, evaluates answers) |
| DEEPGRAM_API_KEY | https://console.deepgram.com/signup | Converts your voice to text |
| ELEVENLABS_API_KEY | https://elevenlabs.io/ | AI interviewer's voice |

All have free tiers — no credit card needed.

### 4. Open the App

Once the server starts, open your browser:

**http://localhost:8000**

---

## Running After First Setup

Just run:
```bash
run.bat
```
from the repo root. Or if you're inside the `InterviewAI` folder:
```bash
run.bat
```

---

## Updating Dependencies

If you pull new code:
```bash
cd InterviewAI
update.bat
```

---

## Manual Setup (If Scripts Fail)

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
notepad .env     # paste your API keys
python server.py
```

---

## Training the ML Model (Optional)

The answer evaluation works without training (uses heuristic fallback).
To train the XGBoost model for better accuracy:

```bash
cd InterviewAI
venv\Scripts\activate
python -m core.evaluator.train_model
```

This generates synthetic data via the Gemini API and trains the model (~5 minutes).

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "python not found" | Reinstall Python, check "Add to PATH" |
| "node not found" | Install Node.js from nodejs.org |
| Agent not speaking | Verify API keys in `.env` file |
| Port 8000 in use | Close other apps or restart computer |
| Camera not working | Allow permission in browser (click lock icon) |
| Import error | Run `venv\Scripts\activate` then `pip install -r requirements.txt` |

---

## System Requirements

- Windows 10/11
- 4GB RAM (8GB recommended)
- 2GB disk space
- Internet connection (for API calls)
- Microphone + Camera
- Chrome or Edge browser
