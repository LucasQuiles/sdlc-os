# Reliability Ledger Reference

Persistent format and computation rules for the March of Nines reliability tracking system.

---

## Ledger Location

`docs/sdlc/reliability-ledger.md` — per-task first-pass rate analysis, one entry per completed task.

**Relationship to system budget:** The reliability ledger computes per-level first-pass rates from bead traces. The system budget (`docs/sdlc/system-budget.jsonl`) aggregates task-level metrics for longitudinal analysis. The derivation scripts (`scripts/derive-quality-budget.sh`, `scripts/append-system-budget.sh`) consume bead traces directly — the reliability ledger is a parallel analysis artifact, not a prerequisite for the system budget.

## Ledger Entry Format

```markdown
## Task: {task-id} ({date})

| Step | First-Pass Rate | Nines | Beads Measured | Bottleneck? |
|------|----------------|-------|----------------|-------------|
| L0 (Runner) | 0.XX | X.X | N | |
| L1 (Sentinel) | 0.XX | X.X | N | |
| L2 (Oracle) | 0.XX | X.X | N | |
| L2.5 (AQS) | 0.XX | X.X | N | |
| L2.75 (Hardening) | 0.XX | X.X | N | |

**End-to-end first-pass:** 0.XX (X.X nines)
**Bottleneck:** L{X} — {recommendation}
**Beads excluded:** {count} ({reason})
```

---

## Rate Computation

### First-Pass Rate per Level

```
rate(level) = count(beads where turbulence[level] == 0) / count(beads that reached level)
```

Beads excluded from a level's denominator:

| Exclusion | Reason |
|-----------|--------|
| Clear beads at L2.5 | AQS skipped for Clear domain |
| Clear beads at L2.75 | Hardening skipped when AQS skipped |
| Evolve beads at L2.5, L2.75 | Evolve status flow skips proven/hardened |
| Stuck/escalated before reaching level | Never entered that loop |
| Beads with profile INVESTIGATE | Read-only, no verification loops |

### Nines Conversion

`nines = -log10(1 - rate)`

| Rate | Nines | Label |
|------|-------|-------|
| 0.50 | 0.3 | Poor |
| 0.75 | 0.6 | Below baseline |
| 0.90 | 1.0 | Baseline |
| 0.95 | 1.3 | Improving |
| 0.99 | 2.0 | Good |
| 0.995 | 2.3 | Strong |
| 0.999 | 3.0 | Excellent |

### End-to-End Rate

`e2e = L0_rate × L1_rate × L2_rate × L2.5_rate × L2.75_rate`

Karpathy: p^N drops multiplicatively. Five steps at 90% each → 59% end-to-end.

---

## Turbulence Field Population

The Conductor populates the bead turbulence field during Execute phase:

| Field | Incremented When | By Whom |
|-------|-----------------|---------|
| L0 | Runner self-corrects (each L0 loop iteration) | Conductor, observing runner retry |
| L1 | Sentinel sends correction directive | Conductor, after sentinel report |
| L2 | Oracle finds test deficiency | Conductor, after oracle report |
| L2.5 | AQS produces findings requiring fixes | Conductor, after AQS cycle |
| L2.75 | Reliability hardening produces findings | Conductor, after hardening cycle |

Initial value: all zeros `{L0: 0, L1: 0, L2: 0, L2.5: 0, L2.75: 0}`. Field is cumulative — only increments, never resets.

---

## Bottleneck Identification Rules

1. Primary bottleneck: lowest first-pass rate
2. Co-bottlenecks: steps within 5% of lowest
3. Use `variation-classifier` to determine common-cause (system) vs special-cause (agent) fix

| Bottleneck | System Fix (Common Cause) | Agent Fix (Special Cause) |
|------------|--------------------------|--------------------------|
| L0 low | Improve bead spec templates | Fix specific runner prompt |
| L1 low | Clarify acceptance criteria format | Fix specific sentinel check |
| L2 low | Strengthen VORP rubric examples | Fix specific oracle check |
| L2.5 low | Reduce solution complexity | Fix specific red team domain |
| L2.75 low | Improve hardening patterns | Fix specific hardening agent |

---

## Trend Analysis

| Delta | Classification | Action |
|-------|---------------|--------|
| Improved > 10% | IMPROVEMENT | Log, continue |
| Within ±10% | HOLDING | No action |
| Declined > 10% | REGRESSION | Dispatch variation-classifier |
| Declined > 20% | CRITICAL | Escalate to Conductor |

Minimum data: 2+ entries for trends, 5+ for statistical confidence.

---

## Integration Points

| Consumer | Usage |
|----------|-------|
| Conductor (Synthesize) | Include bottleneck in delivery summary |
| Evolve skill | Prioritize improvement beads by rate |
| Quality budget | Low e2e rate triggers WARNING |
| Calibration protocol | Cross-reference with detection rates |
| Variation classifier | Ledger rates are classifiable metrics |

---

## Source

- Karpathy March of Nines (thinkers-lab netnew-005)
- Deming anti-tampering, Funnel Rule 1
- Kahneman turbulence score (thinkers-lab netnew-002)
