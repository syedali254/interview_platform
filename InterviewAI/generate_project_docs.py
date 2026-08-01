"""Generate PROJECT_DOCS.docx — comprehensive project explanation."""

from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
import os

doc = Document()

# Styling
for s in doc.sections:
    s.top_margin = Cm(2.54)
    s.bottom_margin = Cm(2.54)
    s.left_margin = Cm(2.54)
    s.right_margin = Cm(2.54)

style = doc.styles['Normal']
style.font.name = 'Arial'
style.font.size = Pt(11)
style.paragraph_format.line_spacing = 1.5


def h1(text):
    h = doc.add_heading(text, level=1)
    for r in h.runs:
        r.font.name = 'Arial'
        r.font.color.rgb = RGBColor(0x1a, 0x20, 0x2c)

def h2(text):
    h = doc.add_heading(text, level=2)
    for r in h.runs:
        r.font.name = 'Arial'
        r.font.color.rgb = RGBColor(0x2c, 0x52, 0x82)

def h3(text):
    h = doc.add_heading(text, level=3)
    for r in h.runs:
        r.font.name = 'Arial'

def para(text, bold=False):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    r = p.add_run(text)
    r.font.size = Pt(11)
    r.font.name = 'Arial'
    r.bold = bold
    p.paragraph_format.line_spacing = 1.5

def bullet(text):
    p = doc.add_paragraph(style='List Bullet')
    r = p.add_run(text)
    r.font.size = Pt(11)
    r.font.name = 'Arial'


# ═══════════════════════════════════════════════════════
# TITLE
# ═══════════════════════════════════════════════════════
for _ in range(4):
    doc.add_paragraph()

tp = doc.add_paragraph()
tp.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = tp.add_run('InterviewAI')
r.bold = True
r.font.size = Pt(28)
r.font.name = 'Arial'

doc.add_paragraph()

tp2 = doc.add_paragraph()
tp2.alignment = WD_ALIGN_PARAGRAPH.CENTER
r2 = tp2.add_run('Project Documentation')
r2.font.size = Pt(18)
r2.font.name = 'Arial'

doc.add_paragraph()

tp3 = doc.add_paragraph()
tp3.alignment = WD_ALIGN_PARAGRAPH.CENTER
r3 = tp3.add_run(
    'Multi-Agent AI Interview Platform\n'
    'Voice Interviews • Skill Graph • Dual-Track Evaluation • Behavioral Integrity'
)
r3.font.size = Pt(12)
r3.font.name = 'Arial'
r3.italic = True

doc.add_page_break()

# ═══════════════════════════════════════════════════════
# OVERVIEW
# ═══════════════════════════════════════════════════════
h1('1. Project Overview')

para(
    'InterviewAI is an intelligent interview platform that conducts real voice-based '
    'technical interviews with candidates. It uses AI to ask questions, listen to answers, '
    'detect emotions, check for cheating, and produce a detailed hiring recommendation.'
)

para(
    'The system is built around 12 modules organized into 4 phases:'
)

bullet('Phase 1 — Pre-Interview: Parse CV, understand job requirements, build skill graph, generate questions')
bullet('Phase 2 — Live Interview: Voice conversation with AI, face tracking, emotion detection')
bullet('Phase 3 — Evaluation: Score answers using two methods, detect behavioral anomalies')
bullet('Phase 4 — Report: Combine all scores, produce recommendation with explanation')

para(
    'The platform runs as a web application. The backend is Python (FastAPI) and the '
    'frontend is React. The AI interviewer speaks using ElevenLabs voice, listens using '
    'Deepgram speech-to-text, and thinks using Google Gemini LLM.'
)

doc.add_page_break()

# ═══════════════════════════════════════════════════════
# HOW IT WORKS
# ═══════════════════════════════════════════════════════
h1('2. How the System Works (End-to-End Flow)')

para('Here is what happens from start to finish when a user runs an interview:')

