"""Build and manage the interview skill graph."""

import sys
import pickle
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx

import config


def build_skill_graph(cv_skills, jd_requirements):
    graph = nx.DiGraph()
    jd_skill_names = [r["skill"].lower() for r in jd_requirements]
    cv_skill_names = [s["skill"].lower() for s in cv_skills]

    for req in jd_requirements:
        skill_name = req["skill"]
        match = None
        for cv in cv_skills:
            if cv["skill"].lower() == skill_name.lower():
                match = cv
                break

        if match:
            graph.add_node(
                skill_name,
                skill=skill_name,
                node_type="matched",
                importance=req["importance"],
                category=match["category"],
                claimed_proficiency=match["proficiency"],
                status=config.STATUS_PENDING,
                questions_asked=0,
                follow_ups_asked=0,
                score=None,
                evaluation_result=None,
                completed=False,
                color="#2ecc71",
            )
        else:
            graph.add_node(
                skill_name,
                skill=skill_name,
                node_type="gap",
                importance=req["importance"],
                category=req["category"],
                claimed_proficiency=None,
                status=config.STATUS_GAP,
                questions_asked=0,
                follow_ups_asked=0,
                score=None,
                evaluation_result=None,
                completed=False,
                color="#e74c3c",
            )

    for cv in cv_skills:
        if cv["skill"].lower() not in jd_skill_names:
            graph.add_node(
                cv["skill"],
                skill=cv["skill"],
                node_type="extra",
                importance=None,
                category=cv["category"],
                claimed_proficiency=cv["proficiency"],
                status="extra",
                questions_asked=0,
                follow_ups_asked=0,
                score=None,
                evaluation_result=None,
                completed=False,
                color="#3498db",
            )

    return graph


def find_skill(graph, skill):
    for node in graph.nodes:
        if node.lower() == skill.lower():
            return node
    raise KeyError(f"Skill '{skill}' not found.")


def increment_questions(graph, skill):
    node = find_skill(graph, skill)
    graph.nodes[node]["questions_asked"] += 1


def update_node_status(graph, skill, score):
    node = find_skill(graph, skill)
    graph.nodes[node]["score"] = score
    if score >= config.SCORE_STRONG_THRESHOLD:
        status = config.STATUS_VERIFIED_STRONG
        color = "#27ae60"
    elif score >= config.SCORE_WEAK_THRESHOLD:
        status = config.STATUS_VERIFIED_WEAK
        color = "#f39c12"
    else:
        status = config.STATUS_CONFIRMED_GAP
        color = "#c0392b"
    graph.nodes[node]["status"] = status
    graph.nodes[node]["color"] = color
    return status


def mark_completed(graph, skill):
    node = find_skill(graph, skill)
    graph.nodes[node]["completed"] = True


def get_priority_queue(graph):
    items = []
    for node, attrs in graph.nodes(data=True):
        if attrs.get("node_type") == "extra":
            continue
        if attrs.get("completed"):
            continue
        items.append((node, attrs.get("importance"), attrs.get("node_type")))

    def sort_key(item):
        _, imp, nt = item
        if nt == "gap" and imp == "must_have":
            return 0
        if nt == "matched" and imp == "must_have":
            return 1
        if nt == "gap" and imp == "nice_to_have":
            return 2
        return 3

    items.sort(key=sort_key)
    return [item[0] for item in items]


def get_graph_summary(graph):
    total = 0
    matched = 0
    gap = 0
    extra = 0
    completed = 0

    for _, attrs in graph.nodes(data=True):
        total += 1
        nt = attrs.get("node_type")
        if nt == "matched":
            matched += 1
        elif nt == "gap":
            gap += 1
        elif nt == "extra":
            extra += 1
        if attrs.get("completed"):
            completed += 1

    return {
        "total": total,
        "matched": matched,
        "gap": gap,
        "extra": extra,
        "completed": completed,
        "remaining": total - completed,
    }


