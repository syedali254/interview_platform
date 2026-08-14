"""Title page, abstract, acknowledgements, declaration, contents and the
lists of figures and tables."""

from docx.shared import Pt
from docx_kit import GREY, HEAD2, h2, page_break, para, toc_entry
from values import probe_cases as _probe_scores


STUDENT_NUMBER = "[STUDENT NUMBER]"


def front_matter(doc, fig, stats=None, extra=None):
    probe = _probe_scores(extra)
    para(doc, space_after=60)
    para(doc, "BIRMINGHAM CITY UNIVERSITY", bold=True, align="center", size=Pt(13))
    para(doc, "Faculty of Computing, Engineering and the Built Environment",
         align="center", size=Pt(11), colour=GREY)
    para(doc, space_after=40)
    para(doc, "An Explainable Multi-Agent AI Interview Platform:",
         bold=True, align="center", size=Pt(18))
    para(doc, "Skill-Graph Question Targeting and a Bias-Mitigated\n"
              "LLM-as-Judge Evaluation Pipeline",
         bold=True, align="center", size=Pt(15), colour=HEAD2)
    para(doc, space_after=44)
    para(doc, "CMP7200 — Individual Master's Project", align="center", size=Pt(12))
    para(doc, "Project Dissertation (Assessment 2)", align="center",
         size=Pt(11), colour=GREY)
    para(doc, space_after=44)
    para(doc, f"Student Number: {STUDENT_NUMBER}", align="center", bold=True, size=Pt(12))
    para(doc, "MSc Computer Science", align="center", size=Pt(11), colour=GREY)
    para(doc, "Academic Year 2025–26", align="center", size=Pt(11), colour=GREY)
    para(doc, space_after=36)
    para(doc, "Module Leader: Samer Bamansoor", align="center", size=Pt(10), colour=GREY)
    para(doc, "September 2026", align="center", size=Pt(10), colour=GREY)

    # ── Abstract ─────────────────────────────────────────────────────────
    page_break(doc)
    h2(doc, "Abstract")
    para(doc,
         "Automated interview platforms now screen millions of candidates each year, but the "
         "systems doing so remain largely opaque: they return a score without an account of how "
         "it was reached. Regulation has caught up with the practice — the EU AI Act classifies "
         "recruitment systems as high-risk and requires transparency, human oversight and bias "
         "testing — yet the tools themselves have been slower to change. Large language models "
         "offer the conversational competence to conduct a structured interview and the fluency "
         "to justify a judgement, but a growing literature shows they are unreliable evaluators: "
         "sensitive to the order in which criteria are presented, and prone to rewarding length "
         "over substance.")
    para(doc,
         "This project designs, builds and evaluates a working interview platform that treats "
         "that unreliability as the central engineering problem rather than an acceptable cost. "
         "The artefact comprises twelve modules across four phases. A candidate's CV and a job "
         "description are parsed into structured profiles and mapped onto a knowledge graph built "
         "from the ESCO occupational taxonomy, which identifies skill gaps and orders the "
         "interview so that genuine gaps are probed before the time budget is spent. The "
         "interview itself runs as a live voice conversation over WebRTC, or as a typed "
         "equivalent producing an identical transcript. Answers are scored by a language model "
         "against a generated reference answer under a four-criterion rubric. Attention, posture "
         "and vocal delivery are measured in the browser, and no video or audio leaves the "
         "candidate's device.")
    para(doc,
         "The evaluation contribution is a reliability instrument built into the scorer. Every "
         "answer is scored twice under permuted rubric orderings; the mean is reported and the "
         "disagreement between the two passes is retained as evidence of that score's stability. "
         "Answers on which the judge disagrees with itself are escalated to a human rather than "
         "reported as confident. Five controlled experiments measure the result: discriminant "
         "validity against known answer-quality levels, a positional-bias ablation, invariance "
         "under paraphrase, rubric criterion independence, and a verbosity probe.")
    para(doc,
         "A trained-classifier evaluation track proposed at the outset was built, measured and "
         "then rejected. Its labels were themselves model-generated, making the intended "
         "comparison circular, and the trained model scored a correct paraphrase of its own "
         f"reference answer at {probe.get('Strong paraphrase', {}).get('score', 0):.0f} out of "
         "100 — below the threshold at which the system reports a skill gap. That rejection, and the evidence behind it, is reported as a finding rather "
         "than concealed as a descoping. The dissertation concludes that transparency in "
         "automated assessment is better served by making a single scorer accountable for its "
         "own reliability than by adding a second scorer that cannot be independently validated.")

    # ── Acknowledgements ─────────────────────────────────────────────────
    page_break(doc)
    h2(doc, "Acknowledgements")
    para(doc,
         "I would like to thank my project supervisor for their guidance across the "
         "design and evaluation stages of this work, and the CMP7200 module team for their "
         "feedback on the project proposal, which shaped the direction the artefact eventually "
         "took. Any errors that remain are my own.")

    h2(doc, "Declaration")
    para(doc,
         "This dissertation is submitted in partial fulfilment of the requirements for the "
         "degree of MSc Computer Science at Birmingham City University. I declare that the work "
         "presented is my own, that all sources have been acknowledged in accordance with the "
         "BCU Harvard referencing convention, and that this work has not been submitted for any "
         "other award. The software artefact described in Chapter 5 was designed and implemented "
         "by me for this project.")

    # ── Contents ─────────────────────────────────────────────────────────
    page_break(doc)
    h2(doc, "Table of Contents")
    contents = [
        ("Abstract", 0, False), ("Acknowledgements", 0, False),
        ("Declaration", 0, False), ("List of Figures", 0, False),
        ("List of Tables", 0, False),
        ("1.  Introduction", 0, True),
        ("1.1  Background and rationale", 1, False),
        ("1.2  Problem statement", 1, False),
        ("1.3  Aim", 1, False),
        ("1.4  Objectives", 1, False),
        ("1.5  Scope and deliverables", 1, False),
        ("1.6  Structure of this dissertation", 1, False),
        ("2.  Literature Review", 0, True),
        ("2.1  Automated interviewing and algorithmic hiring", 1, False),
        ("2.2  Language models as evaluators", 1, False),
        ("2.3  Knowledge graphs for competency modelling", 1, False),
        ("2.4  Fairness, transparency and the regulatory position", 1, False),
        ("2.5  Behavioural integrity and remote assessment", 1, False),
        ("2.6  Synthesis: a conceptual framework", 1, False),
        ("2.7  The gap this project addresses", 1, False),
        ("3.  Research Methodology", 0, True),
        ("3.1  Design Science Research", 1, False),
        ("3.2  How the cycles ran in practice", 1, False),
        ("3.3  Evaluation strategy", 1, False),
        ("3.4  Data strategy", 1, False),
        ("3.5  Alternative approaches considered", 1, False),
        ("3.6  Ethical considerations", 1, False),
        ("3.7  Tools and development environment", 1, False),
        ("4.  System Design", 0, True),
        ("4.1  Architectural overview", 1, False),
        ("4.2  Module decomposition", 1, False),
        ("4.3  Data flow and interface contracts", 1, False),
        ("4.4  Skill graph design", 1, False),
        ("4.5  Question generation and graph traversal", 1, False),
        ("4.6  Interview transport design", 1, False),
        ("4.7  Evaluation pipeline design", 1, False),
        ("4.8  Fusion and reporting design", 1, False),
        ("4.9  Critical assessment of the tools selected", 1, False),
        ("5.  Implementation", 0, True),
        ("5.1  Technology stack and repository structure", 1, False),
        ("5.2  Document understanding (M1, M2)", 1, False),
        ("5.3  The skill graph (M3)", 1, False),
        ("5.4  Question generation and ordering (M4)", 1, False),
        ("5.5  The voice interview agent (M5)", 1, False),
        ("5.6  Text interview mode", 1, False),
        ("5.7  Answer evaluation (M6)", 1, False),
        ("5.8  Presence modules (M7, M8, M10)", 1, False),
        ("5.9  Behavioural integrity (M9)", 1, False),
        ("5.10  Fusion and report assembly (M11, M12)", 1, False),
        ("5.11  Engineering problems encountered", 1, False),
        ("6.  Evaluation and Results", 0, True),
        ("6.1  Experimental design", 1, False),
        ("6.2  Discriminant validity", 1, False),
        ("6.3  Positional-bias ablation", 1, False),
        ("6.4  Paraphrase invariance", 1, False),
        ("6.5  Criterion independence", 1, False),
        ("6.6  Verbosity probe", 1, False),
        ("6.7  System-level verification", 1, False),
        ("6.8  A worked example", 1, False),
        ("6.9  Discussion of results", 1, False),
        ("7.  Critical Reflection", 0, True),
        ("7.1  Achievement against objectives", 1, False),
        ("7.2  Deviations from the proposal", 1, False),
        ("7.3  Limitations", 1, False),
        ("7.4  Professional, legal and ethical reflection", 1, False),
        ("7.5  Personal reflection", 1, False),
        ("8.  Conclusion and Future Work", 0, True),
        ("References", 0, True),
        ("Appendix A — Module reference", 0, False),
        ("Appendix B — Rubric and judge prompt", 0, False),
        ("Appendix C — Repository structure", 0, False),
        ("Appendix D — Test suite summary", 0, False),
    ]
    for text, level, bold in contents:
        toc_entry(doc, text, level=level, bold=bold)

    # ── Lists of figures and tables ──────────────────────────────────────
    page_break(doc)
    h2(doc, "List of Figures")
    figures = [
        "Figure 1  System architecture: four-phase modular design",
        "Figure 2  End-to-end data flow",
        "Figure 3  Skill graph construction and the four-stage matching cascade",
        "Figure 4  Module 6: bias-mitigated LLM-as-Judge evaluation pipeline",
        "Figure 5  Live voice interview: sequence of interactions",
        "Figure 6  Module 11: weighted fusion model",
        "Figure 7  Design Science Research process as executed",
        "Figure 8  Use case model",
        "Figure 9  Deployment and process view",
        "Figure 10  Conceptual framework derived from the literature",
        "Figure 11  Project schedule as delivered, with milestones",
        "Figure 12  Discriminant validity: score distribution by intended quality",
        "Figure 13  Positional-bias ablation and judge self-consistency",
        "Figure 14  Paraphrase invariance across semantically equivalent rewrites",
        "Figure 15  Inter-criterion correlation matrix",
        "Figure 16  Verbosity probe: original versus padded answers",
    ]
    for f in figures:
        toc_entry(doc, f, level=1)

    h2(doc, "List of Tables")
    tables = [
        "Table 1  Strengths and weaknesses of the principal tools selected",
        "Table 4  Rubric criteria and their scoring guidance",
        "Table 5  Fusion component weights",
        "Table 6  Experimental design summary",
        "Table 7  Discriminant validity results by intended quality level",
        "Table 8  Current thresholds against empirically implied boundaries",
        "Table 9  Positional-bias ablation results",
        "Table 10  Paraphrase invariance by question group",
        "Table 11  Per-answer results from the worked example",
        "Table 12  Achievement against objectives",
    ]
    for t in tables:
        toc_entry(doc, t, level=1)
