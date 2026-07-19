from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from pathlib import Path

doc = Document()
style = doc.styles['Normal']
style.font.name = 'Calibri'
style.font.size = Pt(11)

# ── Title ──
doc.add_heading('InterviewAI — Project Guide', level=0)
doc.add_paragraph(
    'A clear explanation of what this project is, how it works, '
    'and what every file inside the core/ folder does.'
)

# ═══════════════════════════════════════════════════════════════════
# SECTION 1: PROJECT OVERVIEW
# ═══════════════════════════════════════════════════════════════════
doc.add_heading('1. What Is This Project?', level=1)
doc.add_paragraph(
    'InterviewAI is an AI-powered interview system. A candidate uploads their Resume (CV) '
    'and a Job Description (JD), and the system:'
)
steps = [
    'Reads the CV and JD to understand the candidate\'s skills and what the job requires.',
    'Builds a skill graph using the ESCO taxonomy (a European standard list of 1,201 IT skills).',
    'Compares candidate skills vs job requirements to find gaps.',
    'Generates interview questions targeting the weak or missing skills.',
    'Asks the questions one by one and evaluates the answers using AI (Gemini).',
    'Produces a final report with scores, strengths, gaps, and a hire verdict.',
]
for s in steps:
    doc.add_paragraph(s, style='List Bullet')

doc.add_paragraph(
    'The interview can be done in two ways:'
)
p = doc.add_paragraph()
p.add_run('Text Mode: ').bold = True
p.add_run('You type your answers in a web page.')
p = doc.add_paragraph()
p.add_run('LiveKit Mode: ').bold = True
p.add_run('You speak your answers through a microphone, and an AI voice agent interviews you.')

# ═══════════════════════════════════════════════════════════════════
# SECTION 2: INPUTS AND OUTPUTS
# ═══════════════════════════════════════════════════════════════════
doc.add_heading('2. Inputs & Outputs', level=1)

doc.add_heading('Inputs (what you give the system)', level=2)
inputs = [
    'Resume / CV — a PDF or text file containing the candidate\'s work history and skills.',
    'Job Description (JD) — text describing the job role, required skills, and experience level.',
    'API Keys — stored in a .env file: Gemini (for AI), Deepgram (for speech-to-text), ElevenLabs (for text-to-speech).',
]
for i in inputs:
    doc.add_paragraph(i, style='List Bullet')

doc.add_heading('Outputs (what the system gives back)', level=2)
outputs = [
    'Skill Gap Analysis — which skills the candidate has, which are missing, and which need verification.',
    'Interview Questions — a structured set of questions (opening, technical, behavioural, closing).',
    'Answer Scores — each answer gets a score out of 100, with detailed feedback.',
    'Final Report — overall score, hire verdict (Strong Hire / Weak Hire / No Hire), per-skill breakdown, strengths, gaps, and full answer log.',
]
for o in outputs:
    doc.add_paragraph(o, style='List Bullet')

# ═══════════════════════════════════════════════════════════════════
# SECTION 3: HOW IT WORKS (STEP BY STEP)
# ═══════════════════════════════════════════════════════════════════
doc.add_heading('3. How It Works — Step by Step', level=1)

steps_data = [
    ('Step 1: Parse CV & JD', [
        'cv_agent.py reads the uploaded CV (PDF or text) and uses Gemini AI to extract: name, list of skills, experience summary.',
        'jd_agent.py reads the Job Description and uses Gemini to extract: job title, role level (junior/mid/senior), required skills.',
    ]),
    ('Step 2: Build Skill Graph', [
        'skill_graph.py loads the ESCO taxonomy (1,201 IT skills from a CSV file) into a graph structure using NetworkX.',
        'It adds modern technologies (Python, React, Docker, etc.) that are not in the official ESCO list.',
        'The candidate\'s skills and the job\'s required skills are matched against the graph using fuzzy matching.',
    ]),
    ('Step 3: Gap Analysis', [
        'The system compares what the candidate knows vs what the job requires.',
        'Skills that are missing or weak become "topics" for the interview.',
        'Each topic gets a priority (high/medium/low) and a reason explaining why it was selected.',
    ]),
    ('Step 4: Generate Questions', [
        'question_agent.py takes the topics and uses Gemini to generate a full interview question set.',
        'The set includes: opening questions (warm-up), technical questions (one per skill), behavioural questions (STAR format), closing questions.',
        'Each question has a difficulty level, follow-up probe, and estimated duration.',
    ]),
    ('Step 5: Conduct Interview', [
        'The InterviewLoop (interview_loop.py) takes control.',
        'It picks the next skill to test — always the one with the lowest score first (adaptive strategy).',
        'For each skill, it generates a fresh question on the fly using Gemini.',
        'The candidate answers (either by typing in Text Mode or speaking in LiveKit Mode).',
        'The answer is scored by evaluator.py using LLM-as-Judge (two parallel Gemini calls to reduce bias).',
        'If the answer is weak, a follow-up question may be asked (max 1 per skill).',
        'The loop continues until all skills are verified or the question limit is reached.',
    ]),
    ('Step 6: Generate Report', [
        'After the interview, report/generator.py creates a final report.',
        'It calculates the overall score (average of all answers).',
        'It assigns a verdict: Strong Hire (≥70), Weak Hire (40-69), No Hire (<40).',
        'It lists strengths (skills scoring ≥70), gaps (skills scoring <40), and development areas.',
        'It includes a full answer log with questions, answers, scores, and feedback.',
    ]),
]

