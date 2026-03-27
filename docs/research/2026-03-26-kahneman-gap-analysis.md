Now I have a thorough understanding of the system. Let me compile the comprehensive gap analysis report.

---

# Kahneman Gap Analysis: SDLC-OS Plugin vs. Complete Body of Work

## SECTION 1: ALREADY EMBEDDED

### AE-1. Adversarial Collaboration Protocol
**Concept:** Kahneman's adversarial collaboration method -- two opposing parties pre-register what evidence would change their minds, a neutral party designs a fair test, the result is binding.
**Implemented as:** The Arbiter agent (`agents/arbiter.md`) implements the full five-step protocol: dispute intake with pre-registered commitments, position extraction, test design by disagreement type (existence/severity/exploitability/relevance), test execution, binding verdict. The dispute contract locks before testing begins, preventing post-hoc rationalization. Two-round maximum mirrors the Kahneman-Klein collaboration pattern where the goal is to narrow disagreement rather than eliminate it.
**Files:** `agents/arbiter.md`, `skills/sdlc-adversarial/arbitration-protocol.md`, `skills/sdlc-adversarial/SKILL.md` (Phase 5)

### AE-2. System 1 / System 2 Dual-Process Architecture
**Concept:** Fast, automatic, low-effort cognition (System 1) vs. slow, deliberate, effortful cognition (System 2). Kahneman's central organizing framework from "Thinking, Fast and Slow."
**Implemented as:** The entire model-tier hierarchy maps to this. Haiku agents operate as System 1 (cheap, fast, broad pattern detection -- recon guppies, premortem agents, sentinels). Sonnet agents operate as System 2 (deliberate analysis -- red team commanders, blue team defenders, runners). Opus fires only for the hardest judgments (arbiter disputes). Phase 4.5 explicitly schedules this as "Dual-Process Scheduling" with a table mapping each step to System 1 (Haiku) or System 2 (Sonnet) processing.
**Files:** `skills/sdlc-harden/SKILL.md` (Dual-Process Scheduling table), `agents/red-reliability-engineering.md` (System 1 recon -> System 2 directed strikes)

### AE-3. WYSIATI (What You See Is All There Is)
**Concept:** People make judgments based only on available information without considering what they do not know. The most dangerous gaps are the ones no one is looking at.
**Implemented as:** The WYSIATI Coverage Sweep in Phase 4.5 (Step 7). A coverage matrix is built with rows for every file and exported function in the bead, and columns for each agent that reviewed it. All-blank rows -- files no agent mentioned -- are flagged with "Unknown" confidence, explicitly the most dangerous label. This mechanically surfaces what the system is blind to.
**Files:** `skills/sdlc-harden/SKILL.md` (WYSIATI Coverage Sweep section), `agents/reliability-conductor.md` (Step 7)

### AE-4. Anchoring Bias Countermeasures
**Concept:** Judgment is biased toward an initial value or piece of information, even when irrelevant. Adjustments from the anchor are typically insufficient.
**Implemented as:** Structural anti-anchoring protocols throughout the system. The Red Team in Phase 4.5 receives raw bead code only, explicitly NOT the Observability Engineer's or Error Hardener's self-assessment. This is a hard constraint in `agents/reliability-conductor.md` ("Showing Blue Team self-assessment to Red Team" listed as an anti-pattern), `agents/red-reliability-engineering.md` (bolded "Critical anti-anchoring rule"), and the AQS model eval (`docs/evals/aqs-model-eval/README.md` tests whether models resist anchoring).
**Files:** `agents/reliability-conductor.md` (Step 4 dispatch), `agents/red-reliability-engineering.md` (anti-anchoring rule), `skills/sdlc-harden/SKILL.md` (Hard Constraints)

### AE-5. Premortem Analysis (with Gary Klein)
**Concept:** From Kahneman and Klein's collaboration: imagine the project has failed, then work backward to determine what caused the failure. More effective than asking "what could go wrong?" because it overcomes optimism bias by treating failure as a certainty.
**Implemented as:** Step 0 of Phase 4.5. Three independent haiku agents receive identical prompts: "Bead {id} has been deployed to production. 90 days later, a severe incident occurred that the hardening phase failed to prevent. Write the postmortem." Each agent works independently (Kahneman independence requirement for noise reduction). Failure modes appearing in 2+ narratives become priority targets for hardening.
**Files:** `agents/reliability-conductor.md` (Step 0), `skills/sdlc-harden/SKILL.md` (Step 0 Premortem)

