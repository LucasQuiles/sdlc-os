---
name: sdlc-loop
description: "The feedback engine. Every role loops against its own metric. Tight self-correction inside tight self-correction inside tight self-correction. Failures propagate pressure backward only when a loop exhausts its budget."
---

# Loop Mechanics

The system is loops all the way down. Every role, every bead, every phase runs a tight self-correcting cycle. The Conductor is the loop of **last** resort, not first.

## The Fractal Loop

The same pattern repeats at every level. Every iteration is **falsifiable** — a hypothesis tested against evidence, not a vibe checked against intuition.

```
LOOP (budget: N attempts):
  1. Read state + prior evidence
  2. Form hypothesis (what will change, why it should work)
  3. Act (implement the hypothesis)
  4. Measure against metric (collect observable evidence)
  5. PASS → advance. FAIL → record what was tried, form new hypothesis.
  6. Budget exhausted → backpressure to parent loop with full evidence trail
```

**One variable at a time.** Each iteration changes ONE thing and measures the result. Shotgun changes that modify three things at once produce uninterpretable evidence — you cannot know which change caused the result.

**Evidence over argument.** Confidence upgrades require new evidence, not reasoning. "I believe this is correct" is not evidence. "The test passes" is.

### Level 0: Runner Loop (innermost — tightest)

The runner loops internally on its own work. No external intervention needed.

```
Runner receives bead.
LOOP (budget: 3 attempts):
  1. Read bead spec + any prior correction signals
  2. Implement / change
  3. Run bead metric command (tests, typecheck, lint — whatever the bead defines)
  4. PASS → submit output. EXIT loop.
  5. FAIL → read error output. Self-correct. Try again.
  6. Budget exhausted → submit partial output with STUCK status + what was tried.
```

**Metric:** The bead's acceptance command (e.g., `npm test -- suite-name`, `tsc --noEmit`).
**Budget:** 3 self-correction attempts before submitting.
**Key:** The runner reads its OWN error output and self-corrects. No Sentinel, no Conductor. Just the runner and its metric.

This is the `/experiment` pattern: change → measure → keep/discard → repeat.

### Level 1: Sentinel Loop (wraps each bead)

After a runner submits, the Sentinel loops on verification.

```
Runner submits bead output.
LOOP (budget: 2 cycles):
  1. Sentinel checks output against bead acceptance criteria
  2. PASS → bead status = verified. EXIT loop.
  3. FAIL → Sentinel produces correction directive (specific findings, not vague "try again")
  4. Fresh runner dispatched with: original bead + sentinel correction + "address THESE issues"
  5. New runner runs its own Level 0 loop internally
  6. Back to step 1 — Sentinel re-checks
  7. Budget exhausted → bead status = escalated. Backpressure to Conductor.
```

**Metric:** Sentinel's verification checklist (from `haiku-verifier`) + drift-detector violations + convention-enforcer violations + safety-constraints-guardian violations + simplicity-auditor findings.
**Budget:** 2 sentinel-runner correction cycles.
**Key:** The correction is SPECIFIC. Not "this is wrong." Instead: "line 45 doesn't handle null, the test on line 80 is vacuous, scope drifted into payments-storage, file naming violates convention (camelCase, should be kebab-case)."
**Convention-enforcer in L1:** Runs alongside drift-detector after each runner submission. BLOCKING convention violations trigger the same L1 correction path as drift-detector findings. `CONVENTION_DRIFT` signals are reported to the Conductor for Convention Map review but do NOT trigger L1 correction (the map may be stale, not the runner).
**safety-constraints-guardian in L1:** Runs alongside drift-detector and convention-enforcer after each runner submission. Checks bead outputs against the Safety Constraints Registry (`references/safety-constraints.md`). Violations are BLOCKING — same correction signal as drift-detector.

**simplicity-auditor in L1 (Karpathy Slopacolypse Defense):** Runs alongside the other L1 checks after each runner submission. Computes a simplicity coefficient (problem_complexity / solution_complexity) and flags disproportionately complex solutions. This catches a class of defect that correctness checks cannot see: code that passes all tests but is unnecessarily complex.

