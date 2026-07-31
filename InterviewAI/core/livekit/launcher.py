"""Manages LiveKit processes — auto-downloads server binary if missing."""

import json
import os
import sys
import time
import subprocess
import tempfile
import socket
import platform
import urllib.request
import urllib.error
import hashlib
from pathlib import Path
import atexit

LIVEKIT_VERSION = "1.6.1"

HERE = Path(__file__).resolve().parent
BASE = HERE.parent.parent

# Binary path depends on platform
_system = platform.system().lower()
_machine = platform.machine().lower()

if _system == "windows":
    _bin_name = "livekit-server.exe"
    _download_suffix = "windows_amd64.exe"
elif _system == "linux":
    _bin_name = "livekit-server"
    _download_suffix = "linux_amd64.tar.gz"
elif _system == "darwin":
    if _machine in ("arm64", "aarch64"):
        _download_suffix = "darwin_arm64.tar.gz"
    else:
        _download_suffix = "darwin_amd64.tar.gz"
    _bin_name = "livekit-server"
else:
    _download_suffix = None
    _bin_name = "livekit-server"

LIVEKIT_BIN = Path(tempfile.gettempdir()) / "livekit" / _bin_name
LIVEKIT_CONFIG = HERE / "livekit.yaml"
LIVEKIT_DL_URL = (
    f"https://github.com/livekit/livekit/releases/download/v{LIVEKIT_VERSION}/"
    f"livekit-server_{_download_suffix}"
) if _download_suffix else None

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


def _download_livekit() -> bool:
    """Download the LiveKit server binary from GitHub releases."""
    if not LIVEKIT_DL_URL:
        log(f"Unsupported platform: {_system} {_machine}")
        return False

    LIVEKIT_BIN.parent.mkdir(parents=True, exist_ok=True)

    log(f"Downloading LiveKit server v{LIVEKIT_VERSION} for {_system}...")
    log(f"URL: {LIVEKIT_DL_URL}")

    try:
        req = urllib.request.Request(
            LIVEKIT_DL_URL,
            headers={"User-Agent": "InterviewAI/1.0"},
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = resp.read()
    except Exception as e:
        log(f"Download failed: {e}")
        return False

    if _download_suffix.endswith(".tar.gz"):
        import tarfile
        import io
        try:
            with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
                members = tar.getmembers()
                for m in members:
                    if m.name.endswith(_bin_name) or "livekit-server" in m.name and not m.name.endswith(".yaml"):
                        with tar.extractfile(m) as f:
                            bin_data = f.read()
                        LIVEKIT_BIN.write_bytes(bin_data)
                        LIVEKIT_BIN.chmod(0o755)
                        log(f"Extracted {m.name} -> {LIVEKIT_BIN}")
                        return True
                log("Binary not found in archive")
                return False
        except Exception as e:
            log(f"Extraction failed: {e}")
            return False
    else:
        try:
            LIVEKIT_BIN.write_bytes(data)
            LIVEKIT_BIN.chmod(0o755)
            log(f"Saved to {LIVEKIT_BIN}")
            return True
        except Exception as e:
            log(f"Save failed: {e}")
            return False


def start_livekit_server() -> bool:
    if os.environ.get("LIVEKIT_SERVER_EXTERNAL") == "1":
        log("External LiveKit server configured — skipping local start")
        return True

    if _port_open(7880):
        log("LiveKit server already running")
        return True

    if not LIVEKIT_BIN.exists():
        log(f"LiveKit binary not found at {LIVEKIT_BIN}")
        log("Attempting auto-download...")
        if not _download_livekit():
            log("Auto-download failed. Try manually:")
            log(f"  {LIVEKIT_DL_URL}")
            log("  Save to:", LIVEKIT_BIN)
            return False
        log("Download complete.")

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


def launch(resume_text="", jd_text="", questions=None, cv_data=None, jd_data=None):
    os.environ["RESUME_TEXT"] = (resume_text or "")[:3000]
    os.environ["JD_TEXT"] = (jd_text or "")[:3000]
    if questions:
        os.environ["INTERVIEW_QUESTIONS"] = json.dumps(questions)
    if cv_data:
        os.environ["CV_DATA"] = json.dumps(cv_data)
    if jd_data:
        os.environ["JD_DATA"] = json.dumps(jd_data)

    if not start_livekit_server():
        return None
    return "ws://localhost:7880"


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


if __name__ == "__main__":
    url = launch()
    if url:
        print(f"\nInterviewAI LiveKit client: {url}")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")
    else:
        print("\nFailed to start. Check logs above.")
        sys.exit(1)