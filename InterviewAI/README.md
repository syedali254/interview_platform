# InterviewAI — Multi-Agent AI Interview Platform

An intelligent multi-agent system that conducts technical interviews using
LLMs, knowledge graphs, and trained ML models.

## How to Run

```bash
cd InterviewAI
pip install -r requirements.txt
streamlit run app.py
```

## Architecture

```
InterviewAI/
├── app.py                      Main application entry point
├── requirements.txt            Python dependencies
├── .env                        API keys (never commit this)
├── .gitignore
│
├── core/                       Backend modules
│   ├── config.py               Environment configuration
│   ├── gemini.py               LLM API client
│   ├── agents/
│   │   ├── cv_agent.py         M1 — CV parsing agent
│   │   └── jd_agent.py         M2 — Job description agent
│   └── graph/
│       └── skill_graph.py      M3 — Skill knowledge graph
│
├── frontend/                   UI components
│   ├── components.py           Reusable UI elements
│   └── pages/
│       ├── input_page.py       Step 1 — Upload & input
│       ├── analysis_page.py    Step 2 — Parsed results
│       └── graph_page.py       Step 3 — Skill gap analysis
│
├── data/                       Sample files & datasets
│   └── sample_jd.txt           Example job description
│
└── tests/
    └── test_pipeline.py        Integration tests
```

## Modules

| # | Module | Tech | Status |
|---|--------|------|--------|
| M1 | CV Parser | Gemini LLM | ✅ |
| M2 | JD Analyser | Gemini LLM | ✅ |
| M3 | Skill Graph | NetworkX | ✅ |
| M4 | Question Generator | Gemini + Graph | 🔜 |
| M5 | Voice Agent | Whisper + TTS | ⏳ |
| M6 | Answer Evaluation | LLM + XGBoost | ⏳ |
