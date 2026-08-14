"""Unit tests for the deterministic parts of the pipeline.

Everything here runs offline — no LLM calls, no network, no LiveKit. The parts
that depend on a language model are covered by the end-to-end check and by the
evaluation harness in experiments/.

Run:  python -m pytest tests/ -v      (or: python tests/test_core.py)
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.agents.question_generator import build_interview_flow
from core.evaluator.score_fusion import (
    ENGAGEMENT_WEIGHTS,
    WEIGHTS,
    compute_engagement,
    compute_fusion_score,
)
from core.evaluator.behavioural_integrity import (
    NORMAL_THRESHOLD,
    assess_integrity,
    extract_behavioral_features,
)
from core.graph.skill_graph import SkillGraph, build_graph, normalise, display_name
from core.graph.skill_state import InterviewState
from core.pipeline.post_interview import derive_behaviour, pair_exchanges
from core.report.report_builder import build_report, judge_reliability


# ═══════════════════════════════════════════════════════════════════════
# M3 — Skill graph
# ═══════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def graph():
    """One SkillGraph for the whole module — loading ESCO is slow."""
    return SkillGraph()


class TestNormalisation:
    def test_lowercases_and_trims(self):
        assert normalise("  Python  ") == "python"

    def test_strips_punctuation_noise_but_keeps_technical_chars(self):
        assert normalise("Node.js") == "node.js"
        assert normalise("C#") == "c#"
        assert normalise("CI/CD") == "ci/cd"

    def test_collapses_whitespace(self):
        assert normalise("machine    learning") == "machine learning"

    def test_display_name_strips_parenthetical(self):
        assert display_name("Python (computer programming)") == "Python"


class TestSkillMatching:
    def test_exact_extension_label(self, graph):
        assert graph.match_skill("Docker") is not None

    def test_alias_resolves_to_same_node(self, graph):
        assert graph.match_skill("k8s") == graph.match_skill("Kubernetes")
        assert graph.match_skill("postgres") == graph.match_skill("PostgreSQL")
        assert graph.match_skill("amazon web services") == graph.match_skill("AWS")

    def test_case_and_spacing_insensitive(self, graph):
        assert graph.match_skill("  rEaCt  ") == graph.match_skill("React")

    def test_base_form_reaches_parenthesised_esco_label(self, graph):
        """'python' must reach 'Python (computer programming)'."""
        assert graph.match_skill("Python") is not None

    def test_short_labels_never_fuzzy_match(self, graph):
        """The regression this guards: 'Team Leadership' once matched ESCO 'R'."""
        uri = graph.match_skill("Team Leadership")
        assert uri is not None
        assert "leadership" in graph.G.nodes[uri]["label"].lower()

    def test_communication_does_not_match_telecommunications(self, graph):
        uri = graph.match_skill("Communication")
        label = graph.G.nodes[uri]["label"].lower()
        assert "telecommunication" not in label

    def test_unknown_skill_returns_none(self, graph):
        assert graph.match_skill("Flibbertigibbet Framework 9000") is None


class TestGapAnalysis:
    def test_matched_missing_and_extra_are_partitioned(self):
        cv = {"skills": ["Python", "Docker", "Git"]}
        jd = {"required_skills": ["Python", "Kubernetes"], "nice_to_have": ["Docker"]}
        sg = build_graph(cv, jd)
        gaps = sg.analyse_gaps()

        assert "Python" in gaps["matched_required"]
        assert any("ubernetes" in s for s in gaps["missing_required"])
        assert "Docker" in gaps["matched_nice_to_have"]
        assert "Git" in gaps["extra_skills"]
        # Docker is a nice-to-have the candidate has, so it is a bonus, not extra
        assert "Docker" not in gaps["extra_skills"]

    def test_match_percentage_is_over_required_only(self):
        cv = {"skills": ["Python"]}
        jd = {"required_skills": ["Python", "Kubernetes"], "nice_to_have": []}
        sg = build_graph(cv, jd)
        assert sg.analyse_gaps()["match_percentage"] == 50.0

    def test_no_requirements_does_not_divide_by_zero(self):
        sg = build_graph({"skills": ["Python"]}, {"required_skills": [], "nice_to_have": []})
        assert sg.analyse_gaps()["match_percentage"] == 0.0

    def test_unmatched_skill_shared_between_cv_and_jd_still_matches(self):
        """A skill ESCO does not know must still match when it is on both sides."""
        novel = "Flibbertigibbet Framework 9000"
        sg = build_graph({"skills": [novel]}, {"required_skills": [novel]})
        assert sg.analyse_gaps()["match_percentage"] == 100.0

    def test_status_map_assigns_one_status_per_node(self):
        cv = {"skills": ["Python", "Docker", "Git"]}
        jd = {"required_skills": ["Python", "Kubernetes"], "nice_to_have": ["Docker"]}
        sg = build_graph(cv, jd)
        statuses = sg.status_map()
        assert len(statuses) == len(set(statuses))
        assert set(statuses.values()) <= {"matched", "missing", "bonus", "bonus_missing", "extra"}

    def test_graph_payload_counts_match_status_map(self):
        cv = {"skills": ["Python", "Docker"]}
        jd = {"required_skills": ["Python", "AWS"], "nice_to_have": []}
        sg = build_graph(cv, jd)
        payload = sg.to_graph_payload()
        assert payload["total_nodes"] == len(sg.status_map())
        assert sum(payload["counts"].values()) == payload["total_nodes"]


class TestInterviewTopics:
    def test_gaps_are_prioritised_first(self):
        cv = {"skills": ["Python"]}
        jd = {"required_skills": ["Python", "Kubernetes", "AWS"], "nice_to_have": []}
        topics = build_graph(cv, jd).get_interview_topics()
        assert topics[0]["priority"] == "high"

    def test_no_duplicate_skills(self):
        cv = {"skills": ["Python", "Docker"]}
        jd = {"required_skills": ["Python", "Docker", "AWS"], "nice_to_have": ["Docker"]}
        topics = build_graph(cv, jd).get_interview_topics()
        names = [t["skill"].lower() for t in topics]
        assert len(names) == len(set(names))


# ═══════════════════════════════════════════════════════════════════════
# M4 — Question flow ordering
# ═══════════════════════════════════════════════════════════════════════

class TestInterviewFlow:
    QUESTIONS = {
        "opening": [{"question": "How are you?", "purpose": "warm-up"}],
        "technical": [
            {"question": "Low priority Q", "skill": "Git", "difficulty": "easy"},
            {"question": "High priority Q", "skill": "Kubernetes", "difficulty": "hard"},
            {"question": "Medium priority Q", "skill": "Python", "difficulty": "medium"},
        ],
        "behavioural": [{"question": "Tell me about a conflict", "competency": "teamwork"}],
        "closing": [{"question": "Any questions for us?", "purpose": "closing"}],
    }
    TOPICS = [
        {"skill": "Kubernetes", "priority": "high", "reason": "gap"},
        {"skill": "Python", "priority": "medium", "reason": "verify"},
        {"skill": "Git", "priority": "low", "reason": "bonus"},
    ]

    def test_technical_questions_ordered_by_graph_priority(self):
        flow = build_interview_flow(self.QUESTIONS, self.TOPICS)
        tech = [s["skill"] for s in flow if s["type"] == "technical"]
        assert tech == ["Kubernetes", "Python", "Git"]

    def test_section_order_is_opening_technical_behavioural_closing(self):
        flow = build_interview_flow(self.QUESTIONS, self.TOPICS)
        types = [s["type"] for s in flow]
        assert types[0] == "opening"
        assert types[-1] == "closing"
        assert types.index("technical") < types.index("behavioural")

    def test_priority_is_attached_to_each_technical_step(self):
        flow = build_interview_flow(self.QUESTIONS, self.TOPICS)
        k = next(s for s in flow if s.get("skill") == "Kubernetes")
        assert k["priority"] == "high"

    def test_missing_topics_does_not_crash(self):
        flow = build_interview_flow(self.QUESTIONS, None)
        assert len(flow) == 6

    def test_empty_question_set_yields_empty_flow(self):
        assert build_interview_flow({}, self.TOPICS) == []


# ═══════════════════════════════════════════════════════════════════════
# Transcript pairing
# ═══════════════════════════════════════════════════════════════════════

class TestPairExchanges:
    def test_basic_alternating_turns(self):
        convo = [
            {"role": "agent", "text": "Q1?", "time": 0},
            {"role": "candidate", "text": "A1", "time": 10},
            {"role": "agent", "text": "Q2?", "time": 15},
            {"role": "candidate", "text": "A2", "time": 25},
        ]
        ex = pair_exchanges(convo)
        assert len(ex) == 2
        assert ex[0]["question"] == "Q1?" and ex[0]["answer"] == "A1"

    def test_consecutive_agent_turns_merge_into_one_question(self):
        convo = [
            {"role": "agent", "text": "Let me ask you something.", "time": 0},
            {"role": "agent", "text": "How does indexing work?", "time": 3},
            {"role": "candidate", "text": "It builds a B-tree.", "time": 20},
        ]
        ex = pair_exchanges(convo)
        assert len(ex) == 1
        assert "indexing" in ex[0]["question"] and "Let me ask" in ex[0]["question"]

    def test_consecutive_candidate_turns_merge_into_one_answer(self):
        convo = [
            {"role": "agent", "text": "Q?", "time": 0},
            {"role": "candidate", "text": "First part.", "time": 10},
            {"role": "candidate", "text": "Second part.", "time": 14},
        ]
        ex = pair_exchanges(convo)
        assert len(ex) == 1
        assert ex[0]["answer"] == "First part. Second part."

    def test_unanswered_trailing_question_is_dropped(self):
        convo = [
            {"role": "agent", "text": "Q1?", "time": 0},
            {"role": "candidate", "text": "A1", "time": 10},
            {"role": "agent", "text": "Q2 never answered?", "time": 15},
        ]
        assert len(pair_exchanges(convo)) == 1

    def test_candidate_speaking_first_is_ignored(self):
        convo = [
            {"role": "candidate", "text": "Hello?", "time": 0},
            {"role": "agent", "text": "Q1?", "time": 5},
            {"role": "candidate", "text": "A1", "time": 15},
        ]
        ex = pair_exchanges(convo)
        assert len(ex) == 1 and ex[0]["question"] == "Q1?"

    def test_empty_and_whitespace_messages_skipped(self):
        convo = [
            {"role": "agent", "text": "Q?", "time": 0},
            {"role": "candidate", "text": "   ", "time": 5},
            {"role": "candidate", "text": "Real answer", "time": 10},
        ]
        ex = pair_exchanges(convo)
        assert ex[0]["answer"] == "Real answer"

    def test_empty_conversation(self):
        assert pair_exchanges([]) == []
        assert pair_exchanges(None) == []

    def test_timing_is_preserved_for_response_time(self):
        convo = [
            {"role": "agent", "text": "Q?", "time": 10},
            {"role": "candidate", "text": "A", "time": 45},
        ]
        ex = pair_exchanges(convo)
        assert ex[0]["q_time"] == 10 and ex[0]["a_time"] == 45


# ═══════════════════════════════════════════════════════════════════════
# M9 — Behavioural integrity
# ═══════════════════════════════════════════════════════════════════════

class TestIntegrityFeatures:
    def test_defaults_when_no_telemetry(self):
        f = extract_behavioral_features({})
        assert f["avg_response_time_sec"] > 0
        assert f["tab_switches"] == 0

    def test_engagement_falls_with_tab_switches(self):
        clean = extract_behavioral_features({"tab_switches": 0})
        noisy = extract_behavioral_features({"tab_switches": 6})
        assert noisy["engagement_score"] < clean["engagement_score"]

    def test_inactivity_ratio_is_relative_to_duration(self):
        f = extract_behavioral_features({"inactivity_periods": [30, 30], "total_duration": 300})
        assert f["inactivity_ratio"] == pytest.approx(0.2, abs=1e-3)


class TestIntegrityAssessment:
    NORMAL = {
        "response_times": [30, 35, 28, 40, 33],
        "tab_switches": 0,
        "inactivity_periods": [],
        "answer_lengths": [50, 45, 60, 55, 48],
        "total_duration": 600,
        "hesitations": [2, 1, 3, 2, 1],
    }

    def test_normal_session_passes(self):
        r = assess_integrity(self.NORMAL)
        assert r["verdict"] == "normal"
        assert r["integrity_score"] >= NORMAL_THRESHOLD

    def test_score_is_bounded(self):
        for data in (self.NORMAL, {}, {"response_times": [0.1], "tab_switches": 99}):
            r = assess_integrity(data)
            assert 0.0 <= r["integrity_score"] <= 100.0

    def test_implausibly_fast_answers_are_flagged_as_a_risk(self):
        r = assess_integrity({**self.NORMAL, "response_times": [2, 3, 2, 1, 2]})
        assert any("fast" in f.lower() for f in r["risk_factors"])

    def test_heavy_tab_switching_is_flagged(self):
        r = assess_integrity({**self.NORMAL, "tab_switches": 12})
        assert any("tab" in f.lower() for f in r["risk_factors"])

    def test_adverse_verdict_always_carries_an_explanation(self):
        """A verdict a recruiter cannot act on is worse than no verdict."""
        r = assess_integrity({**self.NORMAL, "response_times": [1, 1, 1, 1, 1],
                              "tab_switches": 20, "answer_lengths": [2, 300, 2, 400, 1]})
        if r["verdict"] != "normal":
            assert r["risk_factors"], "adverse verdict with no stated reason"

    def test_deterministic(self):
        a = assess_integrity(self.NORMAL)
        b = assess_integrity(self.NORMAL)
        assert a["integrity_score"] == b["integrity_score"]


class TestDeriveBehaviour:
    def test_response_times_come_from_transcript_timing(self):
        exchanges = [
            {"question": "Q1", "answer": "A1", "q_time": 0, "a_time": 30},
            {"question": "Q2", "answer": "A2", "q_time": 40, "a_time": 75},
        ]
        b = derive_behaviour(exchanges, [], {})
        assert b["response_times"] == [30, 35]

    def test_natural_gaze_shift_is_not_counted_as_inactivity(self):
        exchanges = [{"question": "Q", "answer": "A", "q_time": 0, "a_time": 30}]
        telemetry = {"vision": {"looking_away_ratio": 0.15}, "total_duration": 600}
        assert derive_behaviour(exchanges, [], telemetry)["inactivity_periods"] == []

    def test_sustained_looking_away_does_count(self):
        exchanges = [{"question": "Q", "answer": "A", "q_time": 0, "a_time": 30}]
        telemetry = {"vision": {"looking_away_ratio": 0.60}, "total_duration": 600}
        periods = derive_behaviour(exchanges, [], telemetry)["inactivity_periods"]
        assert periods and periods[0] == pytest.approx(0.40 * 600, abs=1)


# ═══════════════════════════════════════════════════════════════════════
# M11 — Fusion
# ═══════════════════════════════════════════════════════════════════════

class TestFusionWeights:
    def test_top_level_weights_sum_to_one(self):
        assert sum(WEIGHTS.values()) == pytest.approx(1.0)

    def test_engagement_sub_weights_sum_to_one(self):
        assert sum(ENGAGEMENT_WEIGHTS.values()) == pytest.approx(1.0)


class TestFusionArithmetic:
    def test_contributions_reconcile_with_the_total(self):
        r = compute_fusion_score([80, 70, 90], skill_match_pct=75,
                                 integrity_score=90, engagement_score=80)
        total = sum(c["weighted_contribution"] for c in r["components"].values())
        assert total == pytest.approx(r["fusion_score"], abs=0.3)

    def test_all_perfect_gives_one_hundred(self):
        r = compute_fusion_score([100], 100, 100, 100)
        assert r["fusion_score"] == pytest.approx(100.0, abs=0.1)

    def test_all_zero_gives_zero(self):
        r = compute_fusion_score([0], 0, 0, 0)
        assert r["fusion_score"] == pytest.approx(0.0, abs=0.1)

    def test_no_answers_does_not_crash(self):
        r = compute_fusion_score([], 50, 80, 70)
        assert r["components"]["answer_quality"]["score"] == 0.0

    def test_integrity_failure_overrides_everything(self):
        r = compute_fusion_score([95, 98], skill_match_pct=100,
                                 integrity_score=10, engagement_score=95)
        assert r["recommendation"] == "disqualified"

    def test_recommendation_is_monotonic_in_score(self):
        low = compute_fusion_score([20], 20, 100, 20)["fusion_score"]
        mid = compute_fusion_score([60], 60, 100, 60)["fusion_score"]
        high = compute_fusion_score([95], 95, 100, 95)["fusion_score"]
        assert low < mid < high

    def test_strengths_and_concerns_are_populated(self):
        strong = compute_fusion_score([85], 85, 90, 85)
        weak = compute_fusion_score([20], 20, 90, 20)
        assert strong["strengths"] and not strong["concerns"]
        assert weak["concerns"]


class TestEngagement:
    def test_falls_back_when_no_presence_data(self):
        e = compute_engagement(None, None, 0, fallback=72.0)
        assert e["measured"] is False and e["score"] == 72.0

    def test_uses_measured_signals_when_present(self):
        e = compute_engagement({"avg_attention": 0.9, "avg_posture": 0.8},
                               {"vocal_confidence": 70}, 0)
        assert e["measured"] is True
        assert set(e["sources"]) == {"attention", "posture", "voice"}

    def test_partial_signals_reweight_to_available_sources(self):
        e = compute_engagement({"avg_attention": 0.8}, None, 0)
        assert e["measured"] is True
        assert e["score"] == pytest.approx(80.0, abs=0.1)

    def test_distraction_penalty_is_capped(self):
        e = compute_engagement({"avg_attention": 1.0}, None, distraction_count=100)
        assert e["distraction_penalty"] == 30.0
        assert e["score"] == pytest.approx(70.0, abs=0.1)

    def test_score_never_negative(self):
        e = compute_engagement({"avg_attention": 0.05}, None, distraction_count=50)
        assert e["score"] >= 0.0


# ═══════════════════════════════════════════════════════════════════════
# M6a — Skill state tracking
# ═══════════════════════════════════════════════════════════════════════

class TestInterviewState:
    def test_strong_answer_verifies_immediately(self):
        s = InterviewState([{"skill": "Python", "priority": "high"}])
        s.record_answer("Python", 85)
        assert s.get_node("Python").status == "verified_strong"

    def test_single_weak_answer_stays_pending(self):
        s = InterviewState([{"skill": "Python", "priority": "high"}])
        s.record_answer("Python", 50)
        assert s.get_node("Python").status == "pending"

    def test_repeated_low_scores_confirm_a_gap(self):
        s = InterviewState([{"skill": "Python", "priority": "high"}])
        for _ in range(3):
            s.record_answer("Python", 20)
        assert s.get_node("Python").status == "confirmed_gap"

    def test_best_score_and_average_tracked(self):
        s = InterviewState([{"skill": "Python", "priority": "high"}])
        s.record_answer("Python", 40)
        s.record_answer("Python", 60)
        node = s.get_node("Python")
        assert node.best_score == 60
        assert node.avg_score == pytest.approx(50.0)

    def test_unknown_skill_is_ignored_not_crashing(self):
        s = InterviewState([{"skill": "Python", "priority": "high"}])
        s.record_answer("Rust", 90)
        assert "Rust" not in s.nodes

    def test_summary_shape(self):
        s = InterviewState([{"skill": "Python", "priority": "high"}])
        s.record_answer("Python", 85)
        summary = s.summary()
        assert summary["total"] == 1 and summary["verified_strong"] == 1
        assert summary["skills"]["Python"]["questions_asked"] == 1


# ═══════════════════════════════════════════════════════════════════════
# M12 — Report assembly
# ═══════════════════════════════════════════════════════════════════════

def _evaluation(skill, score, spread, consistency, flagged=False):
    return {
        "skill": skill, "kind": "technical", "question": f"About {skill}?",
        "candidate_answer": "An answer", "reference_answer": "Ideal",
        "final_score": score, "verdict": "strong" if score >= 70 else "weak",
        "flagged": flagged,
        "judge": {"score": score, "criterion_scores": {}, "feedback": "ok",
                  "call_scores": [score - spread / 2, score + spread / 2],
                  "spread": spread, "consistency": consistency},
    }


class TestJudgeReliability:
    def test_empty_session_is_reported_not_crashed(self):
        r = judge_reliability([])
        assert r["n"] == 0 and r["note"]

    def test_aggregates_spreads(self):
        r = judge_reliability([
            _evaluation("Python", 80, 2, "high"),
            _evaluation("Docker", 60, 10, "moderate"),
        ])
        assert r["n"] == 2
        assert r["mean_spread"] == pytest.approx(6.0)
        assert r["max_spread"] == 10

    def test_low_consistency_produces_a_review_note(self):
        r = judge_reliability([_evaluation("Python", 55, 25, "low", flagged=True)])
        assert r["consistency_distribution"]["low"] == 1
        assert r["flagged_for_review"] == 1
        assert "flagged for human review" in r["note"]


class TestBuildReport:
    def _report(self):
        evaluations = [
            _evaluation("Python", 85, 2, "high"),
            _evaluation("Kubernetes", 30, 4, "high"),
        ]
        skill_states = {
            "total": 2, "verified_strong": 1, "verified_weak": 0,
            "confirmed_gaps": 1, "pending": 0,
            "skills": {
                "Python": {"status": "verified_strong", "avg_score": 85,
                           "best_score": 85, "questions_asked": 1},
                "Kubernetes": {"status": "confirmed_gap", "avg_score": 30,
                               "best_score": 30, "questions_asked": 1},
            },
        }
        fusion = compute_fusion_score([85, 30], 50, 90, 75)
        integrity = assess_integrity({})
        return build_report(evaluations, [], skill_states, integrity, fusion,
                            {"gaps": {"match_percentage": 50, "missing_required": ["Kubernetes"]}},
                            {"generated_at": "now", "total_exchanges": 3})

    def test_overall_is_the_mean_of_scored_answers(self):
        assert self._report()["overall_score"] == pytest.approx(57.5)

    def test_breakdown_sorted_worst_first(self):
        breakdown = self._report()["breakdown"]
        assert [b["skill"] for b in breakdown] == ["Kubernetes", "Python"]

    def test_strengths_and_gaps_classified_by_threshold(self):
        r = self._report()
        assert "Python" in r["strengths"]
        assert "Kubernetes" in r["gaps"]

    def test_counts_are_consistent(self):
        r = self._report()
        assert r["counts"]["scored_answers"] == 2
        assert r["counts"]["skills_assessed"] == 2

    def test_summary_text_mentions_score_and_label(self):
        r = self._report()
        assert "57.5" in r["summary_text"]
        assert r["fusion"]["label"] in r["summary_text"]


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v", "--tb=short"]))
