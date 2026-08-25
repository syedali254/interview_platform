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

def ensure_figures():
    """Draw the architecture diagrams if they are not on disk yet.

    They are build output, so they are not kept in version control. Without
    this a fresh clone could build the report but not the slides.
    """
    expected = [f"fig{n:02d}" for n in range(1, 12)]
    have = {p.stem[:5] for p in FIGURES.glob("*.png")} if FIGURES.exists() else set()
    if not all(e in have for e in expected):
        print("  Rendering architecture figures...")
        import figures
        figures.main()


def build():
    """Ten slides in plain English.

    Order follows what an examiner needs: the problem, what the system does and
    does not do, how it works, what the parts are, what it is built with, the
    one idea that makes it a research project, what testing found, what I would
    change, and what it contributes.

    The wording is deliberately ordinary. Every technical term that has to
    appear is explained on the slide where it appears, because a slide read
    aloud has no footnotes. Every number is read from the results file.
    """
    ensure_figures()
    st = _stats()
    e1 = st.get("e1_discriminant_validity", {})
    e2 = st.get("e2_positional_bias", {})
    e4 = st.get("e4_criterion_independence", {})
    lv = e1.get("by_level", {})
    meta = st.get("meta", {})
    d = Deck()

    # ── 1. Title ─────────────────────────────────────────────────────────
    s = d.slide(number=False, notes="""
Good morning. My project is an AI system that interviews a job candidate, marks
their answers, and explains how it reached every mark.

The one sentence to hold on to: most automated interview tools give you a score
and no explanation. Mine measures how much its own scores can be trusted, and
says so when they cannot.
""")
    d.rule(s, MARGIN, Inches(1.55), Inches(2.2), ACCENT, thickness=Inches(0.06))
    d.text(s, "An AI Interview Platform\nThat Explains Its Own Marking",
           MARGIN, Inches(1.95), W - 2 * MARGIN, Inches(2.0),
           size=40, colour=INK, bold=True, line=1.14)
    d.text(s, "It interviews a candidate, marks the answers, and shows how it\n"
              "reached every mark \u2014 including how sure it is about each one.",
           MARGIN, Inches(3.9), W - 2 * MARGIN, Inches(1.0),
           size=19, colour=MUTED, line=1.3)
    d.rule(s, MARGIN, Inches(5.3), W - 2 * MARGIN, WASH, thickness=Inches(0.02))
    d.text(s, "Abdul Wahab", MARGIN, Inches(5.6), W - 2 * MARGIN, Inches(0.4),
           size=17, colour=INK, bold=True)
    d.text(s, "Student Number: [STUDENT NUMBER]    \u00b7    CMP7200 Individual "
              "Master's Project    \u00b7    Birmingham City University    \u00b7    2025-26",
           MARGIN, Inches(6.05), W - 2 * MARGIN, Inches(0.4), size=13, colour=MUTED)

    # ── 2. The problem ───────────────────────────────────────────────────
    s = d.slide("Companies score interviews with AI. Candidates get a number "
                "and no reason.",
                eyebrow="The problem", accent=RUST, notes="""
Companies now use AI to interview and score people at a scale no human team
could manage. The appeal is obvious: it is fast, and it asks everyone the same
questions.

The trouble is what comes out. A number, and nothing else. No reason, and no way
to argue with it.

This has caused real trouble. In 2019 a privacy group formally complained about
HireVue scoring candidates from their faces. HireVue dropped that in 2021, but
the deeper problem stayed: you still get a score with no explanation.

It also costs companies money. Research shows candidates who think a process was
unfair are less likely to accept the job if offered, which cancels out the time
the company saved.

And the law has caught up. The EU AI Act now treats hiring software as high
risk. Notice what it actually asks for: not a perfect model, which nobody can
build, but that problems be tested for, written down, and checked by a person.
That is a list of requirements, and it is the one I built to.
""")
    y = s._content_top + Inches(0.18)
    for lead, body, col in (
        ("It has caused real trouble.  ",
         "In 2019 a privacy group formally complained about HireVue scoring "
         "candidates from their faces. The feature was dropped in 2021. The "
         "deeper problem stayed.", RUST),
        ("It costs companies money.  ",
         "Candidates who think a process was unfair are less likely to accept "
         "the job \u2014 which cancels out the time the company saved.", ACCENT),
        ("The law has caught up.  ",
         "The EU AI Act now treats hiring software as high risk. It does not "
         "ask for a perfect model. It asks that problems be tested for, written "
         "down, and checked by a person.", BLUE),
    ):
        d.rule(s, MARGIN, y + Inches(0.17), Inches(0.2), col, thickness=Inches(0.06))
        d.text(s, lead + body, MARGIN + Inches(0.42), y, W - 2 * MARGIN - Inches(0.5),
               Inches(0.95), size=18, colour=INK, line=1.32)
        y += Inches(1.12)

    d.panel(s, MARGIN, Inches(5.5), W - 2 * MARGIN, Inches(1.2), WASH)
    d.text(s, "So my question is not \u201ccan AI mark an interview answer?\u201d "
              "It clearly can.\nIt is \u201ccan it be honest about how much to trust "
              "each mark?\u201d",
           MARGIN + Inches(0.45), Inches(5.74), W - 2 * MARGIN - Inches(0.9),
           Inches(0.85), size=19, colour=INK, bold=True, line=1.35)

    # ── 3. Scope ─────────────────────────────────────────────────────────
    s = d.slide("What it does, and what it deliberately does not do",
                eyebrow="Project scope", accent=GREEN, notes="""
Being clear about the boundaries, because the limits are as important as the
features.

What it does. It reads a CV and a job advert. It works out which required skills
the candidate has not shown. It writes an interview and asks about those missing
skills first. It runs that interview by voice or by typing. It marks every
answer and says how confident it is in each mark. And it produces a report where
every number can be traced back to something.

What it does not do, on purpose. It does not hire anyone \u2014 it produces evidence,
a person decides. It knows nothing about who the candidate is: no age, no
gender, no name, no background. It does not predict how well someone would do
the job; it measures how well they answered, which is a different claim, and
proving the first would need years of follow-up data. And it is not a finished
product \u2014 one interview at a time, no login, no database. It is a research
prototype.

If you take one thing from this slide: every one of those limits is a decision I
can defend, not something I ran out of time for.
""")
    y = s._content_top + Inches(0.1)
    d.text(s, "What it does", MARGIN, y, Inches(5.8), Inches(0.4),
           size=19, colour=GREEN, bold=True)
    d.text(s, "What it deliberately does not do", MARGIN + Inches(6.5), y,
           Inches(5.8), Inches(0.4), size=19, colour=RUST, bold=True)
    y += Inches(0.58)
    does = [
        "Reads a CV and a job advert",
        "Works out which required skills are missing",
        "Writes the interview \u2014 missing skills asked first",
        "Runs it by voice, or by typing",
        "Marks every answer, and says how sure it is",
        "Produces a report where every number can be traced",
    ]
    not_does = [
        ("Does not hire anyone. ", "It gives evidence. A person decides."),
        ("Knows nothing about the person. ", "No age, gender, name or background."),
        ("Does not predict job performance. ", "It measures the answer, not the future."),
        ("Not a finished product. ", "One interview at a time. A research prototype."),
    ]
    yl = y
    for item in does:
        d.rule(s, MARGIN, yl + Inches(0.13), Inches(0.16), GREEN, thickness=Inches(0.055))
        d.text(s, item, MARGIN + Inches(0.34), yl, Inches(5.5), Inches(0.5),
               size=17, colour=INK, line=1.25)
        yl += Inches(0.62)
    yr = y
    for lead, rest in not_does:
        d.rule(s, MARGIN + Inches(6.5), yr + Inches(0.13), Inches(0.16), RUST,
               thickness=Inches(0.055))
        d.text(s, lead + rest, MARGIN + Inches(6.84), yr, Inches(5.2), Inches(0.8),
               size=17, colour=INK, line=1.25)
        yr += Inches(0.9)
    d.panel(s, MARGIN + Inches(6.5), Inches(6.05), Inches(5.55), Inches(0.72), WASH)
    d.text(s, "Every limit here is a decision I can defend.",
           MARGIN + Inches(6.85), Inches(6.25), Inches(5.0), Inches(0.4),
           size=16, colour=INK, bold=True)

    # ── 4. How it works ──────────────────────────────────────────────────
    s = d.slide("How it works, start to finish", eyebrow="The solution", notes="""
Here is the whole thing in one picture, left to right, in four stages.

Stage one, prepare. A CV and a job advert go in. The system reads both and maps
the skills onto ESCO \u2014 that is the official EU list of job skills, so when it
says a skill is missing, that skill is a real published thing and not something
the AI invented. It then writes the interview and puts the missing skills first,
because every interview runs out of time and a question at the end never gets
asked.

Stage two, the interview. The candidate picks voice or typing. Both produce
exactly the same transcript, so nothing after this point knows or cares which
one ran. While they answer, the browser watches attention and posture and tone
of voice \u2014 and none of that video or audio ever leaves their computer.

Stage three, marking. Greetings and goodbyes are thrown away so they cannot
drag the average up. Every real answer is marked twice. Timing and tab switches
get checked for anything odd.

Stage four, the report. Everything is combined into one score and a
recommendation, with the working shown.

The design point worth making: each part has one job and a clear input and
output, so any one of them could be replaced without disturbing the rest.
""")
    d.figure(s, "fig01_architecture", top=s._content_top + Inches(0.1),
             height=Inches(4.05))
    y = Inches(6.02)
    for i, (lead, body, col) in enumerate((
        ("1. Prepare  ", "read both documents, find the missing skills, "
                         "write the questions", BLUE),
        ("2. Interview  ", "by voice or by typing \u2014 both give the same "
                           "transcript", GREEN),
        ("3. Mark  ", "score every answer twice, check the session looked "
                      "normal", RUST),
        ("4. Report  ", "combine into a recommendation, and show the working",
         PURPLE))):
        x = MARGIN + i * ((W - 2 * MARGIN) / 4)
        d.text(s, lead, x, y, Inches(1.7), Inches(0.3), size=14, colour=col, bold=True)
        d.text(s, body, x, y + Inches(0.3), (W - 2 * MARGIN) / 4 - Inches(0.25),
               Inches(0.8), size=12, colour=MUTED, line=1.22)

    # ── 5. The thirteen modules ──────────────────────────────────────────
    s = d.slide("Thirteen parts, each with one job",
                eyebrow="The modules", notes="""
Thirteen parts. I will not read them all out \u2014 the point is that each has one
job, and you can see where every piece of the system lives.

The first four prepare the interview: read the CV, read the job advert, compare
them to find the gaps, and write the questions.

The middle group runs and watches the interview: the talking interviewer, the
typed version, the tracker that remembers how each skill is going, and the three
that watch attention, posture and tone of voice through the browser.

The last group does the marking: the judge that scores each answer, the cheating
check, the part that combines everything, and the part that writes the report.

Two things worth noticing. Numbers five and five-T are the same module with a
different way of getting the answer in \u2014 speaking or typing \u2014 which is why the
count is thirteen and not fourteen. And numbers seven, eight and ten all run
inside the candidate's browser, which is how the privacy promise on the last
slide is actually kept.
""")
    mods = [
        ("M1", "Reads the CV", BLUE), ("M2", "Reads the job advert", BLUE),
        ("M3", "Compares them, finds the missing skills", BLUE),
        ("M4", "Writes the questions, gaps first", BLUE),
        ("M5", "Runs the spoken interview", GREEN),
        ("M5t", "Runs the typed interview", GREEN),
        ("M6a", "Tracks how each skill is going", GREEN),
        ("M7", "Watches attention (face)", GREEN),
        ("M8", "Watches posture (body)", GREEN),
        ("M10", "Listens to tone of voice", GREEN),
        ("M6", "Marks each answer, twice", RUST),
        ("M9", "Checks for cheating", RUST),
        ("M11", "Adds everything up", PURPLE),
        ("M12", "Writes the final report", PURPLE),
    ]
    y0 = s._content_top + Inches(0.12)
    half = 7
    for idx, (tag, what, col) in enumerate(mods):
        col_i, row_i = divmod(idx, half)
        x = MARGIN + col_i * Inches(6.3)
        y = y0 + row_i * Inches(0.6)
        d.text(s, tag, x, y, Inches(0.9), Inches(0.36), size=17, colour=col, bold=True)
        d.text(s, what, x + Inches(0.95), y, Inches(4.85), Inches(0.36),
               size=17, colour=INK)
    d.panel(s, MARGIN, Inches(6.05), W - 2 * MARGIN, Inches(0.75), WASH)
    d.text(s, "M5 and M5t are the same interview with a different way of "
              "answering \u2014 which is why it is thirteen parts, not fourteen.",
           MARGIN + Inches(0.42), Inches(6.26), W - 2 * MARGIN - Inches(0.84),
           Inches(0.45), size=16, colour=INK, bold=True)

    # ── 6. Tech stack ────────────────────────────────────────────────────
    s = d.slide("What it is built with", eyebrow="Technology", notes="""
What I actually used, and where the AI is.

Three jobs use a language model: reading the two documents, writing the
questions, and marking the answers. That is Google Gemini 3.6 Flash in every
case. One model, so the behaviour is consistent and there is one thing to test.

The spoken interview uses three services: LiveKit carries the audio call,
Deepgram turns speech into text, and ElevenLabs is the interviewer's voice, with
Deepgram's voice as a backup if that runs out of credit.

The skill matching uses no AI at all, and that is deliberate. ESCO is already a
carefully built list maintained as an EU standard. Learning something over the
top of it would make it harder to explain and would throw away the one property
that makes it defensible \u2014 that every skill traces back to a published standard.

The camera and microphone work uses Google's MediaPipe, running inside the
browser. The cheating check uses a scikit-learn model that trains itself on
first run, because nobody can ethically collect real examples of cheating.

And the app itself is a Python server with a React front end.

The line at the bottom is the one to say out loud: video and audio never leave
the candidate's computer. Only the resulting numbers do.
""")
    rows = [
        ("Reading, writing questions, marking", "Google Gemini 3.6 Flash", BLUE),
        ("Matching skills to a real standard", "ESCO (EU skills list) + NetworkX", BLUE),
        ("Carrying the voice call", "LiveKit", GREEN),
        ("Turning speech into text", "Deepgram Nova-3", GREEN),
        ("The interviewer's voice", "ElevenLabs (Deepgram as backup)", GREEN),
        ("Attention and posture, in the browser", "Google MediaPipe", GREEN),
        ("Tone of voice, in the browser", "Web Audio API", GREEN),
        ("Spotting unusual behaviour", "scikit-learn, trains itself", RUST),
        ("The app itself", "Python + FastAPI, React front end", PURPLE),
        ("Checking it still works", "72 automated tests", PURPLE),
    ]
    y = s._content_top + Inches(0.1)
    for what, tech, col in rows:
        d.rule(s, MARGIN, y + Inches(0.14), Inches(0.16), col, thickness=Inches(0.055))
        d.text(s, what, MARGIN + Inches(0.34), y, Inches(5.6), Inches(0.34),
               size=16, colour=INK)
        d.text(s, tech, MARGIN + Inches(6.2), y, W - MARGIN - Inches(6.4),
               Inches(0.34), size=16, colour=col, bold=True)
        y += Inches(0.42)
    d.panel(s, MARGIN, y + Inches(0.08), W - 2 * MARGIN, Inches(0.72), WASH)
    d.text(s, "The camera and microphone work happens on the candidate's own "
              "computer. Only the resulting numbers are sent.",
           MARGIN + Inches(0.42), y + Inches(0.28), W - 2 * MARGIN - Inches(0.84),
           Inches(0.45), size=16, colour=INK, bold=True)

    # ── 7. The main idea ─────────────────────────────────────────────────
    s = d.slide("The main idea: mark it twice, and keep the disagreement",
                eyebrow="What makes this research", accent=ACCENT, notes="""
This is the idea the whole project rests on, and it is simple.

Research has shown that when you use an AI to mark work, changing the order you
show it the marking criteria changes the score it gives. Most people quote that
as a reason not to trust AI marking.

I read it as an instruction. If the order changes the score, then mark every
answer twice, with the criteria in a different order each time. Averaging cancels
out the effect of the order.

But the average is not the interesting part. The gap between the two marks is.
If it says 82 and then 81, it is sure. If it says 71 and then 45, it is not \u2014
and the average of 58 hides that completely.

So I keep the gap. A big gap means the mark cannot be trusted, and that answer
goes to a human instead of being reported as a confident score.

The claim is deliberately modest. I am not saying the AI is unbiased. I am
saying that when it is unsure, the system admits it.
""")
    y = s._content_top + Inches(0.2)
    d.text(s, "Every answer is marked twice, with the marking criteria shown "
              "in a different order each time.",
           MARGIN, y, W - 2 * MARGIN, Inches(0.5), size=20, colour=INK, line=1.3)
    y += Inches(0.9)
    for lead, body, col in (
        ("The average", "cancels out the effect of the order.", MUTED),
        ("The gap", "is the useful part. 82 then 81 means it is sure. 71 then 45 "
                    "means it is not \u2014 and the average of 58 hides that.", ACCENT),
        ("What happens next", "a big gap sends that answer to a human, instead "
                              "of reporting a confident score.", BLUE),
    ):
        d.rule(s, MARGIN, y + Inches(0.17), Inches(0.2), col, thickness=Inches(0.06))
        d.text(s, lead, MARGIN + Inches(0.42), y, Inches(2.6), Inches(0.4),
               size=18, colour=col, bold=True)
        d.text(s, body, MARGIN + Inches(3.15), y, W - 2 * MARGIN - Inches(3.3),
               Inches(0.9), size=18, colour=INK, line=1.3)
        y += Inches(1.05)
    d.panel(s, MARGIN, Inches(5.85), W - 2 * MARGIN, Inches(0.9), WASH)
    d.text(s, "I am not claiming the AI is unbiased. I am claiming that when it "
              "is unsure, the system says so.",
           MARGIN + Inches(0.45), Inches(6.1), W - 2 * MARGIN - Inches(0.9),
           Inches(0.5), size=19, colour=INK, bold=True)

    # ── 8. What testing found ────────────────────────────────────────────
    s = d.slide("What I found when I tested it \u2014 two faults in my own system",
                eyebrow="Results", accent=RUST, notes="""
I wrote 18 answers to a known quality \u2014 deliberately weak, deliberately average,
deliberately excellent \u2014 and ran five experiments. Here is what came back.

The good news first. It almost never puts a worse answer above a better one. The
agreement score is 0.92 out of 1. As a way of ranking candidates against each
other, it works.

Now the first fault. Look at the averages. Deliberately weak answers get 53.
Deliberately average answers get 92.8. Excellent answers get 98.2. And the system
calls anything 70 or above a strong answer.

So average and excellent get exactly the same verdict. The marks are useful for
comparing two candidates. They are not useful for deciding whether one candidate
is good enough on their own. My report says exactly that, and proposes setting
the thresholds from the scores actually observed instead of assuming the full
range gets used.

The second fault. I ask it to mark four things separately \u2014 accuracy,
completeness, clarity, relevance. They move together at 0.85 out of 1. It forms
one overall impression and spreads it across all four. That is a well-known
effect in human marking too, and telling the model not to do it did not stop it.
This matters because I had defended that four-part breakdown as an explanation
for the candidate. It explains less than I claimed.

And one honest non-result: the safety net for unreliable marks never actually
triggered, because the two marks were only 2.2 points apart on average. I report
that as a null result rather than dressing it up.

The thing I would emphasise: both of these are faults in my own system, found by
my own testing. That is the whole argument for building it this way.
""")
    y = s._content_top + Inches(0.08)
    d.stat(s, MARGIN, y, Inches(2.75), "0.92",
           "how well it ranks answers\n(1.0 would be perfect)", GREEN,
           height=Inches(1.4), value_size=36)
    d.stat(s, MARGIN + Inches(3.0), y, Inches(2.75), f"{lv.get('medium', {}).get('mean', 0):.1f}",
           "what deliberately average\nanswers scored", RUST,
           height=Inches(1.4), value_size=36)
    d.stat(s, MARGIN + Inches(6.0), y, Inches(2.75),
           f"{e4.get('mean_inter_criterion_r', 0):.2f}",
           "how closely the four marking\ncriteria move together", RUST,
           height=Inches(1.4), value_size=36)
    d.stat(s, MARGIN + Inches(9.0), y, Inches(2.85),
           f"{e2.get('mean_absolute_spread', 0):.1f}",
           "average gap between\nthe two markings", BLUE,
           height=Inches(1.4), value_size=36)
    y += Inches(1.68)
    for lead, body, col in (
        ("It ranks well.  ",
         "It almost never puts a worse answer above a better one.", GREEN),
        ("Fault 1 \u2014 it is too generous.  ",
         "The pass mark for a \u201cstrong\u201d answer is 70. Deliberately average "
         "answers scored 92.8 \u2014 so average and excellent get the same verdict.",
         RUST),
        ("Fault 2 \u2014 the four criteria are not separate.  ",
         "It forms one impression and spreads it across all four, so the "
         "breakdown explains less than I had claimed.", RUST),
    ):
        d.rule(s, MARGIN, y + Inches(0.15), Inches(0.18), col, thickness=Inches(0.06))
        d.text(s, lead + body, MARGIN + Inches(0.4), y, W - 2 * MARGIN - Inches(0.5),
               Inches(0.8), size=17, colour=INK, line=1.28)
        y += Inches(0.86)
    d.panel(s, MARGIN, Inches(6.15), W - 2 * MARGIN, Inches(0.72), WASH)
    d.text(s, "Both faults are in my own system, and my own testing found them. "
              "That is the argument for building it this way.",
           MARGIN + Inches(0.42), Inches(6.35), W - 2 * MARGIN - Inches(0.84),
           Inches(0.45), size=17, colour=INK, bold=True)

    # ── 9. Reflection ────────────────────────────────────────────────────
    s = d.slide("What I changed, and what this project cannot claim",
                eyebrow="Looking back honestly", accent=PURPLE, notes="""
Where I departed from my proposal, and I want to be direct about it.

My proposal's headline idea was a second marker: a trained model to check the AI
judge. I built it. Then I measured it, and removed it.

Three reasons. Its training answers came from the same AI it was supposed to be
checking, so the two agreeing tells you nothing about the world. A test showed it
was really keying on how long an answer was, not how good it was. And adding a
second unchecked marker gives the appearance of safety, not safety.

Removing it late felt like going backwards \u2014 it was the part that most looked
like machine learning research. What changed my mind was realising I could not
answer the obvious question: why does that agreement mean anything? Writing it up
as a finding turned the weakest part of the project into one I can defend.

I also replaced a planned emotion detector with a simpler measure of how someone
speaks \u2014 loudness, steadiness, pauses. Every part of that can be inspected. An
emotion label from a black box cannot. In a project about explaining itself, that
swap makes it more consistent, not less.

Now what I cannot claim. Eighteen answers is a small test set. They were written,
not spoken by real people. I have no human markers to compare against. I have not
tested for bias across different groups of people, because that needs exactly the
personal data I chose not to collect. And it runs one interview at a time.

Measured against the EU AI Act: explaining itself and keeping a human in charge,
it does well. Record keeping and bias testing, it does not.
""")
    y = s._content_top + Inches(0.08)
    d.text(s, "What I changed, and why", MARGIN, y, Inches(5.8), Inches(0.34),
           size=18, colour=PURPLE, bold=True)
    d.text(s, "What it cannot claim", MARGIN + Inches(6.6), y, Inches(5.5),
           Inches(0.34), size=18, colour=RUST, bold=True)
    y += Inches(0.52)
    left = [
        ("Removed the second marker. ",
         "Its training answers came from the same AI it was meant to check, so "
         "agreement proved nothing. A test showed it was really measuring length."),
        ("Replaced the emotion detector. ",
         "Now measures how someone speaks \u2014 loudness, steadiness, pauses. Every "
         "part can be inspected; an emotion label cannot."),
        ("Added the double marking. ",
         "Not in the proposal at all. It became the main contribution."),
    ]
    right = [
        ("18 answers, and written not spoken. ", "A small test set."),
        ("No human markers to compare against. ", "So no outside check."),
        ("No bias testing across groups. ",
         "It needs the personal data I chose not to collect."),
        ("One interview at a time. ", "A prototype, not a product."),
    ]
    yl = y
    for lead, rest in left:
        d.rule(s, MARGIN, yl + Inches(0.14), Inches(0.16), PURPLE, thickness=Inches(0.055))
        d.text(s, lead + rest, MARGIN + Inches(0.34), yl, Inches(5.7), Inches(1.0),
               size=15, colour=INK, line=1.28)
        yl += Inches(1.02)
    yr = y
    for lead, rest in right:
        d.rule(s, MARGIN + Inches(6.6), yr + Inches(0.14), Inches(0.16), RUST,
               thickness=Inches(0.055))
        d.text(s, lead + rest, MARGIN + Inches(6.94), yr, Inches(5.1), Inches(0.8),
               size=15, colour=INK, line=1.28)
        yr += Inches(0.76)
    d.panel(s, MARGIN, Inches(6.2), W - 2 * MARGIN, Inches(0.68), WASH)
    d.text(s, "Every one of these changes came from a measurement that proved me "
              "wrong about something.",
           MARGIN + Inches(0.42), Inches(6.38), W - 2 * MARGIN - Inches(0.84),
           Inches(0.42), size=17, colour=INK, bold=True)

    # ── 10. Conclusion ───────────────────────────────────────────────────
    s = d.slide("What this project contributes", eyebrow="In closing",
                accent=GREEN, notes="""
To finish. Four things.

A working platform that aims its questions using a published skills standard,
interviews by voice or typing, and produces a report that shows its working.

A clear measurement of how an AI marker behaves when it is actually deployed \u2014
specifically, that it can rank answers well and still be badly calibrated. That
distinction is where both of my faults came from.

A documented negative result: comparing a trained model against the AI that
supplied its training answers does not tell you anything, and I have the evidence
for why.

And the whole test setup is in the submission, so every number I have shown you
can be produced again.

The wider point is deliberately modest. Being open about one marker \u2014 what it
did, how sure it was, when a human should step in \u2014 is worth more than adding a
second marker nobody has checked. Backup without independent checking looks like
safety without being it.

And the best evidence for that is what I said earlier: my own testing found two
real faults in my own system. Something built to be examined can be shown to be
wrong, and then fixed. That is worth more than a better-looking score from
something nobody can see inside.

Thank you. I am happy to take questions.
""")
    y = s._content_top + Inches(0.15)
    for lead, body in (
        ("A working platform  ",
         "that aims its questions using a published skills standard, interviews "
         "by voice or typing, and shows its working."),
        ("A clear measurement  ",
         "of how an AI marker behaves in practice \u2014 it can rank answers well and "
         "still mark them far too generously."),
        ("A documented negative result  ",
         "checking an AI against a model trained on that same AI's answers proves "
         "nothing, and here is the evidence."),
        ("A test setup anyone can rerun  ",
         "included in the submission, so every number here can be produced again."),
    ):
        d.rule(s, MARGIN, y + Inches(0.15), Inches(0.18), GREEN, thickness=Inches(0.06))
        d.text(s, lead + body, MARGIN + Inches(0.4), y, W - 2 * MARGIN - Inches(0.5),
               Inches(0.8), size=17, colour=INK, line=1.3)
        y += Inches(0.88)

    d.panel(s, MARGIN, Inches(5.35), W - 2 * MARGIN, Inches(1.45), WASH)
    d.text(s, "My own testing found two real faults in my own system.",
           MARGIN + Inches(0.45), Inches(5.58), W - 2 * MARGIN - Inches(0.9),
           Inches(0.45), size=19, colour=INK, bold=True)
    d.text(s, "Something built to be examined can be shown to be wrong, and then "
              "fixed. That is worth more than a\nbetter-looking score from "
              "something nobody can see inside.",
           MARGIN + Inches(0.45), Inches(6.05), W - 2 * MARGIN - Inches(0.9),
           Inches(0.7), size=16, colour=MUTED, line=1.3)

    return d.save()


if __name__ == "__main__":
    out = build()
    print(f"Written: {out}")
    from pptx import Presentation as _P
    p = _P(out)
    slides = list(p.slides)
    print(f"  slides        : {len(slides)}")
    print(f"  speaker notes : {sum(1 for s in slides if s.has_notes_slide and s.notes_slide.notes_text_frame.text.strip())}")
    bad = 0
    for i, s in enumerate(slides, 1):
        for sh in s.shapes:
            if sh.left is None:
                continue
            if (sh.left < -10000 or sh.top < -10000
                    or sh.left + (sh.width or 0) > p.slide_width + 10000
                    or sh.top + (sh.height or 0) > p.slide_height + 10000):
                bad += 1
                print(f"  ! slide {i}: bottom={(sh.top + (sh.height or 0)) / 914400:.2f} "
                      f"right={(sh.left + (sh.width or 0)) / 914400:.2f}")
    print(f"bounds problems: {bad or 'none'}")
