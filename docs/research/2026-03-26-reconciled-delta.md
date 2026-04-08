# Reconciled Delta: New Research Findings vs. Existing Research + Implementation

**Date:** 2026-03-26
**Input files (existing research + implementation):**
- `docs/specs/2026-03-25-aqs-v2-research-synthesis.md` (424 lines, 32 prioritized concepts)
- `docs/plans/2026-03-25-v3-research-upgrade.md` (implementation plan, 5 streams)
- `docs/sdlc/completed/v3-research-upgrade-20260325/state.md` (status: complete)
- `docs/specs/2026-03-25-adversarial-quality-system-design.md` (AQS design spec)
- Actual codebase: `skills/sdlc-adversarial/SKILL.md`, `skills/sdlc-loop/SKILL.md`, `skills/sdlc-harden/SKILL.md`, `references/calibration-protocol.md`, `references/precedent-system.md`, `references/quality-slos.md`, `skills/sdlc-adversarial/arbitration-protocol.md`

**Input files (new research):**
- `docs/research/2026-03-26-kahneman-gap-analysis.md` (Kahneman: 31 concepts)
- `docs/research/2026-03-26-karpathy-gap-analysis.md` (Karpathy: 32 concepts)
- `docs/research/2026-03-26-yegge-gap-analysis.md` (Yegge: 37 concepts)
- `docs/research/2026-03-26-additional-thinkers-research.md` (6 categories, ~35 concepts)

---

## DUPLICATE -- Already in Existing Research AND Implemented

### From Kahneman Gap Analysis

| # | Concept | Existing Research Citation | Implementation Citation |
|---|---------|--------------------------|----------------------|
| 1 | Adversarial Collaboration Protocol | Synthesis Part I, Section 3F (Reasoned rules), Part IV-H (Judge/Evaluator) | `arbitration-protocol.md` (full Kahneman protocol, Steps 0-5), `agents/arbiter.md` |
| 2 | System 1 / System 2 Dual Process | Synthesis Part I, Section 3E | `skills/sdlc-harden/SKILL.md` lines 32-43 (Dual-Process Scheduling table) |
| 3 | Noise Audits (three types) | Synthesis Part I, Section 3A-3B (Noise audits, three types of noise) | `references/calibration-protocol.md` lines 53-78 (full noise audit with level/pattern/occasion) |
| 4 | MAP Scoring | Synthesis Part I, Section 3C (Mediating Assessments Protocol) | `arbitration-protocol.md` lines 131-140 (four-dimension MAP scoring) |
| 5 | Reference Class Forecasting | Synthesis Part I, Section 3D | `agents/reliability-conductor.md` (observability profile as reference class anchor) |
| 6 | Premortem Analysis | Synthesis Part I, Section 5B (Key Assumptions Check) | `skills/sdlc-harden/SKILL.md` Step 0 (3 independent haiku premortem agents) |
| 7 | Anchoring Bias Countermeasures | Implicit in research (anti-anchoring in red team design) | `agents/red-reliability-engineering.md` ("Critical anti-anchoring rule"), red team never sees blue team self-assessment |
| 8 | WYSIATI (What You See Is All There Is) | Implicit in HRO principles (Synthesis Part II-A) | `skills/sdlc-harden/SKILL.md` Step 7 (WYSIATI Coverage Sweep) |
| 9 | Overconfidence Countermeasures | Synthesis Part IV-F (Confidence Calibration) | VORP standard, Daubert gate, confidence scores on all agents |
| 10 | Halo Effect Prevention | Synthesis Part I, Section 3C (MAP prevents halo) | MAP independent dimension scoring in `arbitration-protocol.md` |

**Note:** The Kahneman gap analysis found 13 concepts "Already Embedded" and 5 "Partially Embedded." All 13 already-embedded trace to existing research. The 5 partially-embedded are covered below.

### From Karpathy Gap Analysis

| # | Concept | Existing Research Citation | Implementation Citation |
|---|---------|--------------------------|----------------------|
| 1 | Hypothesis-Experiment-Evidence loop | Synthesis Part I, Section 5A (ACH) + "Karpathy: Already well-used" (line 98) | `references/instrumented-loop.md` lines 7-18 (Karpathy Principle) |
| 2 | Baseline-First | Synthesis line 98 ("Karpathy: Already well-used") | `references/instrumented-loop.md` line 20 |
| 3 | One Variable at a Time | Synthesis line 98 | `skills/sdlc-loop/SKILL.md` line 24 |
| 4 | Evidence Over Argument | Synthesis line 98 | VORP standard in `skills/sdlc-orchestrate/SKILL.md` |
| 5 | Bayesian Belief Updating | Synthesis Part II-H (Control Theory), Part IV-F (Confidence Calibration) | `references/instrumented-loop.md` lines 26-52 (confidence ledger) |
| 6 | Prior Accumulation Across Tasks | Synthesis Part II-L (Information-Theoretic Drift) | `skills/sdlc-loop/SKILL.md` lines 310-318 (Task-Level Prior Adjustments) |
| 7 | Hard Budgets | Synthesis Part II-K (Theory of Constraints) | `skills/sdlc-loop/SKILL.md` lines 207-221 (budget table) |
| 8 | Calibration Loop | Synthesis concepts #4 (Agent drift monitoring) + #12 (Noise audits) | `references/calibration-protocol.md` + L6 loop |
| 9 | Error Budget / SLO | Synthesis concept #9 (Error budgets for quality) | `references/quality-slos.md` (fully implemented) |
| 10 | Pretrial Filter / Res Judicata | Synthesis concept #11 (Pretrial filtering) | `skills/sdlc-adversarial/SKILL.md` Phase 2.5 |
| 11 | Daubert Evidence Gate | Synthesis concept #8 (Daubert evidence gate) | `skills/sdlc-adversarial/SKILL.md` Phase 3, step 5.5 |
| 12 | Non-Zero-Sum Objective Separation | Synthesis Part II-E (Antifragility -- implicit), AQS design spec Section 4.2 | `skills/sdlc-adversarial/SKILL.md` lines 293-303 |

