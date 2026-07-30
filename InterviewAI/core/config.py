"""Configuration — loads environment variables."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)

# ---------------------------------------------------------------------------
# Gemini
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
    print("[WARN] GEMINI_API_KEY not set — LLM calls will fail.")

LLM_TEMPERATURE = 0.3
LLM_MAX_TOKENS = 8192

# ---------------------------------------------------------------------------
# Scoring thresholds
# ---------------------------------------------------------------------------
SCORE_STRONG_THRESHOLD = 70
SCORE_WEAK_THRESHOLD = 40

# ---------------------------------------------------------------------------
# Interview settings
# ---------------------------------------------------------------------------
MAX_QUESTIONS_PER_SESSION = 15  # Adaptive: driven by topic coverage, not fixed cap
MAX_FOLLOW_UP_QUESTIONS = 2
SKILL_VERIFICATION_QUESTIONS = 3

# ---------------------------------------------------------------------------
# Graph state statuses for live interview
# ---------------------------------------------------------------------------
STATUS_PENDING = "pending"
STATUS_VERIFIED_STRONG = "verified_strong"
STATUS_VERIFIED_WEAK = "verified_weak"
STATUS_CONFIRMED_GAP = "confirmed_gap"