para('Step 1: The user uploads their CV (PDF file) and pastes the job description text.')
para('Step 2: The system sends both to Google Gemini LLM which extracts structured data — skills, experience, required qualifications.')
para('Step 3: The Skill Graph module compares candidate skills against job requirements. It shows three views: matched skills (green), missing skills (red), and extra skills the candidate has but job does not require (purple).')
para('Step 4: The Question Generator creates interview questions that specifically target the skill gaps. It makes technical questions, behavioral questions, and follow-up questions.')
para('Step 5: The user sets up their microphone and camera, then clicks "Begin Interview".')
para('Step 6: The AI interviewer greets the candidate by name and starts asking questions using a natural voice (ElevenLabs). It listens to answers via Deepgram speech-to-text.')
para('Step 7: During the interview, the camera tracks the candidate\'s face for attention and detects emotions (happy, nervous, neutral, etc.) using face-api.js.')
para('Step 8: After the interview ends, each answer gets evaluated by TWO different methods (LLM judge + ML model). If they disagree significantly, the answer is flagged.')
para('Step 9: The Behavioral Integrity module checks for cheating patterns — tab switching, suspiciously fast answers, long pauses.')
para('Step 10: The Fusion Engine combines everything (answer scores 50%, skill match 20%, integrity 15%, engagement 15%) into a final recommendation.')
para('Step 11: The Dashboard shows the complete report with emotion timeline, transcript, scores, and hire/no-hire decision.')

doc.add_page_break()

# ═══════════════════════════════════════════════════════
# MODULE DETAILS
# ═══════════════════════════════════════════════════════
h1('3. Module Details')

para(
    'Each module is explained below with: what it does, how it works technically, '
    'what technology it uses, and which file contains the code.'
)

# --- M1 ---
h2('Module 1 — CV Parsing')
h3('What it does')
para('Takes a candidate\'s CV (as a PDF file or plain text) and extracts structured information from it.')
h3('How it works')
para('When the user uploads a PDF, the system uses PyMuPDF library to extract all text from every page. This raw text is then sent to Google Gemini LLM with a specific prompt that says: "Extract the following fields from this CV: name, email, phone, skills (as a list), work experience (company, role, duration), education, projects." The LLM returns a structured JSON object with all the extracted data.')
h3('Technology used')
bullet('PyMuPDF — reads PDF files and extracts text')
bullet('Google Gemini LLM — understands the text and extracts structured fields')
bullet('JSON parsing — converts LLM output into usable data')
h3('File location')
para('core/agents/cv_agent.py')
h3('Status: FULLY WORKING ✅')

# --- M2 ---
h2('Module 2 — Job Description Understanding')
h3('What it does')
para('Takes a job description text and extracts what skills are required, what responsibilities the role has, and what level of seniority is expected.')
h3('How it works')
para('The user pastes the job description into a text box. This text is sent to Gemini LLM with a prompt asking it to extract: required skills, nice-to-have skills, responsibilities, experience level, and job title. The LLM returns structured JSON.')
h3('Technology used')
bullet('Google Gemini LLM — natural language understanding')
bullet('Prompt engineering — specific extraction prompts')
h3('File location')
para('core/agents/jd_agent.py')
h3('Status: FULLY WORKING ✅')

# --- M3 ---
h2('Module 3 — Skill Graph')
h3('What it does')
para('Compares the candidate\'s skills against job requirements using a knowledge graph. Shows which skills match, which are missing, and which extra skills the candidate has.')
h3('How it works')
para('The system uses the ESCO taxonomy (European Skills, Competences, Qualifications and Occupations) — a standardized database of over 13,000 skills with relationships between them. The candidate skills from M1 and job skills from M2 are mapped into this taxonomy using fuzzy text matching. Then NetworkX builds a graph showing: (1) Matched skills — candidate has what job needs (green), (2) Missing skills — job needs but candidate lacks (red), (3) Extra skills — candidate has but job doesn\'t need (purple). The skill relationships are also tracked (e.g., Python → Machine Learning → Deep Learning).')
h3('Technology used')
bullet('NetworkX — Python library for building and analyzing graphs')
bullet('ESCO taxonomy data — European standard skill classification (stored in data/esco/)')
bullet('Fuzzy matching — maps real skill names to ESCO entries')
h3('File location')
para('core/graph/skill_graph.py')
h3('Status: FULLY WORKING ✅')

