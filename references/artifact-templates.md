# Artifact Templates

Copy-paste templates for wave artifacts. Each template uses YAML frontmatter where applicable followed by markdown sections.

---

## 0. Bead — Work Unit

```markdown
# Bead: {id}
**Status:** pending | running | submitted | verified | proven | hardened | reliability-proven | merged | blocked | stuck | escalated
**Type:** investigate | design | implement | verify | review | evolve
**Runner:** [agent name or "unassigned"]
**Dependencies:** [list of bead IDs that must complete first]
**Scope:** [files/areas this bead touches — used for conflict detection]
**Input:** [what context the runner needs]
**Output:** [what the runner must produce]
**Sentinel notes:** [anything the sentinel flagged]
**Cynefin domain:** clear | complicated | complex | chaotic | confusion
**Security sensitive:** true | false
**Complexity source:** essential | accidental
**Profile:** BUILD | INVESTIGATE | REPAIR | EVOLVE
**Intent:** default | migration | registry | debt_companion
**Decision trace:** [path to {bead-id}-decision-trace.md]
**Deterministic checks:** [list of checks routed to scripts per FFT-08]
**Turbulence:** {L0: 0, L1: 0, L2: 0, L2.5: 0, L2.75: 0}
**Dispatched at:** ""
**Review started at:** ""
**Completed at:** ""
**Control actions:** [Projected from hazard-defense-ledger.yaml — distinct control_action values for this bead]
**Unsafe control actions:** [Projected from hazard-defense-ledger.yaml — UCA summaries: control_action — category — scenario]
**Latent condition trace:** [Projected from hazard-defense-ledger.yaml — See HDL-{bead-id}-* records]
**Assumptions:** [explicit list of what must be true for this bead to work — populated by runner]
**Safe-to-fail:** [rollback plan — REQUIRED for Complex domain beads, optional otherwise]
**Confidence:** [runner's self-assessed confidence 0.0-1.0 with rationale — populated after execution]
```

All timestamps are UTC ISO 8601 format (e.g., 2026-03-29T14:22:00Z). Populated by the Conductor at each lifecycle transition.

Beads are written to `docs/sdlc/active/{task-id}/beads/` as individual markdown files.

---

## 1. state.md — Task State

```markdown
---
task-id: ""
description: ""
current-wave:
  number: 0
  name: ""
team-roster:
  - role: Orchestrator
    model: opus
    agent: ""
  - role: Producer
    model: sonnet
    agent: ""
  - role: Verifier
    model: haiku
    agent: ""
created-at: ""
decisions:
  - wave: 0
    decision: ""
    rationale: ""
    timestamp: ""
---

# Task State: {task-id}

_Managed by Orchestrator. Updated at each wave transition._
```

---

### Task Artifacts

Each task directory contains these machine-readable artifacts:

| Artifact | File | Created | Required |
|----------|------|---------|----------|
| Task state | `state.md` | Phase 1 (Frame) | Yes |
| Quality budget | `quality-budget.yaml` | Phase 4 (Execute) | Yes — gates Synthesize and Complete |
| Standards profile | `standards-profile.md` | Phase 2 (Scout) | If standards apply |
| Observability profile | `observability-profile.md` | Phase 2 (Scout) | If observability applies |
| Hazard/Defense Ledger | `hazard-defense-ledger.yaml` | Phase 3 (Architect) | COMPLEX or security_sensitive beads — gates Synthesize and Complete |
| Stress session | `stress-session.yaml` | Phase 4 (Execute) | If stress-sampled — gates Synthesize and Complete |
| STPA Analysis | `stpa-analysis.yaml` | Phase 3 (Architect) | Intermediate: consumed by seeding script |

---

## 2. wave-2-clarify.md — Mission Brief

```markdown
---
wave: 2
artifact: mission-brief
task-id: ""
created-at: ""
---

# Mission Brief

## Objective
<!-- One or two sentences stating what must be true when this task is done. -->

## Scope

### In Scope
-

### Out of Scope
-

## Constraints
-

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
|      |            |        |            |

## Success Criteria
<!-- Each criterion must be testable — someone must be able to verify it pass/fail. -->
1.
2.

## Assumptions

| Assumption | Confidence |
|------------|-----------|
|            | Assumed   |
```

---

## 3. wave-3-discover.md — Discovery Brief

