"""Chapter 5 - Implementation."""

from document_toolkit import figure, h1, h2, h3, para, table


def chapter_5(doc, fig, extra=None):
    code = (extra or {}).get("code", {})
    h1(doc, "5.  Implementation")

    h2(doc, "5.1  Technology stack and repository structure")
    py = f"{code.get('python', 0):,}" if code else "5,466"
    js = f"{code.get('javascript', 0):,}" if code else "4,078"
    para(doc,
         f"The implementation comprises {py} lines of Python and {js} lines of JavaScript, "
         f"excluding dependencies and generated assets. Both figures are counted from the "
         f"repository when this document is built. The backend is organised by module "
         f"responsibility rather than by technical layer, so the correspondence between the "
         f"design in Chapter 4 and the code is direct: a reader looking for Module 6 finds it "
         f"in core/evaluator/answer_judge.py.")

    if code.get("modules"):
        table(doc, ["", "Module", "Implemented in", "Lines"],
              [[t, n, f, f"{ln:,}"] for t, n, f, ln in code["modules"]]
              + [["", "Total across the thirteen modules", "",
                  f"{code.get('module_total', 0):,}"]],
              caption="Table 5  Each design module and the file implementing it. Line counts "
                      "exclude blank lines and comments, and are measured at build time.",
              widths=[1.0, 4.6, 5.2, 1.4], font_size=9, first_col_bold=True)
    figure(doc, fig("fig09_deployment"),
           "Figure 9  Deployment and process view. Video and audio are analysed on the "
           "candidate's device; only derived numeric features cross the network.")
    para(doc,
         "The deployment is single-process and single-session, appropriate for a "
         "research demonstrator and inadequate for anything else. Section 7.3 states the "
         "consequences explicitly.")

    h2(doc, "5.2  Document understanding (M1, M2)")
    para(doc,
         "CV parsing extracts text from an uploaded PDF using PyMuPDF and passes it to the "
         "language model with a schema-constrained prompt requesting name, contact details, a "
         "summary, skills, experience, education and projects. Job description parsing follows "
         "the same pattern, extracting the role title, required and nice-to-have skills, "
         "responsibilities, seniority level, domain and expected experience.")
    para(doc,
         "The practical difficulty with schema-constrained generation is that models "
         "intermittently return malformed JSON — a trailing comma, an unterminated string, or the "
         "whole object wrapped in a markdown fence. Rather than fail, the client strips fences, "
         "attempts a strict parse, and falls back to a repair pass. This is unglamorous, and it is "
         "the difference between a demonstrator that works and one that fails in front of an "
         "examiner.")
    para(doc,
         "Image-based PDFs yield no extractable text; the system reports this rather than "
         "attempting optical character recognition, which was out of scope.")

    h2(doc, "5.3  The skill graph (M3)")
    para(doc,
         "The graph is constructed from two ESCO CSV exports: the digital skills "
         "collection, providing 1,201 skill concepts with preferred and alternative labels, and "
         "the broader-relations file, providing the hierarchy. Category hubs are synthesised from "
         "the ESCO broader-concept field so that the interface can group skills meaningfully.")
    para(doc,
         "Two supplementary taxonomies extend ESCO where it is thin. A technology extension covers "
         "fifteen categories of modern stack, from cloud platforms and containerisation to testing "
         "and data engineering; a soft-skill extension covers five categories ESCO addresses only "
         "sparsely. Extension labels take precedence in the lookup index, because “Docker” is the "
         "recognisable form of the concept and an ESCO near-synonym is not.")
    para(doc,
         "An alias map of roughly seventy entries handles the abbreviations and spelling variants "
         "that appear on real CVs — k8s, postgres, nodejs, sklearn, ci/cd, amazon web services. "
         "Aliases are indexed separately and can never shadow an exact "
         "preferred-label match, which prevents a curated shortcut from overriding the taxonomy.")
    h3(doc, "5.3.1  The matching failure and its correction")
    para(doc,
         "The first implementation added a substring fallback: if nothing else matched, any "
         "taxonomy label contained in the input string was accepted. This is superficially "
         "reasonable and was harmful. The single-character ESCO concept “R” is a "
         "substring of “Team Leadership”. “Telecommunications engineering” contains "
         "“communication”. The graph rendered without error and the gap analysis reported "
         "confident, specific and wrong conclusions.")
    para(doc,
         "The correction was to remove the fallback entirely and constrain fuzzy matching to "
         "strings of at least six characters at a 0.88 similarity cutoff, so that short labels "
         "must match exactly. Both original failures are now regression tests, asserting that "
         "“Team Leadership” resolves to a leadership concept and that “Communication” does not "
         "resolve to anything containing “telecommunication”.")
    para(doc,
         "The general lesson is one the dissertation returns to in Chapter 7: the dangerous "
         "failures in this system are the silent ones. An exception is visible. A plausible wrong "
         "answer is not.")
    figure(doc, fig("ui2_graph"),
           "Figure 17  The skill graph as built for a real pair of documents. Three of six "
           "required skills were evidenced on the CV; Kubernetes, AWS and Microservices are "
           "reported as gaps against 1,358 matched taxonomy concepts.")

    h2(doc, "5.4  Question generation and ordering (M4)")
    para(doc,
         "The generator receives the prioritised topics and produces a structured question set: "
         "two opening questions, two to three technical questions per high-priority topic, one to "
         "two per medium-priority topic, three behavioural questions in STAR format, and two "
         "closing questions.")
    para(doc,
         "The flattening step re-sorts technical questions by graph priority before the interview "
         "begins, so high-priority gaps are asked first. Questions whose skill the graph does not "
         "recognise sort after graph-derived ones but are not discarded. The unit tests assert this "
         "ordering using a fixture in which the model's emission order is the reverse of the "
         "priority order.")
    figure(doc, fig("ui3_questions"),
           "Figure 18  Generated questions for the same pair of documents. Each technical "
           "question carries the skill it targets and a difficulty; the AWS and Kubernetes "
           "questions are those the graph identified as gaps, which is Objective 2 operating "
           "end to end.")

    h2(doc, "5.5  The voice interview agent (M5)")
    para(doc,
         "The agent runs as a subprocess connected to a LiveKit room, orchestrating speech "
         "recognition, language model inference and speech synthesis. Three implementation "
         "problems are worth recording.")
    h3(doc, "5.5.1  Truncated speech")
    para(doc,
         "Piping the model's token stream directly into the synthesis socket produced audio that "
         "stopped after a few words while the full text continued to appear on screen. Buffering "
         "each complete utterance before synthesising it costs a little latency and buys reliable "
         "audio and control over ordering: the question is published to the interface first and "
         "spoken a fraction of a second later, so a candidate who mishears can read it.")
    h3(doc, "5.5.2  The silent provider")
    para(doc,
         "More subtle was a failure where the agent spoke the greeting then went quiet. The "
         "synthesis quota had been exhausted, and an exhausted quota accepts the connection and "
         "returns no audio — indistinguishable from success unless the frames are inspected. A "
         "startup probe now pushes two characters through the engine and confirms audio comes back "
         "before the interview begins; failing that it falls through to the alternative provider, "
         "and failing both it runs text-only with questions still displayed. The interview degrades "
         "rather than fails.")
    h3(doc, "5.5.3  Process lifecycle on Windows")
    para(doc,
         "Terminating the agent subprocess did not stop it: the Python executable inside a virtual "
         "environment on Windows is a redirector that spawns a second process, so terminating the "
         "parent orphans the child, which stays connected and interferes with the next session. "
         "The fix was to terminate the whole process tree.")

    h2(doc, "5.6  Text interview mode")
    para(doc,
         "Text mode implements the same interview over a request-response transport. The class "
         "holds the transcript, the elapsed clock and the question count, renders a bounded "
         "window of recent history into each prompt, and emits an end marker the server strips "
         "before display.")
    para(doc,
         "Two details matter. The transcript is structurally identical to the voice agent's, so the "
         "assessment pipeline needs no branch on mode; and the minimum question count is clamped "
         "never to exceed the maximum, without which a run configured for three questions would "
         "never reach its own limit. Text mode also enables a signal unavailable in voice: a paste "
         "event in the answer box is recorded and surfaced on the report.")

    h2(doc, "5.7  Answer evaluation (M6)")
    para(doc,
         "The pipeline pairs the transcript into question-and-answer exchanges, classifies each "
         "exchange, scores the substantive ones, and aggregates.")
    para(doc,
         "Pairing is less trivial than it appears. An interviewer may ask a question across two "
         "utterances; a candidate may answer across three. Consecutive turns from the same speaker "
         "are merged, so a question split by a pause still produces one exchange, and trailing "
         "unanswered questions are dropped. Six unit tests cover these cases, including a candidate "
         "speaking before the interviewer.")
    para(doc,
         "Classification labels each exchange as technical, behavioural or logistics in one model "
         "call for the whole session. Logistics exchanges are excluded from scoring, because "
         "grading “Yes, ready” against a technical rubric produces a meaningless zero that drags "
         "down the average. A keyword fallback runs if classification fails, so evaluation never "
         "depends on it succeeding.")
    para(doc,
         "Scoring proceeds as designed in Section 4.7: a reference answer is generated, the answer "
         "judged twice under permuted rubric orderings, the mean taken and the spread retained. "
         "One detail matters. The judge returns four criterion marks and a total, and the "
         "implementation trusts the marks over the model's arithmetic — where the stated total "
         "differs from the sum by more than two points, the sum wins. Models are unreliable at "
         "addition in a way they are not at judgement.")

    h2(doc, "5.8  Presence modules (M7, M8, M10)")
    para(doc,
         "Attention and posture are derived from MediaPipe landmarks in the browser. Attention "
         "uses geometric ratios — the horizontal and vertical offset of the nose from the eye "
         "midpoint, normalised by inter-eye distance — rather than the raw transformation matrix, "
         "because the ratios are stable across cameras and can be justified in writing.")
    para(doc,
         "Both are calibrated against a baseline captured while the candidate settles in, so the "
         "score measures deviation from that person's neutral pose rather than an assumed ideal "
         "that would encode whoever the developer had in mind.")
    para(doc,
         "Vocal delivery replaces the proposed wav2vec2 emotion classifier with prosodic analysis "
         "computed locally: root-mean-square energy, fundamental frequency by bounded "
         "autocorrelation restricted to the human speech range, and voiced-frame ratio. These "
         "aggregate into projection, fluency, expression and composure components. The "
         "substitution is defended in Section 7.2; in short, every component here is inspectable, "
         "which an emotion label is not.")

    h2(doc, "5.9  Behavioural integrity (M9)")
    para(doc,
         "The integrity module derives eight features from session timing and telemetry and scores "
         "them with an Isolation Forest fitted to a synthetic baseline of four hundred normal "
         "sessions.")
    para(doc,
         "Two details determined whether the module was usable. The first is what response time "
         "means: measured from question start to answer completion it is twenty to sixty seconds, "
         "but an initial baseline assumed thinking time of five to fifteen and flagged every "
         "ordinary session as anomalous. The second is calibration — the raw decision function is "
         "not interpretable, so the baseline's first and ninety-ninth percentiles map onto fifty "
         "and one hundred, and the bundle is versioned so an uncalibrated one is refitted rather "
         "than silently reused.")
    para(doc,
         "Finally, the module never returns an adverse verdict without naming a reason. Where the "
         "aggregate pattern is anomalous but no single indicator crossed its threshold, it says "
         "exactly that. A flag a recruiter cannot act on is worse than no flag.")

    h2(doc, "5.10  Fusion and report assembly (M11, M12)")
    para(doc,
         "Fusion is deterministic arithmetic rather than a learned combination. Each component is "
         "normalised to 0–100, multiplied by its weight and summed, with the full breakdown "
         "returned alongside the total so the report can show its working. A unit test asserts the "
         "component contributions reconcile with the reported total, guarding against the weights "
         "and the arithmetic drifting apart.")
    para(doc,
         "Engagement is assembled from whichever presence signals were actually captured, "
         "reweighted across the available sources, and marked as measured or estimated. A browser "
         "that could not run MediaPipe still yields a complete report, flagged honestly rather "
         "than silently defaulted.")
    para(doc,
         "Report assembly collects everything into one structure: overall score and "
         "recommendation, per-skill breakdown sorted worst first so gaps surface at the top, "
         "per-answer detail with the rubric breakdown and reference answer, the integrity "
         "assessment with its risk factors, and session-level judge reliability statistics.")

    h2(doc, "5.11  Engineering problems encountered")
    para(doc,
         "Beyond those already described, three further problems are worth recording because each "
         "changed a design decision rather than merely costing time.")
    para(doc,
         "Interruption handling was initially disabled, on the reasoning that a candidate should "
         "not talk over the interviewer. In testing this made the framework discard answers from "
         "candidates who began replying while the question was still being spoken — natural "
         "conversational behaviour. Interruptions were re-enabled with a minimum duration and word "
         "count. Live use showed that was still too permissive: a pause for thought ended the turn "
         "early, and the rest of the answer, arriving mid-reply, cut the question off. Two "
         "apparent faults, one cause — timings suited to conversation, not to interview answers. "
         "The windows were lengthened, and the agent now resumes when an apparent interruption "
         "produces no speech.")
    para(doc,
         "Answer-length thresholds initially skipped very short replies. This silently dropped "
         "genuine non-answers such as “I have not used that” — exactly the evidence a recruiter "
         "needs. The threshold now excludes only replies too short to carry assessable content.")
    para(doc,
         "Finally, the endpoint's concurrency behaviour proved counter-intuitive: one sequential "
         "call completed in 2.3 seconds while six issued concurrently took 273.8 seconds in "
         "total. The harness was changed to run serially, and the measurement is recorded in the "
         "code so the parallelism is not naively reintroduced.")
