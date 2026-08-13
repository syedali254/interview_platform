"""Figures for the CMP7200 dissertation.

Every diagram is generated from code so the report can be rebuilt end to end
and no figure drifts out of step with the system it describes.

    python diagrams.py

Layout discipline lives in figkit.Canvas: a reserved header the content cannot
intrude on, automatic text wrapping inside nodes, and a validation pass that
reports any node leaving the canvas or overlapping a sibling.
"""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch

from figkit import (
    ACCENT, INK, MUTED, NEUTRAL, PAPER, PHASE1, PHASE2, PHASE3, PHASE4, RULE,
    Canvas, tint,
)

FIGURES = Path(__file__).parent / "figures"
FIGURES.mkdir(parents=True, exist_ok=True)


def _save(c: Canvas, name: str):
    path = FIGURES / f"{name}.png"
    issues = c.save(path)
    print(f"  {'!' if issues else ' '} {path.name}")
    return issues


# ═════════════════════════════════════════════════════════════════════════
# Figure 1 — System architecture
# ═════════════════════════════════════════════════════════════════════════

def fig_architecture():
    c = Canvas(9.8, 9.0, 1, "System architecture: four-phase modular design",
               "Thirteen modules across four sequential phases. Each declares its input and "
               "output, communicates only through them, and can be developed, deferred or "
               "replaced without disturbing its neighbours.")

    BW = 21.5
    lanes = [
        (PHASE1, "PHASE 1 — PRE-INTERVIEW", [
            ("M1  CV Parsing", "Gemini"),
            ("M2  JD Analysis", "Gemini"),
            ("M3  Skill Graph", "NetworkX + ESCO"),
            ("M4  Question Gen", "LLM + traversal"),
        ]),
        (PHASE2, "PHASE 2 — LIVE INTERVIEW", [
            ("M5  Interview Agent", "LiveKit / text"),
            ("M7  Attention", "FaceLandmarker"),
            ("M8  Posture", "PoseLandmarker"),
            ("M10  Vocal Delivery", "Web Audio"),
        ]),
    ]

    xs = [15.5, 39.0, 62.5, 86.0]
    lane_h = 13.5
    y1 = c.top - 10.0
    y2 = y1 - 21.0
    y3 = y2 - 21.0
    y4 = y3 - 20.0

    for (colour, label, nodes), y in zip(lanes, (y1, y2)):
        c.band(y, lane_h, colour, label)
        for x, (t, s) in zip(xs, nodes):
            c.box(x, y, BW, colour, t, s)

    c.band(y3, lane_h, PHASE3, "PHASE 3 — ASSESSMENT")
    p3 = [(19.5, "M6  Answer Evaluation", "LLM-as-Judge"),
          (50.0, "M6a  Skill State", "Per-skill verdicts"),
          (81.0, "M9  Integrity", "Isolation Forest")]
    for x, t, s in p3:
        c.box(x, y3, 27, PHASE3, t, s)

    c.band(y4, lane_h, PHASE4, "PHASE 4 — REPORTING")
    c.box(33, y4, 28, PHASE4, "M11  Weighted Fusion", "Recommendation")
    c.box(69, y4, 28, PHASE4, "M12  Report Assembly", "Structured output")

    half = 5.0
    railA = (y1 - half + y2 + half) / 2
    railB = (y2 - half + y3 + half) / 2
    railC = (y3 - half + y4 + half) / 2

    for a, b in zip(xs, xs[1:]):
        c.arrow((a + BW / 2, y1), (b - BW / 2, y1), PHASE1)
    c.arrow((33.5, y3), (36.5, y3), PHASE3)
    c.arrow((47, y4), (55, y4), PHASE4)

    c.elbow([(86, y1 - half), (86, railA), (15.5, railA), (15.5, y2 + half)])
    c.label(51, railA + 2.0, "ordered question set")

    c.elbow([(15.5, y2 - half), (15.5, railB), (19.5, railB), (19.5, y3 + half)])
    c.label(10.5, railB + 2.0, "transcript")

    for x in (39.0, 62.5, 86.0):
        c.elbow([(x, y2 - half), (x, railB), (81, railB), (81, y3 + half)], lw=0.9)
    c.label(66, railB + 2.0, "behavioural telemetry")

    for x in (19.5, 50.0, 81.0):
        c.elbow([(x, y3 - half), (x, railC), (33, railC), (33, y4 + half)], lw=0.9)
    c.label(58, railC + 2.0, "scores, verdicts, integrity")

    # M3 feeds the fusion engine directly: CV-to-role match is 20% of the final
    # score. Routed down the left perimeter, below the header, so it crosses no
    # phase label and no other rail.
    c.elbow([(62.5, y1 - half), (62.5, railA + 4.0), (2.6, railA + 4.0),
             (2.6, y4), (33 - 14, y4)], ACCENT, dashed=True, lw=1.0)
    c.label(30, railA + 4.0, "skill match %", colour=ACCENT)

    return _save(c, "fig01_architecture")


