"""Main orchestrator — connects all modules into one complete interview session."""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent))

import config

from models.skill_extractor import extract_cv_skills, extract_jd_requirements
from models.skill_graph import (
    build_skill_graph,
    update_node_status,
    get_graph_summary,
    visualize_graph,
)
from models.question_generator import (
    get_next_skill,
    generate_question,
    should_follow_up,
    mark_node_complete,
    get_interview_progress,
)
from models.evaluator import evaluate_answer, get_score_label
from utils.document_loader import load_cv, load_jd


# ---------------------------------------------------------------------------
# Section 1: Helper functions
# ---------------------------------------------------------------------------

def print_header(text):
    width = 60
    print("\n" + "=" * width)
    print(f"  {text}")
    print("=" * width)


def print_divider():
    print("-" * 60)


def print_progress(graph):
    progress = get_interview_progress(graph)
    print(f"\nProgress: {progress['completed']}/{progress['total_skills']} "
          f"skills covered ({progress['percent_complete']:.1f}%)")
    print(f"Strong: {progress['verified_strong']} | "
          f"Weak: {progress['verified_weak']} | "
          f"Gap: {progress['confirmed_gap']} | "
          f"Remaining: {progress['remaining']}")


# ---------------------------------------------------------------------------
# Section 2: Report generation
# ---------------------------------------------------------------------------

def generate_final_report(graph, session_results, cv_skills, jd_requirements):
    summary = get_graph_summary(graph)

    verdict_table = []
    scores = []
    total_questions = 0

    for node, attrs in graph.nodes(data=True):
        nt = attrs.get("node_type")
        if nt not in ("matched", "gap"):
            continue
        score = attrs.get("score")
        if score is not None:
            scores.append(score)
        eval_result = attrs.get("evaluation_result") or {}
        feedback = ""
        if eval_result.get("track_a"):
            feedback = eval_result["track_a"].get("feedback", "")
        total_questions += attrs.get("questions_asked", 0)

        verdict_table.append({
            "skill": node,
            "importance": attrs.get("importance", "N/A"),
            "node_type": nt,
            "claimed_proficiency": attrs.get("claimed_proficiency"),
            "status": attrs.get("status", ""),
            "score": score,
            "feedback": feedback,
        })

    overall_score = sum(scores) / len(scores) if scores else 0.0

    must_have_gaps = sum(
        1 for v in verdict_table
        if v["importance"] == "must_have" and v["status"] == config.STATUS_CONFIRMED_GAP
    )

    if overall_score >= 75 and must_have_gaps == 0:
        recommendation = "Strong Fit"
        recommendation_detail = (
            "Candidate demonstrates strong knowledge across "
            "required skills with no critical gaps identified."
        )
    elif overall_score >= 50 and must_have_gaps <= 1:
        recommendation = "Conditional Fit"
        recommendation_detail = (
            "Candidate shows solid foundation but has areas requiring "
            "development. Consider with mentoring plan."
        )
    else:
        recommendation = "Not Recommended"
        recommendation_detail = (
            "Candidate has significant gaps in critical required skills."
        )

    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    return {
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
        "overall_score": overall_score,
        "recommendation": recommendation,
        "recommendation_detail": recommendation_detail,
        "graph_summary": summary,
        "verdict_table": verdict_table,
        "session_results": session_results,
        "total_questions_asked": total_questions,
    }


# ---------------------------------------------------------------------------
# Section 3: Display report
# ---------------------------------------------------------------------------

