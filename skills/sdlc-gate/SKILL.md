---
name: sdlc-gate
description: "Lightweight health check for the current SDLC phase. Not an approval ceremony — a quick confidence assessment before proceeding."
---

# SDLC Health Check

Run a lightweight health check on the current phase. This is NOT an approval gate — it's a quick confidence assessment.

## What to Check

### Bead Health
- Are all beads for the current phase in a terminal state (submitted/verified/hardened/blocked)?
- Are any beads stuck (running for too long without output)?
- Are any beads blocked with unresolved blockers?

### Readiness Checklist
- [ ] AQS engaged for non-trivial beads (or explicitly skipped with justification)

### Quality Budget
- Does `quality-budget.yaml` exist in the task directory?
- Is `artifact_status` appropriate for the current transition? (`ready` for Synthesize, `final` for Complete)
- Are any hard-stop invariants triggered? (Check `references/quality-budget-rules.yaml`)
- Is `budget_state` computed and non-null?
- If `budget_state` is `depleted`: flag for user attention before proceeding.

### Hazard/Defense Ledger (STPA-required tasks only)
- Does `hazard-defense-ledger.yaml` exist for tasks with COMPLEX or security_sensitive beads?
- Is `artifact_status` appropriate? (`seeded` or higher for Execute, `active` for Synthesize, `final` for Complete)
- Are any records still `open`? (Must be resolved before Complete)
- Is `coverage_state` computed and non-depleted? If depleted, flag for user attention.

### Stress Session (stressed tasks only)
- Does `stress-session.yaml` exist for stress-sampled tasks?
- Is `artifact_status` appropriate? (`planned` for Execute, `active` for Synthesize, `final` for Complete)
- Are all stressor applications resolved (no pending results)?
- Has the harvest section been reviewed?

### Decision Noise (AQS-engaged tasks, advisory)
- Does `decision-noise-summary.yaml` exist for tasks with AQS-engaged beads?
- Are any soft escalation conditions triggered? (Check escalations section)
- If verdict flips or MAP divergence detected: flag for Conductor attention (advisory, not blocking)

### Mode & Convergence (advisory)
- Is execution mode classified? If `knowledge_based` with `confidence: high`, flag for Conductor attention.
- Does the escalation log show a dominant reason (3+ occurrences)? Flag: "Systematic issue — consider re-decomposition."
- Is convergence_yield low (< 0.10) across recent tasks? Flag: "Loops rarely stop early."

### Sentinel Status
- Has the sentinel flagged any unresolved issues?
- Are there beads that sentinel hasn't reviewed yet?

### Confidence Assessment
Rate overall confidence: **High** / **Medium** / **Low**

- **High**: All beads verified, no sentinel flags, evidence is solid. Proceed.
- **Medium**: Most beads verified, minor sentinel notes. Proceed with awareness.
- **Low**: Unverified beads, active sentinel flags, or weak evidence. Address before proceeding.

### Output

```markdown
## Health Check: Phase {N} — {name}

**Beads:** {completed}/{total} verified/hardened | {blocked} blocked | {running} in progress
**Sentinel:** {clean/flags pending/alerts active}
**AQS:** {engaged/skipped (trivial)/pending}
**Confidence:** {High/Medium/Low}

### Issues (if any)
- {issue and recommended action}

### Recommendation
{Proceed / Address [specific items] / Escalate to user}
```

## When Confidence is Low

The Conductor should:
1. Read the specific sentinel flags
2. Re-dispatch runners to address flagged issues
3. Re-run health check after fixes
4. If confidence stays low after 2 cycles, escalate to user