for title, bullets in steps_data:
    doc.add_heading(title, level=2)
    for b in bullets:
        doc.add_paragraph(b, style='List Bullet')

# ═══════════════════════════════════════════════════════════════════
# SECTION 4: MODULES / COMPONENTS
# ═══════════════════════════════════════════════════════════════════
doc.add_heading('4. Modules & Components', level=1)
doc.add_paragraph(
    'The project has 7 main modules inside core/. Each module has a specific job:'
)

modules = [
    ('agents/', 'Parsing & Question Generation',
     'Contains 3 files: cv_agent.py (reads CV), jd_agent.py (reads JD), question_agent.py (generates interview questions).'),
    ('evaluator/', 'Answer Scoring',
     'Contains evaluator.py which uses Gemini to score answers on 4 criteria: technical accuracy, completeness, clarity, relevance.'),
    ('graph/', 'Skill Knowledge Graph',
     'Contains 4 files: skill_graph.py (builds ESCO graph), state.py (tracks interview progress), traversal.py (chooses next skill), visualize.py (draws charts).'),
    ('pipeline/', 'Interview Orchestrator',
     'Contains interview_loop.py which runs the question → answer → evaluate cycle.'),
    ('report/', 'Final Report',
     'Contains generator.py which builds the final structured report.'),
    ('livekit/', 'Voice Interview System',
     'Contains 4 files + client.html: run_agent.py (voice agent), whisper_server.py (HTTP server), launcher.py (server manager), livekit.yaml (config).'),
    ('config.py + llm.py', 'Configuration & AI Client',
     'config.py loads settings from .env. llm.py is the unified client for calling Gemini AI.'),
]

for name, title, desc in modules:
    p = doc.add_paragraph()
    run = p.add_run(f'{name} ')
    run.bold = True
    run.font.size = Pt(12)
    p2 = doc.add_paragraph()
    run2 = p2.add_run(f'{title}: ')
    run2.bold = True
    p2.add_run(desc)

# ═══════════════════════════════════════════════════════════════════
# SECTION 5: DIRECTORY STRUCTURE (InterviewAI/core/)
# ═══════════════════════════════════════════════════════════════════
doc.add_heading('5. Directory Structure — InterviewAI/core/', level=1)
doc.add_paragraph(
    'Below is every file and folder inside core/, with a plain-English explanation of what it does.'
)

doc.add_heading('core/config.py', level=2)
doc.add_paragraph(
    'This is the settings file. It loads the .env file and defines all the numbers and rules the project uses: '
    'the Gemini API key and model name, the temperature (creativity) of the AI, the maximum number of tokens, '
    'the scoring thresholds (70 = strong, 40 = weak), how many questions to ask per session (3), '
    'how many follow-ups allowed (1), and the status labels for the graph (pending, verified, confirmed gap). '
    'Every other file imports from here so there is one central place to change settings.'
)

doc.add_heading('core/llm.py', level=2)
doc.add_paragraph(
    'This is the AI communication module. It contains the code that talks to Google\'s Gemini API. '
    'There are three functions: call_llm() sends a text prompt and gets text back. '
    'call_llm_json() sends a prompt and expects JSON back — it also cleans up the response '
    '(removes markdown formatting) and if the JSON is broken, it uses a library called json_repair '
    'to fix it. This is used by the question generator and evaluator to get structured data from the AI.'
)

