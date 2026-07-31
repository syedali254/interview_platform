"""FastAPI backend for InterviewAI platform.

Endpoints:
  POST /api/parse-cv         — Upload CV PDF or text, return parsed data
  POST /api/parse-jd         — Parse job description text
  POST /api/build-graph      — Build skill graph from CV + JD data
  POST /api/generate-questions — Generate interview questions from graph topics
  POST /api/launch-interview — Launch LiveKit interview session
  POST /api/stop-interview   — Stop LiveKit session
  GET  /api/transcript       — Get latest transcript
  POST /api/evaluate         — Evaluate a single answer
  GET  /api/session          — Get current session state
  GET  /api/health           — Health check
  GET  /token                — LiveKit token (for client)
  POST /save_transcript      — Save transcript from client
"""

import json
import os
import sys
import tempfile
import uuid
import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

from core.config import GEMINI_API_KEY
from core.agents.cv_agent import parse_cv_text, parse_cv_pdf
from core.agents.jd_agent import parse_job_description
from core.agents.question_agent import generate_interview_questions, build_interview_flow
from core.graph.skill_graph import build_graph
from core.evaluator.evaluator import evaluate_answer

app = FastAPI(title="InterviewAI API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── In-memory session store (single-user dissertation demo) ──
_session = {
    "cv_data": None,
    "jd_data": None,
    "graph_data": None,
    "questions": None,
    "livekit_launched": False,
    "livekit_url": None,
}


# ── Models ──
class JDInput(BaseModel):
    text: str

class EvalInput(BaseModel):
    question: str
    answer: str
    skill: str

class InterviewConfig(BaseModel):
    max_questions: Optional[int] = 15
    time_budget_mins: Optional[int] = 30


# ── Health ──
@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "gemini_configured": bool(GEMINI_API_KEY),
        "session_has_cv": _session["cv_data"] is not None,
        "session_has_jd": _session["jd_data"] is not None,
    }


# ── Step 1: Parse CV ──
@app.post("/api/parse-cv")
async def parse_cv(file: UploadFile = File(None), text: str = Form(None)):
    try:
        if file:
            content = await file.read()
            data = parse_cv_pdf(content)
        elif text:
            data = parse_cv_text(text)
        else:
            raise HTTPException(400, "Provide either a PDF file or text")

        _session["cv_data"] = data
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(500, str(e))


# ── Step 1: Parse JD ──
@app.post("/api/parse-jd")
async def parse_jd(body: JDInput):
    try:
        data = parse_job_description(body.text)
        data["full_text"] = body.text
        _session["jd_data"] = data
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(500, str(e))


# ── Step 2: Build Graph ──
@app.post("/api/build-graph")
async def api_build_graph():
    if not _session["cv_data"] or not _session["jd_data"]:
        raise HTTPException(400, "Parse CV and JD first")
    try:
        cv = _session["cv_data"]
        jd = _session["jd_data"]
        sg = build_graph(cv, jd)

        # Serialize SkillGraph to JSON-friendly dict
        topics = sg.get_interview_topics()
        gaps = sg.analyse_gaps()
        stats = sg.get_stats()

        graph_data = {
            "topics": topics,
            "summary": {
                "total_skills": stats["candidate_skills"] + stats["job_required"],
                "matched": len(gaps["matched_required"]),
                "gaps": len(gaps["missing_required"]),
                "match_percentage": gaps["match_percentage"],
            },
            "gaps": gaps,
            "stats": stats,
        }

        _session["graph_data"] = graph_data
        return {"success": True, "data": graph_data}
    except Exception as e:
        raise HTTPException(500, str(e))


# ── Step 3: Generate Questions ──
@app.post("/api/generate-questions")
async def api_generate_questions():
    if not _session["graph_data"]:
        raise HTTPException(400, "Build graph first")
    try:
        topics = _session["graph_data"]["topics"]
        cv = _session["cv_data"]
        jd = _session["jd_data"]
        questions = generate_interview_questions(topics, cv, jd)
        _session["questions"] = questions
        return {"success": True, "data": questions}
    except Exception as e:
        raise HTTPException(500, str(e))


# ── Step 4: Launch LiveKit Interview ──
@app.post("/api/launch-interview")
async def api_launch_interview(config: InterviewConfig = InterviewConfig()):
    if not _session["questions"]:
        raise HTTPException(400, "Generate questions first")
    try:
        cv_data = _session["cv_data"]
        jd_data = _session["jd_data"]
        questions = _session["questions"]

        # Collect all questions as seed
        q_list = []
        for section in ("opening", "technical", "behavioural", "closing"):
            for q in questions.get(section, []):
                q_list.append(q.get("question", ""))

        # Set env vars for interview config
        os.environ["MAX_INTERVIEW_QUESTIONS"] = str(config.max_questions)
        os.environ["INTERVIEW_TIME_BUDGET_MINS"] = str(config.time_budget_mins)

        from core.livekit.launcher import launch
        url = launch(
            resume_text=cv_data.get("full_text", ""),
            jd_text=jd_data.get("full_text", ""),
            questions=q_list or None,
            cv_data=cv_data,
            jd_data=jd_data,
        )
        if url:
            _session["livekit_launched"] = True
            _session["livekit_url"] = url
            return {"success": True, "url": url}
        else:
            raise HTTPException(500, "Failed to start LiveKit server")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