def display_report(report):
    print_header("INTERVIEW COMPLETE - FINAL REPORT")

    print(f"\nSession ID: {report['session_id']}")
    print(f"Timestamp: {report['timestamp']}")
    print(f"Total Questions Asked: {report['total_questions_asked']}")

    print_divider()
    print(f"OVERALL SCORE: {report['overall_score']:.1f}/100")
    print(f"RECOMMENDATION: {report['recommendation']}")
    print(f"DETAIL: {report['recommendation_detail']}")

    print_divider()
    print("SKILL BREAKDOWN:")
    print(f"{'Skill':<20} {'Importance':<12} {'Status':<20} {'Score':<8}")
    print("-" * 60)

    status_prefix = {
        config.STATUS_VERIFIED_STRONG: "[STRONG]",
        config.STATUS_VERIFIED_WEAK: "[WEAK]  ",
        config.STATUS_CONFIRMED_GAP: "[GAP]   ",
        config.STATUS_GAP: "[SKIP]  ",
        config.STATUS_PENDING: "[SKIP]  ",
        config.STATUS_SKIPPED: "[SKIP]  ",
    }

    for v in report["verdict_table"]:
        prefix = status_prefix.get(v["status"], "[????]  ")
        score_str = f"{v['score']:.1f}" if v["score"] is not None else "-"
        print(f"{v['skill']:<20} {v['importance']:<12} {prefix:<20} {score_str:<8}")

    print_divider()
    print("GRAPH SUMMARY:")
    s = report["graph_summary"]
    print(f"  Total skills mapped: {s['total']}")
    print(f"  Verified Strong: {s.get('verified_strong', 0)}")
    print(f"  Verified Weak: {s.get('verified_weak', 0)}")
    print(f"  Confirmed Gap: {s.get('confirmed_gap', 0)}")

    out_dir = "outputs"
    os.makedirs(out_dir, exist_ok=True)
    filename = f"{out_dir}/report_{report['session_id']}.json"
    with open(filename, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nReport saved: {filename}")


# ---------------------------------------------------------------------------
# Section 4: Main pipeline function
# ---------------------------------------------------------------------------

def run_pipeline(cv_source, jd_text):
    os.makedirs("outputs", exist_ok=True)

    # STEP 1 — Load documents
    print_header("InterviewIQ - AI Interview Platform")
    print("Loading documents...")
    cv_text = load_cv(cv_source)
    jd_text = load_jd(jd_text)
    print(f"CV loaded: {len(cv_text)} characters")
    print(f"JD loaded: {len(jd_text)} characters")

    # STEP 2 — Extract skills
    print("\nExtracting skills from CV...")
    cv_skills = extract_cv_skills(cv_text)
    print(f"Found {len(cv_skills)} skills in CV:")
    for s in cv_skills:
        print(f"  - {s['skill']} ({s.get('proficiency', 'N/A')}) [{s.get('category', 'N/A')}]")

    print("\nExtracting requirements from JD...")
    jd_requirements = extract_jd_requirements(jd_text)
    print(f"Found {len(jd_requirements)} requirements in JD:")
    for r in jd_requirements:
        print(f"  - {r['skill']} ({r.get('importance', 'N/A')}) [{r.get('category', 'N/A')}]")

    # STEP 3 — Build skill graph
    print("\nBuilding skill graph...")
    graph = build_skill_graph(cv_skills, jd_requirements)
    summary = get_graph_summary(graph)
    print("Graph built:")
    print(f"  Matched skills: {summary.get('matched', 0)}")
    print(f"  Skill gaps: {summary.get('gap', 0)}")
    print(f"  Extra skills: {summary.get('extra', 0)}")

    fig = visualize_graph(graph, "Initial Skill Graph")
    fig.savefig("outputs/graph_initial.png", bbox_inches="tight", dpi=150)
    print("Initial graph saved: outputs/graph_initial.png")

    # STEP 4 — Interview loop
    print_header("Starting Interview Session")
    print("Type your answers and press Enter.")
    print("Type 'skip' to skip a question.")
    print("Type 'quit' to end the interview early.")

    session_results = []
    asked_questions = []
    question_count = 0

    while question_count < config.MAX_QUESTIONS_PER_SESSION:
        skill = get_next_skill(graph)
        if skill is None:
            print("\nAll skills have been covered.")
            break

        node = graph.nodes[skill]
        question_count += 1

        print_divider()
        print(f"\nQuestion {question_count}/{config.MAX_QUESTIONS_PER_SESSION}")
        print(f"Skill: {skill} | Type: {node['node_type']} | "
              f"Importance: {node.get('importance', 'N/A')}")

        print("Generating question...")
        question = generate_question(
            skill=skill,
            node_type=node["node_type"],
            importance=node.get("importance", "nice_to_have"),
            category=node.get("category", "other"),
            claimed_proficiency=node.get("claimed_proficiency"),
            current_status=node["status"],
            asked_questions=asked_questions,
        )

        asked_questions.append(question)
        graph.nodes[skill]["questions_asked"] += 1

        print(f"\nQuestion: {question}\n")

        answer = input("Your answer >> ").strip()

        if answer.lower() == "quit":
            print("\nInterview ended early by candidate.")
            break

        if answer.lower() == "skip":
            print(f"Skipping {skill}...")
            graph.nodes[skill]["status"] = config.STATUS_SKIPPED
            mark_node_complete(graph, skill)
            continue

        if len(answer.split()) < 5:
            print("Answer too short - marking as gap.")
            update_node_status(graph, skill, 0.0)
            mark_node_complete(graph, skill)
            continue

        print("\nEvaluating your answer...")
        result = evaluate_answer(
            question=question,
            candidate_answer=answer,
            skill=skill,
        )

        graph.nodes[skill]["evaluation_result"] = result

        print(f"\nScore: {result['final_score']:.1f}/100 - "
              f"{get_score_label(result['final_score'])}")
        print(f"Feedback: {result['track_a']['feedback']}")
        print(f"Breakdown: "
              f"Accuracy={result['track_a']['criterion_scores']['technical_accuracy']:.0f}/25 | "
              f"Completeness={result['track_a']['criterion_scores']['completeness']:.0f}/25 | "
              f"Clarity={result['track_a']['criterion_scores']['clarity']:.0f}/25 | "
              f"Relevance={result['track_a']['criterion_scores']['relevance']:.0f}/25")

        new_status = update_node_status(graph, skill, result["final_score"])
        print(f"Status: {skill} -> {new_status}")

        session_results.append({
            "skill": skill,
            "question": question,
            "answer": answer,
            "evaluation": result,
        })

        if should_follow_up(graph, skill):
            graph.nodes[skill]["follow_ups_asked"] = (
                graph.nodes[skill].get("follow_ups_asked", 0) + 1
            )
            print(f"\n-> Follow-up question will be generated for {skill}")
        else:
            mark_node_complete(graph, skill)
            print(f"-> {skill} complete")

        print_progress(graph)

    # STEP 5 — Mark remaining
    for node, attrs in graph.nodes(data=True):
        if attrs.get("completed"):
            continue
        if attrs.get("node_type") in ("matched", "gap"):
            if attrs.get("status") in (config.STATUS_PENDING, config.STATUS_GAP):
                graph.nodes[node]["status"] = config.STATUS_SKIPPED

    # STEP 6 — Final graph
    fig = visualize_graph(graph, "Final Skill Graph")
    fig.savefig("outputs/graph_final.png", bbox_inches="tight", dpi=150)
    print("\nFinal graph saved: outputs/graph_final.png")

    # STEP 7 — Report
    report = generate_final_report(graph, session_results, cv_skills, jd_requirements)
    display_report(report)

    return report


# ---------------------------------------------------------------------------
# Section 5: __main__
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    CV_TEXT = """
Sarah Chen - Backend Software Engineer
4 years of professional experience in backend development.

Technical Skills:
- Python: 4 years, advanced proficiency
- Django: 3 years, intermediate proficiency
- PostgreSQL: 3 years, intermediate proficiency
- Docker: 2 years, intermediate proficiency
- Redis: 1 year, beginner proficiency
- Git: 4 years, advanced proficiency
- REST API design: 3 years, intermediate proficiency
"""

    JD_TEXT = """
Backend Engineer - TechCorp

Required Skills:
- Python programming is mandatory and essential
- Django framework experience is required
- FastAPI knowledge is required
- PostgreSQL database skills are essential
- Docker containerization is required
- AWS cloud experience is required

Preferred Skills:
- Redis caching knowledge is a plus
- Kubernetes experience is beneficial
- CI/CD pipeline experience is preferred
"""

    report = run_pipeline(CV_TEXT, JD_TEXT)
    print("\nPipeline test complete.")
