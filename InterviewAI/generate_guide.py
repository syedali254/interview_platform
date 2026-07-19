from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from pathlib import Path

doc = Document()

# ── Styles ──
style = doc.styles['Normal']
font = style.font
font.name = 'Calibri'
font.size = Pt(11)

# ── Title ──
title = doc.add_heading('InterviewAI — Project Guide', level=0)
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
doc.add_paragraph('')
doc.add_paragraph('CMP7200 Individual Masters Project | Birmingham City University').alignment = WD_ALIGN_PARAGRAPH.CENTER
doc.add_paragraph('v0.1').alignment = WD_ALIGN_PARAGRAPH.CENTER
doc.add_page_break()

# ── 1. Overview ──
doc.add_heading('1. Project Overview', level=1)
doc.add_paragraph(
    'InterviewAI is an AI-powered technical interview platform. Candidates upload their CV '
    'and a Job Description (JD), and the system performs automated skill gap analysis using '
    'the ESCO taxonomy (European standard for skill classification). It then conducts a '
    'structured interview in one of two modes:'
)
bullets = [
    ('Text Mode', 'The candidate types answers to questions in a Streamlit UI. Each answer '
     'is evaluated by an LLM-as-Judge (Gemini) and scored in real time.'),
    ('LiveKit Mode', 'A voice-based interview using a self-hosted LiveKit server. The AI agent '
     'asks questions via ElevenLabs TTS, listens via Deepgram STT, and the candidate responds '
     'through a web-based LiveKit client.'),
]
for title_text, desc in bullets:
    p = doc.add_paragraph()
    run = p.add_run(f'{title_text}: ')
    run.bold = True
    p.add_run(desc)

doc.add_paragraph(
    'After the interview, a structured report is generated showing overall score, per-skill '
    'breakdown, strengths, gaps, and recommendations.'
)

# ── 2. Directory Structure ──
doc.add_heading('2. Directory Structure', level=1)
doc.add_paragraph('Below is the full project layout with a brief description of each file.')

structure = [
    ('InterviewAI/', 'Project root'),
    ('  .env', 'Environment variables (API keys) — not tracked in git'),
    ('  .gitignore', 'Git ignore rules'),
    ('  app.py', 'Main entry point (Streamlit). Two-tab UI: Text Mode + LiveKit Mode.'),
    ('  requirements.txt', 'Python dependencies'),
    ('  README.md', 'Setup and usage instructions'),
    ('  generate_guide.py', 'This guide generator script'),
    ('  core/', 'Core application package'),
    ('    config.py', 'Configuration: env vars, scoring thresholds, interview settings'),
    ('    llm.py', 'Unified LLM client — calls Gemini API (text + JSON modes)'),
    ('    __init__.py', 'Package marker'),
    ('    agents/', 'AI agent modules'),
    ('      cv_agent.py', 'CV parser: extracts skills/experience from uploaded PDF or text'),
    ('      jd_agent.py', 'JD parser: extracts job title, role level, required skills'),
    ('      question_agent.py', 'Question generator: produces structured question sets via LLM'),
    ('      __init__.py', 'Package marker'),
    ('    evaluator/', 'Answer evaluation module'),
    ('      evaluator.py', 'LLM-as-Judge: scores answers (Track A), generates reference answers'),
    ('      __init__.py', 'Package marker'),
    ('    graph/', 'Skill knowledge graph (ESCO taxonomy)'),
    ('      skill_graph.py', 'Builds NetworkX DiGraph from ESCO CSV data'),
    ('      state.py', 'InterviewState: tracks per-skill progress during interview'),
    ('      traversal.py', 'Adaptive skill picker: selects next skill based on scores'),
    ('      visualize.py', 'Graph visualization: renders candidate/JD/gap charts'),
    ('      __init__.py', 'Package marker'),
    ('    pipeline/', 'Interview orchestration'),
    ('      interview_loop.py', 'InterviewLoop class: orchestrates question->answer->evaluate cycle'),
    ('      __init__.py', 'Package marker'),
    ('    report/', 'Report generation'),
    ('      generator.py', 'Generates final interview report with scores/verdict/breakdown'),
    ('      __init__.py', 'Package marker'),
    ('    livekit/', 'LiveKit voice interview system'),
    ('      run_agent.py', 'Voice agent: speaks questions (ElevenLabs), listens (Deepgram)'),
    ('      whisper_server.py', 'HTTP server: serves client.html, generates LiveKit tokens'),
    ('      launcher.py', 'Launches/manages LiveKit server process'),
    ('      client.html', 'Web UI for voice interview (camera, chat, transcription)'),
    ('      livekit.yaml', 'LiveKit server configuration'),
    ('      __init__.py', 'Package marker'),
    ('  data/', 'Data files'),
    ('    esco/', 'ESCO taxonomy CSVs'),
    ('      digitalSkillsCollection_en.csv', '1,201 IT skills with descriptions'),
    ('      broaderRelationsSkillPillar.csv', 'Skill hierarchy/relationships'),
]

