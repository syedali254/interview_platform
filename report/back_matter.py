"""References and appendices.

Excluded from the word count under the assignment brief, which counts only
the main body from Chapter 1 to Chapter 8."""

from docx_kit import GREY, code, h1, para, table
from values import probe_cases as _probe


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