# --- M4 ---
h2('Module 4 — Question Generation')
h3('What it does')
para('Creates interview questions that are specifically targeted at the candidate\'s skill gaps. If a candidate is missing "Docker" skills, it generates Docker questions.')
h3('How it works')
para('Takes the skill graph topics (especially gaps and partially-matched skills) and sends them to Gemini LLM with the full context of the CV and JD. The LLM generates: opening questions (warm-up), technical questions (testing specific skills), behavioral questions (testing soft skills and experience), and closing questions. Each question is tagged with which skill it tests. The system creates follow-up questions too — if a candidate gives a weak answer, the AI asks a simpler version.')
h3('Technology used')
bullet('Google Gemini LLM — generates contextual questions')
bullet('Skill graph topics — determines what to ask about')
bullet('Adaptive logic — harder questions for strong candidates, simpler for weak')
h3('File location')
para('core/agents/question_agent.py')
h3('Status: FULLY WORKING ✅')

# --- M5 ---
h2('Module 5 — Voice Interview (LiveKit Agent)')
h3('What it does')
para('Conducts a real-time voice conversation between the AI interviewer and the candidate. The AI speaks questions out loud and listens to spoken answers.')
h3('How it works')
para('This is the most complex module. It uses the LiveKit framework for real-time audio streaming. When the interview starts: (1) A LiveKit room is created, (2) The candidate\'s browser connects with their microphone, (3) A Python agent process starts that joins the same room, (4) The agent uses Deepgram API to convert candidate speech to text in real-time, (5) Google Gemini LLM processes the text and generates a response, (6) ElevenLabs API converts the response to natural-sounding speech, (7) The speech audio is sent back to the candidate. The AI has a personality — it greets by name, asks follow-ups naturally, handles off-topic conversations, and gracefully ends the interview.')
h3('Technology used')
bullet('LiveKit — real-time audio/video framework (handles WebRTC)')
bullet('Deepgram API — speech-to-text (converts voice to text with 99% accuracy)')
bullet('ElevenLabs API — text-to-speech (generates natural AI voice)')
bullet('Google Gemini LLM — generates conversational responses')
bullet('System prompt — defines interviewer personality and rules')
h3('File location')
para('core/livekit/run_agent.py (main agent), core/livekit/launcher.py (starts LiveKit server)')
h3('Status: FULLY WORKING ✅')

# --- M6 ---
h2('Module 6 — Answer Evaluation (Dual-Track)')
h3('What it does')
para('Scores every candidate answer using TWO independent methods, then compares their results. This is the core research contribution of the dissertation.')
h3('How Track A works (LLM-as-Judge)')
para('For each answer: (1) The system first generates an "ideal reference answer" using Gemini — what a perfect candidate would say. (2) Then it sends the candidate\'s actual answer + the reference answer to the LLM with a scoring rubric. (3) The LLM scores on 4 criteria (0-25 each): technical accuracy, completeness, clarity, relevance. (4) To avoid "positional bias" (documented in research), it runs the evaluation TWICE with criteria in different order and averages the results.')
h3('How Track B works (Trained ML Classifier)')
para('Instead of asking an LLM to judge, this approach converts the answer into numbers and lets a trained model predict the score. (1) Extract features: semantic similarity (using Sentence-BERT embeddings — 384-dimensional vectors that capture meaning), keyword coverage, word count, sentence count, specificity score (concrete vs filler words), fluency score. (2) Feed these 6 features into an XGBoost classifier that predicts a score 0-100. (3) Compute SHAP values — these explain exactly WHY the model gave that score (e.g., "low score because semantic_similarity was 0.3 and keyword_coverage was 0.2").')
h3('How the comparison works')
para('Both tracks score every answer independently. If their scores disagree by more than 20 points, the answer gets flagged for human review. The final score is a weighted average: 60% Track A + 40% Track B. This dual-track approach is the main research question of the dissertation.')
h3('Technology used')
bullet('Google Gemini LLM — Track A evaluation')
bullet('Sentence-BERT (all-MiniLM-L6-v2) — creates semantic embeddings for Track B')
bullet('XGBoost — gradient boosting classifier for score prediction')
bullet('SHAP — explains model predictions (feature attribution)')
h3('File locations')
para('core/evaluator/evaluator.py (orchestrator + Track A), core/evaluator/track_b.py (Track B), core/evaluator/train_model.py (training script)')
h3('Status: FULLY WORKING ✅ (Track B uses heuristic fallback until XGBoost is trained)')

