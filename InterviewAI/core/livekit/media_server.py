"""Manages LiveKit processes — auto-downloads server binary if missing."""

import os
import time
import subprocess
import tempfile
import socket
import platform
import urllib.request
import urllib.error
from pathlib import Path
import atexit

# The asset names on the releases page are livekit_<version>_<os>_<arch>.<ext>
# — not livekit-server_<os>_<arch>, which is what this module used to build and
# which 404s on every platform. It went unnoticed because a binary downloaded
# by hand was already sitting in the temp directory on the development machine.
LIVEKIT_VERSION = os.environ.get("LIVEKIT_VERSION", "1.13.5")

HERE = Path(__file__).resolve().parent
BASE = HERE.parent.parent

_system = platform.system().lower()
_machine = platform.machine().lower()

# LiveKit publishes Windows as .zip and Linux as .tar.gz. There is no macOS
# build on the releases page at all, so darwin is steered to Homebrew rather
# than sent to a URL that cannot exist.
_arch = {"amd64": "amd64", "x86_64": "amd64", "arm64": "arm64",
         "aarch64": "arm64", "armv7l": "armv7"}.get(_machine, "amd64")

if _system == "windows":
    _bin_name = "livekit-server.exe"
    _asset = f"livekit_{LIVEKIT_VERSION}_windows_{_arch}.zip"
elif _system == "linux":
    _bin_name = "livekit-server"
    _asset = f"livekit_{LIVEKIT_VERSION}_linux_{_arch}.tar.gz"
else:
    _bin_name = "livekit-server"
    _asset = None

LIVEKIT_BIN = Path(tempfile.gettempdir()) / "livekit" / _bin_name
LIVEKIT_CONFIG = HERE / "livekit.yaml"
LIVEKIT_DL_URL = (
    f"https://github.com/livekit/livekit/releases/download/v{LIVEKIT_VERSION}/{_asset}"
) if _asset else None

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


def _extract_binary(data: bytes) -> bool:
    """Pull livekit-server out of the downloaded archive.

    Both archive types contain the executable at the top level alongside a
    licence and a readme, so the member is chosen by name rather than position.
    """
    import io

    try:
        if _asset.endswith(".zip"):
            import zipfile
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                names = [n for n in zf.namelist()
                         if Path(n).name.lower() in ("livekit-server.exe", "livekit-server")]
                if not names:
                    log(f"No livekit-server in the archive. Contents: {zf.namelist()}")
                    return False
                LIVEKIT_BIN.write_bytes(zf.read(names[0]))
                log(f"Extracted {names[0]} -> {LIVEKIT_BIN}")
        else:
            import tarfile
            with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
                members = [m for m in tar.getmembers()
                           if m.isfile() and Path(m.name).name == "livekit-server"]
                if not members:
                    log(f"No livekit-server in the archive. Contents: "
                        f"{[m.name for m in tar.getmembers()]}")
                    return False
                with tar.extractfile(members[0]) as f:
                    LIVEKIT_BIN.write_bytes(f.read())
                log(f"Extracted {members[0].name} -> {LIVEKIT_BIN}")
        LIVEKIT_BIN.chmod(0o755)
        return True
    except Exception as e:
        log(f"Extraction failed: {type(e).__name__}: {e}")
        return False


def _download_livekit() -> bool:
    """Download and unpack the LiveKit server binary from GitHub releases."""
    if not LIVEKIT_DL_URL:
        if _system == "darwin":
            log("LiveKit publishes no macOS build. Install it with: brew install livekit")
        else:
            log(f"Unsupported platform: {_system} {_machine}")
        return False

    LIVEKIT_BIN.parent.mkdir(parents=True, exist_ok=True)

    log(f"Downloading LiveKit server v{LIVEKIT_VERSION} for {_system} {_arch}...")
    log(f"URL: {LIVEKIT_DL_URL}")

    try:
        req = urllib.request.Request(
            LIVEKIT_DL_URL,
            headers={"User-Agent": "InterviewAI/1.0"},
        )
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = resp.read()
    except urllib.error.HTTPError as e:
        # A 404 here means the version or the asset naming has moved on, which
        # is worth saying plainly — it is not a network problem.
        log(f"Download failed: HTTP {e.code}. The release asset may have been "
            f"renamed or removed.")
        log(f"Check https://github.com/livekit/livekit/releases and set "
            f"LIVEKIT_VERSION in .env to a version listed there.")
        return False
    except Exception as e:
        log(f"Download failed: {type(e).__name__}: {e}")
        return False

    log(f"Downloaded {len(data) / 1048576:.1f} MB, unpacking...")
    return _extract_binary(data)


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
            log("Auto-download failed. To fix it by hand:")
            log(f"  1. Download {LIVEKIT_DL_URL}")
            log(f"  2. Unzip it and put livekit-server.exe at {LIVEKIT_BIN}")
            log("Text-mode interviews still work without this — only the "
                "voice interview needs a media server.")
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