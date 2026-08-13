# Viva Q&A Preparation

**CMP7200 — Assessment 3.** Q&A carries **25%** of this assessment; clarity of critical
evaluation carries **40%**. Both reward the same thing: knowing exactly where your work
is weak and being able to say so without flinching.

Read this until you can answer from memory. Rehearse aloud — the answers below are
arguments, not scripts, and reciting them verbatim will sound rehearsed.

---

## The three questions you must be able to answer cold

Everything else is secondary. If you can handle these three confidently, you will
handle the rest.

### 1. "Your judge scores partial answers at 92.8 against a 70-point threshold. Isn't your system just broken?"

**Yes, that part of it is — and my evaluation is what found it.**

The scoring model is sound: Spearman's rho of 0.920 and a Cohen's d of 2.98 between
strong and weak answers. The ranking can be trusted. What is broken is the verdict
layer sitting on top of it: the thresholds were set a priori at 40 and 70 and never
validated against the model's actual output distribution.

The consequence is precise — medium and strong answers receive the identical verdict, so
the verdict layer discards resolution the scorer had earned. Exact band agreement is
38.9%.

The wider point is what a score of this kind can support. A judge that ranks well but
calibrates badly is a **comparative** instrument, not an absolute one. It supports "A
answered better than B". It does not support "this candidate scored 92 and therefore
meets a standard" — and my artefact was presenting it as though it did. Any system that
publishes absolute thresholds without validating them against the model's real output
distribution is making that same mistake.

### 2. "So why didn't you just recalibrate the thresholds?"

**Because eighteen answers is far too small a sample to move a decision boundary that
would affect every future candidate.**

Fitting thresholds to this corpus would be exactly the overfitting I criticise elsewhere
in the dissertation — and it would be worse than the current error, because it would
*look* validated while resting on six questions.

What the result establishes is that the current values are indefensible. It does not
establish what the correct values are. Section 6.3 derives the implied boundaries — a
clean separator around 77 for weak/medium, and **no** separator for medium/strong
because those distributions overlap — and recommends recalibration on a larger,
human-anchored corpus as the highest-priority next step.

Distinguishing "I know this is wrong" from "I know what right looks like" is the honest
position, and I would rather hold it than guess.

### 3. "Your proposal's main contribution was the dual-track comparison. You deleted it. Isn't the project's core missing?"

**The comparison was removed because it could not have produced a meaningful result, and
I can show why.**

Three reasons, in order of weight.

*Circularity.* My proposal sourced the classifier's training labels by prompting a
language model to generate answers at defined quality levels. The classifier's ground
truth was therefore the language model's own opinion. Agreement between the two would
have been guaranteed by the experimental design; disagreement would have measured only
the poverty of six hand-crafted surface features. The experiment could not have answered
the question it was built to answer.

*No anchor.* Agreement with human ratings was the metric that would have made the
comparison meaningful. That needed the two-rater validation set my timeline could not
accommodate. Without it, the comparison reduces to two automated scorers disagreeing
with no arbiter.

*It was measurably broken.* Feature importance put 0.543 on semantic similarity alone —
more than the other five features combined. That traced to a data-handling error: the
strong answer had been used as its own reference, so every strong training sample
carried a similarity of exactly 1.0, unreachable at inference time. The behavioural
probe made the consequence concrete: an answer **identical to the reference scored
64.7**, and a **correct paraphrase scored 39.2** — below the threshold at which my system
reports a skill gap.

A scorer that calls a correct answer a gap because the candidate used their own words
is not a usable instrument, and it would have penalised exactly the candidates the
system exists to serve.

The research question narrowed from "which of two scorers is better" to "can one scorer
be made accountable for its own reliability". I would rather report a negative result
with the measurements behind it than present a comparison I could not defend.

---

## On the evaluation

**"Eighteen answers is a very small sample."**
It is, and I say so in Sections 6.1, 6.10 and 7.3. Judging uses a reasoning model, each
answer costs two calls, and the endpoint throttles concurrency severely — I measured one
sequential call at 2.3 seconds against six concurrent calls taking 273.8 seconds in
total. A larger corpus would have consumed the remaining project time for a marginal
gain in precision. These results establish direction and rough magnitude, not confidence
intervals, and I do not claim otherwise.

**"Your ground truth is machine-generated. Isn't that circular too?"**
It is weaker than human rating and I do not pretend otherwise. Two things reduce the
circularity. The fixtures were generated by a **different model** from the one grading
them, so the judge is not simply recognising its own prose. And the reference answer
each response is scored against is generated independently of the candidate answers,
rather than being one of them — the precaution whose absence broke the classifier track.