# --- M7 ---
h2('Module 7 — Vision Monitor (Face Detection)')
h3('What it does')
para('Tracks whether the candidate\'s face is visible during the interview. If the face disappears for too long (looking away, leaving), it records a distraction event.')
h3('How it works')
para('The browser uses face-api.js (a JavaScript face detection library) with the TinyFaceDetector model. Every 2 seconds it captures a frame from the webcam and checks if a face is present. It uses a threshold of 10 consecutive misses (20+ seconds) before reporting "no face" — this prevents false alarms from brief glances away. Real tab switches are tracked using the browser\'s Page Visibility API (document.hidden).')
h3('Technology used')
bullet('face-api.js — pre-trained face detection model running in browser')
bullet('TinyFaceDetector — lightweight model, works in real-time')
bullet('Page Visibility API — detects real tab switches')
h3('File location')
para('frontend/src/screens/InterviewScreen.jsx (lines ~149-206)')
h3('Status: FULLY WORKING ✅')

# --- M10 ---
h2('Module 10 — Emotion Detection')
h3('What it does')
para('Detects the candidate\'s emotional state during the interview by analyzing their facial expressions in real-time.')
h3('How it works')
para('Uses the same face-api.js library as M7 but with the FaceExpressionNet model added. Every 2 seconds it analyzes the detected face and classifies the expression into: happy, sad, angry, fearful, disgusted, surprised, neutral. Each detection includes a confidence score. All emotions are recorded with timestamps so they can be plotted on a timeline in the final report.')
h3('Technology used')
bullet('face-api.js with FaceExpressionNet — pre-trained expression classification')
bullet('Runs entirely in the browser (no server calls needed)')
bullet('Canvas API — for real-time face overlay visualization')
h3('File location')
para('frontend/src/screens/InterviewScreen.jsx (emotion detection loop)')
h3('Status: FULLY WORKING ✅')

# --- M9 ---
h2('Module 9 — Behavioral Integrity Detection')
h3('What it does')
para('Detects if a candidate might be cheating during the interview by analyzing their behavioral patterns for anomalies.')
h3('How it works')
para('Uses an Isolation Forest algorithm — an unsupervised machine learning model that learns what "normal" interview behavior looks like and flags anything unusual. It extracts 8 behavioral features from the interview session: (1) average response time in seconds, (2) response time standard deviation, (3) number of tab switches, (4) inactivity ratio, (5) average answer length in words, (6) answer length variance coefficient, (7) hesitation ratio, (8) engagement score. The model was trained on 200 synthetic "normal" interview patterns. Anything that deviates significantly from normal gets flagged. Returns: integrity score (0-100), verdict (normal/suspicious/flagged), and specific risk factors.')
h3('Red flags it catches')
bullet('Response time < 3 seconds — possible copy-paste from another source')
bullet('Response time > 30 seconds — possible searching for answers')
bullet('Tab switches > 5 — likely looking up answers')
bullet('High inactivity — candidate leaving the session')
bullet('Inconsistent answer lengths — mixing own answers with copied ones')
h3('Technology used')
bullet('Isolation Forest (scikit-learn) — unsupervised anomaly detection')
bullet('No labelled data needed — learns from normal patterns')
h3('File location')
para('core/evaluator/integrity.py')
h3('Status: FULLY WORKING ✅')

