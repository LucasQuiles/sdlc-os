---
name: sdlc-harden
description: "This skill should be used when the Conductor activates Phase 4.5 reliability hardening on a bead that has reached 'hardened' status from AQS, or when the user runs '/harden'. Provides the full per-bead hardening pipeline: premortem, sandwich clean, observability instrumentation, error hardening, red/blue reliability probing, WYSIATI sweep, and evidence ledger."
---

# Phase 4.5: Reliability Hardening

Per-bead reliability engineering that instruments user project code with deep observability, exhaustive error handling, and verified resilience patterns. Runs between Execute (Phase 4) and Synthesize (Phase 5).

**Entry condition:** Bead at `hardened` status (passed AQS).
**Exit condition:** Bead at `reliability-proven` status (or `escalated` if correction budget exhausted).

## When This Fires

- Automatically: Conductor dispatches `reliability-conductor` when a bead reaches `hardened` status during Phase 4
- Manually: User runs `/harden` to trigger reliability hardening on current work
- The Conductor (Opus) dispatches the `reliability-conductor` (Sonnet) to orchestrate

## The 7-Step Pipeline

```
Step 0: Premortem ─────────── 3 haiku agents imagine production failure
Step 1: Pre-Clean ─────────── /finding-duplicate-functions + /simplify (parallel)
Step 2: Observe ───────────── observability-engineer instruments the bead
Step 3: Harden ────────────── error-hardener adds defenses
Step 4: Probe ─────────────── red-reliability-engineering swarms for gaps
Step 5: Defend ────────────── blue-reliability-engineering fixes/rebuts
Step 6: Post-Clean ────────── /finding-duplicate-functions + /simplify again
Step 7: Report ────────────── hardening report + WYSIATI sweep + evidence ledger
```

### Dual-Process Scheduling (Kahneman System 1/2)

| Step | System 1 (Haiku — fast) | System 2 (Sonnet — deliberate) |
|---|---|---|
| 0: Premortem | 3 haiku failure narratives | Conductor deduplicates |
| 1: Pre-clean | Haiku categorizes duplicates | Opus detects semantic dupes |
| 2: Observe | — | Sonnet cross-file instrumentation |
| 3: Harden | — | Sonnet failure mode reasoning |
| 4: Probe | 8 haiku guppy recon | Sonnet directed strikes |
| 5: Defend | — | Sonnet evidence-based fixes |
| 6: Post-clean | Haiku categorizes duplicates | Opus detects semantic dupes |
| 7: Report | — | Conductor WYSIATI sweep |

## Dispatch Pattern

The Conductor dispatches the `reliability-conductor` agent:

```
Agent tool:
  subagent_type: sdlc-os:reliability-conductor
  model: sonnet
  mode: auto
  prompt: |
    Phase 4.5 hardening for bead {bead-id}.
    Task: {task-id}
    Bead scope: {files list}
    Bead acceptance criteria: {criteria}
    Quality budget status: {healthy|warning|depleted}

    Run the full 7-step hardening pipeline per the spec.
    Write observability profile, hardening report, and evidence ledger.
    Mark bead reliability-proven when complete, or escalate if budget exhausted.
```

## Observability Stack Detection

Before any instrumentation, the `reliability-conductor` builds the project's observability profile by scanning:

- **Logging:** Framework (winston/pino/bunyan/log4j/slog/serilog/Python logging), structured vs unstructured, standard fields, output targets
- **Tracing:** Framework (OpenTelemetry/Datadog/Jaeger/X-Ray/none), span conventions, propagation
- **Metrics:** Framework (Prometheus/StatsD/OTel/custom/none), naming, labels, buckets
- **Error tracking:** Service (Sentry/Bugsnag/Rollbar/none), capture patterns
- **Resilience:** Retry libraries, circuit breakers, timeout conventions, degradation strategies

Written to `docs/sdlc/active/{task-id}/observability-profile.md`.

## Correction Budget