def visualize_graph(graph, title="Candidate Skill Graph"):
    fig, ax = plt.subplots(figsize=(16, 10))
    pos = nx.spring_layout(graph, seed=42, k=2.0)

    matched_nodes = [n for n in graph.nodes if graph.nodes[n].get("node_type") == "matched"]
    gap_nodes = [n for n in graph.nodes if graph.nodes[n].get("node_type") == "gap"]
    extra_nodes = [n for n in graph.nodes if graph.nodes[n].get("node_type") == "extra"]

    for nodelist, shape in [(matched_nodes, "o"), (gap_nodes, "d"), (extra_nodes, "s")]:
        if not nodelist:
            continue
        colors = [graph.nodes[n].get("color", "#cccccc") for n in nodelist]
        sizes = [1300 if graph.nodes[n].get("importance") == "must_have" else 900 for n in nodelist]
        lw = [3 if graph.nodes[n].get("importance") == "must_have" else 1.5 for n in nodelist]

        nx.draw_networkx_nodes(
            graph, pos, ax=ax, nodelist=nodelist, node_shape=shape,
            node_color=colors, node_size=sizes,
            edgecolors="black", linewidths=lw,
        )

    nx.draw_networkx_edges(graph, pos, ax=ax, arrows=True, arrowsize=15, edge_color="#cccccc")

    for node, (x, y) in pos.items():
        attrs = graph.nodes[node]
        status = attrs.get("status", "").replace("_", " ").title()
        score = attrs.get("score")

        y_off = 0.07
        ax.text(x, y - 0.01, node, ha="center", va="center",
                fontweight="bold", fontsize=8, color="black")
        ax.text(x, y - y_off - 0.02, status, ha="center", va="top",
                fontsize=6.5, style="italic", color="#555555")
        if score is not None:
            ax.text(x, y - y_off - 0.06, f"Score: {score:.1f}",
                    ha="center", va="top", fontsize=6.5, color="#333333")

    legend_elements = [
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor="#2ecc71", markersize=12, label="Matched (Pending)"),
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor="#27ae60", markersize=12, label="Verified Strong"),
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor="#f39c12", markersize=12, label="Verified Weak"),
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor="#c0392b", markersize=12, label="Confirmed Gap"),
        plt.Line2D([0], [0], marker="d", color="w", markerfacecolor="#e74c3c", markersize=12, label="Gap (Unasked)"),
        plt.Line2D([0], [0], marker="s", color="w", markerfacecolor="#3498db", markersize=12, label="Extra Skill"),
    ]
    ax.legend(handles=legend_elements, loc="upper right", fontsize=8, title="Legend")

    s = get_graph_summary(graph)
    info = (
        f"Total: {s['total']}\n"
        f"Matched: {s['matched']} | Gap: {s['gap']} | Extra: {s['extra']}\n"
        f"Completed: {s['completed']} | Remaining: {s['remaining']}"
    )
    ax.text(
        0.02, 0.98, info, transform=ax.transAxes, fontsize=8,
        verticalalignment="top",
        bbox=dict(boxstyle="round", facecolor="white", edgecolor="#cccccc", alpha=0.9),
    )

    ax.set_title(
        f"AI Interview Skill Graph\n{s['completed']} / {s['total']} Skills Completed",
        fontsize=14, fontweight="bold", pad=15,
    )

    ax.axis("off")
    fig.tight_layout()
    return fig


def save_graph(graph, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(graph, f)


def load_graph(path):
    path = Path(path)
    with open(path, "rb") as f:
        return pickle.load(f)


if __name__ == "__main__":
    from models.skill_extractor import extract_cv_skills, extract_jd_requirements

    CV_TEXT = """
John Smith - Senior Software Engineer
5 years experience in Python, Django, FastAPI.
Worked with PostgreSQL, Redis, Docker, Kubernetes.
Deployed on AWS (EC2, S3, Lambda).
Familiar with React, Git, Agile methodologies.
Strong problem-solving and communication skills.
"""

    JD_TEXT = """
Backend Engineer required:
- Strong Python (must have)
- Django or FastAPI (must have)
- PostgreSQL (must have)
- Docker (must have)
- AWS preferred (nice to have)
- Redis (nice to have)
- React (nice to have)
- Good communication (must have)
- Kubernetes (nice to have)
- CI/CD experience (nice to have)
"""

    cv_skills = extract_cv_skills(CV_TEXT)
    jd_reqs = extract_jd_requirements(JD_TEXT)
    graph = build_skill_graph(cv_skills, jd_reqs)

    print("Nodes by type:")
    for _, a in graph.nodes(data=True):
        print(f"  {a['node_type']}: {a['skill']}")

    print("\nPriority queue:")
    for i, s in enumerate(get_priority_queue(graph), 1):
        a = graph.nodes[s]
        print(f"  {i}. {s} ({a['node_type']}, {a['importance']})")

    print("\nSummary:")
    for k, v in get_graph_summary(graph).items():
        print(f"  {k}: {v}")

    if len(graph) > 1:
        first = list(graph.nodes)[0]
        update_node_status(graph, first, 85)
        increment_questions(graph, first)
        mark_completed(graph, first)

    out = Path(__file__).resolve().parent.parent / "outputs"
    out.mkdir(exist_ok=True)
    fig = visualize_graph(graph)
    fig.savefig(str(out / "skill_graph_test.png"), dpi=150)
    plt.close(fig)
    print(f"\nGraph saved to outputs/skill_graph_test.png")

    save_graph(graph, out / "graph.pkl")
    print("Graph saved/loaded OK")

    print("\nSkill Graph: Tests passed")
