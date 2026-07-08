"""Skill Graph Visualization — generates professional hierarchical graph images."""

import io
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np


# ─── Color Palette ────────────────────────────────────────────────────────────
COLORS = {
    "candidate": "#38A169",       # Green
    "required": "#E53E3E",        # Red
    "nice": "#D69E2E",            # Gold
    "matched": "#2B6CB0",         # Strong Blue
    "missing": "#C53030",         # Dark Red
    "extra": "#718096",           # Gray-blue
    "category": "#4A5568",        # Dark gray
    "edge": "#A0AEC0",            # Light gray
    "bg": "#FFFFFF",              # White
    "text": "#1A202C",            # Near black
}


def render_candidate_graph(skill_graph) -> io.BytesIO:
    """Render candidate skills grouped by ESCO category."""
    categories = skill_graph.get_skill_categories()
    groups = categories.get("candidate", {})

    if not groups:
        return _empty_figure("No candidate skills detected")

    return _render_grouped_graph(
        groups=groups,
        title="CANDIDATE SKILL NETWORK",
        subtitle=f"{sum(len(v) for v in groups.values())} skills mapped to ESCO taxonomy",
        node_color=COLORS["candidate"],
        category_color="#276749",
    )


def render_job_graph(skill_graph) -> io.BytesIO:
    """Render job requirement skills grouped by ESCO category."""
    categories = skill_graph.get_skill_categories()
    groups_req = categories.get("required", {})
    groups_nice = categories.get("nice", {})

    if not groups_req and not groups_nice:
        return _empty_figure("No job requirements detected")

    return _render_dual_grouped_graph(
        groups_primary=groups_req,
        groups_secondary=groups_nice,
        title="JOB REQUIREMENTS MAP",
        subtitle=f"{sum(len(v) for v in groups_req.values())} required | {sum(len(v) for v in groups_nice.values())} nice-to-have",
        primary_color=COLORS["required"],
        secondary_color=COLORS["nice"],
        primary_label="Required",
        secondary_label="Nice to Have",
    )


def render_gap_graph(skill_graph) -> io.BytesIO:
    """Render the gap analysis — matched vs missing vs extra."""
    gaps = skill_graph.analyse_gaps()
    matched = gaps["matched_required"]
    missing = gaps["missing_required"]
    bonus = gaps["matched_nice_to_have"]

    if not matched and not missing:
        return _empty_figure("No data for gap analysis")

    return _render_gap_comparison(
        matched=matched,
        missing=missing,
        bonus=bonus,
        title="SKILL GAP ANALYSIS",
        match_pct=gaps["match_percentage"],
    )


