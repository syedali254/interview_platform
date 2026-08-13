# An Explainable Multi-Agent AI Interview Platform

**CMP7200 — Individual Master's Project · Birmingham City University · 2025–26**

Skill-graph question targeting and a bias-mitigated LLM-as-Judge evaluation pipeline.

---

## What this is

An AI interview platform that conducts an adaptive technical interview by voice or
text, targets its questioning using a knowledge graph built from the ESCO
occupational taxonomy, and scores answers through a language-model judge that is
instrumented to measure and report the reliability of its own judgements.

The research question is not whether a language model can grade an interview
answer — it plainly can — but whether a system built around one can be held
accountable for how stable its scores are.

---

## Repository layout

```
Friend-Project/
├── run.bat                  One-click setup and launch (Windows)
├── README.md                This file
│
├── InterviewAI/             The artefact
│   ├── server.py            FastAPI application and API surface
│   ├── core/                Backend modules M1–M12
│   ├── frontend/            React single-page interface
│   ├── data/esco/           ESCO taxonomy exports
│   ├── experiments/         Evaluation harness, results and figures
│   ├── tests/               72-test unit suite
│   ├── docs/                Evidence for design decisions
│   ├── SETUP.md             Setup and troubleshooting guide
│   └── PROJECT_DOCS.docx    Technical handover document
│
├── viva/                    The presentation (Assessment 3)
│   ├── CMP7200_Viva_Presentation.pptx
│   ├── VIVA_QA_PREP.md      Anticipated questions and prepared answers
│   └── build_viva.py        Rebuilds the deck from the measured results
│
├── report/                  The dissertation (Assessment 2)
│   ├── CMP7200_Project_Report.docx      ← the submission
│   ├── build_report.py      Rebuilds the document end to end
│   ├── diagrams.py          Generates all 11 architecture figures
│   ├── figkit.py            Figure layout engine with collision checking
│   ├── docx_kit.py          Document primitives
│   └── content_*.py         Chapter content
│
└── proposal/                Assessment 1, as submitted, plus the brief
```

---

## Running the system

**Windows, one click.** Double-click `run.bat`. It checks for Python and Node.js
and installs them via winget if absent, creates the virtual environment, installs
dependencies, builds the frontend, creates `.env` from its template and opens it
for your API keys, then starts the server at <http://localhost:8000>.

Three API keys are needed. `GEMINI_API_KEY` and `DEEPGRAM_API_KEY` are required;
`ELEVENLABS_API_KEY` is optional and falls back to Deepgram's voice. See
`InterviewAI/SETUP.md` for where to get them and for troubleshooting.

Manual setup, if the script fails:

```bash
cd InterviewAI
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cd frontend && npm install && npm run build && cd ..
copy .env.example .env        # then add your keys
python server.py
```

---

## Verifying the artefact

```bash
cd InterviewAI
python -m pytest tests/ -q                          # 72 unit tests, no API calls
python -m experiments.run_evaluation --figures-only  # recompute results from cache, free
python -m experiments.run_evaluation --quick         # full re-run, ~69 API calls
```

The evaluation harness caches raw scores to `experiments/results/raw_scores.json`,
so statistics and figures can be regenerated without re-spending API calls.

---

## Rebuilding the dissertation

```bash
cd report
python build_report.py
```

This renders every figure, runs the test suite to obtain the count it reports,
reads the measured statistics, and assembles the document. **No result in the
dissertation is typed in by hand** — Chapter 6 renders from
`InterviewAI/experiments/results/statistics.json`, so re-running the evaluation
and rebuilding produces a document consistent with the new numbers.

---

## Rebuilding the viva deck

```bash
cd viva
python build_viva.py
```

Twenty-two slides — eighteen for delivery, four held in reserve for questions — with
speaker notes on every slide. Findings and reflection occupy the middle third,
because critical evaluation carries 40% of that assessment.

---

## Architecture in one paragraph

Thirteen modules across four sequential phases. **Pre-interview** parses the CV
and job description, maps both onto an ESCO skill graph, and generates an
interview ordered so genuine skill gaps are probed first. **Live interview**
conducts the session over WebRTC or as typed exchanges, while attention, posture
and vocal delivery are measured in the browser — no video or audio leaves the
candidate's device. **Assessment** scores each answer twice under permuted rubric
orderings, keeping the disagreement as evidence of that score's reliability, and
assesses behavioural integrity. **Reporting** fuses the components into a
recommendation in which every number can be traced back to its inputs.

---

## Headline findings

Measured over 18 answers written at three known quality levels:

| Finding | Result |
|---|---|
| Rank-order validity | Spearman ρ = 0.920 (p < 0.001), Cohen's d = 2.98 |
| Absolute calibration | Weak 53.0, medium 92.8, strong 98.3 — medium and strong are not separable at the system's own 70-point threshold |
| Categorical agreement | Quadratic weighted κ = 0.560; exact band agreement 38.9% |
| Rubric independence | Mean inter-criterion r = 0.846 — a substantial halo effect |
| Positional stability | Mean spread 2.22 points; no answer required human escalation |

The judge ranks answers well and calibrates them badly. The instrument is
comparative, not absolute. Both defects were found by the project's own
evaluation and are reported in full in Chapter 6.

A trained-classifier second scorer was built, measured and rejected: its labels
were themselves model-generated, making the comparison circular, and the trained
model scored a correct paraphrase of its own reference answer at 39/100. The
evidence is preserved in `InterviewAI/docs/track-b-rejection.md`.

---

## Note on scope

This is a research demonstrator, not a hiring system. It runs single-user and
single-session, makes no automated hiring decision, and was evaluated entirely on
generated data — no human participants were involved at any stage. Section 7.3 of
the dissertation states the limitations in full.
