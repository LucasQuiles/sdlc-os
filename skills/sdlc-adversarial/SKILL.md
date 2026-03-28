---
name: sdlc-adversarial
description: "This skill should be used when the Conductor activates adversarial quality review during Execute phase, when the user runs '/adversarial', or when beads reach 'proven' status and need red team/blue team probing across functionality, security, usability, and resilience domains. Provides the full AQS cycle: recon burst, directed strike with guppy swarms, blue team defense, Kahneman arbitration, and bead hardening."
---

# Adversarial Quality System (AQS)

The AQS is a **complementary, separate review channel** from the Oracle Council. The two systems attack different failure modes and must not be confused:

| System | What it audits | When it fires |
|--------|---------------|---------------|
| **Oracle** | Test integrity and behavioral claims — VORP standard (Verifiable, Observable, Repeatable, Provable) | After runner submits; before AQS |
| **AQS** | Functionality, security, usability, resilience — red team / blue team adversarial pressure | After Oracle passes; L2.5 in loop hierarchy |

Oracle audits whether the *claims are honest*. AQS audits whether the *code survives adversarial attack*. They are structurally independent and do not share findings, agents, or verdict authority.

---

## Model Assignments

| Role | Current Model | Rationale |
|------|--------------|-----------|
| Recon/strike guppies | haiku | Cheap, disposable, high volume — the bullets |
| Red team commanders | sonnet | Genuine reasoning needed for attack design |
| Blue team defenders | sonnet | Must produce real code fixes and evidence |
| Arbiter | opus | Highest-stakes judgment, fires sparingly |

**Model reassignment gate:** Before changing any role's model assignment, run the eval harness at `docs/evals/aqs-model-eval/README.md`. The candidate model must meet Class B (instruction-following) minimums and Class A (evidence reasoning) minimums for the role. This is a required gate, not a suggestion — silent quality collapse from untested model swaps is the failure mode this prevents.

## When to Activate

AQS activation scales with bead complexity. See `scaling-heuristics.md` for full domain selection heuristics and domain-to-bead mapping rules.

| Cynefin Domain | AQS Behavior |
|------------|-------------|
| **Clear** | Skip entirely. Bead goes `proven → merged` directly. |
| **Complicated** | Recon burst fires (all 4 domains, 8 guppies). Conductor selects 1–2 most relevant domains. Only HIGH/MED priority domains get directed strike. |
| **Complex** | All four domains active. Full strike on HIGH/MED. Light sweep on LOW. Cycle 2 governed by convergence assessment. |
| **Chaotic** | Skip entirely. Act-first single runner. Mandatory postmortem bead after merge. |
| **Security-sensitive** | All four domains active regardless of complexity. Security domain always HIGH priority. Cycle 2 mandatory. |

**Domain selection heuristics (Conductor applies these during Phase 1):**
- Bead touches external input or auth → **security**
- Bead creates or modifies user-facing interface or API → **usability**
- Bead implements business logic or state transitions → **functionality**
- Bead touches error handling, I/O, or external services → **resilience**

Cross-reference with recon signals before committing to priority level. Recon can override Conductor judgment in either direction.

---

## The Adversarial Cycle

### Phase 1: Parallel Launch

Two things fire simultaneously the moment a bead reaches `proven` status:

1. **Conductor domain selection** — Conductor analyzes the bead content, applies domain heuristics, and designates preliminary priority per domain (HIGH / MED / LOW / SKIP).
2. **Recon burst** — 8 guppies fire across all four domains, 2 per domain. Each recon guppy asks one lightweight signal-detection question. This is broad and cheap — not deep analysis.

Dispatch all 8 recon guppies in parallel using the Agent tool with `model: haiku`. Recon guppies run regardless of Conductor's preliminary selections. Their purpose is to surface blind spots.

### Phase 2: Cross-Reference

Conductor combines its preliminary selections with recon guppy results to produce final priority per domain:

