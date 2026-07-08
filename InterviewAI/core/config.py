"""Configuration — loads environment variables."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)

# ---------------------------------------------------------------------------
# Gemini (fallback to Ollama if key missing)
# ---------------------------------------------------------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

if GEMINI_API_KEY:
    GEMINI_ENDPOINT = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    )
else:
    GEMINI_ENDPOINT = ""
    print("[INFO] GEMINI_API_KEY not set — using Ollama for LLM.")

# ---------------------------------------------------------------------------
# Ollama (local, no API key needed)
# ---------------------------------------------------------------------------
OLLAMA_ENDPOINT = os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b-instruct")
LLM_TEMPERATURE = 0.3
LLM_MAX_TOKENS = 8192
LLM_MAX_RETRIES = 2

# ---------------------------------------------------------------------------
# LLM provider selection
# ---------------------------------------------------------------------------
LLM_PROVIDER = "ollama" if not GEMINI_API_KEY else os.getenv("LLM_PROVIDER", "gemini")

# ---------------------------------------------------------------------------
# Scoring thresholds
# ---------------------------------------------------------------------------
SCORE_STRONG_THRESHOLD = 70
SCORE_WEAK_THRESHOLD = 40

# ---------------------------------------------------------------------------
# Interview settings
# ---------------------------------------------------------------------------
MAX_QUESTIONS_PER_SESSION = 12
MAX_FOLLOW_UP_QUESTIONS = 1
DISAGREEMENT_THRESHOLD = 20
SKILL_VERIFICATION_QUESTIONS = 3

# ---------------------------------------------------------------------------
# Track weighting for final score fusion
# ---------------------------------------------------------------------------
TRACK_A_WEIGHT = 0.6
TRACK_B_WEIGHT = 0.4

# ---------------------------------------------------------------------------
# LiveKit (self-hosted, free)
# ---------------------------------------------------------------------------
LIVEKIT_URL = os.getenv("LIVEKIT_URL", "ws://localhost:7880")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY", "devkey")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", "devsecret")
LIVEKIT_ROOM_NAME = os.getenv("LIVEKIT_ROOM_NAME", "interview-room")

# ---------------------------------------------------------------------------
# Graph state statuses for live interview
# ---------------------------------------------------------------------------
STATUS_PENDING = "pending"
STATUS_VERIFIED_STRONG = "verified_strong"
STATUS_VERIFIED_WEAK = "verified_weak"
STATUS_CONFIRMED_GAP = "confirmed_gap"
STATUS_SKIPPED = "skipped"