```markdown
---
wave: 3
artifact: discovery-brief
task-id: ""
created-at: ""
---

# Discovery Brief

## Investigation Scope
<!-- What was examined and what was explicitly not examined. -->

## Findings

1. **Finding** — [Confidence: Verified/Likely/Assumed/Unknown]
   <!-- Description, supporting reasoning or evidence. -->

## Evidence Items

1. **Evidence** — Type: file/log/test/trace
   <!-- Path, reference, or description. -->

## Assumptions

| Assumption | Confidence |
|------------|-----------|
|            | Assumed   |

## Open Questions

1.

## Impact Areas
<!-- Systems, components, or flows affected by the findings above. -->
-
```

---

## 4. wave-4-design.md — Design Decision Record

```markdown
---
wave: 4
artifact: design-decision-record
task-id: ""
created-at: ""
---

# Design Decision Record

## Problem Statement
<!-- What decision must be made and why it matters. -->

## Options

### Option A: {name}
**Pros:**
-

**Cons:**
-

### Option B: {name}
**Pros:**
-

**Cons:**
-

## Tradeoff Matrix

| Criterion | Option A | Option B |
|-----------|---------|---------|
|           |         |         |

## Recommendation
<!-- State the chosen option. -->

### Justification
<!-- Why this option over the alternatives. -->

## Validation Strategy
<!-- How will we know the design is correct before full build? -->

## Risks
-

## Edge Cases
-
```

---

## 5. wave-5-gate.md — Gate Decision

```markdown
---
wave: 5
artifact: gate-decision
task-id: ""
created-at: ""
---

# Gate Decision

## Readiness Checklist

- [ ] Mission Brief complete and agreed
- [ ] Discovery findings have sufficient confidence
- [ ] Design decision record produced with at least two options evaluated
- [ ] No unresolved Unknown-confidence blockers
- [ ] Team roster confirmed and agents available

## Decision

> **GO / NO-GO / LOOP-BACK / ESCALATE**

_(Delete all but one)_

## Rationale
<!-- Why this decision. Reference specific checklist items or findings. -->

## Open Risks Accepted
<!-- Risks known at gate time that the team accepts proceeding with. -->
-

## Conditions
<!-- Required only for conditional GO or LOOP-BACK. -->
-
```

---

## 6. wave-6-build.md — Change Set

```markdown
---
wave: 6
artifact: change-set
task-id: ""
created-at: ""
---

# Change Set

## Implementation Increments

### Increment 1: {description}

**Files Changed:**
-

**Tests Written:**
-

**Validation Result:** [Confidence: Verified/Likely/Assumed/Unknown]
<!-- What was run and what was observed. -->

### Increment 2: {description}

**Files Changed:**
-

**Tests Written:**
-

**Validation Result:** [Confidence: Verified/Likely/Assumed/Unknown]

## Deviations from Design
<!-- List any deviations from the wave-4 Design Decision Record with rationale. -->
- None / {deviation and reason}

## Intermediate Validation Notes
<!-- Notes from validation runs during build — errors encountered, fixes applied. -->
```

---

## 7. wave-7-verify.md — Verification Report

```markdown
---
wave: 7
artifact: verification-report
task-id: ""
created-at: ""
---

# Verification Report

## Criteria Checklist

| Criterion (from Mission Brief) | Result | Evidence |
|-------------------------------|--------|---------|
|                               | PASS/FAIL/PARTIAL | |

## Regressions Checked
<!-- List what was checked for regression and the outcome. -->
-

## Residual Uncertainty
<!-- What remains unknown or unverified after this wave. -->
-

## Confidence Level
[Verified/Likely/Assumed/Unknown] — _brief justification_

## Verdict

> **PASS / PARTIAL / FAIL**

_(Delete all but one)_
```

---

## 8. wave-8-review.md — Review Memo

```markdown
---
wave: 8
artifact: review-memo
task-id: ""
created-at: ""
---

# Review Memo

## Issues

| Severity | Description | Recommendation |
|----------|-------------|---------------|
| Critical/Major/Minor | | |

## Strengths
<!-- What was done well that should be preserved or replicated. -->
-

## Concerns
<!-- Issues that are not blockers but warrant attention going forward. -->
-

## Decision

> **Approve / Revise / Escalate**

_(Delete all but one)_

### Rationale
<!-- Specific basis for the decision. Reference issues table or criteria checklist. -->
```