# ═════════════════════════════════════════════════════════════════════════
# Figure 2 — End-to-end data flow
# ═════════════════════════════════════════════════════════════════════════

def fig_dataflow():
    c = Canvas(9.8, 5.4, 2, "End-to-end data flow",
               "How a candidate's material becomes a scored, auditable recommendation. "
               "Every arrow is a serialisable payload of fixed shape.")

    top = c.top - 8
    bot = top - 20
    W = 18.5

    row1 = [(11, "CV (PDF)", "PyMuPDF text", PHASE1),
            (32, "Structured profile", "skills, roles", PHASE1),
            (53, "Skill graph", "matched / missing", PHASE1),
            (74, "Question set", "priority ordered", PHASE1),
            (92, "Interview", "voice or text", PHASE2)]
    row2 = [(92, "Transcript", "+ telemetry", PHASE2),
            (68, "Scored answers", "rubric + spread", PHASE3),
            (44, "Integrity", "anomaly score", PHASE3),
            (20, "Final report", "recommendation", PHASE4)]

    for x, t, s, col in row1:
        c.box(x, top, W if x < 90 else 15, col, t, s, title_size=7.6, sub_size=6.4)
    for x, t, s, col in row2:
        c.box(x, bot, W if x < 90 else 15, col, t, s, title_size=7.6, sub_size=6.4)

    c.box(11, top - 10, W, PHASE1, "Job description", "pasted text",
          title_size=7.6, sub_size=6.4)
    c.arrow((20.5, top - 10), (24, top - 2.5), NEUTRAL, rad=0.15)

    for (x1, *_), (x2, *_) in zip(row1, row1[1:]):
        c.arrow((x1 + W / 2, top), (x2 - W / 2, top))
    c.arrow((92, top - 5), (92, bot + 5))
    for (x1, *_), (x2, *_) in zip(row2, row2[1:]):
        c.arrow((x1 - (7.5 if x1 == 92 else W / 2), bot), (x2 + W / 2, bot))

    c.footer("The transcript shape is identical for voice and text, so the assessment phase "
             "contains no branch on interview mode anywhere in its implementation.")
    return _save(c, "fig02_dataflow")


# ═════════════════════════════════════════════════════════════════════════
# Figure 3 — Skill graph matching cascade
# ═════════════════════════════════════════════════════════════════════════

