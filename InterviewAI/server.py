"""FastAPI backend for the InterviewAI platform.

Pre-interview:
  POST /api/parse-cv           M1 — parse a CV from PDF or text
  POST /api/parse-jd           M2 — parse a job description
  POST /api/build-graph        M3 — map CV + JD onto the ESCO skill graph
  POST /api/generate-questions M4 — generate questions from graph topics

Interview:
  POST /api/launch-interview   M5 — start the LiveKit voice session
  GET  /token                  LiveKit token; also spawns the agent process
  POST /api/stop-interview     tear down the agent and LiveKit server
  POST /save_transcript        transcript written by the client
  GET  /api/transcript         most recent saved transcript

Assessment:
  POST /api/evaluate-session   M6 + M9 + M11 + M12 — score a whole interview
                               and return the final report
  POST /api/evaluate           M6 — score a single answer
  POST /api/integrity          M9 — behavioural integrity for raw telemetry
  POST /api/fusion-report      M11 — weighted fusion for supplied scores

Misc:
  GET  /api/session            current session state
  GET  /api/health             health check
"""

import json
import os
import sys
import subprocess
import tempfile
import uuid
import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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
from core.evaluator.integrity import assess_integrity
from core.evaluator.fusion import compute_fusion_score

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
    "prewarmed_room": None,
    "text_interview": None,
    "report": None,
}

# Currently running agent subprocess (one at a time)
_agent_proc = None


def _save_transcript_record(record: dict):
    """Write a finished interview where /api/transcript can find it."""
    out_dir = Path(tempfile.gettempdir()) / "interviewai_transcripts"
    out_dir.mkdir(exist_ok=True)
    session_id = record.get("session") or f"session-{uuid.uuid4().hex[:8]}"
    (out_dir / f"{session_id}.json").write_text(json.dumps(record, indent=2))


def _prepare_interview_env(max_questions: int = 15, time_budget_mins: int = 30):
    """Populate the environment the agent subprocess reads on startup.

    Questions are flattened in graph-priority order so the skills the graph
    flagged as gaps are asked before the time budget runs out.
    """
    cv_data = _session["cv_data"] or {}
    jd_data = _session["jd_data"] or {}
    questions = _session["questions"] or {}
    topics = (_session["graph_data"] or {}).get("topics", [])

    flow = build_interview_flow(questions, topics)
    q_list = [step["question"] for step in flow if step.get("question")]

    os.environ["MAX_INTERVIEW_QUESTIONS"] = str(max_questions)
    os.environ["INTERVIEW_TIME_BUDGET_MINS"] = str(time_budget_mins)
    os.environ["INTERVIEW_QUESTIONS"] = json.dumps(q_list)
    os.environ["CV_DATA"] = json.dumps(cv_data)
    os.environ["JD_DATA"] = json.dumps(jd_data)
    os.environ["RESUME_TEXT"] = (cv_data.get("full_text") or "")[:3000]
    os.environ["JD_TEXT"] = (jd_data.get("full_text") or "")[:3000]


def _agent_is_alive() -> bool:
    return _agent_proc is not None and _agent_proc.poll() is None


def _spawn_agent(room_name: str):
    """Start the voice agent subprocess for a room, replacing any previous one."""
    global _agent_proc
    _stop_agent_process()

    agent_script = Path(__file__).parent / "core" / "livekit" / "run_agent.py"
    agent_log = Path(__file__).parent / "agent_debug.log"

    env = os.environ.copy()
    env["LIVEKIT_URL"] = os.environ.get("LIVEKIT_URL", "ws://localhost:7880")
    env["LIVEKIT_API_KEY"] = os.environ.get("LIVEKIT_API_KEY", "devkey")
    env["LIVEKIT_API_SECRET"] = os.environ.get("LIVEKIT_API_SECRET", "secret")
    env["PYTHONUNBUFFERED"] = "1"

    log_fh = open(agent_log, "w")
    _agent_proc = subprocess.Popen(
        [sys.executable, "-u", str(agent_script), room_name],
        stdout=log_fh, stderr=subprocess.STDOUT,
        env=env, cwd=str(Path(__file__).parent),
    )
    print(f"[server] Agent process started for room '{room_name}'")


