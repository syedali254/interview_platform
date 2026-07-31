# InterviewAI — Setup Guide

> Complete setup instructions for running the AI Interview Platform.

---

## Quick Start (Automated)

**Run this file ONCE to set everything up automatically:**

```bash
setup.bat
```

Then add your API keys to `.env` (see below), and run:

```bash
run.bat
```

**Done!** Skip to [Get API Keys](#get-api-keys) if using automated setup.

---

## What You Need (Prerequisites)

These must be installed before running `setup.bat`:

1. **Python 3.11+** → https://www.python.org/downloads/
   - ✅ **CHECK "Add Python to PATH" during installation**
   
2. **Node.js 18+** → https://nodejs.org/ (LTS version)

---

## Get API Keys

You need **3 free API keys**:

| Service | Purpose | Get Key | Free Tier |
|---------|---------|---------|-----------|
| **Google Gemini** | LLM (brain) | [Get API Key](https://aistudio.google.com/apikey) | 15 req/min |
| **Deepgram** | Speech-to-Text | [Sign Up](https://console.deepgram.com/signup) | $200 credit |
| **ElevenLabs** | Text-to-Speech | [Sign Up](https://elevenlabs.io/) | 10k chars/month |

### Configure Keys

1. Copy `.env.example` to `.env`:
   ```bash
   copy .env.example .env
   ```

2. Open `.env` in Notepad and replace with YOUR keys:

```env
GEMINI_API_KEY=AIzaXXXXXXXXXXXXXXXXXXXXXXXXXXXX
DEEPGRAM_API_KEY=your_deepgram_key_here
ELEVENLABS_API_KEY=your_elevenlabs_key_here
```

3. Save and close

---

## Manual Setup (If setup.bat Fails)

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Install Python packages
pip install -r requirements.txt

# Build frontend
cd frontend
npm install
npm run build
cd ..
```

---

## Running the App

### Easy way:
```bash
run.bat
```

### Manual way:
```bash
venv\Scripts\activate
python server.py
```

**Open browser:** http://localhost:8000

Press `Ctrl+C` to stop.

---

## How to Use

1. **Upload & Parse** → Upload CV + paste JD → Click "Analyze"
2. **Skill Graph** → Build graph → View matched/missing/extra skills  
3. **Questions** → Generate questions → Review AI questions
4. **Setup** → Allow camera/mic → Test devices → Begin
5. **Interview** → AI asks questions → You answer via voice
6. **Report** → View transcript, emotions, distractions

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `python: command not found` | Reinstall Python with "Add to PATH" checked |
| `pip: command not found` | Run `venv\Scripts\activate` first |
| `npm: command not found` | Install Node.js from nodejs.org |
| Port 8000 in use | Close other apps or change port in server.py |
| Camera/Mic not working | Allow permissions in browser (click lock icon) |
| Agent not speaking | Check API keys in `.env`, see `agent_debug.log` |
| Import errors | Delete `venv`, re-run `setup.bat` |

---

## File Structure

```
InterviewAI/
├── setup.bat          ← Run ONCE to setup everything
├── run.bat            ← Run to start server
├── server.py          ← Main application
├── .env               ← Your API keys (create from .env.example)
├── requirements.txt   ← Python dependencies
├── PROJECT_GUIDE.md   ← Detailed explanation
├── core/              ← Backend (agents, graph, livekit, llm)
├── frontend/          ← React UI (src, dist)
└── venv/              ← Virtual environment (auto-created)
```

---

## System Requirements

- Windows 10/11 (or macOS/Linux with adjustments)
- 4GB RAM minimum, 8GB recommended
- 2GB free disk space
- Internet connection
- Chrome/Edge browser
- Microphone + Camera

---

## Security

- Never commit `.env` (already in `.gitignore`)
- Never share API keys publicly
- All processing is local except API calls

---

## Need Help?

- Read **PROJECT_GUIDE.md** for detailed explanations
- Check **agent_debug.log** for errors
- Verify `.env` has all 3 API keys
- Make sure venv is activated before running
