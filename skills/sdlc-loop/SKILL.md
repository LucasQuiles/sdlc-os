---
name: sdlc-loop
description: "The feedback engine. Every role loops against its own metric. Tight self-correction inside tight self-correction inside tight self-correction. Failures propagate pressure backward only when a loop exhausts its budget."
---

# Loop Mechanics

The system is loops all the way down. Every role, every bead, every phase runs a tight self-correcting cycle. The Conductor is the loop of **last** resort, not first.

## The Fractal Loop

The same pattern repeats at every level:

```
LOOP (budget: N attempts):
  1. Read state
  2. Hypothesize / Act
  3. Measure against metric
  4. PASS → advance. FAIL → try again.
  5. Budget exhausted → backpressure to parent loop
```

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

**Metric:** Sentinel's verification checklist (from `haiku-verifier`).
**Budget:** 2 sentinel-runner correction cycles.
**Key:** The correction is SPECIFIC. Not "this is wrong." Instead: "line 45 doesn't handle null, the test on line 80 is vacuous, scope drifted into payments-storage."

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

### Level 3: Bead Loop (wraps the full bead lifecycle)

The complete lifecycle of a single bead, containing all inner loops.

```
Bead created by Conductor.
LOOP (budget: 1 full cycle — inner loops handle retries):
  1. Runner executes (Level 0 loop: up to 3 self-corrections)
  2. Sentinel verifies (Level 1 loop: up to 2 correction cycles)
  3. Oracle audits (Level 2 loop: up to 2 correction cycles)
  4. ALL PASS → bead = merged. EXIT.
  5. ANY inner loop exhausted budget → bead = escalated to Conductor.
```

**Max agent invocations per bead:** Runner (3) × Sentinel cycles (2) × Oracle cycles (2) = worst case ~12 cheap invocations. Typical case: Runner(1) + Sentinel(1) + Oracle(1) = 3.

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

## Backpressure Cascade

When an inner loop exhausts its budget, pressure flows outward — never inward.

```
Runner stuck (L0 budget: 3) → Sentinel takes over correction (L1)
Sentinel stuck (L1 budget: 2) → Conductor re-decomposes or re-designs (L3/L4)
Phase stuck (L4) → Conductor re-enters earlier phase (L5)
Task stuck (L5 budget: 3) → User gets explicit gap report
```

**The rule:** Each level tries to self-correct before escalating. Escalation always includes:
- What was tried (specific attempts, not "I tried everything")
- Why it failed (specific errors/findings)
- What the escalation target should consider

**Naked escalation is forbidden.** "I'm stuck" without specifics is not escalation — it is abdication.

## Budget Table

| Loop Level | What | Budget | Escalates To |
|------------|------|--------|-------------|
| L0 | Runner self-correction | 3 attempts | L1 (Sentinel) |
| L1 | Sentinel-runner correction | 2 cycles | L3 (Conductor via bead) |
| L2 | Oracle-runner correction | 2 cycles | L3 (Conductor via bead) |
| L3 | Full bead lifecycle | 1 pass (inner loops retry) | L4 (Phase) |
| L4 | Phase completion | All beads resolved | L5 (Task) |
| L5 | Task completion | 3 full passes | User |

**Total worst-case per bead:** 3 (L0) × 2 (L1) × 2 (L2) = 12 invocations.
**Typical case per bead:** 1 + 1 + 1 = 3 invocations.
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
```

The `What NOT to try` field is critical — it prevents loops from repeating the same failed approach. Each correction carries the history of what was already attempted.

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
**Status:** pending | running | submitted | verified | proven | merged | stuck | escalated
**Loop state:**
  - L0 attempts: {N}/3
  - L1 cycles: {N}/2
  - L2 cycles: {N}/2
**Correction history:**
  - [timestamp] L0: self-corrected — {what changed}
  - [timestamp] L1: sentinel correction — {finding}
  - [timestamp] L2: oracle correction — {finding}
```

## Anti-Patterns

- **Naked escalation** — "I'm stuck" without specifics. Every escalation must include what was tried and why it failed.
- **Looping without changing approach** — Trying the same thing 3 times is not 3 attempts. Each attempt must be a different hypothesis.
- **Skipping the metric** — Runners that claim success without running the metric get auto-flagged.
- **Conductor intervening in inner loops** — Let L0/L1/L2 self-correct before the Conductor touches it.
- **Infinite loops** — Hard budgets exist for a reason. Exhausting a budget is a signal, not a failure.
- **Over-budgeting** — Do not set budget to 10. If 3 attempts cannot solve it, the problem is wrong, not the attempt count.
