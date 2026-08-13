"""Front matter and Chapters 1-3 of the dissertation."""

from docx.shared import Pt

from docx_kit import (
    bullet, code, figure, h1, h2, h3, numbered, page_break, para, quote,
    rich, table, toc_entry, GREY, HEAD2,
)

STUDENT_NUMBER = "[STUDENT NUMBER]"


# ═════════════════════════════════════════════════════════════════════════
# Front matter
# ═════════════════════════════════════════════════════════════════════════

def front_matter(doc, fig):
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
         "reference answer at 39 out of 100 — below the threshold at which the system reports a "
         "skill gap. That rejection, and the evidence behind it, is reported as a finding rather "
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


# ═════════════════════════════════════════════════════════════════════════
# Chapter 1 — Introduction
# ═════════════════════════════════════════════════════════════════════════

def chapter_1(doc, fig):
    h1(doc, "1.  Introduction")

    h2(doc, "1.1  Background and rationale")
    para(doc,
         "Recruitment has been reshaped by automation over the last decade. Platforms such as "
         "HireVue, Pymetrics and myInterview now conduct or score interviews at a scale no human "
         "panel could match, and the commercial case is straightforward: screening cycles "
         "shorten, cost per candidate falls, and every applicant is asked the same questions in "
         "the same order. Consistency of that kind is genuinely difficult to achieve with human "
         "interviewers, whose judgements vary with fatigue, order effects and rapport.")
    para(doc,
         "The difficulty is that consistency is not accuracy, and neither is fairness. In 2019 the "
         "Electronic Privacy Information Center complained against HireVue over its use of facial "
         "analysis in scoring, arguing the technique was unvalidated and opaque (EPIC, 2019). "
         "HireVue withdrew visual analysis in January 2021 but continued scoring verbal responses "
         "using natural language processing (HireVue, 2021). The underlying problem survived: "
         "candidates received a number and no account of how it was produced.")
    para(doc,
         "Regulation has since moved. Regulation (EU) 2024/1689, the Artificial Intelligence Act, "
         "classifies AI systems used in employment and worker management as high-risk, and "
         "attaches obligations covering transparency, human oversight, record-keeping and bias "
         "testing (European Commission, 2024). A system that cannot explain a score is now a "
         "compliance problem as well as an ethical one.")
    para(doc,
         "The technical ground has shifted too. Language models can hold a structured "
         "conversation and articulate a judgement in language a recruiter can read, which makes "
         "an interview system's reasoning legible in a way a feature-vector classifier's is not. "
         "Whether such a model can be trusted to grade is a harder question, and it is the one "
         "this project takes up.")

    h2(doc, "1.2  Problem statement")
    para(doc,
         "The evidence on language models as evaluators is mixed. Zheng et al. (2023) showed "
         "GPT-4 agreeing with human preference judgements on open-ended tasks at over eighty per "
         "cent, comparable to agreement between human raters. Against that, Stureborg et al. "
         "(2024) documented positional bias — the same model scoring the same content differently "
         "by presentation order — and Wang et al. (2024) found verbosity bias.")
    para(doc,
         "These are not exotic edge cases. In an interview setting they map directly onto "
         "unfairness: a candidate who answers correctly but concisely is penalised relative to "
         "one who answers correctly at length, and the same answer may score differently "
         "depending on an implementation detail the candidate cannot see. A system that inherits "
         "these biases silently is worse than a transparent one that scores less well, because "
         "the failure is undetectable from the output.")
    para(doc,
         "The problem is therefore not whether a language model can score an interview answer — it "
         "plainly can — but whether a system built around one can be made accountable for the "
         "reliability of its scores.")

    h2(doc, "1.3  Aim")
    quote(doc,
          "To design, implement and critically evaluate a multi-agent AI interview platform that "
          "conducts an adaptive technical interview, targets its questioning using a knowledge "
          "graph built from a standard occupational taxonomy, and scores candidate answers "
          "through a language-model judge instrumented to measure, report and act on the "
          "reliability of its own judgements.")

    h2(doc, "1.4  Objectives")
    para(doc,
         "Six objectives operationalise the aim. Objectives 4 and 6 were revised during the "
         "project following the rejection of the trained-classifier evaluation track; the "
         "original wording, the reason for the change and the evidence supporting it are set out "
         "in Section 7.2.")
    numbered(doc, "Construct a skill knowledge graph from the ESCO occupational taxonomy, map "
                  "candidate CV skills and job requirements onto it, and produce a gap analysis "
                  "identifying which required skills the candidate does not evidence.",
             lead="Objective 1. ")
    numbered(doc, "Implement a question generation agent that derives an interview question set "
                  "from the graph and orders it by the priority the gap analysis assigns, so "
                  "that genuine gaps are probed before the time budget is exhausted.",
             lead="Objective 2. ")
    numbered(doc, "Implement a voice interview agent capable of conducting a natural spoken "
                  "conversation with speech recognition and synthesis, together with a typed "
                  "mode producing an identical transcript so that assessment is independent of "
                  "the delivery channel.",
             lead="Objective 3. ")
    numbered(doc, "Design and implement a bias-mitigated LLM-as-Judge evaluation pipeline that "
                  "scores each response against a generated reference answer under a "
                  "four-criterion rubric, and quantify its positional-bias sensitivity and "
                  "self-consistency through repeated measurement under permuted rubric orderings.",
             lead="Objective 4. ")
    numbered(doc, "Implement a behavioural integrity module that detects interview sessions "
                  "whose interaction patterns depart from a defined baseline, and that reports "
                  "the specific behaviours responsible rather than an unexplained flag.",
             lead="Objective 5. ")
    numbered(doc, "Evaluate the system through controlled experiments covering discriminant "
                  "validity against known answer-quality levels, invariance under paraphrase, a "
                  "positional-bias ablation, rubric criterion independence and sensitivity to "
                  "verbosity, and verify the artefact through automated testing.",
             lead="Objective 6. ")

    h2(doc, "1.5  Scope and deliverables")
    para(doc,
         "The deliverable is a working software artefact together with this dissertation. The "
         "artefact runs locally as a single-user research demonstrator: a FastAPI backend, a "
         "React single-page frontend, an embedded WebRTC media server and a voice agent "
         "subprocess. It is deliberately not a production hiring system, and Section 7.3 sets "
         "out what would have to change before it could be one.")
    para(doc,
         "Three boundaries are worth stating at the outset. The system makes no hiring decision, "
         "only evidence for a human to act on. No real candidate data was used at any point; "
         "every experiment in Chapter 6 runs on generated material, for the reasons in Section "
         "3.6. And the platform is evaluated as a measurement instrument, not as a predictor of "
         "job performance — criterion validity against employment outcomes would need a "
         "longitudinal study far beyond a fourteen-week project.")
    figure(doc, fig("fig08_usecase"),
           "Figure 8  Use case model. The decision boundary is deliberate: the system produces "
           "evidence and adjudication requests, and the hiring decision stays with the recruiter.")

    h2(doc, "1.6  Structure of this dissertation")
    para(doc,
         "Chapter 2 reviews the literatures the design draws on and derives a conceptual "
         "framework. Chapter 3 sets out the methodology, Chapter 4 the design and Chapter 5 the "
         "implementation. Chapter 6 reports the evaluation experiments, Chapter 7 reflects "
         "critically on what was achieved and what changed from the proposal, and Chapter 8 "
         "concludes.")


