"""M7-M10: Live interview pipeline — orchestrates graph state, LLM, evaluator.

The InterviewLoop ties together:
  - M7:  graph state + traversal (adaptive question selection)
  - M8:  question agent (LLM-generated questions per skill)
  - M9:  evaluator (LLM-as-Judge Track A)
  - M10: follow-up decisions
"""

from typing import Optional

from core.graph.state import InterviewState
from core.graph.traversal import pick_next_skill, decide_follow_up
from core.evaluator.evaluator import evaluate_answer
from core.agents.question_agent import generate_position_question
from core.config import MAX_QUESTIONS_PER_SESSION


class InterviewLoop:
    def __init__(self, topics: list, cv_data: dict, jd_data: dict):
        self.state = InterviewState(topics)
        self.cv_data = cv_data
        self.jd_data = jd_data
        self.last_skill: Optional[str] = None
        self.question_history: list = []
        self.answer_history: list = []
        self.total_questions_asked = 0

    @property
    def is_complete(self) -> bool:
        return (
            self.state.is_complete()
            or self.total_questions_asked >= MAX_QUESTIONS_PER_SESSION
        )

    def get_next_question(self) -> Optional[dict]:
        if self.is_complete:
            return None

        skill = pick_next_skill(self.state, strategy="adaptive", last_skill=self.last_skill)
        if not skill:
            return None

        self.last_skill = skill
        node = self.state.get_node(skill)

        # Determine difficulty based on current score
        difficulty = "medium"
        if node and node.best_score < 40:
            difficulty = "easy"
        elif node and node.best_score > 75:
            difficulty = "hard"

        question_text = generate_position_question(
            skill=skill,
            difficulty=difficulty,
            cv_data=self.cv_data,
            jd_data=self.jd_data,
            is_follow_up=(node.questions_asked > 0) if node else False,
        )

        q_data = {
            "skill": skill,
            "question": question_text,
            "difficulty": difficulty,
            "question_number": self.total_questions_asked + 1,
            "is_follow_up": (node.questions_asked > 0) if node else False,
        }

        self.question_history.append(q_data)
        self.total_questions_asked += 1
        return q_data

    def submit_answer(self, question: dict, answer_text: str) -> dict:
        skill = question["skill"]
        result = evaluate_answer(
            question=question["question"],
            candidate_answer=answer_text,
            skill=skill,
        )

        score = result["final_score"]
        self.state.record_answer(skill, score, feedback=result.get("track_a", {}).get("feedback", ""))

        need_follow_up = decide_follow_up(self.state, skill, score)

        self.answer_history.append({
            "question": question["question"],
            "answer": answer_text,
            "skill": skill,
            "score": score,
            "verdict": result["verdict"],
            "reference_answer": result["reference_answer"],
            "track_a": result["track_a"],
        })

        return {
            "score": score,
            "verdict": result["verdict"],
            "feedback": result.get("track_a", {}).get("feedback", ""),
            "reference_answer": result["reference_answer"],
            "need_follow_up": need_follow_up,
            "criterion_scores": result.get("track_a", {}).get("criterion_scores", {}),
        }

    def get_summary(self) -> dict:
        state_summary = self.state.summary()
        return {
            "state": state_summary,
            "total_questions_asked": self.total_questions_asked,
            "question_history": self.question_history,
            "answer_history": self.answer_history,
        }