It remains a real and falsifiable test: a scorer that cannot separate deliberately
strong answers from deliberately weak ones has failed regardless of what any human rater
would say. What it cannot detect is a bias the specification and the judge happen to
share. That is the honest boundary of the claim.

**"You built an escalation mechanism and it never fired. Was it worth building?"**
That is a null result and I report it as one rather than dressing it up. The mechanism is
justified by the literature, is demonstrably operative — the spread is computed and
banded for every answer — but on this corpus it never needed to fire.

Two readings are possible and my data cannot separate them: either the countermeasure
works, or machine-written answers are unusually easy to score consistently. There is one
piece of weak evidence for the second. In my worked example, the single genuinely
partial answer — a candidate admitting they had not used Kubernetes — drew the widest
disagreement of the session at 10 points. One observation proves nothing, but it points
at where the instrumentation would earn its place: not on clearly good or clearly bad
answers, but in the ambiguous middle.

**"Your rubric correlates at 0.85. Doesn't that make the breakdown meaningless?"**
It makes it weaker than I claimed in the design chapter, and I say so in Section 6.6.
Some correlation is legitimate — accurate answers genuinely tend to be more complete. But
0.846 means the four scores carry substantially less than four pieces of information;
the judge forms one impression and distributes it. That is the classic halo effect, and
instructing a model against it did not remove it.

The breakdown retains value as a record of what the judge was asked to weigh, and the
most independent pair does show real separation at 0.744. But it is not the diagnostic
instrument I designed it to be. The structural response is to score each criterion in a
separate call, so each judgement forms without sight of the others — four calls per
answer instead of two.

**"Why Spearman and weighted Kappa rather than accuracy?"**
Because the underlying variable is ordinal, not categorical. Spearman measures whether
the ordering is preserved, which is the property a comparative instrument needs.
Quadratic weighted Kappa penalises being two bands out far more than one band out, which
matches the real cost — confusing weak with strong is much worse than confusing weak with
medium. Plain accuracy would treat those two errors identically.

---

## On the design

**"Why an LLM judge rather than a trained classifier?"**
Beyond the circularity argument: explainability. My project's organising commitment is
that a candidate should be able to see why they were scored as they were. A judge
returns a per-criterion breakdown, the reference answer it compared against, and a
written rationale — all legible to a non-specialist. SHAP attributions over six abstract
linguistic features are not. Whether that is the right trade depends on who the
explanation is for, and my position is that it is for the candidate and the recruiter.

**"Why ESCO rather than your own skill list?"**
Because when the system reports that a candidate lacks a required skill, that skill
should be a concept with a stable identifier in a published EU standard, not a string
the system invented. It makes the assessment auditable at the level of content, not just
scoring. ESCO's limitation is real — v1.1.1 predates much of the modern stack and covers
soft skills sparsely — which is why I extended it with fifteen technology categories and
five soft-skill categories.

**"Talk me through the skill-matching failure."**
My first implementation used a substring fallback when nothing else matched. It mapped
"Team Leadership" onto the ESCO concept "R" — the programming language — and
"Communication" onto "telecommunications engineering". The failure was **silent**: the
graph rendered fine and the gap analysis reported confident nonsense.

The fix removed the fallback and constrained fuzzy matching to strings of at least six
characters at a 0.88 cutoff, so short labels must match exactly. Both failures are now
regression tests.

The general lesson, and the one I would carry forward: in this system the dangerous
failures are the silent ones. An exception is visible. A plausible wrong answer is not.

**"Why 50/20/15/15 for the fusion weights?"**
They reflect evidential quality rather than convenience. What the candidate actually said
carries half because it is the most direct evidence of competence. Skill coverage a
fifth — a CV is weaker evidence than a demonstrated answer, but not nothing. Integrity and
engagement fifteen each, deliberately low, because both rest on inferential signals that
are easily misread. They are not empirically derived, and I would not defend the exact
numbers — only the ordering and the rough magnitudes.

**"Why substitute the vocal analysis module?"**
The proposal specified a wav2vec2 emotion classifier; I implemented prosodic analysis in
the browser. It needs no model download, runs offline, keeps all audio on the
candidate's device, and every component of the score — projection, fluency, expression,
composure — can be inspected and explained. An emotion label from a black-box classifier
could not be. In a project organised around explainability, the substitution improves
coherence. I report it as a change rather than presenting it as the original plan.

---

## On ethics, law and fairness

**"Have you shown the system is fair?"**
No. I have shown it is **inspectable**, which is a precondition for demonstrating
fairness, not a substitute for it.

There is an uncomfortable circularity I name explicitly in Section 7.4. Avoiding human
data removed the ethical burden of collecting it, and simultaneously removed my ability
to test for the harm that matters most — demographic disparity. A project of this length
can reasonably choose the safer path, but it should not then claim a fairness result it
has not earned.