def render_full_graph(skill_graph) -> io.BytesIO:
    """Render the complete unified skill map with ESCO categories."""
    gaps = skill_graph.analyse_gaps()
    categories = skill_graph.get_skill_categories()

    # Classify all skills
    all_categories = {}
    matched_set = set(gaps["matched_required"])
    missing_set = set(gaps["missing_required"])

    for skill in gaps["matched_required"]:
        all_categories[skill] = "matched"
    for skill in gaps["missing_required"]:
        all_categories[skill] = "missing"
    for skill in gaps["matched_nice_to_have"]:
        all_categories[skill] = "bonus_match"
    for skill in gaps["missing_nice_to_have"]:
        all_categories[skill] = "bonus_miss"
    for skill in gaps["extra_skills"]:
        all_categories[skill] = "extra"

    if not all_categories:
        return _empty_figure("No skills to display")

    return _render_unified_map(
        categories=all_categories,
        skill_graph=skill_graph,
        title="COMPLETE SKILL MAP",
        subtitle=f"{len(all_categories)} skills | ESCO taxonomy ({skill_graph.get_stats()['esco_taxonomy_size']} skills loaded)",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# INTERNAL RENDERING FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════


def _render_grouped_graph(groups: dict, title: str, subtitle: str,
                          node_color: str, category_color: str) -> io.BytesIO:
    """Render skills grouped by category in a clean hierarchical layout."""
    fig, ax = plt.subplots(1, 1, figsize=(14, 9), facecolor=COLORS["bg"])
    ax.set_facecolor(COLORS["bg"])

    # Layout: categories on the left, skills radiating right
    y_positions = {}
    x_skill = 0.65
    x_cat = 0.15
    total_cats = len(groups)
    cat_spacing = 0.85 / max(total_cats, 1)

    all_positions = {}
    edges = []

    for i, (cat, skills) in enumerate(sorted(groups.items())):
        cat_y = 0.9 - (i * cat_spacing)
        all_positions[f"__cat_{cat}"] = (x_cat, cat_y)

        skill_spacing = min(cat_spacing / max(len(skills), 1), 0.06)
        start_y = cat_y + (len(skills) - 1) * skill_spacing / 2

        for j, skill in enumerate(skills):
            sy = start_y - j * skill_spacing
            all_positions[skill] = (x_skill + np.random.uniform(-0.05, 0.15), sy)
            edges.append((f"__cat_{cat}", skill))

    # Draw edges (curved lines)
    for (src, dst) in edges:
        if src in all_positions and dst in all_positions:
            x1, y1 = all_positions[src]
            x2, y2 = all_positions[dst]
            ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                        arrowprops=dict(arrowstyle="-", color=COLORS["edge"],
                                        connectionstyle="arc3,rad=0.1", lw=1.2, alpha=0.5))

    # Draw category nodes
    for key, (x, y) in all_positions.items():
        if key.startswith("__cat_"):
            cat_name = key.replace("__cat_", "")
            bbox = FancyBboxPatch((x - 0.08, y - 0.018), 0.16, 0.036,
                                  boxstyle="round,pad=0.008",
                                  facecolor=category_color, edgecolor="none", alpha=0.9)
            ax.add_patch(bbox)
            ax.text(x, y, cat_name, ha="center", va="center",
                    fontsize=8, fontweight="bold", color="white", family="sans-serif")
        else:
            bbox = FancyBboxPatch((x - 0.07, y - 0.015), 0.14, 0.03,
                                  boxstyle="round,pad=0.006",
                                  facecolor=node_color, edgecolor="none", alpha=0.85)
            ax.add_patch(bbox)
            ax.text(x, y, key.title(), ha="center", va="center",
                    fontsize=7.5, fontweight="medium", color="white", family="sans-serif")

    # Title
    ax.text(0.5, 0.97, title, ha="center", va="top",
            fontsize=15, fontweight="bold", color=COLORS["text"], family="sans-serif")
    ax.text(0.5, 0.93, subtitle, ha="center", va="top",
            fontsize=10, color="#718096", family="sans-serif")

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    plt.tight_layout(pad=0.5)

    return _fig_to_buffer(fig)


