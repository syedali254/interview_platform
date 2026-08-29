"""Chapter 4 - System Design."""

from document_toolkit import MODULE_COUNT, figure, h1, h2, para, table


def chapter_4(doc, fig):
    h1(doc, "4.  System Design")

    h2(doc, "4.1  Architectural overview")
    para(doc,
         f"The system is decomposed into {MODULE_COUNT} modules across four sequential phases. The "
         "decomposition is not decorative: each module declares its input and output, "
         "communicates only through those, and can be developed, deferred or replaced without "
         "disturbing its neighbours — the property that allowed a whole evaluation track to be "
         "removed late in the project without touching the rest.")
    figure(doc, fig("fig01_architecture"),
           f"Figure 1  System architecture. {MODULE_COUNT.capitalize()} modules across four sequential phases, with "
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
         "The traversal step matters more than it appears. A model returns questions in whatever "
         "order it composed them, which correlates with nothing, and every interview has a time "
         "budget: a question that falls off the end is never asked. The system therefore re-sorts "
         "technical questions by the priority the graph assigned to their skill, so the budget is "
         "spent on genuine gaps first. This is the concrete content of Objective 2 — targeting "
         "driven by the graph, not by emission order.")

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
         "Averaging the two passes cancels the component attributable to presentation order. The "
         "more useful output is their disagreement. A judge returning 82 and 81 is stable; one "
         "returning 71 and 45 is not, and the mean of 58 conceals that entirely. The spread is "
         "therefore retained, banded high, moderate or low, and low-band answers are flagged for "
         "human review rather than reported as confident scores. This is the mechanism by which "
         "the system is accountable for its own reliability.")

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