def fig_skillgraph():
    c = Canvas(9.8, 7.1, 3, "Skill graph construction and the four-stage matching cascade",
               "Free-text skills are resolved onto a controlled taxonomy, or given their own "
               "node — never forced onto a near neighbour.")

    top = c.top - 6
    sources = [("ESCO v1.1.1", "1,201 digital skills"),
               ("Tech extension", "15 categories"),
               ("Soft-skill extension", "5 categories"),
               ("Alias map", "~70 variant sets")]
    ys = [top - i * 11.5 for i in range(4)]
    for y, (t, s) in zip(ys, sources):
        c.box(13, y, 22, PHASE1, t, s, title_size=7.6, sub_size=6.4)

    mid_y = (ys[0] + ys[-1]) / 2
    idx_h = ys[0] - ys[-1] + 12
    c.box(38, mid_y, 17, NEUTRAL, "Lookup index",
          "preferred labels\nbase forms\nalt labels\naliases\nfuzzy pool (len ≥ 6)",
          h=idx_h, title_size=7.8, sub_size=6.5)
    for y in ys:
        c.arrow((24.2, y), (29.2, mid_y + (y - mid_y) * 0.32), rad=0.05)

    stages = [("1. Exact preferred label", "“docker” → Docker"),
              ("2. Alias or abbreviation", "“k8s” → Kubernetes"),
              ("3. Base form of ESCO label", "“python” → Python (computer programming)"),
              ("4. Fuzzy match, cutoff 0.88", "only when length ≥ 6")]
    sy = [top - i * 11.5 for i in range(4)]
    for y, (t, s) in zip(sy, stages):
        c.box(76, y, 40, PHASE1, t, s, title_size=7.6, sub_size=6.4)
        c.arrow((46.7, mid_y + (y - mid_y) * 0.32), (55.8, y), rad=0.05)

    fail_y = sy[-1] - 12
    c.box(76, fail_y, 40, ACCENT, "No safe match → its own node",
          "shared namespace, so CV and JD still meet", title_size=7.6, sub_size=6.4)
    c.arrow((76, sy[-1] - 5.2), (76, fail_y + 5.2), ACCENT, dashed=True)

    c.footer("Short labels never fuzzy-match. An earlier substring fallback mapped “Team "
             "Leadership” onto ESCO “R” and “Communication” onto “telecommunications "
             "engineering”; both are now regression-tested.")
    return _save(c, "fig03_skillgraph")


# ═════════════════════════════════════════════════════════════════════════
# Figure 4 — Evaluation pipeline
# ═════════════════════════════════════════════════════════════════════════

def fig_evaluation_pipeline():
    c = Canvas(9.8, 6.4, 4, "Module 6: bias-mitigated LLM-as-Judge evaluation pipeline",
               "Each answer is scored twice under permuted rubric orderings. The mean is "
               "reported; the disagreement between the passes is retained as evidence of that "
               "score's own reliability.")

    top = c.top - 6
    c.box(14, top, 23, PHASE2, "Candidate answer", "from transcript",
          title_size=7.8, sub_size=6.5)
    c.box(14, top - 14, 23, PHASE1, "Question + skill", "from M4 and the graph",
          title_size=7.8, sub_size=6.5)
    c.box(42, top - 7, 22, PHASE3, "Reference answer", "generated, T = 0.1",
          title_size=7.8, sub_size=6.5)
    c.arrow((25.7, top), (30.8, top - 4.5))
    c.arrow((25.7, top - 14), (30.8, top - 9.5))

    c.box(76, top, 36, PHASE3, "Judge pass A",
          "accuracy → completeness → clarity → relevance", title_size=7.8, sub_size=6.3)
    c.box(76, top - 14, 36, PHASE3, "Judge pass B",
          "clarity → relevance → accuracy → completeness", title_size=7.8, sub_size=6.3)
    c.arrow((53.2, top - 5), (57.8, top))
    c.arrow((53.2, top - 9), (57.8, top - 14))
    c.label(76, top - 7, "same rubric, permuted order", colour=ACCENT, italic=True, size=6.4)

    mid = top - 27
    c.box(30, mid, 27, PHASE4, "Mean of the two", "the reported score",
          title_size=7.8, sub_size=6.5)
    c.box(71, mid, 27, ACCENT, "Absolute spread", "self-consistency",
          title_size=7.8, sub_size=6.5)
    c.elbow([(60, top - 5.2), (60, mid + 8), (30, mid + 8), (30, mid + 5.2)])
    c.elbow([(90, top - 5.2), (90, mid + 8), (71, mid + 8), (71, mid + 5.2)], ACCENT)

    low = mid - 14
    c.box(24, low, 30, PHASE4, "Verdict", "strong / weak / gap",
          title_size=7.8, sub_size=6.5)
    c.box(64, low, 30, ACCENT, "spread ≥ 16 → flagged", "escalated to a human",
          title_size=7.8, sub_size=6.5)
    c.arrow((30, mid - 5.2), (24, low + 5.2))
    c.arrow((71, mid - 5.2), (64, low + 5.2), ACCENT)

    c.ax.text(90, low, "high  < 8\nmoderate  < 16\nlow  ≥ 16", ha="center", va="center",
              fontsize=6.3, color=MUTED, linespacing=1.6, zorder=5,
              bbox=dict(boxstyle="round,pad=0.45", fc=tint(ACCENT, 0.05),
                        ec=RULE, lw=0.7))
    return _save(c, "fig04_evaluation_pipeline")


