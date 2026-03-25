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