### AE-6. Planning Fallacy Countermeasure
**Concept:** People underestimate the time, costs, and risks of future actions while overestimating their benefits. The optimistic frame of "what should we do?" produces systematically poor estimates.
**Implemented as:** The premortem analysis explicitly reframes from optimistic to pessimistic. `agents/reliability-conductor.md` states: "This defeats the planning fallacy: instead of 'what should we harden?' (optimistic), we ask 'what will we fail to harden?' (loss-aversion frame)." The loss-aversion reframe is deliberate Kahneman.
**Files:** `agents/reliability-conductor.md` (Step 0 commentary)

### AE-7. Noise Audits
**Concept:** From "Noise" (2021): measuring the variability in decisions that should be identical. Run the same case through the system twice; high variance means the system is unreliable regardless of bias.
**Implemented as:** The Calibration Protocol includes a full noise audit procedure. Re-runs the same AQS cycle on the same bead with fresh agent instances. Measures finding overlap: >80% = LOW noise, 50-80% = MODERATE, <50% = HIGH. Breaks noise into three Kahneman types (level, pattern, occasion) with specific mitigations for each. Additionally, LOSA Observer re-runs Red Team probes every 5th bead; divergence >20% triggers an occasion noise signal.
**Files:** `references/calibration-protocol.md` (Noise Audit section), `skills/sdlc-harden/SKILL.md` (LOSA integration)

### AE-8. Level Noise / Pattern Noise / Occasion Noise (Three Types from "Noise")
**Concept:** Level noise: some judges are systematically harsher. Pattern noise: same judge treats different case types differently. Occasion noise: same judge, same case, different day = different judgment.
**Implemented as:** All three types are explicitly defined in `references/calibration-protocol.md` with cause analysis and mitigations: level noise mitigated by standardized rubrics with anchored examples, pattern noise by rebalancing domain emphasis in agent prompts, occasion noise by resetting agent context between beads and randomizing review order.
**Files:** `references/calibration-protocol.md` (Noise Type Analysis table)

### AE-9. Mediating Assessments Protocol (MAP)
**Concept:** From "Noise": score each dimension of a decision independently before forming an overall judgment. Prevents the halo effect where a strong impression on one dimension biases all others.
**Implemented as:** The Arbiter uses MAP explicitly in the arbitration protocol. Before writing the holistic verdict, the Arbiter scores four dimensions independently (Evidence strength, Impact severity, Fix proportionality, Confidence in test) on a 1-5 scale. The protocol states: "Score each dimension BEFORE considering the others -- do not let one dimension bias another." Scores inform but do not mechanically determine the verdict.
**Files:** `skills/sdlc-adversarial/arbitration-protocol.md` (Step 5: Verdict, MAP section)

### AE-10. Halo Effect Prevention
**Concept:** The tendency for an impression in one area to influence opinion in another area. A positive impression of evidence quality might bias severity assessment upward.
**Implemented as:** MAP scoring with independent dimensions (AE-9 above) and the explicit instruction "do not let one dimension bias another." Also, the non-zero-sum objective separation between red and blue teams prevents role-based halo effects -- each team optimizes a different objective function.
**Files:** `skills/sdlc-adversarial/arbitration-protocol.md` (MAP), `skills/sdlc-adversarial/SKILL.md` (Non-Zero-Sum Objective Separation)

### AE-11. Reference Class Forecasting
**Concept:** Instead of planning from the inside (how this specific project will go), consult the base rate of similar projects. Kahneman and Lovallo's key insight for countering planning fallacy.
**Implemented as:** The Reliability Conductor builds an "observability profile" before any instrumentation. `agents/reliability-conductor.md` states: "This is the reference class anchor -- understanding what exists so instrumentation is coherent." The observability profile maps logging frameworks, tracing, metrics, error tracking, and resilience patterns across the existing codebase, establishing the reference class against which all new instrumentation is judged. The AQS research synthesis also explicitly called for tracking fix-complexity estimates vs. actuals.
**Files:** `agents/reliability-conductor.md` (Step 0 commentary, Observability Stack Detection), `docs/specs/2026-03-25-aqs-v2-research-synthesis.md` (Section 3D)

