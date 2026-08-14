"""Chapters 3-5: Methodology, System Design, Implementation."""

from docx_kit import (
    bullet, figure, h1, h2, h3, para, table,
)


# ═════════════════════════════════════════════════════════════════════════
# Chapter 3 — Research Methodology
# ═════════════════════════════════════════════════════════════════════════

def chapter_3(doc, fig):
    h1(doc, "3.  Research Methodology")

    h2(doc, "3.1  Design Science Research")
    para(doc,
         "This project builds an artefact and then studies it, which places it squarely in the "
         "Design Science Research tradition set out by Hevner et al. (2004). DSR is concerned "
         "with the creation and evaluation of IT artefacts that address identified organisational "
         "problems, and it distinguishes itself from behavioural research by treating the "
         "artefact itself as the vehicle of the contribution. That fits the present work: the "
         "claim being made is not about how people behave in interviews but about whether a "
         "particular construction of an assessment system can be made accountable for its own "
         "reliability.")
    para(doc,
         "Hevner's framework is organised around two cycles. The relevance cycle grounds the work "
         "in a real problem environment, here the documented opacity of commercial hiring tools "
         "and the transparency obligations the EU AI Act now imposes. The rigour cycle grounds it "
         "in an existing knowledge base — the literature reviewed in Chapter 2 — and returns "
         "findings to it. Between them sits the design cycle, in which the artefact is built, "
         "evaluated and refined. Figure 7 shows how those cycles ran in this project.")
    figure(doc, fig("fig07_dsr"),
           "Figure 7  The Design Science Research process as executed, showing three "
           "build–evaluate–refine cycles and the design change each produced.")
    para(doc,
         "A purely experimental design was rejected because there was no system to hold fixed at "
         "the outset. It does describe Chapter 6 accurately, though: once the artefact "
         "stabilised, evaluation proceeded experimentally. DSR governs the project; controlled "
         "experiment governs its evaluation.")

    h2(doc, "3.2  How the cycles ran in practice")
    para(doc,
         "Three design cycles are worth recording, because in each the evaluation stage produced "
         "a measurement that forced a change rather than confirming a decision already taken.")
    para(doc,
         "The first concerned skill matching: a substring fallback mapped “Team Leadership” onto "
         "the ESCO concept “R” and “Communication” onto “telecommunications engineering”, "
         "silently, while the gap analysis reported confident nonsense. The second concerned "
         "interview delivery, where the voice agent fell silent mid-session because an exhausted "
         "synthesis quota returns no audio while still accepting the connection. The third "
         "concerned answer evaluation, where measuring a trained second scorer exposed both a "
         "data leak in its training set and a circularity in the comparison it was meant to "
         "support, and ended the track. Sections 5.3.1, 5.5.2 and 7.2 give the evidence and the "
         "resulting design changes in full.")

    h2(doc, "3.3  Evaluation strategy")
    para(doc,
         "Hevner et al. (2004) enumerate five families of DSR evaluation method. Three are used "
         "here, and each supports a different claim.")
    bullet(doc, "controlled experiments on the evaluation pipeline, reported in Chapter 6. These "
                "support claims about how the scorer behaves — whether it separates good answers "
                "from poor ones, whether presentation order moves it, whether paraphrase does.",
           lead="Experimental — ")
    bullet(doc, "an automated unit test suite covering the deterministic components, and an "
                "end-to-end run exercising the full pipeline against a synthetic candidate. These "
                "support claims about correctness, not quality.",
           lead="Testing — ")
    bullet(doc, "a worked example carried through the whole system in Section 6.8, which "
                "demonstrates utility in a way that aggregate statistics cannot.",
           lead="Descriptive — ")
    para(doc,
         "What is deliberately absent is criterion validity: no claim is made that scores predict "
         "job performance. Establishing that would require tracking hired candidates over months "
         "and is beyond any fourteen-week project. The evaluation treats the system as a "
         "measurement instrument and asks whether the instrument is stable and discriminating — "
         "necessary conditions for validity, not sufficient ones.")

    h2(doc, "3.4  Data strategy")
    para(doc,
         "All evaluation data is generated rather than collected from people. This was a "
         "deliberate choice with a cost attached, and the reasoning should be stated plainly.")
    para(doc,
         "The proposal envisaged a validation set of roughly two hundred interview answers "
         "labelled by two independent human raters, plus pilot sessions with volunteers to fit "
         "the behavioural baseline. Both require ethical approval and participant recruitment. "
         "Within the project timeline, pursuing approval would have consumed the weeks that the "
         "implementation needed, and a rushed study with a handful of untrained raters would have "
         "produced a gold standard too noisy to support the agreement statistics it was meant to "
         "anchor.")
    para(doc,
         "The strategy adopted instead uses answers written to a specified quality level as the "
         "reference standard: for each question a strong, medium and weak answer, whose intended "
         "levels form an ordinal ground truth. This is weaker than human rating in one specific "
         "way — it measures agreement with an intended level, not with expert judgement — but it "
         "remains a real and falsifiable test. A scorer that cannot separate deliberately strong "
         "answers from deliberately weak ones has failed regardless of what a human rater would "
         "say.")
    para(doc,
         "Two measures reduce the circularity risk. The fixtures are generated by a different "
         "model from the one that grades them, so the judge is not simply recognising its own "
         "prose. And the reference answer each response is scored against is generated "
         "independently of the candidate answers, rather than being one of them — a precaution "
         "whose absence caused a measurable failure in the rejected classifier track, described "
         "in Section 7.2.")

    h2(doc, "3.5  Alternative approaches considered")
    para(doc,
         "Four significant alternatives were considered and rejected, and the reasoning is set "
         "out here rather than left implicit.")
    para(doc,
         "A trained supervised classifier as a second scoring track was the original plan and is "
         "treated at length in Section 7.2. In summary, it was built, measured, found to rest on "
         "a circular comparison, and removed.")
    para(doc,
         "A fine-tuned transformer classifier trained end to end on answer text would likely "
         "outperform hand-crafted features, but was rejected on explainability grounds: a "
         "fine-tuned encoder offers no account of an individual judgement a non-specialist can "
         "read. A graph neural network over the skill graph was rejected because ESCO is already "
         "a curated hierarchy with explicit relations — learning embeddings over a documented "
         "structure adds opacity while removing the property that makes the graph useful in a "
         "high-risk system, that every edge traces to a published standard. A custom speech "
         "recognition model was rejected immediately: commercial recognition is near human parity "
         "for English, and building a worse one would consume the project without touching the "
         "research question.")

    h2(doc, "3.6  Ethical considerations")
    para(doc,
         "No human participants were involved in this project, and no ethical approval was "
         "therefore sought. That is a limitation, discussed in Section 7.3, but it is also a "
         "deliberate reduction of ethical exposure: no personal data was collected, stored or "
         "processed at any stage.")
    para(doc,
         "Several ethical commitments are nonetheless built into the artefact. The system issues "
         "no hiring decision, only evidence for a person to act on. Video and audio are analysed "
         "in the browser and never transmitted, a data-minimisation measure in the sense the GDPR "
         "intends. The integrity module never returns an adverse verdict without naming the "
         "behaviours behind it, so a candidate can contest a finding. And scoring uses only what "
         "the candidate said, with no demographic input or proxy for one.")
    para(doc,
         "One tension deserves acknowledgement rather than resolution. Behavioural monitoring of "
         "any kind is intrusive, and a system that measures gaze direction and posture is making "
         "inferences about a person from signals they cannot fully control. Nervousness reads "
         "much like evasion. The mitigation adopted — weighting these signals lightly, "
         "calibrating them against the candidate's own neutral pose rather than an assumed ideal, "
         "and reporting them as context rather than as findings — reduces the harm but does not "
         "eliminate the objection. A production deployment would need explicit informed consent "
         "and a genuine opt-out.")

    h2(doc, "3.7  Tools and development environment")
    para(doc,
         "The backend is Python 3.11 with FastAPI; the frontend is React with Vite. NetworkX "
         "holds the skill graph, LiveKit carries real-time audio, and MediaPipe Tasks Vision runs "
         "landmark detection in the browser. Gemini provides language model inference, Deepgram "
         "speech recognition, and ElevenLabs synthesis with Deepgram as fallback. scikit-learn "
         "supplies the Isolation Forest, SciPy the statistical tests, Matplotlib the figures. "
         "Version control is Git and testing is pytest. Section 4.9 assesses the significant "
         "choices critically rather than merely listing them.")

    h2(doc, "3.8  Project execution")
    para(doc,
         "Figure 11 shows the schedule as delivered. Two departures from the plan submitted with "
         "the proposal are visible. Dissertation writing began in week 7 and ran alongside "
         "implementation rather than following it, which proved essential — the engineering "
         "decisions recorded in Chapter 5 were written up while the reasoning was still fresh. "
         "And the trained-classifier track occupies weeks 11 and 12 as a build-and-reject cycle "
         "rather than the build-and-compare originally scheduled.")
    figure(doc, fig("fig11_gantt"),
           "Figure 11  Project schedule as delivered, with the four milestones marked.")