def _render_dual_grouped_graph(groups_primary: dict, groups_secondary: dict,
                               title: str, subtitle: str,
                               primary_color: str, secondary_color: str,
                               primary_label: str, secondary_label: str) -> io.BytesIO:
    """Render two groups side by side — required vs nice-to-have."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8), facecolor=COLORS["bg"])

    for ax, groups, color, label in [
        (ax1, groups_primary, primary_color, primary_label),
        (ax2, groups_secondary, secondary_color, secondary_label),
    ]:
        ax.set_facecolor(COLORS["bg"])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")

        # Header
        ax.text(0.5, 0.95, label, ha="center", va="top",
                fontsize=13, fontweight="bold", color=color, family="sans-serif")

        if not groups:
            ax.text(0.5, 0.5, "None", ha="center", va="center",
                    fontsize=12, color="#A0AEC0")
            continue

        # Render skills as a clean list with category headers
        y = 0.85
        for cat, skills in sorted(groups.items()):
            if y < 0.05:
                break
            ax.text(0.1, y, f"▸ {cat}", ha="left", va="center",
                    fontsize=9, fontweight="bold", color=COLORS["category"])
            y -= 0.06
            for skill in skills:
                if y < 0.05:
                    break
                bbox = FancyBboxPatch((0.12, y - 0.015), 0.7, 0.035,
                                      boxstyle="round,pad=0.005",
                                      facecolor=color, edgecolor="none", alpha=0.15)
                ax.add_patch(bbox)
                ax.plot(0.14, y, "o", color=color, markersize=6, alpha=0.9)
                ax.text(0.18, y, skill.title(), ha="left", va="center",
                        fontsize=9, color=COLORS["text"], family="sans-serif")
                y -= 0.05
            y -= 0.03

    # Main title
    fig.suptitle(title, fontsize=15, fontweight="bold", color=COLORS["text"],
                 family="sans-serif", y=0.98)
    fig.text(0.5, 0.94, subtitle, ha="center", fontsize=10, color="#718096")

    plt.tight_layout(pad=1.0, rect=[0, 0, 1, 0.92])
    return _fig_to_buffer(fig)


def _render_gap_comparison(matched: list, missing: list, bonus: list,
                           title: str, match_pct: float) -> io.BytesIO:
    """Render gap analysis as a clear visual comparison."""
    fig, ax = plt.subplots(1, 1, figsize=(14, 9), facecolor=COLORS["bg"])
    ax.set_facecolor(COLORS["bg"])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Title + match percentage
    ax.text(0.5, 0.96, title, ha="center", va="top",
            fontsize=15, fontweight="bold", color=COLORS["text"], family="sans-serif")

    # Match score circle
    circle = plt.Circle((0.5, 0.82), 0.06, color=COLORS["matched"], alpha=0.15)
    ax.add_patch(circle)
    ax.text(0.5, 0.82, f"{match_pct}%", ha="center", va="center",
            fontsize=18, fontweight="bold", color=COLORS["matched"], family="sans-serif")
    ax.text(0.5, 0.74, "Match Score", ha="center", va="center",
            fontsize=9, color="#718096")

    # Three columns: Matched | Missing | Bonus
    columns = [
        (0.17, matched, COLORS["matched"], "✓ MATCHED", "Skills you have that match"),
        (0.5, missing, COLORS["missing"], "✗ MISSING", "Required skills you lack"),
        (0.83, bonus, COLORS["nice"], "★ BONUS", "Nice-to-have you possess"),
    ]

    for cx, skills, color, header, desc in columns:
        # Column header
        ax.text(cx, 0.66, header, ha="center", va="center",
                fontsize=11, fontweight="bold", color=color, family="sans-serif")
        ax.text(cx, 0.62, desc, ha="center", va="center",
                fontsize=7.5, color="#718096", family="sans-serif")

        # Count badge
        badge = plt.Circle((cx, 0.56), 0.025, color=color, alpha=0.2)
        ax.add_patch(badge)
        ax.text(cx, 0.56, str(len(skills)), ha="center", va="center",
                fontsize=10, fontweight="bold", color=color)

        # Skill pills
        y = 0.49
        for skill in skills[:10]:
            bbox = FancyBboxPatch((cx - 0.12, y - 0.014), 0.24, 0.03,
                                  boxstyle="round,pad=0.005",
                                  facecolor=color, edgecolor="none", alpha=0.12)
            ax.add_patch(bbox)
            ax.text(cx, y, skill.title(), ha="center", va="center",
                    fontsize=8, color=color, fontweight="medium", family="sans-serif")
            y -= 0.04

        if len(skills) > 10:
            ax.text(cx, y, f"+{len(skills) - 10} more", ha="center", va="center",
                    fontsize=7.5, color="#A0AEC0", style="italic")

    # Divider lines
    ax.axvline(x=0.33, ymin=0.05, ymax=0.7, color="#E2E8F0", lw=1, alpha=0.6)
    ax.axvline(x=0.67, ymin=0.05, ymax=0.7, color="#E2E8F0", lw=1, alpha=0.6)

    plt.tight_layout(pad=0.5)
    return _fig_to_buffer(fig)


def _render_unified_map(categories: dict, skill_graph, title: str,
                        subtitle: str) -> io.BytesIO:
    """Render a unified knowledge graph with clear node placement."""
    fig, ax = plt.subplots(1, 1, figsize=(15, 10), facecolor=COLORS["bg"])
    ax.set_facecolor(COLORS["bg"])

    # Build a subgraph using skill labels as nodes (not URIs)
    G = nx.DiGraph()
    for skill, cat in categories.items():
        G.add_node(skill, category=cat)

    if len(G.nodes) == 0:
        return _empty_figure("No skills to visualize")

    # Use shell layout - put matched in center, missing outer
    if len(G.nodes) <= 8:
        pos = nx.spring_layout(G, k=4, iterations=100, seed=42)
    elif len(G.nodes) <= 20:
        pos = nx.kamada_kawai_layout(G)
    else:
        shells = []
        matched_n = [n for n, c in categories.items() if c == "matched"]
        missing_n = [n for n, c in categories.items() if c == "missing"]
        other_n = [n for n, c in categories.items() if c not in ("matched", "missing")]
        if matched_n:
            shells.append(matched_n)
        if other_n:
            shells.append(other_n)
        if missing_n:
            shells.append(missing_n)
        if not shells:
            shells = [list(G.nodes)]
        pos = nx.shell_layout(G, nlist=shells)

    # Color mapping
    color_map = {
        "matched": COLORS["matched"],
        "missing": COLORS["missing"],
        "bonus_match": "#38A169",
        "bonus_miss": COLORS["nice"],
        "extra": COLORS["extra"],
    }

    # Draw edges
    nx.draw_networkx_edges(
        G, pos, ax=ax,
        edge_color="#CBD5E0",
        arrows=True, arrowsize=12,
        arrowstyle="-|>",
        connectionstyle="arc3,rad=0.08",
        width=1.2, alpha=0.5,
    )

    # Draw nodes by category
    for cat, color in color_map.items():
        nodes = [n for n, c in categories.items() if c == cat and n in pos]
        if nodes:
            nx.draw_networkx_nodes(
                G, pos, ax=ax,
                nodelist=nodes,
                node_color=color,
                node_size=1400,
                edgecolors="white",
                linewidths=2.5,
                alpha=0.9,
            )

    # Draw labels with white background for readability
    for node, (x, y) in pos.items():
        label = node.title() if len(node) <= 14 else node.title()[:12] + ".."
        ax.text(x, y, label, ha="center", va="center",
                fontsize=7.5, fontweight="bold", color="white",
                family="sans-serif")

    # Title
    ax.set_title(title, fontsize=15, fontweight="bold", color=COLORS["text"],
                 family="sans-serif", pad=20)
    ax.text(0.5, 1.02, subtitle, ha="center", va="bottom", transform=ax.transAxes,
            fontsize=10, color="#718096")

    # Legend
    legend_items = [
        mpatches.Patch(color=COLORS["matched"], label="Matched (Have + Required)"),
        mpatches.Patch(color=COLORS["missing"], label="Missing (Required)"),
        mpatches.Patch(color="#38A169", label="Bonus Matched"),
        mpatches.Patch(color=COLORS["nice"], label="Nice-to-Have (Missing)"),
        mpatches.Patch(color=COLORS["extra"], label="Extra (Candidate Only)"),
    ]
    ax.legend(handles=legend_items, loc="lower right", framealpha=0.95,
              fontsize=9, edgecolor="#E2E8F0", fancybox=True)

    ax.axis("off")
    plt.tight_layout(pad=1.0)
    return _fig_to_buffer(fig)


# ─── Utilities ────────────────────────────────────────────────────────────────

def _fig_to_buffer(fig) -> io.BytesIO:
    """Save figure to BytesIO buffer."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return buf


def _empty_figure(message: str) -> io.BytesIO:
    """Return a clean placeholder figure with a message."""
    fig, ax = plt.subplots(1, 1, figsize=(10, 5), facecolor=COLORS["bg"])
    ax.set_facecolor(COLORS["bg"])
    ax.text(0.5, 0.5, message, ha="center", va="center",
            fontsize=14, color="#718096", family="sans-serif")
    ax.axis("off")
    return _fig_to_buffer(fig)