### AE-12. Conditions for Intuitive Expertise (Kahneman-Klein 2009)
**Concept:** Expert intuition is trustworthy only in environments with (a) high validity/regularity and (b) adequate opportunity to learn those regularities. In low-validity environments, expert intuition is unreliable.
**Implemented as:** The Cynefin framework integration directly operationalizes this. Clear-domain tasks (high-validity, regular patterns) trust fast, low-oversight paths (L0 auto-merge). Complex-domain tasks (low-validity, irregular) require full adversarial scrutiny. The system explicitly does not trust "intuition" (agent self-reports) -- it demands evidence. The loop system's core principle "Evidence over argument -- confidence upgrades require new evidence, not reasoning" is a direct implementation of the Kahneman-Klein boundary condition.
**Files:** `skills/sdlc-loop/SKILL.md` ("Evidence over argument"), `skills/sdlc-orchestrate/SKILL.md` (Complexity Scaling), `skills/sdlc-adversarial/SKILL.md` (When to Activate)

### AE-13. Overconfidence Bias Countermeasures
**Concept:** People systematically overestimate their knowledge, the precision of their information, and their ability to predict outcomes.
**Implemented as:** Multiple mechanisms. Every bead requires a self-assessed confidence score (0.0-1.0 with rationale). Oracle overrides runner self-reports ("If a Runner says 'done' and the Oracle says 'not proven,' the Oracle wins"). The VORP standard (Verifiable, Observable, Repeatable, Provable) rejects claims without evidence. The Daubert evidence gate in AQS filters findings based on factual basis, methodological reliability, and known false-positive patterns. The correction signal format forces runners to state what they tried and why it failed rather than just claiming the fix works.
**Files:** `skills/sdlc-orchestrate/SKILL.md` (Oracle section, VORP), `skills/sdlc-adversarial/SKILL.md` (Daubert gate)

---

## SECTION 2: PARTIALLY EMBEDDED

### PE-1. Substitution (Answering an Easier Question)
**Concept:** When faced with a hard question, people unconsciously substitute an easier one. "Is this code secure?" gets replaced by "Does this code look like secure code I've seen before?"
**Implemented as:** Partially addressed by the VORP standard, which demands verifiable evidence rather than pattern-matching impressions. The Daubert gate filters findings based on executed probe output rather than inference ("this looks like it could be vulnerable"). The AQS research synthesis explicitly notes that "LLMs performing code review operate primarily in System 1 mode, failing 78% of the time on semantic-preserving mutations."
**Missing:** No explicit substitution detection mechanism. No protocol that forces agents to re-state the original question they were asked and verify their answer addresses THAT question rather than a related-but-easier one. A sentinel check comparing "question asked" vs. "question answered" would catch drift where a security review substitutes for a pattern-match review.
**Where it would go:** L1 Sentinel loop (`skills/sdlc-loop/SKILL.md`), as a "substitution detector" check alongside drift-detector and convention-enforcer.

### PE-2. Loss Aversion (Prospect Theory)
**Concept:** Losses loom larger than equivalent gains. People are risk-averse for gains but risk-seeking for losses.
**Implemented as:** The premortem analysis uses loss-aversion framing explicitly ("what will we fail to harden?" rather than "what should we harden?"). Error budget policy uses loss framing -- depleted budget triggers slowdown and increased scrutiny.
**Missing:** No systematic use of loss framing in bead specifications or runner prompts. When runners receive beads, the acceptance criteria are framed as positive targets ("implement X"). Kahneman's research suggests framing some criteria as losses ("if this bead ships without Y, users will lose Z") would increase attention to critical requirements. Loss framing is used in one place (premortem) but not propagated to the routine dispatch pattern.
**Where it would go:** Runner dispatch template in `skills/sdlc-orchestrate/SKILL.md` (How to Dispatch Runners section), adding a "Risk of omission" field to bead specifications.

