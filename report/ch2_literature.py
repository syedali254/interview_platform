"""Chapter 2 - Literature Review."""

from docx_kit import figure, h1, h2, para


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
