import json
import os
import subprocess
import sys
import tempfile
import threading
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

_whisper_server_port = 18765
_server_instance = None

_CLIENT_DIR = Path(__file__).resolve().parent

LIVEKIT_API_KEY = os.environ.get("LIVEKIT_API_KEY", "devkey")
LIVEKIT_API_SECRET = os.environ.get("LIVEKIT_API_SECRET", "secret")
LIVEKIT_WS_URL = os.environ.get("LIVEKIT_URL", "ws://localhost:7880")


class WhisperHTTPHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self._respond(200, b"", {"Content-Type": "text/plain"})

    def do_POST(self):
        if self.path == "/save_transcript":
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length)
                data = json.loads(body)
                transcript_dir = Path(tempfile.gettempdir()) / "interviewai_transcripts"
                transcript_dir.mkdir(exist_ok=True)
                session = data.get("session", "unknown")
                fp = transcript_dir / f"{session}.json"
                fp.write_text(json.dumps(data, indent=2))
                self._json_response({"saved": True, "path": str(fp)})
            except Exception as e:
                self._json_response({"saved": False, "error": str(e)}, 500)
        else:
            self._json_response({"error": "not found"}, 404)

    def do_GET(self):
        if self.path == "/" or self.path == "/client" or self.path == "/livekit":
            self._serve_client()
        elif self.path == "/token":
            self._serve_token()
        else:
            self._respond(404, b"Not found")

    def _serve_client(self):
        html_path = _CLIENT_DIR / "client.html"
        if html_path.exists():
            data = html_path.read_bytes()
            self._respond(200, data, {"Content-Type": "text/html; charset=utf-8"})
        else:
            self._respond(404, b"client.html not found")

    def _serve_token(self):
        try:
            import datetime
            from livekit.api import AccessToken, VideoGrants

            room_name = f"interview-{uuid.uuid4().hex[:8]}"
            identity = f"candidate-{uuid.uuid4().hex[:6]}"

            grants = VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True,
            )
            token = (
                AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
                .with_identity(identity)
                .with_name("Interview Candidate")
                .with_grants(grants)
                .with_ttl(datetime.timedelta(hours=1))
                .to_jwt()
            )

            # Start agent subprocess for this room (direct connection, no dispatch)
            agent_script = _CLIENT_DIR / "run_agent.py"
            agent_log = _CLIENT_DIR.parent.parent / "agent_debug.log"
            env = os.environ.copy()
            env["LIVEKIT_URL"] = LIVEKIT_WS_URL
            env["LIVEKIT_API_KEY"] = LIVEKIT_API_KEY
            env["LIVEKIT_API_SECRET"] = LIVEKIT_API_SECRET
            env["PYTHONUNBUFFERED"] = "1"
            # Pass pre-generated questions (set by launcher from Step 4)
            if "INTERVIEW_QUESTIONS" in os.environ:
                env["INTERVIEW_QUESTIONS"] = os.environ["INTERVIEW_QUESTIONS"]
            log_fh = open(agent_log, "w")
            subprocess.Popen(
                [sys.executable, "-u", str(agent_script), room_name],
                stdout=log_fh, stderr=subprocess.STDOUT,
                env=env,
                cwd=str(_CLIENT_DIR.parent.parent),
            )

            self._json_response({
                "token": token,
                "url": LIVEKIT_WS_URL,
                "room": room_name,
                "identity": identity,
            })
        except Exception as e:
            self._json_response({"error": str(e)}, 500)

    def _respond(self, status, body, extra_headers=None):
        self.send_response(status)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        if extra_headers:
            for k, v in extra_headers.items():
                self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _json_response(self, data, status=200):
        body = json.dumps(data).encode()
        self._respond(status, body, {"Content-Type": "application/json", "Content-Length": str(len(body))})

    def log_message(self, fmt, *args):
        pass


def start_whisper_server(force_restart=False):
    global _server_instance
    if _server_instance is not None:
        if not force_restart:
            return _server_instance
        _server_instance.shutdown()
        _server_instance = None
    server = HTTPServer(("localhost", _whisper_server_port), WhisperHTTPHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    _server_instance = server
    return server