- **PASS** (coefficient >= 0.5): Solution proportionate to problem. No action.
- **WARNING** (0.3 <= coefficient < 0.5): Solution may be over-engineered. Runner must justify complexity or simplify. Non-blocking but logged.
- **BLOCKING** (coefficient < 0.3): Solution is disproportionately complex. L1 correction directive issued with specific simplification targets.

The audit also checks for specific slopacolypse indicators: factory patterns wrapping single functions, strategy patterns for two-branch conditionals, premature generalization (generics with single implementation), dead code paths, and copy-paste amplification. See `references/simplicity-metrics.md` for metric definitions and thresholds. See `agents/simplicity-auditor.md` for the full agent specification.

ACCIDENTAL beads (FFT-10) are expected to have high coefficients — if they don't, something is wrong. ESSENTIAL beads get more latitude but coefficient < 0.3 still requires justification.

### Deterministic Check Routing (FFT-08)

Before dispatching LLM-based sentinel checks, the Conductor applies **FFT-08** from `references/fft-decision-trees.md` to classify each verification check. Checks answerable by running a command (type-check, lint, test, file-exists, schema validation) are routed to shell scripts, not LLM agents. See `references/deterministic-checks.md` for the full catalog.

This directly improves pipeline reliability: replacing a p=0.95 LLM step with a p=1.0 script step contributes multiplicative improvement to end-to-end reliability (Karpathy March of Nines).

### Level 2: Oracle Loop (wraps test quality)

After Sentinel passes, Oracle audits test integrity.

```
Bead verified by Sentinel.
LOOP (budget: 2 cycles):
  1. Oracle audits tests (Layer 1: static, Layer 2: runtime)
  2. PASS (VORP satisfied) → bead status = proven. EXIT loop.
  3. FAIL → Oracle produces specific test deficiency report
  4. Fresh runner dispatched with: bead + oracle findings + "fix THESE test issues"
  5. New runner loops internally (Level 0), Sentinel re-checks (Level 1)
  6. Oracle re-audits
  7. Budget exhausted → bead status = test-concern. Flag to Conductor with specifics.
```

**Metric:** VORP standard (Verifiable, Observable, Repeatable, Provable).
**Budget:** 2 oracle-runner correction cycles.
**Key:** Oracle findings flow INTO the runner's next attempt. The runner learns what the Oracle catches.

### Level 2.5: AQS Loop (wraps adversarial quality)

After Oracle proves the bead, the Adversarial Quality System probes it across four domains.

```
Bead proven by Oracle.
LOOP (budget: 2 cycles):
  1. Recon burst (8 guppies, 2 per domain) + Conductor domain selection → cross-reference priorities
  2. Red team commanders dispatch guppy swarms at HIGH/MED/LOW domains
  3. Blue team triages findings: accept (fix), rebut (evidence), or dispute
  4. Disputed findings → Arbiter (Kahneman protocol, binding verdict)
  5. CLEAN (no findings) → bead status = hardened. EXIT loop.
  6. Cycle 1 produced fixes → Cycle 2: re-attack fixed code to verify hardening
  7. Budget exhausted → bead status = hardened + residual risk documented. EXIT loop.
```

**Metric:** Residual risk after adversarial engagement.
**Budget:** 2 red/blue/arbiter cycles.
**Key:** AQS is skipped for trivial beads (beads go `proven → merged` directly). See `sdlc-os:sdlc-adversarial` for full cycle details.

### FFT-Driven Loop Depth

Loop depth assignment is formalized via **FFT-05** from `references/fft-decision-trees.md`. Key behaviors:
- CHAOTIC → L0 only (act-first, postmortem retroactively)
- CONFUSION → BLOCKED (must decompose first)
- CLEAR + healthy budget → L0 only
- CLEAR + unhealthy budget → L0 + L1
- COMPLICATED → L0 + L1 + L2 + L2.5
- COMPLEX or security_sensitive → L0 + L1 + L2 + L2.5 + L2.75 (full pipeline)

### Level 3: Bead Loop (wraps the full bead lifecycle)

The complete lifecycle of a single bead, containing all inner loops.