for line, desc in structure:
    p = doc.add_paragraph()
    run = p.add_run(f'  {line}')
    run.font.size = Pt(9)
    run.font.name = 'Consolas'
    p.add_run(f'  — {desc}')

doc.add_page_break()

# ── 3. Architecture & Flow ──
doc.add_heading('3. Architecture & Flow', level=1)

doc.add_heading('3.1 Data Flow', level=2)
steps = [
    ('1. Input', 'User uploads CV (PDF/text) and pastes a Job Description in the Streamlit UI.'),
    ('2. Parsing', 'cv_agent.py extracts candidate skills/experience. jd_agent.py extracts job title, role level, and required skills.'),
    ('3. Skill Graph', 'skill_graph.py builds a NetworkX graph from ESCO taxonomy (1,201 IT skills). Candidate and JD skills are mapped to ESCO URIs via fuzzy matching.'),
    ('4. Gap Analysis', 'The graph compares candidate skills vs JD requirements to identify gaps. Topics are generated for skills needing verification.'),
    ('5. Question Generation', 'question_agent.py uses Gemini LLM to generate a structured interview: opening questions, technical questions per skill, behavioural questions, closing.'),
    ('6. Interview Loop', 'InterviewLoop (interview_loop.py) cycles through skills, generating position-specific questions on the fly, collecting answers, and evaluating them.'),
    ('7. Evaluation', 'evaluator.py uses LLM-as-Judge (Track A — two parallel Gemini calls with different criterion orderings, scores averaged).'),
    ('8. Report', 'generator.py produces a final report with overall score, per-skill breakdown, strengths/gaps, and answer log.'),
]
for title_text, desc in steps:
    p = doc.add_paragraph()
    run = p.add_run(f'{title_text}: ')
    run.bold = True
    p.add_run(desc)

doc.add_heading('3.2 Two Interview Modes', level=2)

doc.add_heading('Text Mode', level=3)
doc.add_paragraph(
    'In Text Mode, the candidate answers questions by typing in a Streamlit text area. '
    'The flow is:'
)
text_steps = [
    'InterviewLoop.get_next_question() picks the next skill adaptively (lowest score first).',
    'generate_position_question() creates a question tailored to the skill, difficulty, and job context.',
    'The candidate types an answer and clicks Submit.',
    'evaluate_answer() runs LLM-as-Judge (two Gemini calls, scores averaged).',
    'The result (score, verdict, feedback) is displayed. The loop continues until all skills are verified or max questions reached.',
    'A final report is generated with full breakdown.',
]
for s in text_steps:
    doc.add_paragraph(s, style='List Bullet')

