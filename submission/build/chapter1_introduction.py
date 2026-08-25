"""Chapter 1 - Introduction."""

from document_toolkit import figure, h1, h2, numbered, para, quote


def chapter_1(doc, fig):
    h1(doc, "1.  Introduction")

    h2(doc, "1.1  Background and rationale")
    para(doc,
         "Recruitment has been reshaped by automation. Platforms such as HireVue, Pymetrics and "
         "myInterview now conduct or score interviews at a scale no human panel could match, and "
         "the commercial case is straightforward: screening cycles shorten, cost per candidate "
         "falls, and every applicant is asked the same questions in the same order. Consistency of "
         "that kind is genuinely difficult to achieve with human interviewers, whose judgements "
         "vary with fatigue, order effects and rapport.")
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
         "unfairness: a candidate who answers correctly but concisely is penalised relative to one "
         "who answers correctly at length, and the same answer may score differently depending on "
         "an implementation detail the candidate cannot see. A system that inherits these biases "
         "silently is worse than a transparent one that scores less well, because the failure is "
         "undetectable from the output.")
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
         "Three boundaries are worth stating. The system makes no hiring decision, only evidence "
         "for a human to act on. No real candidate data was used; every experiment in Chapter 6 "
         "runs on generated material, for the reasons in Section 3.6. And the platform is "
         "evaluated as a measurement instrument, not a predictor of job performance — criterion "
         "validity against employment outcomes would need a longitudinal study far beyond a "
         "fourteen-week project.")
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