# ═════════════════════════════════════════════════════════════════════════
# Figure 5 — Voice interview sequence
# ═════════════════════════════════════════════════════════════════════════

def fig_sequence():
    c = Canvas(9.8, 6.8, 5, "Live voice interview: sequence of interactions",
               "Pre-warming moves roughly twelve seconds of process start-up off the "
               "candidate's critical path, onto the device-setup screen.")

    lanes = [(10, "Browser", PHASE2), (31, "FastAPI", PHASE1), (51, "LiveKit", NEUTRAL),
             (71, "Agent", PHASE2), (91, "Providers", PHASE3)]
    head_y = c.top - 4
    bottom = 6.0
    for x, name, colour in lanes:
        c.box(x, head_y, 16, colour, name, title_size=7.8)
        c.ax.plot([x, x], [bottom, head_y - 4.2], color=RULE, linewidth=0.9,
                  linestyle=(0, (3, 3)), zorder=0)

    steps = [
        (0, 1, "POST /api/prewarm", False),
        (1, 2, "start media server", False),
        (1, 3, "spawn agent subprocess", False),
        (3, 2, "connect, wait in room", True),
        (0, 1, "GET /token", False),
        (1, 0, "JWT + room name", True),
        (0, 2, "join room", False),
        (2, 3, "participant_connected", False),
        (3, 4, "TTS probe (2 characters)", False),
        (4, 3, "audio frames confirmed", True),
        (3, 0, "publish question text", False),
        (3, 4, "synthesise utterance", False),
        (4, 0, "audio stream", True),
        (0, 4, "candidate speech", False),
        (4, 3, "transcript (Deepgram)", True),
        (3, 1, "save transcript on end", False),
    ]
    y = head_y - 9.5
    step = (y - bottom - 2) / (len(steps) - 1)
    prewarm_top = y + 2.6
    for i, (a, b, text, dashed) in enumerate(steps):
        yy = y - i * step
        xa, xb = lanes[a][0], lanes[b][0]
        c.arrow((xa, yy), (xb, yy), lanes[a][2], lw=1.0, dashed=dashed)
        c.label((xa + xb) / 2, yy + 1.5, text, size=6.2, colour=INK)
        if i == 3:
            prewarm_bot = yy - 2.4

    c.ax.add_patch(FancyBboxPatch(
        (3, prewarm_bot), 94, prewarm_top - prewarm_bot,
        boxstyle="round,pad=0,rounding_size=1", linewidth=0.9, edgecolor=ACCENT,
        facecolor="none", linestyle=(0, (4, 3)), zorder=1))
    c.ax.text(95.5, prewarm_bot + 1.2, "pre-warm phase", fontsize=6.6, color=ACCENT,
              style="italic", va="bottom", ha="right")
    return _save(c, "fig05_sequence")


# ═════════════════════════════════════════════════════════════════════════
# Figure 6 — Fusion weighting
# ═════════════════════════════════════════════════════════════════════════

