I now have a thorough understanding of both the sdlc-os system and Karpathy's complete body of work. Here is the structured gap analysis report.

---

# Karpathy Gap Analysis: sdlc-os Multi-Agent SDLC Plugin

---

## ALREADY EMBEDDED

**1. Hypothesis -> Experiment -> Evidence (from "Recipe for Training Neural Networks" + "State of GPT")**
Implemented as the Karpathy Principle in `/Users/q/.claude/plugins/sdlc-os/skills/sdlc-adversarial/references/instrumented-loop.md` lines 7-18. Every red team probe is a testable hypothesis, not a vague concern. One variable at a time. Evidence required for confidence upgrades. This is a direct, cited implementation.

**2. Overfit-One-Case Sanity Gate (from "Recipe" Step 3: "overfit a single batch")**
Implemented in `instrumented-loop.md` line 18: "Before firing a full swarm, the red team commander must first overfit: pick the single most likely vulnerability and verify the attack tooling works against it." Direct translation of Karpathy's "if you can't overfit a single batch, your network won't work."

**3. Baseline-First (from "Recipe" Step 2: "set up end-to-end skeleton")**
Implemented in `instrumented-loop.md` line 20: "On Cycle 1, establish a baseline of the code's current state before attacking. On Cycle 2, compare against the Cycle 1 baseline." Directly maps to Karpathy's insistence on establishing a baseline before adding complexity.

**4. Incremental Complexity with Validation at Each Step (from "Recipe" overall philosophy)**
Implemented as the L0-L5 loop hierarchy in `/Users/q/.claude/plugins/sdlc-os/skills/sdlc-loop/SKILL.md`. Each loop level adds complexity (self-correction -> sentinel -> oracle -> AQS -> phase -> task), and each level validates before advancing. The fractal loop pattern (lines 14-22) is structurally equivalent to Karpathy's "build from simple to complex, validate at every step."

**5. One Variable at a Time (from "Recipe" debugging discipline)**
Implemented in `sdlc-loop/SKILL.md` line 24: "Each iteration changes ONE thing and measures the result. Shotgun changes that modify three things at once produce uninterpretable evidence." Also enforced per-guppy in `instrumented-loop.md` line 16.

**6. Evidence Over Argument (from "Recipe" core philosophy)**
Implemented across the system as VORP standard (Verifiable, Observable, Repeatable, Provable) in `sdlc-orchestrate/SKILL.md` line 70 and the Bayesian evidence accumulation protocol in `instrumented-loop.md` lines 26-52. Confidence upgrades require new evidence, never argument.

**7. Bayesian-Lite Belief Updating (from "State of GPT" on chain of thought + process reward)**
Implemented as confidence ledger and belief update per cycle in `instrumented-loop.md` lines 26-52. Finding confidence trajectories track upgrade/stable/degrade across cycles. Domain-level risk estimates track pre-AQS through post-cycle deltas.

**8. Prior Accumulation Across Tasks (from Tesla Data Engine pattern)**
Implemented in `sdlc-loop/SKILL.md` lines 310-318 (task-level prior adjustments) and `instrumented-loop.md` line 50: "If the same domain finds issues across multiple beads, the Conductor should increase that domain's default priority for subsequent beads."

**9. Registered-Report Mode (from scientific rigor / pre-registration)**
Implemented in `instrumented-loop.md` lines 56-87. Red team pre-registers attack plan, expected evidence, and guppy count. Blue team receives the pre-registration alongside findings. Prevents post-hoc rationalization.

**10. Replay Gate for Cross-Bead Interactions (from Tesla shadow mode post-deployment verification)**
Implemented in `instrumented-loop.md` lines 90-108. Post-merge replay sweep fires recon guppies across the full changeset to catch cross-bead interaction bugs that per-bead AQS cannot find.

**11. Correction History / What NOT to Try (from "Recipe" avoiding repeated failures)**
Implemented in `sdlc-loop/SKILL.md` lines 226-235 as the correction signal format. Every correction includes "What NOT to try" — approaches already attempted that failed. Prevents loops from repeating the same failed approach.