### PE-3. Structured Decision-Making / Decision Hygiene ("Noise")
**Concept:** From "Noise": use structured protocols (checklists, independent assessments, delayed holistic judgment) to reduce noise in decisions. Decision hygiene is the set of organizational practices that reduce unwanted variability.
**Implemented as:** Strong implementation across multiple mechanisms: MAP scoring for arbiter, independent premortem agents, pre-registered dispute contracts, correction signal format with required fields, bead specifications with required sections. The overall system is heavily structured.
**Missing:** The Conductor's own decisions are not structured. When the Conductor selects Cynefin domains, chooses between re-decomposition strategies, or decides whether to escalate, there is no MAP-style scoring protocol. The Conductor operates with holistic judgment where structured assessment would reduce noise. Phase 1 (Frame) and Phase 3 (Architect) are the least structured phases -- sonnet-investigator and sonnet-designer get broad prompts without the forced-dimension-scoring that the arbiter uses.
**Where it would go:** `skills/sdlc-orchestrate/SKILL.md` Phase 1 and Phase 3, adding a structured scoring protocol for the Conductor's key decisions (Cynefin classification, design selection, escalation thresholds).

### PE-4. Base Rate Neglect
**Concept:** People overweight specific case information and underweight statistical base rates. A vivid anecdote about one failure overrides the base rate that 95% of similar cases succeed.
**Implemented as:** Partially addressed through the precedent system (stare decisis) which accumulates base rates of dispute outcomes, the regression watchlist which tracks defect type frequencies, and the error budget's SLI tracking which provides statistical base rates for code quality.
**Missing:** No mechanism feeds base rates into the Conductor's risk assessment at Phase 1 (Frame). When the Conductor classifies beads into Cynefin domains, there is no lookup against historical base rates of how similar beads performed. A bead touching authentication code might have a 40% historical rate of security findings, but without explicit base rate injection, the Conductor relies on case-by-case judgment.
**Where it would go:** Phase 1 in `skills/sdlc-orchestrate/SKILL.md`, adding a base rate lookup step: "Before assigning Cynefin domain, check historical finding rates for beads touching similar code areas (from precedent database + regression watchlist)."

### PE-5. Regression to the Mean
**Concept:** Extreme observations tend to be followed by more moderate ones. A spectacularly successful bead does not predict the next bead will be equally good; a catastrophic failure does not predict the next will be equally bad.
**Implemented as:** The error budget policy partially addresses this by using rolling 3-task windows rather than single-task snapshots. The calibration loop's baseline comparison implicitly accounts for regression by measuring against a stable baseline rather than recent peaks.
**Missing:** No explicit warning against over-reacting to single outlier results. If one bead produces 5 critical AQS findings, the system adjusts domain priorities upward for subsequent beads (per the "Task-Level Prior Adjustments" in `skills/sdlc-loop/SKILL.md`). This is a reasonable Bayesian update, but there is no dampening factor to account for regression to the mean -- the adjustment treats one extreme data point as signal rather than partially noise. Similarly, after a streak of clean beads, there is no warning that the next bead may revert to base rate difficulty.
**Where it would go:** The "Task-Level Prior Adjustments" mechanism in `skills/sdlc-loop/SKILL.md` (Evidence Accumulation Across Loops), adding a dampening coefficient and explicit regression-to-mean note.

---

## SECTION 3: NOT YET EMBEDDED (sorted HIGH to LOW)

### NE-1. Focusing Illusion
**Concept:** "Nothing in life is as important as you think it is while you are thinking about it." The very act of attending to something inflates its perceived importance. Kahneman considered this one of his most useful findings.
**Rating: HIGH**
**Gap:** No mechanism detects when agents or the Conductor are disproportionately focused on one aspect of a bead while neglecting others. The WYSIATI sweep catches files that were never mentioned, but it does not catch the more insidious case where a file WAS mentioned but only one aspect was reviewed. A security audit might focus entirely on input validation while ignoring authorization logic in the same file -- both were "seen" but attention was asymmetric. The Conductor can become fixated on a complex problem in one bead while auto-advancing other beads with insufficient scrutiny.
**Mechanism:** Add a "Proportionality Audit" to Phase 5 (Synthesize). For each bead, measure the ratio of agent-turns spent per concern area vs. the risk profile of that concern area. If the Conductor spent 80% of attention budget on bead-3's edge case while bead-7 (which touches auth) got one sentinel pass, flag the imbalance. Implementation: a simple token-count-per-bead metric compared against the bead's Cynefin domain would surface disproportionate attention allocation.
**Where:** `skills/sdlc-orchestrate/SKILL.md` Phase 5: Synthesize, as a new dispatch step alongside the existing fitness check.

