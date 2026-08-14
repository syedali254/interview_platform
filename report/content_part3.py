"""Chapters 7-8, references and appendices.

Chapter 6 lives in content_ch6.py because it renders from measured data.
"""

from docx_kit import bullet, code, h1, h2, h3, numbered, para, table, GREY
from values import (
    probe_cases as _probe, level_mean as _level_mean,
    strong_threshold as _strong_threshold,
)










# ═════════════════════════════════════════════════════════════════════════
# Chapter 7 — Critical Reflection
# ═════════════════════════════════════════════════════════════════════════

def chapter_7(doc, fig, stats, extra=None):
    h1(doc, "7.  Critical Reflection")

    h2(doc, "7.1  Achievement against objectives")
    para(doc,
         "Table 12 assesses each objective honestly rather than favourably: two were revised "
         "mid-project and one met in a materially different form from the original plan.")
    table(doc,
          ["Objective", "Outcome", "Evidence"],
          [
              ["1  Skill graph and gap analysis", "Met",
               "1,201 ESCO concepts plus two extension taxonomies; four-stage matching cascade; "
               "gap analysis verified by unit tests and the worked example"],
              ["2  Graph-driven question targeting", "Met",
               "Technical questions re-sorted by graph priority before the interview; ordering "
               "asserted by unit test"],
              ["3  Voice and text interview", "Met",
               "Live WebRTC voice interview with provider fallback; text mode producing an "
               "identical transcript; both verified end to end"],
              ["4  Bias-mitigated evaluation pipeline", "Met, revised",
               "Permuted rubric orderings, self-consistency measurement and human escalation, "
               "quantified in Section 6.4. Original dual-track wording revised — see 7.2"],
              ["5  Behavioural integrity detection", "Met, with caveat",
               "Calibrated Isolation Forest with named risk factors; baseline is synthetic and "
               "unvalidated against real anomalous sessions"],
              ["6  Controlled evaluation", "Met, revised",
               "Five experiments reported in Chapter 6, plus a 72-test suite and an end-to-end "
               "verification run. The evaluation identified two real defects — see 7.3"],
          ],
          widths=[4.4, 2.8, 8.4], font_size=9,
          caption="Table 12  Achievement against objectives.")

    h2(doc, "7.2  Deviations from the proposal")
    para(doc,
         "Three deviations from the project proposal require explanation. Each is reported with "
         "the evidence that prompted it.")

    h3(doc, "7.2.1  Removal of the trained-classifier evaluation track")
    para(doc,
         "The proposal's central research contribution was a comparison between two answer "
         "scorers: an LLM-as-Judge and a supervised classifier using Sentence-BERT embeddings and "
         "XGBoost with SHAP explanations. That track was implemented, trained, measured and then "
         "removed. This is the most significant change in the project and the reasoning is set "
         "out in full.")
    para(doc,
         "The first and decisive problem is that the comparison was circular by construction. The "
         "proposal sourced training labels by prompting a language model to generate answers at "
         "pre-defined quality levels, so the classifier's ground truth was the language model's "
         "own opinion. Agreement between the two was guaranteed by the design, and disagreement "
         "would have measured only the representational poverty of six surface features.")
    para(doc,
         "The second problem is that the metric which would have given the comparison meaning was "
         "unobtainable. Agreement with human ratings was the intended anchor, requiring the "
         "two-rater validation set the timeline could not accommodate (Section 3.4). Without a "
         "human gold standard the comparison reduces to two automated scorers disagreeing with no "
         "arbiter.")
    tb = (extra or {}).get("track_b", {})
    top_feature = max((tb.get("feature_importance") or {"semantic_similarity": 0}).items(),
                      key=lambda kv: kv[1])
    pr = _probe(extra)
    para(doc,
         f"The third problem is empirical and settled the matter. Inspection before removal showed "
         f"the model dominated by one feature — semantic similarity at {top_feature[1]:.3f}, more "
         f"than the other five combined — traceable to a data-handling error in which the strong "
         f"answer had been used as its own reference. A behavioural probe made the consequence "
         f"concrete: an answer identical to the reference scored "
         f"{pr.get('Answer identical to the reference', {}).get('score', 0):.1f}, a correct "
         f"paraphrase of it scored {pr.get('Strong paraphrase', {}).get('score', 0):.1f}, below "
         f"the threshold at which the system reports a skill gap, and a deliberately vague answer "
         f"scored {pr.get('Deliberately vague', {}).get('score', 0):.1f}. Appendix E gives the "
         f"full measurements.")
    para(doc,
         "A scorer that classifies a correct answer as a skill gap because the candidate used "
         "their own words is not a usable instrument, and its failure mode would have "
         "systematically penalised exactly the candidates the system is meant to serve. The track "
         "was removed and Objectives 4 and 6 were rewritten around establishing the reliability "
         "of a single scorer.")
    para(doc,
         "The loss should be acknowledged rather than minimised. SHAP feature attribution is gone, "
         "and with it a quantitative form of explanation. What replaces it is more legible to a "
         "recruiter but less rigorous as attribution — and Section 6.6 shows that replacement is "
         "itself weaker than the design assumed.")

    h3(doc, "7.2.2  Substitution of the vocal analysis module")
    para(doc,
         "Module 10 was proposed as a wav2vec2 speech-emotion classifier and implemented instead "
         "as prosodic analysis in the browser. The substitution was deliberate. It requires no "
         "model download, runs offline, keeps all audio on the candidate's device, and every "
         "component of the resulting score — projection, fluency, expression, composure — can be "
         "inspected and explained. An emotion label from a black-box classifier could not be. In "
         "a project whose organising commitment is explainability, the substitution improves "
         "coherence, and it is reported here as a change rather than presented as the original "
         "plan.")

    h3(doc, "7.2.3  Synthetic rather than piloted integrity baseline")
    para(doc,
         "The proposal intended to fit the Isolation Forest baseline on pilot sessions with "
         "volunteers. No human participants were recruited, so the baseline is synthetic: four "
         "hundred sessions drawn from distributions chosen to match the ranges the system "
         "actually measures. This is defensible as a starting point and is honestly labelled in "
         "the code, but it has a real consequence recorded in the next section.")

    h2(doc, "7.3  Limitations")
    para(doc,
         "Two of the following were discovered by the evaluation itself rather than anticipated, "
         "and they are the most consequential defects in the artefact as submitted.")
    bullet(doc, "The judge is systematically lenient. Deliberately partial answers scored a mean "
                f"of {_level_mean(stats, 'medium'):.1f}, comfortably above the "
                f"{_strong_threshold(stats):.0f}-point threshold at which the system reports a "
                "strong answer, so medium and strong answers receive identical verdicts. Rank "
                "ordering is excellent, but the absolute score cannot be read against a fixed "
                "standard. Section 6.3 derives the empirically implied boundaries and explains "
                "why they were not adopted on a sample this size.",
           lead="Miscalibrated verdict thresholds — ")
    bullet(doc, "The four rubric criteria correlate at a mean of 0.85, indicating that the judge "
                "forms one overall impression and distributes it rather than assessing four "
                "properties independently. The per-criterion breakdown is therefore a weaker "
                "explanation mechanism than Chapter 4 claimed.",
           lead="Halo effect across rubric criteria — ")
    bullet(doc, "No answer in the evaluation corpus triggered the low-consistency escalation "
                "path. The mechanism is implemented and operative, but its value in practice is "
                "not demonstrated by these results.",
           lead="Escalation mechanism untested in practice — ")
    para(doc,
         "The remaining limitations were anticipated and constrain how the results should be "
         "read.")
    bullet(doc, "Chapter 6 rests on a modest number of answers. The statistics establish "
                "direction and approximate magnitude; they do not support tight confidence "
                "intervals, and a replication at larger scale could move the values "
                "meaningfully.",
           lead="Sample size — ")
    bullet(doc, "No human raters assessed any answer, so E1 measures agreement with an "
                "intended quality specification — a weaker anchor than expert judgement, and one "
                "blind to any bias the specification and the judge share. The answers were also "
                "machine-written and therefore cleaner than transcribed speech, so performance "
                "on genuine spoken answers is not established.",
           lead="Test data and ground truth — ")
    bullet(doc, "The Isolation Forest has never encountered a real interview, normal or "
                "otherwise. No false-positive rate can be quoted, and the module should be read "
                "as a demonstrated mechanism rather than a validated detector.",
           lead="Unvalidated integrity baseline — ")
    bullet(doc, "Session state is held in a single in-memory dictionary in one server process. "
                "The system supports one interview at a time, does not persist across restarts, "
                "and the transcript endpoint returns the most recent file irrespective of "
                "requester. Multi-tenancy would require authentication, per-session isolation "
                "and durable storage.",
           lead="Single-session architecture — ")
    bullet(doc, "Cross-origin requests are unrestricted, there is no authentication or rate "
                "limiting, and transcripts are written unencrypted to the system temporary "
                "directory. None of this is acceptable for real candidate data. Separately, no "
                "claim is made that scores predict job performance; criterion validity would "
                "require longitudinal outcome data.",
           lead="Security posture and criterion validity — ")
    bullet(doc, "Scoring depends on an external commercial model that can be updated or retired "
                "without notice. One model used during this project was retired mid-evaluation, "
                "which is a concrete instance of the risk.",
           lead="External model dependency — ")

    h2(doc, "7.4  Professional, legal and ethical reflection")
    para(doc,
         "Measured against the EU AI Act's requirements for high-risk systems, the artefact meets "
         "some obligations and fails others. Transparency is well served: every score decomposes "
         "into rubric criteria, a reference answer and a rationale, with the weights published. "
         "Human oversight is well served by design, since the system issues no hiring decision. "
         "Record-keeping is adequate for a demonstrator and inadequate for deployment, with "
         "transcripts stored unencrypted and without retention policy. Bias testing has taken a "
         "first step — Chapter 6 tests two documented model biases — but not demographic "
         "disparity, which needs exactly the human data the project avoided collecting.")
    para(doc,
         "That last point is an uncomfortable circularity worth naming. Avoiding human data "
         "removed the ethical burden of collecting it and simultaneously removed the possibility "
         "of testing for the harm that matters most. A project of this length can reasonably "
         "choose the safer path, but it should not claim the resulting system has been shown to "
         "be fair. It has been shown to be inspectable, which is a precondition for demonstrating "
         "fairness rather than a substitute for it.")
    para(doc,
         "On data protection, in-browser analysis is a genuine data-minimisation measure: no "
         "biometric data leaves the device and only derived scalars are transmitted. It does not "
         "answer the deeper objection that inferring engagement from posture and gaze is "
         "intrusive, and that nervousness and evasion look alike to any such measure. Light "
         "weighting and per-candidate calibration reduce the harm without resolving the "
         "principle.")

    h2(doc, "7.5  Personal reflection")
    para(doc,
         "The most valuable thing I learned on this project was that measuring my own work "
         "changed it more than planning did. Every significant design decision recorded in this "
         "dissertation came from an observation that contradicted an assumption. I assumed "
         "substring matching was a reasonable fallback until I saw “Team Leadership” resolve to "
         "the programming language R. I assumed a speech provider that accepted a connection was "
         "working until the agent went silent mid-interview. I assumed parallelising API calls "
         "would speed up the evaluation until I measured six concurrent calls taking longer than "
         "a hundred sequential ones would have.")
    para(doc,
         "The hardest decision was removing the trained classifier. It was several days of work "
         "and the part of the proposal that most looked like machine learning research, so "
         "deleting it late felt like a retreat. What changed my view was recognising I could not "
         "have defended it: asked why agreement between a model trained on LLM labels and the LLM "
         "itself meant anything, I had no answer. Reporting the failure as a finding turned the "
         "weakest part of the project into one I can defend.")
    para(doc,
         "If I began again I would run the evaluation harness far earlier. I built for most of "
         "the project and measured at the end, so the classifier's defects went undetected for "
         "weeks and the leniency problem in Section 6.2 surfaced too late to address. Measuring "
         "alongside building would have left time to fix rather than only to report.")


