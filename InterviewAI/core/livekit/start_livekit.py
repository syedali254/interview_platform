"""Launch the full LiveKit voice interview system.

Usage:
  python core/livekit/start_livekit.py

This starts:
  1. LiveKit server (WebRTC signaling)
  2. The voice agent (Deepgram + Gemini + ElevenLabs)
  3. A mini web server for the client page + whisper STT

Environment:
  GEMINI_API_KEY (required)
  DEEPGRAM_API_KEY (required, free at deepgram.com)
  ELEVENLABS_API_KEY (required, free at elevenlabs.io)
  LIVEKIT_URL (optional, default: ws://localhost:7880)
"""

import os
import sys
import subprocess
import time
import webbrowser
import signal
import atexit
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import tempfile

LIVEKIT_BIN = Path(os.environ.get("TEMP", tempfile.gettempdir())) / "livekit" / "livekit-server.exe"
LIVEKIT_CONFIG = Path(__file__).resolve().parent / "livekit.yaml"
AGENT_SCRIPT = Path(__file__).resolve().parent / "run_agent.py"
WHISPER_SERVER_MODULE = "core.livekit.whisper_server"

processes = []


def log(msg):
    print(f"[start_livekit] {msg}")


def start_livekit_server():
    if not LIVEKIT_BIN.exists():
        log(f"ERROR: LiveKit server not found at {LIVEKIT_BIN}")
        log("Download from https://github.com/livekit/livekit/releases")
        sys.exit(1)

    log("Starting LiveKit server...")
    proc = subprocess.Popen(
        [str(LIVEKIT_BIN), "--config", str(LIVEKIT_CONFIG)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    processes.append(proc)
    log(f"LiveKit server PID: {proc.pid}")
    time.sleep(2)
    return proc


def start_agent():
    log("Starting voice agent...")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).resolve().parent.parent.parent)
    proc = subprocess.Popen(
        [sys.executable, str(AGENT_SCRIPT)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
    )
    processes.append(proc)
    log(f"Agent PID: {proc.pid}")
    return proc


def start_web():
    log("Starting web server (whisper + client)...")
    # Import and start the whisper server
    import importlib
    ws = importlib.import_module(WHISPER_SERVER_MODULE)
    ws.start_whisper_server()
    log(f"Web server running on http://localhost:{ws._whisper_server_port}")
    time.sleep(1)
    return ws


def cleanup():
    log("Shutting down...")
    for proc in processes:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()


atexit.register(cleanup)
signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))
signal.signal(signal.SIGTERM, lambda s, f: sys.exit(0))


def main():
    # Check required env
    missing = []
    for key in ["GEMINI_API_KEY"]:
        if not os.environ.get(key):
            missing.append(key)
    if missing:
        log(f"WARNING: Missing env vars: {', '.join(missing)}")
        log("Some features may not work without these.")

    # Start services
    svr = start_livekit_server()
    web = start_web()
    agent = start_agent()

    # Open browser
    port = web._whisper_server_port
    url = f"http://localhost:{port}/livekit"
    log(f"Opening {url} ...")
    webbrowser.open(url)

    log("All services running. Press Ctrl+C to stop.")
    log(f"  LiveKit server  : ws://localhost:7880")
    log(f"  Web client      : {url}")
    log(f"  Agent           : running")

    # Wait forever
    try:
        while True:
            time.sleep(1)
            # Check processes are alive
            for i, proc in enumerate(processes):
                if proc.poll() is not None:
                    log(f"Process {i} exited with code {proc.returncode}")
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()


if __name__ == "__main__":
    main()