def fig_fusion():
    c = Canvas(9.8, 5.8, 6, "Module 11: the weighted fusion model",
               "Every contribution to the final score is exposed on the report, so a "
               "recommendation can always be decomposed into the evidence behind it.")

    comps = [("Answer quality", 0.50, PHASE3, "M6 — mean rubric score"),
             ("Skill coverage", 0.20, PHASE1, "M3 — graph match percentage"),
             ("Integrity", 0.15, PHASE3, "M9 — calibrated anomaly score"),
             ("Engagement", 0.15, PHASE2, "M7 + M8 + M10 — presence signals")]

    top = c.top - 5
    gap = 10.6
    BAR_X, BAR_MAX, SPINE = 24.0, 34.0, 66.0
    ys = [top - i * gap for i in range(len(comps))]

    for y, (name, w, colour, source) in zip(ys, comps):
        c.ax.text(1, y + 1.5, name, fontsize=8.2, color=INK, va="center",
                  fontweight="bold")
        c.ax.text(1, y - 2.7, source, fontsize=6.4, color=MUTED, va="center")
        bar_w = BAR_MAX * (w / 0.5)
        c.ax.add_patch(FancyBboxPatch(
            (BAR_X, y - 2.5), bar_w, 5.0,
            boxstyle="round,pad=0,rounding_size=0.7", linewidth=0,
            facecolor=tint(colour, 0.62), zorder=2))
        c.ax.text(BAR_X + bar_w + 2.0, y, f"{w:.0%}", fontsize=8.4, color=colour,
                  va="center", fontweight="bold")
        c.ax.plot([SPINE - 3.0, SPINE], [y, y], color=NEUTRAL, linewidth=0.85, zorder=1)

    # One spine collects the four weighted contributions and feeds the panel.
    c.ax.plot([SPINE, SPINE], [ys[-1], ys[0]], color=NEUTRAL, linewidth=0.85, zorder=1)
    panel_y = (ys[0] + ys[-1]) / 2
    c.arrow((SPINE, panel_y), (70.5, panel_y), NEUTRAL, lw=1.1)

    bands = "\n".join(["≥ 72   Strong hire", "≥ 55   Hire",
                       "≥ 40   Consider", "< 40   No hire"])
    c.box(86, panel_y, 26, NEUTRAL, "Fusion score", bands,
          title_size=8.0, sub_size=6.8)
    c.label(86, panel_y - 13.5, "integrity < 30 overrides\nto disqualified",
            colour=ACCENT, italic=True, size=6.3, boxed=False)

    c.footer("Engagement sub-weights: attention 45%, voice 35%, posture 20%. Where no "
             "presence data is captured the component is reported as estimated rather than "
             "measured.")
    return _save(c, "fig06_fusion")


# ═════════════════════════════════════════════════════════════════════════
# Figure 7 — Design Science Research
# ═════════════════════════════════════════════════════════════════════════

def fig_dsr():
    c = Canvas(9.8, 5.2, 7, "The Design Science Research process as executed",
               "After Hevner et al. (2004). Three build–evaluate–refine cycles, each ending "
               "in a design change traceable to a measurement rather than a preference.")

    top = c.top - 4
    cx, cy, r = 22, top - 17, 12.5
    c.ax.add_patch(Circle((cx, cy), r, fill=False, edgecolor=RULE, linewidth=1.1, zorder=1))
    for lbl, ang in (("Build", 90), ("Evaluate", 210), ("Refine", 330)):
        a = math.radians(ang)
        c.box(cx + r * math.cos(a), cy + r * math.sin(a), 16, PHASE1, lbl,
              title_size=7.8, pad=1.6)
    for ang in (150, 270, 30):
        a = math.radians(ang)
        c.arrow((cx + r * math.cos(a - 0.3), cy + r * math.sin(a - 0.3)),
                (cx + r * math.cos(a + 0.3), cy + r * math.sin(a + 0.3)),
                PHASE1, lw=1.3, rad=0.3)
    c.label(cx, cy + r + 8.5, "Rigour  ·  knowledge base", size=6.8, boxed=False)
    c.label(cx, cy - r - 8.5, "Relevance  ·  problem environment", size=6.8, boxed=False)

    cycles = [
        ("Cycle 1 — skill graph and question targeting",
         "Substring matching mapped unrelated skills, silently. Replaced with a four-stage "
         "cascade plus regression tests."),
        ("Cycle 2 — live interview delivery",
         "A silent agent was traced to an exhausted speech quota. Added a startup probe and "
         "automatic provider fallback."),
        ("Cycle 3 — answer evaluation",
         "A trained second scorer graded a correct paraphrase at 39/100. Track rejected; judge "
         "reliability instrumented instead."),
    ]
    ys = [top - 3 - i * 13.5 for i in range(3)]
    for y, (name, outcome) in zip(ys, cycles):
        c.box(72, y, 50, PHASE3, name, outcome, title_size=7.4, sub_size=6.3,
              align="left")
        c.arrow((36, cy + (y - cy) * 0.45), (46.5, y), rad=0.10, lw=0.9)

    return _save(c, "fig07_dsr")


