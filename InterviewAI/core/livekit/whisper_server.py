import json
import os
import threading
import tempfile
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

_audio_dir = Path(tempfile.gettempdir()) / "interviewai_tts"
_audio_dir.mkdir(exist_ok=True)

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
        if self.path == "/transcribe":
            try:
                length = int(self.headers.get("Content-Length", 0))
                audio_data = self.rfile.read(length)
                from .voice import transcribe_audio
                text = transcribe_audio(audio_data) if audio_data else ""
                self._json_response({"text": text})
            except Exception as e:
                self._json_response({"text": "", "error": str(e)}, 500)
        else:
            self._json_response({"error": "not found"}, 404)

    def do_GET(self):
        if self.path == "/" or self.path == "/client" or self.path == "/livekit":
            self._serve_client()
        elif self.path == "/token":
            self._serve_token()
        elif self.path.startswith("/tts/"):
            filename = self.path[5:]
            filepath = _audio_dir / filename
            if filepath.exists():
                data = filepath.read_bytes()
                self._respond(200, data, {
                    "Content-Type": "audio/mpeg",
                    "Content-Length": str(len(data)),
                })
            else:
                self._respond(404, b"Not found")
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
            from livekit.api import AccessToken

            room_name = f"interview-{uuid.uuid4().hex[:8]}"
            identity = f"candidate-{uuid.uuid4().hex[:6]}"

            token = (
                AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
                .with_identity(identity)
                .with_name("Interview Candidate")
                .with_grants({"room_join": True, "room": room_name})
                .with_room_config(room_name)
                .with_ttl(3600)
                .to_jwt()
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


def start_whisper_server():
    global _server_instance
    if _server_instance is not None:
        return _server_instance
    server = HTTPServer(("localhost", _whisper_server_port), WhisperHTTPHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    _server_instance = server
    # Pre-warm whisper model
    try:
        from .voice import transcribe_audio
        transcribe_audio(b"")
    except Exception:
        pass
    return server


def save_tts_audio(audio_bytes: bytes, filename: str) -> Path:
    fp = _audio_dir / filename
    fp.write_bytes(audio_bytes)
    return fp


def tts_url(filename: str) -> str:
    return f"http://localhost:{_whisper_server_port}/tts/{filename}"


def transcribe_url() -> str:
    return f"http://localhost:{_whisper_server_port}/transcribe"
