# Adversarial Quality System — Quick Reference

---

## The Four Domains

| Domain | What It Finds | Red Team | Blue Team |
|--------|--------------|----------|-----------|
| **Functionality** | Business logic defects, edge cases, incorrect state transitions | `red-functionality` | `blue-functionality` |
| **Security** | Input validation gaps, auth bypasses, data exposure paths | `red-security` | `blue-security` |
| **Usability** | API contract violations, inconsistent error shapes, convention deviations | `red-usability` | `blue-usability` |
| **Resilience** | Unhandled I/O failures, missing retry/timeout, resource leaks | `red-resilience` | `blue-resilience` |

---

## Severity Definitions

| Severity | Definition | Functionality Example | Security Example | Usability Example | Resilience Example |
|----------|-----------|----------------------|------------------|-------------------|--------------------|
| **critical** | Immediate data loss, security breach, or service outage | Calculation produces wrong result for all inputs | Unauthenticated access to admin endpoint | API returns 500 with no error body | Database connection never released |
| **high** | Significant defect affecting common use cases | Edge case causes silent data corruption | SQL injection in search parameter | Breaking change to public method signature | No timeout on external HTTP call |
| **medium** | Defect affecting uncommon paths or degrading quality | Off-by-one in paginated results | Verbose error messages leak internal paths | Inconsistent field naming across endpoints | Retry storm possible under load |
| **low** | Minor issue with negligible user impact | Cosmetic logic inconsistency | Overly permissive CORS preflight | Undocumented optional parameter | Log message missing context field |

---

## The Adversarial Cycle

```
Bead proven -> Parallel Launch -> Cross-Reference -> Directed Strike -> Blue Team Response -> Arbiter (disputes only) -> Bead hardened
```

---

## Finding Format (Red Team)

```
## Finding: {ID}
**Domain:** functionality | security | usability | resilience
**Severity:** critical | high | medium | low
**Claim:** {one sentence: what is wrong}
**Minimal reproduction:** {smallest possible demonstration}
**Impact:** {what goes wrong if unaddressed}
**Evidence:** {file:line, guppy output, or test result}
**Confidence:** Verified | Likely | Assumed
**Confidence score:** {0.0-1.0}
**Confidence rationale:** {what drives the score up/down}
```

Note: If `Minimal reproduction` cannot be filled in, `Confidence` must be set to `Assumed`. Blue team may dismiss `Assumed` findings without rebuttal.

---

## Response Format (Blue Team)

```
## Response: {Finding ID}
**Action:** accepted | rebutted | disputed
**If accepted:**
  - Fix: {what was changed, file:line}
  - Verification: {how fix was confirmed}
**If rebutted:**
  - Reasoning: {why this is not a real issue}
  - Evidence: {proof supporting the rebuttal}
**If disputed:**
  - Contested claim: {what specifically is disagreed}
  - Proposed test: {what evidence would resolve this}
**Confidence score:** {0.0-1.0}
**Confidence rationale:** {what drives the score up/down}
```

"Acknowledged" is not a response. "Looks fine" is not a rebuttal. Every response must produce evidence.

### Fast-Track Response Format

For uncontested medium/low severity findings (see SKILL.md Phase 4 for eligibility):

```
## Response: {Finding ID}
**Action:** accepted-fast-track
**Fix:** {file:line — one-line description}
**Verification:** {one-line confirmation}
**Confidence:** {0.0-1.0 with rationale}
```

---

## Verdict Format (Arbiter)

```
## Verdict: {Finding ID}
**Decision:** SUSTAINED | DISMISSED | MODIFIED
**Red team claim:** {summary}
**Blue team position:** {summary}
**Test designed:** {description of the fair test}
**Test result:** {observable evidence}
**Reasoning:** {why this evidence resolves the dispute}
**If MODIFIED:** {adjusted scope/severity}
```

---

## Priority Cross-Reference

| Conductor Selected | Recon Signal | Final Priority | Strike Volume |
|-------------------|-------------|----------------|---------------|
| Yes | Yes | **HIGH** | 20–40 guppies |
| No | Yes | **MED** | 10–20 guppies — Conductor reconsiders |
| Yes | No | **LOW** | 5–10 guppies, skip if still clean |
| No | No | **SKIP** | No strike |

---

## Loop Position: L2.5

```
L0 (Runner) -> L1 (Sentinel) -> L2 (Oracle) -> L2.5 (AQS) -> L3+ (Escalation)
```

AQS fires only after a bead passes Oracle (L2). A bead that fails Oracle never reaches AQS. A bead that exhausts AQS budget escalates to Conductor (L3+), not back to Oracle.

---

## Bead Status

```
pending -> running -> submitted -> verified -> proven -> hardened -> merged
```

- `verified` — Sentinel confirmed acceptance criteria are met
- `proven` — Oracle confirmed claims are VORP-compliant
- `hardened` — AQS confirmed code survives adversarial attack (or Clear bead skipped)
- `merged` — Bead output incorporated into delivery

Clear beads skip AQS entirely: `proven -> merged`