# ═════════════════════════════════════════════════════════════════════════
# Chapter 4 — System Design
# ═════════════════════════════════════════════════════════════════════════

def chapter_4(doc, fig):
    h1(doc, "4.  System Design")

    h2(doc, "4.1  Architectural overview")
    para(doc,
         "The system is decomposed into twelve modules across four sequential phases. The "
         "decomposition is not decorative: each module declares its input and output, "
         "communicates only through those, and can be developed, deferred or replaced without "
         "disturbing its neighbours — the property that allowed a whole evaluation track to be "
         "removed late in the project without touching the rest.")
    figure(doc, fig("fig01_architecture"),
           "Figure 1  System architecture. Twelve modules across four sequential phases, with "
           "the inter-phase data dependencies shown explicitly.")
    para(doc,
         "Phase 1 turns unstructured documents into a targeted interview plan, Phase 2 conducts "
         "and observes the interview, Phase 3 assesses it, and Phase 4 reports. The phases are "
         "sequential in data dependency but not in development.")
    para(doc,
         "One decision visible in the figure deserves comment. The skill graph feeds both the "
         "question generator in Phase 1 and the fusion engine in Phase 4, shown as the long-range "
         "dependency on the left: it is not merely a preparation step, since CV-to-role match "
         "contributes a fifth of the final score in its own right.")

    h2(doc, "4.2  Module decomposition")
    para(doc,
         "All thirteen modules were implemented. Appendix A lists each with its technology, its "
         "implementing file and its role. One deviates from the proposal: M10 was specified as a "
         "wav2vec2 emotion classifier and is implemented as browser-side prosodic analysis, for "
         "the reasons given in Section 7.2.2.")

    h2(doc, "4.3  Data flow and interface contracts")
    para(doc,
         "Figure 2 traces a candidate's material through the system, from an uploaded CV to a "
         "scored recommendation.")
    figure(doc, fig("fig02_dataflow"),
           "Figure 2  End-to-end data flow. Every arrow is a serialisable payload with a fixed "
           "shape, which is what allows modules to be tested in isolation.")
    para(doc,
         "The full interface contracts are tabulated in Appendix F. The most important is the "
         "transcript: a list of role-tagged utterances with timestamps. Both interview modes "
         "produce exactly this structure, which is why the assessment phase contains no branch on "
         "interview mode anywhere in its implementation.")

    h2(doc, "4.4  Skill graph design")
    para(doc,
         "The skill graph is a directed graph whose nodes are skill concepts and category hubs, "
         "and whose edges are containment and the real broader-than relations published in ESCO. "
         "Candidate skills and role requirements are resolved onto it, and the set operations "
         "between the two populations yield the gap analysis.")
    figure(doc, fig("fig03_skillgraph"),
           "Figure 3  Skill graph construction and the four-stage matching cascade.")
    para(doc,
         "The design problem is not graph construction, which is mechanical, but mapping free "
         "text onto a controlled vocabulary. A CV says “k8s” where ESCO says “Kubernetes”; an "
         "advertisement says “strong communicator” where the taxonomy has “Communication”. "
         "Resolving these requires tolerance, whose failure mode is a false match — and a false "
         "match here produces a confident, specific and wrong claim that a candidate lacks a "
         "skill.")
    para(doc,
         "The cascade in Figure 3 is therefore deliberately conservative. Exact preferred-label "
         "matches are tried first, then curated aliases, then the base form of parenthesised ESCO "
         "labels so that “Python” reaches “Python (computer programming)”. Fuzzy matching is the "
         "last resort and is restricted to strings of at least six characters, at a similarity "
         "cutoff of 0.88. Short labels must match exactly or not at all, because fuzzy matching "
         "on two-character strings is meaningless — this is precisely how “Team Leadership” "
         "previously reached the ESCO concept “R”.")
    para(doc,
         "When nothing matches safely, the skill becomes its own node rather than being forced "
         "onto a neighbour. These unmatched nodes share one namespace across the CV and the job "
         "description, so a technology ESCO has never heard of still registers as a match when it "
         "appears on both sides. Refusing to guess is treated as the correct behaviour, not a "
         "shortcoming.")

    h2(doc, "4.5  Question generation and graph traversal")
    para(doc,
         "The gap analysis produces a prioritised topic list: required skills the candidate does "
         "not evidence are high priority, skills claimed on the CV are medium priority and are "
         "probed to verify depth, and nice-to-have skills the candidate does hold are low "
         "priority. The question generator receives this list and produces a structured set with "
         "opening, technical, behavioural and closing sections.")
    para(doc,
         "The traversal step matters more than it first appears. A language model asked to "
         "generate questions returns them in whatever order it composed them, which correlates "
         "with nothing. Every interview has a time budget, and any question that falls off the "
         "end of that budget is a question never asked. The system therefore re-sorts the "
         "technical questions by the priority the graph assigned to their skill before the "
         "interview begins, so the budget is spent on genuine gaps first. This is the concrete "
         "content of Objective 2: question targeting is driven by the graph, not by the order the "
         "model happened to emit.")

    h2(doc, "4.6  Interview transport design")
    para(doc,
         "Two delivery modes are supported. The voice mode conducts a spoken conversation over "
         "WebRTC; the text mode conducts the same interview as typed exchanges. They share the "
         "interviewer's instructions, the question bank, the question and time budgets, and the "
         "rules for redirecting an off-topic candidate and for closing the session. Only the "
         "transport differs.")
    figure(doc, fig("fig05_sequence"),
           "Figure 5  Sequence of interactions in a live voice interview, including the "
           "pre-warm phase that removes process start-up from the candidate's critical path.")
    para(doc,
         "Keeping one set of interviewer instructions shared between the modes is a design "
         "decision with a clear rationale: two copies would diverge the first time either was "
         "tuned, and the report would then be comparing candidates assessed under subtly "
         "different conditions. The mode-specific difference is confined to a single note about "
         "delivery — spoken replies must be short because the candidate is listening rather than "
         "reading.")
    para(doc,
         "The pre-warm phase shown boxed in Figure 5 addresses a latency problem rather than a "
         "functional one. Starting the media server and the agent subprocess costs roughly twelve "
         "seconds, most of it importing the agent framework and its plugins. Paid after the "
         "candidate presses “Begin Interview”, that is twelve seconds of silence at the most "
         "anxious moment of the session. Moving it to the device-setup screen, while the "
         "candidate is checking their camera, hides it entirely.")

    h2(doc, "4.7  Evaluation pipeline design")
    para(doc,
         "Module 6 is the centre of the project's contribution, and its design follows directly "
         "from the conceptual framework in Section 2.6.")
    figure(doc, fig("fig04_evaluation_pipeline"),
           "Figure 4  The evaluation pipeline, from a transcribed answer through to a verdict "
           "and, where the two passes disagree, an escalation.")
    para(doc,
         "Each answer is first paired with a reference answer generated for the same question, "
         "giving the judge a concrete standard rather than an abstract sense of quality. The "
         "reference is framed as what a strong answer covers, not a script to reproduce, because "
         "scoring by similarity to a fixed text penalises candidates who are right in their own "
         "words.")
    para(doc,
         "The answer is then scored twice against a four-criterion rubric, with the criteria "
         "presented in two different orders. Table 4 gives the criteria and the guidance attached "
         "to each.")
    table(doc,
          ["Criterion", "Marks", "Scoring guidance"],
          [
              ["Technical accuracy", "0–25",
               "Deduct only for statements that are wrong or misleading. Omissions belong to completeness."],
              ["Completeness", "0–25",
               "Deduct only for genuinely important missing concepts. Brevity is not penalised."],
              ["Clarity", "0–25",
               "Is the answer well structured and easy to follow?"],
              ["Relevance", "0–25",
               "Does it address the question actually asked?"],
          ],
          widths=[3.6, 1.8, 10.2],
          caption="Table 4  Rubric criteria and scoring guidance. The separation of accuracy from "
                  "completeness is deliberate: a short answer containing nothing incorrect should "
                  "score highly on the former and may legitimately score lower on the latter.")
    para(doc,
         "Averaging the two passes cancels the component of the score attributable to "
         "presentation order. The more useful output, however, is the disagreement between them. "
         "A judge that returns 82 and 81 for the same answer is stable; one that returns 71 and "
         "45 is not, and the mean of 58 conceals that instability entirely. The spread is "
         "therefore retained, banded into high, moderate and low consistency, and answers in the "
         "low band are flagged for human review rather than reported as confident scores. This is "
         "the mechanism by which the system is accountable for its own reliability.")

    h2(doc, "4.8  Fusion and reporting design")
    para(doc,
         "The fusion engine combines four components into a single recommendation. The weights, "
         "shown in Figure 6, are deterministic and published on the report itself.")
    figure(doc, fig("fig06_fusion"),
           "Figure 6  The weighted fusion model, with every component's contribution exposed.")
    para(doc,
         "The weighting reflects a judgement about evidential quality rather than convenience. "
         "What the candidate actually said carries half the score because it is the most direct "
         "evidence of competence available. Skill coverage carries a fifth: a CV is weaker "
         "evidence than a demonstrated answer, but it is not nothing. Integrity and engagement "
         "carry fifteen per cent each — deliberately low, because both rest on inferential "
         "signals that are easily misread.")
    para(doc,
         "One override exists. Where the integrity score falls below thirty, the recommendation "
         "is set to disqualified regardless of the other components, on the reasoning that a "
         "session whose conduct cannot be trusted yields answers whose provenance cannot be "
         "trusted either. This is the only place in the system where a module can override the "
         "others, and it is deliberately hard to trigger.")
    para(doc,
         "Every number on the report decomposes: each component's weighted contribution beside "
         "its raw score, the rubric breakdown and reference answer for every response, the "
         "judge's consistency band, and the behaviours behind any integrity finding. A recruiter "
         "should never encounter a number they cannot trace.")

    h2(doc, "4.9  Critical assessment of the tools selected")
    para(doc,
         "Every significant tool choice carries a cost as well as a benefit, and Table 3 records "
         "both rather than presenting the stack as a series of obviously correct decisions.")
    table(doc,
          ["Tool", "Why selected", "Weakness accepted"],
          [
              ["Gemini 2.5 Flash",
               "Strong instruction-following, JSON-constrained output, generous free tier",
               "Non-deterministic; a reasoning model, so latency and token cost are high; external dependency"],
              ["ESCO v1.1.1",
               "Published EU standard; stable concept identifiers; explicit hierarchy",
               "Predates the modern technology stack; sparse on soft skills; required extension"],
              ["NetworkX",
               "Simple, well documented, adequate for graphs of this size",
               "In-memory only; would not scale to a multi-tenant deployment"],
              ["LiveKit",
               "Production-grade WebRTC; agent framework handles turn-taking and interruption",
               "Heavy dependency; ~12 s process start-up; adds a server to the deployment"],
              ["MediaPipe Tasks Vision",
               "Runs in-browser, so no video leaves the device; no inference cost",
               "Requires WebAssembly and ideally GPU; degrades on older browsers"],
              ["Web Audio prosody (M10)",
               "Fully inspectable features; no model download; offline",
               "A proxy for emotion, not a classifier; weaker than a trained model at that task"],
              ["Isolation Forest",
               "Needs no labelled anomalies; fast; deterministic under a fixed seed",
               "Baseline is synthetic; no measured false-positive rate against real sessions"],
          ],
          widths=[3.4, 6.0, 6.2], font_size=9,
          caption="Table 3  Strengths and weaknesses of the principal tools selected.")
    para(doc,
         "Two of these shaped results reported later. A reasoning model gives better rubric "
         "adherence but makes every score cost reasoning tokens, which is why Chapter 6 runs at a "
         "deliberately modest sample size. And the in-browser vision pipeline, chosen for privacy, "
         "produces nothing on an unsupported browser — so the fusion engine must distinguish a "
         "measured engagement score from an estimated one.")


