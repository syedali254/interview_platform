"""Chapter 2 - Literature Review."""

from document_toolkit import figure, h1, h2, para


def chapter_2(doc, fig):
    h1(doc, "2.  Literature Review")
    para(doc,
         "Four bodies of work bear on this project: the empirical literature on automated "
         "interviewing, the fast-moving literature on language models as evaluators, work on "
         "knowledge graphs for competency modelling, and the fairness and regulatory literature on "
         "algorithmic hiring. A fifth, on remote assessment integrity, informs one module. This "
         "chapter reviews each, draws out where they agree and conflict, and synthesises them into "
         "the framework that governs the design.")

    h2(doc, "2.1  Automated interviewing and algorithmic hiring")
    para(doc,
         "Automated hiring has moved from keyword screening to multimodal assessment of live "
         "interviews. Hickman et al. (2022) reach a conclusion easy to misread as endorsement: "
         "automated scoring is more reliable than unstructured human scoring, in the narrow sense "
         "that it returns the same output for the same input. They separate that carefully from "
         "criterion validity, noting that automated approaches lack the decades of validation "
         "evidence behind structured interviewing. The distinction matters here: a system can be "
         "perfectly consistent and consistently wrong, and consistency alone is not a defence of "
         "a scoring method.")
    para(doc,
         "Langer, König and Papathanasiou (2019) approach the same technology from the "
         "candidate's side. They find candidates rate automated interviews as markedly less fair "
         "than human ones, the effect strongest where no feedback or explanation is given. The "
         "consequence is commercially significant: candidates who perceive a process as unfair are "
         "less likely to accept an offer, eroding the efficiency gain that motivated the "
         "automation. This is the direct motivation for the explanation-first orientation here — "
         "the argument for explainability is not only ethical but instrumental.")
    para(doc,
         "Together these frame a tension the design must resolve rather than choose between. "
         "Automation buys consistency and scale at the cost of validity evidence and perceived "
         "fairness; a system wanting both must make its reasoning inspectable.")

    h2(doc, "2.2  Language models as evaluators")
    para(doc,
         "The use of a language model as judge was popularised by Zheng et al. (2023), whose "
         "MT-Bench and Chatbot Arena work established that GPT-4's preference judgements agree "
         "with human evaluators at over eighty per cent on open-ended tasks — comparable to "
         "inter-human agreement on the same material. The result matters because it suggests that "
         "for tasks with no single correct answer, a capable model can substitute for expensive "
         "human annotation.")
    para(doc,
         "The qualifications arrived quickly, and are specific rather than general. Stureborg, "
         "Alikaniotis and Suhara (2024) show LLM judges are both inconsistent and biased: "
         "presented with the same candidates in a different order, the same model returns "
         "different scores. The bias is positional, arising from sequence rather than content. "
         "Wang et al. (2024) identify a complementary failure, verbosity bias, in which longer "
         "responses score higher irrespective of whether the extra length carries substance.")
    para(doc,
         "These findings are usually cited as reasons not to trust LLM judges. That reading misses "
         "what makes them useful: both biases are characterised precisely enough to be countered by "
         "construction. If a score depends on presentation order, presenting the same material under "
         "several orders and aggregating removes the order-specific component — and the disagreement "
         "between orderings becomes a direct measure of how unstable that judgement was. A bias that "
         "can be measured can be reported, and one that is reported can be acted on. This project "
         "treats these results as specifications for countermeasures, not grounds for abandonment.")
    para(doc,
         "One methodological caution in this literature shaped a significant decision here: where "
         "an automated scorer is compared against labels a language model itself produced, "
         "agreement is partly an artefact of the design rather than evidence about the world. "
         "Section 7.2 returns to it.")

    h2(doc, "2.3  Knowledge graphs for competency modelling")
    para(doc,
         "Knowledge graphs represent entities and their relations in a form supporting traversal "
         "and inference. Chen, Li and Zhang (2021) apply graph-based models to prerequisite "
         "identification in online learning, showing traversal over a structured concept graph can "
         "generate coherent learning paths without learned embeddings. The relevance here is "
         "specific: where domain structure is already documented and reliable, deterministic "
         "traversal is both simpler and more explainable than a learned alternative.")
    para(doc,
         "The ESCO framework (European Commission, 2023) supplies exactly such a structure — a "
         "multilingual taxonomy of skills, competences and occupations maintained as an EU "
         "standard, with over thirteen thousand skill concepts linked by explicit broader and "
         "narrower relations. Using a published taxonomy rather than an ad hoc list matters for a "
         "high-risk system: when the platform reports a candidate lacks a required skill, that "
         "skill is a concept with a stable identifier in a public standard, not a string the "
         "system invented.")
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
         "The regulatory response is now concrete. The EU AI Act places recruitment systems in the "
         "high-risk category and requires transparency, human oversight, technical documentation "
         "and testing for bias (European Commission, 2024). What is notable for a designer is that "
         "the Act does not demand a model be unbiased, which would be unachievable; it demands "
         "that bias be tested for, documented and subject to human oversight. That is a design "
         "brief, met by instrumentation rather than aspiration.")
    para(doc,
         "This project addresses fairness at three points. Scoring uses only what the candidate "
         "said, judged against a reference answer for the same question, with no demographic input "
         "and no proxy for one. The rubric is published to the candidate rather than held "
         "internally. And the reliability of every score is measured and reported alongside it, so "
         "a recruiter can see which judgements are firm. None of this guarantees fairness; it "
         "makes unfairness detectable, which is weaker but achievable, and the claim the "
         "literature supports.")

    h2(doc, "2.5  Behavioural integrity and remote assessment")
    para(doc,
         "Remote assessment raises an integrity problem that predates AI interviewing. The "
         "approach here follows the unsupervised anomaly-detection tradition: rather than classify "
         "cheating directly, which needs labelled examples no institution can ethically produce, a "
         "model of normal interaction is fitted and departures flagged for review. Isolation "
         "Forest (Liu, Ting and Zhou, 2008) suits this framing because it isolates anomalies by "
         "random partitioning and requires no labelled negative class.")
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
         "Most bias-mitigation work here is evaluated offline on benchmark datasets, applying the "
         "mitigation and re-measuring aggregate agreement. That is valuable, but leaves the "
         "practitioner without a per-item reliability signal at inference time. The contribution "
         "claimed is modest and concrete: an interview pipeline in which every score carries an "
         "empirically derived confidence from the judge's agreement with itself, and in which that "
         "confidence changes what the system does.")