| Conductor Selected | Recon Signal | Final Priority | Strike Volume |
|-------------------|-------------|----------------|---------------|
| Yes | Yes | **HIGH** | 20–40 guppies |
| No | Yes | **MED** | 10–20 guppies — Conductor reconsiders |
| Yes | No | **LOW** | 5–10 guppies, skip if still clean |
| No | No | **SKIP** | No strike |

Domains at SKIP receive no further action. Domains at LOW get a light sweep only; if clean, they close.

### Phase 2.5: Pretrial Filter

After cross-reference produces final domain priorities but before directed strike fires, the Conductor screens recon signals against three dismissal criteria. This is not a separate agent dispatch — the Conductor applies these filters as part of cross-reference processing.

**Dismissal criteria:**

1. **Scope exclusion** — The recon signal concerns code not changed in this bead. Recon guppies sometimes flag pre-existing issues in surrounding code — these are out of scope for this bead's AQS engagement. Log the signal for future reference but do not strike.

2. **Category exclusion** — The recon signal is about style, formatting, or naming conventions when the domain under review is functionality or security. Style concerns belong to the usability domain. If usability is not active for this bead, the signal is dismissed. If usability IS active, redirect the signal there.

3. **Prior resolution (res judicata)** — The recon signal matches a finding that was previously ruled DISMISSED in the precedent database (`references/precedent-system.md`). Match on: domain + finding type + same code path. If an exact match exists, the signal is precluded from re-litigation. Log: "Precluded — matches precedent {verdict-id}."

**Logging:** Every pretrial dismissal is logged in the recon artifact (`recon-{bead-id}.md`) with the dismissal criterion and reasoning. This creates an audit trail and prevents silent filtering.

**Override:** If the Conductor believes a pretrial dismissal is wrong (e.g., a prior DISMISSED precedent may no longer apply due to changed context), the Conductor can override the dismissal and allow the signal through. Overrides must be documented with reasoning.

### Phase 3: Directed Strike

For each HIGH/MED/LOW domain, dispatch the corresponding red team Sonnet commander agent. Each commander:

1. Receives the bead code, recon guppy signals, and priority level. For COMPLEX and security-sensitive beads, red team commanders also receive the bead's `unsafe_control_actions` list from the safety-analyst's STPA analysis. UCAs provide systematic attack vectors — probe each UCA type rather than relying on heuristic attack selection alone.
2. Designs attack vectors specific to its domain and the signals received
3. Fires guppy swarms — **machine gun volume, narrow focus** — each guppy gets one probe
4. Analyzes guppy results; separates genuine hits from noise
5. Applies mandatory shrinking: every hit must be reduced to minimal reproduction
5.5. **Applies Daubert evidence gate:** Before submitting findings, the red team commander self-checks each finding against three reliability criteria:

   - **Factual basis** — Every file:line reference in the finding must exist. The red team commander verifies by reading the cited locations. Findings citing non-existent code paths are hallucinations and must be dropped.
   - **Methodological reliability** — The finding must come from executed probe output (a guppy returned HIT with evidence), not from pattern-match inference ("this looks like it could be vulnerable"). Inference-only findings are downgraded to `Assumed` confidence.
   - **Known false-positive pattern** — Cross-reference the finding type against the precedent database. If this finding type has been DISMISSED more than twice on similar code patterns, flag it as high-false-positive-risk in the finding. This does not block submission but alerts the blue team and arbiter.

   Findings that fail the factual basis check are dropped entirely (not submitted). Findings that fail methodological reliability are downgraded to `Assumed`. The Daubert gate is a self-check, not an external review — the red team commander applies it to its own output before delivery.
6. Produces formal findings in the required format

RED commanders: `red-functionality`, `red-security`, `red-usability`, `red-resilience` (all Sonnet).

If a finding cannot be shrunk to a minimal reproduction, it is automatically downgraded to `Assumed` confidence. Blue team may dismiss `Assumed` findings without rebuttal.

### Phase 4: Blue Team Response

Domain-matched blue team Sonnet agents receive the findings from Phase 3. For each finding, the blue team agent responds with exactly one of:

- **Accepted** — produce a code fix and verification evidence
- **Rebutted** — produce an evidence-based rebuttal (cite code, tests, or specifications)
- **Disputed** — escalate to Arbiter, stating what evidence would resolve the question

**Fast-track resolution (plea bargaining):** For uncontested findings where both sides agree, a streamlined path is available:

**Eligibility:** A finding qualifies for fast-track when ALL of:
- Red team confidence is `Verified` (not Likely or Assumed)
- Blue team immediately recognizes the issue as real (no analysis needed to confirm)
- Severity is `medium` or `low` (high and critical always get full response)
- Fix is straightforward (single-site change, no architectural implications)

**Fast-track response format:**
```
## Response: {Finding ID}
**Action:** accepted-fast-track
**Fix:** {file:line — one-line description of change}
**Verification:** {one-line confirmation that the fix addresses the finding}
**Confidence:** {0.0-1.0 with brief rationale}
```

Fast-track responses skip the full reproduction cycle, regression narrative, and principle extraction. They are logged in the adversarial report identically to `accepted` findings but marked as fast-tracked. The arbiter is never involved.

**Do not abuse fast-track.** If the blue team is uncertain about whether the issue is real, it is not a fast-track candidate — use the full `accepted` flow with reproduction. Fast-track is for cases where the finding is obviously correct and the fix is obviously right.

BLUE defenders: `blue-functionality`, `blue-security`, `blue-usability`, `blue-resilience` (all Sonnet).

"Acknowledged" is not an accepted response. "Looks fine" is not a rebuttal. Every response must produce evidence.

**Latent condition field (required for accepted and sustained findings):** For each accepted or sustained finding, the Blue Team response must include:

```
**Latent condition:** Which upstream layer should have caught this?
- [ ] L0 Runner (prompt gap, spec ambiguity, missing context)
- [ ] L1 Sentinel (drift-detector blind spot, convention gap)
- [ ] L2 Oracle (VORP check missed this claim type)
- [ ] L2.5 AQS (attack library gap, domain selection miss)
- [ ] L2.75 Hardening (observability gap, error handling gap)
- [ ] Convention Map (unmapped pattern)
- [ ] Code Constitution (missing rule)
- [ ] Safety Constraints (missing constraint)
- [ ] Hook/Guard (validator didn't catch this pattern)
- [ ] Other: {specify}
```

### Phase 5: Arbiter (Disputes Only)

The Arbiter (`arbiter` agent, Opus) fires only when blue team selects `disputed`. This is the **Kahneman adversarial collaboration protocol**:

1. Red team pre-registers: what evidence would prove the issue is real?
2. Blue team pre-registers: what evidence would prove the issue is not real?
3. Arbiter designs a fair test incorporating both criteria — a test both sides would agree is fair if asked beforehand
4. Test executes (Arbiter dispatches a guppy or runs directly)
5. Result is binding: **SUSTAINED** (red team wins, blue team must fix) | **DISMISSED** (blue team rebuttal holds) | **MODIFIED** (partially real, scope adjusted)

The Arbiter has no stake in either side's outcome. If the Arbiter cannot design a fair test, it escalates to the Conductor with explanation. Disputes cannot remain open.

### Structured AQS Exit (FFT-14 Input)

Before transitioning the bead to `hardened`, emit the structured exit block as a YAML code fence in the AQS report:

```yaml
aqs_exit:
  aqs_verdict: {HARDENED | PARTIALLY_HARDENED | DEFERRED}
  arbiter_invoked: {true | false}
  residual_risk_per_domain:
    functionality: {NONE | LOW | MEDIUM | HIGH}
    security: {NONE | LOW | MEDIUM | HIGH}
    usability: {NONE | LOW | MEDIUM | HIGH}
    resilience: {NONE | LOW | MEDIUM | HIGH}
  dominant_residual_risk_domain: {domain with highest risk, tie-break: security > functionality > resilience > usability}
  turbulence_sum: {integer from bead turbulence field}
```

This block is consumed by FFT-14 (cross-model escalation). If cross-model review is active, the `hardened` transition is gated by FFT-14 — the Conductor evaluates FFT-14 using these fields, and the bead only transitions to `hardened` after any cross-model findings are resolved.