# ── Stop Interview ──
@app.post("/api/stop-interview")
async def api_stop_interview():
    from core.livekit.launcher import cleanup
    cleanup()
    _session["livekit_launched"] = False
    return {"success": True}


# ── Get Transcript ──
@app.get("/api/transcript")
async def api_get_transcript():
    transcript_dir = Path(tempfile.gettempdir()) / "interviewai_transcripts"
    if not transcript_dir.exists():
        return {"found": False, "data": None}
    files = list(transcript_dir.glob("*.json"))
    if not files:
        return {"found": False, "data": None}
    latest = max(files, key=lambda f: f.stat().st_mtime)
    data = json.loads(latest.read_text())
    return {"found": True, "data": data}


# ── Evaluate Answer ──
@app.post("/api/evaluate")
async def api_evaluate(body: EvalInput):
    try:
        result = evaluate_answer(body.question, body.answer, body.skill)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(500, str(e))


# ── Get Session State ──
@app.get("/api/session")
async def api_session():
    return {
        "cv_parsed": _session["cv_data"] is not None,
        "jd_parsed": _session["jd_data"] is not None,
        "graph_built": _session["graph_data"] is not None,
        "questions_generated": _session["questions"] is not None,
        "interview_launched": _session["livekit_launched"],
        "interview_url": _session["livekit_url"],
        "cv_data": _session["cv_data"],
        "jd_data": _session["jd_data"],
        "graph_data": _session["graph_data"],
        "questions": _session["questions"],
    }


# ── LiveKit token endpoint (used by client.html and React frontend) ──
@app.get("/token")
async def get_token():
    from livekit.api import AccessToken, VideoGrants
    import subprocess

    LIVEKIT_API_KEY = os.environ.get("LIVEKIT_API_KEY", "devkey")
    LIVEKIT_API_SECRET = os.environ.get("LIVEKIT_API_SECRET", "secret")
    LIVEKIT_WS_URL = os.environ.get("LIVEKIT_URL", "ws://localhost:7880")

    room_name = f"interview-{uuid.uuid4().hex[:8]}"
    identity = f"candidate-{uuid.uuid4().hex[:6]}"

    grants = VideoGrants(
        room_join=True, room=room_name,
        can_publish=True, can_subscribe=True, can_publish_data=True,
    )
    token = (
        AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        .with_identity(identity)
        .with_name("Interview Candidate")
        .with_grants(grants)
        .with_ttl(datetime.timedelta(hours=1))
        .to_jwt()
    )

    # Start agent subprocess
    agent_script = Path(__file__).parent / "core" / "livekit" / "run_agent.py"
    agent_log = Path(__file__).parent / "agent_debug.log"
    env = os.environ.copy()
    env["LIVEKIT_URL"] = LIVEKIT_WS_URL
    env["LIVEKIT_API_KEY"] = LIVEKIT_API_KEY
    env["LIVEKIT_API_SECRET"] = LIVEKIT_API_SECRET
    env["PYTHONUNBUFFERED"] = "1"
    for env_key in ("INTERVIEW_QUESTIONS", "CV_DATA", "JD_DATA",
                    "MAX_INTERVIEW_QUESTIONS", "MIN_INTERVIEW_QUESTIONS",
                    "INTERVIEW_TIME_BUDGET_MINS"):
        if env_key in os.environ:
            env[env_key] = os.environ[env_key]

    log_fh = open(agent_log, "w")
    subprocess.Popen(
        [sys.executable, "-u", str(agent_script), room_name],
        stdout=log_fh, stderr=subprocess.STDOUT,
        env=env, cwd=str(Path(__file__).parent),
    )

    return {
        "token": token,
        "url": LIVEKIT_WS_URL,
        "room": room_name,
        "identity": identity,
    }


# ── Save transcript from client ──
@app.post("/save_transcript")
async def save_transcript_endpoint(data: dict):
    transcript_dir = Path(tempfile.gettempdir()) / "interviewai_transcripts"
    transcript_dir.mkdir(exist_ok=True)
    session_id = data.get("session", f"client-{uuid.uuid4().hex[:8]}")
    fp = transcript_dir / f"{session_id}.json"
    fp.write_text(json.dumps(data, indent=2))
    return {"saved": True, "path": str(fp)}


# ── Serve React frontend (production) ──
_frontend_dist = Path(__file__).parent / "frontend" / "dist"
if _frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(_frontend_dist / "assets")), name="assets")

    @app.get("/{path:path}")
    async def serve_spa(path: str):
        # Try to serve static file first
        file_path = _frontend_dist / path
        if file_path.is_file():
            return FileResponse(file_path)
        # Fall back to index.html for SPA routing
        return FileResponse(_frontend_dist / "index.html")
else:
    @app.get("/")
    async def root():
        return {"message": "InterviewAI API running. Build frontend with: cd frontend && npm run build"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
