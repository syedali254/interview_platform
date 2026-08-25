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
    """Ten slides, weighted the way the brief marks them.

    The viva is assessed 15% on visuals, 20% on delivery, 40% on critical
    evaluation and reflection, and 25% on the discussion that follows. Four of
    these ten slides are therefore findings and reflection, and the two that
    describe the artefact are compressed into one architecture slide and one
    module table. Every number on a slide is read from the results file.
    """
    st = _stats()
    e1 = st.get("e1_discriminant_validity", {})
    e2 = st.get("e2_positional_bias", {})
    e4 = st.get("e4_criterion_independence", {})
    e5 = st.get("e5_verbosity", {})
    lv = e1.get("by_level", {})
    meta = st.get("meta", {})
    d = Deck()

    def val(x, dp=2):
        return f"{x:.{dp}f}" if isinstance(x, (int, float)) else str(x)

    # ── 1. Title ─────────────────────────────────────────────────────────
    s = d.slide(number=False, notes="""
Good morning. This project asks whether an AI system that scores job interviews
can be made accountable for how reliable its own scores are.

The short version of what I found: the judge ranks answers almost perfectly,
but calibrates them badly, and the per-criterion breakdown I designed as an
explanation does not decompose the way I claimed. Both defects were found by my
own evaluation, in my own system, and both are in the report as findings.
""")
    d.rule(s, MARGIN, Inches(1.55), Inches(2.2), ACCENT, thickness=Inches(0.06))
    d.text(s, "An Explainable Multi-Agent\nAI Interview Platform",
           MARGIN, Inches(1.95), W - 2 * MARGIN, Inches(2.0),
           size=42, colour=INK, bold=True, line=1.12)
    d.text(s, "Skill-graph question targeting and a bias-mitigated\n"
              "LLM-as-Judge evaluation pipeline",
           MARGIN, Inches(3.85), W - 2 * MARGIN, Inches(1.0),
           size=19, colour=MUTED, line=1.3)
    d.rule(s, MARGIN, Inches(5.25), W - 2 * MARGIN, WASH, thickness=Inches(0.02))
    d.text(s, "Abdul Wahab", MARGIN, Inches(5.55), W - 2 * MARGIN, Inches(0.4),
           size=17, colour=INK, bold=True)
    d.text(s, "Student Number: [STUDENT NUMBER]    ·    CMP7200 Individual "
              "Master's Project    ·    Birmingham City University    ·    2025-26",
           MARGIN, Inches(6.0), W - 2 * MARGIN, Inches(0.4), size=13, colour=MUTED)

    # ── 2. The problem ───────────────────────────────────────────────────
    s = d.slide("A score, with no account of how it was reached",
                eyebrow="The problem", accent=RUST, notes="""
Automated interview tools screen millions of candidates. The commercial case is
real: they are consistent in a way tired human panels are not.

But consistency is not accuracy. In 2019 EPIC challenged HireVue over facial
analysis it called unvalidated and opaque. HireVue dropped the video scoring in
2021 and kept scoring speech. The underlying problem survived: a number, and no
explanation.

Langer and colleagues show candidates rate these processes as markedly less
fair, worst where no explanation is given, and are then less likely to accept
an offer. So the explanation problem is commercial as well as ethical.

And the EU AI Act now classes hiring software as high-risk. Note what it asks:
not that a model be unbiased, which is unachievable, but that bias be tested
for, documented and overseen. That is a design brief, and it is the one I took.
""")
    y = s._content_top + Inches(0.12)
    for lead, body, col in (
        ("2019   ", "EPIC challenges HireVue over unvalidated facial analysis. "
                    "Video scoring withdrawn in 2021; speech scoring continues.", RUST),
        ("Unfair   ", "Candidates rate automated interviews as less fair, worst "
                      "where no explanation is given \u2014 and are then less likely "
                      "to accept an offer.", ACCENT),
        ("2024   ", "The EU AI Act classes hiring as high-risk. It does not "
                    "require an unbiased model. It requires that bias be tested "
                    "for, documented and humanly overseen.", BLUE),
    ):
        d.rule(s, MARGIN, y + Inches(0.16), Inches(0.2), col, thickness=Inches(0.06))
        d.text(s, lead, MARGIN + Inches(0.4), y, Inches(1.3), Inches(0.4),
               size=18, colour=col, bold=True)
        d.text(s, body, MARGIN + Inches(1.75), y, W - 2 * MARGIN - Inches(1.9),
               Inches(0.8), size=17, colour=INK, line=1.3)
        y += Inches(1.05)

    d.panel(s, MARGIN, Inches(5.55), W - 2 * MARGIN, Inches(1.15), WASH)
    d.text(s, "So the question is not whether a model can score an interview answer. "
              "It plainly can.\nIt is whether it can be honest about how far each "
              "score should be trusted.",
           MARGIN + Inches(0.45), Inches(5.78), W - 2 * MARGIN - Inches(0.9),
           Inches(0.8), size=18, colour=INK, bold=True, line=1.35)

    # ── 3. What I built ──────────────────────────────────────────────────
    s = d.slide("Thirteen modules, four phases", eyebrow="The solution", notes="""
A CV and a job advert go in. The system maps both onto ESCO, the EU skills
taxonomy, and works out which required skills the candidate has not evidenced.

It writes the interview and reorders it so the missing skills are asked first,
because every interview has a time budget and a question that falls off the end
is never asked.

The interview runs by voice or by text. Both produce an identical transcript, so
nothing downstream knows which ran.

Afterwards the transcript is paired into exchanges, greetings are dropped so
they cannot dilute the average, every real answer is scored twice, behaviour is
checked, and everything is fused into a report that shows its working.

The point to land: each module has one job and a declared input and output, so
any one can be replaced without disturbing the others.
""")
    d.figure(s, "fig01_architecture", top=s._content_top + Inches(0.1),
             height=Inches(4.05))
    y = Inches(6.05)
    for i, (lead, body) in enumerate((
        ("Prepare   ", "read both documents, find the gaps, write the questions"),
        ("Interview   ", "voice or text, adapting as it goes"),
        ("Assess   ", "score every answer twice, check the session"),
        ("Report   ", "fuse into a recommendation, with the working shown"))):
        x = MARGIN + i * ((W - 2 * MARGIN) / 4)
        d.text(s, lead, x, y, Inches(1.5), Inches(0.3), size=14,
               colour=(BLUE, GREEN, RUST, PURPLE)[i], bold=True)
        d.text(s, body, x, y + Inches(0.3), (W - 2 * MARGIN) / 4 - Inches(0.25),
               Inches(0.7), size=12, colour=MUTED, line=1.2)

    # ── 4. Modules and the technology in each ────────────────────────────
    s = d.slide("What each part does, and what it runs on",
                eyebrow="Modules and technology", notes="""
This is the whole system on one slide, so you can see where the AI actually is.

Three modules call a language model: reading the documents, writing the
questions, and scoring the answers. That is Gemini 3.6 Flash in every case.

Two run trained vision models entirely inside the browser \u2014 MediaPipe face and
pose landmarkers. The video never leaves the candidate's machine. Only derived
numbers cross the network.

One trains itself: the Isolation Forest for behavioural integrity fits a model
of normal interaction on first run, because labelled examples of cheating are
not something anyone can ethically collect.

And the skill graph deliberately uses no machine learning at all. ESCO is
already a curated hierarchy; learning embeddings over a documented structure
would add opacity and remove the property that makes it defensible \u2014 that every
edge traces to a published standard.
""")
    rows = [
        ("M1 · M2", "Read the CV and the job advert", "Gemini 3.6 Flash", BLUE),
        ("M3", "Map skills onto ESCO, find the gaps", "NetworkX + ESCO v1.1.1", BLUE),
        ("M4", "Write the questions, gaps asked first", "Gemini 3.6 Flash", BLUE),
        ("M5", "Run the interview by voice or text", "LiveKit · Deepgram Nova-3 · ElevenLabs", GREEN),
        ("M6 · M6a", "Score each answer twice; track each skill", "Gemini as judge, permuted rubric", RUST),
        ("M7 · M8", "Attention and posture, in the browser", "MediaPipe Face + Pose Landmarker", GREEN),
        ("M9", "Flag unusual session behaviour", "Isolation Forest, self-trained", RUST),
        ("M10", "Vocal delivery from pitch and pauses", "Web Audio API", GREEN),
        ("M11 · M12", "Fuse the scores, write the report", "Deterministic weighting", PURPLE),
    ]
    y = s._content_top + Inches(0.06)
    for tag, what, tech, col in rows:
        d.text(s, tag, MARGIN, y, Inches(1.25), Inches(0.34), size=14,
               colour=col, bold=True)
        d.text(s, what, MARGIN + Inches(1.35), y, Inches(5.0), Inches(0.34),
               size=14, colour=INK)
        d.text(s, tech, MARGIN + Inches(6.6), y, W - MARGIN - Inches(6.8),
               Inches(0.34), size=13, colour=MUTED)
        y += Inches(0.44)
    d.panel(s, MARGIN, y + Inches(0.06), W - 2 * MARGIN, Inches(0.62), WASH)
    d.text(s, "Video and audio are analysed on the candidate's own device. Only "
              "derived numbers ever cross the network.",
           MARGIN + Inches(0.4), y + Inches(0.24), W - 2 * MARGIN - Inches(0.8),
           Inches(0.4), size=15, colour=INK, bold=True)

    # ── 5. The contribution ──────────────────────────────────────────────
    s = d.slide("The scorer measures its own reliability",
                eyebrow="The contribution", accent=ACCENT, notes="""
This is the core idea, and it comes straight out of the literature.

Stureborg and colleagues showed LLM judges are positionally biased: change the
order the rubric criteria are presented in and the score changes. Most people
cite that as a reason not to trust LLM judges.

I read it as a specification. If the score depends on presentation order, then
score the same answer twice under two different orders. Averaging cancels the
order-specific component.

But the average is not the interesting output. The disagreement is. Eighty-two
and eighty-one means the judge is sure. Seventy-one and forty-five means it is
not \u2014 and the mean of fifty-eight hides that completely.

So the spread is kept, banded high, moderate or low, and a low-consistency
answer is escalated to a human instead of being reported as a confident score.

That is the whole claim: not that the model is unbiased, but that when it is
unsure, the system says so.
""")
    y = s._content_top + Inches(0.15)
    d.text(s, "Every answer is scored twice, with the four rubric criteria "
              "presented in a different order each time.",
           MARGIN, y, W - 2 * MARGIN, Inches(0.5), size=19, colour=INK, line=1.3)
    y += Inches(0.85)
    for lead, body, col in (
        ("The mean", "cancels the component of the score caused by presentation "
                     "order.", MUTED),
        ("The spread", "is the useful part. 82 and 81 is a stable judgement. "
                       "71 and 45 is not \u2014 and their mean of 58 conceals that "
                       "entirely.", ACCENT),
        ("The action", "low-consistency answers are escalated to a human rather "
                       "than reported as confident scores.", BLUE),
    ):
        d.rule(s, MARGIN, y + Inches(0.17), Inches(0.2), col, thickness=Inches(0.06))
        d.text(s, lead, MARGIN + Inches(0.42), y, Inches(1.8), Inches(0.4),
               size=18, colour=col, bold=True)
        d.text(s, body, MARGIN + Inches(2.3), y, W - 2 * MARGIN - Inches(2.4),
               Inches(0.9), size=17, colour=INK, line=1.3)
        y += Inches(1.0)
    d.panel(s, MARGIN, Inches(5.75), W - 2 * MARGIN, Inches(0.95), WASH)
    d.text(s, "The claim is not that the judge is unbiased. It is that when the "
              "judge is unsure, the system says so.",
           MARGIN + Inches(0.45), Inches(6.02), W - 2 * MARGIN - Inches(0.9),
           Inches(0.5), size=18, colour=INK, bold=True)

    # ── 6. How I tested it ───────────────────────────────────────────────
    s = d.slide("Five controlled experiments on known-quality answers",
                eyebrow="Methodology and evaluation design", notes="""
Design Science Research: build the artefact, then measure it, and let the
measurement change the build. Three cycles, each ended by a measurement that
contradicted something I had assumed.

The evaluation itself needed a corpus where the right answer was known. I could
not use real candidates \u2014 no ethics approval, and the data does not exist. So
answers were written to a specified quality level: weak, medium, strong. That
gives ground truth for rank order, which is what the judge is being tested on.

Five experiments. Does it separate quality levels. Does presentation order move
the score. Does rewording the question move it. Do the four criteria measure
different things. Does padding an answer raise its score.

And one honest constraint worth stating: eighteen graded answers is a small
corpus. Sixty-eight API calls, run serially after I measured that six concurrent
calls took longer than a hundred sequential ones would have. Every result you
are about to see carries that limitation.
""")
    y = s._content_top + Inches(0.1)
    exps = [
        ("E1", "Discriminant validity", "does it separate weak, medium and strong?"),
        ("E2", "Positional bias", "does the rubric order change the score?"),
        ("E3", "Paraphrase invariance", "does rewording the question change it?"),
        ("E4", "Criterion independence", "do the four criteria measure different things?"),
        ("E5", "Verbosity bias", "does padding an answer raise its score?"),
    ]
    for tag, name, q in exps:
        d.text(s, tag, MARGIN, y, Inches(0.8), Inches(0.36), size=17,
               colour=ACCENT, bold=True)
        d.text(s, name, MARGIN + Inches(0.85), y, Inches(3.4), Inches(0.36),
               size=17, colour=INK, bold=True)
        d.text(s, q, MARGIN + Inches(4.4), y, W - MARGIN - Inches(4.7),
               Inches(0.36), size=16, colour=MUTED)
        y += Inches(0.62)
    y += Inches(0.15)
    d.stat(s, MARGIN, y, Inches(3.4), str(meta.get("n_graded_answers", 18)),
           "answers graded, written to a\nspecified quality level", ACCENT,
           height=Inches(1.35), value_size=34)
    d.stat(s, MARGIN + Inches(3.7), y, Inches(3.4),
           str(meta.get("api_usage", {}).get("calls", 68)),
           "API calls in total, run serially\nafter measuring concurrency", BLUE,
           height=Inches(1.35), value_size=34)
    d.stat(s, MARGIN + Inches(7.4), y, Inches(4.4), "72",
           "automated tests, run to produce the\nfigure quoted in the report", GREEN,
           height=Inches(1.35), value_size=34)

    # ── 7. Finding 1 ─────────────────────────────────────────────────────
    s = d.slide("It ranks answers almost perfectly, and calibrates them badly",
                eyebrow="Finding 1", accent=RUST, notes="""
This is the most important slide in the deck, and it is a defect in my own
system.

The good half. Spearman's rho of 0.92, p under ten to the minus seven. It almost
never puts a worse answer above a better one. Cohen's d of 2.98 between strong
and weak. As a ranking instrument it works.

Now the defect. Look at the means. Weak answers average 53. Medium average 92.8.
Strong average 98.3. The system calls anything at or above 70 a strong answer.

So deliberately mediocre answers and genuinely excellent answers receive the
same verdict. Quadratic weighted kappa is 0.56, and exact band agreement is only
39 per cent \u2014 against a rank correlation of 0.92. That gap between rho and kappa
is the finding: the ordering is sound, the thresholds are wrong.

The practical consequence is concrete. These scores are usable for comparing two
candidates against each other. They are not usable for deciding whether one
candidate is good enough on their own. The report says exactly that, and Section
8.3 proposes deriving thresholds from the observed distribution rather than
assuming a 0 to 100 scale is used evenly.
""")
    y = s._content_top + Inches(0.1)
    d.stat(s, MARGIN, y, Inches(2.9), val(e1.get("spearman_rho", 0)),
           "Spearman's rho\nit orders answers correctly", GREEN, height=Inches(1.45))
    d.stat(s, MARGIN + Inches(3.15), y, Inches(2.9),
           val(e1.get("quadratic_weighted_kappa", 0)),
           "quadratic weighted kappa\nbut the bands disagree", RUST, height=Inches(1.45))
    d.stat(s, MARGIN + Inches(6.3), y, Inches(2.9),
           f"{e1.get('exact_band_agreement', 0) * 100:.0f}%",
           "exact band agreement\nagainst rho of 0.92", RUST, height=Inches(1.45))
    d.stat(s, MARGIN + Inches(9.45), y, Inches(2.4),
           val(e1.get("separation", {}).get("strong_vs_weak_cohens_d", 0), 1),
           "Cohen's d\nstrong vs weak", GREEN, height=Inches(1.45))

    y += Inches(1.75)
    d.text(s, "The defect, in one line of numbers", MARGIN, y, Inches(6.0),
           Inches(0.36), size=17, colour=INK, bold=True)
    y += Inches(0.5)
    for lvl, col in (("weak", MUTED), ("medium", RUST), ("strong", GREEN)):
        m = lv.get(lvl, {}).get("mean", 0)
        d.text(s, lvl.capitalize(), MARGIN, y, Inches(1.5), Inches(0.34),
               size=16, colour=col, bold=True)
        d.rule(s, MARGIN + Inches(1.7), y + Inches(0.12),
               int((W - 2 * MARGIN - Inches(3.6)) * (m / 100.0)), col,
               thickness=Inches(0.12))
        d.text(s, f"{m:.1f}", W - MARGIN - Inches(1.5), y, Inches(1.4),
               Inches(0.34), size=16, colour=col, bold=True,
               align=PP_ALIGN.RIGHT)
        y += Inches(0.46)

    d.panel(s, MARGIN, Inches(6.02), W - 2 * MARGIN, Inches(0.82), WASH)
    d.text(s, "The \u201cstrong\u201d threshold is 70. Deliberately mediocre answers score "
              "92.8 \u2014 so medium and strong receive the same verdict.",
           MARGIN + Inches(0.42), Inches(6.24), W - 2 * MARGIN - Inches(0.84),
           Inches(0.5), size=17, colour=INK, bold=True)

    # ── 8. Findings 2 and 3 ──────────────────────────────────────────────
    s = d.slide("The rubric does not decompose \u2014 and an honest null result",
                eyebrow="Findings 2 and 3", accent=RUST, notes="""
Two more findings, one of which qualifies a claim I made in my own design
chapter.

Finding two, the halo effect. The judge is explicitly instructed to score four
criteria independently. They correlate at a mean of 0.85, rising to 0.93 for
clarity against relevance.

Some correlation is legitimate \u2014 accurate answers do tend to be complete. But at
this level the four scores are not carrying four pieces of information. The judge
forms one overall impression and spreads it across the criteria. That is the
classic halo effect from the human rating literature, and instructing a model
against a known bias did not remove it.

This matters because I defended the per-criterion breakdown in Chapter 4 as an
explanation mechanism \u2014 telling a candidate which aspect fell short. If the four
marks move together, it communicates one impression four times. Section 8.3
proposes scoring each criterion in a separate call.

Finding three is a null result and I report it as one. Mean spread between the
two passes was 2.2 points. Seventeen of eighteen answers were highly consistent.
The escalation path never fired.

I could have quietly dropped that. Two readings are possible and my data cannot
separate them: either the countermeasure works, or machine-written answers are
just easy to score consistently. The one realistic partial answer I have \u2014 a
candidate admitting they had not used Kubernetes \u2014 drew the widest disagreement
of its session, ten points. That is weak evidence for the second reading, and it
points at where the mechanism would earn its place: the ambiguous middle.
""")
    y = s._content_top + Inches(0.08)
    d.text(s, "Finding 2  ·  Halo effect", MARGIN, y, Inches(5.6), Inches(0.36),
           size=18, colour=RUST, bold=True)
    d.text(s, "Finding 3  ·  Null result", MARGIN + Inches(6.6), y, Inches(5.6),
           Inches(0.36), size=18, colour=BLUE, bold=True)
    y += Inches(0.52)
    d.stat(s, MARGIN, y, Inches(2.6), val(e4.get("mean_inter_criterion_r", 0)),
           "mean correlation between\nthe four rubric criteria", RUST,
           height=Inches(1.4))
    d.stat(s, MARGIN + Inches(2.85), y, Inches(2.6),
           val(e4.get("max_inter_criterion_r", 0)),
           "highest pair\nclarity / relevance", RUST, height=Inches(1.4))
    d.stat(s, MARGIN + Inches(6.6), y, Inches(2.6),
           f"{e2.get('mean_absolute_spread', 0):.1f}",
           "mean spread between\nthe two scoring passes", BLUE, height=Inches(1.4))
    d.stat(s, MARGIN + Inches(9.45), y, Inches(2.4),
           f"{e2.get('consistency_distribution', {}).get('high', 0)}/18",
           "answers rated\nhighly consistent", BLUE, height=Inches(1.4))
    y += Inches(1.72)
    d.text(s, "Instructed to score them independently. It forms one impression "
              "and distributes it \u2014 so the breakdown\nexplains less than the design "
              "claimed.",
           MARGIN, y, Inches(6.0), Inches(0.9), size=15, colour=INK, line=1.28)
    d.text(s, "The escalation path never fired. Reported as a null result, not "
              "dressed up: either the countermeasure\nworks, or written answers are "
              "simply easy to score.",
           MARGIN + Inches(6.6), y, Inches(6.0), Inches(0.9), size=15,
           colour=INK, line=1.28)
    d.panel(s, MARGIN, Inches(6.1), W - 2 * MARGIN, Inches(0.78), WASH)
    d.text(s, "Both findings are defects in my own artefact, found by my own "
              "evaluation. That is the argument for instrumenting it.",
           MARGIN + Inches(0.42), Inches(6.3), W - 2 * MARGIN - Inches(0.84),
           Inches(0.5), size=17, colour=INK, bold=True)

    # ── 9. Critical reflection ───────────────────────────────────────────
    s = d.slide("What I changed, what I removed, and what I cannot claim",
                eyebrow="Critical reflection", accent=PURPLE, notes="""
This is where I depart from the proposal, and I want to be direct about it.

The proposal's headline contribution was a second scorer: a trained classifier
to cross-check the language model. I built it. Then I measured it, and removed
it.

Three reasons. Its training labels came from the same language model it was
meant to check, so agreement between them measures nothing about the world. A
behavioural probe showed it keying on answer length rather than quality. And
adding a second unvalidated scorer produces the appearance of robustness, not
robustness.

Removing it late felt like a retreat \u2014 it was the part that most looked like
machine learning research. What changed my mind was realising I could not defend
it if you asked me why that agreement meant anything. The evidence is preserved
in Appendix E, and reporting the failure turned the weakest part of the project
into one I can actually defend.

Second change: the proposed wav2vec2 emotion classifier became prosodic analysis
in the browser. Every component \u2014 projection, fluency, expression, composure \u2014
can be inspected. An emotion label from a black box cannot. In a project about
explainability, that substitution improves coherence.

Now the limitations, honestly. Eighteen answers is a small corpus. They were
machine-written, not spoken by real candidates. No human rating study, so I have
no external validity check on the judge. No demographic bias testing, because
that needs exactly the data I avoided collecting. And single-session, no
persistence \u2014 it is a research demonstrator.

Against the EU AI Act: transparency and human oversight are well served.
Record-keeping and demographic bias testing are not.
""")
    y = s._content_top + Inches(0.08)
    d.text(s, "Deviations from the proposal, and why", MARGIN, y, Inches(6.0),
           Inches(0.34), size=17, colour=PURPLE, bold=True)
    d.text(s, "What this project cannot claim", MARGIN + Inches(6.7), y,
           Inches(5.6), Inches(0.34), size=17, colour=RUST, bold=True)
    y += Inches(0.5)
    left_items = [
        ("Removed the trained classifier. ",
         "Its labels came from the model it was meant to check, and a probe showed "
         "it keying on answer length. Evidence in Appendix E."),
        ("Replaced the emotion classifier. ",
         "Prosodic analysis in the browser instead \u2014 every component can be "
         "inspected; an emotion label cannot."),
        ("Added self-consistency measurement. ",
         "Not in the proposal. It became the contribution."),
    ]
    right_items = [
        ("18 answers, machine-written. ", "Small corpus, and not real speech."),
        ("No human rating study. ", "So no external check on the judge."),
        ("No demographic bias testing. ",
         "It needs the data this project avoided collecting."),
        ("Single session, no persistence. ", "A demonstrator, not a product."),
    ]
    yl = y
    for lead, body in left_items:
        d.rule(s, MARGIN, yl + Inches(0.14), Inches(0.16), PURPLE,
               thickness=Inches(0.055))
        d.text(s, lead + body, MARGIN + Inches(0.34), yl, Inches(5.8),
               Inches(1.0), size=15, colour=INK, line=1.28)
        yl += Inches(1.0)
    yr = y
    for lead, body in right_items:
        d.rule(s, MARGIN + Inches(6.7), yr + Inches(0.14), Inches(0.16), RUST,
               thickness=Inches(0.055))
        d.text(s, lead + body, MARGIN + Inches(7.04), yr, Inches(5.0),
               Inches(0.8), size=15, colour=INK, line=1.28)
        yr += Inches(0.74)
    d.panel(s, MARGIN, Inches(6.15), W - 2 * MARGIN, Inches(0.72), WASH)
    d.text(s, "Every one of these changes came from a measurement that "
              "contradicted an assumption I had made.",
           MARGIN + Inches(0.42), Inches(6.34), W - 2 * MARGIN - Inches(0.84),
           Inches(0.45), size=17, colour=INK, bold=True)

    # ── 10. Conclusion ───────────────────────────────────────────────────
    s = d.slide("What this project contributes", eyebrow="Conclusion",
                accent=GREEN, notes="""
To close.

Four contributions. A working platform that targets questions from a published
taxonomy and delivers by voice or text. An empirical characterisation of an LLM
judge in a deployed setting, separating rank-order validity from absolute
calibration \u2014 which is where the leniency defect came from. A documented
negative result on comparing a trained classifier against the judge that
supplied its labels. And a reusable harness and test suite, both in the
submission, so every number I have quoted can be regenerated.

The wider claim is deliberately modest. Transparency in automated assessment is
better served by making one scorer accountable \u2014 reporting what it did, how
stable it was, and when a human should step in \u2014 than by adding a second scorer
that cannot itself be validated. Redundancy without independent validation
produces the appearance of robustness.

The strongest evidence for that position is the thing I said at the start: the
evaluation found two real defects in the artefact it was measuring. A system
built to be examined can be shown to be wrong, and then corrected. That is worth
more than a higher headline score from a system nobody can inspect.

Thank you. I am happy to take questions.
""")
    y = s._content_top + Inches(0.12)
    for lead, body in (
        ("A working platform  ",
         "skill-graph question targeting, voice and text delivery, and a report "
         "that shows its working."),
        ("An empirical characterisation  ",
         "of an LLM judge in a deployed setting, separating rank-order validity "
         "from absolute calibration."),
        ("A documented negative result  ",
         "on comparing a trained classifier against the judge that produced its "
         "own training labels."),
        ("A reusable harness and test suite  ",
         "both submitted, so every number quoted here can be regenerated."),
    ):
        d.rule(s, MARGIN, y + Inches(0.15), Inches(0.18), GREEN,
               thickness=Inches(0.06))
        d.text(s, lead + body, MARGIN + Inches(0.4), y, W - 2 * MARGIN - Inches(0.5),
               Inches(0.8), size=17, colour=INK, line=1.3)
        y += Inches(0.86)

    d.panel(s, MARGIN, Inches(5.3), W - 2 * MARGIN, Inches(1.5), WASH)
    d.text(s, "The evaluation found two real defects in the system it was measuring.",
           MARGIN + Inches(0.45), Inches(5.55), W - 2 * MARGIN - Inches(0.9),
           Inches(0.45), size=19, colour=INK, bold=True)
    d.text(s, "A system built to be examined can be shown to be wrong, and then "
              "corrected. That is worth more than a\nhigher headline score from a "
              "system nobody can inspect.",
           MARGIN + Inches(0.45), Inches(6.02), W - 2 * MARGIN - Inches(0.9),
           Inches(0.7), size=16, colour=MUTED, line=1.3)

    return d.save()


if __name__ == "__main__":
    out = build()
    print(f"Written: {out}")
    from pptx import Presentation as _P
    p = _P(out)
    print(f"  slides        : {len(p.slides.__iter__.__self__._sldIdLst)}")
    print(f"  speaker notes : {sum(1 for s in p.slides if s.has_notes_slide and s.notes_slide.notes_text_frame.text.strip())}")
    bad = 0
    for i, s in enumerate(p.slides, 1):
        for sh in s.shapes:
            if sh.left is None:
                continue
            if (sh.left < -10000 or sh.top < -10000
                    or sh.left + (sh.width or 0) > p.slide_width + 10000
                    or sh.top + (sh.height or 0) > p.slide_height + 10000):
                bad += 1
                print(f"  ! slide {i}: {sh.shape_type} bottom={(sh.top+(sh.height or 0))/914400:.2f}")
    print(f"bounds problems: {bad or 'none'}")