# --- M11 ---
h2('Module 11 — Fusion Engine (Final Recommendation)')
h3('What it does')
para('Combines scores from all modules into one final hiring recommendation with a confidence level.')
h3('How it works')
para('Takes four inputs and applies weighted scoring: (1) Answer quality from M6 — weighted 50% (this is the most important), (2) Skill match percentage from M3 — weighted 20%, (3) Behavioral integrity from M9 — weighted 15%, (4) Engagement/emotion score from M10 — weighted 15%. The weighted sum produces a fusion score (0-100). Recommendation thresholds: above 72 = Strong Hire, 55-72 = Hire, 40-55 = Consider, below 40 = No Hire. Special rule: if integrity score is below 30, the candidate is automatically disqualified regardless of other scores.')
h3('Technology used')
bullet('Weighted scoring algorithm — configurable weights')
bullet('Rule-based override — integrity failure = disqualification')
h3('File location')
para('core/evaluator/fusion.py')
h3('Status: FULLY WORKING ✅')

# --- M12 ---
h2('Module 12 — Report & Dashboard')
h3('What it does')
para('Displays the complete interview results in a visual dashboard with charts, transcript, scores, and the final recommendation.')
h3('How it works')
para('The React frontend collects all data from the interview (transcript, emotions, distractions, scores) and renders it on the Dashboard screen. It includes: (1) Emotion Timeline — a canvas chart plotting emotions over time with different colors, (2) Emotion Distribution — horizontal bars showing percentage of each emotion, (3) Transcript — Q&A pairs with timestamps and response times, (4) Distraction Events — list with severity badges (low/medium/high), (5) Overall Metrics — dominant emotion, total questions, interview duration, (6) Final Recommendation — hire/no-hire with score breakdown.')
h3('Technology used')
bullet('React — UI rendering')
bullet('Canvas API — custom emotion timeline chart')
bullet('CSS Grid/Flexbox — responsive layout')
h3('File location')
para('frontend/src/screens/DashboardScreen.jsx')
h3('Status: FULLY WORKING ✅')

doc.add_page_break()

# ═══════════════════════════════════════════════════════
# TECH STACK
# ═══════════════════════════════════════════════════════
h1('4. Technology Stack')

tbl = doc.add_table(rows=13, cols=3)
tbl.style = 'Light Shading Accent 1'
headers = ['Component', 'Technology', 'Why We Use It']
for i, h in enumerate(headers):
    tbl.rows[0].cells[i].text = h

data = [
    ('Backend Server', 'FastAPI (Python)', 'Fast, handles async, auto-generates API docs'),
    ('Frontend', 'React + Vite', 'Modern single-page app, fast development'),
    ('AI Brain', 'Google Gemini', 'Free tier, good reasoning, fast responses'),
    ('Speech-to-Text', 'Deepgram', 'Real-time transcription, very accurate'),
    ('Text-to-Speech', 'ElevenLabs', 'Natural sounding voice, low latency'),
    ('Voice Framework', 'LiveKit', 'Handles WebRTC audio streaming'),
    ('Skill Graph', 'NetworkX + ESCO', 'Graph operations + standard skill taxonomy'),
    ('ML Classifier', 'XGBoost', 'Fast, accurate, works with SHAP'),
    ('Text Embeddings', 'Sentence-BERT', 'Captures semantic meaning as numbers'),
    ('Explainability', 'SHAP', 'Shows why model made each decision'),
    ('Anomaly Detection', 'Isolation Forest', 'Finds unusual patterns without labels'),
    ('Face/Emotion', 'face-api.js', 'Runs in browser, no server needed'),
]
for i, (comp, tech, why) in enumerate(data, 1):
    tbl.rows[i].cells[0].text = comp
    tbl.rows[i].cells[1].text = tech
    tbl.rows[i].cells[2].text = why

doc.add_page_break()

# ═══════════════════════════════════════════════════════
# FILE STRUCTURE
# ═══════════════════════════════════════════════════════
h1('5. File Structure — What Each File Does')