# ═════════════════════════════════════════════════════════════════════════
# Chapter 2 — Literature Review
# ═════════════════════════════════════════════════════════════════════════

def chapter_2(doc, fig):
    h1(doc, "2.  Literature Review")
    para(doc,
         "Four bodies of work bear directly on this project: the empirical literature on "
         "automated interviewing, the fast-moving literature on language models used as "
         "evaluators, work on knowledge graphs for competency modelling, and the fairness and "
         "regulatory literature on algorithmic hiring. A fifth, smaller literature on remote "
         "assessment integrity informs one module. This chapter reviews each, draws out where "
         "they agree and where they conflict, and synthesises them into the conceptual framework "
         "that governs the design.")

    h2(doc, "2.1  Automated interviewing and algorithmic hiring")
    para(doc,
         "Automated hiring tools have moved from keyword screening of CVs to multimodal "
         "assessment of recorded or live interviews. Hickman et al. (2022), reviewing text-mining "
         "practice in organisational research, reach a conclusion that is easy to misread as "
         "endorsement. Automated scoring is more reliable than unstructured human scoring, in the "
         "narrow psychometric sense that it produces the same output for the same input. But "
         "they are careful to separate that from criterion validity, and note that automated "
         "approaches largely lack the decades of accumulated validation evidence that supports "
         "traditional structured interviewing. The distinction matters for this project: a system "
         "can be perfectly consistent and consistently wrong, and consistency alone is not a "
         "defence of a scoring method.")
    para(doc,
         "Langer, König and Papathanasiou (2019) approach the same technology from the "
         "candidate's side, studying applicant reactions to highly automated interviews. They "
         "find that candidates rate automated interviews as markedly less fair than human ones, "
         "and that the effect is strongest where the system provides no feedback or explanation. "
         "The practical consequence they identify is commercially significant: candidates who "
         "perceive a process as unfair are less likely to accept an offer, which erodes the "
         "efficiency gain that motivated the automation. This finding is the direct motivation "
         "for the explanation-first orientation of the present work — the argument for "
         "explainability here is not only ethical but instrumental.")
    para(doc,
         "Together these frame a tension the design must resolve rather than choose between. "
         "Automation buys consistency and scale at the cost of validity evidence and perceived "
         "fairness; a system wanting both must make its reasoning inspectable.")

    h2(doc, "2.2  Language models as evaluators")
    para(doc,
         "The use of a language model as an automated judge was popularised by Zheng et al. "
         "(2023), whose MT-Bench and Chatbot Arena work established that GPT-4's preference "
         "judgements agree with human evaluators at over eighty per cent on open-ended "
         "conversational tasks — a rate comparable to inter-human agreement on the same material. "
         "The result is genuinely important, because it suggests that for tasks with no single "
         "correct answer, a sufficiently capable model can substitute for expensive human "
         "annotation.")
    para(doc,
         "The qualifications arrived quickly, and they are specific rather than general. "
         "Stureborg, Alikaniotis and Suhara (2024) demonstrate that LLM judges are both "
         "inconsistent and biased: presented with the same candidates in a different order, the "
         "same model returns different scores. The bias is positional, arising from the sequence "
         "in which material is presented rather than from its content. Wang et al. (2024) "
         "identify a complementary failure they term verbosity bias, in which longer responses "
         "receive higher scores irrespective of whether the additional length carries additional "
         "substance.")
    para(doc,
         "These findings are frequently cited as reasons not to trust LLM judges. That reading is "
         "too pessimistic, and it misses what makes the findings useful. Both biases are "
         "characterised precisely enough to be countered by construction. If a judge's score "
         "depends on presentation order, then presenting the same material under several orders "
         "and aggregating removes the order-specific component — and, more usefully, the "
         "disagreement between the orderings becomes a direct measurement of how unstable that "
         "particular judgement was. A bias that can be measured can be reported; a bias that is "
         "reported can be acted on. This project treats the Stureborg and Wang results as "
         "specifications for countermeasures rather than as grounds for abandoning the approach.")
    para(doc,
         "One methodological caution in this literature shaped a significant decision here: where "
         "an automated scorer is compared against labels a language model itself produced, "
         "agreement is partly an artefact of the design rather than evidence about the world. "
         "Section 7.2 returns to it.")

    h2(doc, "2.3  Knowledge graphs for competency modelling")
    para(doc,
         "Knowledge graphs represent entities and the relations between them in a form that "
         "supports traversal and inference. Chen, Li and Zhang (2021) apply graph-based models to "
         "prerequisite identification in online learning, showing that traversal over a "
         "structured concept graph can generate coherent learning paths without learned "
         "embeddings. Their result is relevant here in a specific way: where the domain structure "
         "is already documented and reliable, deterministic traversal is both simpler and more "
         "explainable than a learned alternative.")
    para(doc,
         "The ESCO framework (European Commission, 2023) supplies exactly such a structure — a "
         "multilingual taxonomy of skills, competences, qualifications and occupations, "
         "maintained as an EU standard, with over thirteen thousand skill concepts linked by "
         "explicit broader and narrower relations. Using a published taxonomy rather than an "
         "ad hoc skill list has a consequence that matters for a high-risk system: when the "
         "platform reports that a candidate lacks a required skill, the skill is a concept with a "
         "stable identifier in a public standard, not a string the system invented.")
    para(doc,
         "ESCO's limitations became apparent quickly in implementation. Version 1.1.1 predates "
         "much of the modern technology stack and covers soft skills only sparsely, so a "
         "practical system must extend it. Section 5.3 describes the extension taxonomies added "
         "here and, more importantly, the matching failures that arise when free-text skills are "
         "mapped onto a controlled vocabulary carelessly.")

    h2(doc, "2.4  Fairness, transparency and the regulatory position")
    para(doc,
         "Raghavan et al. (2020) audited a set of commercial algorithmic hiring vendors and found "
         "that claims of bias mitigation were common while documented validation protocols were "
         "rare. Bogen and Rieke (2018) had already set out the mechanism by which such systems "
         "encode historical inequity: a model trained on past hiring outcomes learns the "
         "preferences embedded in those outcomes, including the ones nobody would defend "
         "explicitly.")
    para(doc,
         "The regulatory response is now concrete. The EU AI Act places recruitment systems in "
         "the high-risk category and requires transparency, human oversight, technical "
         "documentation and testing for bias (European Commission, 2024). What is notable for a "
         "system designer is that the Act does not demand that a model be unbiased, which would "
         "be unachievable; it demands that bias be tested for, documented, and subject to human "
         "oversight. That is a design brief, and it is met by instrumentation rather than by "
         "aspiration.")
    para(doc,
         "This project addresses fairness at three points. Scoring uses only what the candidate "
         "said, judged against a reference answer for the same question, with no demographic "
         "input and no proxy for one. The rubric is published to the candidate in the report "
         "rather than held internally. And the reliability of every score is measured and "
         "reported alongside it, so that a recruiter can see which judgements are firm and which "
         "are not. None of this guarantees fairness. It makes unfairness detectable, which is a "
         "weaker but achievable claim, and the one the literature supports.")

    h2(doc, "2.5  Behavioural integrity and remote assessment")
    para(doc,
         "Remote assessment raises an integrity problem that predates AI interviewing and has "
         "been studied extensively in online proctoring. The approach adopted here follows the "
         "unsupervised anomaly-detection tradition: rather than attempting to classify cheating "
         "directly, which would require labelled examples of cheating that no institution can "
         "ethically produce, a model of normal interaction is fitted and departures from it are "
         "flagged for review. Isolation Forest (Liu, Ting and Zhou, 2008) suits this framing "
         "because it isolates anomalies by random partitioning and requires no labelled negative "
         "class.")
    para(doc,
         "The literature is clear that such signals are weak individually and easily "
         "misinterpreted: a candidate who looks away is thinking as often as they are consulting "
         "a second screen. The design consequence adopted here is that the module never issues a "
         "verdict without naming the behaviours behind it, and that its output is advisory "
         "context rather than an automatic disqualification.")

    h2(doc, "2.6  Synthesis: a conceptual framework")
    para(doc,
         "The four literatures converge on three failings of current automated hiring tools, each "
         "of which admits a specific design response. Figure 10 sets out the resulting framework.")
    figure(doc, fig("fig10_framework"),
           "Figure 10  Conceptual framework derived from the literature: three documented "
           "failings of automated hiring tools and the design response adopted for each.")
    para(doc,
         "The first failing is opacity. Langer et al. (2019) and EPIC (2019) both document "
         "systems that return scores without accounts, and the AI Act now treats this as a "
         "compliance defect. The response adopted is to surface the full basis of every score: "
         "the four rubric criteria and their individual marks, the reference answer the response "
         "was judged against, and a written rationale.")
    para(doc,
         "The second is susceptibility to systematic bias. Stureborg et al. (2024) and Wang et "
         "al. (2024) identify position and verbosity effects that are invisible in a single "
         "score. The response is to permute the rubric ordering across repeated passes and "
         "average, and to instruct explicitly against rewarding length — then to test whether "
         "either countermeasure works, which Sections 6.3 and 6.6 do.")
    para(doc,
         "The third is reliance on a single unvalidated method. Raghavan et al. (2020) found this "
         "to be the norm commercially. The response adopted here is not a second scorer — for "
         "reasons Section 7.2 explains at length — but self-consistency measurement: the "
         "disagreement between repeated passes over the same answer is retained as evidence about "
         "that score, and answers on which the judge is unstable are escalated to a human instead "
         "of being reported as confident.")
    para(doc,
         "A fourth element sits underneath all three. Grounding the interview in a published "
         "occupational taxonomy means that what is being assessed is a documented competency "
         "rather than whatever the question generator happened to produce, which makes the "
         "assessment auditable at the level of content as well as scoring.")

    h2(doc, "2.7  The gap this project addresses")
    para(doc,
         "The literature establishes that language models can evaluate open-ended responses "
         "competently, and separately that they do so unreliably in characterised ways. What is "
         "largely missing is work that treats the unreliability as a first-class engineering "
         "concern inside a deployed assessment pipeline — measuring it per judgement, reporting "
         "it to the person acting on the score, and routing unstable cases to human "
         "adjudication.")
    para(doc,
         "Most bias-mitigation work in this area is evaluated offline on benchmark datasets, "
         "where the mitigation is applied and aggregate agreement is re-measured. That is "
         "valuable, but it leaves the practitioner without a per-item reliability signal at "
         "inference time. The contribution claimed here is modest and concrete: an interview "
         "assessment pipeline in which every score carries an empirically derived confidence "
         "derived from the judge's agreement with itself, and in which that confidence changes "
         "what the system does.")