# agents/
doc.add_heading('core/agents/ (folder)', level=2)
doc.add_paragraph('This folder contains 3 files that handle input parsing and question creation.')

doc.add_heading('core/agents/cv_agent.py', level=3)
doc.add_paragraph(
    'Reads a candidate\'s CV (resume). If the file is a PDF, it first extracts the text using PyPDF2. '
    'Then it sends the full text to Gemini with a prompt asking it to extract: the candidate\'s name, '
    'their list of skills, and a short experience summary. Returns this as a dictionary.'
)

doc.add_heading('core/agents/jd_agent.py', level=3)
doc.add_paragraph(
    'Reads a Job Description text. Sends it to Gemini with a prompt asking it to extract: the job title, '
    'the role level (junior/mid/senior), and the list of required skills. Returns this as a dictionary.'
)

doc.add_heading('core/agents/question_agent.py', level=3)
doc.add_paragraph(
    'Generates interview questions. It has three functions: '
    'generate_interview_questions() takes the skill graph topics and creates a full structured question set '
    '(opening questions, technical questions per skill, behavioural questions, closing questions) using Gemini. '
    'It also calculates estimated total interview duration. '
    'generate_position_question() is used during the live interview — it creates a single question on the fly '
    'for a specific skill, adjusted for difficulty and whether it\'s a follow-up. '
    'build_interview_flow() takes the structured set and flattens it into a simple ordered list.'
)

# evaluator/
doc.add_heading('core/evaluator/ (folder)', level=2)
doc.add_paragraph('This folder contains 1 file that scores answers.')

doc.add_heading('core/evaluator/evaluator.py', level=3)
doc.add_paragraph(
    'This is the scoring engine. It works like this: first, it generates a "reference answer" (an ideal answer) '
    'for the question using Gemini. Then it compares the candidate\'s real answer against this reference. '
    'It scores on 4 criteria: technical accuracy (0-25), completeness (0-25), clarity (0-25), relevance (0-25). '
    'To reduce AI bias, it runs the evaluation twice with the criteria in different orders and averages the scores. '
    'If the answer is very short (under 10 words), it automatically scores 0. '
    'Returns a result with final score (0-100), verdict (strong/weak/gap), feedback, and the reference answer.'
)

# graph/
doc.add_heading('core/graph/ (folder)', level=2)
doc.add_paragraph(
    'This folder contains 4 files that build and manage the skill knowledge graph.'
)

doc.add_heading('core/graph/skill_graph.py', level=3)
doc.add_paragraph(
    'Builds a graph of skills using the ESCO taxonomy (a European standard list of 1,201 IT skills). '
    'It loads two CSV files: one with skill names and descriptions, another with relationships between skills '
    '(broader/narrower). It creates a NetworkX directed graph where skills are nodes and relationships are edges. '
    'Since ESCO is missing many modern tools (Python, React, Docker, etc.), it adds them manually. '
    'It can fuzzy-match skill names to the graph using difflib. The gap_analysis() function compares '
    'a candidate\'s skills against job requirements and identifies what\'s missing.'
)

doc.add_heading('core/graph/state.py', level=3)
doc.add_paragraph(
    'Tracks the progress of the interview. For each skill being tested, it stores: current status '
    '(pending, verified_strong, verified_weak, confirmed_gap), list of scores, how many questions asked, '
    'best score so far, and feedback. The record_answer() method updates the status automatically based on '
    'the score. The InterviewState class holds all skills together and provides methods like pending_skills, '
    'is_complete(), and summary() to check overall progress.'
)

doc.add_heading('core/graph/traversal.py', level=3)
doc.add_paragraph(
    'Decides which skill to ask about next. The pick_next_skill() function looks at all incomplete skills '
    'and picks the one with the lowest average score first (prioritizing high-priority skills). '
    'It avoids asking the same skill twice in a row. '
    'The decide_follow_up() function checks if a weak answer (below 70) needs a follow-up question, '
    'capped at one follow-up per skill.'
)

doc.add_heading('core/graph/visualize.py', level=3)
doc.add_paragraph(
    'Creates charts (matplotlib figures) to show the skill analysis visually. '
    'render_candidate_graph() shows the candidate\'s skills grouped by category. '
    'render_job_graph() shows the job\'s required skills. '
    'render_gap_graph() highlights missing or weak skills. '
    'render_full_graph() shows everything together. These charts appear in the Streamlit UI.'
)

# pipeline/
doc.add_heading('core/pipeline/ (folder)', level=2)
doc.add_paragraph('This folder contains 1 file that orchestrates the interview.')

