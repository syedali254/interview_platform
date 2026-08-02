"""Text interview mode — the typed equivalent of the live voice interview.

Same interviewer, same question bank, same budgets, same ending rules. The
only difference is the transport: instead of LiveKit carrying speech both
ways, the browser posts an answer and gets the next question back.

The transcript this produces is byte-for-byte the same shape the voice agent
saves, so /api/evaluate-session scores a typed interview exactly as it scores
a spoken one — no branching in the evaluation pipeline at all.
"""

import time
from datetime import datetime

from core.agents.interviewer_prompt import build_system_prompt
from core.llm import call_llm

# Marker the interviewer emits to signal it is finished. Stripped before the
# closing line is shown to the candidate.
END_MARKER = "[[END_INTERVIEW]]"

# How much of the conversation to replay to the model each turn. Long enough
# to stay coherent, short enough to keep latency and cost sane.
HISTORY_TURNS = 24


class TextInterview:
    """Drives one typed interview from greeting to closing statement."""

    def __init__(self, cv_data: dict, jd_data: dict, seed_questions: list,
                 max_questions: int = 15, min_questions: int = 5,
                 time_budget_mins: int = 30):
        self.cv_data = cv_data or {}
        self.jd_data = jd_data or {}
        self.seed_questions = seed_questions or []
        self.max_questions = max_questions
        # The floor must never sit above the ceiling, or a short demo run
        # configured with max_questions=3 would never reach its own limit.
        self.min_questions = min(min_questions, max_questions)
        self.time_budget_mins = time_budget_mins

        self.system_prompt = build_system_prompt(
            self.cv_data, self.jd_data, self.seed_questions, mode="text"
        )
        self.transcript: list[dict] = []
        self.started_at = time.time()
        self.q_count = 0
        self.turn_count = 0
        self.finished = False
        self.end_reason: str | None = None
        self._wrap_up_requested = False

    # ── Timing and budget ─────────────────────────────────────────────

    @property
    def elapsed_seconds(self) -> float:
        return time.time() - self.started_at

    @property
    def elapsed_mins(self) -> float:
        return self.elapsed_seconds / 60

    def _budget_spent(self) -> bool:
        if self.q_count < self.min_questions:
            return False
        return (self.q_count >= self.max_questions
                or self.elapsed_mins >= self.time_budget_mins)

    # ── Conversation ──────────────────────────────────────────────────

    def _render_history(self) -> str:
        recent = self.transcript[-HISTORY_TURNS:]
        lines = []
        for msg in recent:
            who = "Interviewer" if msg["role"] == "agent" else "Candidate"
            lines.append(f"{who}: {msg['text']}")
        return "\n".join(lines)

    def _ask_model(self, directive: str) -> str:
        prompt = (
            f"{self.system_prompt}\n\n"
            f"CONVERSATION SO FAR:\n{self._render_history() or '(nothing yet)'}\n\n"
            f"INSTRUCTION: {directive}\n\n"
            f"When the rules say the interview should end, append {END_MARKER} "
            f"to the very end of your reply, after your closing sentence.\n\n"
            "Write only the interviewer's next message, with no name prefix "
            "and no quotation marks."
        )
        return call_llm(prompt, temperature=0.5).strip()

    def _record_agent(self, text: str) -> dict:
        self.turn_count += 1
        if "?" in text:
            self.q_count += 1
        entry = {
            "role": "agent",
            "text": text,
            "time": int(self.elapsed_seconds),
        }
        self.transcript.append(entry)
        return entry

    def _emit(self, raw: str) -> dict:
        """Clean the model's reply, record it, and report interview state."""
        finished = END_MARKER in raw
        text = raw.replace(END_MARKER, "").strip()

        if not text:
            text = ("Thank you for your time. Your evaluation report will be "
                    "ready shortly.")

        self._record_agent(text)

        if finished:
            self.finished = True
            self.end_reason = self.end_reason or (
                "question limit" if self._wrap_up_requested else "completed"
            )

        return {
            "message": text,
            "finished": self.finished,
            "end_reason": self.end_reason,
            "q_count": self.q_count,
            "turn_count": self.turn_count,
            "max_questions": self.max_questions,
            "elapsed_mins": round(self.elapsed_mins, 1),
        }

    # ── Public API ────────────────────────────────────────────────────

    def start(self) -> dict:
        """Produce the opening greeting."""
        # The clock starts when the candidate actually sees the greeting.
        self.started_at = time.time()
        return self._emit(self._ask_model(
            "Greet the candidate and open the interview."
        ))

    def submit(self, answer: str) -> dict:
        """Record a typed answer and return the interviewer's next message."""
        if self.finished:
            return {
                "message": "The interview has already ended.",
                "finished": True,
                "end_reason": self.end_reason,
                "q_count": self.q_count,
                "turn_count": self.turn_count,
                "max_questions": self.max_questions,
                "elapsed_mins": round(self.elapsed_mins, 1),
            }

        text = (answer or "").strip()
        if text:
            self.transcript.append({
                "role": "candidate",
                "text": text,
                "time": int(self.elapsed_seconds),
            })

        if self._budget_spent():
            self._wrap_up_requested = True
            directive = (
                "The interview has reached its limit. Give one short closing "
                "statement thanking the candidate by name and telling them "
                f"their report will be ready shortly, then append {END_MARKER}. "
                "Do not ask any further questions."
            )
        else:
            directive = (
                "Respond to the candidate's latest answer and ask your next "
                "question, following your approach and ending rules."
            )

        return self._emit(self._ask_model(directive))

    def end_now(self, reason: str = "candidate_request") -> dict:
        """Close the interview immediately, at the candidate's request."""
        if self.finished:
            return {"message": "", "finished": True, "end_reason": self.end_reason}
        self.finished = True
        self.end_reason = reason
        closing = ("Thank you for your time. Your evaluation report will be "
                   "ready shortly.")
        self._record_agent(closing)
        return {
            "message": closing,
            "finished": True,
            "end_reason": reason,
            "q_count": self.q_count,
            "turn_count": self.turn_count,
            "max_questions": self.max_questions,
            "elapsed_mins": round(self.elapsed_mins, 1),
        }

    def to_session_record(self) -> dict:
        """The same record the voice agent writes when it disconnects."""
        return {
            "session": f"text-{int(self.started_at)}",
            "mode": "text",
            "completed": True,
            "end_reason": self.end_reason or "disconnected",
            "questions_count": self.q_count,
            "turns_count": self.turn_count,
            "elapsed_mins": round(self.elapsed_mins, 1),
            "conversation": self.transcript,
            "generated_at": datetime.now().isoformat(),
            "config": {
                "max_questions": self.max_questions,
                "min_questions": self.min_questions,
                "time_budget_mins": self.time_budget_mins,
            },
        }