2 cycles maximum. After Blue Team fixes, if Red Team re-probe finds critical issues, re-enter at Step 2. If still failing after 2 cycles, escalate to L3 with full evidence ledger.

This is Karpathy's test-time compute scaling: trading compute for reliability. Each cycle costs tokens but increases confidence.

## State Persistence (Yegge NDI)

State written after each step to `docs/sdlc/active/{task-id}/beads/{bead-id}/reliability-state.json`. Agent crashes resume from last completed step. Path is nondeterministic; outcome converges on persistent acceptance criteria.

## Quality Budget Scaling

| Budget State | Premortem Agents | Red Team Guppies | Clear Bead Behavior |
|---|---|---|---|
| Healthy | 3 | Standard (8 recon) | Skip Steps 4-5 (Red/Blue), go Step 3 → Step 6 |
| Warning | 3 | Standard | Full pipeline |
| Depleted | 5 | Double (16 recon) | Full pipeline, no skipping |

**Clear bead criteria:** Single-file, no external calls, no state mutation, low cyclomatic complexity. Assessed by `reliability-conductor` during stack detection.

## Hardening Report

Produced at `docs/sdlc/active/{task-id}/beads/{bead-id}/hardening-report.md`. Required sections:

1. **Observability Profile** — stack summary
2. **Premortem Analysis** — failure modes, priority gaps
3. **Pre-Clean Results** — duplicates removed, simplifications
4. **Instrumentation Summary** — per-file: functions, spans, metrics, error paths
5. **Edge Case Tests Generated** — count, coverage dimensions
6. **Red Team Findings** — per-finding: domain, severity, claim, evidence, resolution
7. **Disputes & Arbitration** — per-dispute: positions, test, outcome, precedent
8. **Post-Clean Results** — hardening-induced duplication removed
9. **WYSIATI Coverage Sweep** — files total, files covered, gaps with Unknown confidence
10. **Evidence Ledger** — per-hypothesis: initial/final confidence, evidence chain
11. **Verdict** — reliability-proven or escalated, cycles used, risk accepted

## WYSIATI Coverage Sweep (Kahneman)

After all agents complete, build coverage matrix:
- Rows: every file and exported function in the bead
- Columns: mentioned by Observability Engineer? Error Hardener? Red Team? Blue Team?
- All-blank rows = WYSIATI gaps (invisible to context-bounded agents)
- Flag with `Unknown` confidence — the most dangerous label

## Integration Points

- **L1 Sentinel:** Patrols during Phase 4.5 — drift-detector and convention-enforcer validate hardening changes
- **Arbiter:** Resolves Red/Blue disputes using existing Kahneman adversarial collaboration protocol
- **LOSA Observer:** Every 5th bead, randomly samples hardening report and re-runs Red Team probes. Divergence >20% = occasion noise signal
- **Precedent System:** Arbiter verdicts on reliability disputes enter precedent database (stare decisis)
- **Loop System:** Phase 4.5 operates at L2.75 — between AQS (L2.5) and bead escalation (L3)

## Hard Constraints (Karpathy — Non-Negotiable)

- Hardening MUST NOT change function behavior (beyond adding observability)
- Hardening MUST NOT add dependencies not already in the project
- Hardening MUST NOT remove existing tests
- Hardening MUST NOT log sensitive data (PII, secrets, tokens)
- Every agent output is an unverified proposal until evidence confirms it
- Red Team MUST NOT see Blue Team self-assessment (anti-anchoring)

## Cost Awareness

Phase 4.5 is compute-intensive. Per bead:
- Step 0: 3 haiku calls (cheap)
- Steps 1, 6: 2 agent dispatches each (moderate)
- Steps 2, 3: 1 sonnet each (moderate)
- Step 4: 8+ haiku recon + sonnet strikes (moderate-expensive)
- Step 5: 1 sonnet (moderate)
- Step 7: Conductor synthesis (moderate)

Clear beads under healthy budget skip Steps 4-5, cutting cost roughly in half. The 2-cycle budget caps maximum spend at 2x per bead.