para('Below is every important file in the project with a one-line explanation of what it does.', bold=True)

files = [
    ('run.bat (in repo root)', 'One-click setup and launch script — the only file you need to run'),
    ('InterviewAI/SETUP.md', 'Setup instructions document'),
    ('InterviewAI/server.py', 'Main backend server — all API endpoints live here'),
    ('InterviewAI/.env.example', 'Template file showing what API keys are needed'),
    ('InterviewAI/.env', 'Your actual API keys (never share this)'),
    ('InterviewAI/requirements.txt', 'List of Python packages the project needs'),
    ('', ''),
    ('core/config.py', 'Configuration — loads API keys, defines score thresholds'),
    ('core/llm.py', 'Wrapper for calling Google Gemini API — all LLM calls go through here'),
    ('', ''),
    ('core/agents/cv_agent.py', 'M1: Parses CV PDF/text into structured data using LLM'),
    ('core/agents/jd_agent.py', 'M2: Parses job description text using LLM'),
    ('core/agents/question_agent.py', 'M4: Generates interview questions from skill topics'),
    ('', ''),
    ('core/graph/skill_graph.py', 'M3: Builds skill graph, matches against ESCO, finds gaps'),
    ('core/graph/state.py', 'Tracks per-skill status during live interview (pending/verified/gap)'),
    ('core/graph/traversal.py', 'Picks which skill to test next based on current state'),
    ('', ''),
    ('core/livekit/run_agent.py', 'M5: The voice interview agent — speaks, listens, responds'),
    ('core/livekit/launcher.py', 'Starts and stops the LiveKit server process'),
    ('core/livekit/livekit.yaml', 'LiveKit server configuration'),
    ('', ''),
    ('core/evaluator/evaluator.py', 'M6: Orchestrates both tracks — runs Track A + Track B, compares'),
    ('core/evaluator/track_b.py', 'M6 Track B: Feature extraction + XGBoost + SHAP'),
    ('core/evaluator/integrity.py', 'M9: Isolation Forest behavioral anomaly detection'),
    ('core/evaluator/fusion.py', 'M11: Weighted fusion of all scores into recommendation'),
    ('core/evaluator/train_model.py', 'Script to train the XGBoost model on synthetic data'),
    ('', ''),
    ('core/pipeline/interview_loop.py', 'Connects graph state + question selection + evaluation'),
    ('core/report/generator.py', 'M12: Generates structured report from interview data'),
    ('', ''),
    ('data/esco/', 'ESCO taxonomy data files (skill classifications from EU)'),
    ('', ''),
    ('frontend/src/App.jsx', 'Main React app — handles step navigation (6 steps)'),
    ('frontend/src/screens/UploadStep.jsx', 'Step 1: CV upload + JD paste UI'),
    ('frontend/src/screens/GraphStep.jsx', 'Step 2: Three skill graph visualizations'),
    ('frontend/src/screens/QuestionsStep.jsx', 'Step 3: Shows generated questions'),
    ('frontend/src/screens/SetupScreen.jsx', 'Step 4: Camera/microphone device setup'),
    ('frontend/src/screens/InterviewScreen.jsx', 'Step 5: Live interview + M7 + M10 (face/emotion)'),
    ('frontend/src/screens/DashboardScreen.jsx', 'Step 6: Final report with charts and metrics'),
]

for filepath, desc in files:
    if not filepath:
        doc.add_paragraph()
        continue
    p = doc.add_paragraph()
    r1 = p.add_run(filepath)
    r1.bold = True
    r1.font.size = Pt(10)
    r1.font.name = 'Consolas'
    r2 = p.add_run(f' — {desc}')
    r2.font.size = Pt(10)
    r2.font.name = 'Arial'
    p.paragraph_format.space_after = Pt(2)

doc.add_page_break()

# ═══════════════════════════════════════════════════════
# WHAT IS DONE
# ═══════════════════════════════════════════════════════
h1('6. Current Status — What Is Done')

para('Every module listed below is fully implemented and working:')