# ═════════════════════════════════════════════════════════════════════════
# Chapter 8 — Conclusion
# ═════════════════════════════════════════════════════════════════════════

def chapter_8(doc, fig, stats, extra=None):
    h1(doc, "8.  Conclusion and Future Work")

    h2(doc, "8.1  Conclusions")
    para(doc,
         "This project set out to determine whether an AI interview platform could be made "
         "accountable for the reliability of its own judgements rather than merely confident in "
         "them. A working artefact was produced: an adaptive technical interview by voice or "
         "text, questions targeted by a knowledge graph grounded in a published occupational "
         "taxonomy, and answers scored by a judge instrumented to measure its own stability.")
    para(doc,
         "The central empirical finding was not the one the design anticipated. Measuring the "
         "judge against answers of known quality showed that it ranks them almost perfectly "
         f"(Spearman's rho of {(stats or {}).get('e1_discriminant_validity', {}).get('spearman_rho', 0):.2f}) "
         f"while calibrating them badly: deliberately partial answers averaged "
         f"{_level_mean(stats, 'medium'):.1f} on a scale where the system treats "
         f"{_strong_threshold(stats):.0f} as the threshold for a strong "
         "answer. Ordering is trustworthy; the absolute number is not. A system that publishes "
         "absolute thresholds without validating them against the model's actual output "
         "distribution is making a claim its evidence does not support, and this artefact was "
         "doing exactly that until the evaluation exposed it.")
    para(doc,
         "The second finding qualifies the explainability claim. The four rubric criteria "
         "correlate at a mean of 0.85 despite an explicit instruction to score them "
         "independently, which indicates the judge forms a single impression and distributes it. "
         "Instructing a model against a known cognitive bias does not reliably remove it, and a "
         "per-criterion breakdown that moves as one block explains less than it appears to.")
    para(doc,
         "Positional instability, by contrast, proved small on this corpus and the escalation "
         "path never fired. That null result is reported as such. The mechanism remains "
         "defensible on the literature and is demonstrably operative, and the single realistic "
         "partial answer encountered did draw the widest disagreement of its session — but this "
         "project has not shown it catching real failures at scale.")
    para(doc,
         "The second finding is methodological and arrived by way of a failure. The proposed "
         "comparison between a trained classifier and a language-model judge could not have been "
         "informative, because the classifier's training labels were generated by a language "
         "model. Building it anyway proved instructive: the trained model scored a correct "
         f"paraphrase of its own reference answer at "
         f"{_probe(extra).get('Strong paraphrase', {}).get('score', 0):.0f} out of 100. "
         "The episode is a reminder that "
         "in evaluation research the design of the comparison determines what a result can mean, "
         "and that a comparison which cannot fail informatively is not worth running.")
    para(doc,
         "The wider claim the project supports is modest. Transparency in automated assessment is "
         "better served by making one scorer accountable — reporting what it did, how stable it "
         "was, and when a human should intervene — than by adding a second scorer that cannot "
         "itself be validated. Redundancy without independent validation produces the appearance "
         "of robustness rather than robustness.")
    para(doc,
         "The strongest evidence for that position is that the evaluation found two real defects "
         "in the artefact it was measuring. A system instrumented to be examined can be shown to "
         "be wrong, and then corrected. That property is worth more than a higher headline score "
         "obtained from a system nobody can inspect.")

    h2(doc, "8.2  Contributions")
    numbered(doc, "A working multi-agent interview platform integrating skill-graph question "
                  "targeting, dual-transport interview delivery, privacy-preserving in-browser "
                  "behavioural analysis, and an evaluation pipeline that measures and reports its "
                  "own per-answer reliability rather than presenting every score as confident.")
    numbered(doc, "An empirical characterisation of an LLM judge in a deployed assessment "
                  "setting, separating rank-order validity from absolute calibration and "
                  "quantifying a halo effect across rubric criteria that explicit instruction "
                  "failed to prevent.")
    numbered(doc, "A documented negative result on comparing a trained classifier against a "
                  "language-model judge when the classifier's labels are model-generated, with "
                  "the measurements that demonstrate the failure.")
    numbered(doc, "A reusable evaluation harness and test suite, both part of the submitted "
                  "artefact, allowing every reported result to be regenerated.")

    h2(doc, "8.3  Future work")
    para(doc,
         "Five directions follow directly from the limitations in Section 7.3, ordered by how "
         "much they would strengthen the claims made here.")
    bullet(doc, "Section 6.3 shows the verdict thresholds sit far below where answers "
                "actually land, and that medium and strong answers are not separable in absolute "
                "terms. Recalibrating them against a corpus large enough to avoid overfitting is "
                "the single change that would most improve the system as it stands.",
           lead="Threshold recalibration — ")
    bullet(doc, "Scoring each rubric criterion in a separate call, so that each judgement is "
                "formed without sight of the others, is a direct structural response to the halo "
                "effect measured in Section 6.6. It costs four calls per answer instead of two "
                "and would test whether the correlation is inherent to the answers or induced by "
                "assessing all four together.",
           lead="Criterion isolation — ")
    bullet(doc, "The single most valuable next step for validity is a rating study with trained human "
                "assessors over a corpus of genuine transcribed answers. This would replace the "
                "intended-quality anchor with expert judgement, allow a proper "
                "agreement-with-humans figure, and make it possible to test whether the "
                "consistency signal predicts the cases where humans and the system disagree.",
           lead="Human-rated validation — ")
    bullet(doc, "Collecting sessions from volunteers under both normal and deliberately "
                "anomalous conditions would replace the synthetic baseline and yield a measured "
                "false-positive rate, without which the integrity module cannot responsibly be "
                "deployed.",
           lead="Pilot data for the integrity model — ")
    bullet(doc, "Testing for score disparity across demographic groups requires a dataset the "
                "present project deliberately avoided collecting. Doing so properly, with "
                "consent and ethical approval, is the obligation the EU AI Act imposes and the "
                "one this work has not discharged.",
           lead="Demographic bias testing — ")
    bullet(doc, "The verbosity probe used obvious filler. A stronger test would append "
                "plausible but redundant technical elaboration, which is how verbosity bias "
                "would actually manifest in a real answer.",
           lead="Adversarial verbosity testing — ")
    bullet(doc, "Persistent storage, per-session isolation, authentication and encrypted "
                "transcripts would be prerequisites for any use beyond demonstration.",
           lead="Production hardening — ")

    para(doc,
         "The broader question this project leaves open is whether reliability signalling changes "
         "how people actually use an automated assessment. The system can report that it was "
         "unsure; whether a recruiter under time pressure attends to that or reads past it to the "
         "number is a question about human behaviour that instrumentation cannot answer.")