### NE-2. Duration Neglect and Peak-End Rule
**Concept:** People judge experiences primarily by their peak intensity and how they end, not by their total duration or average quality. A review process that ends badly (last-minute critical finding) feels worse than one that was painful throughout but ended cleanly.
**Rating: HIGH**
**Gap:** The system accumulates evidence and findings chronologically but does not account for temporal bias in agent judgment. When Blue Team receives a long list of Red Team findings, the last few findings will disproportionately influence the overall response quality (peak-end). When the Conductor reviews a bead's full correction history, the most recent correction dominates the assessment of bead health. The "Belief Update" in AQS reports tracks pre/post assessments but does not correct for the fact that the final cycle's impression will dominate.
**Mechanism:** Require the Conductor to score bead health using the FULL correction history, not just the final state. Add an explicit "History-Weighted Assessment" instruction to Phase 5: "Your assessment of this bead must account for ALL cycles, not just the final outcome. A bead that required 24 agent invocations to reach 'hardened' is not equivalent to one that passed on first attempt, even if both are now 'hardened'." The bead status extension already tracks L0/L1/L2/L2.5 cycle counts -- surface these as a "turbulence score" in the delivery summary.
**Where:** `skills/sdlc-orchestrate/SKILL.md` Phase 5 delivery summary format, `skills/sdlc-loop/SKILL.md` bead status extensions.

### NE-3. Certainty Effect (Prospect Theory)
**Concept:** People overweight outcomes that are certain relative to outcomes that are merely probable. A reduction from 100% to 95% (losing certainty) feels much larger than a reduction from 50% to 45% (same absolute change). This creates excessive risk aversion when certainty is possible and insufficient attention to highly-probable-but-not-certain risks.
**Rating: HIGH**
**Gap:** The AQS convergence assessment and error budget policy treat probability changes linearly. Going from "zero findings" to "one finding" should trigger a qualitatively different response than going from "three findings" to "four findings" -- the first breaks a certainty threshold. Currently, the convergence assessment checks three indicators (low diversity, low severity, low volume) but does not distinguish between "this bead had zero findings across all domains" (certainty of clean) and "this bead had one low finding in one domain" (almost clean). The system treats both similarly, but the certainty effect means the psychological and practical significance of the first crack in a clean record deserves special attention.
**Mechanism:** Add a "Zero-to-One" signal in AQS Phase 6 reporting. When a bead that was expected to be clean (Clear domain, healthy error budget) produces even a single finding, this should be flagged distinctly from routine finding volumes. The first finding in a previously-clean area is disproportionately informative because it breaks a certainty assumption. Implementation: if a bead's Cynefin domain is Clear but AQS produces any finding, auto-escalate the bead to Complicated and require full Cycle 2 regardless of convergence indicators.
**Where:** `skills/sdlc-adversarial/SKILL.md` (Cycle Budget section), `skills/sdlc-adversarial/scaling-heuristics.md`.

### NE-4. Diminishing Sensitivity (Prospect Theory)
**Concept:** The subjective difference between $0 and $100 is much larger than between $1000 and $1100. Marginal impacts matter less as you move away from the reference point. Applied to code quality: the difference between 0 bugs and 1 bug matters more than between 10 bugs and 11.
**Rating: MEDIUM**
**Gap:** The system's severity calibration (critical/high/medium/low) is flat -- it does not adjust based on the current defect count. The 11th medium-severity finding on a bead gets the same treatment as the 1st. But in practice, the marginal value of fixing the 11th issue is lower than fixing the 1st, and the signal content is different -- 11 findings suggests a systemic problem requiring design rethinking, not 11 individual fixes.
**Mechanism:** Add a "finding saturation threshold" to AQS. If a single bead accumulates more than N findings (tunable, default 5), the Conductor should pause directed strikes and instead dispatch a "systemic assessment" guppy that asks: "Are these N findings symptoms of a single root cause?" If yes, the root cause gets a single high-severity finding and the symptoms are bundled. This prevents diminishing returns on individual finding remediation.
**Where:** `skills/sdlc-adversarial/SKILL.md` Phase 3 (Directed Strike), as a saturation circuit breaker.