See `references/artifact-templates.md` "AQS Structured Exit Block" for field definitions.

### Phase 6: Bead Update

After all domains complete Phase 4 (and Phase 5 where needed):

1. Apply all accepted/sustained code fixes to the bead
2. Write the adversarial quality report (`{bead-id}-aqs.md`) in the required format
3. Update the bead status to `hardened`
4. Persist all adversarial artifacts to the `adversarial/` directory

---

## Dispatch Patterns

Consult **`references/dispatch-patterns.md`** for complete Agent tool templates for all AQS roles (recon guppies, strike guppies, red team commanders, blue team defenders, arbiter). Copy and adapt the templates — fill in `{placeholders}` with actual bead content.

**Quick dispatch reference:**

| Role | Model | Name Pattern | Key Context |
|------|-------|-------------|-------------|
| Recon guppy | haiku | `recon-{domain}-{N}` | Bead content + one signal question |
| Strike guppy | haiku | `strike-{domain}-{N}` | One narrow attack probe |
| Red commander | sonnet | `red-{domain}-{bead-id}` | Bead + recon signals + priority |
| Blue defender | sonnet | `blue-{domain}-{bead-id}` | Bead + red team findings |
| Arbiter | opus | `arbiter-{bead-id}-{finding-id}` | Disputed finding + blue team dispute |

All dispatches use `subagent_type: general-purpose` with the model specified above. **Always set `mode: auto`** to ensure subagents inherit the parent's allow/deny lists and can Write/Edit in dontAsk mode.

---

### Cycle Budget

AQS runs a maximum of **2 full cycles per bead**.

- **Cycle 1:** Always runs when AQS is active. Red team attacks → blue team responds → accepted/sustained fixes applied.

- **Cycle 2 — Convergence Assessment:** After Cycle 1 completes, the Conductor assesses whether the finding space has converged. Cycle 2 fires only if the space has NOT converged.

  **Convergence indicators (all three must be true to skip Cycle 2):**
  1. **Low diversity** — Cycle 1 findings were concentrated in a single domain
  2. **Low severity** — All Cycle 1 fixes were `medium` or `low` severity
  3. **Low volume** — Cycle 1 produced fewer than 3 total findings

  If all three convergence indicators are true → skip Cycle 2. Log the convergence decision with reasoning in the AQS report.

  If ANY indicator is false (findings span multiple domains, any `high`/`critical` fix was applied, or 3+ findings were produced) → Cycle 2 is **mandatory**. The attack surface has been meaningfully changed and needs re-verification.

- **Immediate completion:** If Cycle 1 produces no findings (all domains return clean), AQS completes immediately without Cycle 2. No convergence assessment needed.

- **Budget exhausted:** If 2 cycles complete and residual risk remains unresolved, escalate to Conductor with the adversarial report. Report verdict as `PARTIALLY_HARDENED` or `DEFERRED` as appropriate.

---

## Loop Integration

AQS occupies the **L2.5 position** in the loop hierarchy — between Oracle verification and Conductor escalation:

```
L0 Runner         — Runner self-corrects (3 attempts)
L1 Sentinel       — Sentinel correction directives, fresh runner (2 cycles)
L2 Oracle         — Oracle audits test integrity + behavioral proof (2 cycles)
L2.5 AQS          — Adversarial quality cycle (2 cycles max per bead)
L3+ Escalation    — Conductor handles budget-exhausted failures
```

AQS fires only after a bead has passed L1 (Sentinel) and L2 (Oracle). A bead that fails Oracle never reaches AQS. A bead that fails AQS budget escalates to L3 (Conductor), not back to Oracle.

---

## Bead Status Extension

AQS introduces the `hardened` bead status. The canonical flow for non-trivial beads:

```
pending → running → submitted → verified (L1) → proven (L2) → hardened (L2.5) → merged
```

Clear beads skip AQS entirely:

```
pending → running → submitted → verified (L1) → proven (L2) → merged
```

