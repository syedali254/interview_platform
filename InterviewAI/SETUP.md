# InterviewAI — Setup Guide

> One-file setup. Just run `run.bat` and you're done.

---

## ⚡ Quick Start (Easiest Way)

**Your friend's entire workflow:**

```bash
# 1. Get the code
git clone https://github.com/syedali254/interview_platform.git
cd interview_platform

# 2. Run this ONE file
run.bat
```

**That's it!** On first run, it will:
- Switch to the latest fixed branch automatically
- Install everything automatically
- Open Notepad for API keys
- Start the server
- Open http://localhost:8000

**Next times:** Just double-click `run.bat` → server starts!

---

## 📦 What You Need First

Install these two things (one time only):

1. **Python 3.11+** → https://www.python.org/downloads/
   - ✅ **CHECK "Add Python to PATH" during installation**
   
2. **Node.js 18+** → https://nodejs.org/ (download LTS version)

---

## 🔑 API Keys (Free, Required)

On first run, `run.bat` opens Notepad. You'll need these 3 keys:

| Service | Purpose | Get Key | Free Tier |
|---------|---------|---------|-----------|
| **Google Gemini** | AI Brain | [Get Key](https://aistudio.google.com/apikey) | 15 req/min |
| **Deepgram** | Speech→Text | [Sign Up](https://console.deepgram.com/signup) | $200 credit |
| **ElevenLabs** | Text→Speech | [Sign Up](https://elevenlabs.io/) | 10k chars/mo |

Paste them in Notepad when prompted, save, close. Done!

---

## 🎯 Complete Friend Workflow

```
Step 1: Install Python + Node.js (5 minutes)
Step 2: Clone repo (1 minute)
Step 3: Double-click run.bat (3 minutes first time)
Step 4: Paste API keys when Notepad opens
Step 5: Browser opens automatically → http://localhost:8000
```

**Total time:** ~10 minutes including downloads

---

## 📥 Alternative: Download ZIP (No Git)

```
https://github.com/syedali254/interview_platform/archive/refs/heads/sherali-dev2.zip
```

Extract → Open the `interview_platform` folder → Double-click `run.bat`

---

## 🤖 What run.bat Does

**First Run (Automatic Setup):**
1. Checks Python & Node.js installed
2. Creates Python virtual environment
3. Installs 15+ Python packages (~2 mins)
4. Installs JavaScript packages (~1 min)
5. Builds React frontend (~30 sec)
6. Creates .env file
7. Opens Notepad for API keys
8. Waits for you to save & close
9. Starts server
10. Opens http://localhost:8000

**Every Other Run:**
1. Activates virtual environment
2. Starts server
3. Done in 2 seconds!

---

## 🎮 Using the App

1. **Upload & Parse** → Upload CV (PDF) + paste job description → Click "Analyze"
2. **Skill Graph** → Click "Build Graph" → See 3 graphs (matched/missing/extra skills)
3. **Questions** → Click "Generate Questions" → Review AI-generated questions
4. **Device Setup** → Allow camera & mic → Test → Click "Begin Interview"
5. **Live Interview** → AI asks questions via voice → You answer
6. **Dashboard** → Full report with transcript, emotion timeline, metrics

---

## 🛠 Troubleshooting

| Problem | Solution |
|---------|----------|
| `python not found` | Reinstall Python, check "Add to PATH" |
| `node not found` | Install Node.js from nodejs.org |
| Setup hangs | Check internet connection |
| Port 8000 in use | Close other apps or restart PC |
| Camera/mic not working | Allow browser permissions (click lock icon) |
| Agent not speaking | Check `.env` has correct API keys |
| Still broken | Delete `venv` folder, run `run.bat` again |

---

## 📂 Project Structure

```
interview_platform/
├── run.bat                ← Double-click this!
├── InterviewAI/
│   ├── .env               ← API keys (auto-created)
│   ├── server.py          ← FastAPI backend
│   ├── PROJECT_GUIDE.md   ← Detailed explanation
│   ├── core/              ← Backend logic
│   │   ├── agents/        ← CV/JD parsers, question generator
│   │   ├── graph/         ← Skill graph (ESCO-based)
│   │   └── livekit/       ← Voice interview system
│   ├── frontend/          ← React UI
│   │   ├── dist/          ← Built files (auto-generated)
│   │   └── src/           ← Source code
│   └── venv/              ← Python environment (auto-created)
```

---

## 💻 System Requirements

- Windows 10/11 (macOS/Linux with minor tweaks)
- 4GB RAM (8GB recommended)
- 2GB free disk space
- Internet connection
- Chrome or Edge browser (latest)
- Microphone (required)
- Camera (required for emotion detection)

---

## 🔒 Security

- `.env` is never committed (in `.gitignore`)
- Never share your API keys
- All processing is local except API calls
- No data stored on external servers

---

## 📚 Next Steps

- Read **PROJECT_GUIDE.md** for how everything works
- Check **agent_debug.log** if something fails
- Verify `.env` contains all 3 API keys
- Join camera/mic must be allowed in browser

---

## ✋ Manual Setup (Only If run.bat Fails)

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

cd frontend
npm install
npm run build
cd ..

copy .env.example .env
notepad .env  # Add your API keys

python server.py
```

---

**That's it!** Your friend just clones and runs one file. 🚀