### NE-5. Experienced Utility vs. Decision Utility (Hedonic Psychology)
**Concept:** What people choose (decision utility) often differs from what they actually experience (experienced utility). People predict they will enjoy or suffer from outcomes differently than they actually do. In software: what developers predict will be the pain points in code differs from what actually causes production incidents.
**Rating: MEDIUM**
**Gap:** The system has no feedback loop from actual production outcomes back to the predictions made during Frame/Scout/Architect phases. The premortem predicts failure modes; AQS probes for them. But there is no mechanism to compare these predictions against what actually happens post-deployment. Without this feedback, the system cannot calibrate whether its predicted "experienced utility" (expected code quality) matches actual "experienced utility" (real-world reliability).
**Mechanism:** Add a "Production Outcome Tracker" to the L6 Calibration Loop. After a task's code has been in production for N days (configurable), the Conductor dispatches a guppy to check: were any of the premortem predictions realized? Were any AQS findings that were dismissed actually triggered? Were any issues that arose NOT predicted by the premortem or AQS? This closes the prediction-outcome gap and calibrates future premortems.
**Where:** `references/calibration-protocol.md` (new section: Production Outcome Calibration), `skills/sdlc-loop/SKILL.md` L6 loop.

### NE-6. Availability Heuristic
**Concept:** People judge the probability of events by how easily examples come to mind. Recent, vivid, or emotionally salient events are overweighted. A spectacular security breach in the news makes agents over-index on security while neglecting resilience.
**Rating: MEDIUM**
**Gap:** The system's domain priority selection in AQS is influenced by recon signals and Conductor judgment, but there is no correction for availability bias. If the previous three beads all had security findings, the availability heuristic will cause the Conductor to over-prioritize security on the 4th bead even if it does not warrant it. The "Task-Level Prior Adjustments" table in `skills/sdlc-loop/SKILL.md` actually amplifies this bias -- it explicitly increases priority for domains with prior findings, which is a reasonable Bayesian update but also a vector for availability bias when the sample is small.
**Mechanism:** Add a "base rate anchor" to the Conductor's domain selection. Before applying task-level prior adjustments, the Conductor should consult the full historical distribution of findings across domains (from the precedent database), not just the current task's recent beads. If the historical base rate for security findings is 20% but the current task has 60%, flag this as a potential availability bias inflation and require the Conductor to document why this task genuinely deserves elevated security focus.
**Where:** `skills/sdlc-adversarial/SKILL.md` Phase 2 (Cross-Reference), `skills/sdlc-loop/SKILL.md` (Task-Level Prior Adjustments).

### NE-7. Representativeness Heuristic
**Concept:** People judge the probability that A belongs to category B by how much A resembles B, ignoring base rates and sample sizes. A piece of code that "looks like" a vulnerability gets flagged even if the pattern is common and rarely exploitable.
**Rating: MEDIUM**
**Gap:** Red team guppies are particularly vulnerable to representativeness. A haiku-tier agent seeing a pattern that "looks like" SQL injection (string concatenation near a database call) will flag it even if the string is a log message, not a query. The Daubert gate partially addresses this (checks factual basis and methodological reliability) but does not explicitly check for representativeness errors -- cases where the surface pattern matches a known vulnerability class but the functional context makes it irrelevant.
**Mechanism:** Add a "Context Override" check to the Daubert gate in AQS Phase 3. After verifying factual basis and methodological reliability, the red team commander must answer: "Does the surrounding code context make this pattern benign despite its surface similarity to a known vulnerability?" This forces a base-rate check against the actual functional context rather than just the surface pattern.
**Where:** `skills/sdlc-adversarial/SKILL.md` Phase 3 (Directed Strike, Daubert evidence gate, new criterion).

