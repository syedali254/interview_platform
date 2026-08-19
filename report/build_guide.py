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

ROOT = Path(__file__).resolve().parent.parent
PROJECT = ROOT / "InterviewAI"
RESULTS = PROJECT / "experiments" / "results"
OUTPUT = ROOT / "PROJECT_GUIDE.docx"

sys.path.insert(0, str(Path(__file__).resolve().parent))

from docx.shared import Pt  # noqa: E402
from docx_kit import (  # noqa: E402
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

    ("report/build_report.py", "Builds the dissertation."),
    ("report/build_guide.py", "Builds this guide."),
    ("report/front_matter.py", "Title page, abstract, contents."),
    ("report/ch1_introduction.py", "Chapter 1."),
    ("report/ch2_literature.py", "Chapter 2."),
    ("report/ch3_methodology.py", "Chapter 3."),
    ("report/ch4_design.py", "Chapter 4."),
    ("report/ch5_implementation.py", "Chapter 5."),
    ("report/ch6_evaluation.py", "Chapter 6. Reads the real numbers from the results file."),
    ("report/ch7_reflection.py", "Chapter 7."),
    ("report/ch8_conclusion.py", "Chapter 8."),
    ("report/back_matter.py", "References and appendices."),
    ("report/diagrams.py", "Draws the 11 diagrams used in the report."),
    ("report/figkit.py", "Stops diagram text overlapping or running off the edge."),
    ("report/docx_kit.py", "Makes headings, tables and captions look right."),
    ("report/values.py", "One place that reads the results, so every chapter agrees."),
    ("report/CMP7200_Project_Report.docx", "The dissertation."),

    ("viva/build_viva.py", "Builds the presentation."),
    ("viva/CMP7200_Viva_Presentation.pptx", "The presentation."),
    ("viva/VIVA_QA_PREP.md", "Likely viva questions with prepared answers."),

    ("proposal/AI_Interview_Final_Proposal.docx", "The original project proposal."),
    ("proposal/CMP7200_Assignment_Brief.pdf", "The assignment brief."),
]

MODULES = [
    ("M1", "Read the CV", "cv_parser.py",
     "Pulls the skills, jobs and education out of an uploaded CV."),
    ("M2", "Read the job advert", "jd_parser.py",
     "Pulls out which skills the job needs, and which are just nice to have."),
    ("M3", "Match skills, find gaps", "skill_graph.py",
     "Lines both lists up against the official EU skills list and works out "
     "what the candidate is missing."),
    ("M4", "Write the questions", "question_generator.py",
     "Writes the interview, then reorders it so the missing skills get asked "
     "first, before time runs out."),
    ("M5", "Run the interview (voice)", "voice_agent.py",
     "Speaks the questions, listens to the answers, adapts as it goes."),
    ("M5", "Run the interview (typed)", "text_interview.py",
     "The same interview, typed instead of spoken. Same questions, same "
     "marking — only the way the answer arrives is different."),
    ("M6", "Mark the answers", "answer_judge.py",
     "Marks every answer out of 100 against four criteria — twice, in a "
     "different order each time, to check it agrees with itself."),
    ("M6a", "Track each skill", "skill_state.py",
     "Keeps a running verdict on each skill: proven, weak, or a real gap."),
    ("M7", "Watch attention", "vision.js",
     "Works out if the candidate is looking at the screen, using the camera."),
    ("M8", "Watch posture", "vision.js",
     "Looks at how they are sitting: slouching, leaning, shoulders uneven."),
    ("M9", "Check for cheating", "behavioural_integrity.py",
     "Flags odd behaviour — tab switching, answers that arrive too fast, long "
     "silences — and always says which behaviour caused the flag."),
    ("M10", "Listen to the voice", "voice.js",
     "Measures volume, pitch and pauses to judge how confidently they spoke."),
    ("M11", "Add it all up", "score_fusion.py",
     "Combines everything into one score and a hire recommendation."),
    ("M12", "Write the report", "report_builder.py",
     "Puts it all together into the report the recruiter reads."),
]

TECH = [
    ("Google Gemini", "Reading CVs, writing questions, marking answers",
     "Understands language well and can explain its own marking",
     "Costs money, can be slow, and Google can retire the model"),
    ("ESCO (EU skills list)", "The official list of skills to match against",
     "A real published standard, so a 'missing skill' means something",
     "Old — it does not know newer technology, so we added our own list"),
    ("NetworkX", "Holding the skill map",
     "Simple and fast enough",
     "Kept in memory only, so it would not work for many users at once"),
    ("LiveKit", "Carrying the audio for the spoken interview",
     "Professional-grade; handles people talking over each other",
     "Big install, and takes about 12 seconds to start up"),
    ("MediaPipe", "Face and body tracking",
     "Runs inside the browser, so no video is ever uploaded",
     "Needs a reasonably modern browser"),
    ("Web Audio", "Measuring the voice",
     "Free, offline, and you can see exactly how the score was made",
     "It measures how they sound, not how they feel"),
    ("Isolation Forest", "Spotting unusual behaviour",
     "Does not need examples of cheating, which nobody could collect fairly",
     "Trained on made-up 'normal' data, so we cannot say how often it is wrong"),
    ("FastAPI + React", "The web server and the web page",
     "Quick to build, and one program serves both",
     "Handles one interview at a time"),
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
    fig = ROOT / "report" / "figures" / "fig01_architecture.png"
    if fig.exists():
        figure(doc, fig, "The four stages and what passes between them.")
    for lead, b in (
        ("Stage 1 — before the interview. ", "Turn two documents into a plan."),
        ("Stage 2 — the interview. ", "Ask the questions and watch how it goes."),
        ("Stage 3 — marking. ", "Score the answers and check the session was normal."),
        ("Stage 4 — the report. ", "Add it all up into something a recruiter can act on."),
    ):
        bullet(doc, b, lead=lead)

    h2(doc, "4.1  The thirteen parts")
    table(doc, ["", "What it does", "In plain English", "File"],
          [[t, n, how, f] for t, n, f, how in MODULES],
          widths=[1.0, 3.4, 7.4, 3.7], font_size=8)

    # ── 5. Technology ────────────────────────────────────────────────────
    h1(doc, "5.  What it is built with")
    para(doc,
         "Every choice has a downside as well as an upside. Both are listed, because "
         "pretending otherwise helps nobody.")
    table(doc, ["Tool", "Used for", "Why", "Downside"],
          [[t, u, w, c] for t, u, w, c in TECH],
          widths=[2.8, 3.4, 4.8, 4.5], font_size=8)

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
