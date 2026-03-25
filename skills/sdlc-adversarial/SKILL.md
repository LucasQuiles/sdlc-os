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

| Complexity | AQS Behavior |
|------------|-------------|
| **Trivial** | Skip entirely. Bead goes `proven → merged` directly. |
| **Moderate** | Recon burst fires (all 4 domains, 8 guppies). Conductor selects 1–2 most relevant domains. Only HIGH/MED priority domains get directed strike. |
| **Complex** | All four domains active. Full strike on HIGH/MED. Light sweep on LOW. Cycle 2 mandatory if Cycle 1 produced accepted/sustained fixes. |
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

### Phase 3: Directed Strike

For each HIGH/MED/LOW domain, dispatch the corresponding red team Sonnet commander agent. Each commander:

1. Receives the bead code, recon guppy signals, and priority level
2. Designs attack vectors specific to its domain and the signals received
3. Fires guppy swarms — **machine gun volume, narrow focus** — each guppy gets one probe
4. Analyzes guppy results; separates genuine hits from noise
5. Applies mandatory shrinking: every hit must be reduced to minimal reproduction
6. Produces formal findings in the required format

RED commanders: `red-functionality`, `red-security`, `red-usability`, `red-resilience` (all Sonnet).

If a finding cannot be shrunk to a minimal reproduction, it is automatically downgraded to `Assumed` confidence. Blue team may dismiss `Assumed` findings without rebuttal.

### Phase 4: Blue Team Response

Domain-matched blue team Sonnet agents receive the findings from Phase 3. For each finding, the blue team agent responds with exactly one of:

- **Accepted** — produce a code fix and verification evidence
- **Rebutted** — produce an evidence-based rebuttal (cite code, tests, or specifications)
- **Disputed** — escalate to Arbiter, stating what evidence would resolve the question

BLUE defenders: `blue-functionality`, `blue-security`, `blue-usability`, `blue-resilience` (all Sonnet).

"Acknowledged" is not an accepted response. "Looks fine" is not a rebuttal. Every response must produce evidence.

### Phase 5: Arbiter (Disputes Only)

The Arbiter (`arbiter` agent, Opus) fires only when blue team selects `disputed`. This is the **Kahneman adversarial collaboration protocol**:

1. Red team pre-registers: what evidence would prove the issue is real?
2. Blue team pre-registers: what evidence would prove the issue is not real?
3. Arbiter designs a fair test incorporating both criteria — a test both sides would agree is fair if asked beforehand
4. Test executes (Arbiter dispatches a guppy or runs directly)
5. Result is binding: **SUSTAINED** (red team wins, blue team must fix) | **DISMISSED** (blue team rebuttal holds) | **MODIFIED** (partially real, scope adjusted)

The Arbiter has no stake in either side's outcome. If the Arbiter cannot design a fair test, it escalates to the Conductor with explanation. Disputes cannot remain open.

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

All dispatches use `subagent_type: general-purpose` with the model specified above.

---

## Cycle Budget

AQS runs a maximum of **2 full cycles per bead**.

- **Cycle 1:** Red team attacks → blue team responds → accepted/sustained fixes applied
- **Cycle 2:** Fires only if Cycle 1 produced accepted or arbiter-sustained fixes. Re-attacks the hardened code to verify fixes hold and no new attack surface was introduced.
- **Immediate completion:** If Cycle 1 produces no findings (all domains return clean), AQS completes immediately without Cycle 2.
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

Trivial beads skip AQS entirely:

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

### Related Plugin Components

- **Agents:** `agents/red-*.md` (4 domain commanders), `agents/blue-*.md` (4 domain defenders), `agents/arbiter.md` (dispute resolver)
- **Hooks:** `hooks/hooks.json` — Code-enforced schema validation, status guards, vocabulary linting
- **Quick reference:** `references/adversarial-quality.md` — One-page summary of domains, formats, priorities
- **Model eval:** `docs/evals/aqs-model-eval/README.md` — Required gate before changing role model assignments
