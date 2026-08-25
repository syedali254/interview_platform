"""Build the CMP7200 viva voce presentation.

    python build_viva.py

Marking weights for this assessment drive the structure:
    Presentation — visual      15%
    Presentation — verbal      20%
    Critical evaluation        40%   <- the largest single component
    Q&A / discussion           25%

So the deck spends its middle on findings, limitations and reflection rather
than on a tour of the system. Slides carry figures and short claims; the
argument lives in the speaker notes, which are written to be spoken rather
than read aloud verbatim.
"""

from __future__ import annotations

import json
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
FIGURES = HERE / "figures_png"
EXP_FIGURES = ROOT / "InterviewAI" / "experiments" / "figures"
STATS = ROOT / "InterviewAI" / "experiments" / "results" / "statistics.json"
OUTPUT = HERE.parent / "CMP7200_Viva_Presentation.pptx"

# ── Palette, matching the dissertation figures ───────────────────────────
INK = RGBColor(0x1B, 0x27, 0x33)
MUTED = RGBColor(0x5A, 0x6B, 0x7B)
PAPER = RGBColor(0xFF, 0xFF, 0xFF)
WASH = RGBColor(0xF4, 0xF7, 0xFA)
BLUE = RGBColor(0x1F, 0x4E, 0x79)
GREEN = RGBColor(0x1E, 0x6B, 0x4F)
RUST = RGBColor(0x9A, 0x44, 0x15)
PURPLE = RGBColor(0x4C, 0x3A, 0x8C)
ACCENT = RGBColor(0xB4, 0x53, 0x0F)

W, H = Inches(13.333), Inches(7.5)
MARGIN = Inches(0.72)
FONT = "Calibri"


def _stats():
    return json.loads(STATS.read_text(encoding="utf-8")) if STATS.exists() else {}


AUTHOR = "Abdul Wahab"


class Deck:
    def __init__(self):
        self.prs = Presentation()
        self.prs.slide_width, self.prs.slide_height = W, H
        self.blank = self.prs.slide_layouts[6]
        self.n = 0

    # ── Slide scaffolding ────────────────────────────────────────────────

    def slide(self, title=None, eyebrow=None, *, notes="", accent=BLUE,
              number=True):
        s = self.prs.slides.add_slide(self.blank)
        self.n += 1
        top = MARGIN

        if eyebrow:
            self.text(s, eyebrow.upper(), MARGIN, top, W - 2 * MARGIN, Inches(0.3),
                      size=12, colour=accent, bold=True, space=1.5)
            top += Inches(0.36)

        if title:
            self.text(s, title, MARGIN, top, W - 2 * MARGIN, Inches(0.72),
                      size=30, colour=INK, bold=True)
            top += Inches(0.86)
            # Accent rule under the title
            self.rule(s, MARGIN, top - Inches(0.10), Inches(1.5), accent)
            top += Inches(0.16)

        if number:
            self.text(s, str(self.n), W - MARGIN - Inches(0.6),
                      H - Inches(0.52), Inches(0.5), Inches(0.3),
                      size=11, colour=MUTED, align=PP_ALIGN.RIGHT)

        if notes:
            s.notes_slide.notes_text_frame.text = notes.strip()

        s._content_top = top
        return s

    def text(self, slide, body, left, top, width, height, *, size=16,
             colour=INK, bold=False, italic=False, align=PP_ALIGN.LEFT,
             space=0, line=1.25, font=FONT):
        box = slide.shapes.add_textbox(left, top, width, height)
        tf = box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = 0
        tf.margin_top = tf.margin_bottom = 0
        for i, line_text in enumerate(str(body).split("\n")):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = align
            p.line_spacing = line
            r = p.add_run()
            r.text = line_text
            f = r.font
            f.name, f.size, f.bold, f.italic = font, Pt(size), bold, italic
            f.color.rgb = colour
            if space:
                r.font._rPr.set("spc", str(int(space * 100)))
        return box

    def bullets(self, slide, items, left, top, width, *, size=17, gap=0.52,
                colour=INK, marker_colour=BLUE, lead_colour=None):
        y = top
        for item in items:
            lead, rest = (item if isinstance(item, tuple) else (None, item))
            self.rule(slide, left, y + Inches(0.13), Inches(0.16), marker_colour,
                      thickness=Inches(0.055))
            box = slide.shapes.add_textbox(left + Inches(0.34), y,
                                           width - Inches(0.34), Inches(gap))
            tf = box.text_frame
            tf.word_wrap = True
            tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
            p = tf.paragraphs[0]
            p.line_spacing = 1.22
            if lead:
                r = p.add_run()
                r.text = lead
                r.font.name, r.font.size, r.font.bold = FONT, Pt(size), True
                r.font.color.rgb = lead_colour or marker_colour
            r = p.add_run()
            r.text = rest
            r.font.name, r.font.size = FONT, Pt(size)
            r.font.color.rgb = colour
            lines = max(1, len(rest) // int(width / Inches(1) * 11) + 1)
            y += Inches(gap * lines * 0.62 + 0.16)
        return y

    def rule(self, slide, left, top, width, colour, thickness=Inches(0.045)):
        from pptx.enum.shapes import MSO_SHAPE
        shp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, thickness)
        shp.fill.solid()
        shp.fill.fore_color.rgb = colour
        shp.line.fill.background()
        shp.shadow.inherit = False
        return shp

    def panel(self, slide, left, top, width, height, colour=WASH, line=None):
        from pptx.enum.shapes import MSO_SHAPE
        shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        shp.fill.solid()
        shp.fill.fore_color.rgb = colour
        if line:
            shp.line.color.rgb = line
            shp.line.width = Pt(1.1)
        else:
            shp.line.fill.background()
        shp.shadow.inherit = False
        shp.adjustments[0] = 0.06
        return shp

    def figure(self, slide, name, *, experiments=False, top=None, height=None,
               left=None, width=None):
        path = (EXP_FIGURES if experiments else FIGURES) / f"{name}.png"
        if not path.exists():
            raise FileNotFoundError(path)
        from PIL import Image
        iw, ih = Image.open(path).size
        ratio = ih / iw
        if height is not None:
            w = int(height / ratio)
            h = height
        else:
            w = width or int(W - 2 * MARGIN)
            h = int(w * ratio)
        l = left if left is not None else int((W - w) / 2)
        t = top if top is not None else int((H - h) / 2)
        slide.shapes.add_picture(str(path), l, t, w, h)

    def stat(self, slide, left, top, width, value, label, colour=BLUE,
             height=Inches(1.5), value_size=40, label_size=13):
        self.panel(slide, left, top, width, height)
        self.text(slide, value, left, top + Inches(0.22), width, Inches(0.7),
                  size=value_size, colour=colour, bold=True, align=PP_ALIGN.CENTER)
        self.text(slide, label, left + Inches(0.16), top + Inches(0.92),
                  width - Inches(0.32), Inches(0.5), size=label_size,
                  colour=MUTED, align=PP_ALIGN.CENTER, line=1.15)

    def save(self):
        # Without this, PowerPoint credits the python-pptx author under
        # File > Properties rather than the person who wrote the deck.
        props = self.prs.core_properties
        props.author = AUTHOR
        props.last_modified_by = AUTHOR
        props.title = "An Explainable Multi-Agent AI Interview Platform"
        self.prs.save(OUTPUT)
        return OUTPUT


