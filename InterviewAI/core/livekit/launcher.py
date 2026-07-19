"""Manages LiveKit processes for integration with Streamlit Step 6."""

import json
import os
import sys
import time
import subprocess
import tempfile
import socket
from pathlib import Path
import atexit

HERE = Path(__file__).resolve().parent
BASE = HERE.parent.parent
LIVEKIT_BIN = Path(tempfile.gettempdir()) / "livekit" / "livekit-server.exe"
LIVEKIT_CONFIG = HERE / "livekit.yaml"

_processes: list[subprocess.Popen] = []


def log(msg):
    print(f"[LiveKit-Launcher] {msg}")


def _port_open(port: int) -> bool:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        s.connect(("127.0.0.1", port))
        s.close()
        return True
    except:
        return False


def start_livekit_server() -> bool:
    if _port_open(7880):
        log("LiveKit server already running")
        return True
    if not LIVEKIT_BIN.exists():
        log(f"LiveKit binary not found at {LIVEKIT_BIN}")
        log("Download from https://github.com/livekit/livekit/releases")
        return False
    log("Starting LiveKit server...")
    proc = subprocess.Popen(
        [str(LIVEKIT_BIN), "--config", str(LIVEKIT_CONFIG)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    _processes.append(proc)
    for _ in range(10):
        time.sleep(1)
        if _port_open(7880):
            log("LiveKit server started")
            return True
    log("LiveKit server failed to start")
    return False


def start_web_server():
    """Start the mini web server (tokens + client page + whisper STT)."""
    log("Starting/restarting web server...")
    from core.livekit.whisper_server import start_whisper_server
    start_whisper_server(force_restart=True)
    time.sleep(1)
    log("Web server running on http://localhost:18765")
    return True


def launch(resume_text="", jd_text="", questions=None):
    """Launch all LiveKit services and return the client URL.
    
    Args:
        resume_text: candidate resume text
        jd_text: job description text
        questions: list of question strings (max 5) from Step 4
    """
    os.environ["RESUME_TEXT"] = (resume_text or "")[:3000]
    os.environ["JD_TEXT"] = (jd_text or "")[:3000]
    if questions:
        os.environ["INTERVIEW_QUESTIONS"] = json.dumps(questions[:5])

    if not start_livekit_server():
        return None
    if not start_web_server():
        return None
    return "http://localhost:18765/livekit"


def cleanup():
    for proc in _processes:
        if proc.poll() is None:
            try:
                proc.terminate()
                proc.wait(timeout=3)
            except:
                proc.kill()
    _processes.clear()


atexit.register(cleanup)