done_table = doc.add_table(rows=13, cols=3)
done_table.style = 'Light Shading Accent 1'
done_table.rows[0].cells[0].text = 'Module'
done_table.rows[0].cells[1].text = 'Function'
done_table.rows[0].cells[2].text = 'Status'

statuses = [
    ('M1', 'CV Parsing', '✅ Fully Working'),
    ('M2', 'JD Understanding', '✅ Fully Working'),
    ('M3', 'Skill Graph (3 views)', '✅ Fully Working'),
    ('M4', 'Question Generation', '✅ Fully Working'),
    ('M5', 'Voice Interview', '✅ Fully Working'),
    ('M6 Track A', 'LLM-as-Judge Scoring', '✅ Fully Working'),
    ('M6 Track B', 'ML Classifier + SHAP', '✅ Working (heuristic until trained)'),
    ('M7', 'Face Detection / Attention', '✅ Fully Working'),
    ('M9', 'Behavioral Integrity', '✅ Fully Working'),
    ('M10', 'Emotion Detection', '✅ Fully Working'),
    ('M11', 'Fusion Recommendation', '✅ Fully Working'),
    ('M12', 'Dashboard Report', '✅ Fully Working'),
]
for i, (mod, func, status) in enumerate(statuses, 1):
    done_table.rows[i].cells[0].text = mod
    done_table.rows[i].cells[1].text = func
    done_table.rows[i].cells[2].text = status

doc.add_paragraph()

h2('What Is Left (ML Work Only)')
para('The only remaining work is machine learning training and dissertation experiments:')
bullet('Train XGBoost model: Run python -m core.evaluator.train_model (5 minutes, needs API key)')
bullet('Run comparison experiments: Compare Track A vs Track B, compute Cohen\'s Kappa')
bullet('Collect real pilot data: Do a few test interviews, use data to improve Isolation Forest')
bullet('M8 Posture Analysis: Optional module (proposal says it can be descoped)')
bullet('Write dissertation chapters using experimental results')

doc.add_page_break()

# ═══════════════════════════════════════════════════════
# API ENDPOINTS
# ═══════════════════════════════════════════════════════
h1('7. API Endpoints')

para('These are all the API routes the server exposes:')

api_tbl = doc.add_table(rows=15, cols=3)
api_tbl.style = 'Light Shading Accent 1'
api_tbl.rows[0].cells[0].text = 'Endpoint'
api_tbl.rows[0].cells[1].text = 'Method'
api_tbl.rows[0].cells[2].text = 'What It Does'

apis = [
    ('/api/parse-cv', 'POST', 'Upload CV file, get structured data back'),
    ('/api/parse-jd', 'POST', 'Send JD text, get extracted requirements'),
    ('/api/build-graph', 'POST', 'Build skill graph from CV + JD data'),
    ('/api/generate-questions', 'POST', 'Generate interview questions from graph'),
    ('/api/launch-interview', 'POST', 'Start the voice interview session'),
    ('/api/stop-interview', 'POST', 'Stop the voice interview'),
    ('/api/evaluate', 'POST', 'Evaluate one answer (dual-track scoring)'),
    ('/api/integrity', 'POST', 'Run behavioral integrity assessment'),
    ('/api/fusion-report', 'POST', 'Generate weighted final recommendation'),
    ('/api/transcript', 'GET', 'Get the interview transcript'),
    ('/api/session', 'GET', 'Get current session state'),
    ('/api/health', 'GET', 'Health check — is server running?'),
    ('/token', 'GET', 'Get LiveKit token + start agent process'),
    ('/save_transcript', 'POST', 'Save transcript from frontend'),
]
for i, (ep, method, desc) in enumerate(apis, 1):
    api_tbl.rows[i].cells[0].text = ep
    api_tbl.rows[i].cells[1].text = method
    api_tbl.rows[i].cells[2].text = desc

# ═══════════════════════════════════════════════════════
# SAVE
# ═══════════════════════════════════════════════════════
out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'PROJECT_DOCS.docx')
doc.save(out_path)
print(f'Generated: {out_path}')