---

## 9. wave-10-handoff.md — Delivery Summary

```markdown
---
wave: 10
artifact: delivery-summary
task-id: ""
created-at: ""
---

# Delivery Summary

## Objective
<!-- Restate the original objective from the Mission Brief. -->

## What Changed
<!-- Enumerate what was built, modified, or removed. Be concrete. -->
-

## How We Know
<!-- Evidence that the objective was met. Reference test results, logs, diffs. -->
-

## What's Uncertain
<!-- Residual unknowns or assumptions that persist into production. -->
-

## Risks and Caveats
<!-- Known limitations, edge cases not covered, or conditions under which this may fail. -->
-

## Next Action
<!-- What the recipient of this handoff should do next. -->
```

---

## 10. AQS Finding — Red Team

```markdown
## Finding: {ID}
**Domain:** functionality | security | usability | resilience
**Severity:** critical | high | medium | low
**Claim:** {One sentence: what is wrong}
**Minimal reproduction:** {The smallest possible demonstration}
**Impact:** {What goes wrong if unaddressed}
**Evidence:** {file:line, guppy output, or test result}
**Confidence:** Verified | Likely | Assumed | Unknown
```

---

## 11. AQS Response — Blue Team

```markdown
## Response: {Finding ID}
**Action:** accepted | rebutted | disputed

### If accepted:
- **Fix:** {what was changed, file:line}
- **Verification:** {how fix was confirmed}

### If rebutted:
- **Reasoning:** {why not a real issue}
- **Evidence:** {proof}

### If disputed:
- **Contested claim:** {what is disagreed}
- **Proposed test:** {what evidence would resolve}
```

---

## 12. AQS Verdict — Arbiter

```markdown
## Verdict: {Finding ID}
**Decision:** SUSTAINED | DISMISSED | MODIFIED
**Red team claim:** {summary}
**Blue team position:** {summary}
**Test designed:** {fair test description}
**Test result:** {observable evidence}
**Reasoning:** {why this resolves the dispute}
**If MODIFIED:** {adjusted scope/severity}
```

---

## 13. AQS Report — Per Bead

```markdown
## Adversarial Quality Report: Bead {id}

### Engagement Summary
- **Domains activated:** {list}
- **Priority:** {per domain}
- **Recon guppies fired:** {count}
- **Strike guppies fired:** {count}
- **Cycle:** {N} of 2

### Findings
| ID | Domain | Severity | Claim | Status |
|----|--------|----------|-------|--------|
| F1 | {domain} | {severity} | {claim} | {accepted/rebutted/disputed → verdict} |

### Hardening Changes
- {file}:{line} — {description} ({finding ID})

### Residual Risk
- {any unresolved findings, or "None"}

### Verdict
> **[HARDENED | PARTIALLY_HARDENED | DEFERRED]**
```

---

### AQS Structured Exit Block

Machine-readable fields emitted alongside the prose AQS report. Consumed by FFT-14 (cross-model escalation).

```yaml
aqs_exit:
  aqs_verdict: HARDENED | PARTIALLY_HARDENED | DEFERRED
  arbiter_invoked: true | false
  residual_risk_per_domain:
    functionality: NONE | LOW | MEDIUM | HIGH
    security: NONE | LOW | MEDIUM | HIGH
    usability: NONE | LOW | MEDIUM | HIGH
    resilience: NONE | LOW | MEDIUM | HIGH
  dominant_residual_risk_domain: functionality | security | usability | resilience
  turbulence_sum: <integer>
```

**Field definitions:**
- `aqs_verdict`: Final AQS determination. HARDENED = clean or all findings resolved. PARTIALLY_HARDENED = residual risk documented. DEFERRED = blocked, escalate to L3.
- `arbiter_invoked`: True if the arbiter agent was dispatched during any AQS cycle on this bead.
- `residual_risk_per_domain`: Per-domain risk after blue team resolution. NONE = no findings or all resolved. LOW/MEDIUM/HIGH = accepted findings with documented residual risk.
- `dominant_residual_risk_domain`: Domain with highest residual risk. Tie-break order: security > functionality > resilience > usability.
- `turbulence_sum`: Sum of bead turbulence fields (L0 + L1 + L2 + L2.5 + L2.75).
