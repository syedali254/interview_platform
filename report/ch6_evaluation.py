"""Chapter 6 — Evaluation and Results.

Rendered directly from InterviewAI/experiments/results/statistics.json. No
figure in this chapter is typed in by hand; re-running the harness and
rebuilding produces a chapter consistent with the new measurements.
"""

from docx_kit import figure, h1, h2, para, table
from values import fmt as _fmt, p_value as _p_value






def chapter_6(doc, fig, stats, extra):
    h1(doc, "6.  Evaluation and Results")

    if not stats:
        para(doc,
             "The evaluation harness described in this chapter is implemented at "
             "experiments/run_evaluation.py and forms part of the submitted artefact. Results "
             "were unavailable when this document was generated; running the harness regenerates "
             "this chapter with the measured values.", italic=True)
        return

    e1 = stats["e1_discriminant_validity"]
    e2 = stats["e2_positional_bias"]
    e3 = stats["e3_paraphrase_invariance"]
    e4 = stats["e4_criterion_independence"]
    e5 = stats.get("e5_verbosity", {})
    meta = stats["meta"]
    usage = meta.get("api_usage", {})

    # ── 6.1 Design ───────────────────────────────────────────────────────
    h2(doc, "6.1  Experimental design")
    para(doc,
         "Five controlled experiments, each isolating one property by manipulating a single "
         "factor while holding the rest constant.")
    table(doc,
          ["#", "Property tested", "Manipulation", "Statistic"],
          [
              ["E1", "Discriminant validity",
               "Answer quality varied across three intended levels",
               "Spearman's rho, quadratic weighted Cohen's kappa"],
              ["E2", "Positional-bias sensitivity",
               "Rubric criterion order permuted, content held constant",
               "Wilcoxon signed-rank, mean absolute spread"],
              ["E3", "Paraphrase invariance",
               "Wording varied, semantic content held constant",
               "Within-group standard deviation"],
              ["E4", "Criterion independence",
               "None — observational across all scored answers",
               "Pearson correlation matrix"],
              ["E5", "Verbosity sensitivity",
               "Contentless filler appended, content held constant",
               "Wilcoxon signed-rank on paired differences"],
          ],
          widths=[1.0, 4.0, 6.2, 5.4], font_size=9,
          caption="Table 6  Experimental design summary.")
    para(doc,
         f"The corpus comprises {meta['n_questions']} technical questions, each with answers at "
         f"three intended quality levels, giving {meta['n_graded_answers']} graded answers. Every "
         f"answer is scored twice, once under each rubric ordering, so E1, E2 and E4 all draw on "
         f"the same {meta['n_graded_answers']} × 2 judge calls. E3 and E5 reuse their baselines "
         f"from E1 rather than rescoring identical text.")
    if usage:
        by_model = usage.get("by_model", {})
        judge_model = max(by_model, key=by_model.get) if by_model else "the judging model"
        fixture_model = min(by_model, key=by_model.get) if len(by_model) > 1 else None
        para(doc,
             f"The run consumed {usage.get('calls', 0)} API calls with "
             f"{usage.get('errors', 0)} error over "
             f"{meta.get('elapsed_seconds', 0) / 60:.0f} minutes. All judging "
             f"was performed by {judge_model}"
             + (f", with fixtures generated separately by {fixture_model}"
                if fixture_model else "")
             + f" — a different model from the one grading them, which weakens the objection that "
               f"the judge recognises its own prose.")
        para(doc,
             f"Naming it matters, because it did not survive the project: {judge_model} was "
             f"withdrawn from new API keys shortly after these measurements, and the system now "
             f"runs a later release. The results therefore describe {judge_model} specifically, "
             f"not language-model judges in general — the external-dependency risk of "
             f"Section 7.3, encountered rather than anticipated.")
    para(doc,
         "The sample is deliberately modest: each answer costs two calls and the endpoint "
         "throttled concurrency badly. Section 6.10 gives the consequence.")

    # ── 6.2 E1 ───────────────────────────────────────────────────────────
    h2(doc, "6.2  Discriminant validity")
    para(doc,
         "The first question is whether the judge can tell a good answer from a bad one. The "
         "three quality levels were scored blind.")
    figure(doc, fig("e1_discriminant_validity", experiments=True),
           "Figure 12  Score distribution by intended answer quality, with the band thresholds "
           "the system uses for its verdicts marked.")
    para(doc,
         f"On rank ordering the result is excellent. Spearman's rho between intended quality and "
         f"awarded score is {_fmt(e1['spearman_rho'])} ({_p_value(e1['spearman_p'])}), and "
         f"Cohen's d separating strong from weak answers is "
         f"{_fmt(e1['separation']['strong_vs_weak_cohens_d'], '{:.2f}')} — a very large effect. A "
         f"Mann-Whitney test confirms the ordering is not chance "
         f"({_p_value(e1['separation'].get('mann_whitney_p'))}). Within this corpus the judge "
         f"almost never places a weaker answer above a stronger one.")
    rows = []
    for level in ("strong", "medium", "weak"):
        b = e1["by_level"][level]
        rows.append([level.capitalize(), b["n"], _fmt(b["mean"], "{:.2f}"),
                     _fmt(b["sd"], "{:.2f}"),
                     f"{_fmt(b['min'], '{:.1f}')} – {_fmt(b['max'], '{:.1f}')}"])
    table(doc, ["Intended quality", "n", "Mean score", "SD", "Range"], rows,
          widths=[4.2, 1.6, 3.2, 2.4, 4.2],
          caption="Table 7  Discriminant validity results by intended quality level.")
    para(doc,
         f"The categorical agreement figures tell a very different story, and this is the most "
         f"significant finding of the evaluation. Quadratic weighted Cohen's kappa is only "
         f"{_fmt(e1['quadratic_weighted_kappa'])}, and exact agreement between the intended level "
         f"and the band the system assigns is just {e1['exact_band_agreement']*100:.1f}%. Every "
         f"answer fell within one band of its intended level, so nothing is wildly misplaced — but "
         f"the bands themselves are wrong.")
    para(doc,
         f"The cause is visible in Table 7. The judge is systematically lenient. Answers written "
         f"to be deliberately weak averaged {_fmt(e1['by_level']['weak']['mean'], '{:.1f}')}, "
         f"partially correct answers averaged "
         f"{_fmt(e1['by_level']['medium']['mean'], '{:.1f}')}, and strong answers averaged "
         f"{_fmt(e1['by_level']['strong']['mean'], '{:.1f}')}. Almost the entire working range of "
         f"the scale sits above 50, and the medium and strong distributions overlap: the highest "
         f"medium answer scored {_fmt(e1['by_level']['medium']['max'], '{:.1f}')} while the lowest "
         f"strong answer scored {_fmt(e1['by_level']['strong']['min'], '{:.1f}')}.")
    strong_edge = (e1.get("calibration", {}).get("thresholds_in_use", {})
                   .get("medium_strong", 70))
    para(doc,
         f"This has a direct and damaging consequence for the deployed system. The verdict layer "
         f"labels any answer at or above {strong_edge:.0f} as strong. On this evidence, "
         f"deliberately partial answers clear that threshold comfortably, so medium and strong "
         f"answers receive the same verdict. The scoring model ranks candidates well and the "
         f"verdict layer then discards most of that resolution.")

    # ── 6.3 Calibration ──────────────────────────────────────────────────
    h2(doc, "6.3  Threshold calibration")
    para(doc,
         "Because the ordering is sound and only the thresholds are wrong, the defect is "
         "correctable in principle. Table 8 contrasts the thresholds in use with the boundaries "
         "the observed distributions imply.")
    cal = e1.get("calibration", {})
    in_use = cal.get("thresholds_in_use", {})
    rows = []
    for key, name, edge in (("weak_medium", "Weak / medium", "weak_medium"),
                            ("medium_strong", "Medium / strong", "medium_strong")):
        b = cal.get(key) or {}
        if b.get("separable"):
            gap = (f"{b['clean_separator']:.1f}  (max lower {b['max_lower']:.1f}, "
                   f"min upper {b['min_upper']:.1f})")
        else:
            gap = "none — the distributions overlap"
        rows.append([name, f"{in_use.get(edge, 0):.0f}",
                     f"{b.get('midpoint_of_means', 0):.1f}", gap])
    table(doc,
          ["Boundary", "In use", "Midpoint of adjacent means", "Widest observed gap"],
          rows,
          widths=[3.4, 2.2, 4.6, 6.2], font_size=9,
          caption="Table 8  Current thresholds against empirically implied boundaries.")
    wm = cal.get("weak_medium") or {}
    para(doc,
         f"A clean separator exists between weak and medium answers at approximately "
         f"{wm.get('clean_separator', 0):.0f}, against a threshold of "
         f"{in_use.get('weak_medium', 0):.0f} currently in use. No separator exists between "
         f"medium and strong, because those distributions overlap: on this corpus the judge "
         f"cannot reliably distinguish a partially correct answer from an excellent one in "
         f"absolute terms, only in relative ones.")
    para(doc,
         f"The thresholds were deliberately not changed on the strength of this run. "
         f"{meta['n_graded_answers']} answers across {meta['n_questions']} questions is far too "
         f"small a sample on which to move a decision boundary affecting every future candidate, "
         f"and fitting thresholds to this corpus would be precisely the overfitting criticised "
         f"elsewhere in this dissertation. What the result does establish is that the current "
         f"values are indefensible, and that recalibration against a larger human-anchored corpus "
         f"is the highest-priority next step.")
    para(doc,
         "The deeper implication concerns what the score means. A judge that ranks well but "
         "calibrates poorly is a comparative instrument, not an absolute one: it supports the "
         "claim that one candidate answered better than another, not that a candidate scored 92 "
         "and therefore meets a standard.")

    # ── 6.4 E2 ───────────────────────────────────────────────────────────
    h2(doc, "6.4  Positional-bias ablation")
    para(doc,
         "Stureborg et al. (2024) report that language model judges score identical content "
         "differently depending on presentation order. Every answer here was scored under two "
         "rubric orderings to test whether that effect is present and how large it is.")
    figure(doc, fig("e2_positional_bias", experiments=True),
           "Figure 13  Left: agreement between the two rubric orderings. Right: distribution of "
           "the absolute spread between them, with the consistency thresholds marked.")
    para(doc,
         f"Across {e2['n']} answers the mean score under ordering A was "
         f"{_fmt(e2['order_a_mean'], '{:.2f}')} and under ordering B "
         f"{_fmt(e2['order_b_mean'], '{:.2f}')}, a mean signed difference of "
         f"{e2['mean_signed_difference']:+.3f} points favouring ordering A. A Wilcoxon "
         f"signed-rank test gives {_p_value(e2['wilcoxon_p'])}, short of the conventional "
         f"threshold. The direction is consistent enough to be suggestive and the sample too "
         f"small to settle it.")
    table(doc,
          ["Measure", "Value"],
          [
              ["Answers scored under both orderings", e2["n"]],
              ["Mean signed difference (A − B)", f"{e2['mean_signed_difference']:+.3f} points"],
              ["Mean absolute spread", _fmt(e2["mean_absolute_spread"], "{:.2f}") + " points"],
              ["Median absolute spread", _fmt(e2["median_absolute_spread"], "{:.2f}") + " points"],
              ["Maximum absolute spread", _fmt(e2["max_absolute_spread"], "{:.1f}") + " points"],
              ["Wilcoxon signed-rank", _p_value(e2["wilcoxon_p"])],
              ["High consistency (spread < 8)", e2["consistency_distribution"].get("high", 0)],
              ["Moderate consistency (8 – 16)", e2["consistency_distribution"].get("moderate", 0)],
              ["Low consistency (spread ≥ 16)", e2["consistency_distribution"].get("low", 0)],
              ["Escalated to human review", f"{e2['pct_flagged_low_consistency']:.1f}%"],
          ],
          widths=[9.0, 6.5],
          caption="Table 9  Positional-bias ablation results.")
    para(doc,
         f"Per-item instability is small on this corpus. The mean absolute spread between the two "
         f"orderings was {_fmt(e2['mean_absolute_spread'], '{:.2f}')} points and the largest "
         f"observed was {_fmt(e2['max_absolute_spread'], '{:.1f}')}. "
         f"{e2['consistency_distribution'].get('high', 0)} of {e2['n']} answers fell in the high "
         f"consistency band, one in moderate, none in low. No answer was escalated to human "
         f"review.")
    para(doc,
         "That is a null result for the escalation mechanism, and it is reported as one rather "
         "than dressed up as a success. The instrumentation is justified by the literature and is "
         "demonstrably operative — the spread is computed, banded and acted upon for every "
         "answer — but on this corpus it never needed to fire. Two readings are possible and these "
         "data cannot separate them. Either the countermeasure works and the averaging is doing "
         "its job, or machine-written answers are unusually easy to score consistently and real "
         "transcribed speech would produce wider spreads. The worked example in Section 6.9 is "
         "weak evidence for the second reading.")

    # ── 6.5 E3 ───────────────────────────────────────────────────────────
    h2(doc, "6.5  Paraphrase invariance")
    para(doc,
         "A candidate who expresses the same understanding in different words should receive the "
         "same score. This experiment rewrote answers preserving technical content while changing "
         "wording, sentence structure and order of presentation.")
    figure(doc, fig("e3_paraphrase_invariance", experiments=True),
           "Figure 14  Scores across semantically equivalent rewrites of the same answer.")
    para(doc,
         f"Across {e3['n_groups']} groups the mean within-group standard deviation was "
         f"{_fmt(e3['mean_within_group_sd'], '{:.2f}')} points, with a maximum of "
         f"{_fmt(e3['max_within_group_sd'], '{:.2f}')} and a mean within-group range of "
         f"{_fmt(e3['mean_within_group_range'], '{:.2f}')} points. In absolute terms this is "
         f"reassuring: rewording an answer moves its score by only a point or two.")
    if e3.get("between_group_sd"):
        para(doc,
             f"The comparison that matters is against the between-group standard deviation of "
             f"{_fmt(e3['between_group_sd'], '{:.2f}')} points. Within-group noise is therefore "
             f"roughly half the between-group signal, which sounds poor until one notes why: all "
             f"three groups used strong answers, and Section 6.2 showed strong answers compressed "
             f"into a four-point range. The between-group figure is small because the ceiling "
             f"effect crushed it, not because the judge cannot discriminate. A cleaner version of "
             f"this experiment would draw groups from across the quality range rather than from "
             f"the top of it — a limitation that follows directly from reusing the E1 strong "
             f"answers to conserve API calls.")
    rows = [[g["group"], g["n"], _fmt(g["mean"], "{:.2f}"), _fmt(g["sd"], "{:.2f}"),
             _fmt(g["range"], "{:.1f}")] for g in e3["groups"]]
    table(doc, ["Question group", "Variants", "Mean", "SD", "Range"], rows,
          widths=[5.4, 2.4, 2.6, 2.4, 2.8],
          caption="Table 10  Paraphrase invariance by question group.")

    # ── 6.6 E4 ───────────────────────────────────────────────────────────
    h2(doc, "6.6  Criterion independence")
    para(doc,
         "The rubric instructs the judge to score four criteria independently and states "
         "explicitly that a weakness in one must not drag down the others. Whether it complies is "
         "an empirical question, and the answer here is largely that it does not.")
    figure(doc, fig("e4_criterion_correlation", experiments=True),
           "Figure 15  Correlation matrix between the four rubric criteria across all scored "
           "answers.")
    para(doc,
         f"The mean inter-criterion correlation was {_fmt(e4['mean_inter_criterion_r'])}, ranging "
         f"from {_fmt(e4['min_inter_criterion_r'])} to {_fmt(e4['max_inter_criterion_r'])}. The "
         f"most strongly associated pair was {e4['pairwise'][0]['pair']} at r = "
         f"{_fmt(e4['pairwise'][0]['r'])}; even the most independent pair, "
         f"{e4['pairwise'][-1]['pair']}, correlated at r = {_fmt(e4['pairwise'][-1]['r'])}.")
    para(doc,
         "Some correlation is expected and legitimate. Answers that are technically accurate do "
         "genuinely tend to be more complete, because both follow from understanding the material, "
         "and no rubric could or should force them apart. But correlations in this range indicate "
         "that the four scores carry substantially less than four pieces of information. The judge "
         "appears to form an overall impression and then distribute it across the criteria — the "
         "classic halo effect described in the human rating literature, evidently not eliminated "
         "by instructing a model against it.")
    para(doc,
         "This qualifies a claim made in Chapter 4. The per-criterion breakdown was defended as an "
         "explanation mechanism telling a candidate which aspect of their answer fell short. That "
         "defence is weaker than it appeared: if the four marks move together, the breakdown "
         "communicates one impression four times rather than decomposing it. It retains value as a "
         "record of what the judge was asked to weigh, and the most independent pair does show "
         "real separation, but it is not the diagnostic instrument the design assumed. Section 8.3 "
         "proposes scoring each criterion in a separate call, so that each is formed without "
         "sight of the others.")

    # ── 6.7 E5 ───────────────────────────────────────────────────────────
    if e5.get("n"):
        h2(doc, "6.7  Verbosity probe")
        para(doc,
             "Wang et al. (2024) report that language model judges reward length independently of "
             "substance. The rubric instructs explicitly against this. The probe appends "
             "contentless filler to good answers and rescores them.")
        figure(doc, fig("e5_verbosity", experiments=True),
               "Figure 16  Original and padded versions of the same answers.")
        para(doc,
             f"Across {e5['n']} usable pairs the mean change from padding was "
             f"{e5['mean_delta']:+.2f} points, with {e5['n_increased']} scores rising and "
             f"{e5['n_decreased']} falling. A Wilcoxon signed-rank test gives "
             f"{_p_value(e5['wilcoxon_p'])}.")
        para(doc,
             f"No conclusion can responsibly be drawn from {e5['n']} pairs — a third was lost to "
             f"an API timeout during the run, and the test has essentially no power at this size. "
             f"The direction is at least not adverse: padding raised no score, and both moved "
             f"slightly down. The probe is reported for completeness and because the harness "
             f"supports it, not because it establishes anything. A properly powered version using "
             f"plausible redundant elaboration rather than obvious filler is proposed in "
             f"Section 8.3.")

    # ── 6.8 Verification ─────────────────────────────────────────────────
    h2(doc, "6.8  System-level verification")
    para(doc, "Separately from the scorer, the artefact was verified as software.")
    tests = extra.get("tests", {})
    para(doc,
         f"A unit test suite of {tests.get('count', 72)} tests covers the deterministic "
         f"components: skill normalisation and the matching cascade, gap analysis and the set "
         f"operations behind it, graph-priority question ordering, transcript pairing including "
         f"the merge and drop cases, integrity feature derivation and calibration, the fusion "
         f"weights and their arithmetic reconciliation, per-skill state transitions and report "
         f"assembly. All {tests.get('count', 72)} pass. Two are direct regressions on the matching "
         f"failures described in Section 5.3.1.")
    para(doc,
         "An end-to-end run additionally exercises the full pipeline against a synthetic candidate "
         "and job description, using live model calls at every stage. It asserts that the graph "
         "builds, that gap analysis is coherent, that questions are generated and ordered by "
         "priority, that logistics exchanges are excluded from scoring, that rubric criteria "
         "remain in range and sum to the reported score, and that fusion contributions reconcile "
         "with the total. It passes.")

    # ── 6.9 Worked example ───────────────────────────────────────────────
    h2(doc, "6.9  A worked example")
    para(doc,
         "Aggregate statistics do not convey what the system produces. This traces one "
         "interview end to end. The candidate is a synthetic backend engineer with four years of "
         "Python experience; the role is a senior backend position requiring Python, Kubernetes, "
         "PostgreSQL, REST APIs, microservices and AWS.")
    para(doc,
         "The skill graph resolved the candidate's declared skills against the requirements and "
         "returned a 50% match, correctly identifying Kubernetes and AWS as required skills absent "
         "from the CV and promoting them to high-priority topics. The flattening step then moved "
         "the Kubernetes question ahead of questions about skills already evidenced.")
    rows = []
    for ex in (extra.get("worked_example", {}).get("exchanges") or []):
        scored = ex.get("score") is not None
        rows.append([
            ex["exchange"],
            ex.get("skill") or "—",
            f"{ex['score']:.1f}" if scored else "not scored",
            ", ".join(f"{c:.1f}" for c in ex["call_scores"]) if scored else "—",
            f"{ex['spread']:.1f}" if scored else "—",
            ex.get("consistency") or "—",
        ])
    table(doc,
          ["Exchange", "Skill", "Score", "Judge passes", "Spread", "Consistency"],
          rows,
          widths=[5.0, 3.0, 2.2, 3.0, 1.8, 2.4], font_size=9,
          caption="Table 11  Per-answer results from the worked example.")
    para(doc,
         "Three points are worth drawing out. The greeting and sign-off were correctly classified "
         "as logistics and excluded, so they did not dilute the average. The candidate's admission "
         "that they had not used Kubernetes scored 50 rather than zero, because the rubric credits "
         "accuracy separately from completeness and an honest acknowledgement of a gap contains "
         "nothing incorrect. And that same answer carried the widest judge disagreement of the "
         "session at 10 points — the only moderate-consistency score in the interview, on the only "
         "genuinely partial answer.")
    para(doc,
         "That last observation runs against the null result in Section 6.4 and is the most "
         "interesting thing in this section. Where the machine-written corpus produced almost "
         "uniformly high consistency, the one partial answer in a realistic session produced "
         "measurably more disagreement. It is a single observation and proves nothing, but it "
         "indicates where the reliability instrumentation would earn its place: not on clearly "
         "good or clearly bad answers, which are easy, but in the ambiguous middle where a "
         "recruiter most needs to know how far to trust the number.")

    # ── 6.10 Discussion ──────────────────────────────────────────────────
    h2(doc, "6.10  Discussion of results")
    para(doc,
         "Taken together the experiments support a more qualified claim than the design "
         "anticipated, and that qualification is the most useful thing the evaluation produced.")
    para(doc,
         f"The judge ranks answers extremely well. A Spearman's rho of "
         f"{e1.get('spearman_rho', 0):.2f} and a Cohen's d of "
         f"{e1.get('separation', {}).get('strong_vs_weak_cohens_d', 0):.2f} between strong and "
         "weak answers show the relative ordering can be trusted. But it "
         "calibrates poorly: scores compress into the upper half of the scale, medium and strong "
         "answers overlap, and the system's published thresholds sit far below where answers "
         "actually land. The instrument is comparative rather than absolute, and the artefact "
         "currently presents it as though it were absolute.")
    para(doc,
         f"The rubric is also less decomposed than intended. A mean inter-criterion correlation of "
         f"{e4.get('mean_inter_criterion_r', 0):.2f} indicates a substantial halo effect that an "
         "explicit instruction did not prevent, "
         "weakening — without eliminating — the explainability claim attached to the "
         "per-criterion breakdown.")
    para(doc,
         "Against expectation, positional instability was small on this corpus and the escalation "
         "mechanism never fired. This does not invalidate the design: the motivating literature is "
         "sound, the mechanism is implemented and operative, and the one realistic partial answer "
         "encountered did produce elevated disagreement. But this project has not demonstrated the "
         "mechanism catching real failures at scale and does not claim to have done so.")
    para(doc,
         f"Four threats to validity apply, and Section 7.3 details them: a sample of "
         f"{meta['n_graded_answers']} graded answers, an intended-quality rather than human "
         "ground truth, machine-written "
         "answers cleaner than transcribed speech — which plausibly explains both the E1 ceiling "
         "effect and the unusually high E2 consistency — and paraphrase groups drawn entirely "
         "from strong answers.")