# ═════════════════════════════════════════════════════════════════════════

def build():
    st = _stats()
    _usage = st.get("meta", {}).get("api_usage", {}).get("by_model", {})
    JUDGE_MODEL = max(_usage, key=_usage.get) if _usage else "the judging model"
    e1 = st.get("e1_discriminant_validity", {})
    e2 = st.get("e2_positional_bias", {})
    e4 = st.get("e4_criterion_independence", {})
    lv = e1.get("by_level", {})

    d = Deck()

    # ── 1. Title ─────────────────────────────────────────────────────────
    s = d.slide(number=False, notes="""
Good morning. My project is an AI interview platform, but the question I set out
to answer is narrower than that and more specific.

Automated interview tools already screen millions of candidates. They return a
score. What they mostly do not return is any account of how stable that score
is. My question was whether a system built around a language model can be made
accountable for the reliability of its own judgements.

I will cover what I built in about five minutes, then spend most of my time on
what measuring it actually revealed — because the evaluation found two real
defects in my own system, and that is the most interesting part of this project.
""")
    d.rule(s, MARGIN, Inches(1.55), Inches(2.2), ACCENT, thickness=Inches(0.07))
    d.text(s, "An Explainable Multi-Agent\nAI Interview Platform", MARGIN, Inches(1.85),
           W - 2 * MARGIN, Inches(2.0), size=44, colour=INK, bold=True, line=1.12)
    d.text(s, "Skill-graph question targeting and a bias-mitigated\nLLM-as-Judge evaluation pipeline",
           MARGIN, Inches(3.65), W - 2 * MARGIN, Inches(1.0), size=19, colour=MUTED, line=1.35)
    d.rule(s, MARGIN, Inches(4.95), Inches(11.9), RGBColor(0xD8, 0xE0, 0xE8),
           thickness=Inches(0.012))
    d.text(s, "CMP7200 — Individual Master's Project    ·    Viva Voce",
           MARGIN, Inches(5.25), W - 2 * MARGIN, Inches(0.4), size=15, colour=INK)
    d.text(s, "Student Number: [STUDENT NUMBER]    ·    MSc Computer Science    ·    2025–26",
           MARGIN, Inches(5.72), W - 2 * MARGIN, Inches(0.4), size=13, colour=MUTED)

    # ── 2. The problem ───────────────────────────────────────────────────
    s = d.slide("A score without an account", eyebrow="The problem", accent=RUST, notes="""
Three things frame this project.

First, the practice. HireVue was challenged by the Electronic Privacy Information
Center in 2019 over unvalidated facial analysis. They withdrew visual analysis in
2021 but kept scoring verbal responses. The underlying problem survived the
change — candidates still received a number and no account of how it was reached.

Second, the regulation. The EU AI Act now classifies recruitment systems as
high-risk and requires transparency, human oversight and bias testing. Opacity is
now a compliance problem, not just an ethical one.

Third — and this is the part that motivated my design — Langer and colleagues
found that candidates rate automated interviews as markedly less fair, and the
effect is strongest where no explanation is given. Candidates who think a process
is unfair are less likely to accept offers. So explainability is not only
ethical, it is commercially instrumental. That reframing is what made me treat it
as an engineering requirement rather than a nice-to-have.
""")
    y = s._content_top + Inches(0.25)
    third = (W - 2 * MARGIN - Inches(0.5)) / 3
    for i, (val, lab, col) in enumerate([
        ("2019", "EPIC challenges HireVue over unvalidated\nfacial analysis in candidate scoring", RUST),
        ("2024", "EU AI Act classifies recruitment as\nhigh-risk: transparency, oversight, bias testing", BLUE),
        ("Unfair", "Candidates rate automated interviews as\nless fair — worst where no explanation is given", ACCENT),
    ]):
        d.stat(s, MARGIN + i * (third + Inches(0.25)), y, third, val, lab, col,
               height=Inches(1.9), value_size=34, label_size=13)
    y += Inches(2.35)
    d.panel(s, MARGIN, y, W - 2 * MARGIN, Inches(1.55), WASH)
    d.text(s, "Language models can now hold a structured interview and articulate a judgement.\n"
              "Whether they can be trusted to grade one is a separate — and much harder — question.",
           MARGIN + Inches(0.4), y + Inches(0.34), W - 2 * MARGIN - Inches(0.8),
           Inches(1.0), size=19, colour=INK, line=1.35)

    # ── 3. Research question ─────────────────────────────────────────────
    s = d.slide(eyebrow="Research question", accent=ACCENT, notes="""
This is the question the whole project turns on.

Note what it does not ask. It does not ask whether a language model can score an
interview answer — the literature already establishes that it can, at roughly
human levels of agreement on open-ended tasks.

It asks whether a system built around one can be held accountable for how
reliable its scores are. That is an engineering question, and it has a testable
answer.

The distinction matters because it changes what counts as success. A system that
scores well but cannot tell you when it is unsure has not solved the problem I
set out to solve.
""")
    d.panel(s, MARGIN, Inches(2.1), W - 2 * MARGIN, Inches(3.0), WASH)
    d.rule(s, MARGIN, Inches(2.1), Inches(0.09), ACCENT, thickness=Inches(3.0))
    d.text(s, "Can an LLM-as-Judge evaluation pipeline be made\n"
              "sufficiently reliable and transparent for high-stakes\n"
              "assessment — through rubric-order randomisation,\n"
              "self-consistency measurement, and calibrated\n"
              "escalation to human review?",
           MARGIN + Inches(0.6), Inches(2.42), W - 2 * MARGIN - Inches(1.1),
           Inches(2.4), size=25, colour=INK, bold=True, line=1.32)
    d.text(s, "Not “can a model grade an answer?” — the literature settles that. "
              "The question is whether the system knows when it is unsure.",
           MARGIN, Inches(5.45), W - 2 * MARGIN, Inches(0.6), size=17,
           colour=MUTED, italic=True)

    # ── 4. Architecture ──────────────────────────────────────────────────
    s = d.slide("Thirteen modules, four phases", eyebrow="What I built", notes="""
The architecture in one sentence: pre-interview turns documents into a targeted
interview plan, the live phase conducts and observes it, assessment scores it,
and reporting fuses the result.

Two things are worth pointing at.

The skill graph on the left feeds both the question generator in phase one and
the fusion engine in phase four — the dashed orange line. It is not just a
preparation step; CV-to-role match is a fifth of the final score in its own
right.

And every module declares its input and output and communicates only through
them. That sounds like textbook advice, but it earned its keep: it is what let me
remove an entire evaluation track late in the project without touching anything
else. I will come back to that.
""")
    d.figure(s, "fig01_architecture", top=s._content_top + Inches(0.05),
             height=Inches(5.15))

    # ── 4b. What a session looks like ────────────────────────────────────
    s = d.slide("What actually happens in a session", eyebrow="End to end", notes="""
Quickly, so you can picture it.

A CV and a job advert go in. The system reads both, maps the skills onto ESCO
and works out what is missing.

It writes the interview and reorders it so the missing skills are asked first —
because every interview has a time budget, and a question that falls off the end
is a question never asked.

The candidate does a device check and picks voice or typing. While they are on
that screen the media server and the agent are already starting, which hides
about twelve seconds of start-up.

The interview runs. The browser watches attention, posture and tone of voice —
none of that video or audio leaves their machine. Tab switches are recorded.

Afterwards the transcript is paired into question-and-answer exchanges.
Greetings and sign-offs are dropped so they cannot dilute the average. Every
real answer is marked twice.

Timing and telemetry go to the integrity check, everything is fused, and the
report comes out with the working shown.

The point to land: the same transcript shape comes out of both voice and text,
so nothing downstream knows or cares which mode ran.
""")
    y = s._content_top + Inches(0.12)
    steps = [
        ("1", "Upload", "CV and job advert read into structured data", BLUE),
        ("2", "Match", "Skills mapped onto ESCO; gaps identified", BLUE),
        ("3", "Plan", "Questions written, missing skills ordered first", BLUE),
        ("4", "Check", "Camera and mic; voice or typing; agent pre-warms", GREEN),
        ("5", "Interview", "Adaptive Q&A; attention and tone measured in-browser", GREEN),
        ("6", "Mark", "Logistics dropped; every real answer scored twice", RUST),
        ("7", "Verify", "Timing and tab switches checked against a baseline", RUST),
        ("8", "Report", "Fused into a recommendation, with the working shown", PURPLE),
    ]
    for i, (num, name, body, col) in enumerate(steps):
        yy = y + i * Inches(0.50)
        d.text(s, num, MARGIN + Inches(0.1), yy, Inches(0.4), Inches(0.4),
               size=15, colour=col, bold=True)
        d.text(s, name, MARGIN + Inches(0.65), yy, Inches(2.2), Inches(0.4),
               size=15, colour=INK, bold=True)
        d.text(s, body, MARGIN + Inches(3.0), yy + Inches(0.02), Inches(8.9),
               Inches(0.4), size=14, colour=MUTED)
    y += Inches(8 * 0.50) + Inches(0.15)
    d.panel(s, MARGIN, y, W - 2 * MARGIN, Inches(0.72), WASH)
    d.text(s, "Voice and text produce an identical transcript — so nothing after the "
              "interview knows which mode ran.",
           MARGIN + Inches(0.45), y + Inches(0.20), W - 2 * MARGIN - Inches(0.9),
           Inches(0.4), size=14, colour=INK)

    # ── 5. Skill graph ───────────────────────────────────────────────────
    s = d.slide("Questions aimed at gaps, not at what the CV already proves",
                eyebrow="Objectives 1 and 2", notes="""
The graph is built from ESCO, the EU occupational taxonomy — 1,201 digital
skills, extended with a modern technology stack and soft skills that ESCO covers
only sparsely.

The design problem here is not building the graph, which is mechanical. It is
mapping free text onto a controlled vocabulary. A CV says k8s; the taxonomy says
Kubernetes.

My first implementation used a substring fallback. It mapped Team Leadership onto
the ESCO concept R — the programming language — and Communication onto
telecommunications engineering. The failure was silent. The graph looked
plausible and the gap analysis reported confident nonsense.

That is the lesson I would most want to carry forward: in this system the
dangerous failures are the silent ones. An exception is visible. A plausible
wrong answer is not. Both of those specific failures are now regression tests.
""")
    d.figure(s, "fig03_skillgraph", top=s._content_top + Inches(0.05),
             height=Inches(4.6))

    # ── 6. The contribution ──────────────────────────────────────────────
    s = d.slide("The scorer measures its own reliability", eyebrow="The contribution",
                accent=RUST, notes="""
This is the core of the project, so let me be precise about it.

Every answer is scored twice against the same rubric, with the four criteria
presented in two different orders. The mean is what gets reported.

But the more useful output is the disagreement between the two passes. A judge
returning 82 and 81 for the same answer is stable. One returning 71 and 45 is
not — and the mean of 58 hides that completely.

So the spread is kept, banded into high, moderate and low consistency, and
answers in the low band are flagged for a human instead of being reported as
confident scores.

That is the mechanism by which the system is accountable for its own reliability.
It is not a claim that the judge is unbiased. It is a claim that when the judge
is unstable, the system says so.
""")
    d.figure(s, "fig04_evaluation_pipeline", top=s._content_top + Inches(0.05),
             height=Inches(4.75))

    # ── 7. Methodology ───────────────────────────────────────────────────
    s = d.slide("Three cycles, each ended by a measurement", eyebrow="Methodology",
                notes="""
Design Science Research, after Hevner. I built an artefact and then studied it.

What I want to draw out is that in all three cycles the evaluation stage produced
a measurement that forced a change, rather than confirming a decision I had
already made.

Cycle one: the substring matching failure I just described.

Cycle two: the voice agent went silent mid-interview. The cause was an exhausted
speech-synthesis quota — the provider accepts the connection and returns no audio,
which is indistinguishable from success unless you inspect the frames. The fix
was a startup probe that spends two characters confirming audio actually comes
back, then falls through to a second provider.

Cycle three ended a whole track. I will come to that.
""")
    d.figure(s, "fig07_dsr", top=s._content_top + Inches(0.1), height=Inches(4.5))

    # ── 8. Evaluation design ─────────────────────────────────────────────
    s = d.slide("Five controlled experiments", eyebrow="How I tested it", notes="""
Five experiments, each isolating one property by manipulating a single factor.

Discriminant validity: does it separate good answers from bad ones.
Positional bias: does presentation order move the score.
Paraphrase invariance: does rewording move it.
Criterion independence: does the rubric actually decompose.
Verbosity: does padding buy marks.

Eighteen graded answers across six questions, each scored twice — so E1, E2 and
E4 all draw on the same set of judge calls. Sixty-eight API calls in total, all
judging done by gemini-2.5-flash.

Worth knowing, and worth saying if asked: that model was withdrawn from new API
keys shortly after I took these measurements, and the system now runs a later
release. So these results describe that model specifically, not language-model
judges in general. It is also a live example of the external-dependency risk in
my limitations.

The sample is small and I will say so again in the limitations. The fixtures were
generated by a different model from the one grading them, which weakens the
objection that the judge is just recognising its own prose.
""")
    y = s._content_top + Inches(0.2)
    rows = [
        ("E1", "Discriminant validity", "Answer quality varied across three known levels",
         "Spearman ρ, weighted κ", BLUE),
        ("E2", "Positional bias", "Rubric order permuted, content held constant",
         "Wilcoxon, mean spread", RUST),
        ("E3", "Paraphrase invariance", "Wording varied, meaning held constant",
         "Within-group SD", GREEN),
        ("E4", "Criterion independence", "Observational across all scored answers",
         "Correlation matrix", PURPLE),
        ("E5", "Verbosity", "Contentless filler appended", "Wilcoxon on pairs", ACCENT),
    ]
    for i, (tag, name, manip, stat_name, col) in enumerate(rows):
        yy = y + i * Inches(0.92)
        d.panel(s, MARGIN, yy, W - 2 * MARGIN, Inches(0.78), WASH)
        d.text(s, tag, MARGIN + Inches(0.3), yy + Inches(0.19), Inches(0.7),
               Inches(0.4), size=17, colour=col, bold=True)
        d.text(s, name, MARGIN + Inches(1.05), yy + Inches(0.19), Inches(3.3),
               Inches(0.4), size=16, colour=INK, bold=True)
        d.text(s, manip, MARGIN + Inches(4.5), yy + Inches(0.21), Inches(4.5),
               Inches(0.4), size=14, colour=MUTED)
        d.text(s, stat_name, MARGIN + Inches(9.3), yy + Inches(0.21), Inches(2.5),
               Inches(0.4), size=14, colour=col)

    # ── 9. Finding 1a ────────────────────────────────────────────────────
    s = d.slide("It ranks answers almost perfectly", eyebrow="Finding 1  ·  the good half",
                accent=GREEN, notes="""
On rank ordering, the result is genuinely strong. Spearman's rho of 0.92, p below
0.001. Cohen's d separating strong from weak answers is 2.98 — a very large
effect.

Within this corpus the judge almost never places a weaker answer above a stronger
one. If the question is "did candidate A answer better than candidate B", the
ordering can be trusted.

Hold that thought, because the next slide is the same data viewed differently,
and it says something much less comfortable.
""")
    d.figure(s, "e1_discriminant_validity", experiments=True,
             top=s._content_top + Inches(0.15), height=Inches(2.9))
    y = s._content_top + Inches(3.25)
    quarter = (W - 2 * MARGIN - Inches(0.75)) / 4
    for i, (v, l, c) in enumerate([
        (f"{e1.get('spearman_rho', 0):.3f}", "Spearman's ρ\nagainst intended quality", GREEN),
        ("p < 0.001", "significance", GREEN),
        (f"{e1.get('separation', {}).get('strong_vs_weak_cohens_d', 0):.2f}",
         "Cohen's d\nstrong vs weak", GREEN),
        (f"{e1.get('n', 0)}", "answers scored\nunder both orderings", MUTED),
    ]):
        d.stat(s, MARGIN + i * (quarter + Inches(0.25)), y, quarter, v, l, c,
               height=Inches(1.6), value_size=32, label_size=12)

    # ── 10. Finding 1b — the key slide ───────────────────────────────────
    s = d.slide("…and calibrates them badly", eyebrow="Finding 1  ·  the defect",
                accent=RUST, notes="""
This is the most important slide in the presentation.

Look at the means. Answers written to be deliberately weak averaged 53. Partially
correct answers averaged 92.8. Strong answers averaged 98.3.

My system reports any answer at or above 70 as strong. So deliberately partial
answers clear that threshold comfortably — and medium and strong answers receive
the identical verdict. Exact band agreement is only 38.9 per cent, and weighted
kappa drops to 0.56.

The scoring model ranks candidates well, and then my verdict layer throws most of
that resolution away.

The implication is about what the score means. A judge that ranks well but
calibrates badly is a comparative instrument, not an absolute one. It supports
"A answered better than B". It does not support "this candidate scored 92 and
therefore meets a standard" — and my artefact was presenting it as though it did.

If asked why I did not simply fix the thresholds: eighteen answers is far too
small a sample on which to move a decision boundary that would affect every
future candidate. Fitting thresholds to this corpus is exactly the overfitting I
criticise elsewhere in the dissertation. I derived the implied boundaries and
recommended recalibration on a larger corpus as the highest-priority next step.
""")
    y = s._content_top + Inches(0.2)
    d.panel(s, MARGIN, y, Inches(6.6), Inches(3.0), WASH)
    d.text(s, "Mean score by intended quality", MARGIN + Inches(0.4), y + Inches(0.22),
           Inches(5.8), Inches(0.4), size=15, colour=MUTED, bold=True)
    for i, (name, key, col) in enumerate([("Weak", "weak", RUST),
                                          ("Medium", "medium", ACCENT),
                                          ("Strong", "strong", GREEN)]):
        yy = y + Inches(0.78) + i * Inches(0.68)
        mean = lv.get(key, {}).get("mean", 0)
        d.text(s, name, MARGIN + Inches(0.4), yy, Inches(1.3), Inches(0.4),
               size=17, colour=INK, bold=True)
        d.rule(s, MARGIN + Inches(1.8), yy + Inches(0.11), Inches(3.4 * mean / 100),
               col, thickness=Inches(0.22))
        d.text(s, f"{mean:.1f}", MARGIN + Inches(5.4), yy, Inches(1.0), Inches(0.4),
               size=18, colour=col, bold=True)
    d.rule(s, MARGIN + Inches(1.8) + Inches(3.4 * 0.70), y + Inches(0.72),
           Inches(0.022), INK, thickness=Inches(2.0))
    d.text(s, "system's 70-point\n“strong” threshold", MARGIN + Inches(1.9) + Inches(3.4 * 0.70),
           y + Inches(2.45), Inches(2.2), Inches(0.5), size=11, colour=INK, line=1.2)

    d.panel(s, MARGIN + Inches(7.0), y, W - MARGIN - (MARGIN + Inches(7.0)),
            Inches(3.0), RGBColor(0xFB, 0xF1, 0xEA))
    d.text(s, "Medium and strong answers\nreceive the same verdict.",
           MARGIN + Inches(7.4), y + Inches(0.35), Inches(4.6), Inches(1.0),
           size=22, colour=RUST, bold=True, line=1.25)
    d.text(s, f"Exact band agreement   {e1.get('exact_band_agreement', 0)*100:.1f}%\n"
              f"Quadratic weighted κ   {e1.get('quadratic_weighted_kappa', 0):.3f}\n"
              f"Medium range   {lv.get('medium', {}).get('min', 0):.1f} – {lv.get('medium', {}).get('max', 0):.1f}\n"
              f"Strong range   {lv.get('strong', {}).get('min', 0):.1f} – {lv.get('strong', {}).get('max', 0):.1f}",
           MARGIN + Inches(7.4), y + Inches(1.65), Inches(4.6), Inches(1.2),
           size=15, colour=INK, line=1.5)

    d.text(s, "The instrument is comparative, not absolute — and the artefact was presenting it as absolute.",
           MARGIN, y + Inches(3.3), W - 2 * MARGIN, Inches(0.5), size=18,
           colour=INK, bold=True)

    # ── 11. Finding 2 — halo ─────────────────────────────────────────────
    s = d.slide("The rubric does not decompose as designed", eyebrow="Finding 2  ·  halo effect",
                accent=PURPLE, notes="""
My rubric instructs the judge, explicitly, to score four criteria independently,
and states that a weakness in one must not drag down the others.

The mean correlation between them is 0.846. Even the most independent pair
correlates at 0.744.

Some correlation is legitimate — accurate answers genuinely do tend to be more
complete, because both follow from understanding the material. But correlations
in this range mean the four scores carry substantially less than four pieces of
information. The judge appears to form one overall impression and then distribute
it. That is the classic halo effect from the human rating literature, and
instructing a model against it evidently did not remove it.

This qualifies a claim I make in the design chapter. I defended the per-criterion
breakdown as telling a candidate which aspect fell short. That defence is weaker
than it looked: if the four marks move together, the breakdown communicates one
impression four times.

The structural response — which I propose rather than claim — is to score each
criterion in a separate call, so each judgement is formed without sight of the
others.
""")
    d.figure(s, "e4_criterion_correlation", experiments=True,
             top=s._content_top + Inches(0.1), height=Inches(3.5),
             left=Inches(0.9))
    x = Inches(6.6)
    d.text(s, f"{e4.get('mean_inter_criterion_r', 0):.3f}", x, s._content_top + Inches(0.35),
           Inches(3.0), Inches(1.0), size=54, colour=PURPLE, bold=True)
    d.text(s, "mean inter-criterion correlation", x, s._content_top + Inches(1.35),
           Inches(4.5), Inches(0.4), size=16, colour=MUTED)
    d.bullets(s, [
        ("Range  ", f"{e4.get('min_inter_criterion_r', 0):.3f} to {e4.get('max_inter_criterion_r', 0):.3f}"),
        ("Instructed  ", "to score the four criteria independently"),
        ("Observed  ", "one impression, distributed across four marks"),
        ("Response  ", "score each criterion in a separate call"),
    ], x, s._content_top + Inches(2.0), Inches(6.0), size=16, marker_colour=PURPLE)

    # ── 12. Finding 3 — null result ──────────────────────────────────────
    s = d.slide("An honest null result", eyebrow="Finding 3  ·  the escalation path",
                accent=MUTED, notes="""
I want to report this one carefully, because it did not go the way my design
predicted.

Positional instability was small. Mean absolute spread between the two rubric
orderings was 2.22 points. Seventeen of eighteen answers fell in the high
consistency band, one in moderate, none in low. No answer was escalated to human
review.

That is a null result for the mechanism I built, and I report it as one rather
than dressing it up. The instrumentation is justified by the literature, it is
demonstrably operative — the spread is computed and banded for every answer — but
on this corpus it never needed to fire.

Two readings are possible and my data cannot separate them. Either the
countermeasure works and the averaging is doing its job, or machine-written
answers are unusually easy to score consistently and real transcribed speech
would produce wider spreads.

There is one piece of weak evidence for the second reading. In my worked example
using a realistic session, the single genuinely partial answer — a candidate
admitting they had not used Kubernetes — drew the widest disagreement of the
interview, ten points. One observation proves nothing, but it points at where the
instrumentation would earn its place: not on clearly good or clearly bad answers,
which are easy, but in the ambiguous middle.
""")
    y = s._content_top + Inches(0.25)
    quarter = (W - 2 * MARGIN - Inches(0.75)) / 4
    for i, (v, l, c) in enumerate([
        (f"{e2.get('mean_absolute_spread', 0):.2f}", "mean spread between\nrubric orderings (points)", BLUE),
        (f"{e2.get('consistency_distribution', {}).get('high', 0)}/{e2.get('n', 0)}", "answers in the\nhigh-consistency band", GREEN),
        ("0", "answers escalated to\nhuman review", MUTED),
        (f"p = {e2.get('wilcoxon_p', 0):.3f}", "Wilcoxon — no systematic\norder effect", MUTED),
    ]):
        d.stat(s, MARGIN + i * (quarter + Inches(0.25)), y, quarter, v, l, c,
               height=Inches(1.75), value_size=34, label_size=12)
    y += Inches(2.15)
    d.panel(s, MARGIN, y, W - 2 * MARGIN, Inches(2.3), WASH)
    d.text(s, "Two readings, and my data cannot separate them",
           MARGIN + Inches(0.45), y + Inches(0.3), Inches(11.5), Inches(0.45),
           size=19, colour=INK, bold=True)
    d.bullets(s, [
        "The countermeasure works, and averaging two orderings is doing its job",
        "Machine-written answers are unusually easy to score consistently, and real speech would differ",
        "Weak evidence for the second: in a realistic session, the one partial answer drew a 10-point spread",
    ], MARGIN + Inches(0.45), y + Inches(0.85), Inches(11.6), size=15,
        marker_colour=MUTED)

    # ── 13. The rejected track ───────────────────────────────────────────
    s = d.slide("I built a second scorer, measured it, and rejected it",
                eyebrow="Deviation from the proposal", accent=ACCENT, notes="""
My proposal's headline contribution was a comparison between the language-model
judge and a trained classifier — Sentence-BERT features into XGBoost, with SHAP
explanations. I built it. Then I removed it. This is the biggest change in the
project, so let me justify it properly.

Three reasons, in order of weight.

First, the comparison was circular by construction. My proposal sourced training
labels by prompting a language model to generate answers at defined quality
levels. So the classifier's ground truth was the language model's own opinion.
Agreement was guaranteed by the design; disagreement would only have measured the
poverty of six surface features. The experiment could not have answered the
question it was built to answer.

Second, the metric that would have made it meaningful was unobtainable. Agreement
with human ratings was the anchor, and that needed the two-rater validation set my
timeline could not accommodate.

Third — and this settled it — the trained model failed on inspection. One feature,
semantic similarity, carried 0.543 of the model, more than the other five
combined. That traced to a data-handling error: the strong answer had been used
as its own reference, so every strong training sample carried a similarity of
exactly 1.0, a value unreachable at inference time.

The probe on the right is the consequence. An answer identical to the reference
scored 64.7. A correct paraphrase of it scored 39.2 — below the threshold at
which my system reports a skill gap. A scorer that calls a correct answer a gap
because the candidate used their own words is not a usable instrument, and it
would have penalised exactly the candidates the system is meant to serve.

I would rather report that as a finding than hide it as a descoping.
""")
    y = s._content_top + Inches(0.2)
    d.panel(s, MARGIN, y, Inches(6.3), Inches(3.5), WASH)
    d.text(s, "Why the comparison could not work", MARGIN + Inches(0.4),
           y + Inches(0.28), Inches(5.6), Inches(0.4), size=17, colour=INK, bold=True)
    d.bullets(s, [
        ("Circular  ", "the classifier's labels were themselves LLM-generated"),
        ("Unanchored  ", "no human gold standard was obtainable in the timeline"),
        ("Broken  ", "a data leak put 0.543 of the model on one feature"),
    ], MARGIN + Inches(0.4), y + Inches(0.85), Inches(5.5), size=15,
        marker_colour=ACCENT)
    d.text(s, "Removed. Objectives 4 and 6 rewritten around establishing\n"
              "the reliability of a single scorer instead.",
           MARGIN + Inches(0.4), y + Inches(2.72), Inches(5.6), Inches(0.7),
           size=14, colour=MUTED, italic=True, line=1.3)

    x2 = MARGIN + Inches(6.7)
    d.panel(s, x2, y, W - MARGIN - x2, Inches(3.5), RGBColor(0xFB, 0xF1, 0xEA))
    d.text(s, "The probe that settled it", x2 + Inches(0.4), y + Inches(0.28),
           Inches(5.0), Inches(0.4), size=17, colour=RUST, bold=True)
    for i, (case, score, verdict, col) in enumerate([
        ("Identical to the reference", "64.7", "weak", ACCENT),
        ("Correct paraphrase", "39.2", "gap", RUST),
        ("Deliberately vague", "29.5", "gap", MUTED),
    ]):
        yy = y + Inches(0.9) + i * Inches(0.75)
        d.text(s, case, x2 + Inches(0.4), yy, Inches(3.2), Inches(0.4),
               size=15, colour=INK)
        d.text(s, score, x2 + Inches(3.7), yy, Inches(1.0), Inches(0.4),
               size=19, colour=col, bold=True)
        d.text(s, verdict, x2 + Inches(4.8), yy + Inches(0.04), Inches(1.0),
               Inches(0.4), size=13, colour=MUTED)
    d.text(s, "A correct answer, in the candidate's own words,\nclassified as a skill gap.",
           x2 + Inches(0.4), y + Inches(2.85), Inches(5.2), Inches(0.7),
           size=15, colour=RUST, bold=True, line=1.3)

    # ── 14. Against objectives ───────────────────────────────────────────
    s = d.slide("Six objectives, honestly assessed", eyebrow="Achievement", notes="""
All six objectives were met, but two were revised mid-project and one carries a
caveat I want to state rather than bury.

Objectives one, two and three — the skill graph, graph-driven question targeting,
and the dual-mode interview — were met as specified and are verified by unit tests
and an end-to-end run.

Objective four was revised. The original wording specified the dual-track
comparison. It became the bias-mitigated single-scorer pipeline, for the reasons
I have just given.

Objective five carries a caveat. The integrity module works and always names the
behaviours behind an adverse verdict — but its baseline is synthetic. It has never
seen a real interview, normal or anomalous, so I cannot quote a false-positive
rate.

Objective six was met and then some: five experiments rather than three, plus a
72-test suite. And it did the thing an evaluation is supposed to do — it found two
real defects in my own artefact.
""")
    y = s._content_top + Inches(0.15)
    objs = [
        ("1", "Skill graph and gap analysis", "Met", GREEN,
         "1,201 ESCO concepts, four-stage cascade, regression-tested"),
        ("2", "Graph-driven question targeting", "Met", GREEN,
         "Technical questions re-sorted by graph priority before the interview"),
        ("3", "Voice and text interview", "Met", GREEN,
         "WebRTC voice with provider fallback; text mode, identical transcript"),
        ("4", "Bias-mitigated evaluation pipeline", "Met, revised", ACCENT,
         "Permuted orderings, self-consistency, escalation — original wording revised"),
        ("5", "Behavioural integrity detection", "Met, with caveat", ACCENT,
         "Calibrated and always explained — but the baseline is synthetic"),
        ("6", "Controlled evaluation", "Met, revised", GREEN,
         "Five experiments, 72 tests — and it found two real defects"),
    ]
    for i, (num, name, verdict, col, ev) in enumerate(objs):
        yy = y + i * Inches(0.82)
        d.panel(s, MARGIN, yy, W - 2 * MARGIN, Inches(0.7), WASH)
        d.text(s, num, MARGIN + Inches(0.32), yy + Inches(0.14), Inches(0.4),
               Inches(0.4), size=17, colour=col, bold=True)
        d.text(s, name, MARGIN + Inches(0.85), yy + Inches(0.15), Inches(4.0),
               Inches(0.4), size=15, colour=INK, bold=True)
        d.text(s, verdict, MARGIN + Inches(4.95), yy + Inches(0.17), Inches(1.9),
               Inches(0.4), size=14, colour=col, bold=True)
        d.text(s, ev, MARGIN + Inches(6.95), yy + Inches(0.18), Inches(4.9),
               Inches(0.4), size=13, colour=MUTED)

    # ── 15. Limitations ──────────────────────────────────────────────────
    s = d.slide("What this work does not establish", eyebrow="Limitations",
                accent=RUST, notes="""
I want to state these plainly, because a marker will find them anyway and
declaring a limitation scores better than hiding one.

Eighteen answers is a small sample. Every figure I have shown carries a wide
confidence interval. These results establish direction and rough magnitude, not
precision.

There were no human raters. My ground truth is an intended quality level, which
is a weaker anchor than expert judgement and blind to any bias that the
specification and the judge happen to share.

The answers were machine-written, so cleaner than transcribed speech. That
plausibly explains both the ceiling effect in E1 and the unusually high
consistency in E2.

The integrity model has never seen a real interview.

And there is an uncomfortable circularity I should name. Avoiding human data
removed the ethical burden of collecting it, and simultaneously removed my
ability to test for the harm that matters most — demographic disparity. A project
of this length can reasonably choose the safer path, but I should not claim the
system has been shown to be fair. It has been shown to be inspectable. That is a
precondition for demonstrating fairness, not a substitute for it.
""")
    y = s._content_top + Inches(0.25)
    left_items = [
        ("Sample size  ", "18 graded answers — direction, not precision"),
        ("No human raters  ", "ground truth is an intended quality level"),
        ("Machine-written data  ", "cleaner than transcribed speech"),
        ("Synthetic baseline  ", "no false-positive rate for integrity"),
    ]
    right_items = [
        ("No criterion validity  ", "no claim that scores predict job performance"),
        ("Single session  ", "in-memory state, one interview at a time"),
        ("Research posture  ", "no auth, transcripts stored unencrypted"),
        ("External dependency  ", "a model was retired mid-evaluation"),
    ]
    d.bullets(s, left_items, MARGIN, y, Inches(5.9), size=16, marker_colour=RUST)
    d.bullets(s, right_items, MARGIN + Inches(6.3), y, Inches(5.6), size=16,
              marker_colour=RUST)
    yy = y + Inches(3.15)
    d.panel(s, MARGIN, yy, W - 2 * MARGIN, Inches(1.5), RGBColor(0xFB, 0xF1, 0xEA))
    d.text(s, "Avoiding human data removed the ethical burden of collecting it — and with it my "
              "ability to test for\ndemographic disparity. The system is shown to be inspectable, "
              "not shown to be fair.",
           MARGIN + Inches(0.45), yy + Inches(0.32), W - 2 * MARGIN - Inches(0.9),
           Inches(1.0), size=17, colour=RUST, line=1.35)

    # ── 16. Contributions ────────────────────────────────────────────────
    s = d.slide("What this project contributes", eyebrow="Contributions", accent=GREEN,
                notes="""
Four things, stated modestly.

A working platform that integrates skill-graph targeting, dual-transport
interviewing, privacy-preserving in-browser analysis, and a scorer that reports
its own per-answer reliability.

An empirical characterisation that separates rank-order validity from absolute
calibration — and quantifies a halo effect that explicit instruction failed to
prevent.

A documented negative result on comparing a trained classifier against a
language-model judge when the classifier's labels are model-generated, with the
measurements that demonstrate the failure.

And a reusable harness and test suite, so every number I have shown can be
regenerated.

The wider claim is modest: transparency is better served by making one scorer
accountable than by adding a second that cannot itself be validated. Redundancy
without independent validation produces the appearance of robustness rather than
robustness.
""")
    y = s._content_top + Inches(0.3)
    items = [
        ("A working artefact", "Skill-graph targeting, dual-transport interview, in-browser "
         "behavioural analysis, and a scorer that reports its own reliability", BLUE),
        ("An empirical characterisation", "Rank-order validity separated from absolute "
         "calibration; a halo effect quantified that instruction failed to prevent", RUST),
        ("A documented negative result", "Why comparing a trained classifier against an LLM "
         "judge fails when the labels are model-generated — with the measurements", ACCENT),
        ("A reproducible harness", "Evaluation suite and 72 unit tests, so every reported "
         "number can be regenerated from cached data", GREEN),
    ]
    for i, (title, body, col) in enumerate(items):
        yy = y + i * Inches(1.12)
        d.panel(s, MARGIN, yy, W - 2 * MARGIN, Inches(0.98), WASH)
        d.rule(s, MARGIN, yy, Inches(0.07), col, thickness=Inches(0.98))
        d.text(s, title, MARGIN + Inches(0.42), yy + Inches(0.14), Inches(4.2),
               Inches(0.4), size=17, colour=col, bold=True)
        d.text(s, body, MARGIN + Inches(4.8), yy + Inches(0.13), Inches(7.0),
               Inches(0.75), size=14, colour=INK, line=1.28)

    # ── 17. Future work ──────────────────────────────────────────────────
    s = d.slide("What I would do next", eyebrow="Future work", notes="""
Ordered by how much each would strengthen the claims.

Threshold recalibration is the single change that would most improve the system
as it stands — but it needs a corpus large enough to avoid overfitting.

Criterion isolation is the direct structural response to the halo effect: score
each criterion in a separate call so each judgement is formed without sight of
the others. It costs four calls per answer instead of two, and it would tell me
whether the correlation is inherent in the answers or induced by assessing all
four together.

A human rating study is the most valuable step for validity — it would replace the
intended-quality anchor with expert judgement and let me test whether the
consistency signal actually predicts the cases where humans and the system
disagree.

Then pilot data for the integrity model, and demographic bias testing — which is
the obligation the AI Act imposes and the one this work has not discharged.

If I began the project again, the single thing I would change is building the
evaluation harness far earlier. I built for most of the project and measured at
the end, so the classifier's defects went undetected for weeks and the leniency
problem surfaced too late to address properly. Measuring alongside building would
have left time to fix rather than only to report.
""")
    y = s._content_top + Inches(0.25)
    items = [
        ("1", "Threshold recalibration", "On a corpus large enough to avoid overfitting — "
         "the single change that would most improve the system", RUST),
        ("2", "Criterion isolation", "Score each rubric criterion in a separate call, "
         "removing the halo effect by construction", PURPLE),
        ("3", "Human-rated validation", "Replace the intended-quality anchor with expert "
         "judgement; test whether the consistency signal predicts disagreement", BLUE),
        ("4", "Pilot data for integrity", "Real sessions, normal and anomalous, to obtain "
         "a measured false-positive rate", GREEN),
        ("5", "Demographic bias testing", "The obligation the EU AI Act imposes, and the "
         "one this work has not discharged", ACCENT),
    ]
    for i, (num, title, body, col) in enumerate(items):
        yy = y + i * Inches(0.92)
        d.text(s, num, MARGIN + Inches(0.05), yy + Inches(0.1), Inches(0.5),
               Inches(0.5), size=22, colour=col, bold=True)
        d.text(s, title, MARGIN + Inches(0.62), yy + Inches(0.14), Inches(3.6),
               Inches(0.4), size=17, colour=INK, bold=True)
        d.text(s, body, MARGIN + Inches(4.4), yy + Inches(0.12), Inches(7.4),
               Inches(0.7), size=14, colour=MUTED, line=1.28)
        if i < len(items) - 1:
            d.rule(s, MARGIN, yy + Inches(0.78), W - 2 * MARGIN,
                   RGBColor(0xE4, 0xEA, 0xF0), thickness=Inches(0.008))

    # ── 18. Close ────────────────────────────────────────────────────────
    s = d.slide(eyebrow="In closing", accent=ACCENT, notes="""
Let me finish where I started.

I set out to find whether a system built around a language model could be held
accountable for the reliability of its own judgements. The answer is a qualified
yes — and the qualification is the useful part.

The judge ranks answers well and calibrates them badly. My rubric decomposes less
than I designed it to. The escalation mechanism I built never needed to fire on
this corpus.

I found all three of those by measuring my own system. A system instrumented to
be examined can be shown to be wrong, and then corrected. I would argue that is
worth more than a higher headline score obtained from a system nobody can
inspect.

Thank you. I am happy to take questions.
""")
    d.text(s, "The judge ranks well.\nIt calibrates badly.", MARGIN, Inches(1.6),
           Inches(11.9), Inches(1.9), size=42, colour=INK, bold=True, line=1.15)
    d.rule(s, MARGIN, Inches(3.75), Inches(2.2), ACCENT, thickness=Inches(0.07))
    d.text(s, "Both defects were found by this project's own evaluation, and both are reported in full.\n"
              "A system instrumented to be examined can be shown to be wrong — and then corrected.",
           MARGIN, Inches(4.15), Inches(11.9), Inches(1.4), size=20, colour=MUTED, line=1.45)
    d.text(s, "Thank you — questions welcome", MARGIN, Inches(5.75), Inches(11.9),
           Inches(0.5), size=18, colour=INK, bold=True)

    # ── Backup slides ────────────────────────────────────────────────────
    s = d.slide("Backup  ·  threshold calibration", eyebrow="Reserve slide", notes="""
Use this if asked why I did not recalibrate the thresholds.

A clean separator exists between weak and medium answers at about 77 — nearly
double the 40 currently in use. No separator exists between medium and strong,
because those distributions overlap: the highest medium answer scored 96.5 and
the lowest strong answer scored 96.0.

I did not change them because eighteen answers is far too small a sample on which
to move a boundary affecting every future candidate. Fitting to this corpus would
be overfitting. What the result establishes is that the current values are
indefensible, not what the correct values are.
""")
    y = s._content_top + Inches(0.4)
    d.panel(s, MARGIN, y, W - 2 * MARGIN, Inches(2.6), WASH)
    hdr = ["Boundary", "In use", "Midpoint of means", "Widest observed gap"]
    # (x offset, column width) — the last column must stop inside the slide
    cols = [(Inches(0.5), Inches(3.4)), (Inches(4.0), Inches(1.6)),
            (Inches(5.9), Inches(2.6)), (Inches(8.7), Inches(3.1))]
    for (c, cw), htxt in zip(cols, hdr):
        d.text(s, htxt, MARGIN + c, y + Inches(0.28), cw, Inches(0.4),
               size=14, colour=MUTED, bold=True)
    for i, row in enumerate([
        ["Weak / medium", "40", "72.9", "76.8  (max weak 67.0, min medium 86.5)"],
        ["Medium / strong", "70", "95.5", "none — the distributions overlap"],
    ]):
        yy = y + Inches(0.95) + i * Inches(0.78)
        for j, ((c, cw), val) in enumerate(zip(cols, row)):
            d.text(s, val, MARGIN + c, yy, cw, Inches(0.5), size=15,
                   colour=RUST if j == 1 else INK, bold=(j == 1), line=1.2)
    d.text(s, "Not changed: 18 answers is too small a sample on which to move a decision boundary "
              "that would affect every future candidate.",
           MARGIN, y + Inches(2.85), W - 2 * MARGIN, Inches(0.6), size=16,
           colour=MUTED, italic=True)

    s = d.slide("Backup  ·  the fusion model", eyebrow="Reserve slide", notes="""
Use this if asked how the final recommendation is composed.

Answer quality carries half the score because it is the most direct evidence of
competence. Skill coverage a fifth — a CV is weaker evidence than a demonstrated
answer, but it is not nothing. Integrity and engagement fifteen per cent each,
deliberately low, because both rest on inferential signals that are easily
misread.

One override exists: integrity below 30 sets the recommendation to disqualified
regardless of the other components. It is the only place a module can override
the others and it is deliberately hard to trigger.
""")
    d.figure(s, "fig06_fusion", top=s._content_top + Inches(0.2), height=Inches(4.4))

    s = d.slide("Backup  ·  privacy and deployment", eyebrow="Reserve slide", notes="""
Use this if asked about data protection or GDPR.

Video and audio are analysed in the browser using MediaPipe and the Web Audio
API. Only derived numeric features cross the network — attention and posture
scores, prosodic measures. No biometric data leaves the candidate's device. Under
GDPR that materially reduces the processing footprint.

It does not answer the deeper objection that inferring engagement from posture
and gaze is intrusive, and that nervousness and evasion look alike to any such
measure. My mitigations — light weighting, calibrating against the candidate's own
neutral pose rather than an assumed ideal, and reporting as context rather than
finding — reduce the harm without resolving the principle.
""")
    d.figure(s, "fig09_deployment", top=s._content_top + Inches(0.25), height=Inches(4.2))

    s = d.slide("Backup  ·  verification", eyebrow="Reserve slide", notes="""
Use this if asked how I know the artefact works.

Seventy-two unit tests over the deterministic components — skill matching, gap
analysis, question ordering, transcript pairing, integrity calibration, fusion
arithmetic, state transitions and report assembly. All pass. Two are direct
regressions on the substring-matching failure.

Plus an end-to-end run against a synthetic candidate using live model calls at
every stage, asserting that the graph builds, questions are ordered by priority,
logistics exchanges are excluded from scoring, rubric criteria stay in range and
sum to the reported score, and the fusion contributions reconcile with the total.
""")
    y = s._content_top + Inches(0.4)
    third = (W - 2 * MARGIN - Inches(0.5)) / 3
    for i, (v, l, c) in enumerate([
        ("72", "unit tests, all passing —\nno API calls required", GREEN),
        ("2", "direct regressions on the\nsubstring-matching failure", RUST),
        ("1", "end-to-end run with live\nmodel calls at every stage", BLUE),
    ]):
        d.stat(s, MARGIN + i * (third + Inches(0.25)), y, third, v, l, c,
               height=Inches(1.9), value_size=44, label_size=13)
    y += Inches(2.3)
    d.bullets(s, [
        "Skill normalisation, the four-stage matching cascade, and its regressions",
        "Gap analysis: matched / missing / bonus / extra partitioning and match percentage",
        "Transcript pairing: consecutive-speaker merging, unanswered questions, empty input",
        "Fusion: weight sums, arithmetic reconciliation, integrity override, monotonicity",
    ], MARGIN, y, W - 2 * MARGIN, size=16, marker_colour=BLUE)

    return d.save()


if __name__ == "__main__":
    path = build()
    from pptx import Presentation as _P
    p = _P(str(path))
    notes = sum(1 for s in p.slides
                if s.has_notes_slide and s.notes_slide.notes_text_frame.text.strip())
    print(f"Written: {path}")
    print(f"  slides        : {len(p.slides.__iter__.__self__._sldIdLst)}")
    print(f"  speaker notes : {notes}")