# ═════════════════════════════════════════════════════════════════════════
# References
# ═════════════════════════════════════════════════════════════════════════

REFERENCES = [
    "Bogen, M. and Rieke, A. (2018) Help Wanted: An Examination of Hiring Algorithms, Equity, "
    "and Bias. Washington, DC: Upturn.",

    "Chen, Y., Li, X. and Zhang, J. (2021) 'A knowledge graph approach to prerequisite "
    "identification in online learning', Computers and Education: Artificial Intelligence, 2(1), "
    "pp. 1–12. doi: 10.1016/j.caeai.2021.100016.",

    "EPIC (2019) Complaint and Request for Investigation, Injunction, and Other Relief: HireVue, "
    "Inc. Washington, DC: Electronic Privacy Information Center.",

    "European Commission (2023) ESCO: European Skills, Competences, Qualifications and "
    "Occupations, version 1.1.1. Available at: https://esco.ec.europa.eu/ "
    "(Accessed: 12 July 2026).",

    "European Commission (2024) Regulation (EU) 2024/1689 of the European Parliament and of the "
    "Council laying down harmonised rules on artificial intelligence (Artificial Intelligence "
    "Act). Official Journal of the European Union, L series, 12 July 2024.",

    "Hevner, A.R., March, S.T., Park, J. and Ram, S. (2004) 'Design science in information "
    "systems research', MIS Quarterly, 28(1), pp. 75–105. doi: 10.2307/25148625.",

    "Hickman, L., Thapa, S., Tay, L., Cao, M. and Srinivasan, P. (2022) 'Text preprocessing for "
    "text mining in organizational research: review and recommendations', Organizational Research "
    "Methods, 25(1), pp. 114–146. doi: 10.1177/1094428120971683.",

    "HireVue (2021) HireVue Leads the Industry with Commitment to Transparent and Ethical Use of "
    "AI: Removal of Visual Analysis from Assessments. Press release, 11 January.",

    "Langer, M., König, C.J. and Papathanasiou, M. (2019) 'Highly automated job interviews: "
    "acceptance under the influence of stakes', International Journal of Selection and "
    "Assessment, 27(3), pp. 217–234. doi: 10.1111/ijsa.12246.",

    "Liu, F.T., Ting, K.M. and Zhou, Z.-H. (2008) 'Isolation Forest', in Proceedings of the 8th "
    "IEEE International Conference on Data Mining. Pisa: IEEE, pp. 413–422. "
    "doi: 10.1109/ICDM.2008.17.",

    "Lundberg, S.M. and Lee, S.-I. (2017) 'A unified approach to interpreting model predictions', "
    "in Advances in Neural Information Processing Systems 30. Long Beach, CA: Curran Associates, "
    "pp. 4765–4774.",

    "Raghavan, M., Barocas, S., Kleinberg, J. and Levy, K. (2020) 'Mitigating bias in algorithmic "
    "hiring: evaluating claims and practices', in Proceedings of the 2020 Conference on Fairness, "
    "Accountability, and Transparency. Barcelona: ACM, pp. 469–481. doi: 10.1145/3351095.3372828.",

    "Reimers, N. and Gurevych, I. (2019) 'Sentence-BERT: sentence embeddings using Siamese "
    "BERT-networks', in Proceedings of the 2019 Conference on Empirical Methods in Natural "
    "Language Processing. Hong Kong: ACL, pp. 3982–3992. doi: 10.18653/v1/D19-1410.",

    "Stureborg, R., Alikaniotis, D. and Suhara, Y. (2024) 'Large language models are inconsistent "
    "and biased evaluators', arXiv preprint arXiv:2405.01724.",

    "Wang, P., Li, L., Chen, L., Cai, Z., Zhu, D., Lin, B., Cao, Y., Liu, Q., Liu, T. and Sui, Z. "
    "(2024) 'Large language models are not fair evaluators', in Proceedings of the 62nd Annual "
    "Meeting of the Association for Computational Linguistics. Bangkok: ACL, pp. 9440–9450.",

    "Ye, J., Chen, J., Liu, Q., Xu, Z. and Wan, X. (2022) 'Generative data augmentation for "
    "commonsense reasoning', in Findings of the Association for Computational Linguistics: EMNLP "
    "2022. Abu Dhabi: ACL, pp. 1008–1025.",

    "Zheng, L., Chiang, W.-L., Sheng, Y., Zhuang, S., Wu, Z., Zhuang, Y., Lin, Z., Li, Z., Li, D., "
    "Xing, E.P., Zhang, H., Gonzalez, J.E. and Stoica, I. (2023) 'Judging LLM-as-a-Judge with "
    "MT-Bench and Chatbot Arena', in Advances in Neural Information Processing Systems 36. New "
    "Orleans, LA: Curran Associates, pp. 46595–46623.",
]