```
Bead created by Conductor.
LOOP (budget: 1 full cycle — inner loops handle retries):
  1. Runner executes (Level 0 loop: up to 3 self-corrections)
  2. Sentinel verifies (Level 1 loop: up to 2 correction cycles)
  3. Oracle audits (Level 2 loop: up to 2 correction cycles)
  4. AQS engages (Level 2.5 loop: up to 2 red/blue/arbiter cycles) — skipped for trivial beads
  5. ALL PASS → bead = merged. EXIT.
  6. ANY inner loop exhausted budget → bead = escalated to Conductor.
```

**Max agent invocations per bead:** Runner (3) × Sentinel cycles (2) × Oracle cycles (2) × AQS cycles (2) = worst case ~24 invocations. Typical case: Runner(1) + Sentinel(1) + Oracle(1) + AQS(1) = 4.

### Level 4: Phase Loop (wraps all beads in a phase)

```
Phase begins (e.g., Execute).
LOOP (budget: all beads must reach merged/escalated):
  1. Dispatch all independent beads (parallel where safe)
  2. Each bead runs its Level 3 loop autonomously
  3. Collect results: merged | escalated
  4. ALL merged → phase complete. Advance.
  5. ANY escalated → Conductor intervenes:
     a. Re-decompose the failed bead into smaller beads? (decomposition was wrong)
     b. Provide missing context and re-dispatch? (information gap)
     c. Change the design? (backpressure to Architect phase)
     d. Escalate to user? (genuine blocker)
  6. After Conductor intervention, re-enter phase loop for remaining beads.
```

### Level 5: Task Loop (outermost — wraps the entire SDLC)

```
Task received.
LOOP (budget: 3 full passes):
  1. Frame → Scout → Architect → Execute → Synthesize
  2. Final verification: does the delivery meet the mission brief?
  3. YES → deliver. EXIT.
  4. NO → identify which phase broke:
     - Bad framing? → re-Frame
     - Missing context? → re-Scout
     - Wrong design? → re-Architect
     - Incomplete implementation? → re-Execute specific beads
  5. Budget exhausted → deliver what you have + explicit gap report to user.
```

### Level 6: Calibration Loop (outermost — wraps multiple tasks)

The calibration loop monitors system health across sessions. Unlike L0-L5 which run within tasks, L6 runs between tasks.

```
CALIBRATION LOOP (cadence: every 5th task or on Conductor suspicion):
  1. Inject a calibration bead — known code with 3-5 planted defects across 2+ domains
  2. Run through L1 (Sentinel) + L2 (Oracle) + L2.5 (AQS)
  3. Compare detection results against known-planted defects
  4. DETECTION RATE >= baseline → system is calibrated. Log and continue.
  5. DETECTION RATE < baseline → system is drifting. Trigger investigation:
     a. Which defect types were missed? (update regression watchlist)
     b. Which agents failed to detect? (review agent prompts)
     c. Has the constitution drifted? (rule review)
  6. After recalibration, re-run calibration bead to verify improvement.
```

**Metric:** Detection rate of planted defects vs. established baseline.
**Budget:** 1 calibration run. If the first run passes, no further action needed. If it fails, recalibrate and re-run once.
**Key:** This is a system health check, not a task. It does not produce deliverable output — it produces confidence that the system is still working correctly.

See `references/calibration-protocol.md` for full procedures including:
- Drift signal detection (semantic, coordination, behavioral)
- Regression watchlist maintenance
- Noise audit protocol (consistency measurement)
- LOSA observer integration

## Backpressure Cascade

When an inner loop exhausts its budget, pressure flows outward — never inward.

```
Runner stuck (L0 budget: 3) → Sentinel takes over correction (L1)
Sentinel stuck (L1 budget: 2) → Conductor re-decomposes or re-designs (L3/L4)
Oracle stuck (L2 budget: 2) → Conductor re-decomposes or re-designs (L3/L4)
AQS stuck (L2.5 budget: 2) → Conductor reviews residual risk, decides accept or re-dispatch (L3)
Phase stuck (L4) → Conductor re-enters earlier phase (L5)
Task stuck (L5 budget: 3) → User gets explicit gap report
```

**The rule:** Each level tries to self-correct before escalating. Escalation always includes:
- What was tried (specific attempts, not "I tried everything")
- Why it failed (specific errors/findings)
- What the escalation target should consider

**Naked escalation is forbidden.** "I'm stuck" without specifics is not escalation — it is abdication.