# ═════════════════════════════════════════════════════════════════════════
# Figure 8 — Use case model
# ═════════════════════════════════════════════════════════════════════════

def _actor(c, x, y, label):
    ax = c.ax
    ax.add_patch(Circle((x, y + 5.0), 1.9, fill=False, edgecolor=INK, linewidth=1.2, zorder=3))
    ax.plot([x, x], [y + 3.1, y - 1.5], color=INK, linewidth=1.2, zorder=3)
    ax.plot([x - 2.5, x + 2.5], [y + 1.5, y + 1.5], color=INK, linewidth=1.2, zorder=3)
    ax.plot([x, x - 2.1], [y - 1.5, y - 4.8], color=INK, linewidth=1.2, zorder=3)
    ax.plot([x, x + 2.1], [y - 1.5, y - 4.8], color=INK, linewidth=1.2, zorder=3)
    ax.text(x, y - 7.4, label, ha="center", fontsize=7.8, color=INK, fontweight="bold")


def fig_usecase():
    c = Canvas(9.8, 5.6, 8, "Use case model",
               "The decision boundary is deliberate: the system produces evidence and "
               "adjudication requests, and the hiring decision stays with a person.")

    top = c.top - 4
    bottom = 5.0
    c.ax.add_patch(FancyBboxPatch(
        (23, bottom), 54, top - bottom, boxstyle="round,pad=0,rounding_size=2",
        linewidth=1.0, edgecolor=RULE, facecolor=tint(NEUTRAL, 0.03), zorder=0))
    c.ax.text(50, top - 1.6, "InterviewAI", ha="center", fontsize=8.0,
              color=MUTED, fontweight="bold", va="top")

    mid = (top + bottom) / 2
    _actor(c, 9, mid, "Candidate")
    _actor(c, 91, mid, "Recruiter")

    left = ["Upload CV", "Complete device check", "Answer questions", "Request to end"]
    right = ["Provide job description", "Review skill gaps", "Read scored report",
             "Adjudicate flagged answers", "Make hiring decision"]

    def ellipses(items, x, colour):
        span = top - 7 - bottom - 4
        step = span / max(len(items) - 1, 1)
        ys = [top - 8 - i * step for i in range(len(items))]
        for y, text in zip(ys, items):
            wrapped = c.wrap(text, 22, 6.7)
            c.ax.add_patch(FancyBboxPatch(
                (x - 12.5, y - 3.1), 25, 6.2,
                boxstyle="round,pad=0,rounding_size=3.1", linewidth=1.0,
                edgecolor=colour, facecolor=tint(colour, 0.07), zorder=2))
            c.ax.text(x, y, wrapped, ha="center", va="center", fontsize=6.7,
                      color=colour, zorder=3, linespacing=1.3)
        return ys

    for y in ellipses(left, 37, PHASE2):
        c.ax.plot([11.8, 24], [mid, y], color=RULE, linewidth=0.9, zorder=1)
    for y in ellipses(right, 63, PHASE4):
        c.ax.plot([88.2, 76], [mid, y], color=RULE, linewidth=0.9, zorder=1)

    c.footer("The system issues no automated hiring decision. Flagged answers and "
             "low-consistency scores are routed to the recruiter for adjudication.")
    return _save(c, "fig08_usecase")


# ═════════════════════════════════════════════════════════════════════════
# Figure 9 — Deployment view
# ═════════════════════════════════════════════════════════════════════════