Status definitions:
- `verified` — Sentinel confirmed acceptance criteria are met
- `proven` — Oracle confirmed claims are VORP-compliant
- `hardened` — AQS confirmed code survives adversarial attack (or trivial bead skipped)
- `merged` — Bead output incorporated into delivery

---

## Artifact Persistence

All AQS artifacts persist in Git alongside the bead files:

```
docs/sdlc/active/{task-id}/
├── beads/
│   ├── {bead-id}.md              ← existing bead file (updated with hardening changes)
│   └── {bead-id}-aqs.md          ← adversarial quality report
└── adversarial/
    ├── recon-{bead-id}.md         ← recon burst results (all 8 guppies)
    ├── findings-{bead-id}.md      ← all red team findings across all domains
    ├── responses-{bead-id}.md     ← all blue team responses
    └── verdicts-{bead-id}.md      ← arbiter verdicts (if any disputes occurred)
```

Write artifacts immediately as each phase completes — do not batch. If a session crashes mid-cycle, the persisted artifacts allow resumption from the last completed phase.

### Resume-from-State Semantics

AQS state is **session-ephemeral, work-persistent** (Gas Town pattern). The Conductor's session may end at any point. The persisted artifacts contain enough state to resume:

```
## AQS State: Bead {id}
**Phase completed:** {1-6, or 0 if not started}
**Cycle:** {1 or 2}
**Domains active:** {list with priorities}
**Recon complete:** {yes/no}
**Findings produced:** {count, or "pending"}
**Responses received:** {count, or "pending"}
**Verdicts issued:** {count, or "pending"}
```

**Resume protocol:** When a new session encounters a bead at `proven` status with existing AQS artifacts:
1. Read the AQS state from the most recent artifact
2. Identify the last completed phase
3. Resume from the next phase — do not re-run completed phases
4. Recon results, findings, and responses from prior phases are still valid
5. If mid-Phase-3 (partial strike results), the Conductor decides: resume with remaining domains or re-run from Phase 1

This state is written to the `recon-{bead-id}.md` file header on every phase transition. The Conductor checks for existing AQS state before launching a new cycle.

---

## Non-Zero-Sum Objective Separation

Red and blue teams optimize **different** objectives — not opposite ends of one metric. This structural separation prevents GAN-style mode collapse where both sides optimize the same loss function in opposite directions.

**Red team objective:** Maximize the severity-weighted count of *sustained* findings — findings that survive blue team scrutiny and arbiter review. Noise findings dismissed by blue team count against red team credibility. This incentivizes genuine discoveries over volume. Marking everything "critical" is self-defeating.

**Blue team objective:** Minimize residual risk in the hardened bead. Blue team succeeds by producing real fixes and evidence-based rebuttals. Rubber-stamped acceptances without real fixes count against quality. The blue team did not write the original code and has no reason to defend it — ego investment is prohibited by design.

**Arbiter objective:** Maximize test fairness and evidence quality. The Arbiter has no stake in either side's outcome. It is not an advocate. It fires sparingly and only on genuine disputes that cannot resolve with available evidence.

This separation is not merely a prompt instruction — it is enforced structurally through separate agents, separate evaluation criteria, and no shared context between red and blue teams.

---

## Instrumented Loop Discipline

The AQS cycle is not vibe-based. Every iteration is falsifiable — hypothesis, experiment, evidence. Consult **`references/instrumented-loop.md`** for the complete protocol.

**Core principles (always in effect):**
- Every guppy probe is a testable hypothesis, not a vague concern (Karpathy)
- One variable at a time — each guppy tests exactly one thing
- Confidence upgrades require new evidence, never argument (Bayesian)
- Belief update per cycle tracks how evidence changed the risk picture
- Prior accumulation: domains with repeated findings get higher priority on subsequent beads
- Security-sensitive beads use registered-report mode (protocol locked before execution)
- Post-merge replay gate catches cross-bead interaction bugs

---

## Adversarial Quality Report Format

Written to `docs/sdlc/active/{task-id}/beads/{bead-id}-aqs.md` after Phase 6.