doc.add_heading('LiveKit Mode', level=3)
doc.add_paragraph(
    'In LiveKit Mode, the interview is conducted via voice using a self-hosted LiveKit server. '
    'The flow is:'
)
livekit_steps = [
    'whisper_server.py serves an HTML page (client.html) and generates LiveKit access tokens.',
    'launcher.py starts the LiveKit server if not already running.',
    'The user connects from client.html (browser), publishing their mic + camera tracks.',
    'run_agent.py connects as an AI agent, speaking pre-generated questions via ElevenLabs TTS.',
    'The candidate\'s spoken answers are transcribed via Deepgram STT.',
    'The conversation (questions + answers) is displayed in real time in client.html.',
    'After all questions, a transcript JSON is saved to temp directory.',
]
for s in livekit_steps:
    doc.add_paragraph(s, style='List Bullet')

doc.add_page_break()

# ── 4. Key Components ──
doc.add_heading('4. Key Components Explained', level=1)

components = [
    ('app.py (Main Entry Point)', [
        'Streamlit application with two tabs: "Text Interview" and "Live Interview".',
        'Tab 1 (Text): user uploads CV + JD, system parses/builds graph/generates questions, then runs the interview loop inline.',
        'Tab 2 (LiveKit): user uploads CV + JD, generates questions, then launches the LiveKit client in a new browser tab.',
        'Contains collapsible debug panel showing state/logs.',
        'Starts a background HTTP server (whisper_server.py) on import to serve LiveKit tokens and client page.',
    ]),
    ('core/config.py', [
        'Loads .env from project root via python-dotenv.',
        'Exposes constants: GEMINI_API_KEY, scoring thresholds (70 strong, 40 weak), max questions (3 per session), skill verification questions (3 per skill), LLM temperature/max tokens.',
        'Status constants for graph state machine: pending, verified_strong, verified_weak, confirmed_gap.',
    ]),
    ('core/llm.py (LLM Client)', [
        'Single unified client for Gemini API.',
        '_call_gemini(): POST to Gemini generateContent endpoint with prompt + config. Returns raw text.',
        'call_llm(): public wrapper for text generation.',
        'call_llm_json(): calls LLM, strips markdown fences, attempts JSON.parse. Falls back to json_repair library if standard parsing fails.',
    ]),
    ('core/agents/', [
        'cv_agent.py: Parses resume text/PDF to extract name, skills list, and experience summary using Gemini.',
        'jd_agent.py: Parses job description to extract job title, role level (junior/mid/senior), and required skills using Gemini.',
        'question_agent.py: Two functions — generate_interview_questions() creates full structured set (opening, technical, behavioural, closing) from graph topics; generate_position_question() creates a single on-the-fly question for a specific skill during live interview.',
    ]),
    ('core/graph/', [
        'skill_graph.py: Loads ESCO digital skills CSV into a NetworkX DiGraph. Skills connected via broader/narrower relationships. Fuzzy-matches candidate/JD skills to ESCO URIs using difflib. Extends ESCO with modern tech (Python, React, Docker, etc.).',
        'state.py: InterviewState contains per-skill SkillNodeState dataclasses tracking status, scores, questions asked. Key methods: record_answer() transitions skill states based on scores; is_complete() checks if all skills verified.',
        'traversal.py: pick_next_skill() selects the next skill adaptively — lowest average score first, with priority weighting. decide_follow_up() determines if a weak answer warrants a follow-up question.',
        'visualize.py: Renders matplotlib graphs showing candidate skills, JD requirements, gaps, and the full unified skill map — displayed in the Streamlit UI.',
    ]),
    ('core/evaluator/evaluator.py', [
        'Track A LLM-as-Judge evaluation.',
        'generate_reference_answer(): Creates an ideal answer for a question using Gemini (acts as benchmark).',
        'evaluate_answer(): Skips <10 word answers (immediate gap verdict). Otherwise generates reference, then runs two parallel evaluations with different criterion orderings to reduce bias. Scores averaged from both calls.',
        'Scoring criteria: technical_accuracy (0-25), completeness (0-25), clarity (0-25), relevance (0-25). Total = 0-100.',
        'Returns: final_score, verdict (strong/weak/gap), reference_answer, track_a details.',
    ]),
    ('core/pipeline/interview_loop.py', [
        'InterviewLoop class orchestrates the entire text interview lifecycle.',
        'get_next_question(): picks next skill adaptively, generates a position-specific question via LLM.',
        'submit_answer(): evaluates the answer via evaluator.py, updates state, decides follow-ups.',
        'get_summary(): returns current state snapshot for report generation.',
    ]),
    ('core/report/generator.py', [
        'generate_report() takes an InterviewLoop, computes overall score (average of all answers), generates a verdict (strong_hire/weak_hire/no_hire), produces per-skill breakdown, identifies strengths and gaps.',
        'Returns a structured dict suitable for display in Streamlit.',
    ]),
    ('core/livekit/ (Voice System)', [
        'whisper_server.py: Minimal HTTP server (port 18765) serving client.html at /livekit, generating LiveKit tokens at /token, and saving transcripts at /save_transcript. Starts agent subprocess (run_agent.py) when a token is requested.',
        'run_agent.py: LiveKit Agent that speaks 5 pre-generated questions via ElevenLabs TTS, listens for answers via Deepgram STT, and publishes transcript data to the room.',
        'launcher.py: Manages the LiveKit server process lifecycle (start/stop/cleanup).',
        'client.html: Full-featured browser client with webcam, real-time transcription display, chat-style conversation log, and connect/disconnect controls.',
        'livekit.yaml: Configuration for self-hosted LiveKit server (ports, logging, keys).',
    ]),
]

