# Quick Setup Guide — InterviewAI

Follow these steps exactly to get InterviewAI running on your machine.

---

## Prerequisites (Install First)

### 1. Install Python 3.11
- Download: https://www.python.org/downloads/
- **IMPORTANT**: During installation, check ✅ "Add Python to PATH"
- Verify: Open Command Prompt and type: `python --version`
- Should show: `Python 3.11.x`

### 2. Install Node.js
- Download: https://nodejs.org/ (LTS version)
- Install with default settings
- Verify: `node --version` (should show v18+ or v20+)

### 3. Install Git (if not already installed)
- Download: https://git-scm.com/downloads
- Install with default settings

---

## Get the Code

```bash
# Clone the repository
git clone https://github.com/syedali254/interview_platform.git
cd interview_platform

# Switch to the working branch
git checkout sherali-dev2

# Navigate to the project folder
cd InterviewAI
```

---

## Get API Keys (Required)

You need **3 free API keys**:

### 1. Google Gemini API Key
1. Go to: https://aistudio.google.com/apikey
2. Click "Get API key" → "Create API key"
3. Copy the key (starts with `AIza...`)

### 2. Deepgram API Key
1. Go to: https://console.deepgram.com/signup
2. Sign up for free account ($200 free credit)
3. Go to "API Keys" → Create new key
4. Copy the key

### 3. ElevenLabs API Key
1. Go to: https://elevenlabs.io/
2. Sign up for free account (10,000 characters/month free)
3. Go to Profile → API Key
4. Copy the key

---

## Setup (One-Time)

### Step 1: Python Setup

```bash
# Create virtual environment
python -m venv venv

# Activate it (Windows)
venv\Scripts\activate

# You should see (venv) in your terminal now

# Install Python packages (takes 2-3 minutes)
pip install -r requirements.txt
```

### Step 2: Configure API Keys

1. Open the `InterviewAI` folder in File Explorer
2. Find the file `.env.example`
3. Make a copy and rename it to `.env` (remove `.example`)
4. Open `.env` in Notepad
5. Replace the placeholder values with your actual API keys:

```env
# Replace these with YOUR actual keys:
GEMINI_API_KEY=AIzaXXXXXXXXXXXXXXXXXXXXXXXXXXXX
DEEPGRAM_API_KEY=your_deepgram_key_here
ELEVENLABS_API_KEY=your_elevenlabs_key_here

# Keep these as-is:
GEMINI_MODEL=gemini-2.0-flash
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret
LIVEKIT_URL=ws://localhost:7880
```

6. Save and close

### Step 3: Frontend Build

```bash
# Go to frontend folder
cd frontend

# Install JavaScript packages (takes 1-2 minutes)
npm install

# Build the React app (takes ~30 seconds)
npm run build

# Go back to main folder
cd ..
```

---

## Running the Application

Every time you want to use InterviewAI:

```bash
# 1. Navigate to the project folder
cd path\to\interview_platform\InterviewAI

# 2. Activate virtual environment (if not already active)
venv\Scripts\activate

# 3. Start the server
python server.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**Open your browser and go to:** http://localhost:8000

---

## Using the Application

1. **Upload Step**
   - Upload a CV (PDF file)
   - Paste a job description
   - Click "Analyze CV & JD"

2. **Skill Graph**
   - Click "Build Graph"
   - Review the 3 skill graphs (Matched, Missing, Extra)

3. **Questions**
   - Click "Generate Questions"
   - Review the AI-generated interview questions

4. **Device Setup**
   - Allow camera and microphone access when prompted
   - Test your devices
   - Click "Begin Interview"

5. **Live Interview**
   - AI will greet you and start asking questions
   - Speak your answers naturally
   - Interview runs for ~15 questions or 30 minutes

6. **Report**
   - View full transcript
   - See emotion timeline
   - Check distraction events
   - Review metrics

---

## Troubleshooting

### ❌ "python: command not found"
- Python not installed or not in PATH
- Reinstall Python and check "Add to PATH"

### ❌ "ModuleNotFoundError"
- Virtual environment not activated
- Run: `venv\Scripts\activate` first

### ❌ "Port 8000 already in use"
- Another process using port 8000
- Close it or change port in `server.py` (line: `uvicorn.run(app, host="0.0.0.0", port=8000)`)

### ❌ "Camera/Mic not working"
- Check browser permissions
- Chrome/Edge: Click lock icon in address bar → Allow camera/mic
- Try refreshing the page

### ❌ "Agent not speaking"
- Check API keys in `.env`
- Check console for error messages
- Check `agent_debug.log` file for detailed errors

### ❌ "npm: command not found"
- Node.js not installed
- Install from: https://nodejs.org/

---

## Stopping the Server

Press `Ctrl+C` in the terminal where the server is running.

---

## File Structure (What's What)

```
interview_platform/
└── InterviewAI/                 ← Main project folder
    ├── server.py                ← Start this to run the app
    ├── .env                     ← Your API keys (DON'T SHARE THIS)
    ├── requirements.txt         ← Python packages list
    ├── PROJECT_GUIDE.md         ← Detailed explanation
    ├── SETUP.md                 ← This file
    │
    ├── core/                    ← Backend logic
    │   ├── agents/              ← CV/JD parsers, question generator
    │   ├── graph/               ← Skill graph engine
    │   ├── livekit/             ← Voice interview system
    │   └── ...
    │
    ├── frontend/                ← React UI
    │   ├── dist/                ← Built files (served by server.py)
    │   ├── src/                 ← React source code
    │   └── package.json         ← JS packages list
    │
    └── venv/                    ← Python virtual environment
```

---

## Quick Command Reference

```bash
# Activate environment (do this first every time)
venv\Scripts\activate

# Run the app
python server.py

# Rebuild frontend (only if you change React code)
cd frontend
npm run build
cd ..

# Install new Python package
pip install package_name

# Install new JS package
cd frontend
npm install package_name
cd ..
```

---

## System Requirements

- **OS**: Windows 10/11, macOS, or Linux
- **RAM**: 4GB minimum (8GB recommended)
- **Disk**: ~2GB free space
- **Internet**: Required for API calls (LLM, STT, TTS)
- **Browser**: Chrome, Edge, or Firefox (latest version)
- **Microphone**: Required for interview
- **Camera**: Required for emotion detection

---

## Need Help?

1. Check `agent_debug.log` file for errors
2. Read `PROJECT_GUIDE.md` for detailed explanations
3. Verify all API keys are correct in `.env`
4. Make sure virtual environment is activated (`venv\Scripts\activate`)

---

## Security Notes

- **Never commit `.env`** to Git (it's already in `.gitignore`)
- **Never share API keys** publicly
- Free tier limits:
  - Gemini: 15 requests/minute
  - Deepgram: $200 credit (~100 hours)
  - ElevenLabs: 10,000 characters/month (~7-10 interviews)

---

## What If It Still Doesn't Work?

1. Delete `venv` folder
2. Run: `python -m venv venv` again
3. Activate: `venv\Scripts\activate`
4. Reinstall: `pip install -r requirements.txt`
5. Try again

---

**That's it! You're ready to conduct AI interviews. 🎤🤖**
