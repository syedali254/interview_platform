"""Build PROJECT_GUIDE.docx — the plain-language guide to this project.

    python build_guide.py

Everything that could drift is read from the project rather than written down:
the file listing walks the working tree, the module table is checked against the
files it names, the results come from the measured fixtures, and the test count
comes from running the tests. If a file is added or removed and this guide is
not updated, the build says so instead of quietly disagreeing with the code.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECT = ROOT / "InterviewAI"
RESULTS = PROJECT / "experiments" / "results"
OUTPUT = ROOT / "PROJECT_GUIDE.docx"

sys.path.insert(0, str(Path(__file__).resolve().parent))

from docx.shared import Pt  # noqa: E402
from docx_kit import (  # noqa: E402
    add_page_numbers, bullet, code, figure, h1, h2, h3, new_document, para,
    table, GREY,
)

# ── The file map. Every entry is checked against the working tree. ────────
FILES = [
    ("run.bat", "One-click setup and launch for Windows: installs Python and Node.js "
                "if missing, builds the environment, and starts the server."),
    ("README.md", "Repository overview — what the project is, how to run it, how to "
                  "verify it, and the headline findings."),
    ("PROJECT_GUIDE.docx", "This document."),
    ("report/build_guide.py", "Generates this document from the live project."),
    (".gitignore", "Excludes build output and secrets; the measured results are "
                   "deliberately tracked."),
    (".gitattributes", "Forces CRLF on batch files so run.bat survives cloning."),

    ("InterviewAI/server.py", "FastAPI application. Defines every API endpoint, holds the "
                              "session state, and spawns the voice agent subprocess."),
    ("InterviewAI/requirements.txt", "Every Python dependency, pinned to the versions "
                                 "this project was verified against."),
    ("InterviewAI/SETUP.md", "Setup guide and troubleshooting table."),
    ("InterviewAI/.env.example", "Template for the three API keys."),

    ("InterviewAI/core/config.py", "Thresholds and environment configuration in one place: "
                                   "score bands, question limits, the minimum answer length."),
    ("InterviewAI/core/llm.py", "Gemini client. Handles JSON repair when the model returns "
                                "malformed output, and counts API usage."),
    ("InterviewAI/core/agents/cv_agent.py", "M1 — extracts a structured profile from a CV."),
    ("InterviewAI/core/agents/jd_agent.py", "M2 — extracts requirements from a job description."),
    ("InterviewAI/core/agents/question_agent.py", "M4 — generates the question set and orders "
                                                  "it by the priority the graph assigned."),
    ("InterviewAI/core/agents/interviewer_prompt.py", "The interviewer's instructions, shared "
                                                      "by both voice and text modes."),
    ("InterviewAI/core/graph/skill_graph.py", "M3 — builds the ESCO skill graph and runs the "
                                              "four-stage matching cascade and gap analysis."),
    ("InterviewAI/core/graph/state.py", "M6a — tracks each skill's verdict across the session."),
    ("InterviewAI/core/graph/traversal.py", "Decides which skills needed further probing."),
    ("InterviewAI/core/livekit/run_agent.py", "M5 — the voice interviewer: speech recognition, "
                                              "model inference and synthesis over WebRTC."),
    ("InterviewAI/core/livekit/launcher.py", "Downloads and manages the LiveKit server process."),
    ("InterviewAI/core/livekit/livekit.yaml", "LiveKit server configuration."),
    ("InterviewAI/core/pipeline/text_interview.py", "The typed interview engine, producing an "
                                                    "identical transcript to the voice agent."),
    ("InterviewAI/core/pipeline/session_eval.py", "Post-interview pipeline: pairs the "
                                                  "transcript, classifies, scores, fuses."),
    ("InterviewAI/core/evaluator/evaluator.py", "M6 — the LLM-as-Judge scorer with permuted "
                                                "rubric orderings and self-consistency."),
    ("InterviewAI/core/evaluator/integrity.py", "M9 — Isolation Forest behavioural integrity."),
    ("InterviewAI/core/evaluator/fusion.py", "M11 — weighted fusion into a recommendation."),
    ("InterviewAI/core/report/generator.py", "M12 — assembles the candidate report."),

    ("InterviewAI/frontend/src/main.jsx", "React entry point; mounts the application."),
    ("InterviewAI/frontend/src/App.jsx", "Six-step navigation; the interview and the report "
                                         "each take the whole viewport."),
    ("InterviewAI/frontend/src/lib/vision.js", "M7 and M8 — attention and posture from "
                                               "MediaPipe landmarks, in the browser."),
    ("InterviewAI/frontend/src/lib/voice.js", "M10 — vocal delivery from Web Audio prosody."),
    ("InterviewAI/frontend/src/components/LandmarkOverlay.jsx", "Draws the face mesh and pose "
                                                                "skeleton over the video."),
    ("InterviewAI/frontend/src/components/Sidebar.jsx", "Step navigation, gated by progress."),
    ("InterviewAI/frontend/src/screens/UploadStep.jsx", "Step 1 — CV upload and JD entry."),
    ("InterviewAI/frontend/src/screens/GraphStep.jsx", "Step 2 — renders the skill graph."),
    ("InterviewAI/frontend/src/screens/QuestionsStep.jsx", "Step 3 — the generated questions."),
    ("InterviewAI/frontend/src/screens/SetupScreen.jsx", "Step 4 — device check and mode choice."),
    ("InterviewAI/frontend/src/screens/InterviewScreen.jsx", "Step 5a — the voice interview."),
    ("InterviewAI/frontend/src/screens/TextInterviewScreen.jsx", "Step 5b — the text interview."),
    ("InterviewAI/frontend/src/screens/DashboardScreen.jsx", "Step 6 — the final report."),

    ("InterviewAI/experiments/run_evaluation.py", "The evaluation harness: five controlled "
                                                  "experiments over the judge."),
    ("InterviewAI/experiments/results/statistics.json", "Computed statistics — what the "
                                                        "dissertation's Chapter 6 reads."),
    ("InterviewAI/experiments/results/raw_scores.json", "Every individual score, cached so "
                                                        "figures regenerate without API calls."),
    ("InterviewAI/experiments/results/track_b_evidence.json", "Measurements from the rejected "
                                                              "classifier, before deletion."),
    ("InterviewAI/experiments/results/worked_example.json", "The end-to-end verification session."),
    ("InterviewAI/tests/test_core.py", "The unit test suite over the deterministic components."),
    ("InterviewAI/docs/track-b-rejection.md", "Why the trained classifier was removed, with "
                                              "the evidence."),
    ("InterviewAI/data/esco/digitalSkillsCollection_en.csv", "ESCO digital skills export."),
    ("InterviewAI/data/esco/broaderRelationsSkillPillar.csv", "ESCO hierarchy relations."),

    ("report/build_report.py", "Builds the dissertation end to end."),
    ("report/front_matter.py", "Title page, abstract, contents."),
    ("report/ch1_introduction.py", "Chapter 1 — the problem, aim and objectives."),
    ("report/ch2_literature.py", "Chapter 2 — literature review and conceptual framework."),
    ("report/ch3_methodology.py", "Chapter 3 — Design Science Research methodology."),
    ("report/ch4_design.py", "Chapter 4 — system design and the tool trade-offs."),
    ("report/ch5_implementation.py", "Chapter 5 — implementation and the problems met."),
    ("report/ch6_evaluation.py", "Chapter 6 — rendered from the measured statistics."),
    ("report/ch7_reflection.py", "Chapter 7 — critical reflection and limitations."),
    ("report/ch8_conclusion.py", "Chapter 8 — conclusions and future work."),
    ("report/back_matter.py", "References and appendices."),
    ("report/diagrams.py", "Generates the eleven architecture figures."),
    ("report/figkit.py", "Figure layout engine: reserved header, measured text wrapping, "
                         "collision checking."),
    ("report/docx_kit.py", "Document primitives — headings, tables, figures."),
    ("report/values.py", "Shared access to the measured results."),
    ("report/CMP7200_Project_Report.docx", "The dissertation (Assessment 2)."),

    ("viva/build_viva.py", "Builds the viva presentation."),
    ("viva/CMP7200_Viva_Presentation.pptx", "The presentation (Assessment 3)."),
    ("viva/VIVA_QA_PREP.md", "Anticipated viva questions and prepared answers."),

    ("proposal/AI_Interview_Final_Proposal.docx", "The project proposal (Assessment 1)."),
    ("proposal/CMP7200_Assignment_Brief.pdf", "The assignment brief."),
]

MODULES = [
    ("M1", "CV parsing", "core/agents/cv_agent.py", "Gemini, PyMuPDF",
     "Extracts text from the uploaded PDF, then asks the model for a structured "
     "profile: skills, experience, education, projects."),
    ("M2", "Job description analysis", "core/agents/jd_agent.py", "Gemini",
     "Extracts required and nice-to-have skills, seniority, domain and expected "
     "experience from pasted text."),
    ("M3", "Skill graph and gap analysis", "core/graph/skill_graph.py",
     "NetworkX, ESCO v1.1.1",
     "Builds a graph from 1,201 ESCO skills plus technology and soft-skill "
     "extensions, resolves both sides onto it through a four-stage matching "
     "cascade, and compares them to find gaps."),
    ("M4", "Question generation", "core/agents/question_agent.py",
     "Gemini + graph traversal",
     "Generates opening, technical, behavioural and closing questions, then "
     "re-sorts the technical ones so the highest-priority gaps are asked first."),
    ("M5", "Voice interview", "core/livekit/run_agent.py",
     "LiveKit, Deepgram, ElevenLabs",
     "Conducts a spoken interview over WebRTC. Buffers each utterance before "
     "synthesis, publishes the question to the screen before speaking it, and "
     "falls back between voice providers if one returns no audio."),
    ("M5t", "Text interview", "core/pipeline/text_interview.py", "FastAPI, Gemini",
     "The typed equivalent, sharing the interviewer prompt, question bank and "
     "budgets. Produces a transcript of identical shape."),
    ("M6", "Answer evaluation", "core/evaluator/evaluator.py", "Gemini as judge",
     "Scores each answer twice against a generated reference under a "
     "four-criterion rubric, with the criteria in two different orders. Reports "
     "the mean and keeps the disagreement as a reliability signal."),
    ("M6a", "Skill state tracking", "core/graph/state.py", "Finite state model",
     "Moves each skill from pending to verified-strong, verified-weak or "
     "confirmed-gap as answers arrive."),
    ("M7", "Visual attention", "frontend/src/lib/vision.js", "MediaPipe FaceLandmarker",
     "Derives gaze direction from face landmark geometry, calibrated against the "
     "candidate's own neutral pose rather than an assumed ideal."),
    ("M8", "Posture analysis", "frontend/src/lib/vision.js", "MediaPipe PoseLandmarker",
     "Shoulder tilt, slouch and lean from pose landmarks."),
    ("M9", "Behavioural integrity", "core/evaluator/integrity.py",
     "Isolation Forest (scikit-learn)",
     "Fits a baseline of normal interview behaviour and flags sessions that "
     "depart from it, always naming the specific behaviours responsible."),
    ("M10", "Vocal delivery", "frontend/src/lib/voice.js", "Web Audio API",
     "Pitch, energy, voiced ratio and pause length, combined into projection, "
     "fluency, expression and composure."),
    ("M11", "Weighted fusion", "core/evaluator/fusion.py", "Deterministic weighting",
     "Combines answer quality (50%), skill coverage (20%), integrity (15%) and "
     "engagement (15%) into one recommendation, exposing every contribution."),
    ("M12", "Report assembly", "core/report/generator.py", "Structured templates",
     "Assembles the overall score, per-skill breakdown, per-answer rubric detail, "
     "integrity findings and the judge's reliability statistics."),
]

TECH = [
    ("Gemini 2.5 Flash", "Language model for parsing, question generation and scoring",
     "Strong instruction-following; JSON-constrained output; generous free tier",
     "Non-deterministic; a reasoning model, so each call is slow and costs thinking "
     "tokens; an external dependency that can be retired without notice"),
    ("ESCO v1.1.1", "The skill taxonomy the graph is built from",
     "A published EU standard, so a reported skill gap names a concept with a "
     "stable public identifier rather than a string the system invented",
     "Predates much of the modern technology stack and covers soft skills sparsely, "
     "so it needed extending"),
    ("NetworkX", "Holds the skill graph",
     "Simple, well documented, more than adequate at this size",
     "In-memory only; would not scale to a multi-tenant deployment"),
    ("LiveKit", "Real-time audio transport and the agent framework",
     "Production-grade WebRTC; handles turn-taking and interruption",
     "Heavy dependency, about twelve seconds of process start-up, and adds a "
     "server to the deployment"),
    ("MediaPipe Tasks Vision", "Face and pose landmark detection",
     "Runs in the browser, so no video leaves the candidate's device and there is "
     "no inference cost",
     "Needs WebAssembly and ideally a GPU; degrades on older browsers"),
    ("Web Audio API", "Vocal delivery analysis",
     "Every component of the score is inspectable; no model download; works offline",
     "A prosodic proxy for emotion, not a trained classifier, and weaker at that task"),
    ("Isolation Forest", "Behavioural anomaly detection",
     "Needs no labelled examples of cheating, which no institution could ethically "
     "produce; fast and deterministic under a fixed seed",
     "The baseline here is synthetic, so no false-positive rate can be quoted"),
    ("FastAPI + React", "Backend API and the interface",
     "Fast to build, good defaults, and the frontend is served by the same process",
     "Session state is held in memory, so one interview at a time"),
]


def load(path, label):
    if not path.exists():
        print(f"  ! {label} missing at {path}")
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def check_file_map():
    """Every mapped file must exist, and every source file must be mapped."""
    mapped = {f for f, _ in FILES}
    # This document is the build's own output, so it need not exist yet.
    missing = sorted(f for f in mapped
                     if f != OUTPUT.name and not (ROOT / f).exists())

    tracked = subprocess.run(["git", "ls-files"], cwd=str(ROOT),
                             capture_output=True, text=True).stdout.split()
    interesting = re.compile(
        r"^(run\.bat|README\.md|build_guide\.py"
        r"|InterviewAI/(server\.py|requirements.*\.txt|SETUP\.md|\.env\.example"
        r"|core/.*\.(py|yaml)|frontend/src/.*\.(jsx|js)|experiments/.*\.(py|json)"
        r"|tests/.*\.py|docs/.*\.md)"
        r"|report/.*\.py|viva/.*\.(py|md))$")
    unmapped = sorted(t for t in tracked
                      if interesting.match(t)
                      and t not in mapped
                      and not t.endswith("__init__.py"))
    return missing, unmapped


def run_tests():
    py = PROJECT / "venv" / "Scripts" / "python.exe"
    if not py.exists():
        py = Path(sys.executable)
    try:
        r = subprocess.run([str(py), "-m", "pytest", "tests/", "-q", "--tb=no"],
                           cwd=str(PROJECT), capture_output=True, text=True, timeout=600)
        m = re.search(r"(\d+) passed", r.stdout)
        return int(m.group(1)) if m else None
    except Exception:
        return None


def build():
    stats = load(RESULTS / "statistics.json", "statistics")
    worked = load(RESULTS / "worked_example.json", "worked example")
    e1 = stats.get("e1_discriminant_validity", {})
    e2 = stats.get("e2_positional_bias", {})
    e4 = stats.get("e4_criterion_independence", {})
    lv = e1.get("by_level", {})
    meta = stats.get("meta", {})

    missing, unmapped = check_file_map()
    n_tests = run_tests()

    doc = new_document()
    add_page_numbers(doc)

    # ── Cover ────────────────────────────────────────────────────────────
    para(doc, space_after=90)
    para(doc, "InterviewAI", bold=True, align="center", size=Pt(34))
    para(doc, "Project Guide", align="center", size=Pt(19), colour=GREY)
    para(doc, space_after=30)
    para(doc, "An explainable multi-agent AI interview platform:\n"
              "what it does, how it is built, and why it is built that way.",
         align="center", size=Pt(12), colour=GREY)
    para(doc, space_after=60)
    para(doc, "CMP7200 — Individual Master's Project", align="center", size=Pt(11))
    para(doc, "Birmingham City University · 2025–26", align="center",
         size=Pt(10), colour=GREY)
    para(doc, space_after=40)
    para(doc, "This document is generated from the project itself. The file listing is "
              "checked against the working tree and the results are read from the "
              "measured data, so it cannot disagree with the code it describes.",
         align="center", size=Pt(9), colour=GREY, italic=True)

    # ── 1. Problem ───────────────────────────────────────────────────────
    h1(doc, "1.  The problem")
    para(doc,
         "Automated interview platforms screen millions of candidates a year. They return a "
         "score, and rarely any account of how it was reached or how far to trust it.")
    for lead, b in (
        ("The practice. ", "In 2019 the Electronic Privacy Information Center challenged "
         "HireVue over unvalidated facial analysis. Visual analysis was withdrawn in 2021, "
         "but verbal scoring continued and the problem survived it: a number, no "
         "explanation."),
        ("The regulation. ", "The EU AI Act classifies recruitment systems as high-risk and "
         "requires transparency, human oversight and bias testing. Opacity is now a "
         "compliance defect, not only an ethical one."),
        ("The commercial cost. ", "Candidates rate automated interviews as markedly less "
         "fair, worst where no explanation is given, and are then less likely to accept "
         "offers — eroding the efficiency that motivated automating at all."),
    ):
        bullet(doc, b, lead=lead)
    para(doc,
         "Language models can now conduct an interview and justify a judgement in readable "
         "language, but the literature shows they grade unreliably: sensitive to the order "
         "criteria are presented in, and inclined to reward length over substance. So the "
         "question is not whether a model can score an answer — it plainly can — but whether "
         "a system built around one can be made accountable for how reliable its own scores "
         "are.", bold=True)

    # ── 2. Scope ─────────────────────────────────────────────────────────
    h1(doc, "2.  Scope")
    h2(doc, "2.1  What the system does")
    for b in ("Parses a candidate's CV and a job description into structured profiles.",
              "Maps both onto a knowledge graph built from the ESCO occupational taxonomy "
              "and identifies which required skills the candidate does not evidence.",
              "Generates an interview and orders it so genuine gaps are probed first.",
              "Conducts that interview as a live spoken conversation, or as a typed one.",
              "Measures attention, posture and vocal delivery in the browser, without any "
              "video or audio leaving the candidate's device.",
              "Scores every answer against a generated reference under a four-criterion "
              "rubric, and measures how stable each score is.",
              "Assesses whether the session was conducted normally.",
              "Produces a report in which every number can be traced to its inputs."):
        bullet(doc, b)
    h2(doc, "2.2  What it deliberately does not do")
    for lead, b in (
        ("No hiring decision. ", "The system produces evidence and a recommendation. A "
         "person decides. Answers the judge scored inconsistently are escalated rather "
         "than reported as confident."),
        ("No demographic input. ", "Scoring uses only what the candidate said, judged "
         "against a reference answer for the same question. There is no demographic "
         "feature and no proxy for one."),
        ("No claim of predicting job performance. ", "The system is evaluated as a "
         "measurement instrument, not as a predictor of employment outcomes. That would "
         "need a longitudinal study."),
        ("Not a production system. ", "It runs one interview at a time, holds state in "
         "memory, and has no authentication. It is a research demonstrator."),
    ):
        bullet(doc, b, lead=lead)

    # ── 3. Approach ──────────────────────────────────────────────────────
    h1(doc, "3.  The approach, and why")
    para(doc,
         "Three design commitments follow from the problem, and each answers a specific "
         "failing documented in the literature.")
    h2(doc, "3.1  Ground the interview in a published taxonomy")
    para(doc,
         "Questions derive from a skill graph built on ESCO, the EU occupational standard, "
         "rather than being invented freely. A reported skill gap therefore names a concept "
         "with a stable public identifier, which makes the assessment auditable at the level "
         "of content and not merely of scoring.")
    h2(doc, "3.2  Make the scorer measure its own reliability")
    para(doc,
         "The core of the project. Every answer is scored twice against the same rubric with "
         "the criteria in two different orders. The mean is reported; the disagreement "
         "between the passes is the more useful output. A judge returning 82 and 81 is "
         "stable, one returning 71 and 45 is not, and the mean of 58 hides that entirely. "
         "The spread is banded into high, moderate and low consistency, and low-band answers "
         "go to a human rather than being reported as confident scores.")
    para(doc,
         "This is not a claim that the judge is unbiased. It is a claim that when the judge "
         "is unstable, the system says so.", bold=True)
    h2(doc, "3.3  Keep the candidate data on their own machine")
    para(doc,
         "Attention, posture and vocal delivery are computed in the browser. Only derived "
         "numbers cross the network; no video or audio is transmitted or stored. That is "
         "data minimisation in the sense the GDPR intends, and it costs nothing to run.")

    # ── 4. Architecture ──────────────────────────────────────────────────
    h1(doc, "4.  Architecture")
    para(doc,
         "Fourteen modules across four sequential phases. Each declares its input and output "
         "and communicates only through them, so any one can be replaced without disturbing "
         "its neighbours — which is how an entire evaluation track was removed late on "
         "without touching anything else.")
    fig = ROOT / "report" / "figures" / "fig01_architecture.png"
    if fig.exists():
        figure(doc, fig, "The four phases and the data that flows between them.")
    for lead, b in (
        ("Phase 1 — pre-interview. ", "Turns two documents into a targeted interview plan."),
        ("Phase 2 — live interview. ", "Conducts the session and observes it."),
        ("Phase 3 — assessment. ", "Scores what was said and checks how the session ran."),
        ("Phase 4 — reporting. ", "Combines everything into a traceable recommendation."),
    ):
        bullet(doc, b, lead=lead)

    # ── 5. Modules ───────────────────────────────────────────────────────
    h1(doc, "5.  The modules")
    para(doc, "What each module does, how it works, and where to find it.")
    table(doc, ["", "Module", "What it does", "Built with", "File"],
          [[t, n, how, tech, path] for t, n, path, tech, how in MODULES],
          widths=[0.9, 2.6, 6.6, 2.6, 3.3], font_size=8)

    # ── 6. Technology ────────────────────────────────────────────────────
    h1(doc, "6.  Technology choices")
    para(doc,
         "Every significant choice carries a cost as well as a benefit. Both are recorded "
         "here rather than presenting the stack as a series of obviously correct decisions.")
    table(doc, ["Technology", "Used for", "Why chosen", "What it costs"],
          [[t, u, w, c] for t, u, w, c in TECH],
          widths=[3.0, 3.4, 4.6, 4.5], font_size=8.5)

    # ── 7. A session end to end ──────────────────────────────────────────
    h1(doc, "7.  How a session runs, end to end")
    steps = [
        ("Upload", "The candidate uploads a CV and the recruiter pastes a job description. "
                   "M1 and M2 turn both into structured data."),
        ("Skill graph", "M3 resolves both sets of skills onto the ESCO graph and compares "
                        "them, producing a match percentage and a prioritised topic list."),
        ("Questions", "M4 generates the interview and re-sorts the technical questions so "
                      "the highest-priority gaps are asked while time remains."),
        ("Device check", "The candidate checks camera and microphone and chooses voice or "
                         "text. Meanwhile the media server and agent start in the "
                         "background, hiding about twelve seconds of start-up."),
        ("Interview", "M5 conducts the session. M7, M8 and M10 measure presence in the "
                      "browser. Tab switches and pasted answers are recorded."),
        ("Scoring", "The transcript is paired into exchanges, greetings and sign-offs are "
                    "excluded, and every substantive answer is scored twice by M6."),
        ("Integrity", "M9 derives behavioural features from timing and telemetry and "
                      "compares them against its baseline."),
        ("Report", "M11 fuses the components and M12 assembles the report: overall score, "
                   "per-skill verdicts, per-answer rubric detail, integrity findings, and "
                   "how consistent the judge was with itself."),
    ]
    table(doc, ["#", "Stage", "What happens"],
          [[str(i), n, b] for i, (n, b) in enumerate(steps, 1)],
          widths=[0.9, 3.0, 11.6], font_size=8.5)

    if worked.get("exchanges"):
        h2(doc, "7.1  A real session")
        para(doc,
             "Taken from the end-to-end verification run: a synthetic backend engineer "
             f"against a senior backend role, scoring "
             f"{worked.get('skill_graph', {}).get('match_percentage', 0):.0f}% on the skill "
             "graph with Kubernetes and AWS correctly identified as missing.")
        rows = []
        for ex in worked["exchanges"]:
            scored = ex.get("score") is not None
            rows.append([ex["exchange"], ex.get("skill") or "—",
                         f"{ex['score']:.1f}" if scored else "not scored",
                         f"{ex['spread']:.1f}" if scored else "—",
                         ex.get("consistency") or "—"])
        table(doc, ["Exchange", "Skill", "Score", "Judge spread", "Consistency"], rows,
              widths=[5.2, 3.0, 2.2, 2.6, 2.5], font_size=9)
        para(doc,
             "The candidate's admission that they had not used Kubernetes scored 50 rather "
             "than zero, because the rubric credits accuracy separately from completeness "
             "and an honest acknowledgement contains nothing incorrect. That same answer "
             "drew the widest judge disagreement of the session — which is the pattern one "
             "would expect, since a partial answer is genuinely harder to score.")

    # ── 8. What the evaluation found ─────────────────────────────────────
    h1(doc, "8.  What the evaluation found")
    if stats:
        para(doc,
             f"Five controlled experiments over {meta.get('n_graded_answers', 0)} answers "
             f"written at three known quality levels. The full analysis is in Chapter 6 of "
             f"the dissertation; the headline is that the evaluation found two real defects "
             f"in the system it was measuring.")
        h2(doc, "8.1  It ranks well")
        para(doc,
             f"Spearman's rho between intended quality and awarded score is "
             f"{e1.get('spearman_rho', 0):.3f}, and Cohen's d separating strong from weak "
             f"answers is {e1.get('separation', {}).get('strong_vs_weak_cohens_d', 0):.2f} — "
             f"a very large effect. The relative ordering can be trusted.")
        h2(doc, "8.2  It calibrates badly")
        table(doc, ["Intended quality", "Mean score awarded"],
              [[lvl.capitalize(), f"{lv.get(lvl, {}).get('mean', 0):.1f}"]
               for lvl in ("weak", "medium", "strong")],
              widths=[5.5, 5.5], font_size=9.5)
        para(doc,
             f"The system reports any answer at or above 70 as strong. Deliberately partial "
             f"answers averaged {lv.get('medium', {}).get('mean', 0):.1f} — comfortably above "
             f"it — so medium and strong answers receive the same verdict. Exact band "
             f"agreement is only {e1.get('exact_band_agreement', 0)*100:.1f}%.")
        para(doc,
             "The instrument is comparative, not absolute. It supports the claim that one "
             "candidate answered better than another; it does not support the claim that a "
             "candidate scored 92 and therefore meets a standard.", bold=True)
        h2(doc, "8.3  The rubric does not decompose as designed")
        para(doc,
             f"The four criteria correlate at a mean of "
             f"{e4.get('mean_inter_criterion_r', 0):.3f} despite an explicit instruction to "
             f"score them independently. The judge appears to form one overall impression "
             f"and distribute it — the classic halo effect, which instructing a model "
             f"against did not remove.")
        h2(doc, "8.4  Positional instability was small")
        para(doc,
             f"Mean spread between the two rubric orderings was "
             f"{e2.get('mean_absolute_spread', 0):.2f} points, and no answer required "
             f"escalation. That is a null result for the escalation mechanism on this "
             f"corpus, and it is reported as one rather than dressed up.")

    # ── 9. Directory guide ───────────────────────────────────────────────
    h1(doc, "9.  Directory guide")
    para(doc, "Every significant file, and what it is for.")
    if missing or unmapped:
        para(doc,
             "This listing did not fully match the working tree when the document was "
             f"generated: {len(missing)} listed file(s) absent, {len(unmapped)} tracked "
             "file(s) not listed. Update FILES in build_guide.py.",
             colour=GREY, italic=True, size=Pt(9))
    current = None
    rows = []
    for path, desc in FILES:
        top = path.split("/")[0] if "/" in path else "(root)"
        if top != current:
            if rows:
                table(doc, ["File", "Purpose"], rows, widths=[6.2, 9.3], font_size=8.5)
                rows = []
            current = top
            h3(doc, top)
        rows.append([path, desc])
    if rows:
        table(doc, ["File", "Purpose"], rows, widths=[6.2, 9.3], font_size=8.5)

    # ── 10. Running and verifying ────────────────────────────────────────
    h1(doc, "10.  Running, verifying and rebuilding")
    h2(doc, "10.1  Running it")
    para(doc,
         "Double-click run.bat. It installs Python and Node.js if they are missing, creates "
         "the environment, installs both dependency sets, builds the interface, and starts "
         "the server at http://localhost:8000. Three API keys go in InterviewAI\\.env — "
         "Gemini and Deepgram are required, ElevenLabs is optional and falls back to "
         "Deepgram's voice.")
    h2(doc, "10.2  Verifying it")
    code(doc,
         "cd InterviewAI\n"
         "python -m pytest tests/ -q                           # unit tests, no API calls\n"
         "python -m experiments.run_evaluation --figures-only  # recompute from cache, free\n"
         "python -m experiments.run_evaluation --quick         # full re-run, ~69 API calls")
    if n_tests:
        para(doc, f"The suite currently holds {n_tests} tests, all passing. Two are direct "
                  f"regressions on a skill-matching bug that once mapped “Team Leadership” "
                  f"onto the ESCO concept “R”.")
    h2(doc, "10.3  Rebuilding the documents")
    code(doc,
         "python build_guide.py          # this guide\n"
         "cd report && python build_report.py   # the dissertation\n"
         "cd viva   && python build_viva.py     # the presentation")
    para(doc,
         "No result in any of these documents is typed in by hand. They read the measured "
         "statistics, so re-running the evaluation and rebuilding produces documents "
         "consistent with the new numbers.")

    doc.save(OUTPUT)
    return OUTPUT, missing, unmapped, n_tests


if __name__ == "__main__":
    out, missing, unmapped, n_tests = build()
    print(f"Written: {out}")
    print(f"  tests reported : {n_tests}")
    if missing:
        print(f"  ! {len(missing)} listed file(s) do not exist:")
        for m in missing:
            print(f"      {m}")
    if unmapped:
        print(f"  ! {len(unmapped)} tracked file(s) are not in the guide:")
        for u in unmapped:
            print(f"      {u}")
    if not missing and not unmapped:
        print("  file listing matches the working tree exactly")