### NE-8. Sunk Cost Fallacy
**Concept:** People continue investing in a failing course of action because of previously invested resources rather than future value. The more effort spent, the harder it is to abandon the approach.
**Rating: MEDIUM**
**Gap:** The loop system has hard budgets to prevent infinite loops, which partially addresses sunk cost. However, the L4 Phase Loop and L5 Task Loop do not have explicit sunk-cost warnings. When the Conductor has invested heavily in a design approach through multiple beads and the approach is failing, the system's L4 options include "change the design" but there is no protocol that actively counteracts the Conductor's reluctance to discard work. The Conductor must weigh "re-decompose" vs. "provide more context" vs. "change design" vs. "escalate," and sunk cost bias will push toward options that preserve existing work.
**Mechanism:** Add a "Fresh Eyes Protocol" to L4 escalation. When a bead escalates from L3 to L4, the Conductor must answer: "If I were starting this task from scratch right now with everything I know, would I choose the same design approach?" If the answer is no, the design must be changed regardless of work already completed. This reframes the decision from "should I abandon my investment?" to "would I make this investment again?" -- the standard Kahneman de-biasing technique for sunk cost.
**Where:** `skills/sdlc-loop/SKILL.md` Level 4 (Phase Loop), as an additional step before the Conductor selects a recovery strategy.

### NE-9. Cognitive Reflection (from CRT research)
**Concept:** The Cognitive Reflection Test measures ability to suppress an intuitive but wrong answer in favor of a reflective correct answer. "A bat and ball cost $1.10 total. The bat costs $1 more than the ball. How much does the ball cost?" (Intuitive: $0.10. Correct: $0.05.) The key insight: System 1 generates plausible-but-wrong answers that feel right.
**Rating: MEDIUM**
**Gap:** No mechanism tests whether agents are giving "bat and ball" answers -- responses that are intuitively plausible but factually wrong. The Oracle verifies claims against evidence (VORP), which catches some of these. But the Oracle checks whether claims are SUPPORTED, not whether the reasoning path was correct. An agent could reach the right conclusion via wrong reasoning (lucky coincidence) or reach a plausible-sounding wrong conclusion via a reasoning shortcut.
**Mechanism:** Add "reasoning path verification" to the Oracle's L2 audit. For complicated and complex beads, the Oracle should not just verify that the output is correct -- it should verify that the reasoning chain in the runner's output is logically valid. Specifically: check for cases where the runner's stated rationale does not actually support the conclusion (the reasoning is a post-hoc justification, not the actual derivation). Implementation: Oracle Layer 1 (static) checks for logical coherence between stated reasoning and conclusion.
**Where:** `skills/sdlc-orchestrate/SKILL.md` Oracle section (Layer 1 audit scope expansion).

### NE-10. Peak-End Rule Applied to User-Facing Outputs
**Concept:** The peak-end rule applied to the delivery summary -- the user's impression of the SDLC's work will be dominated by the most intense moment and the final summary, not the average quality across all beads.
**Rating: LOW**
**Gap:** The delivery summary in Phase 5 is structured as a factual report (fitness report, evidence, uncertainty, next actions). It does not account for how the user will perceive it. A delivery summary that buries a critical residual risk in the middle of a long list of clean results will be perceived as "clean delivery" even if the risk is significant.
**Mechanism:** Structure the delivery summary to front-load the highest-severity residual risks and end with a clear, honest confidence statement. Add an explicit "Peak Risk" section at the top of the delivery summary that surfaces the single highest-risk item from across all beads, regardless of its resolution status. This ensures the user's peak impression aligns with the actual peak risk rather than the average.
**Where:** `skills/sdlc-orchestrate/SKILL.md` Phase 5 delivery summary format.

### NE-11. Endowment Effect (Prospect Theory)
**Concept:** People value things they own more than identical things they do not own. Applied to code: agents (and humans) value code they wrote more than equivalent code that already exists.
**Rating: LOW**
**Gap:** The reuse-first protocol (`sdlc-os:sdlc-reuse`) partially addresses this by searching for existing solutions before implementation. However, once a runner has written code, there is no mechanism to check whether the runner's new code is genuinely better than the existing solution it chose not to reuse. The runner might acknowledge the reuse scout's findings but still write new code because of implicit endowment effect -- preferring its own output.
**Mechanism:** In L1 Sentinel verification, when a reuse-scout report was provided and the runner wrote new code instead, add a mandatory "reuse rejection justification" check. The sentinel verifies that the runner's stated reason for not reusing is substantive (the existing solution does not meet requirements) rather than cosmetic (the existing solution "could be improved"). If the justification is weak, flag for Conductor review.
**Where:** `skills/sdlc-loop/SKILL.md` Level 1 (Sentinel Loop), as an additional verification criterion when reuse-scout reports are present.

