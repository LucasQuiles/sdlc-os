---
name: sdlc-adversarial
description: "Adversarial Quality System — continuous red team/blue team shadow during Execute phase. Activates domain-specialized adversaries against completed beads to find and harden against functionality, security, usability, and resilience weaknesses."
---

# Adversarial Quality System (AQS)

The AQS is a **complementary, separate review channel** from the Oracle Council. The two systems attack different failure modes and must not be confused:

| System | What it audits | When it fires |
|--------|---------------|---------------|
| **Oracle** | Test integrity and behavioral claims — VORP standard (Verifiable, Observable, Repeatable, Provable) | After runner submits; before AQS |
| **AQS** | Functionality, security, usability, resilience — red team / blue team adversarial pressure | After Oracle passes; L2.5 in loop hierarchy |

Oracle audits whether the *claims are honest*. AQS audits whether the *code survives adversarial attack*. They are structurally independent and do not share findings, agents, or verdict authority.

---

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

### Recon Guppy Dispatch (Phase 1)

Dispatch all 8 in parallel. Two per domain, each with a different signal-detection angle.

```
Agent tool:
  subagent_type: general-purpose
  model: haiku
  name: "recon-{domain}-{N}"
  description: "Recon probe: {domain} domain, signal {N}"
  prompt: |
    You are a recon probe for the {domain} domain.

    ## Bead Under Analysis
    {bead content — objective, scope, code changes}

    ## Your Question
    {one focused signal-detection question for this domain}
    Example questions by domain:
    - functionality: "Are there input states or edge cases the bead does not handle?"
    - security: "Are there external inputs that reach data operations without validation?"
    - usability: "Are there API contracts or error messages that deviate from codebase conventions?"
    - resilience: "Are there dependency calls or I/O operations without error handling?"

    Answer: SIGNAL (one-line description of what you found) or NO_SIGNAL.
    Nothing else. One probe, one answer.
```

### Strike Guppy Dispatch (Phase 3)

Red team commanders design the target list and dispatch these. Volume matches priority level.

```
Agent tool:
  subagent_type: general-purpose
  model: haiku
  name: "strike-{domain}-{N}"
  description: "Strike probe: {domain} — {short probe description}"
  prompt: |
    You are an attack probe. Test exactly this:

    ## Target
    {specific attack vector from the red team commander}

    ## Code Under Test
    {relevant code snippet or file reference}

    ## Your Probe
    {the one narrow question or test to execute}

    Report:
    - What you tried
    - What happened
    - HIT (describe the vulnerability/defect) or MISS
    Nothing else.
```

### Red Team Commander Dispatch (Phase 3)

```
Agent tool:
  subagent_type: general-purpose
  model: sonnet
  name: "red-{domain}-{bead-id}"
  description: "Red team {domain} commander: bead {bead-id}"
  prompt: |
    You are the Red Team {Domain} Commander. Your job is to find real
    problems, not generate noise. You are rewarded for genuine findings
    that survive blue team scrutiny — noise counts against your credibility.

    ## Bead Under Attack
    {full bead content — objective, scope, code changes, tests}

    ## Recon Signals
    {recon guppy results for this domain}

    ## Priority Level
    {HIGH | MED | LOW} — dispatch {20-40 | 10-20 | 5-10} strike guppies

    ## Your Mission
    1. Study the bead and recon signals
    2. Design attack vectors specific to your domain
    3. Dispatch strike guppies — machine gun volume, narrow focus
    4. Triage guppy results: real hits vs noise
    5. For each real hit: reduce to minimal reproduction (mandatory)
    6. Produce formal findings in required format

    ## Output Format (per finding)
    ## Finding: {ID}
    **Domain:** {domain}
    **Severity:** critical | high | medium | low
    **Claim:** {one sentence: what is wrong}
    **Minimal reproduction:** {smallest possible demonstration}
    **Impact:** {what goes wrong if unaddressed}
    **Evidence:** {file:line, guppy output, or test result}
    **Confidence:** Verified | Likely | Assumed

    If you cannot fill in Minimal reproduction, set Confidence to Assumed.
    Severity must be calibrated — marking everything "critical" destroys your credibility.
```

