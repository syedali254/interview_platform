"""Graph traversal rules over the live skill state.

Used after the interview to identify skills whose evidence was too thin to
support a confident verdict — the ones that warranted another question.
"""

from core.graph.state import InterviewState


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