### FFT-Driven Escalation

Escalation strategy at L3+ is formalized via **FFT-07** from `references/fft-decision-trees.md`. Key behaviors:
- Same error 3+ times across beads → ROOT_CAUSE_ANALYSIS (Dekker: fix the context, not the runner)
- Already re-decomposed once → ESCALATE_TO_USER
- Runner reported NEEDS_CONTEXT → ENRICH_AND_REDISPATCH
- Sunk cost check: "If starting fresh, would I choose this design?" → If NO: REDESIGN_BEAD

## Budget Table

| Loop Level | What | Budget | Escalates To |
|------------|------|--------|-------------|
| L0 | Runner self-correction | 3 attempts | L1 (Sentinel) |
| L1 | Sentinel-runner correction | 2 cycles | L3 (Conductor via bead) |
| L2 | Oracle-runner correction | 2 cycles | L3 (Conductor via bead) |
| L2.5 | AQS red/blue/arbiter cycle | 2 cycles | L3 (Conductor via bead) |
| L3 | Full bead lifecycle | 1 pass (inner loops retry) | L4 (Phase) |
| L4 | Phase completion | All beads resolved | L5 (Task) |
| L5 | Task completion | 3 full passes | User |

**Total worst-case per bead:** 3 (L0) × 2 (L1) × 2 (L2) × 2 (L2.5) = 24 invocations.
**Typical case per bead:** 1 + 1 + 1 + 1 = 4 invocations.
**Cost control:** Haiku agents (Sentinel, Oracle L2, Guppies) are cheap. Sonnet runners are the main cost. Hard budgets prevent runaway.

## Correction Signal Format

Every correction flowing between loops uses this format:

```markdown
## Correction: {source} → {target}

**Attempt:** {N} of {budget}
**What failed:** [specific finding — not "it's wrong"]
**Evidence:** [file:line, test output, or observation]
**What to try:** [specific suggestion — not "fix it"]
**What NOT to try:** [approaches already attempted that didn't work]
**escalation_reason:** [required when escalating — must be one of the enum values in `references/mode-convergence-rules.yaml:escalation_reasons`]
**convergence_signal:** [JSON output from `scripts/compute-convergence-signal.sh` for the current cycle, or omit if not yet computed]
```

The `What NOT to try` field is critical — it prevents loops from repeating the same failed approach. Each correction carries the history of what was already attempted.

Every escalation MUST include an `escalation_reason` from the enum in `references/mode-convergence-rules.yaml`. Do NOT hardcode values — read the enum directly from the rules file. The reason is recorded in the bead's escalation log and the task's `mode-convergence-summary.yaml`.

### Convergence-Aware Budget Handling

After each loop iteration, compute the convergence signal via `scripts/compute-convergence-signal.sh`. The `recommendation` field modifies budget behavior:

- `continue` → proceed normally within existing budget
- `stop_early` → skip remaining budget iterations, advance bead (convergence detected — no value in continuing)
- `extend_budget` → add 1 cycle to remaining budget if total does not exceed 2x original budget (per `references/mode-convergence-rules.yaml:max_budget_multiplier` — do NOT hardcode this multiplier)
- `change_approach` → escalate to next loop level with structured `escalation_reason`

Branch on the `recommendation` field values, not on `convergence_state` names.

## Metric Commands

Every bead must define its acceptance metric. If the bead creator (Conductor) does not specify one, the default is:

| Bead Type | Default Metric |
|-----------|---------------|
| implement | `tsc --noEmit && npm test -- {relevant-suite}` |
| investigate | Findings include ≥1 Verified claim with evidence |
| design | ≥2 options with tradeoff comparison |
| verify | All acceptance criteria have PASS/FAIL with evidence |
| review | Issues table populated, decision stated |

Runners that submit without running their metric are automatically flagged by Sentinel.

## How This Changes Dispatch

The runner dispatch template now includes loop awareness:

```
Agent tool:
  mode: auto
  prompt: |
    You are a Runner executing one atomic work unit.

    ## Your Bead
    {bead content}

    ## Your Metric
    {acceptance command — you MUST run this before submitting}

    ## Self-Correction Protocol
    You have a budget of 3 attempts. On each attempt:
    1. Implement the change
    2. Run your metric command
    3. If it passes → submit your output
    4. If it fails → read the error output, diagnose, and try again
    5. If you exhaust 3 attempts → submit what you have with status STUCK
       Include: what you tried, what failed, what you think the issue is

    ## Prior Corrections (if any)
    {sentinel/oracle findings from previous cycle — empty on first dispatch}

    ## Approaches Already Tried (do not repeat these)
    {list of failed approaches from prior attempts — empty on first dispatch}
```

## Bead Status Extensions

Beads now track loop state:

```markdown
# Bead: {id}
**Status:** pending | running | submitted | verified | proven | hardened | merged | stuck | escalated
**Loop state:**
  - L0 attempts: {N}/3
  - L1 cycles: {N}/2
  - L2 cycles: {N}/2
  - L2.5 cycles: {N}/2
**Correction history:**
  - [timestamp] L0: self-corrected — {what changed}
  - [timestamp] L1: sentinel correction — {finding}
  - [timestamp] L2: oracle correction — {finding}
  - [timestamp] L2.5: AQS finding — {domain}: {finding}
```

### Turbulence Tracking

Every bead tracks its loop cycle consumption in the `Turbulence` field:

```
**Turbulence:** {L0: 1, L1: 0, L2: 0, L2.5: 0, L2.75: 0}
```

The Turbulence field is updated after each loop level completes:
- L0: increment when runner self-corrects (each attempt counts)
- L1: increment when sentinel flags and correction cycle runs
- L2: increment when oracle flags and correction cycle runs
- L2.5: increment per AQS cycle
- L2.75: increment per Phase 4.5 hardening cycle

**Turbulence Score** = total cycles consumed / expected cycles for beads of this Cynefin domain. Score near 1.0 = normal. Score > 2.0 = high turbulence (Kahneman duration neglect countermeasure — makes correction history visible even after bead reaches "hardened" status).

High-turbulence beads are flagged in the Phase 5 delivery summary and may warrant additional monitoring in production.

## Evidence Accumulation Across Loops

The loop system tracks evidence trajectories, not just pass/fail states. Each correction cycle produces evidence that informs the next cycle — the system gets smarter as it iterates.

**Within a bead:** The correction history (L0 → L1 → L2 → L2.5) forms an evidence chain. Each level's findings become the next level's prior context. A runner that self-corrected on a null check (L0) should not have that same null check flagged by the Sentinel (L1) — the correction history prevents redundant work.

**Across beads in a task:** If AQS finds security issues in beads 1 and 2, the Conductor should increase the security domain's default priority for beads 3+. The system learns from its own engagement history:

```markdown
## Task-Level Prior Adjustments
| Domain | Beads with findings | Default priority adjustment |
|--------|--------------------|-----------------------------|
| security | 2 of 3 beads | Upgrade to HIGH for remaining beads |
| functionality | 0 of 3 beads | Keep at Conductor judgment |
```

**Confidence direction tracking:** Every finding carries not just a confidence level but a direction — is confidence upgrading or degrading across cycles?

- `↑ upgraded` — New evidence strengthened the claim (e.g., Assumed → Verified via reproduction)
- `→ stable` — Same evidence, same confidence
- `↓ degraded` — New evidence weakened the claim (e.g., Likely → Dismissed via rebuttal)

Findings with `↑ upgraded` trajectories across cycles are the most trustworthy. Findings that remain `→ stable` at `Assumed` after two cycles should be closed — if no evidence emerged in two cycles, the claim is not actionable.

## Anti-Patterns

- **Naked escalation** — "I'm stuck" without specifics. Every escalation must include what was tried and why it failed.
- **Looping without changing approach** — Trying the same thing 3 times is not 3 attempts. Each attempt must be a different hypothesis.
- **Skipping the metric** — Runners that claim success without running the metric get auto-flagged.
- **Conductor intervening in inner loops** — Let L0/L1/L2 self-correct before the Conductor touches it.
- **Infinite loops** — Hard budgets exist for a reason. Exhausting a budget is a signal, not a failure.
- **Over-budgeting** — Do not set budget to 10. If 3 attempts cannot solve it, the problem is wrong, not the attempt count.