def _stop_agent_process():
    global _agent_proc
    if _agent_proc is not None and _agent_proc.poll() is None:
        try:
            if os.name == "nt":
                # venv python.exe is a redirector: it spawns a child python
                # that does the real work. Terminating only the parent would
                # orphan the child, so kill the whole process tree.
                subprocess.run(
                    ["taskkill", "/PID", str(_agent_proc.pid), "/T", "/F"],
                    capture_output=True, timeout=10,
                )
            else:
                _agent_proc.terminate()
                _agent_proc.wait(timeout=5)
        except Exception:
            try:
                _agent_proc.kill()
            except Exception:
                pass
    _agent_proc = None


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

class TextAnswerInput(BaseModel):
    answer: str

class SessionEvalInput(BaseModel):
    # Role-tagged transcript: [{"role": "agent"|"candidate", "text", "time"}]
    conversation: Optional[list] = None
    # Client-side behavioural telemetry for M9 + M11
    telemetry: Optional[dict] = None


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
        graph = sg.to_graph_payload()

        graph_data = {
            "topics": topics,
            "summary": {
                # Distinct skills in play across CV and JD — matched skills
                # belong to both sides and must not be counted twice.
                "total_skills": graph["total_nodes"],
                "matched": len(gaps["matched_required"]),
                "gaps": len(gaps["missing_required"]),
                "bonus": len(gaps["matched_nice_to_have"]),
                "extra": len(gaps["extra_skills"]),
                "match_percentage": gaps["match_percentage"],
            },
            "gaps": gaps,
            "stats": stats,
            "graph": graph,
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


# ── Pre-warm the media server and the agent process ──
@app.post("/api/prewarm")
async def api_prewarm(config: InterviewConfig = InterviewConfig()):
    """Get everything slow out of the way while the candidate reads the briefing.

    Two things dominate the wait after pressing Begin Interview: booting the
    LiveKit server, and the agent process importing livekit-agents and its
    plugins — around 12 seconds of pure import time. Both are started here,
    on the device-setup screen, so by the time the candidate is ready the
    agent is already connected to the room and waiting for them.
    """
    try:
        from core.livekit.launcher import start_livekit_server
        ok = await run_in_threadpool(start_livekit_server)
        if not ok:
            return {"success": False, "ready": False, "agent_ready": False}

        _session["livekit_launched"] = True
        _session["livekit_url"] = os.environ.get("LIVEKIT_URL", "ws://localhost:7880")

        # The agent can only be started once we know what to ask.
        agent_ready = False
        if _session["questions"] and _session["cv_data"] and _session["jd_data"]:
            _prepare_interview_env(config.max_questions, config.time_budget_mins)
            room_name = f"interview-{uuid.uuid4().hex[:8]}"
            _spawn_agent(room_name)
            _session["prewarmed_room"] = room_name
            agent_ready = True

        return {"success": True, "ready": True, "agent_ready": agent_ready}
    except Exception as e:
        # Never block the setup screen on this — the real launch retries.
        return {"success": False, "ready": False, "detail": str(e)}


# ── Step 4: Launch LiveKit Interview ──
@app.post("/api/launch-interview")
async def api_launch_interview(config: InterviewConfig = InterviewConfig()):
    if not _session["questions"]:
        raise HTTPException(400, "Generate questions first")
    try:
        # Usually a no-op: /api/prewarm did this while the candidate was on
        # the device-setup screen.
        _prepare_interview_env(config.max_questions, config.time_budget_mins)

        from core.livekit.launcher import start_livekit_server
        if not await run_in_threadpool(start_livekit_server):
            raise HTTPException(500, "Failed to start LiveKit server")

        url = os.environ.get("LIVEKIT_URL", "ws://localhost:7880")
        _session["livekit_launched"] = True
        _session["livekit_url"] = url
        return {"success": True, "url": url}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


# ── Text interview mode ──
# The typed equivalent of the voice interview. Same interviewer prompt, same
# budgets, same transcript shape — so /api/evaluate-session scores it with no
# knowledge of which mode produced it.

@app.post("/api/text-interview/start")
async def api_text_start(config: InterviewConfig = InterviewConfig()):
    if not _session["questions"]:
        raise HTTPException(400, "Generate questions first")
    try:
        from core.pipeline.text_interview import TextInterview

        topics = (_session["graph_data"] or {}).get("topics", [])
        flow = build_interview_flow(_session["questions"], topics)
        q_list = [step["question"] for step in flow if step.get("question")]

        interview = TextInterview(
            cv_data=_session["cv_data"],
            jd_data=_session["jd_data"],
            seed_questions=q_list,
            max_questions=config.max_questions,
            min_questions=int(os.environ.get("MIN_INTERVIEW_QUESTIONS", "5")),
            time_budget_mins=config.time_budget_mins,
        )
        _session["text_interview"] = interview
        result = await run_in_threadpool(interview.start)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/api/text-interview/answer")
async def api_text_answer(body: TextAnswerInput):
    interview = _session.get("text_interview")
    if interview is None:
        raise HTTPException(400, "No text interview in progress")
    try:
        result = await run_in_threadpool(interview.submit, body.answer)
        if result.get("finished"):
            _save_transcript_record(interview.to_session_record())
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/api/text-interview/end")
async def api_text_end():
    interview = _session.get("text_interview")
    if interview is None:
        raise HTTPException(400, "No text interview in progress")
    result = interview.end_now("candidate_request")
    _save_transcript_record(interview.to_session_record())
    return {"success": True, "data": result}


# ── Stop Interview ──
@app.post("/api/stop-interview")
async def api_stop_interview():
    from core.livekit.launcher import cleanup
    cleanup()
    _stop_agent_process()
    _session["livekit_launched"] = False
    _session["prewarmed_room"] = None
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


# ── M6 + M9 + M11 + M12: Full post-interview assessment ──
@app.post("/api/evaluate-session")
async def api_evaluate_session(body: SessionEvalInput):
    """Score a completed interview and return the final report.

    Runs the LLM-as-Judge evaluator over every substantive answer, assesses
    behavioural integrity, fuses the results, and assembles the M12 report.
    """
    conversation = body.conversation
    if not conversation:
        # Fall back to the transcript the agent saved on disconnect.
        transcript_dir = Path(tempfile.gettempdir()) / "interviewai_transcripts"
        files = list(transcript_dir.glob("*.json")) if transcript_dir.exists() else []
        if files:
            latest = max(files, key=lambda f: f.stat().st_mtime)
            conversation = json.loads(latest.read_text()).get("conversation", [])

    if not conversation:
        raise HTTPException(400, "No interview transcript available to evaluate")

    try:
        from core.pipeline.session_eval import evaluate_session
        report = await run_in_threadpool(
            evaluate_session,
            conversation=conversation,
            graph_data=_session["graph_data"],
            telemetry=body.telemetry or {},
        )
        _session["report"] = report
        return {"success": True, "data": report}
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
        "report": _session["report"],
    }