### NE-12. Scope Insensitivity
**Concept:** People's willingness to pay to address a problem does not scale linearly with the problem's magnitude. Saving 2,000 birds feels almost as important as saving 200,000 birds. Applied to code: a bead affecting 2 users gets similar review depth to one affecting 200,000 users.
**Rating: LOW**
**Gap:** The Cynefin classification considers complexity but not scope of impact. A Clear bead that changes a user-facing API endpoint serving millions of requests gets less review than a Complex bead that refactors an internal utility used by 3 developers. The scaling heuristics in `skills/sdlc-adversarial/scaling-heuristics.md` consider what the code does (auth, I/O, business logic) but not how many users/requests it affects.
**Mechanism:** Add an "impact scope" dimension to the Cynefin classification heuristics. Beads affecting high-traffic paths (>N requests/day or >N users) should receive minimum Complicated-level review regardless of code complexity. This ensures review depth scales with blast radius, not just technical complexity.
**Where:** `skills/sdlc-adversarial/scaling-heuristics.md` (Cynefin classification signals).

### NE-13. Status Quo Bias
**Concept:** People prefer the current state of affairs. Changes from the status quo are perceived as losses. Applied to code: "it works now" creates resistance to refactoring even when the current implementation is suboptimal.
**Rating: LOW**
**Gap:** The fitness functions check for DRY, SSOT, SoC violations in new code, but the drift-detector does not flag cases where the status quo itself is the problem. If existing code has a fitness score of 50/100 and new code maintains that score, the system reports "no regression" rather than "existing debt." The normalizer catches unstructured changes but does not flag existing architectural debt.
**Mechanism:** In Phase 2 (Scout), when the gap-analyst runs in Finder mode, add a "Status Quo Quality Baseline" step. Before deciding what beads are needed, measure the fitness score of the existing code in the affected area. If the baseline is below threshold (e.g., <60), surface this explicitly: "The code area you are modifying has pre-existing quality debt [specifics]. The task scope may need to include debt remediation." This counteracts the tendency to treat existing poor code as an acceptable baseline.
**Where:** `skills/sdlc-orchestrate/SKILL.md` Phase 2 (Scout), `skills/sdlc-gap-analysis/SKILL.md` Finder mode.

---

## Summary Statistics

| Category | Count |
|---|---|
| **ALREADY EMBEDDED** | 13 concepts |
| **PARTIALLY EMBEDDED** | 5 concepts |
| **NOT YET EMBEDDED (HIGH)** | 3 concepts |
| **NOT YET EMBEDDED (MEDIUM)** | 6 concepts |
| **NOT YET EMBEDDED (LOW)** | 4 concepts |
| **Total Kahneman concepts analyzed** | 31 |

## Key Findings

The system has remarkably deep Kahneman integration. The adversarial collaboration protocol, System 1/2 dual-process architecture, WYSIATI sweeps, noise audits with three noise types, MAP scoring, anchoring countermeasures, and premortem analysis are all mechanically implemented -- not just referenced. This is not surface-level citation; these are structural design decisions.

The most significant gaps are:

1. **Focusing Illusion (HIGH)** -- The system catches what agents never looked at (WYSIATI) but not what agents looked at disproportionately. Attention asymmetry within reviewed files is invisible.

2. **Duration Neglect / Peak-End (HIGH)** -- The system accumulates evidence chronologically but does not correct for temporal bias. Beads that barely survived 24 agent invocations are treated identically to beads that passed cleanly, once both reach "hardened" status.

3. **Certainty Effect (HIGH)** -- The system treats probability changes linearly. The qualitative shift from "zero findings" to "one finding" (breaking certainty) deserves special treatment it does not currently receive.

The partially-embedded concepts reveal a pattern: Kahneman's ideas are well-implemented at the individual-agent level (arbiter MAP, red team anti-anchoring, premortem loss framing) but less implemented at the Conductor/system level (Conductor decision-making is unstructured, base rates are not injected into Phase 1, the Task-Level Prior Adjustments amplify availability bias). The next frontier is applying the same rigor to the Conductor's own judgment that the system already applies to its agents.