for comp_title, bullets_list in components:
    doc.add_heading(comp_title, level=2)
    for b in bullets_list:
        doc.add_paragraph(b, style='List Bullet')

doc.add_page_break()

# ── 5. API Keys & Configuration ──
doc.add_heading('5. API Keys & Configuration', level=1)
doc.add_paragraph('The following environment variables must be set in .env:')
keys = [
    ('GEMINI_API_KEY', 'Required for all LLM operations (question gen, evaluation, parsing)'),
    ('DEEPGRAM_API_KEY', 'Required for LiveKit Mode (speech-to-text)'),
    ('ELEVENLABS_API_KEY', 'Required for LiveKit Mode (text-to-speech)'),
    ('LIVEKIT_URL', 'WebSocket URL for self-hosted LiveKit (default: ws://localhost:7880)'),
    ('LIVEKIT_API_KEY', 'LiveKit API key (default: devkey)'),
    ('LIVEKIT_API_SECRET', 'LiveKit API secret (default: secret)'),
]
for key, desc in keys:
    p = doc.add_paragraph()
    run = p.add_run(f'{key}: ')
    run.bold = True
    p.add_run(desc)

doc.add_paragraph('')
doc.add_paragraph('Scoring thresholds (configurable in core/config.py):')
p = doc.add_paragraph()
p.add_run('SCORE_STRONG_THRESHOLD = 70').bold = True
doc.add_paragraph('Score >= 70 → strong_hire verdict')
p = doc.add_paragraph()
p.add_run('SCORE_WEAK_THRESHOLD = 40').bold = True
doc.add_paragraph('Score >= 40 but < 70 → weak_hire. Score < 40 → no_hire (gap)')

# ── 6. How to Run ──
doc.add_heading('6. How to Run', level=1)
doc.add_paragraph('1. Install dependencies: pip install -r requirements.txt')
doc.add_paragraph('2. Create .env file with required API keys (see Section 5)')
doc.add_paragraph('3. For LiveKit Mode: download livekit-server from github.com/livekit/livekit/releases')
doc.add_paragraph('4. Run: streamlit run app.py')
doc.add_paragraph('5. Open the URL shown in terminal (default: http://localhost:8501)')

# ── Save ──
output_path = Path(__file__).resolve().parent / 'PROJECT_GUIDE.docx'
doc.save(output_path)
print(f'Guide saved to {output_path}')