# ═════════════════════════════════════════════════════════════════════════
# Chapter 5 — Implementation
# ═════════════════════════════════════════════════════════════════════════

def chapter_5(doc, fig):
    h1(doc, "5.  Implementation")

    h2(doc, "5.1  Technology stack and repository structure")
    para(doc,
         "The implementation comprises approximately 4,500 lines of Python and 4,200 lines of "
         "JavaScript, excluding dependencies and generated assets. The backend is organised by "
         "module responsibility rather than by technical layer, so that the correspondence "
         "between the design in Chapter 4 and the code is direct: a reader looking for Module 6 "
         "finds it in core/evaluator/evaluator.py.")
    figure(doc, fig("fig09_deployment"),
           "Figure 9  Deployment and process view. Video and audio are analysed on the "
           "candidate's device; only derived numeric features cross the network.")
    para(doc,
         "The deployment is single-process and single-session, which is appropriate for a "
         "research demonstrator and inadequate for anything else. Section 7.3 states the "
         "consequences explicitly rather than leaving them to be discovered.")

    h2(doc, "5.2  Document understanding (M1, M2)")
    para(doc,
         "CV parsing extracts text from an uploaded PDF using PyMuPDF and passes it to the "
         "language model with a schema-constrained prompt requesting name, contact details, a "
         "summary, skills, experience, education and projects. Job description parsing follows "
         "the same pattern, extracting the role title, required and nice-to-have skills, "
         "responsibilities, seniority level, domain and expected experience.")
    para(doc,
         "The practical difficulty with schema-constrained generation is that models intermittently "
         "return malformed JSON — a trailing comma, an unterminated string, or the whole object "
         "wrapped in a markdown fence. Rather than failing the request, the client strips fences, "
         "attempts a strict parse, and falls back to a repair pass before giving up. This is "
         "unglamorous but it is the difference between a demonstrator that works and one that "
         "fails intermittently in front of an examiner.")
    para(doc,
         "Image-based PDFs yield no extractable text; the system reports this rather than "
         "attempting optical character recognition, which was out of scope.")

    h2(doc, "5.3  The skill graph (M3)")
    para(doc,
         "The graph is constructed at request time from two ESCO CSV exports: the digital skills "
         "collection, providing 1,201 skill concepts with preferred and alternative labels, and "
         "the broader-relations file, providing the hierarchy. Category hubs are synthesised from "
         "the ESCO broader-concept field so that the interface can group skills meaningfully.")
    para(doc,
         "Two supplementary taxonomies extend ESCO where it is thin. A technology extension covers "
         "fifteen categories of modern stack — cloud platforms, containerisation, CI/CD, backend "
         "and frontend frameworks, databases, messaging, machine learning tooling, architecture "
         "patterns, version control, APIs, testing, data engineering and productivity software. A "
         "soft-skill extension covers five categories that ESCO addresses only sparsely. Extension "
         "labels deliberately take precedence over ESCO labels in the lookup index, because "
         "“Docker” is the recognisable form of the concept and an ESCO near-synonym is not.")
    para(doc,
         "An alias map of roughly seventy entries handles the abbreviations and spelling variants "
         "that appear on real CVs — k8s, postgres, nodejs, sklearn, ci/cd, amazon web services. "
         "Aliases are indexed separately from preferred labels and can never shadow an exact "
         "preferred-label match, which prevents a curated shortcut from overriding the taxonomy.")
    h3(doc, "5.3.1  The matching failure and its correction")
    para(doc,
         "The first implementation added a substring fallback: if nothing else matched, any "
         "taxonomy label contained in the input string was accepted. This is superficially "
         "reasonable and was actively harmful. The single-character ESCO concept “R” is a "
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

    h2(doc, "5.4  Question generation and ordering (M4)")
    para(doc,
         "The generator receives the prioritised topics and produces a structured question set: "
         "two opening questions, two to three technical questions per high-priority topic, one to "
         "two per medium-priority topic, three behavioural questions in STAR format, and two "
         "closing questions.")
    para(doc,
         "The flattening step then re-sorts the technical questions by graph priority before the "
         "interview begins, so that high-priority gaps are asked first. Questions whose skill the "
         "graph does not recognise sort after graph-derived ones but before nothing, so they are "
         "not silently discarded. The unit tests assert this ordering directly, using a fixture in "
         "which the model's emission order is deliberately the reverse of the priority order.")

    h2(doc, "5.5  The voice interview agent (M5)")
    para(doc,
         "The agent runs as a subprocess connected to a LiveKit room, orchestrating speech "
         "recognition, language model inference and speech synthesis. Three implementation "
         "problems were substantial enough to record.")
    h3(doc, "5.5.1  Truncated speech")
    para(doc,
         "Piping the model's token stream directly into the synthesis socket produced audio that "
         "stopped after a few words while the full text continued to appear on screen. The "
         "solution was to buffer each complete utterance before synthesising it. This costs a "
         "little latency and buys two things: reliable audio, and control over ordering. The "
         "question is published to the interface first and spoken a fraction of a second later, "
         "so a candidate who mishears can read it.")
    h3(doc, "5.5.2  The silent provider")
    para(doc,
         "More subtle was a failure in which the agent spoke the greeting and then went quiet. "
         "The synthesis provider's quota had been exhausted, and an exhausted quota accepts the "
         "connection and returns no audio frames — indistinguishable from success unless the "
         "frames are inspected. The fix was a startup probe that pushes two characters through "
         "the engine and confirms at least one audio frame comes back, before the interview "
         "begins. If it does not, the agent falls through to the alternative provider, and if "
         "neither works it runs in text-only mode with questions still displayed. The interview "
         "degrades rather than failing.")
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
         "Two details matter. The transcript is structurally identical to the voice agent's, so "
         "the assessment pipeline requires no branch on mode; and the minimum question count is "
         "clamped never to exceed the maximum, without which a demonstration run configured for "
         "three questions would never reach its own limit. Text mode also enables an integrity "
         "signal unavailable in voice: a paste event in the answer box is recorded and surfaced "
         "on the report.")

    h2(doc, "5.7  Answer evaluation (M6)")
    para(doc,
         "The pipeline pairs the transcript into question-and-answer exchanges, classifies each "
         "exchange, scores the substantive ones, and aggregates.")
    para(doc,
         "Pairing is less trivial than it appears. An interviewer may ask a question across two "
         "utterances; a candidate may answer across three. Consecutive turns from the same "
         "speaker are therefore merged, so a question split by a pause still produces one "
         "exchange. Trailing unanswered questions are dropped. Six unit tests cover these cases, "
         "including a candidate speaking before the interviewer.")
    para(doc,
         "Classification labels each exchange as technical, behavioural or logistics in one model "
         "call for the whole session. Logistics exchanges are excluded from scoring, because "
         "grading “Yes, ready” against a technical rubric produces a meaningless zero that drags "
         "down the average. A keyword fallback runs if classification fails, so evaluation never "
         "depends on it succeeding.")
    para(doc,
         "Scoring then proceeds as designed in Section 4.7: a reference answer is generated, the "
         "answer is judged twice under permuted rubric orderings, the mean is taken and the "
         "spread retained. One detail is worth noting. The judge is asked to return both the four "
         "criterion marks and their total, and the implementation trusts the criterion marks over "
         "the model's own arithmetic — if the stated total differs from the sum by more than two "
         "points, the sum is used. Language models are unreliable at addition in a way they are "
         "not unreliable at judgement.")

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
         "Two details determined whether the module was usable. The first is the definition of "
         "response time: the system measures from the question beginning to the answer "
         "completing, typically twenty to sixty seconds. An initial baseline assumed it meant "
         "thinking time, five to fifteen seconds, and flagged every ordinary session as "
         "anomalous. The second is calibration — the raw decision function is not a number a "
         "person can interpret, so the baseline's first and ninety-ninth percentiles are mapped "
         "onto fifty and one hundred at training time, and the bundle is versioned so that an "
         "uncalibrated one is refitted rather than silently reused.")
    para(doc,
         "Finally, the module never returns an adverse verdict without naming a reason. Where the "
         "aggregate pattern is anomalous but no single indicator crossed its threshold, it says "
         "exactly that. A flag a recruiter cannot act on is worse than no flag.")

    h2(doc, "5.10  Fusion and report assembly (M11, M12)")
    para(doc,
         "Fusion is deliberately deterministic arithmetic rather than a learned combination. Each "
         "component is normalised to 0–100, multiplied by its weight, and summed, with the full "
         "breakdown returned alongside the total so the report can show its working. A unit test "
         "asserts that the component contributions reconcile with the reported total, which "
         "guards against the weights and the arithmetic drifting apart.")
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
         "Interruption handling in the voice agent was initially disabled, on the reasoning that a "
         "candidate should not be able to talk over the interviewer. In testing this caused the "
         "framework to discard answers from candidates who began replying while the question was "
         "still being spoken — a natural conversational behaviour. Interruptions were re-enabled "
         "with a minimum duration and word count, so a cough does not interrupt but an answer "
         "does.")
    para(doc,
         "Answer-length thresholds were initially used to skip very short replies. This silently "
         "dropped genuine non-answers such as “I have not used that” from the report, which is "
         "exactly the evidence a recruiter needs. The threshold now excludes only replies too "
         "short to carry any assessable content, and every substantive answer is scored on its "
         "merits however brief.")
    para(doc,
         "Finally, the endpoint's concurrency behaviour proved counter-intuitive: one sequential "
         "call completed in 2.3 seconds while six issued concurrently took 273.8 seconds in "
         "total. The harness was changed to run serially, and the measurement is recorded in the "
         "code so the parallelism is not naively reintroduced.")
