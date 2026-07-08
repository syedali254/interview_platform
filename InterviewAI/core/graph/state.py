"""M6a: Live interview graph state tracker.

Tracks per-skill status through the interview lifecycle:
  pending -> verified_strong / verified_weak / confirmed_gap / skipped

Provides the dynamic graph that traversal.py reads to choose next questions.
"""

from dataclasses import dataclass, field
from typing import Optional

from core.config import (
    STATUS_PENDING,
    STATUS_VERIFIED_STRONG,
    STATUS_VERIFIED_WEAK,
    STATUS_CONFIRMED_GAP,
    STATUS_SKIPPED,
    SCORE_STRONG_THRESHOLD,
    SCORE_WEAK_THRESHOLD,
    SKILL_VERIFICATION_QUESTIONS,
)


@dataclass
class SkillNodeState:
    skill: str
    status: str = STATUS_PENDING
    scores: list = field(default_factory=list)
    questions_asked: int = 0
    best_score: float = 0.0
    last_question: Optional[str] = None
    feedback: list = field(default_factory=list)

    @property
    def verdict(self) -> str:
        return self.status

    @property
    def avg_score(self) -> float:
        return sum(self.scores) / len(self.scores) if self.scores else 0.0

    def is_verified(self) -> bool:
        return self.status in (STATUS_VERIFIED_STRONG, STATUS_VERIFIED_WEAK, STATUS_CONFIRMED_GAP, STATUS_SKIPPED)

    def needs_more_questions(self) -> bool:
        return self.questions_asked < SKILL_VERIFICATION_QUESTIONS and not self.is_verified()

    def record_answer(self, score: float):
        self.scores.append(score)
        self.questions_asked += 1
        self.best_score = max(self.best_score, score)

        if score >= SCORE_STRONG_THRESHOLD:
            self.status = STATUS_VERIFIED_STRONG
        elif score >= SCORE_WEAK_THRESHOLD:
            if self.questions_asked >= SKILL_VERIFICATION_QUESTIONS:
                self.status = STATUS_VERIFIED_WEAK
            else:
                self.status = STATUS_PENDING
        else:
            if self.questions_asked >= SKILL_VERIFICATION_QUESTIONS:
                self.status = STATUS_CONFIRMED_GAP
            else:
                self.status = STATUS_PENDING

    def skip(self):
        self.status = STATUS_SKIPPED


class InterviewState:
    """Tracks state across all skills during a live interview session."""

    def __init__(self, topics: list):
        self.nodes: dict[str, SkillNodeState] = {}
        for t in topics:
            skill_name = t["skill"]
            self.nodes[skill_name] = SkillNodeState(skill=skill_name)
            self.nodes[skill_name].priority = t.get("priority", "medium")
            self.nodes[skill_name].reason = t.get("reason", "")

    @property
    def pending_skills(self) -> list[str]:
        return [s for s, n in self.nodes.items() if n.status == STATUS_PENDING]

    @property
    def verified_strong_skills(self) -> list[str]:
        return [s for s, n in self.nodes.items() if n.status == STATUS_VERIFIED_STRONG]

    @property
    def verified_weak_skills(self) -> list[str]:
        return [s for s, n in self.nodes.items() if n.status == STATUS_VERIFIED_WEAK]

    @property
    def confirmed_gaps(self) -> list[str]:
        return [s for s, n in self.nodes.items() if n.status == STATUS_CONFIRMED_GAP]

    @property
    def incomplete_skills(self) -> list[str]:
        return [s for s, n in self.nodes.items() if n.needs_more_questions()]

    def get_node(self, skill: str) -> SkillNodeState:
        return self.nodes.get(skill)

    def record_answer(self, skill: str, score: float, feedback: str = ""):
        node = self.nodes.get(skill)
        if node:
            node.record_answer(score)
            if feedback:
                node.feedback.append(feedback)

    def skip_skill(self, skill: str):
        node = self.nodes.get(skill)
        if node:
            node.skip()

    def is_complete(self) -> bool:
        return len(self.incomplete_skills) == 0

    def summary(self) -> dict:
        return {
            "total": len(self.nodes),
            "verified_strong": len(self.verified_strong_skills),
            "verified_weak": len(self.verified_weak_skills),
            "confirmed_gaps": len(self.confirmed_gaps),
            "pending": len(self.pending_skills),
            "skills": {
                s: {
                    "status": n.status,
                    "avg_score": n.avg_score,
                    "best_score": n.best_score,
                    "questions_asked": n.questions_asked,
                }
                for s, n in self.nodes.items()
            },
        }