### Blue Team Defender Dispatch (Phase 4)

```
Agent tool:
  subagent_type: general-purpose
  model: sonnet
  name: "blue-{domain}-{bead-id}"
  description: "Blue team {domain} defender: bead {bead-id}"
  prompt: |
    You are the Blue Team {Domain} Defender. You receive findings from the
    red team and respond to each one honestly. You did NOT write this code.
    You have no ego investment in defending it.

    ## Bead Context
    {full bead content — objective, scope, code changes, tests}

    ## Red Team Findings
    {all findings from the red team commander for this domain}

    ## Your Mission
    For each finding, respond with exactly one of:
    - ACCEPTED: produce a code fix and verification evidence
    - REBUTTED: produce evidence-based rebuttal (cite code, tests, or spec)
    - DISPUTED: escalate to Arbiter, state what evidence would resolve it

    "Acknowledged" is not a response. "Looks fine" is not a rebuttal.
    Never rubber-stamp. Never accept without fixing.

    ## Output Format (per finding)
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
```

### Arbiter Dispatch (Phase 5)

```
Agent tool:
  subagent_type: general-purpose
  model: opus
  name: "arbiter-{bead-id}-{finding-id}"
  description: "Arbiter: disputed finding {finding-id} on bead {bead-id}"
  prompt: |
    You are a neutral Arbiter. You have no stake in either side's outcome.
    Your job is to design a fair test and produce a binding verdict.

    ## Disputed Finding
    {full finding from red team}

    ## Blue Team Dispute
    {blue team's disputed response}

    ## Your Protocol (Kahneman adversarial collaboration)
    1. Extract what evidence red team claims would prove the issue is real
    2. Extract what evidence blue team claims would prove the issue is not real
    3. Design a test that both sides would agree is fair if asked beforehand
    4. Execute the test (dispatch a guppy or run directly)
    5. Publish a binding verdict

    ## Output Format
    ## Verdict: {Finding ID}
    **Decision:** SUSTAINED | DISMISSED | MODIFIED
    **Red team claim:** {summary}
    **Blue team position:** {summary}
    **Test designed:** {description of the fair test}
    **Test result:** {observable evidence}
    **Reasoning:** {why this evidence resolves the dispute}
    **If MODIFIED:** {adjusted scope/severity}

    If you cannot design a fair test, output:
    ESCALATE: {explanation of why a fair test cannot be designed}
```

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

---

## Non-Zero-Sum Objective Separation

Red and blue teams optimize **different** objectives — not opposite ends of one metric. This structural separation prevents GAN-style mode collapse where both sides optimize the same loss function in opposite directions.

**Red team objective:** Maximize the severity-weighted count of *sustained* findings — findings that survive blue team scrutiny and arbiter review. Noise findings dismissed by blue team count against red team credibility. This incentivizes genuine discoveries over volume. Marking everything "critical" is self-defeating.

**Blue team objective:** Minimize residual risk in the hardened bead. Blue team succeeds by producing real fixes and evidence-based rebuttals. Rubber-stamped acceptances without real fixes count against quality. The blue team did not write the original code and has no reason to defend it — ego investment is prohibited by design.

**Arbiter objective:** Maximize test fairness and evidence quality. The Arbiter has no stake in either side's outcome. It is not an advocate. It fires sparingly and only on genuine disputes that cannot resolve with available evidence.

This separation is not merely a prompt instruction — it is enforced structurally through separate agents, separate evaluation criteria, and no shared context between red and blue teams.

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

### Residual Risk
- {description of any findings that could not be fully resolved}
- `None` if all findings were resolved

### Verdict
> **HARDENED** — All findings resolved. No residual risk.
> **PARTIALLY_HARDENED** — Some findings resolved. Residual risk documented above.
> **DEFERRED** — Cycle budget exhausted. Conductor escalation required.
```

**Verdict criteria:**
- `HARDENED`: All findings accepted/rebutted/arbitrated. Residual Risk is None.
- `PARTIALLY_HARDENED`: Some findings resolved, but one or more remain open or disputed without binding verdict.
- `DEFERRED`: AQS budget exhausted (2 cycles complete) with unresolved findings. Conductor must decide next action.