**12. Hard Budgets Prevent Runaway (from "Recipe" discipline + cost control)**
Implemented as the budget table in `sdlc-loop/SKILL.md` lines 207-221. L0=3, L1=2, L2=2, L2.5=2. Worst case 24 invocations per bead. "Exhausting a budget is a signal, not a failure" (line 334).

**13. Calibration Loop / System Health Check (from Tesla Data Engine's shadow mode recalibration)**
Implemented as L6 calibration loop in `sdlc-loop/SKILL.md` lines 160-186 and the full calibration protocol in `/Users/q/.claude/plugins/sdlc-os/references/calibration-protocol.md`. Planted defect beads, detection rate baselines, regression watchlist, noise audits.

**14. Noise Audit / Consistency Measurement (from Kahneman system noise)**
Implemented in `calibration-protocol.md` lines 53-78. Re-runs AQS on the same bead with fresh agent instances, measures finding overlap. Level noise, pattern noise, and occasion noise are distinguished and addressed separately.

**15. WYSIATI Coverage Sweep (Kahneman "What You See Is All There Is")**
Implemented in `/Users/q/.claude/plugins/sdlc-os/skills/sdlc-harden/SKILL.md` lines 114-121. After all agents complete, build a coverage matrix. All-blank rows are flagged as WYSIATI gaps with "Unknown" confidence.

**16. Non-Zero-Sum Objective Separation (preventing mode collapse)**
Implemented in `sdlc-adversarial/SKILL.md` lines 293-303. Red team optimizes sustained-finding severity, blue team optimizes residual risk reduction, arbiter optimizes test fairness. Structurally enforced through separate agents with no shared context.

**17. Pretrial Filter / Res Judicata (avoiding redundant work)**
Implemented in `sdlc-adversarial/SKILL.md` lines 76-89. Scope exclusion, category exclusion, and prior resolution (matching against precedent database). Audit trail for all dismissals.

**18. Daubert Evidence Gate (evidence quality control)**
Implemented in `sdlc-adversarial/SKILL.md` lines 101-107. Factual basis (file:line references must exist), methodological reliability (probe output, not inference), and known false-positive pattern checks.

**19. Error Budget Policy with Velocity Tradeoff (from SRE principles Karpathy endorses)**
Implemented in `/Users/q/.claude/plugins/sdlc-os/references/quality-slos.md`. Budget healthy = move faster (skip sentinel for clear beads). Budget depleted = slow down (full AQS for all beads). Direct application of "faster when safe, slower when not."

---

## PARTIALLY EMBEDDED

**1. "Become One with the Data" (from "Recipe" Step 1)**
Implemented as Phase 2 (Scout) in `sdlc-orchestrate/SKILL.md` lines 139-147, which dispatches investigators, convention-scanner, gap-analyst, and feature-finder. Also as reuse-scout pre-dispatch in `sdlc-reuse/SKILL.md`.
**Missing:** Karpathy's Step 1 is specifically about understanding the *distribution* of your data -- its patterns, imbalances, outliers, and biases -- before writing any code. The Scout phase gathers facts about the codebase but does not systematically profile the *distribution of the problem space* itself (e.g., "80% of the complexity is in 2 of the 12 files," "the error handling paths outnumber happy paths 3:1," "the test suite covers module A at 95% but module B at 12%"). This distributional awareness would inform bead decomposition quality and complexity assignment.
**Priority: MEDIUM** -- Would improve Conductor's bead decomposition and Cynefin assignments by grounding them in quantitative distributions rather than surface-level heuristics.

**2. "Keep Deterministic Work Deterministic" (from Karpathy's 2025-2026 commentary)**
Implemented partially through metric commands in `sdlc-loop/SKILL.md` lines 240-250 (beads must run `tsc --noEmit`, `npm test`, etc.) and the L0 runner loop that measures against these deterministic checks.
**Missing:** The system does not have a formal principle that differentiates tasks that *should* be solved deterministically (code formatting, import sorting, schema validation, file existence checks) from tasks that benefit from probabilistic LLM reasoning. There is no routing mechanism that says "this sub-task is deterministic -- execute it as a script, not as an LLM prompt." Agents may be using LLM reasoning for tasks that a shell script would handle more reliably.
**Priority: HIGH** -- Karpathy's point is that every step handled by an LLM has a reliability ceiling below 100%, and those ceilings multiply. Routing deterministic tasks away from LLMs directly reduces compounding failure.

**3. March of Nines / Compounding Failure Math (from Karpathy 2025)**
Implemented implicitly through the multi-level loop hierarchy where each level has hard budgets and escalation paths, and through the quality SLO system.
**Missing:** The system does not explicitly model *end-to-end success probability* across the pipeline. There is no mechanism that calculates or estimates p^n (per-step success rate raised to the power of steps) for a given bead or task. The Conductor cannot answer "what is the estimated end-to-end reliability of this 8-bead task?" There is no tracking of per-step success rates across tasks to identify which steps are the reliability bottleneck.
**Priority: HIGH** -- Without explicit reliability math, the system cannot make informed tradeoffs between adding more verification steps (which increase per-step reliability but add more steps) versus simplifying the pipeline.

**4. Autonomy Slider / Graduated Trust (from Karpathy's Software 3.0 talk, June 2025)**
Implemented partially through the Cynefin domain assessment in `scaling-heuristics.md` which scales process depth (Clear = minimal, Complex = full), and through the error budget policy which relaxes controls when quality is healthy.
**Missing:** The system has no explicit *user-facing* autonomy control. The human operator cannot say "for this task, I want to be in the loop at every bead" or "for this task, run fully autonomous and show me the result." The Cynefin classification is agent-determined, not user-adjustable. Karpathy specifically advocates for a slider that lets the user modulate autonomy, starting low-risk and ascending as trust is earned.
**Priority: MEDIUM** -- The system already scales internally, but lacks the user-facing control that Karpathy considers essential for trust-building. Adding a user-settable oversight level (e.g., `--oversight=high|normal|low`) would bridge this gap.

**5. Tesla Data Engine Closed-Loop (shadow mode -> trigger -> label -> retrain)**
Implemented as the calibration loop (L6) in `sdlc-loop/SKILL.md` and LOSA observer in `sdlc-orchestrate/SKILL.md` line 207, which randomly samples merged beads and re-runs probes.
**Missing:** The full Tesla data engine is a *closed loop* where detected failures automatically become training data for the next iteration. The LOSA observer and calibration bead detect drift, but the *remediation* is manual (review agent prompts, check constitution). There is no mechanism to automatically update agent prompts, the code-constitution, or the attack library based on observed failures. The "retrain" equivalent is absent.
**Priority: MEDIUM** -- Closing the loop would mean AQS findings that repeatedly appear automatically generate new code-constitution rules or attack library entries. Currently this requires Conductor judgment, which is fine for now but limits self-improvement velocity.

**6. Process Reward Models / Step-Level Verification (from "State of GPT")**
Implemented partially through the per-level metrics (L0 has acceptance commands, L1 has sentinel checklist, L2 has VORP, L2.5 has adversarial metrics).
**Missing:** These are binary pass/fail checks, not *continuous reward signals* on intermediate steps. Karpathy's point about process reward models is that rewarding intermediate reasoning steps (not just the final answer) significantly improves outcomes. The system verifies each level's output but does not score the *quality of the process* used to reach that output. A runner that stumbles through 3 L0 attempts before passing is treated identically to one that passes on the first try -- there is no process quality signal fed back.
**Priority: LOW** -- The system's tiered loop structure is functionally similar, but adding process quality signals could improve Conductor decisions about bead complexity assignment and agent capability assessment.

---

## NOT YET EMBEDDED

### HIGH Priority

**1. The Slopacolypse Defense: Structural Anti-Slop Verification**
Concept: Karpathy predicts a flood of "almost right, but not quite" AI-generated code -- code that compiles, passes tests, but is subtly wrong, over-abstracted, or unnecessarily complex. Current AI "makes subtle conceptual mistakes like sloppy junior developers, operates on incorrect assumptions, fails to ask clarifying questions, and tends to overcomplicate solutions."
Gap: The system's verification focuses on correctness (tests pass, VORP satisfied, AQS finds no vulnerabilities) but has no explicit check for *unnecessary complexity introduced by agents*. The fitness function checks cognitive complexity per function (SLO: <= 15), but this is a threshold, not a directional check. There is no mechanism asking "is this solution simpler than what a competent human would write?" or "did the agent over-engineer this?"
Mechanism: Add a **simplicity audit** to the L1 sentinel loop. After a runner submits, a dedicated check compares the solution's complexity (lines of code, abstraction layers, dependency count) against the problem's inherent complexity. Flag solutions where the ratio is disproportionate. This could be a guppy swarm asking: "Could this be done in fewer lines? Does every abstraction earn its keep? Is there dead code?" -- run *before* the full sentinel check.
Where: `sdlc-loop/SKILL.md` L1 sentinel loop, `sdlc-fitness/SKILL.md` as a new fitness dimension.

**2. Explicit Per-Step Reliability Tracking (March of Nines)**
Concept: If a workflow has n steps each with success probability p, end-to-end success is p^n. At 90% per step, a 10-step workflow succeeds 34.9% of the time. Karpathy says "every single nine is the same amount of work."
Gap: The system tracks which loops exhaust budgets and which SLOs are breached, but does not track *per-step success rates* (e.g., "L0 passes on first attempt 72% of the time for implement beads" or "L1 sentinel approves on first submission 85% of the time"). Without this data, the Conductor cannot identify which steps are the reliability bottleneck.
Mechanism: Add a **reliability ledger** that records, for each bead: L0 attempts used, L1 cycles used, L2 cycles used, L2.5 cycles used. Aggregate across tasks to compute per-step first-pass success rates. The Conductor uses this to prioritize system improvements: if L0 first-pass rate is 60% but L2 is 95%, the investment should go into improving runner context quality, not oracle prompts.
Where: `sdlc-loop/SKILL.md` bead status extensions (already track loop state, just need aggregation), `references/quality-slos.md` (add per-step SLIs).

**3. Deterministic Task Routing**
Concept: Karpathy emphasizes keeping deterministic work deterministic -- using LLMs to write code that performs deterministic tasks, not asking LLMs to perform those tasks directly. Every LLM invocation has a reliability ceiling; deterministic code does not.
Gap: The system dispatches all work through LLM agents. There is no classification of sub-tasks as "deterministic" (can be handled by a shell script, a linter, or a static analysis tool) versus "requires LLM reasoning." Tasks like "check if file X exists," "count lines changed," "verify import graph has no cycles," and "ensure all exported functions have JSDoc" are currently handled by LLM agents when they could be handled by deterministic scripts with 100% reliability.
Mechanism: Add a **deterministic task catalog** to the bead specification. The Conductor classifies each check as `deterministic` or `reasoning-required`. Deterministic checks run as shell commands or scripts, not agent dispatches. The sentinel's verification checklist separates "run these deterministic checks" from "have an agent evaluate these." This reduces the number of LLM steps in the pipeline, directly improving p^n reliability.
Where: `sdlc-orchestrate/SKILL.md` bead spec, `sdlc-loop/SKILL.md` L1 sentinel loop, new reference file `references/deterministic-checks.md`.

**4. Distributional Problem Profiling ("Become One with the Data" for Codebases)**
Concept: Karpathy's Step 1 is not "read your data" -- it is "understand the distribution of your data." For codebases, this means understanding: which modules are most complex, where the test coverage gaps are, what the ratio of error paths to happy paths is, which files change most frequently, where the technical debt clusters.
Gap: Phase 2 (Scout) investigates the codebase and maps conventions, but does not produce a *distributional profile*. The gap-analyst produces a completeness map (EXISTS/PARTIAL/MISSING) but not a *quantitative complexity distribution*. The Conductor assigns Cynefin domains using heuristic signals (line count, file count), not empirical complexity data.
Mechanism: Add a **distributional profiler** to Phase 2 (Scout) that produces quantitative metrics: lines per module, cyclomatic complexity per function, test coverage per module, churn rate per file (from git log), ratio of error handling code to business logic. Feed this profile into Phase 3 (Architect) so bead decomposition is grounded in empirical complexity data, not intuition.
Where: `sdlc-orchestrate/SKILL.md` Phase 2 (Scout), new agent `distributional-profiler`.

### MEDIUM Priority

**5. Closed-Loop Self-Improvement (Tesla Data Engine "Retrain" Step)**
Concept: Tesla's data engine is a closed loop: deploy -> detect failures via shadow mode -> auto-label failures -> add to training set -> retrain -> redeploy. The key insight is that detected failures automatically feed back into the system's improvement.
Gap: The system detects failures through calibration beads, LOSA observation, and AQS findings. But the remediation is manual: the Conductor must review prompts, update the constitution, or adjust attack libraries. There is no automatic feedback from detected failure patterns to system configuration.
Mechanism: Add an **auto-rule generator** that runs after every AQS engagement. When a finding type appears 3+ times across tasks (e.g., "missing null check on database query result"), automatically draft a new code-constitution rule and present it to the Conductor for approval (not auto-apply). When an attack vector proves effective 3+ times, automatically add it to the domain attack library. This closes the loop without removing human judgment.
Where: `sdlc-adversarial/SKILL.md` Phase 6, `references/code-constitution.md`, `sdlc-adversarial/domain-attack-libraries.md`.

**6. Autoresearch-Style Experimental Loop for System Tuning**
Concept: Karpathy's autoresearch (March 2026) runs a tight loop: modify code -> run experiment -> measure -> keep or discard. Applied to the SDLC plugin itself, this would mean: modify a system parameter (e.g., guppy count, budget size, prompt wording) -> run a calibration bead -> measure detection rate -> keep or discard the change.
Gap: The calibration loop (L6) detects drift but does not systematically experiment with system parameters. When calibration detects a decline, the response is manual investigation. There is no automated experimentation loop for the system's own configuration.
Mechanism: Add an **autotune mode** to the calibration loop. When drift is detected, generate N parameter variations (e.g., different guppy counts, different prompt phrasings for the red team), run the calibration bead against each, and keep the variation with the highest detection rate. Budget: limited to parameters that do not change system architecture, only tunable knobs.
Where: `references/calibration-protocol.md`, new reference `references/autotune-protocol.md`.

**7. Cognitive Debt Tracking (from Karpathy's 2026 commentary on the "slopacolypse")**
Concept: Cognitive debt is the accumulated cost of poorly managed AI interactions -- context loss, unreliable agent behavior, code that nobody understands because it was generated, not designed.
Gap: The system tracks technical quality (fitness functions, SLOs, AQS findings) but not *cognitive debt* -- the cost of understanding the generated code. A bead can pass all quality checks while producing code that is hard for humans to reason about in the future.
Mechanism: Add a **readability/comprehensibility dimension** to the fitness functions. Measure: ratio of comments to code, naming clarity (are variable names descriptive?), function length distribution, nesting depth, and whether the generated code follows the patterns already established in the codebase (not just conventions, but *idioms*). The existing convention-enforcer checks naming; this goes deeper into semantic clarity.
Where: `sdlc-fitness/SKILL.md` as a new fitness dimension "Comprehensibility."

**8. "Animals vs. Ghosts" Awareness: LLM Limitation Modeling**
Concept: Karpathy's framework distinguishes between animals (systems that learn from world interaction) and ghosts (statistical distillations of human text). LLMs are ghosts -- they simulate intelligence based on imitation, not grounded understanding. They will confidently produce plausible-but-wrong code.
Gap: The system treats LLM outputs as "unverified proposals" (sdlc-harden line 136: "Every agent output is an unverified proposal until evidence confirms it"), which is correct. But it does not model *specific LLM failure modes* -- the ways ghosts fail differently from humans. Ghosts hallucinate confidently, cannot verify their own outputs, over-rely on pattern matching, and struggle with novel combinations of familiar concepts.
Mechanism: Add an **LLM failure mode checklist** to the sentinel verification. After each runner submission, the sentinel specifically checks for: (a) hallucinated file paths or function names, (b) confident assertions without evidence, (c) solutions that pattern-match to a common template but don't fit the specific problem, (d) unnecessary complexity added by "helpful" overengineering. These are ghost-specific failure modes.
Where: `sdlc-loop/SKILL.md` L1 sentinel loop, agents that define the `haiku-verifier` role.

**9. Tokenization/Context Window Awareness in Agent Dispatch**
Concept: Karpathy has extensively documented how tokenization creates LLM blind spots -- inability to count characters, perform arithmetic, reverse strings, handle non-English text. Context windows create working memory limits.
Gap: The runner dispatch template in `sdlc-orchestrate/SKILL.md` lines 211-240 instructs the Conductor to craft "precisely crafted context packets -- never your full session history." This is good practice but does not systematically account for *what is likely to be lost or misprocessed* due to tokenization/context limitations. Long file contents, complex nested structures, and numeric data are all prone to tokenization-related errors.
Mechanism: Add **context budget estimation** to the Conductor's bead dispatch. Before sending a context packet to a runner, estimate the token count and flag if it exceeds a threshold (e.g., 80% of the model's effective context). For numeric or structural data, prefer to reference file paths rather than inline the content. For tasks involving counting, arithmetic, or string manipulation, add explicit instructions to use code execution rather than mental arithmetic.
Where: `sdlc-orchestrate/SKILL.md` "How to Dispatch Runners" section, new reference `references/context-budget-heuristics.md`.

### LOW Priority

**10. Scaffolded Complexity Progression (from Eureka Labs education philosophy)**
Concept: Karpathy's educational work at Eureka Labs and Stanford (CS231n) emphasizes scaffolded learning -- start with the simplest possible version and build up. Each new concept is introduced only after the prerequisite is mastered.
Gap: The system's bead decomposition follows dependency order but does not explicitly scaffold complexity. A task with 8 beads might have bead 1 be the hardest and bead 8 the easiest, depending on dependency order. Karpathy's approach would suggest ordering beads so that simpler beads succeed first, building evidence and context that de-risk the harder beads.
Mechanism: When the Conductor creates the bead manifest in Phase 3 (Architect), sort independent beads by estimated complexity (simplest first) rather than by dependency order alone. This means the system "warms up" on easier work, and findings from earlier beads inform later, harder beads. Apply only when multiple beads are truly independent.
Where: `sdlc-orchestrate/SKILL.md` Phase 3 (Architect).

**11. Simplicity as an Architectural Value (from nanoGPT/minbpe design philosophy)**
Concept: Karpathy's projects are defined by radical simplicity -- nanoGPT is 600 lines total, minbpe is minimal, autoresearch is 630 lines. The philosophy: if you cannot understand the entire system, you cannot debug it.
Gap: The sdlc-os plugin itself is architecturally rich (orchestrate, loop, adversarial, harden, reuse, fitness, normalize, gap-analysis, feature-sweep, swarm, gate, refactor, status -- 13+ skills). This complexity is justified by the problem domain but stands in tension with Karpathy's simplicity ethos. The system does not have a mechanism to evaluate whether its own complexity is justified.
Mechanism: Periodic **system complexity audit** -- count the number of agent types, loop levels, reference documents, and decision points. Ask whether any could be merged or eliminated without losing capability. This is meta-level housekeeping, not urgent.
Where: Meta-level concern, not specific to a single file.

**12. "Squeeze Out the Juice" / Ensemble Methods (from "Recipe" Step 6)**
Concept: Karpathy's final step is to extract maximum performance through ensembling, longer training, and hyperparameter sweeps after the basic approach works.
Gap: The system uses a single model per agent role (haiku for guppies, sonnet for runners, opus for arbiter). There is no ensemble mechanism where multiple independent agent instances produce outputs that are then aggregated. The Oracle council has three members, but they check different aspects (static, runtime, adversarial) rather than independently evaluating the same aspect.
Mechanism: For high-stakes beads (Complex domain, security-sensitive), dispatch 2-3 independent runners on the same bead with slightly different context framings. Compare outputs. Divergence between independent runners on the same task is a powerful signal that the problem is underspecified or the solution space is large. This is expensive and should be reserved for critical work.
Where: `sdlc-orchestrate/SKILL.md` Phase 4 (Execute), applicable only to Complex/security-sensitive beads.

**13. Shadow Mode for New Rules/Agents (from Tesla's shadow deployment)**
Concept: At Tesla, new neural network versions ran in "shadow mode" alongside production -- making predictions without acting on them -- to compare against the existing system before deployment.
Gap: When the code-constitution gets new rules or agent prompts are updated, there is no shadow-mode verification. The new rules go live immediately. The calibration loop checks system health periodically, but does not specifically validate new rules before they take effect.
Mechanism: When a new code-constitution rule or agent prompt update is proposed, run the next task with both old and new configurations in parallel (shadow mode). Compare findings. If the new configuration produces fewer detections on the calibration bead, reject the change. Only apply once verified.
Where: `references/calibration-protocol.md`, `references/code-constitution.md`.

---

## Summary Statistics

| Category | Count |
|---|---|
| Already Embedded | 19 |
| Partially Embedded | 6 |
| Not Yet Embedded -- HIGH | 4 |
| Not Yet Embedded -- MEDIUM | 5 |
| Not Yet Embedded -- LOW | 4 |

The system has deeply embedded Karpathy's most important operational principles: hypothesis-experiment-evidence, one-variable-at-a-time, baseline-first, incremental complexity, evidence over argument, and hard budgets. The explicit citation of "Karpathy Principle" in `instrumented-loop.md` confirms intentional design alignment.

The highest-priority gaps cluster around a theme Karpathy has been hammering in 2025-2026: **reliability engineering for probabilistic systems**. Specifically:
1. Routing deterministic work away from LLMs entirely (reducing p^n exposure)
2. Tracking per-step reliability to identify bottlenecks (measuring the march of nines)
3. Defending against the slopacolypse (unnecessary complexity detection)
4. Grounding bead decomposition in quantitative distributional data rather than heuristic signals

These four HIGH-priority items, if implemented, would address the failure modes Karpathy considers most pressing for multi-agent coding systems in 2026.

Sources:
- [A Recipe for Training Neural Networks (2019)](http://karpathy.github.io/2019/04/25/recipe/)
- [Software 2.0 (2017)](https://karpathy.medium.com/software-2-0-a64152b37c35)
- [Software 3.0 at YC AI Startup School (2025)](https://www.latent.space/p/s3)
- [State of GPT - Microsoft Build 2023](https://github.com/giachat/State-of-GPT-2023)
- [The Unreasonable Effectiveness of Recurrent Neural Networks (2015)](http://karpathy.github.io/2015/05/21/rnn-effectiveness/)
- [2025 LLM Year in Review](https://karpathy.bearblog.dev/year-in-review-2025/)
- [Animals vs Ghosts](https://karpathy.bearblog.dev/animals-vs-ghosts/)
- [March of Nines - VentureBeat](https://venturebeat.com/technology/karpathys-march-of-nines-shows-why-90-ai-reliability-isnt-even-close-to)
- [Keep Deterministic Work Deterministic - O'Reilly](https://www.oreilly.com/radar/keep-deterministic-work-deterministic/)
- [Autoresearch - GitHub](https://github.com/karpathy/autoresearch)
- [nanoGPT - GitHub](https://github.com/karpathy/nanoGPT)
- [Slopacolypse Warning - Cybernews](https://cybernews.com/ai-news/andrej-karpathy-slopacolypse/)
- [Agentic Engineering - Karpathy on X](https://x.com/karpathy/status/2015883857489522876)
- [Autonomy Slider concept](https://medium.com/@asatkinson/the-decade-of-agents-karpathys-strategy-for-building-the-agent-optimized-web-735191a69009)
- [Tesla Data Engine](https://www.braincreators.com/insights/teslas-data-engine-and-what-we-should-all-learn-from-it)
- [Eureka Labs announcement](https://venturebeat.com/ai/ex-openai-and-tesla-engineer-andrej-karpathy-announces-ai-native-school-eureka-labs)