# InterviewAI

AI-powered interview platform with two modes:

- **Text Mode** — Type answers to skill-based interview questions
- **LiveKit Mode** — Voice interview via LiveKit agent (self-hosted)

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Create `.env` in the project root with:
   ```
   GEMINI_API_KEY=your_key
   DEEPGRAM_API_KEY=your_key
   ELEVENLABS_API_KEY=your_key
   LIVEKIT_URL=ws://localhost:7880
   LIVEKIT_API_KEY=devkey
   LIVEKIT_API_SECRET=secret
   ```

3. Run:
   ```
   streamlit run app.py
   ```

## Project Structure

```
app.py                  # Streamlit entry point
core/
  config.py             # Configuration & env vars
  llm.py                # Gemini LLM wrapper
  agents/               # CV parsing, JD parsing, question generation
  evaluator/            # Answer evaluation (LLM-as-judge)
  graph/                # ESCO skill knowledge graph + visualization
  interview/            # Room components
  livekit/              # LiveKit voice agent + server
  pipeline/             # Interview loop orchestrator
  report/               # Report generation
data/esco/              # ESCO taxonomy CSV data
```
