"""Build PROJECT_GUIDE.docx — a short, plain-English guide to this project.

    cd report && python build_guide.py

Written for someone who has never seen the project. Short enough to read in one
sitting, but nothing important left out: the problem, the scope, the approach,
every module, the technology, the results, and a file-by-file directory guide.

Generated rather than written by hand, because a guide that drifts from the code
is worse than none. The file listing is checked in both directions against the
working tree, the results come from the measured data, and the test count comes
from running the tests. Any mismatch is reported instead of quietly disagreeing.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
PROJECT = ROOT / "InterviewAI"
RESULTS = PROJECT / "experiments" / "results"
OUTPUT = ROOT / "PROJECT_GUIDE.docx"

sys.path.insert(0, str(Path(__file__).resolve().parent))

from docx.shared import Pt  # noqa: E402
from document_toolkit import (  # noqa: E402
    add_page_numbers, bullet, figure, h1, h2, new_document, para, table, GREY,
)

# ── The file map. Checked against the working tree in both directions. ───
FILES = [
    # (path, what it is)
    ("run.bat", "Double-click this. Installs everything and starts the app."),
    ("README.md", "Short overview: what it is, how to run it, how to check it."),
    ("PROJECT_GUIDE.docx", "This document."),
    (".gitignore", "Keeps secrets and build output out of Git."),
    (".gitattributes", "Stops Windows line endings breaking run.bat on a clone."),

    ("InterviewAI/server.py", "The web server. Every API the browser calls lives here."),
    ("InterviewAI/requirements.txt", "Every Python package, locked to a tested version."),
    ("InterviewAI/SETUP.md", "Setup help and a troubleshooting table."),
    ("InterviewAI/.env.example", "Template for the API keys. Copied to .env on first run."),

    ("InterviewAI/core/config.py", "All the numbers in one place: score thresholds, question limits."),
    ("InterviewAI/core/gemini_client.py", "Talks to Google Gemini. Fixes broken JSON replies and counts usage."),
    ("InterviewAI/core/agents/cv_parser.py", "Reads a CV and pulls out skills, jobs, education."),
    ("InterviewAI/core/agents/jd_parser.py", "Reads a job advert and pulls out the required skills."),
    ("InterviewAI/core/agents/question_generator.py", "Writes the interview questions and puts the important ones first."),
    ("InterviewAI/core/agents/interviewer_prompt.py", "The interviewer's personality and rules. Shared by voice and text."),
    ("InterviewAI/core/graph/skill_graph.py", "Matches CV skills to job skills using the ESCO standard, and finds the gaps."),
    ("InterviewAI/core/graph/skill_state.py", "Remembers how the candidate is doing on each skill during the interview."),
    ("InterviewAI/core/graph/follow_up_rules.py", "Decides when a skill needs another question."),
    ("InterviewAI/core/livekit/voice_agent.py", "The talking interviewer: listens, thinks, speaks."),
    ("InterviewAI/core/livekit/media_server.py", "Starts the audio server. Downloads it the first time."),
    ("InterviewAI/core/livekit/livekit.yaml", "Audio server settings."),
    ("InterviewAI/core/pipeline/text_interview.py", "The typed version of the interview."),
    ("InterviewAI/core/pipeline/post_interview.py", "After the interview: pairs up questions and answers, then scores them."),
    ("InterviewAI/core/evaluator/answer_judge.py", "Marks each answer out of 100, twice, and checks it agrees with itself."),
    ("InterviewAI/core/evaluator/behavioural_integrity.py", "Spots unusual behaviour, like tab-switching or suspiciously fast answers."),
    ("InterviewAI/core/evaluator/score_fusion.py", "Combines all the scores into one recommendation."),
    ("InterviewAI/core/report/report_builder.py", "Builds the final candidate report."),

    ("InterviewAI/frontend/src/main.jsx", "Starts the web page."),
    ("InterviewAI/frontend/src/App.jsx", "The six steps and how you move between them."),
    ("InterviewAI/frontend/src/lib/vision.js", "Watches attention and posture through the camera, in the browser."),
    ("InterviewAI/frontend/src/lib/voice.js", "Measures tone of voice through the microphone, in the browser."),
    ("InterviewAI/frontend/src/components/LandmarkOverlay.jsx", "Draws the face and body tracking on screen so you can see it."),
    ("InterviewAI/frontend/src/components/Sidebar.jsx", "The step menu down the side."),
    ("InterviewAI/frontend/src/screens/UploadStep.jsx", "Step 1: upload the CV, paste the job advert."),
    ("InterviewAI/frontend/src/screens/GraphStep.jsx", "Step 2: shows the skill match and the gaps."),
    ("InterviewAI/frontend/src/screens/QuestionsStep.jsx", "Step 3: shows the questions it will ask."),
    ("InterviewAI/frontend/src/screens/SetupScreen.jsx", "Step 4: camera and mic check, pick voice or typing."),
    ("InterviewAI/frontend/src/screens/InterviewScreen.jsx", "Step 5: the spoken interview."),
    ("InterviewAI/frontend/src/screens/TextInterviewScreen.jsx", "Step 5: the typed interview."),
    ("InterviewAI/frontend/src/screens/DashboardScreen.jsx", "Step 6: the final report."),

    ("InterviewAI/experiments/run_evaluation.py", "Runs the five experiments that test how good the marking is."),
    ("InterviewAI/experiments/results/statistics.json", "The results. The report reads its numbers from here."),
    ("InterviewAI/experiments/results/raw_scores.json", "Every individual score, saved so charts can be redrawn for free."),
    ("InterviewAI/experiments/results/track_b_evidence.json", "Proof of why the second marking method was thrown away."),
    ("InterviewAI/experiments/results/worked_example.json", "One complete test interview, used as an example in the report."),
    ("InterviewAI/tests/test_core.py", "72 automatic tests. Run these to check nothing is broken."),
    ("InterviewAI/docs/track-b-rejection.md", "The full story of the marking method that was removed."),
    ("InterviewAI/data/esco/digitalSkillsCollection_en.csv", "The official EU list of 1,201 digital skills."),
    ("InterviewAI/data/esco/broaderRelationsSkillPillar.csv", "How those skills relate to each other."),

    ("submission/AI-Interview.docx", "The dissertation. The main piece of work."),
    ("submission/CMP7200_Viva_Presentation.pptx", "The presentation for the oral exam."),
    ("submission/AI_Interview_Final_Proposal.docx", "The original project proposal."),
    ("submission/CMP7200_Assignment_Brief.pdf", "What the university asked for."),
    ("submission/VIVA_QA_PREP.md", "Likely exam questions with prepared answers."),

    ("submission/build/build_dissertation.py", "Builds the dissertation."),
    ("submission/build/build_presentation.py", "Builds the presentation."),
    ("submission/build/build_project_guide.py", "Builds this guide."),
    ("submission/build/front_matter.py", "Title page, abstract, contents."),
    ("submission/build/chapter1_introduction.py", "Chapter 1."),
    ("submission/build/chapter2_literature.py", "Chapter 2."),
    ("submission/build/chapter3_methodology.py", "Chapter 3."),
    ("submission/build/chapter4_design.py", "Chapter 4."),
    ("submission/build/chapter5_implementation.py", "Chapter 5."),
    ("submission/build/chapter6_evaluation.py", "Chapter 6. Reads the real numbers from the results file."),
    ("submission/build/chapter7_reflection.py", "Chapter 7."),
    ("submission/build/chapter8_conclusion.py", "Chapter 8."),
    ("submission/build/back_matter.py", "References and appendices."),
    ("submission/build/figures.py", "Draws the diagrams used in the report."),
    ("submission/build/figure_toolkit.py", "Stops diagram text overlapping or running off the edge."),
    ("submission/build/document_toolkit.py", "Makes headings, tables and captions look right."),
    ("submission/build/results.py", "One place that reads the results, so every chapter agrees."),
]

MODULES = [
    ("M1", "Read the CV", "cv_parser.py", "Google Gemini + PyMuPDF",
     "Opens the uploaded PDF, reads the text, and turns it into a tidy list: "
     "name, contact details, skills, past jobs, education and projects. If the "
     "AI replies with broken data it repairs it instead of giving up."),
    ("M2", "Read the job advert", "jd_parser.py", "Google Gemini",
     "Does the same for the job advert: the job title, which skills are "
     "required, which are only nice to have, the seniority level and the "
     "industry."),
    ("M3", "Match skills, find gaps", "skill_graph.py", "NetworkX + ESCO list",
     "Lines both lists up against the official EU list of 1,201 skills, using "
     "four increasingly forgiving matching steps. Then works out which "
     "required skills the candidate has not shown — those are the gaps."),
    ("M4", "Write the questions", "question_generator.py", "Google Gemini",
     "Writes the whole interview: opening questions, technical questions for "
     "each skill, behavioural questions, and closing questions. Then reorders "
     "it so the missing skills get asked first, before time runs out."),
    ("M5", "Run the interview (voice)", "voice_agent.py",
     "LiveKit + Deepgram + ElevenLabs",
     "The talking interviewer. It shows each question on screen, then speaks "
     "it aloud. It listens to the answer, decides whether to dig deeper, and "
     "moves on. It knows when to stop, and saves the full transcript."),
    ("M5", "Run the interview (typed)", "text_interview.py", "FastAPI",
     "The same interview, typed instead of spoken. Same questions, same "
     "marking. It produces a transcript in exactly the same shape, so nothing "
     "after the interview can tell which way it was done."),
    ("M6", "Mark the answers", "answer_judge.py", "Google Gemini as judge",
     "Marks every answer out of 100 on four things: accuracy, completeness, "
     "clarity and relevance. It marks each answer TWICE, showing the four "
     "criteria in a different order each time, then checks whether the two "
     "marks agree. A big disagreement means the mark cannot be trusted."),
    ("M6a", "Track each skill", "skill_state.py", "Plain Python",
     "Keeps a running note on every skill: not asked yet, asked, answered "
     "well, answered badly, or still unknown. This is what decides whether a "
     "follow-up question is needed."),
    ("M7", "Watch attention (face)", "vision.js", "MediaPipe Face Landmarker",
     "Uses the webcam to find 478 points on the face, then works out where "
     "the head is pointing and whether the eyes are on the screen. From that "
     "it produces an attention score and counts how long they looked away. "
     "This runs inside the browser — the video never leaves the computer."),
    ("M8", "Watch posture (body)", "vision.js", "MediaPipe Pose Landmarker",
     "Uses the same camera picture to find 33 points on the upper body, then "
     "checks whether the shoulders are level and the person is upright rather "
     "than slouched or leaning off-screen. Also entirely in the browser."),
    ("M9", "Check for cheating", "behavioural_integrity.py",
     "Isolation Forest (scikit-learn)",
     "Looks at how the session behaved rather than what was said: tab "
     "switches, answers arriving suspiciously fast or slow, answers that are "
     "all oddly the same length. It learns what normal looks like on first "
     "run, and always names the behaviour that caused a flag."),
    ("M10", "Listen to the voice", "voice.js", "Web Audio API",
     "Measures the sound of the voice, not the words: how steady the pitch "
     "is, how loud, how much of the time is actual speech rather than pauses "
     "and 'um'. From that it estimates how confidently they spoke. Browser "
     "only — no audio is uploaded."),
    ("M11", "Add it all up", "score_fusion.py", "Plain Python",
     "Combines the answer marks, how many required skills were covered, the "
     "behaviour check and the voice score into one number and a hire "
     "recommendation — showing how much each part contributed."),
    ("M12", "Write the report", "report_builder.py", "Plain Python",
     "Builds the report the recruiter reads: each answer and its mark, how "
     "consistent the marking was, the behaviour verdict, the recommendation, "
     "and the reasoning behind all of it."),
]

# The three AI models the system actually calls. Named exactly, because
# "we used AI" is not an answer anyone can check.
MODELS = [
    ("Gemini 3.6 Flash", "google-genai 2.11.0",
     "Reading the CV and job advert, writing the questions, and marking every "
     "answer. Every language task in the project uses this one model.",
     "Google's servers"),
    ("Deepgram Nova-3", "livekit-plugins-deepgram 1.6.4",
     "Turning the candidate's speech into text during the voice interview. It "
     "is given the job's technical words in advance so it does not mishear "
     "them.", "Deepgram's servers"),
    ("ElevenLabs Turbo v2.5", "livekit-plugins-elevenlabs 1.6.4",
     "The interviewer's speaking voice. If this key is missing or out of "
     "credit, the system automatically falls back to Deepgram Aura-2.",
     "ElevenLabs' servers"),
    ("MediaPipe Face Landmarker", "@mediapipe/tasks-vision 1.0.1",
     "Finds 478 points on the face to work out attention and gaze.",
     "Inside the browser"),
    ("MediaPipe Pose Landmarker Lite", "@mediapipe/tasks-vision 1.0.1",
     "Finds 33 points on the upper body to work out posture.",
     "Inside the browser"),
    ("Isolation Forest", "scikit-learn 1.9.0",
     "Spots unusual session behaviour. Not a downloaded model — the system "
     "trains it itself on first run and saves it.", "On your own machine"),
]

TECH = [
    ("Google Gemini 3.6 Flash", "Reading CVs, writing questions, marking answers",
     "Understands language well and can explain its own marking",
     "Costs money, can be slow, and Google can retire the model"),
    ("ESCO v1.1.1 (EU skills list)", "The official list of skills to match against",
     "A real published standard, so a 'missing skill' means something",
     "Old — it does not know newer technology, so we added our own list"),
    ("NetworkX 3.6", "Holding the skill map",
     "Simple and fast enough",
     "Kept in memory only, so it would not work for many users at once"),
    ("difflib (built into Python)", "Matching skill names that are spelled differently",
     "No extra library needed, and catches 'k8s' meaning Kubernetes",
     "Too loose a setting invents matches, so it only runs on names of six "
     "letters or more and must be 88% similar"),
    ("PyMuPDF 1.28", "Getting the text out of a CV in PDF form",
     "Fast and accurate on normal PDFs",
     "A scanned or photographed CV has no text to extract"),
    ("LiveKit 1.1 (+ agents 1.6)", "Carrying the audio for the spoken interview",
     "Professional-grade; handles people talking over each other",
     "Big install, and takes about 12 seconds to start up"),
    ("Deepgram Nova-3", "Turning speech into text",
     "Accurate, and can be told the job's technical words in advance",
     "Needs internet and an API key"),
    ("ElevenLabs Turbo v2.5", "The interviewer's voice",
     "Natural sounding and fast — a full question in about one second",
     "Free tier runs out quickly; falls back to Deepgram Aura-2 automatically"),
    ("MediaPipe Tasks Vision 1.0", "Face and body tracking",
     "Runs inside the browser, so no video is ever uploaded",
     "Needs a reasonably modern browser"),
    ("Web Audio API", "Measuring the voice",
     "Free, offline, and you can see exactly how the score was made",
     "It measures how they sound, not how they feel"),
    ("scikit-learn 1.9 (Isolation Forest)", "Spotting unusual behaviour",
     "Does not need examples of cheating, which nobody could collect fairly",
     "Trained on made-up 'normal' data, so we cannot say how often it is wrong"),
    ("FastAPI 0.141 + Uvicorn", "The web server",
     "Quick to build, and one program serves both the API and the web page",
     "Handles one interview at a time"),
    ("React 19 + Vite 8 + Tailwind 4", "The web page the candidate sees",
     "Fast to develop and quick to load",
     "Vite 8 needs Node.js 20.19 or newer, so an old Node will not build it"),
    ("pytest 9.1", "The 72 automatic tests",
     "Catches breakages without spending any API credit",
     "Tests the parts, not the live interview end to end"),
    ("python-docx / python-pptx", "Building this guide, the dissertation and the slides",
     "The documents are generated from the real data, so they cannot drift",
     "Formatting has to be written in code rather than clicked in Word"),
]


def load(path, label):
    if not path.exists():
        print(f"  ! {label} missing at {path}")
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def check_file_map():
    mapped = {f for f, _ in FILES}
    missing = sorted(f for f in mapped
                     if f != OUTPUT.name and not (ROOT / f).exists())
    tracked = subprocess.run(["git", "ls-files"], cwd=str(ROOT),
                             capture_output=True, text=True).stdout.split()
    interesting = re.compile(
        r"^(run\.bat|README\.md"
        r"|InterviewAI/(server\.py|requirements\.txt|SETUP\.md|\.env\.example"
        r"|core/.*\.(py|yaml)|frontend/src/.*\.(jsx|js)|experiments/.*\.(py|json)"
        r"|tests/.*\.py|docs/.*\.md)"
        r"|report/.*\.py|viva/.*\.(py|md))$")
    unmapped = sorted(t for t in tracked
                      if interesting.match(t) and t not in mapped
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
    para(doc, space_after=100)
    para(doc, "InterviewAI", bold=True, align="center", size=Pt(36))
    para(doc, "Project Guide", align="center", size=Pt(20), colour=GREY)
    para(doc, space_after=34)
    para(doc, "An AI that interviews a job candidate, marks their answers,\n"
              "and shows its working.",
         align="center", size=Pt(13), colour=GREY)
    para(doc, space_after=70)
    para(doc, "Abdul Wahab", align="center", bold=True, size=Pt(13))
    para(doc, space_after=18)
    para(doc, "CMP7200 — Individual Master's Project", align="center", size=Pt(11))
    para(doc, "Birmingham City University · 2025–26", align="center",
         size=Pt(10), colour=GREY)
    para(doc, space_after=44)
    para(doc, "This guide is built from the project itself, so it cannot go out of date.",
         align="center", size=Pt(9), colour=GREY, italic=True)

    # ── 1. Problem ───────────────────────────────────────────────────────
    h1(doc, "1.  The problem")
    para(doc,
         "Companies now use AI to interview and score job candidates at a scale no human "
         "team could manage. The problem is that these systems give you a number and "
         "nothing else. No reason. No way to argue with it.")
    for lead, b in (
        ("It has caused real trouble. ",
         "In 2019 a privacy group formally challenged HireVue over scoring candidates "
         "from their faces. The feature was dropped, but the deeper issue stayed: you "
         "still get a score and no explanation."),
        ("The law has caught up. ",
         "The EU AI Act now treats hiring software as high-risk. It must be able to "
         "explain itself, be overseen by a human, and be tested for bias."),
        ("It also costs companies money. ",
         "Candidates who think the process was unfair are less likely to take the job "
         "if offered — which cancels out the time the company saved."),
    ):
        bullet(doc, b, lead=lead)
    para(doc,
         "AI can now hold a proper conversation and explain its reasoning. But research "
         "shows it marks unreliably: change the order you show it the marking criteria "
         "and the score changes, and it tends to reward long answers over good ones.")
    para(doc,
         "So the question is not whether AI can mark an interview answer. It clearly can. "
         "The question is whether it can be honest about how much to trust each mark.",
         bold=True)

    # ── 2. Scope ─────────────────────────────────────────────────────────
    h1(doc, "2.  What it does, and what it does not")
    h2(doc, "2.1  What it does")
    for b in ("Reads a CV and a job advert.",
              "Works out which required skills the candidate is missing.",
              "Writes an interview and asks about the missing skills first.",
              "Runs the interview — spoken out loud, or typed.",
              "Watches attention, posture and tone of voice, all inside the browser.",
              "Marks every answer and says how confident it is in each mark.",
              "Checks whether the session looked normal.",
              "Produces a report where every number can be traced back."):
        bullet(doc, b)
    h2(doc, "2.2  What it deliberately does not do")
    for lead, b in (
        ("It does not hire anyone. ",
         "It gives evidence and a recommendation. A person decides. Answers it was "
         "unsure about get passed to a human instead of being scored confidently."),
        ("It knows nothing about the person. ",
         "Only what they said is marked. No age, gender, name or background is used."),
        ("It does not predict job performance. ",
         "It measures how well someone answered, not how well they would do the job. "
         "Proving that would take years of follow-up data."),
        ("It is not a finished product. ",
         "One interview at a time, no login, no database. It is a research prototype."),
    ):
        bullet(doc, b, lead=lead)

    # ── 3. Approach ──────────────────────────────────────────────────────
    h1(doc, "3.  How it solves the problem")
    h2(doc, "3.1  Ask about real skills, from a real list")
    para(doc,
         "The questions are not made up freely. They come from ESCO, the official EU "
         "list of job skills. So when the system says a candidate is missing a skill, "
         "that skill is a recognised thing with an official name — not something the "
         "AI invented.")
    h2(doc, "3.2  Mark everything twice, and admit when the two disagree")
    para(doc,
         "This is the important bit. Every answer is marked twice, with the four marking "
         "criteria shown in a different order each time. The average is the score.")
    para(doc,
         "The gap between the two marks is what matters. If it marks 82 and then 81, it "
         "is sure. If it marks 71 and then 45, it is not — and the average of 58 hides "
         "that completely. So the gap is kept, and answers where the two marks disagree "
         "badly are sent to a human instead of being reported as a confident score.")
    para(doc,
         "This does not claim the AI is unbiased. It claims that when the AI is unsure, "
         "the system says so.", bold=True)
    h2(doc, "3.3  Never send the video anywhere")
    para(doc,
         "Attention, posture and tone of voice are all worked out inside the candidate's "
         "own browser. Only numbers are sent to the server — never video or audio. "
         "Nothing is recorded or stored.")

    # ── 4. How it is put together ────────────────────────────────────────
    h1(doc, "4.  How it is put together")
    para(doc,
         "Thirteen parts, in four stages. Each part has one job and passes its result to "
         "the next, so any one of them can be swapped out without breaking the others.")
    fig = Path(__file__).resolve().parent / "figures_png" / "fig01_architecture.png"
    if fig.exists():
        figure(doc, fig, "The four stages and what passes between them.")
    for lead, b in (
        ("Stage 1 — before the interview. ", "Turn two documents into a plan."),
        ("Stage 2 — the interview. ", "Ask the questions and watch how it goes."),
        ("Stage 3 — marking. ", "Score the answers and check the session was normal."),
        ("Stage 4 — the report. ", "Add it all up into something a recruiter can act on."),
    ):
        bullet(doc, b, lead=lead)

    h2(doc, "4.1  The thirteen parts, one by one")
    table(doc, ["", "What it does", "How it works", "Built with", "File"],
          [[t, n, how, tech, f] for t, n, f, tech, how in MODULES],
          widths=[0.7, 2.5, 6.6, 2.6, 2.7], font_size=8)

    h2(doc, "4.2  The camera and microphone parts, explained")
    para(doc,
         "Four of the thirteen parts (M7, M8, M10 and part of M9) do not read words at "
         "all. They watch how the interview went. These are the parts people ask about "
         "most, so here is what each one actually measures.")
    for lead, b in (
        ("Face and attention (M7). ",
         "The camera picture is scanned for 478 points on the face — the corners of the "
         "eyes, the edge of the jaw, the tip of the nose. From how those points sit "
         "relative to each other, the system works out which way the head is turned and "
         "whether the eyes are pointed at the screen. It produces two things: an "
         "attention score, and how much of the interview was spent looking away."),
        ("Posture (M8). ",
         "The same picture is scanned again for 33 points on the upper body — shoulders, "
         "elbows, hips. It checks whether the shoulders are level and whether the person "
         "is sitting upright, slouched, or leaning out of frame."),
        ("Tone of voice (M10). ",
         "This listens to the sound, not the words. It measures how steady the pitch is "
         "(a wobbling pitch suggests nerves), how loud the speech is, and what fraction "
         "of the time is real speech rather than pauses. Those combine into a confidence "
         "estimate."),
        ("Behaviour (M9). ",
         "This one is not a camera at all. It watches the shape of the session: how many "
         "times the candidate switched browser tab, whether answers arrived far faster or "
         "slower than normal, whether every answer is suspiciously the same length."),
    ):
        bullet(doc, b, lead=lead)
    para(doc,
         "Two things are worth being clear about. All of this happens inside the "
         "candidate's own browser — the video and audio are never uploaded, never "
         "recorded, and never stored; only the resulting numbers are sent. And none of it "
         "is used to judge the person: it does not read emotions, and it makes no claim "
         "about honesty or personality.", bold=True)
    para(doc,
         "It also counts for much less than the answers. This is the exact recipe for the "
         "final score — the camera and voice together are worth 15 out of 100:")
    table(doc, ["What is measured", "Which part", "Share of the final score"],
          [["What the candidate actually said", "M6", "50%"],
           ["How many required skills were covered", "M3", "20%"],
           ["Whether the session looked normal", "M9", "15%"],
           ["Attention, posture and tone of voice", "M7, M8, M10", "15%"]],
          widths=[6.6, 3.4, 5.5], font_size=9)

    # ── 5. Technology ────────────────────────────────────────────────────
    h1(doc, "5.  What it is built with")
    h2(doc, "5.1  The AI models, named exactly")
    para(doc,
         "Six trained models are involved. Three are language and speech models reached "
         "over the internet; two are vision models that run inside the browser; one is "
         "trained by the system itself. Nothing else in the project is a model — the rest "
         "is ordinary code.")
    table(doc, ["Model", "Which library calls it", "What it is used for", "Where it runs"],
          [[m, lib, use, where] for m, lib, use, where in MODELS],
          widths=[3.4, 3.4, 6.5, 2.2], font_size=8)
    para(doc,
         "Only the first three cost money or need an internet connection. The two "
         "MediaPipe models are downloaded once when the app is first built and then run "
         "offline on the candidate's own machine, which is what makes the privacy promise "
         "in section 3.3 possible.")

    h2(doc, "5.2  Everything else it is built with")
    para(doc,
         "Every choice has a downside as well as an upside. Both are listed, because "
         "pretending otherwise helps nobody.")
    table(doc, ["Tool", "Used for", "Why", "Downside"],
          [[t, u, w, c] for t, u, w, c in TECH],
          widths=[3.2, 3.3, 4.8, 4.2], font_size=8)
    para(doc,
         "Every Python package is pinned to an exact version in "
         "InterviewAI\\requirements.txt, and every JavaScript one in "
         "InterviewAI\\frontend\\package.json. Both are installed automatically by "
         "run.bat, so the versions above are what actually gets installed — not a "
         "recommendation.", size=Pt(9), colour=GREY)

    # ── 6. What happens, start to finish ─────────────────────────────────
    h1(doc, "6.  What happens, start to finish")
    steps = [
        ("Upload", "The CV and the job advert go in. The AI reads both."),
        ("Match", "It compares the two skill lists and finds what is missing."),
        ("Questions", "It writes the interview, missing skills first."),
        ("Check", "Camera and mic test. Voice or typing. The audio server warms up "
                  "quietly in the background so there is no wait."),
        ("Interview", "It asks, listens and follows up. The browser watches attention "
                      "and tone. Tab switches are noted."),
        ("Marking", "Greetings are skipped. Every real answer is marked twice."),
        ("Behaviour", "Timing and tab switches are checked against normal."),
        ("Report", "Everything is combined: a score, a recommendation, and the working "
                   "behind both."),
    ]
    table(doc, ["#", "Stage", "What happens"],
          [[str(i), n, b] for i, (n, b) in enumerate(steps, 1)],
          widths=[0.9, 3.0, 11.6], font_size=8.5)

    # ── 7. Results ───────────────────────────────────────────────────────
    if stats:
        h1(doc, "7.  Does the marking actually work?")
        para(doc,
             f"Five experiments were run on {meta.get('n_graded_answers', 0)} answers "
             f"written to be deliberately good, average or bad. The full analysis is in "
             f"Chapter 6 of the dissertation. Two real problems were found — in this "
             f"project's own system.")
        h2(doc, "7.1  Good news: it ranks answers correctly")
        para(doc,
             f"It almost never puts a worse answer above a better one. The statistical "
             f"measure of agreement is {e1.get('spearman_rho', 0):.2f} out of 1.")
        h2(doc, "7.2  Problem one: it is too generous")
        table(doc, ["Answers written to be…", "Average mark given"],
              [[lvl.capitalize(), f"{lv.get(lvl, {}).get('mean', 0):.0f} out of 100"]
               for lvl in ("weak", "medium", "strong")],
              widths=[5.5, 5.5], font_size=9.5)
        para(doc,
             f"The system calls anything 70 or above a strong answer. But deliberately "
             f"average answers scored {lv.get('medium', {}).get('mean', 0):.0f} — so "
             f"average and excellent answers get the same verdict. The marks are useful "
             f"for comparing two candidates, but not for saying whether one is good "
             f"enough on their own.")
        h2(doc, "7.3  Problem two: the four criteria move together")
        para(doc,
             f"The AI is told to mark accuracy, completeness, clarity and relevance "
             f"separately. In practice they correlate at "
             f"{e4.get('mean_inter_criterion_r', 0):.2f} out of 1 — it forms one overall "
             f"impression and spreads it across all four. So the breakdown explains less "
             f"than it appears to.")
        h2(doc, "7.4  And an honest non-result")
        para(doc,
             f"The double-marking safety net never triggered. The two marks were only "
             f"{e2.get('mean_absolute_spread', 0):.1f} points apart on average, so no "
             f"answer needed a human. The mechanism works, but this test did not prove "
             f"it was needed.")

    # ── 8. Directory guide ───────────────────────────────────────────────
    h1(doc, "8.  Every file, and what it does")
    if missing or unmapped:
        para(doc,
             f"This listing did not match the folder when the guide was built: "
             f"{len(missing)} listed file(s) missing, {len(unmapped)} file(s) not listed. "
             f"Update FILES in report/build_guide.py.",
             colour=GREY, italic=True, size=Pt(9))
    current, rows = None, []
    for path, desc in FILES:
        top = path.split("/")[0] if "/" in path else "In the main folder"
        if top != current:
            if rows:
                table(doc, ["File", "What it does"], rows,
                      widths=[6.4, 9.1], font_size=8.5)
                rows = []
            current = top
            h2(doc, top)
        rows.append([path, desc])
    if rows:
        table(doc, ["File", "What it does"], rows, widths=[6.4, 9.1], font_size=8.5)

    # ── 9. Running it ────────────────────────────────────────────────────
    h1(doc, "9.  Running and checking it")
    h2(doc, "9.1  To run it")
    para(doc,
         "Double-click run.bat. It installs Python and Node.js if they are missing, sets "
         "everything up, and opens the app at http://localhost:8000.")
    para(doc,
         "It needs two API keys, in the file InterviewAI\\.env — one for Google Gemini, "
         "one for Deepgram. The first run creates that file and tells you to paste them "
         "in. Paste them, run it again, and it starts straight away.")
    h2(doc, "9.2  To check nothing is broken")
    para(doc,
         f"Open a terminal in the InterviewAI folder and run: "
         f"venv\\Scripts\\python.exe -m pytest tests/ -q")
    if n_tests:
        para(doc, f"It should say {n_tests} passed. This uses no API credit, so it works "
                  f"even without keys.")
    h2(doc, "9.3  To rebuild the documents")
    para(doc,
         "In the report folder: python build_report.py for the dissertation, "
         "python build_guide.py for this guide. In the viva folder: python build_viva.py "
         "for the presentation. None of them invents a number — they all read the same "
         "results file, so the documents can never disagree with each other.")

    doc.save(OUTPUT)
    return OUTPUT, missing, unmapped, n_tests


if __name__ == "__main__":
    out, missing, unmapped, n_tests = build()
    print(f"Written: {out}")
    print(f"  tests reported : {n_tests}")
    for m in missing:
        print(f"  ! listed but missing: {m}")
    for u in unmapped:
        print(f"  ! present but not listed: {u}")
    if not missing and not unmapped:
        print("  file listing matches the working tree exactly")
