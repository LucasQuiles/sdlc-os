# Instrumented Loop Discipline

The AQS cycle is not vibe-based. Every iteration follows a falsifiable, instrumented protocol drawn from three complementary frameworks.

---

## Karpathy Principle: Hypothesis -> Experiment -> Evidence

Every red team probe must be a testable hypothesis, not a vague concern. The loop is:

1. **Hypothesis** — "This code will fail when input X is provided because path Y is unguarded"
2. **Experiment** — Dispatch a guppy with the exact probe
3. **Evidence** — Guppy returns observable result: HIT (with evidence) or MISS
4. **Advance** — Only escalate to a finding if evidence supports the hypothesis

**One variable at a time.** Each guppy tests exactly one thing. Do not combine multiple hypotheses into a single probe. If a probe returns ambiguous results, shrink the hypothesis before re-probing.

**Overfit-one-case sanity gate:** Before firing a full swarm, the red team commander must first overfit: pick the single most likely vulnerability in the domain and verify the attack tooling works against it. If the most obvious probe fails to execute cleanly, fix the approach before scaling to a full swarm.

**Baseline-first:** On Cycle 1, establish a baseline of the code's current state before attacking. On Cycle 2 (re-attack after fixes), compare against the Cycle 1 baseline to verify fixes hold and no regression occurred.

---

## Bayesian Evidence Accumulation

Findings carry confidence levels (Verified / Likely / Assumed) but the system also tracks **confidence trajectories across cycles**:

```markdown
### Confidence Ledger (per bead)
| Finding | Cycle 1 Confidence | Cycle 1 Evidence | Cycle 2 Confidence | Cycle 2 Evidence | Direction |
|---------|-------------------|------------------|-------------------|------------------|-----------|
| F1      | Likely            | guppy signal     | Verified          | reproduction     | upgraded |
| F2      | Assumed           | no repro         | Dismissed         | blue rebuttal    | resolved |
```

**Upgrade rule:** Confidence upgrades require new evidence, never argument. "I'm more sure now" is not an upgrade. "I found a reproduction" is.

**Belief update per cycle:** Each AQS report includes a residual risk delta — a lightweight Bayesian-lite score tracking how the overall risk picture changed across cycles:

```markdown
### Belief Update
| Domain | Pre-AQS Risk Estimate | Post-Cycle-1 | Post-Cycle-2 | Delta |
|--------|----------------------|--------------|--------------|-------|
| security | unknown | elevated (2 findings) | low (both fixed, re-attack clean) | reduced |
| resilience | unknown | low (no findings) | -- | stable |
```

This is not formal Bayesian inference — it is a structured summary of how evidence changed the risk picture. The Conductor uses the delta column to decide whether the bead is genuinely hardened or needs further attention. A domain that stays `elevated` after Cycle 2 is a flag for Conductor escalation.

**Prior accumulation:** If the same domain (e.g., security) finds issues across multiple beads in the same task, the Conductor should increase that domain's default priority for subsequent beads. The system learns from its own engagement history within a task.

**Cumulative evidence over one-shot falsification:** A single clean sweep does not prove robustness. The confidence ledger and belief update track whether the "clean" result is genuinely clean (tested thoroughly, multiple probes, no signals) or superficially clean (few probes, narrow attack surface tested). The Conductor should treat a clean sweep from 5 guppies differently than a clean sweep from 40.

---

## Registered-Report Mode (High-Risk Tasks)

For security-sensitive beads and complex tasks, the AQS cycle operates in **registered-report mode**: the protocol is locked before execution begins.

Before Phase 3 (Directed Strike), the red team commander produces a **pre-registration document**:

```markdown
## Pre-Registration: Red Team {Domain} -- Bead {id}

### Attack Plan
1. {Hypothesis 1} -- will test by {method}
2. {Hypothesis 2} -- will test by {method}
...

### Expected Evidence
- If vulnerable: {what the guppy output would look like}
- If secure: {what the guppy output would look like}

### Commitment
- Guppy count: {N}
- I will report ALL results including nulls -- not cherry-pick hits
```

The blue team receives the pre-registration alongside the findings. This prevents post-hoc rationalization: the red team cannot retroactively claim they were "looking for" something they found by accident and inflate its severity.

**When to use registered-report mode:**
- Security-sensitive beads (always)
- Complex tasks with many beads (Conductor decision)
- When prior AQS cycles on this task produced disputed findings (trust calibration)

**When to skip:** Moderate and trivial complexity. Pre-registration adds overhead that is not justified when the attack surface is small.

---

## Replay Gate (Post-Merge Verification)

After all beads in a task are merged, the Conductor can optionally run a **replay sweep** — a lightweight adversarial pass across the integrated result. This catches cross-bead interaction bugs that per-bead AQS cannot find.

The replay sweep:
1. Fires recon guppies across the full changeset (not individual beads)
2. If recon finds signals, dispatches one red team commander for the flagged domain
3. Findings from replay are treated as new issues requiring blue team response
4. Replay is NOT a full AQS cycle — it is a single-pass sanity check

**When to replay:**
- Complex tasks with 3+ beads (cross-bead interaction risk)
- Tasks where AQS Cycle 1 produced accepted findings (fixes may interact)
- Conductor judgment

**When to skip:**
- Single-bead tasks
- Tasks where all beads returned clean from AQS
