"""M6b: Graph traversal strategies for adaptive interview flow.

Strategies:
  - adaptive:  reorder remaining skills by score + priority (lowest first)
  - bfs:       breadth-first (cover categories in parallel)
  - dfs:       depth-first (deep-dive one category at a time)
  - spaced:    spaced repetition — re-ask weak skills at intervals
"""

import random
from typing import Optional

from core.graph.state import InterviewState


def pick_next_skill(
    state: InterviewState,
    strategy: str = "adaptive",
    last_skill: Optional[str] = None,
) -> Optional[str]:
    incomplete = state.incomplete_skills
    if not incomplete:
        return None

    if strategy == "adaptive":
        return _adaptive_pick(state, incomplete, last_skill)
    elif strategy == "bfs":
        return _bfs_pick(state, incomplete)
    elif strategy == "dfs":
        return _dfs_pick(state, incomplete, last_skill)
    elif strategy == "spaced":
        return _spaced_pick(state, incomplete)
    else:
        return _adaptive_pick(state, incomplete, last_skill)


def _adaptive_pick(
    state: InterviewState,
    incomplete: list,
    last_skill: Optional[str] = None,
) -> str:
    """Pick the lowest-scored skill first, but avoid repeating the same skill."""
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


def _bfs_pick(state: InterviewState, incomplete: list) -> str:
    """Pick the first incomplete skill; simple round-robin style."""
    return incomplete[0]


def _dfs_pick(
    state: InterviewState,
    incomplete: list,
    last_skill: Optional[str] = None,
) -> str:
    """Stick with the same skill until verified, then move on."""
    if last_skill and last_skill in incomplete:
        return last_skill
    return _bfs_pick(state, incomplete)


def _spaced_pick(
    state: InterviewState,
    incomplete: list,
) -> str:
    """Prefer skills with fewer questions asked so far (spaced repetition)."""
    scored = [(state.get_node(s).questions_asked, s) for s in incomplete]
    scored.sort(key=lambda x: x[0])
    return scored[0][1]


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
