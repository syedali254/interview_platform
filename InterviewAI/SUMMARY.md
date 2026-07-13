# InterviewAI — Voice Interview System

## To Supervisor

### What's Built

A voice-based interview system where the app speaks the question, the candidate speaks the answer, and the app transcribes + evaluates it — all automatically, no buttons to click.

---

### Two Voice Options

**Option A — Streamlit Step 6 (Existing, works now)**
- Browser auto-records the candidate's voice
- Uses **server-side Whisper** (offline, very accurate) for transcription
- Uses **edge-tts** (Microsoft neural voices, natural sounding) to speak questions
- Automatic: question plays → mic opens → silence detected → transcribed → submitted

**Option B — LiveKit (New, needs API keys)**
- Full-duplex real-time voice conversation (like a phone call)
- Uses **Deepgram** (cloud STT, very fast)
- Uses **ElevenLabs** (cloud TTS, ultra-realistic voices)
- Uses **Gemini** (Google AI) for the interview brain
- Runs outside Streamlit as a standalone web page

---

### Issues Faced & Solutions

| Issue | Problem | Fix |
|---|---|---|
| **LiveKit API Changed** | LiveKit v1.6 removed `VoicePipelineAgent`, the old way to build voice apps | Rebuilt with new `Agent` + `AgentSession` pattern |
| **No LiveKit STT/TTS plugin for our tools** | No plugin exists for local Whisper or edge-tts | Built a custom HTTP server that transcodes audio between browser ↔ whisper. Circumvents LiveKit's plugin system entirely |
| **Browser speech recognition is inaccurate** | Chrome's built-in speech-to-text has ~70% accuracy on technical terms | Added server-side Whisper (industry standard, ~95% accuracy) as the transcription engine |
| **Real-time streaming is complex** | Making audio flow in real-time through Python requires deep async code | Recorded audio in the browser, sent it to a tiny local HTTP server for Whisper, got text back. Simpler than WebRTC |
| **Whisper download is slow** | faster-whisper downloads a 1.5GB model on first use | Added pre-warming on startup so the model is loaded before the user starts speaking |
| **LiveKit needs separate server** | LiveKit requires a WebRTC server process running alongside | Created `start_livekit.py` — one command launches everything |

---

### What's Implemented

- ✅ CV parsing (PDF/text)
- ✅ Job description analysis
- ✅ Question generation with skill-gap detection
- ✅ Answer evaluation with scoring
- ✅ Report generation
- ✅ Voice interview in Streamlit (auto-record, Whisper, edge-tts)
- ✅ LiveKit pipeline (agent, client, token server, launcher)
- ✅ Gemini integration (all AI brains)
- ✅ 5 questions per session limit

### Not Yet Done / Known Gaps

| Gap | Why | What's Needed |
|---|---|---|
| **No Deepgram API key** | LiveKit Option B needs `DEEPGRAM_API_KEY` | Sign up at deepgram.com (free, $200 credit) |
| **No ElevenLabs API key** | LiveKit Option B needs `ELEVENLABS_API_KEY` | Sign up at elevenlabs.io (free tier) |
| **LiveKit not integrated into Step 6** | LiveKit runs as a separate page, not inside Streamlit | Can be added later if needed |
| **Whisper model cold start** | First transcription is slow (~3s) while model loads | Already pre-warmed, but could be faster with "small" model instead of "base" |
| **No interrupt handling** | Candidate can't interrupt the question | Possible to add with Voice Activity Detection |
| **Text area still visible in Step 6** | The answer text box shows during recording | Could be hidden for cleaner UX |

---

### Quick Commands

```bash
# Run Streamlit app (Option A — works now)
cd InterviewAI
streamlit run app.py

# Run LiveKit (Option B — needs API keys)
set DEEPGRAM_API_KEY=your_key
set ELEVENLABS_API_KEY=your_key
python core/livekit/start_livekit.py
```

Branch: `sherali-dev` on GitHub