### From Yegge Gap Analysis

| # | Concept | Existing Research Citation | Implementation Citation |
|---|---------|--------------------------|----------------------|
| 1 | Beads as Atomic Work Units | Core system design (predates research) | `skills/sdlc-orchestrate/SKILL.md` bead format |
| 2 | Colony/Factory Model | Core system design | Full conductor-runner-sentinel-oracle architecture |
| 3 | Disposable Ephemeral Workers | Core system design | Runner and guppy disposability |
| 4 | Guppy/Swarm Pattern | Core system design | `skills/sdlc-swarm/SKILL.md` |
| 5 | Watchdog/Supervisor Chain | Core system design | Sentinel + Oracle + L6 Calibration |
| 6 | Escalation with Budgets | Core system design | L0-L5 loop hierarchy |
| 7 | State Persistence in Git | Core system design | Bead files + AQS resume-from-state |
| 8 | NDI (Nondeterministic Idempotence) | Synthesis -- implicit in loop design | `skills/sdlc-harden/SKILL.md` ("State Persistence (Yegge NDI)") |
| 9 | Rule of Five (Multi-Pass Review) | Synthesis multi-layer verification | L0 -> L1 -> L2 -> L2.5 -> L2.75 |
| 10 | Cynefin-Based Scaling | Synthesis concept #1 (Cynefin task classification) | `skills/sdlc-adversarial/scaling-heuristics.md` |
| 11 | Convention/Constitution Governance | Synthesis concept #5 (Constitution-based defense) | `references/code-constitution.md`, convention map |
| 12 | Calibration/Drift Detection | Synthesis concept #4 (Agent drift monitoring) | `references/calibration-protocol.md` |

### From Additional Thinkers Research

| # | Concept | Existing Research Citation | Implementation Citation |
|---|---------|--------------------------|----------------------|
| 1 | Taleb -- Antifragility / Barbell / Via Negativa | Synthesis Part II-E (Antifragility) | Calibration beads as controlled stressors; sandwich clean steps as via negativa |
| 2 | Leveson -- STAMP/STPA | Synthesis Part II-G (STAMP/STPA) | Not yet fully implemented but explicitly in research |
| 3 | Weick -- HRO Five Principles | Synthesis Part II-A (HRO) | Partially: preoccupation with failure (premortems), sensitivity to operations (LOSA), commitment to resilience (loop hierarchy) |
| 4 | James Reason -- Swiss Cheese Model | Synthesis Part II-B (Swiss Cheese Model) | Loop hierarchy L0-L6 is the Swiss cheese model |
| 5 | Just Culture (three failure types) | Synthesis Part II-F (Just Culture) + Edmondson Section 7-16 | Implicit in error handling approach |
| 6 | Kent Beck -- TDD Red-Green-Refactor | Implicit in hypothesis-experiment-evidence loop | Karpathy Principle subsumes this |

---

## DUPLICATE -- Already in Existing Research BUT Not Yet Implemented

### From Kahneman Gap Analysis

| # | Concept | Where Researched | Status | What Remains |
|---|---------|-----------------|--------|-------------|
| 1 | Substitution Detection (PE-1) | Not in v2 synthesis but Kahneman's System 1 failure modes were researched (Synthesis 3E) | **New gap identified** -- see NET NEW section | Sentinel check comparing "question asked" vs "question answered" |
| 2 | Loss Aversion Framing (PE-2) | Not explicitly in v2 synthesis | **New gap identified** -- see NET NEW section | Loss framing in runner dispatch ("if this ships without Y, users lose Z") |
| 3 | Structured Conductor Decisions (PE-3) | Synthesis 3C mentions MAP for arbiter; Conductor decisions not mentioned | **New gap identified** -- see NET NEW section | MAP-style scoring for Conductor's Cynefin classification and escalation decisions |
| 4 | Base Rate Neglect (PE-4) | Synthesis 3D mentions reference class forecasting but only for fix complexity | **Partially new** -- see NET NEW section | Base rate lookup before Cynefin domain assignment |
| 5 | Regression to Mean (PE-5) | Not in v2 synthesis | **New gap identified** -- see NET NEW section | Dampening coefficient in Task-Level Prior Adjustments |

### From Karpathy Gap Analysis

| # | Concept | Where Researched | Status | What Remains |
|---|---------|-----------------|--------|-------------|
| 1 | Distributional Problem Profiling | Not in v2 synthesis (Phase 2 Scout exists but lacks quantitative profiling) | **New gap identified** -- see NET NEW section | Quantitative complexity distribution before bead decomposition |
| 2 | Closed-Loop Self-Improvement | Synthesis concept #5 (Constitution-based defense) + #29 (Archgate self-ratcheting) | **Planned but manual** | Auto-rule generator: 3+ occurrences of finding type -> draft new constitution rule |
| 3 | Process Reward (Step-Level Verification) | Synthesis Part IV-F (Confidence Calibration) mentions trajectory confidence | **Partially planned** | Continuous process quality signals, not just binary pass/fail at each level |

