"""M6b: Graph traversal — chooses next skill during interview.

Strategy: adaptive — picks the lowest-scored incomplete skill first,
avoiding repeating the same skill consecutively.
"""

from typing import Optional

from core.graph.state import InterviewState


def pick_next_skill(
    state: InterviewState,
    last_skill: Optional[str] = None,
) -> Optional[str]:
    incomplete = state.incomplete_skills
    if not incomplete:
        return None

    scored = []
    for skill in incomplete:
        node = state.get_node(skill)
        avg = node.avg_score if node else 0
        priority_weight = {"high": 0, "medium": 1, "low": 2}.get(
            getattr(node, "priority", "medium"), 1
        )
        scored.append((avg, priority_weight, 0 if skill != last_skill else 1, skill))

    scored.sort(key=lambda x: (x[0], x[1], x[2]))
    return scored[0][3]


def decide_follow_up(
    state: InterviewState,
    skill: str,
    score: float,
) -> bool:
    """Decide if a follow-up question is warranted based on score."""
    node = state.get_node(skill)
    if not node:
        return False

    from core.config import SCORE_STRONG_THRESHOLD, SCORE_WEAK_THRESHOLD, MAX_FOLLOW_UP_QUESTIONS

    if node.questions_asked >= MAX_FOLLOW_UP_QUESTIONS + 1:
        return False

    if score >= SCORE_STRONG_THRESHOLD:
        return False

    if score < SCORE_WEAK_THRESHOLD:
        return True

    if SCORE_WEAK_THRESHOLD <= score < SCORE_STRONG_THRESHOLD:
        return node.questions_asked < 2

    return False