def references(doc):
    h1(doc, "References")
    para(doc, "Referencing follows the BCU Harvard convention.",
         italic=True, colour=GREY, space_after=14)
    for ref in sorted(REFERENCES):
        p = para(doc, ref, align="left", space_after=10)
        p.paragraph_format.left_indent = __import__("docx").shared.Cm(1.0)
        p.paragraph_format.first_line_indent = __import__("docx").shared.Cm(-1.0)


# ═════════════════════════════════════════════════════════════════════════
# Appendices
# ═════════════════════════════════════════════════════════════════════════

def appendices(doc, fig, extra):
    h1(doc, "Appendix A — Module Reference")
    para(doc,
         "Each module, the file implementing it, and its role in the pipeline.")
    table(doc,
          ["Module", "Core technology", "Implementation", "Role"],
          [
              ["M1", "Gemini (JSON-constrained)", "core/agents/cv_agent.py", "Structured profile from CV text or PDF"],
              ["M2", "Gemini (JSON-constrained)", "core/agents/jd_agent.py", "Role requirements from a job description"],
              ["M3", "NetworkX + ESCO v1.1.1", "core/graph/skill_graph.py", "Taxonomy, matching cascade, gap analysis"],
              ["M4", "Gemini + graph traversal", "core/agents/question_agent.py", "Question generation and priority ordering"],
              ["M5", "LiveKit, Deepgram, ElevenLabs", "core/livekit/run_agent.py", "Voice interview agent (WebRTC)"],
              ["M5t", "FastAPI request/response", "core/pipeline/text_interview.py", "Text interview engine"],
              ["M6", "LLM-as-Judge, permuted rubric", "core/evaluator/evaluator.py", "Answer scoring and self-consistency"],
              ["M6a", "Finite state model", "core/graph/state.py", "Per-skill status across the session"],
              ["M7/M8", "MediaPipe Face/Pose Landmarker", "frontend/src/lib/vision.js", "Attention and posture"],
              ["M9", "Isolation Forest (scikit-learn)", "core/evaluator/integrity.py", "Behavioural integrity"],
              ["M10", "Web Audio API prosody", "frontend/src/lib/voice.js", "Vocal delivery"],
              ["M11", "Deterministic weighting", "core/evaluator/fusion.py", "Weighted fusion and recommendation"],
              ["M12", "Structured templates", "core/report/generator.py", "Report assembly and reliability statistics"],
              ["—", "ThreadPool orchestration", "core/pipeline/session_eval.py", "Ties M6, M9, M11 and M12 together"],
              ["—", "Shared prompt", "core/agents/interviewer_prompt.py", "Interviewer instructions for both modes"],
          ],
          widths=[1.6, 4.6, 5.2, 5.1], font_size=8.5)

    h1(doc, "Appendix B — Rubric and Judge Prompt")
    para(doc,
         "The rubric criteria and the scoring rules given to the judge. Reproduced from "
         "core/evaluator/evaluator.py.")
    code(doc,
         "Scoring rules the judge must follow:\n"
         "- Score each of the four criteria independently. A weakness in one\n"
         "  criterion must not drag down the others: an answer can be entirely\n"
         "  accurate yet incomplete, or thorough yet unclear.\n"
         "- Judge the substance, not the phrasing. Different wording that conveys\n"
         "  the same concept is fully credited.\n"
         "- This is speech, not writing. Ignore filler words, false starts and\n"
         "  informal grammar unless they genuinely obscure the meaning.\n"
         "- Do not reward padding. Length is not a proxy for quality.\n"
         "- Clarity and relevance measure how well the candidate communicated a\n"
         "  real answer. If the response contains essentially no substantive\n"
         "  content, clarity and relevance must also be low.\n"
         "- Do not inflate scores to be kind.\n\n"
         "Interpreting the total (the sum of the four criteria):\n"
         "- 70-100: a genuinely strong answer covering the core concepts\n"
         "- 40-69:  real but partial understanding\n"
         "- 0-39:   very weak, largely wrong, or minimal understanding")
    para(doc, "The two rubric orderings used to detect positional sensitivity:")
    code(doc,
         "Ordering A: technical_accuracy -> completeness -> clarity -> relevance\n"
         "Ordering B: clarity -> relevance -> technical_accuracy -> completeness\n\n"
         "Consistency banding on the absolute spread between the two:\n"
         "  spread <  8  ->  high      (reported as a confident score)\n"
         "  spread < 16  ->  moderate\n"
         "  spread >= 16 ->  low       (escalated to human review)")

    h1(doc, "Appendix C — Repository Structure")
    code(doc,
         "InterviewAI/\n"
         "  server.py                     FastAPI application and API surface\n"
         "  core/\n"
         "    llm.py                      Gemini client, JSON repair, usage accounting\n"
         "    config.py                   Thresholds and environment configuration\n"
         "    agents/                     M1, M2, M4, shared interviewer prompt\n"
         "    graph/                      M3 skill graph, M6a state, traversal rules\n"
         "    livekit/                    M5 voice agent and media server launcher\n"
         "    evaluator/                  M6 judge, M9 integrity, M11 fusion\n"
         "    pipeline/                   Text interview engine, session evaluation\n"
         "    report/                     M12 report assembly\n"
         "  experiments/\n"
         "    run_evaluation.py           Evaluation harness (Chapter 6)\n"
         "    results/                    Raw scores and computed statistics\n"
         "    figures/                    Generated result figures\n"
         "  tests/test_core.py            Unit test suite\n"
         "  docs/track-b-rejection.md     Evidence for the removed classifier track\n"
         "  data/esco/                    ESCO taxonomy exports\n"
         "  frontend/src/                 React interface, vision and voice analysis\n"
         "report/\n"
         "  diagrams.py                   Architecture and design figures\n"
         "  build_report.py               This document")

    h1(doc, "Appendix D — Test Suite Summary")
    tests = extra.get("tests", {})
    para(doc,
         f"The suite comprises {tests.get('count', 72)} tests, all passing, covering the "
         f"deterministic components of the pipeline. Components requiring live model inference "
         f"are covered by the end-to-end verification run described in Section 6.7.")
    table(doc,
          ["Area", "Coverage"],
          [
              ["Skill normalisation", "Case, whitespace, punctuation, technical characters, parenthetical stripping"],
              ["Skill matching", "Exact labels, aliases, base forms, fuzzy cutoff, short-label protection, regressions"],
              ["Gap analysis", "Matched / missing / bonus / extra partitioning, match percentage, division-by-zero"],
              ["Question flow", "Graph-priority ordering, section sequence, missing-topic and empty-set handling"],
              ["Transcript pairing", "Alternating turns, consecutive-speaker merging, unanswered questions, empty input"],
              ["Integrity", "Feature derivation, score bounds, risk-factor identification, determinism, gaze allowance"],
              ["Fusion", "Weight sums, arithmetic reconciliation, integrity override, monotonicity, engagement fallback"],
              ["Skill state", "Verification transitions, gap confirmation, averaging, unknown-skill handling"],
              ["Report assembly", "Overall score, worst-first ordering, threshold classification, reliability statistics"],
          ],
          widths=[4.4, 11.1], font_size=9)

    h1(doc, "Appendix E — Evidence for the Rejected Classifier Track")
    para(doc,
         "The measurements referenced in Section 7.2.1, taken from the trained model before it "
         "was removed from the repository. Reproduction instructions are held with the artefact "
         "at docs/track-b-rejection.md.")
    para(doc, "Provenance of the saved model", bold=True, space_after=4)
    para(doc,
         "The model artefact on disk was not produced by the training script that accompanied it. "
         "Hyperparameters disagreed (n_estimators 100 against 200, max_depth 4 against 3, "
         "learning rate 0.1 against 0.08, regularisation unset against 1.0), and the file "
         "predated the script's last modification by one hour and thirty-nine minutes. The change "
         "made in that interval was the correction of the reference-answer data leak, so the "
         "saved model was the output of the defective pipeline. No training metrics file was "
         "produced, so the model's held-out performance was never recorded.")
    para(doc, "Feature importances", bold=True, space_after=4)
    tb = extra.get("track_b", {})
    table(doc,
          ["Feature", "Gain importance"],
          [[name, f"{value:.4f}"]
           for name, value in (tb.get("feature_importance") or {}).items()],
          widths=[7.5, 4.0], font_size=9,
          caption="One feature carries more weight than the other five combined — the signature "
                  "of a model that has learned a training artefact.")
    para(doc, "Behavioural probe", bold=True, space_after=4)
    para(doc,
         "Three answers scored against one fixed reference answer on machine learning.")
    probe = tb.get("behavioural_probe", {})
    pcases = _probe(extra)
    table(doc,
          ["Case", "Semantic similarity", "Model score", "System verdict"],
          [[c["case"], f"{c['semantic_similarity']:.3f}",
            f"{c['score']:.1f} / 100", c["system_verdict"]]
           for c in (probe.get("cases") or [])],
          widths=[6.4, 3.4, 3.0, 2.7], font_size=9)
    para(doc,
         "Two failures are visible. A perfect answer never approaches the 70-point strong "
         "threshold, and a correct paraphrase falls below the 40-point gap threshold. The model "
         f"separates a strong paraphrase from a deliberately weak answer by "
         f"{probe.get('separation_strong_paraphrase_vs_weak', 0):.1f} points while separating a "
         f"verbatim match from a "
         f"{(pcases.get('Strong paraphrase', {}).get('semantic_similarity', 0) * 100):.1f}%-similar "
         f"paraphrase by {probe.get('separation_verbatim_vs_paraphrase', 0):.1f} points: "
         "discriminative power sits almost entirely above similarity 0.9, a region real candidate "
         "answers never reach.")

    h1(doc, "Appendix F — Interface Contracts Between Phases")
    para(doc,
         "Each boundary carries a serialisable payload of fixed shape, which is what allows the "
         "modules to be developed and tested in isolation.")
    table(doc,
          ["Boundary", "Payload", "Consumed by"],
          [
              ["M1 → M3", "Structured profile: skills, experience, education, projects", "Skill graph"],
              ["M2 → M3", "Role requirements: required skills, nice-to-have, level, domain", "Skill graph"],
              ["M3 → M4", "Prioritised topic list: skill, reason, priority", "Question generator"],
              ["M3 → M11", "Gap analysis: match percentage, missing required skills", "Fusion engine"],
              ["M4 → M5", "Ordered question list, flattened by graph priority", "Interview agent"],
              ["M5 → M6", "Transcript: role-tagged utterances with timestamps", "Evaluation pipeline"],
              ["M7/M8/M10 → M9", "Telemetry: attention, posture, prosody, tab switches", "Integrity module"],
              ["M6/M9/M3 → M11", "Component scores on a common 0–100 scale", "Fusion engine"],
          ],
          widths=[3.6, 8.0, 4.0], font_size=9)

    h1(doc, "Appendix G — User Interface and Installation")
    para(doc,
         "The interface is a six-step React single-page application. Each step corresponds to a "
         "phase of the pipeline described in Chapter 4, so a user's progress through the "
         "interface is also a traversal of the architecture.")
    table(doc,
          ["Step", "Screen", "Implementation", "Purpose"],
          [
              ["1", "Upload and parse", "screens/UploadStep.jsx",
               "CV upload (PDF or pasted text) and job description entry; triggers M1 and M2"],
              ["2", "Skill graph", "screens/GraphStep.jsx",
               "Renders the M3 clusters with matched, missing, bonus and extra statuses, and "
               "the gap analysis summary"],
              ["3", "Questions", "screens/QuestionsStep.jsx",
               "Shows the generated question set in the graph-priority order the interview "
               "will follow"],
              ["4", "Setup and mode", "screens/SetupScreen.jsx",
               "Camera and microphone check, and the choice between voice and text interview"],
              ["5a", "Voice interview", "screens/InterviewScreen.jsx",
               "Full-viewport call interface with live transcript, question counter and the "
               "landmark overlay"],
              ["5b", "Text interview", "screens/TextInterviewScreen.jsx",
               "Typed equivalent; records paste events and keystroke telemetry"],
              ["6", "Report", "screens/DashboardScreen.jsx",
               "The M12 report: overall score, per-skill breakdown, per-answer rubric detail, "
               "integrity findings and the fusion arithmetic"],
              ["—", "Landmark overlay", "components/LandmarkOverlay.jsx",
               "Draws the face mesh, gaze points and pose skeleton over the video, so the "
               "candidate can see exactly what is being measured"],
              ["—", "Wizard sidebar", "components/Sidebar.jsx",
               "Step navigation, gated so a step cannot be entered before its inputs exist"],
          ],
          widths=[1.3, 3.4, 4.6, 7.2], font_size=8.5)
    para(doc,
         "Showing the candidate the landmark overlay is a deliberate transparency measure "
         "rather than a decorative one. A system that measures gaze and posture without "
         "revealing that it is doing so would be difficult to defend; rendering the tracking "
         "live makes the observation visible to the person being observed.")
    para(doc, "Installation", bold=True, space_after=4)
    para(doc,
         "A single Windows batch script (run.bat) performs the whole setup: it checks for "
         "Python and Node.js and installs them through winget if absent, creates the virtual "
         "environment, installs Python and npm dependencies, builds the frontend, creates the "
         ".env file from its template and opens it for the API keys, then starts the server. "
         "The LiveKit media server binary is downloaded on first use by "
         "core/livekit/launcher.py, so no manual installation step is required. The system is "
         "then reachable at http://localhost:8000.")