### From Yegge Gap Analysis

| # | Concept | Where Researched | Status | What Remains |
|---|---------|-----------------|--------|-------------|
| 1 | GUPP / Pull-Based Work Distribution | Not in v2 synthesis | **New concept** -- see NET NEW section | Agent-side work queue and self-scheduling |
| 2 | Proactive Handoff (context window management) | Not in v2 synthesis (session recovery exists, proactive handoff doesn't) | **New gap identified** -- see NET NEW section | Runner self-detecting context exhaustion and triggering graceful handoff |
| 3 | Bisecting Merge Queue (Refinery) | Not in v2 synthesis | **New concept** -- see NET NEW section | Sequential merge queue with Bors-style bisection on failure |

### From Additional Thinkers Research

| # | Concept | Where Researched | Status | What Remains |
|---|---------|-----------------|--------|-------------|
| 1 | STAMP/STPA Control Analysis | Synthesis Part II-G (explicit mention) | **Researched but not implemented** | Systematic unsafe control action enumeration during Phase 3 |
| 2 | Swiss Cheese Hole Alignment Analysis | Synthesis Part II-B + concept #27 | **Researched but not implemented** | Explicit mapping of which defect types each loop layer catches; finding correlated blind spots |
| 3 | Double-Loop Learning / Meta-Analysis | Synthesis concept #18 (Double-loop meta-analysis) | **Researched but not implemented** | After N sessions, meta-analysis agent reviews bug patterns and modifies prompts/checklists |
| 4 | Chaos Injection for Process | Synthesis concept #25 (Chaos injection) | **Researched but not implemented** | Inject process-level chaos (incomplete context, conflicting convention), not just code-level defects |
| 5 | Archgate Self-Ratcheting ADRs | Synthesis concept #29 | **Researched but not implemented** | Violations during review automatically become permanent rules |

---

## NET NEW -- Not in Existing Research, Genuinely Novel Addition

Sorted by priority: HIGH -> MEDIUM -> LOW.

---

### HIGH Priority

**1. Focusing Illusion / Proportionality Audit**
- **Source:** Kahneman gap analysis (NE-1)
- **Rating:** HIGH
- **Description:** The system catches what agents never looked at (WYSIATI sweep) but not what agents looked at *disproportionately*. A security audit might focus entirely on input validation while ignoring authorization in the same file -- both were "seen" but attention was asymmetric. A "Proportionality Audit" at Phase 5 would measure agent-turns spent per concern area vs. the risk profile and flag imbalances.
- **Where it would go:** `skills/sdlc-orchestrate/SKILL.md` Phase 5: Synthesize.

**2. Duration Neglect / Peak-End Rule / Turbulence Score**
- **Source:** Kahneman gap analysis (NE-2)
- **Rating:** HIGH
- **Description:** The system accumulates evidence chronologically but does not account for temporal bias. A bead that required 24 agent invocations to reach "hardened" is treated identically to one that passed on first attempt once both reach "hardened" status. A "turbulence score" surfacing full correction history in the delivery summary would prevent the peak-end rule from masking troubled beads.
- **Where it would go:** `skills/sdlc-orchestrate/SKILL.md` Phase 5 delivery summary, `skills/sdlc-loop/SKILL.md` bead status extensions.

**3. Certainty Effect / Zero-to-One Signal**
- **Source:** Kahneman gap analysis (NE-3)
- **Rating:** HIGH
- **Description:** The system treats probability changes linearly. Going from "zero findings" to "one finding" should trigger a qualitatively different response than going from "three" to "four" because it breaks a certainty threshold. When a Clear-domain bead produces any finding, it should auto-escalate to Complicated and require Cycle 2 regardless of convergence indicators.
- **Where it would go:** `skills/sdlc-adversarial/SKILL.md` Cycle Budget section, `skills/sdlc-adversarial/scaling-heuristics.md`.

**4. Slopacolypse Defense / Simplicity Audit**
- **Source:** Karpathy gap analysis (NE-1)
- **Rating:** HIGH
- **Description:** The system verifies correctness (tests pass, VORP satisfied, AQS finds no vulnerabilities) but has no explicit check for *unnecessary complexity introduced by agents*. A simplicity audit at L1 sentinel would compare the solution's complexity against the problem's inherent complexity, flagging disproportionate abstraction layers, dead code, or over-engineering.
- **Where it would go:** `skills/sdlc-loop/SKILL.md` L1 sentinel loop, `skills/sdlc-fitness/SKILL.md` as new fitness dimension.

**5. Explicit Per-Step Reliability Tracking (March of Nines)**
- **Source:** Karpathy gap analysis (NE-2)
- **Rating:** HIGH
- **Description:** The system tracks which loops exhaust budgets but not per-step success rates (e.g., "L0 passes first attempt 72% of the time"). Without this data, the Conductor cannot identify reliability bottlenecks. A reliability ledger recording L0/L1/L2/L2.5 attempt counts per bead, aggregated across tasks, would enable data-driven system improvement.
- **Where it would go:** `skills/sdlc-loop/SKILL.md` bead status extensions, `references/quality-slos.md` (add per-step SLIs).

**6. Deterministic Task Routing**
- **Source:** Karpathy gap analysis (NE-3)
- **Rating:** HIGH
- **Description:** All work dispatches through LLM agents. Tasks like "check if file X exists," "count lines changed," or "verify import graph has no cycles" could be handled by deterministic scripts with 100% reliability. A deterministic task catalog classifying each check as `deterministic` or `reasoning-required` would reduce the number of LLM steps, directly improving p^n reliability.
- **Where it would go:** `skills/sdlc-orchestrate/SKILL.md` bead spec, `skills/sdlc-loop/SKILL.md` L1 sentinel, new reference `references/deterministic-checks.md`.

**7. Hook / Pull-Based Work Distribution**
- **Source:** Yegge gap analysis (NE-22)
- **Rating:** HIGH
- **Description:** Work distribution is entirely push-based (Conductor dispatches). There is no agent-side work queue or self-scheduling. A hook mechanism would enable more autonomous operation, reduce Conductor bottlenecks, and support persistent colony operation.
- **Where it would go:** `skills/sdlc-orchestrate/SKILL.md` dispatch model.

**8. Persistent Agent Identity with CV Chains**
- **Source:** Yegge gap analysis (NE-23)
- **Rating:** HIGH
- **Description:** Runners are purely disposable with no persistent identity. The system cannot learn which runner configurations perform best or track agent performance over time. Persistent identity with CV chains would enable per-agent performance tracking, drift detection at the individual level, and data-driven prompt optimization.
- **Where it would go:** `references/calibration-protocol.md`, new reference for agent identity tracking.

**9. Deacon Pattern / Autonomous Daemon Supervisor**
- **Source:** Yegge gap analysis (NE-24)
- **Rating:** HIGH
- **Description:** All supervision is Conductor-initiated. If the Conductor stalls, there is no watchdog watching the watchdog. A Deacon-equivalent daemon with heartbeat would ensure the SDLC pipeline continues operating even when the Conductor session is lost.
- **Where it would go:** System architecture level -- new agent pattern.

**10. LLM-as-Judge Bias Mitigation (Position Bias, Verbosity Bias)**
- **Source:** Additional thinkers research (Section 6.1)
- **Rating:** HIGH
- **Description:** Research documents 12+ systematic biases in LLM-as-Judge systems: position bias (~40% decision flips when answer order swaps), verbosity bias (~15% inflation for longer answers). The entire AQS uses LLM-as-judge at multiple points. Mitigations: randomize argument presentation order in arbiter prompts, add rubric penalizing verbosity without substance in severity definitions, domain-specific calibration beads.
- **Where it would go:** `references/adversarial-quality.md`, agent prompt templates (`agents/arbiter.md`, `agents/red-*.md`), `references/calibration-protocol.md`.

**11. Reward Hacking / Specification Gaming Defense**
- **Source:** Additional thinkers research (Section 6.2)
- **Rating:** HIGH
- **Description:** RL-trained models exploit reward function flaws. In the SDLC, this manifests as: runners producing tests that pass but do not test the right thing, red team producing findings that look legitimate but test irrelevant properties, blue team producing fixes satisfying the literal claim but not its spirit. New mitigation: outcome-independent verification -- periodically evaluate final deployed behavior vs. artifacts' claims. Also: reward signal upper bounds to prevent infinitely confident/detailed outputs.
- **Where it would go:** `references/calibration-protocol.md` (new section), `skills/sdlc-loop/SKILL.md` L6 loop.

**12. Donella Meadows -- Leverage Points Hierarchy**
- **Source:** Additional thinkers research (Section 1.1)
- **Rating:** HIGH
- **Description:** Ranks 12 intervention points from weakest (tweaking parameters) to strongest (changing the paradigm). The Conductor currently makes ad-hoc decisions about where to invest correction effort. A leverage assessment during Phase 3 would tag each bead with its leverage tier. Higher-leverage beads (information flow changes, rule changes) get more scrutiny; lower-leverage beads (parameter tweaks) fast-track.
- **Where it would go:** `skills/sdlc-orchestrate/SKILL.md` Phase 3 (Architect), bead spec format.

**13. Deming -- Common Cause vs. Special Cause Variation**
- **Source:** Additional thinkers research (Section 1.3)
- **Rating:** HIGH
- **Description:** The noise audit measures variation but does not classify it as common cause (inherent to system -- fix prompts/rubrics/temperature) vs. special cause (attributable to specific factor -- fix that agent). Tampering = treating common cause as special cause. The system should prohibit recalibrating individual agent prompts based on single-session performance -- only control-chart-verified sustained drift warrants intervention.
- **Where it would go:** `references/calibration-protocol.md` (enhance noise audit with common/special cause classification).

**14. Dekker -- Drift Into Failure / Normalization of Deviance Detection**
- **Source:** Additional thinkers research (Section 2.2)
- **Rating:** HIGH
- **Description:** The existing drift-detector catches architectural drift but not *process drift* (normalization of deviance). The system should track whether: fast-track resolutions are increasing over time, error budget "healthy" periods are growing without recalibration, Clear bead classifications are expanding. A "deviance normalization detector" metric in the calibration protocol addresses drift in the quality process itself, not just the codebase.
- **Where it would go:** `references/calibration-protocol.md` (new section: Process Drift Detection).

**15. Actor Model -- Let-It-Crash / Supervision Tree Restructure**
- **Source:** Additional thinkers research (Section 5.1)
- **Rating:** HIGH
- **Description:** The loop hierarchy conflates detection and recovery at each level. The actor model cleanly separates these. The "let it crash" insight suggests runners should NOT attempt 3 self-correction attempts at L0 -- self-correction risks papering over fundamental misunderstandings. Instead: 1 attempt, then crash to L1 (sentinel/supervisor has more context). Making the supervision tree explicit with defined restart strategies per level would clarify escalation behavior.
- **Where it would go:** `skills/sdlc-loop/SKILL.md` L0 budget and escalation model.

**16. Surowiecki -- Four Conditions for Wise Crowds**
- **Source:** Additional thinkers research (Section 5.2)
- **Rating:** HIGH
- **Description:** Multi-agent consensus requires four conditions: diversity, independence, decentralization, effective aggregation. The system uses multi-agent consensus extensively (premortems, recon bursts, red/blue teams) but does not verify these conditions hold. Diversity should be measured (unique failure modes / total). Aggregation should use formal mechanisms (majority voting for severity, weighted averaging for confidence) rather than ad hoc Conductor deduction.
- **Where it would go:** `skills/sdlc-harden/SKILL.md` Step 0 (premortem), `skills/sdlc-adversarial/SKILL.md` recon burst, `skills/sdlc-orchestrate/SKILL.md` aggregation.

---

### MEDIUM Priority

**17. Diminishing Sensitivity / Finding Saturation Threshold**
- **Source:** Kahneman gap analysis (NE-4)
- **Rating:** MEDIUM
- **Description:** The 11th medium-severity finding gets the same treatment as the 1st. If a bead accumulates >N findings (default 5), the Conductor should pause strikes and dispatch a "systemic assessment" asking whether these are symptoms of a single root cause. Prevents diminishing returns on individual remediation.
- **Where it would go:** `skills/sdlc-adversarial/SKILL.md` Phase 3 (saturation circuit breaker).

**18. Experienced Utility vs. Decision Utility / Production Outcome Tracker**
- **Source:** Kahneman gap analysis (NE-5)
- **Rating:** MEDIUM
- **Description:** No feedback loop from actual production outcomes back to predictions made during Frame/Scout/Architect. After N days in production, check: were premortem predictions realized? Were dismissed AQS findings actually triggered? Were there issues not predicted? Closes the prediction-outcome gap.
- **Where it would go:** `references/calibration-protocol.md` (new section), `skills/sdlc-loop/SKILL.md` L6 loop.

**19. Availability Heuristic / Base Rate Anchor for Domain Selection**
- **Source:** Kahneman gap analysis (NE-6)
- **Rating:** MEDIUM
- **Description:** If the previous three beads all had security findings, the Conductor will over-prioritize security on the 4th bead via availability bias. Task-Level Prior Adjustments amplify this. Before applying priors, consult the full historical distribution from the precedent database and flag disproportionate emphasis.
- **Where it would go:** `skills/sdlc-adversarial/SKILL.md` Phase 2, `skills/sdlc-loop/SKILL.md` Task-Level Prior Adjustments.

**20. Representativeness Heuristic / Context Override in Daubert**
- **Source:** Kahneman gap analysis (NE-7)
- **Rating:** MEDIUM
- **Description:** Red team guppies flag patterns that "look like" vulnerabilities (string concatenation near DB call) even when the context makes it benign (log message). Add a "Context Override" check to Daubert: "Does the surrounding code context make this pattern benign despite surface similarity?"
- **Where it would go:** `skills/sdlc-adversarial/SKILL.md` Phase 3 (Daubert gate, new criterion).

**21. Sunk Cost Fallacy / Fresh Eyes Protocol for L4 Escalation**
- **Source:** Kahneman gap analysis (NE-8)
- **Rating:** MEDIUM
- **Description:** When the Conductor has invested heavily in a design approach through multiple beads and it is failing, sunk cost bias pushes toward preserving existing work. At L4 escalation, force the question: "If starting from scratch with everything I know, would I choose the same design?" If no, change the design regardless of work completed.
- **Where it would go:** `skills/sdlc-loop/SKILL.md` Level 4 (Phase Loop).

**22. Cognitive Reflection / Reasoning Path Verification**
- **Source:** Kahneman gap analysis (NE-9)
- **Rating:** MEDIUM
- **Description:** No mechanism tests whether agents give "bat and ball" answers -- plausible but wrong. Oracle verifies claims are supported but not that the reasoning chain is valid. Add reasoning path verification: check that stated rationale actually supports the conclusion.
- **Where it would go:** `skills/sdlc-orchestrate/SKILL.md` Oracle section (Layer 1 audit scope expansion).

**23. Distributional Problem Profiling ("Become One with the Data")**
- **Source:** Karpathy gap analysis (NE-4)
- **Rating:** MEDIUM (originally HIGH in source but partially addressed by Scout phase)
- **Description:** Phase 2 (Scout) gathers facts but does not produce a quantitative distributional profile (lines per module, cyclomatic complexity per function, test coverage per module, churn rate per file). Feed this into Phase 3 so bead decomposition is grounded in empirical data, not intuition.
- **Where it would go:** `skills/sdlc-orchestrate/SKILL.md` Phase 2 (Scout).

**24. Closed-Loop Self-Improvement / Auto-Rule Generator**
- **Source:** Karpathy gap analysis (NE-5)
- **Rating:** MEDIUM
- **Description:** When a finding type appears 3+ times across tasks, automatically draft a new constitution rule for Conductor approval. When an attack vector proves effective 3+ times, auto-add to domain attack library. Closes the learning loop without removing human judgment.
- **Where it would go:** `skills/sdlc-adversarial/SKILL.md` Phase 6, `references/code-constitution.md`.

**25. Autoresearch-Style Experimental Loop for System Tuning**
- **Source:** Karpathy gap analysis (NE-6)
- **Rating:** MEDIUM
- **Description:** When calibration detects drift, generate N parameter variations (guppy counts, prompt phrasings), run calibration bead against each, keep the variation with highest detection rate. Automated experimentation for the system's own configuration.
- **Where it would go:** `references/calibration-protocol.md`, new reference `references/autotune-protocol.md`.

**26. Cognitive Debt Tracking / Comprehensibility Dimension**
- **Source:** Karpathy gap analysis (NE-7)
- **Rating:** MEDIUM
- **Description:** The system tracks technical quality but not cognitive debt -- the cost of understanding generated code. A readability/comprehensibility fitness dimension measuring naming clarity, function length distribution, nesting depth, and idiom consistency.
- **Where it would go:** `skills/sdlc-fitness/SKILL.md` as new fitness dimension.

**27. LLM Failure Mode Checklist ("Animals vs. Ghosts")**
- **Source:** Karpathy gap analysis (NE-8)
- **Rating:** MEDIUM
- **Description:** Sentinel should specifically check for ghost-specific failure modes: hallucinated file paths, confident assertions without evidence, solutions that pattern-match a template but do not fit the specific problem, unnecessary complexity from "helpful" overengineering.
- **Where it would go:** `skills/sdlc-loop/SKILL.md` L1 sentinel loop.

**28. Context Budget Estimation (Tokenization/Context Window Awareness)**
- **Source:** Karpathy gap analysis (NE-9)
- **Rating:** MEDIUM
- **Description:** Before sending a context packet to a runner, estimate token count and flag if exceeding 80% of effective context. For numeric/structural data, prefer file path references over inline content. For counting/arithmetic tasks, instruct code execution over mental arithmetic.
- **Where it would go:** `skills/sdlc-orchestrate/SKILL.md` runner dispatch section.

**29. MEOW Stack / Workflow Template Hierarchy**
- **Source:** Yegge gap analysis (NE-25)
- **Rating:** MEDIUM
- **Description:** No formal workflow template/instantiation system. Protomolecules for common patterns ("audit-then-fix", "investigate-design-implement") would reduce Conductor overhead. Formulas as reusable templates.
- **Where it would go:** New reference for workflow templates.

**30. Wisps / Ephemeral Non-Persisted Orchestration Beads**
- **Source:** Yegge gap analysis (NE-26)
- **Rating:** MEDIUM
- **Description:** Every bead and AQS artifact persists to Git, creating noise for large tasks. Wisps would let ephemeral verification work (recon bursts, sentinel micro-checks) execute without polluting the repository, burning down to summary lines.
- **Where it would go:** `skills/sdlc-adversarial/SKILL.md` artifact persistence, `skills/sdlc-harden/SKILL.md`.

**31. Mayor / Dedicated Concierge Agent**
- **Source:** Yegge gap analysis (NE-32)
- **Rating:** MEDIUM
- **Description:** The Conductor serves as both orchestrator AND user-facing interface. A dedicated concierge handling user communication, progress reporting, and decision solicitation would let orchestration logic focus purely on work distribution.
- **Where it would go:** `skills/sdlc-orchestrate/SKILL.md` separation of concerns.

**32. Desire Paths / Agent UX Feedback Loop**
- **Source:** Yegge gap analysis (NE-34)
- **Rating:** MEDIUM
- **Description:** Agent definitions are designed by the human operator, not iteratively shaped by observing agent behavior. A feedback mechanism detecting when agents struggle with dispatch format, context packet structure, or output format would surface improvement opportunities.
- **Where it would go:** `references/dispatch-patterns.md`, agent definitions.

**33. Heresies Detection / Agent Misconceptions Registry**
- **Source:** Yegge gap analysis (NE-36)
- **Rating:** MEDIUM
- **Description:** The code constitution addresses code-level conventions but not agent-level misconceptions. A heresies registry would document known recurring incorrect assumptions agents make about the system itself. Calibration could test whether agents still hold them.
- **Where it would go:** `references/calibration-protocol.md`, agent prompts.

**34. Crew Pattern / Long-Lived Design Agents**
- **Source:** Yegge gap analysis (NE-37)
- **Rating:** MEDIUM
- **Description:** All agents are ephemeral. A Crew-equivalent for design work would enable richer architectural reasoning drawing on accumulated project context rather than starting fresh each time. Relevant for Phase 3 (Architect) and long-running complex projects.
- **Where it would go:** `skills/sdlc-orchestrate/SKILL.md` Phase 3.

**35. Sterman -- System Dynamics Delays / Delay Budget**
- **Source:** Additional thinkers research (Section 1.4)
- **Rating:** MEDIUM (originally HIGH but partially addressed by L6 cadence)
- **Description:** The system has multiple feedback loops but no explicit delay accounting. The L6 calibration loop firing every 5th task creates dangerous multi-task delay. Add a delay budget per loop level and track quality decline *velocity* (rate of change matters more than current level). Leading indicators at L1 should predict L6 problems.
- **Where it would go:** `references/calibration-protocol.md`, `references/quality-slos.md`.

**36. Snowden -- Distributed Cognition / Narrative Patterns (beyond Cynefin)**
- **Source:** Additional thinkers research (Section 1.5)
- **Rating:** MEDIUM
- **Description:** Beyond Cynefin (already implemented), Snowden's micro-narrative approach would have all agents at Phase 5 answer: "In one paragraph, what surprised you about this task?" Pattern-matching across narratives surfaces systemic issues invisible to the Conductor individually.
- **Where it would go:** `skills/sdlc-orchestrate/SKILL.md` Phase 5 (Synthesize).

**37. Fred Brooks -- Essence vs. Accident Classification**
- **Source:** Additional thinkers research (Section 3.1)
- **Rating:** MEDIUM (originally HIGH but overlaps significantly with Cynefin)
- **Description:** More nuanced than Cynefin: classify bead complexity as *essential* (novel business logic, state machines) or *accidental* (framework boilerplate, config, migration scripts). Essential = full L2.5/L2.75. Accidental = skip adversarial review. Orthogonal to Cynefin's knowability dimension.
- **Where it would go:** `skills/sdlc-adversarial/scaling-heuristics.md`, bead spec format.

**38. Gary Klein -- Recognition-Primed Decision (RPD) / Conductor Fast-Path**
- **Source:** Additional thinkers research (Section 4.1)
- **Rating:** MEDIUM (originally HIGH but overlaps with precedent system)
- **Description:** For familiar problem types matching established precedents with >80% similarity, the Conductor should operate in recognition mode: match to precedent, simulate via quick haiku probe, execute without full analytical decomposition. Skip Phases 1-3 for beads matching known solution templates.
- **Where it would go:** `skills/sdlc-orchestrate/SKILL.md`, `references/precedent-system.md`.

**39. Gigerenzer -- Fast-and-Frugal Heuristics / Single-Cue Decision Trees**
- **Source:** Additional thinkers research (Section 4.3)
- **Rating:** MEDIUM
- **Description:** For well-structured decisions, a single-cue heuristic is more robust than multi-factor analysis. Cynefin fast classification: if bead touches auth, it is Complex -- one cue. AQS convergence: if any critical finding, Cycle 2 mandatory -- one cue. Reduces Conductor decision overhead and is more robust against context pollution.
- **Where it would go:** `skills/sdlc-adversarial/scaling-heuristics.md`, `skills/sdlc-orchestrate/SKILL.md`.

**40. Multi-Agent Debate Enhancements (Tool-MAD / ColMAD)**
- **Source:** Additional thinkers research (Section 6.3)
- **Rating:** MEDIUM
- **Description:** Two enhancements: (1) tool diversity -- assign different verification approaches per guppy (grep, AST analysis, test execution) to reduce correlated blind spots; (2) cooperative meta-review -- after adversarial cycle, red and blue collaboratively identify what both sides missed.
- **Where it would go:** `skills/sdlc-adversarial/SKILL.md` Phase 3 (guppy dispatch), Phase 6 (post-cycle review).

**41. Constitutional AI Self-Critique + Constitution Staleness Check**
- **Source:** Additional thinkers research (Section 6.4)
- **Rating:** MEDIUM
- **Description:** Every runner output should include a self-critique section evaluating against the constitution before submitting to L1. Additionally, a constitution staleness check should verify rules still catch real defects, not just defects the system has learned to produce and detect in a closed loop.
- **Where it would go:** `skills/sdlc-loop/SKILL.md` L0 runner loop, `references/calibration-protocol.md`.

---

### LOW Priority

**42. Peak-End Rule for Delivery Summaries**
- **Source:** Kahneman gap analysis (NE-10)
- **Rating:** LOW
- **Description:** Front-load highest-severity residual risks in delivery summary and end with honest confidence statement. Add "Peak Risk" section surfacing the single highest-risk item.
- **Where it would go:** `skills/sdlc-orchestrate/SKILL.md` Phase 5 delivery summary.

**43. Endowment Effect / Reuse Rejection Justification**
- **Source:** Kahneman gap analysis (NE-11)
- **Rating:** LOW
- **Description:** When reuse-scout found an existing solution but the runner wrote new code, L1 should verify the rejection justification is substantive, not cosmetic.
- **Where it would go:** `skills/sdlc-loop/SKILL.md` Level 1 (Sentinel).

**44. Scope Insensitivity / Impact Scope Dimension**
- **Source:** Kahneman gap analysis (NE-12)
- **Rating:** LOW
- **Description:** Add "impact scope" to Cynefin classification -- beads affecting high-traffic paths get minimum Complicated-level review regardless of code complexity.
- **Where it would go:** `skills/sdlc-adversarial/scaling-heuristics.md`.

**45. Status Quo Bias / Status Quo Quality Baseline**
- **Source:** Kahneman gap analysis (NE-13)
- **Rating:** LOW
- **Description:** Measure fitness score of existing code before deciding what beads are needed. Surface pre-existing debt explicitly.
- **Where it would go:** `skills/sdlc-orchestrate/SKILL.md` Phase 2 (Scout).

**46. Scaffolded Complexity Progression**
- **Source:** Karpathy gap analysis (NE-10)
- **Rating:** LOW
- **Description:** Sort independent beads by estimated complexity (simplest first) so the system warms up on easier work.
- **Where it would go:** `skills/sdlc-orchestrate/SKILL.md` Phase 3 (Architect).

**47. Ensemble Methods for High-Stakes Beads**
- **Source:** Karpathy gap analysis (NE-12)
- **Rating:** LOW
- **Description:** For Complex/security-sensitive beads, dispatch 2-3 independent runners with slightly different context framings. Divergence is a powerful signal.
- **Where it would go:** `skills/sdlc-orchestrate/SKILL.md` Phase 4 (Execute).

**48. Shadow Mode for New Rules/Agents**
- **Source:** Karpathy gap analysis (NE-13)
- **Rating:** LOW
- **Description:** When constitution rules or agent prompts are updated, run next task with both old and new configs in parallel. Only apply once verified.
- **Where it would go:** `references/calibration-protocol.md`.

**49. Guzzoline / Work Liquidity Metric**
- **Source:** Yegge gap analysis (NE-27)
- **Rating:** LOW
- **Description:** Track how much decomposed, ready-to-execute work exists in the pipeline. Helps Conductor decide when to decompose more vs. execute existing beads.
- **Where it would go:** Phase 4 (Execute) dispatch.

**50. Trust Ladders and Stamps / Agent Reputation**
- **Source:** Yegge gap analysis (NE-29)
- **Rating:** LOW
- **Description:** Three-level trust system for agents. Track which agent configurations produce better results over time.
- **Where it would go:** `references/calibration-protocol.md`.

**51. Collusion Detection**
- **Source:** Yegge gap analysis (NE-30)
- **Rating:** LOW
- **Description:** Detect if agents develop coordinated anti-patterns (sentinel consistently overlooking a runner's defects).
- **Where it would go:** `references/calibration-protocol.md`.

**52. Simon -- Near Decomposability Fitness Check**
- **Source:** Additional thinkers research (Section 4.4)
- **Rating:** LOW
- **Description:** Verify beads are near-decomposable: weak coupling between beads, strong cohesion within. Flag beads sharing mutable state or depending on each other's internal behavior.
- **Where it would go:** Phase 3 (Architect), bead dependency validation.

**53. March -- Exploration vs. Exploitation Budget**
- **Source:** Additional thinkers research (Section 4.5)
- **Rating:** LOW
- **Description:** Every Nth task, deliberately try a new approach (different decomposition strategy, new domain emphasis, novel probe technique). Also: calibration beads with novel planted defect types.
- **Where it would go:** `references/calibration-protocol.md`.

**54. Helland -- Saga Pattern for Cross-Bead Coordination**
- **Source:** Additional thinkers research (Section 5.3)
- **Rating:** LOW
- **Description:** When beads interact and one fails after another started, define compensating actions rather than just restarts. Relevant for post-merge replay gate.
- **Where it would go:** `skills/sdlc-loop/SKILL.md` L4 Phase Loop.

**55. Lamport -- Formal State Machine Specification**
- **Source:** Additional thinkers research (Section 3.2)
- **Rating:** LOW (originally HIGH but implementation cost is very high for a markdown plugin)
- **Description:** For Complex/security-sensitive beads, produce lightweight state machine specification (states, transitions, invariants) as acceptance criteria and red team attack surface.
- **Where it would go:** Phase 3 (Architect), bead spec for Complex beads.

---

## Summary Statistics

| Category | Count |
|---|---|
| DUPLICATE -- researched AND implemented | 34 |
| DUPLICATE -- researched but NOT YET implemented | 13 |
| NET NEW -- HIGH priority | 16 |
| NET NEW -- MEDIUM priority | 25 |
| NET NEW -- LOW priority | 14 |
| **Total NET NEW concepts** | **55** |

## Thematic Clusters in NET NEW

The 55 net-new concepts cluster into 7 themes:

1. **Attention/Proportionality gaps** (Focusing Illusion, Duration Neglect, Certainty Effect, Scope Insensitivity) -- the system catches what was missed but not what was examined disproportionately
2. **Reliability engineering for the pipeline itself** (March of Nines, Deterministic Routing, Process Drift Detection, Delay Budget, Per-Step Tracking) -- measuring and improving the SDLC system's own reliability
3. **Agent autonomy and persistence** (Hooks, Persistent Identity, Deacon, Crew, Work Liquidity) -- evolving from session-scoped orchestration to persistent colony runtime
4. **LLM-specific failure mode defense** (Slopacolypse, LLM-as-Judge Bias, Reward Hacking, Ghost Failure Modes, Specification Gaming) -- defending against failure modes unique to probabilistic agents
5. **Conductor decision quality** (Structured Decisions, Base Rate Anchors, Sunk Cost Protocol, Fast-and-Frugal Heuristics, RPD Fast-Path) -- applying to the Conductor the same rigor already applied to agents
6. **Learning loop closure** (Auto-Rule Generator, Autotune, Constitution Staleness, Production Outcome Tracker, Narrative Patterns) -- making the system self-improving
7. **Artifact management** (Wisps, Cognitive Debt Tracking, Context Budget) -- managing the overhead of the system's own operation
