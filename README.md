# InterviewIQ — AI Interview Platform

## Setup
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set your Groq API key:
   - Linux/macOS: `export GROQ_API_KEY="your_key_here"`
   - Windows: `set GROQ_API_KEY=your_key_here`
   - Or create a `.env` file based on `.env.example`
4. Run the app: `streamlit run app.py`

## Testing Individual Modules
Each module can be tested independently:
```bash
python -m utils.llm_client
python -m utils.schema_validator
python -m utils.document_loader
python -m models.skill_extractor
```

## Project Structure
| Path | Purpose |
|------|---------|
| `config.py` | All thresholds, model names, constants |
| `utils/llm_client.py` | Centralized Groq API wrapper |
| `utils/schema_validator.py` | LLM JSON response validation |
| `utils/document_loader.py` | CV (PDF/txt) and JD loading |
| `models/skill_extractor.py` | M1 + M2: skill extraction from CV/JD |
| `models/skill_graph.py` | M3: skill relationship graph |
| `models/question_generator.py` | M4: interview question generation |
| `models/voice_agent.py` | M5: voice interaction (TTS/STT) |
| `models/evaluator.py` | M6: dual-track response evaluation |
| `models/report_generator.py` | M11 + M12: final report generation |
| `app.py` | Streamlit frontend |
| `pipeline.py` | Full pipeline orchestration |

## Architecture
The platform runs a 4-phase pipeline:
1. **Skill Extraction** — Parse CV + JD, identify required vs. possessed skills
2. **Graph Construction** — Build skill relationship graph, plan interview order
3. **Voice Interview** — Ask questions, capture audio, transcribe responses
4. **Evaluation** — Dual-track scoring (LLM semantic + SBERT feature), fusion, report