doc.add_heading('core/pipeline/interview_loop.py', level=3)
doc.add_paragraph(
    'This is the brain of the Text Mode interview. The InterviewLoop class: '
    'get_next_question() picks the next skill using traversal.py, determines difficulty based on '
    'how the candidate has scored so far on that skill, generates a fresh question via question_agent.py, '
    'and returns it. submit_answer() takes the candidate\'s typed answer, sends it to evaluator.py for scoring, '
    'updates the graph state, and decides if a follow-up is needed. '
    'The loop keeps going until all skills are verified or the maximum questions (3) are asked. '
    'get_summary() collects everything for the final report.'
)

# report/
doc.add_heading('core/report/ (folder)', level=2)
doc.add_paragraph('This folder contains 1 file that creates the final output.')

doc.add_heading('core/report/generator.py', level=3)
doc.add_paragraph(
    'After the interview ends, this builds the final report. It takes the InterviewLoop, '
    'computes the overall score (average of all answers), picks a verdict: Strong Hire (≥70), '
    'Weak Hire (40-69), or No Hire (<40). It creates a per-skill breakdown showing scores and feedback. '
    'It identifies strengths (skills scoring ≥70), gaps (skills scoring <40), and development areas. '
    'Returns a dictionary with all this information plus a full answer log.'
)

# livekit/
doc.add_heading('core/livekit/ (folder)', level=2)
doc.add_paragraph(
    'This folder handles the voice interview mode (LiveKit). It has 4 Python files, a config file, '
    'and an HTML file.'
)

doc.add_heading('core/livekit/run_agent.py', level=3)
doc.add_paragraph(
    'This is the AI voice agent. It connects to a LiveKit room and conducts the interview by voice. '
    'It speaks pre-generated questions using ElevenLabs TTS (text-to-speech). '
    'It listens to the candidate\'s answers using Deepgram STT (speech-to-text). '
    'It does NOT use Gemini for conversation — all questions are pre-loaded. '
    'The agent publishes real-time transcript data to the room so the web client can display it. '
    'After all questions are done, it saves a transcript JSON file and disconnects.'
)

doc.add_heading('core/livekit/whisper_server.py', level=3)
doc.add_paragraph(
    'A tiny web server (runs on port 18765) that provides three services: '
    'GET /livekit serves the client.html page (the voice interview UI). '
    'GET /token generates a LiveKit access token and starts the agent subprocess. '
    'POST /save_transcript saves the conversation transcript. '
    'It runs in a background thread and is started automatically when app.py launches.'
)

doc.add_heading('core/livekit/launcher.py', level=3)
doc.add_paragraph(
    'Manages the LiveKit server process. start_livekit_server() checks if LiveKit is already running '
    '(on port 7880) and starts it if not. launch() starts both the LiveKit server and the web server, '
    'and returns the client URL. cleanup() shuts everything down when the application exits.'
)

doc.add_heading('core/livekit/livekit.yaml', level=3)
doc.add_paragraph(
    'Configuration file for the LiveKit server. Sets the ports, API keys, logging level, '
    'and WebRTC settings. The launcher.py passes this to the livekit-server executable.'
)

doc.add_heading('core/livekit/client.html', level=3)
doc.add_paragraph(
    'A web page that the candidate uses for the voice interview. It shows: the candidate\'s webcam feed, '
    'real-time transcription of what the AI agent says, a chat-style conversation history, '
    'and the current question being asked. It connects to LiveKit using the livekit-client JavaScript SDK, '
    'publishes the mic and camera tracks, and subscribes to the agent\'s audio. '
    'It auto-connects when the page loads and saves a transcript when disconnected.'
)

# ── Bottom line ──
doc.add_heading('6. Summary', level=1)
doc.add_paragraph(
    'InterviewAI takes a Resume + Job Description → parses them → builds a skill graph → '
    'finds gaps → generates questions → conducts an interview (text or voice) → '
    'scores each answer using AI → produces a final report with verdict and recommendations.'
)

doc.add_paragraph(
    'All the logic lives inside core/: config (settings), llm (AI client), agents (parsing & questions), '
    'evaluator (scoring), graph (skill knowledge & state), pipeline (interview loop), '
    'report (final output), and livekit (voice system).'
)

# Save
out = Path(__file__).resolve().parent / 'PROJECT_GUIDE.docx'
doc.save(out)
print(f'Saved to {out}')