```markdown
## Adversarial Quality Report: Bead {id}

### Engagement Summary
- **Domains activated:** {list of domains and their priority levels}
- **Recon guppies fired:** {count} (2 per domain × {N active domains})
- **Strike guppies fired:** {count} (broken down by domain)
- **Cycle:** {N} of 2
- **Arbiter invocations:** {count, or "None"}

### Findings

| ID | Domain | Severity | Claim | Status |
|----|--------|----------|-------|--------|
| F1 | {domain} | {severity} | {one-line claim} | accepted / rebutted / sustained / dismissed / modified |
| F2 | ... | ... | ... | ... |

### Hardening Changes
- `{file}:{line}` — {description of change} (finding {ID})
- _(none)_ if no changes were made

### Belief Update
| Domain | Pre-AQS | Post-Cycle-1 | Post-Cycle-2 | Delta |
|--------|---------|--------------|--------------|-------|
| {domain} | {unknown/low/elevated} | {assessment + reason} | {assessment + reason} | {↓ reduced / → stable / ↑ elevated} |

### Residual Risk
- {description of any findings that could not be fully resolved}
- `None` if all findings were resolved

### Verdict
> **HARDENED** — All findings resolved. No residual risk.
> **PARTIALLY_HARDENED** — Some findings resolved. Residual risk documented above.
> **DEFERRED** — Cycle budget exhausted. Conductor escalation required.
```

**Report verdict vs bead status — these are distinct:**

| Report Verdict | Meaning | Bead Status Set To |
|---|---|---|
| `HARDENED` | All findings resolved. No residual risk. | `hardened` |
| `PARTIALLY_HARDENED` | Some findings resolved, residual risk documented. | `hardened` (with residual risk in report) |
| `DEFERRED` | Budget exhausted, unresolved findings remain. | Stays at `proven` — escalated to Conductor at L3 |

Report verdicts describe the *quality of the adversarial engagement*. Bead statuses describe the *bead's position in the lifecycle*. A bead marked `hardened` with a `PARTIALLY_HARDENED` report verdict means: "AQS completed, the bead can proceed, but residual risk exists and is documented." A `DEFERRED` verdict means the bead does NOT advance to `hardened` — it stays at `proven` and the Conductor decides next steps.

---

## Additional Resources

### Reference Files

For detailed patterns and protocols, consult:
- **`references/dispatch-patterns.md`** — Complete Agent tool templates for all AQS roles (recon, strike, red, blue, arbiter)
- **`references/instrumented-loop.md`** — Full Karpathy/Bayesian/registered-report/replay gate protocol
- **`domain-attack-libraries.md`** — Attack vectors organized by domain (functionality, security, usability, resilience)
- **`recon-directives.md`** — 8 copy-paste-ready guppy directive templates for recon burst
- **`arbitration-protocol.md`** — Full Kahneman adversarial collaboration protocol with pre-registered dispute contracts
- **`scaling-heuristics.md`** — Complexity assessment, domain selection, budget management, cross-reference matrix
- **`references/code-constitution.md`** — Living rules distilled from adversarial findings. Blue team checks before fixing; Conductor accumulates after Phase 6.
- **`references/precedent-system.md`** — Arbiter verdict database. Precedent lookup before arbitration; res judicata in pretrial filter.
- **`references/quality-slos.md`** — Error budget definitions and policy governing system velocity.
- **`references/calibration-protocol.md`** — Drift monitoring, noise audits, regression watchlist, LOSA integration.

### Related Plugin Components

- **Agents:** `agents/red-*.md` (4 domain commanders), `agents/blue-*.md` (4 domain defenders), `agents/arbiter.md` (dispute resolver)
- **Agents:** `agents/losa-observer.md` (random-sample quality observer — Haiku tier)
- **Hooks:** `hooks/hooks.json` — Code-enforced schema validation, status guards, vocabulary linting
- **Quick reference:** `references/adversarial-quality.md` — One-page summary of domains, formats, priorities
- **Model eval:** `docs/evals/aqs-model-eval/README.md` — Required gate before changing role model assignments