def fig_deployment():
    c = Canvas(9.8, 5.0, 9, "Deployment and process view",
               "Video and audio are analysed on the candidate's device. Only derived numeric "
               "features cross the network.")

    top = c.top - 4
    bottom = 6.0
    zones = [(1, 43, PHASE2, "CANDIDATE DEVICE  (browser)"),
             (46, 32, PHASE1, "LOCAL HOST"),
             (80, 19, PHASE3, "EXTERNAL SERVICES")]
    for x, w, colour, name in zones:
        c.ax.add_patch(FancyBboxPatch(
            (x, bottom), w, top - bottom, boxstyle="round,pad=0,rounding_size=1.4",
            linewidth=1.0, edgecolor=colour, facecolor=tint(colour, 0.04), zorder=0))
        c.ax.text(x + 1.6, top - 1.4, name, fontsize=6.6, color=colour,
                  fontweight="bold", va="top")

    r1, r2, r3 = top - 7, top - 18, top - 29
    c.box(12, r1, 19, PHASE2, "React SPA", title_size=7.4, pad=1.5)
    c.box(33, r1, 19, PHASE2, "Camera / mic", title_size=7.4, pad=1.5)
    c.box(12, r2, 19, PHASE2, "MediaPipe", "M7 + M8", title_size=7.4, sub_size=6.2, pad=1.5)
    c.box(33, r2, 19, PHASE2, "Web Audio", "M10", title_size=7.4, sub_size=6.2, pad=1.5)
    c.box(22.5, r3, 40, PHASE2, "Derived features only",
          "no video or audio leaves the device", title_size=7.4, sub_size=6.2, pad=1.5)

    c.box(62, r1, 28, PHASE1, "FastAPI (uvicorn)", title_size=7.4, pad=1.5)
    c.box(62, r2, 28, PHASE1, "LiveKit server", "port 7880", title_size=7.4, sub_size=6.2, pad=1.5)
    c.box(62, r3, 28, PHASE1, "Agent subprocess", "one per interview",
          title_size=7.4, sub_size=6.2, pad=1.5)

    c.box(89.5, r1, 16, PHASE3, "Gemini", title_size=7.2, pad=1.5)
    c.box(89.5, r2, 16, PHASE3, "Deepgram", title_size=7.2, pad=1.5)
    c.box(89.5, r3, 16, PHASE3, "ElevenLabs", title_size=7.2, pad=1.5)

    c.arrow((42.5, r1), (47.8, r1))
    c.label(45, r1 + 2.4, "HTTPS", size=6.0)
    c.arrow((42.5, r2), (47.8, r2))
    c.label(45, r2 + 2.4, "WebRTC", size=6.0)
    for y in (r1, r2, r3):
        c.arrow((76.2, y), (81.3, y))

    c.footer("A single-process, single-session deployment appropriate to a research "
             "demonstrator. Concurrency and persistence are discussed in Section 7.3.")
    return _save(c, "fig09_deployment")


# ═════════════════════════════════════════════════════════════════════════
# Figure 10 — Conceptual framework
# ═════════════════════════════════════════════════════════════════════════

def fig_framework():
    c = Canvas(9.8, 5.2, 10, "Conceptual framework derived from the literature",
               "Three documented failings of automated hiring tools, and the design response "
               "this project adopts for each.")

    rows = [
        ("Opacity", "Scores issued without any account of how they were reached",
         "Langer et al. (2019); EPIC (2019)",
         "Rubric transparency",
         "Four criteria, the reference answer and a written rationale all surfaced"),
        ("Susceptibility to bias", "Position and verbosity effects invisible in a single score",
         "Stureborg et al. (2024); Wang et al. (2024)",
         "Order permutation",
         "Two rubric orderings averaged, with explicit anti-verbosity instruction"),
        ("One unvalidated method", "No independent check on the scorer's reliability",
         "Raghavan et al. (2020)",
         "Self-consistency and escalation",
         "Spread measured per answer; unstable scores routed to a human"),
    ]
    top = c.top - 6
    gap = 15.5
    for i, (p, pd, cite, r, rd) in enumerate(rows):
        y = top - i * gap
        c.box(21, y, 36, PHASE3, p, pd, title_size=7.8, sub_size=6.4)
        c.ax.text(21, y - 7.6, cite, ha="center", fontsize=5.9, color=MUTED,
                  style="italic", va="top")
        c.box(72, y, 40, PHASE2, r, rd, title_size=7.8, sub_size=6.4)
        c.arrow((39.2, y), (51.8, y), ACCENT, lw=1.2)

    c.label(45.5, top + 5.2, "design response", colour=ACCENT, italic=True, size=6.4)
    return _save(c, "fig10_framework")


