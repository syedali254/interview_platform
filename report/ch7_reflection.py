"""Chapter 7 - Critical Reflection."""

from docx_kit import bullet, h1, h2, h3, para, table
from values import (
    level_mean as _level_mean, probe_cases as _probe, strong_threshold as _strong_threshold,
)


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
    bullet(doc, "Scoring depends on an external commercial model that can be retired without "
                "notice. It happened twice here: the fixture model mid-evaluation, the judging "
                "model shortly after. The artefact has outlived the model it was measured on.",
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