# ── LiveKit token endpoint (used by client.html and React frontend) ──
@app.get("/token")
async def get_token():
    from livekit.api import AccessToken, VideoGrants

    LIVEKIT_API_KEY = os.environ.get("LIVEKIT_API_KEY", "devkey")
    LIVEKIT_API_SECRET = os.environ.get("LIVEKIT_API_SECRET", "secret")
    LIVEKIT_WS_URL = os.environ.get("LIVEKIT_URL", "ws://localhost:7880")

    # Reuse the agent started during prewarm if it is still alive — it has
    # already paid the ~12 second import cost and is sitting in the room
    # waiting. Only spawn a fresh one if prewarm never ran or the process died.
    prewarmed = _session.get("prewarmed_room")
    reused = bool(prewarmed and _agent_is_alive())
    room_name = prewarmed if reused else f"interview-{uuid.uuid4().hex[:8]}"
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

    if reused:
        print(f"[server] Reusing prewarmed agent in room '{room_name}'")
    else:
        _spawn_agent(room_name)

    # One agent serves one interview; clear it so a later run starts fresh.
    _session["prewarmed_room"] = None

    return {
        "token": token,
        "url": LIVEKIT_WS_URL,
        "room": room_name,
        "identity": identity,
        "agent_prewarmed": reused,
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


# ── M9: Behavioral Integrity Assessment ──
@app.post("/api/integrity")
async def api_integrity(data: dict):
    """Assess behavioral integrity of an interview session."""
    try:
        result = assess_integrity(data)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(500, str(e))


# ── M11: Fusion Report ──
@app.post("/api/fusion-report")
async def api_fusion_report(data: dict):
    """Generate weighted fusion report combining all module outputs."""
    try:
        answer_scores = data.get("answer_scores", [])
        skill_match_pct = data.get("skill_match_pct", 0)
        integrity_score = data.get("integrity_score", 100)
        engagement_score = data.get("engagement_score", 75)
        emotion_data = data.get("emotion_data", None)

        result = compute_fusion_score(
            answer_scores=answer_scores,
            skill_match_pct=skill_match_pct,
            integrity_score=integrity_score,
            engagement_score=engagement_score,
            emotion_data=emotion_data,
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(500, str(e))


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