**"How does this measure against the EU AI Act?"**
Mixed, and I audit it honestly in Section 7.4. **Transparency**: well served — every score
decomposes into rubric criteria, a reference answer and a rationale, with weights
published. **Human oversight**: well served by design — no automated hiring decision, and
unstable scores escalate. **Record-keeping**: adequate for a demonstrator, inadequate for
deployment, since transcripts are stored unencrypted without a retention policy. **Bias
testing**: a first step only — I test two documented model biases but not demographic
disparity.

**"Isn't gaze and posture monitoring intrusive?"**
Yes, and I do not think that objection is fully answerable. Nervousness and evasion look
alike to any such measure. My mitigations reduce the harm without resolving the
principle: the signals are weighted lightly at 15% combined, calibrated against the
candidate's own neutral pose rather than an assumed ideal — which would encode whoever
the developer had in mind — and reported as context rather than as findings. The landmark
overlay is shown live to the candidate, so the observation is visible to the person being
observed. A production deployment would need explicit informed consent and a real
opt-out.

**"Did you need ethical approval?"**
No, because no human participants were involved and no personal data was collected,
stored or processed at any stage. That is also a limitation: it is why there is no
human-rated validation set and why the integrity baseline is synthetic.

---

## On the implementation

**"How do you know the artefact actually works?"**
Seventy-two unit tests over the deterministic components, all passing — skill matching,
gap analysis, question ordering, transcript pairing, integrity calibration, fusion
arithmetic, state transitions, report assembly. Two are direct regressions on the
substring-matching failure. Plus an end-to-end run against a synthetic candidate using
live model calls at every stage, asserting the graph builds, questions order by
priority, logistics exchanges are excluded, rubric criteria stay in range and sum to the
reported score, and fusion contributions reconcile with the total.

**"What was the hardest engineering problem?"**
The silent voice agent. It would speak the greeting and then go quiet while the
transcript kept scrolling. The cause was an exhausted speech-synthesis quota — the
provider accepts the connection and returns no audio frames, which is indistinguishable
from success unless you inspect the frames. The fix was a startup probe that spends two
characters confirming audio actually comes back, then falls through to a second provider,
and finally to text-only with questions still displayed. The interview degrades rather
than failing.

**"Why does the system support both voice and text?"**
Accessibility, and evaluation robustness. Both modes share the interviewer's
instructions, the question bank, the budgets and the closing rules — only the transport
differs. The transcript they produce is structurally identical, which is why the
assessment pipeline contains no branch on interview mode anywhere. Keeping one shared
prompt is deliberate: two copies would diverge the first time either was tuned, and the
report would then be comparing candidates assessed under different conditions.

**"Could this be deployed?"**
Not as it stands, and Section 7.3 says so. Session state is a single in-memory
dictionary, so it supports one interview at a time and does not survive a restart. There
is no authentication or rate limiting, cross-origin requests are unrestricted, and
transcripts are written unencrypted to the system temporary directory. It is a research
demonstrator. Production would need persistence, per-session isolation, authentication
and encryption before it touched real candidate data.

---

## Questions to expect on reflection

**"What would you do differently?"**
Build the evaluation harness far earlier. I built the system for most of the project and
measured it at the end. That is why the classifier's defects went undetected for weeks,
and why the leniency problem surfaced too late to address properly rather than only to
report. Measuring alongside building would have left time to fix.

**"What are you most pleased with?"**
That the evaluation found real defects in my own system. Two of the limitations in
Section 7.3 were discovered by my own experiments rather than anticipated. A system
instrumented to be examined can be shown to be wrong, and then corrected — and I would
argue that is worth more than a higher headline score from a system nobody can inspect.

**"What is the single biggest weakness?"**
The absence of a human-rated gold standard. It is upstream of almost everything else: it
is why the classifier comparison collapsed, why E1 measures agreement with a
specification rather than expert judgement, and why I cannot recalibrate the thresholds.
If I had one more month, that is what I would spend it on.

---

## Delivery notes

- **Slides 9 to 13 are the heart of it.** Critical evaluation is 40% of this assessment.
  Do not rush them to reach the conclusion.
- **Do not defend the defects.** Own them fast and move to what they mean. "Yes, and
  here is what it tells us" beats any hedge.
- **Distinguish what you measured from what you infer.** Examiners reward that boundary
  being visible.
- Backup slides 19 to 22 cover threshold calibration, the fusion model, privacy and
  verification. Know they are there.
- If you do not know something, say so and say what would settle it. That reads as
  competence, not weakness.
