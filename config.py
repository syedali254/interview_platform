"""All configuration values for InterviewIQ. Every module reads from here."""

import os
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Groq API
# ---------------------------------------------------------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY environment variable not set. Please set it before running."
    )

MODEL_NAME = "llama-3.3-70b-versatile"
LLM_TEMPERATURE = 0.3
LLM_MAX_RETRIES = 2
LLM_MAX_TOKENS = 2048

# ---------------------------------------------------------------------------
# Scoring thresholds
# ---------------------------------------------------------------------------
SCORE_STRONG_THRESHOLD = 75
SCORE_WEAK_THRESHOLD = 40

# ---------------------------------------------------------------------------
# Interview settings
# ---------------------------------------------------------------------------
MAX_QUESTIONS_PER_SESSION = 12
MAX_FOLLOW_UP_QUESTIONS = 1
DISAGREEMENT_THRESHOLD = 20

# ---------------------------------------------------------------------------
# Track weighting for final score fusion
# ---------------------------------------------------------------------------
TRACK_A_WEIGHT = 0.6
TRACK_B_WEIGHT = 0.4

SBERT_SIMILARITY_WEIGHT = 0.5
KEYWORD_COVERAGE_WEIGHT = 0.3
SUBSTANCE_RATIO_WEIGHT = 0.2

# ---------------------------------------------------------------------------
# Sentence-BERT
# ---------------------------------------------------------------------------
SBERT_MODEL_NAME = "all-MiniLM-L6-v2"

# ---------------------------------------------------------------------------
# Skill graph
# ---------------------------------------------------------------------------
SKILL_FUZZY_MATCH_THRESHOLD = 0.85

# ---------------------------------------------------------------------------
# Skill node statuses
# ---------------------------------------------------------------------------
STATUS_PENDING = "pending"
STATUS_VERIFIED_STRONG = "verified_strong"
STATUS_VERIFIED_WEAK = "verified_weak"
STATUS_CONFIRMED_GAP = "confirmed_gap"
STATUS_SKIPPED = "skipped"
STATUS_GAP = "gap"
