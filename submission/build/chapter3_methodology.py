"""Chapter 3 - Research Methodology."""

from document_toolkit import bullet, figure, h1, h2, para


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