# ═════════════════════════════════════════════════════════════════════════
# Figure 11 — Project schedule
# ═════════════════════════════════════════════════════════════════════════

def fig_gantt():
    fig, ax = plt.subplots(figsize=(9.8, 4.6))
    tasks = [
        ("Literature review", 1, 4, PHASE1),
        ("Environment and data setup", 1, 2, PHASE1),
        ("M1–M2 document parsing", 2, 2, PHASE1),
        ("M3 skill graph and ESCO", 3, 3, PHASE1),
        ("M4 question generation", 5, 2, PHASE1),
        ("M5 voice interview agent", 6, 3, PHASE2),
        ("M7/M8/M10 presence modules", 8, 2, PHASE2),
        ("Text interview mode", 9, 2, PHASE2),
        ("M6 evaluation pipeline", 10, 2, PHASE3),
        ("M9 integrity detection", 10, 2, PHASE3),
        ("M11–M12 fusion and report", 11, 2, PHASE4),
        ("Track B build and rejection", 11, 2, ACCENT),
        ("Evaluation experiments", 12, 2, PHASE3),
        ("Test suite and verification", 12, 2, PHASE3),
        ("Dissertation writing", 7, 8, NEUTRAL),
        ("Viva preparation", 14, 1, NEUTRAL),
    ]
    for i, (name, start, dur, colour) in enumerate(tasks):
        y = len(tasks) - i
        ax.barh(y, dur, left=start, height=0.6, color=tint(colour, 0.55),
                edgecolor=colour, linewidth=0.9, zorder=2)
    ax.set_yticks([len(tasks) - i for i in range(len(tasks))])
    ax.set_yticklabels([t[0] for t in tasks], fontsize=7.6, color=INK)
    ax.set_xlabel("Project week", fontsize=8.2, color=MUTED)
    ax.set_xlim(0.5, 15.4)
    ax.set_xticks(range(1, 15))
    ax.tick_params(axis="x", labelsize=7.6, colors=MUTED)
    ax.grid(axis="x", color="#e8edf2", linewidth=0.7)
    ax.set_axisbelow(True)
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color(RULE)

    for wk, lbl in [(5, "M1 prototype"), (9, "M2 interview"),
                    (13, "M3 draft"), (14, "M4 viva")]:
        ax.axvline(wk, color=ACCENT, linestyle="--", linewidth=0.9, alpha=0.65, zorder=1)
        ax.text(wk, len(tasks) + 0.85, lbl, fontsize=6.3, color=ACCENT, ha="center")
    ax.set_ylim(0.2, len(tasks) + 1.9)
    ax.set_title("Figure 11   Project schedule as delivered, with milestones",
                 fontsize=11.5, color=INK, fontweight="bold", loc="left", pad=16)
    fig.tight_layout()
    path = FIGURES / "fig11_gantt.png"
    fig.savefig(path, bbox_inches="tight", pad_inches=0.12, facecolor=PAPER)
    plt.close(fig)
    print(f"    {path.name}")
    return []


# ═════════════════════════════════════════════════════════════════════════

def main():
    print("Rendering dissertation figures at 300 dpi...")
    issues = []
    for fn in (fig_architecture, fig_dataflow, fig_skillgraph,
               fig_evaluation_pipeline, fig_sequence, fig_fusion, fig_dsr,
               fig_usecase, fig_deployment, fig_framework, fig_gantt):
        issues.extend(fn() or [])
    n = len(list(FIGURES.glob("*.png")))
    print(f"\n{n} figures written to {FIGURES}")
    if issues:
        print(f"{len(issues)} layout problem(s) reported above.")
    else:
        print("No layout problems: nothing clipped, nothing overlapping.")


if __name__ == "__main__":
    main()
