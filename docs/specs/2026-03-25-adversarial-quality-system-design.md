# Adversarial Quality System (AQS) — Design Specification

**Date:** 2026-03-25
**Status:** Draft
**Plugin:** sdlc-os
**Author:** Conductor (Opus)

---

## 1. Problem Statement

The SDLC OS has an Oracle Council that audits test integrity, behavioral proof, and mutation resistance — but this is narrowly scoped to code correctness and fires reactively after work is done. There is no continuous adversarial pressure system that covers the full quality spectrum: functionality, security, usability, and resilience. Without structured adversarial friction across these domains, defects that pass automated checks and code review survive into delivery.

## 2. Solution Overview

The Adversarial Quality System (AQS) adds continuous red team / blue team pressure during the Execute phase. Four domain-specialized red team agents command high-volume haiku guppy swarms to probe completed beads. Domain-matched blue team agents harden against confirmed findings. An Opus arbiter resolves disputes via Kahneman adversarial collaboration protocol.

### Relationship to Existing SDLC OS

- **Complementary to the Oracle Council** — separate review channel attacking different failure modes (Oracle: test/claim integrity; AQS: functionality, security, usability, resilience)
- **Orchestrated by the existing Conductor** — no new orchestration role
- **Uses existing bead, loop, and handoff systems** — extends rather than replaces
- **Follows existing naming conventions, frontmatter format, and output patterns**

### Research Foundation

This design is grounded in six research streams:

1. **Security & pentesting industry** — Purple teaming evolution, continuous vs point-in-time testing, rules of engagement
2. **AI/LLM adversarial practices** — Pairwise comparison > pointwise scoring (100% vs 28% attack success), Agent-as-a-Judge (90% human agreement vs 70% LLM-as-Judge), heterogeneous agents outperform homogeneous
3. **Beyond-security adversarial practices** — Chaos engineering, mutation testing at Google scale, adversarial code review, game days
4. **High-stakes industry QA** — Aviation CRM/ASRS, nuclear defense-in-depth, NASA IV&V, financial stress-testing, adversarial legal system
5. **Game theory & incentive design** — Non-zero-sum objective separation, steep severity gradients (Google bug bounty: 724% increase in critical findings from reward restructuring), proper scoring rules, mandatory shrinking from property-based testing, Bayesian Truth Serum, contract-based blame assignment
6. **Adversarial team psychology** — Army Red Team University 4 pillars, Nemeth's authentic vs assigned dissent research, Edmondson's safety+accountability framework, Klein's pre-mortem technique, Johnson & Johnson's constructive controversy

### Key Design Principles Derived from Research

1. **Non-zero-sum beats zero-sum.** Red and blue teams optimize separate objectives, not opposite ends of one metric.
2. **Pairwise comparison over absolute scoring.** Adversarial agents evaluate comparatively, not absolutely.
3. **Multiple independent review channels.** AQS + Oracle = two channels attacking different failure modes.
4. **Authentic dissent over role-played criticism.** Structural independence and genuinely different evaluation criteria, not just a "be critical" prompt.
5. **Pre-mortem framing > critique framing.** "Imagine this has failed, explain why" produces 30% more failure-mode identification.
6. **Mandatory shrinking.** Findings must be reduced to minimal reproducing cases — noise prevention.
7. **Steep severity gradients.** Critical findings vastly outweigh trivial ones — discourages volume gaming.
8. **Structural independence.** Red team has no dependency on builder's success.
9. **Adversarial structures decay toward performative.** System needs meta-monitoring of its own adversarial health.
10. **Safety + accountability = the learning zone.** Permission to challenge AND expectation of rigor.

---

## 3. The Four Domains

### 3.1 Functionality

Finds logic errors, missing edge cases, broken workflows, incorrect behavior.

Attack surface:
- Unhandled input states and edge cases
- Logic errors and off-by-one mistakes
- Broken workflows and missing state transitions
- Contract violations (does the code do what the spec says?)
- Regression against prior behavior

### 3.2 Security

Finds injection vectors, auth bypass, data exposure, insecure defaults.

Attack surface:
- OWASP Top 10 attack patterns
- Input validation gaps (injection, XSS, path traversal)
- Authentication and authorization bypass
- Data exposure in errors, logs, or responses
- Insecure defaults and dependency vulnerabilities
- Secrets and credential handling

### 3.3 Usability

Finds confusing APIs, poor error messages, inconsistent interfaces, accessibility gaps, DX friction.

Attack surface:
- API consistency with existing codebase conventions
- Error message clarity and actionability
- Documentation accuracy against actual behavior
- Accessibility violations (WCAG patterns)
- Developer experience friction (confusing names, surprising behavior, missing types)
- Cognitive load assessment

### 3.4 Resilience

Finds failure handling gaps, missing recovery paths, resource exhaustion, degradation failures.

Attack surface:
- Failure mode analysis (what if each dependency fails?)
- Error propagation paths (does one failure cascade?)
- Recovery behavior (can the system return to good state?)
- Resource exhaustion (memory leaks, unbounded growth, connection pools)
- Timeout and retry behavior
- Graceful degradation under partial failure

---

## 4. Agent Architecture

### 4.1 Agent Roster (9 new agent files + existing guppy agent)

| Agent | Model | Role | New File? |
|---|---|---|---|
| `red-functionality` | Sonnet | Red team commander — functionality domain | Yes |
| `red-security` | Sonnet | Red team commander — security domain | Yes |
| `red-usability` | Sonnet | Red team commander — usability domain | Yes |
| `red-resilience` | Sonnet | Red team commander — resilience domain | Yes |
| `blue-functionality` | Sonnet | Blue team defender — functionality domain | Yes |
| `blue-security` | Sonnet | Blue team defender — security domain | Yes |
| `blue-usability` | Sonnet | Blue team defender — usability domain | Yes |
| `blue-resilience` | Sonnet | Blue team defender — resilience domain | Yes |
| `arbiter` | Opus | Dispute resolver — Kahneman protocol | Yes |
| Recon guppies | Haiku | Broad lightweight probes | No — existing `guppy` agent, domain-specialized prompts |
| Strike guppies | Haiku | High-volume narrow attack probes | No — existing `guppy` agent, attack-specialized prompts |

### 4.2 Non-Zero-Sum Objective Separation

Red and blue teams optimize **different** objectives, not opposite ends of one metric:

- **Red team objective:** Maximize the severity-weighted count of *sustained* findings (findings that survive blue team scrutiny and arbiter review). Noise and dismissed findings count against them. This incentivizes genuine discoveries over volume.
- **Blue team objective:** Minimize residual risk in the hardened bead. They succeed by producing real fixes and evidence-based rebuttals, not by dismissing findings. Rubber-stamped acceptances without real fixes count against them.
- **Arbiter objective:** Maximize test fairness and evidence quality. The arbiter has no stake in either side's outcome.

This separation prevents the GAN-style mode collapse that occurs when both sides optimize the same loss function in opposite directions.

### 4.3 Red Team Agent Pattern

All four red team agents share a common structure, differentiated by domain expertise, attack libraries, and guppy directives.

```markdown
---
name: red-{domain}
description: "Red team {domain} specialist — commands guppy swarms
  to probe completed beads for {domain} weaknesses, analyzes results,
  produces findings with mandatory shrinking"
model: sonnet
---

## Identity
You are a Red Team {Domain} Specialist. Your job is to find real
problems, not generate noise. You are rewarded for genuine findings
that survive blue team scrutiny, not for volume.

## Operating Model
1. RECON — Receive bead + recon guppy signals. Study the code.
2. TARGET — Design attack vectors specific to your domain.
3. FIRE — Dispatch guppy swarms. Each guppy gets ONE narrow probe.
   High volume, narrow focus. Machine gun, not sniper.
4. ASSESS — Triage guppy results. Separate real hits from noise.
5. SHRINK — For each real hit, reduce to minimal reproduction.
   If you cannot shrink it, downgrade to Assumed confidence.
6. REPORT — Produce formal findings in required format.

## Constraints
- You have NO dependency on the builder's success.
- You have NEVER seen this code before this engagement.
- You must produce minimal reproductions, not vague concerns.
- Severity must be calibrated — marking everything "critical"
  destroys your credibility.
- Quality over quantity. Ten noise findings are worth less than
  one genuine critical.
```

### 4.4 Blue Team Agent Pattern

```markdown
---
name: blue-{domain}
description: "Blue team {domain} defender — triages red team findings,
  produces code fixes for accepted findings, evidence-based rebuttals
  for rejected findings, or dispute escalations"
model: sonnet
---

## Identity
You are a Blue Team {Domain} Defender. You receive findings from the
red team and respond to each one honestly. You have NO ego investment
in the original code — you did not write it.

## Operating Model
1. TRIAGE — Review each finding. Is this real, false positive,
   or ambiguous?
2. For REAL findings:
   - Produce a code fix
   - Verify the fix addresses the finding
   - Document what was changed and why
3. For FALSE POSITIVES:
   - Produce evidence-based rebuttal
   - Show specifically why the finding is not a real issue
   - Cite code, tests, or specifications
4. For AMBIGUOUS findings:
   - Escalate to Arbiter with disputed status
   - State what evidence would resolve the question
   - Do NOT guess — genuine uncertainty should escalate

## Constraints
- You did NOT build this code. You have no reason to defend it.
- Accept real findings without ego. Fix them.
- Rebut false positives with evidence, not dismissal.
- Never rubber-stamp — "looks fine" is not a rebuttal.
- Never accept without fixing — "acknowledged" is not a response.
```

### 4.5 Arbiter Agent

```markdown
---
name: arbiter
description: "Dispute resolver — runs Kahneman adversarial
  collaboration protocol when red and blue teams disagree.
  Designs fair tests, executes them, produces binding verdicts.
  Fires only on disputed findings."
model: opus
---

## Identity
You are a neutral Arbiter. You have seen neither the red team's
investigation process nor the blue team's defense preparation.
You see only their final positions and design a fair test.

## Protocol
1. Receive red team's finding + blue team's dispute
2. Extract: what does each side claim? What evidence would each
   side accept as resolution?
3. Design a test that:
   - Both sides would agree is fair (if asked beforehand)
   - Produces observable, reproducible evidence
   - Has a clear pass/fail criterion
4. Execute the test (dispatch guppy or run directly)
5. Publish verdict:
   - FINDING SUSTAINED — red team's issue is real, blue team
     must fix
   - FINDING DISMISSED — blue team's rebuttal holds, finding
     is closed
   - FINDING MODIFIED — partially real, scope adjusted
6. Include all evidence. Verdict is binding.

## Constraints
- You are NOT an advocate for either side.
- Your test must be executable, not theoretical.
- If you cannot design a fair test, escalate to Conductor
  with explanation.
- You fire sparingly — most findings resolve without you.
```

### 4.6 Guppy Usage

Recon and strike guppies use the existing `guppy` agent definition with domain-specialized prompts. No new agent definition needed.

**Recon guppy example:**
```
You are a recon probe for the security domain. Examine this code
and answer ONE question: "Are there any external inputs that reach
data operations without validation?" Answer: SIGNAL (with one-line
description) or NO_SIGNAL. Nothing else.
```

**Strike guppy example:**
```
You are an attack probe. Test exactly this: "What happens when
the userId parameter is set to ../../../etc/passwd?"
Report: what you tried, what happened, whether it's a hit.
Nothing else.
```

**Volume model:** Guppies are machine gun fire. High volume, narrow focus. Each guppy gets ONE probe. The red team commander designs the target list and pulls the trigger.

---

## 5. The Adversarial Cycle

### 5.1 Trigger

A bead completes and passes Sentinel check (existing flow). Bead is marked `verified`. AQS activates.

### 5.2 Phase 1: Parallel Launch

Two things happen simultaneously:

1. **Conductor analyzes** the bead and selects likely relevant domains based on heuristics (Section 7)
2. **Recon guppy burst** fires across all four domains — 8 guppies total, 2 per domain

### 5.3 Phase 2: Cross-Reference

Conductor combines its domain selection with recon results:

| Conductor Selected | Recon Signal | Priority | Action |
|---|---|---|---|
| Yes | Yes | **HIGH** | Heavy strike (20-40 guppies) |
| No | Yes | **MED** | Medium strike (10-20 guppies) — Conductor reconsiders |
| Yes | No | **LOW** | Light sweep (5-10 guppies), skip if still clean |
| No | No | **SKIP** | No strike |

### 5.4 Phase 3: Directed Strike

For each HIGH/MED/LOW domain, the corresponding red team Sonnet commander is dispatched:

1. Receives bead code + recon signals + priority level
2. Designs attack vectors specific to domain and signals
3. Fires guppy swarms — volume matches priority level
4. Analyzes guppy results, separates hits from noise
5. Shrinks each hit to minimal reproduction
6. Produces formal findings

### 5.5 Phase 4: Blue Team Response

Domain-matched blue team Sonnet agents receive findings:

For each finding, respond with one of:
- **Accepted** — produce code fix + verification
- **Rebutted** — produce evidence-based rebuttal
- **Disputed** — escalate to Arbiter with proposed resolution test

### 5.6 Phase 5: Arbiter (Disputes Only)

Fires only when blue team selects `disputed`. Kahneman adversarial collaboration protocol:

1. Red team states what evidence would prove the issue is real
2. Blue team states what evidence would prove the issue is not real
3. Arbiter designs a fair test incorporating both criteria
4. Test executes (arbiter dispatches guppy or runs directly)
5. Result is binding — SUSTAINED, DISMISSED, or MODIFIED

### 5.7 Phase 6: Bead Update

Bead file updated with:
- Hardening code changes (from accepted findings)
- Adversarial quality report (summary of engagement)
- Bead status changed to `hardened`

### 5.8 Cycle Diagram

```
Bead completes & passes Sentinel
            │
            ▼
    ┌───────────────────┐
    │  PARALLEL LAUNCH   │
    │                    │
    │ ① Conductor        │
    │    analyzes bead,  │
    │    selects domains │
    │                    │
    │ ② Recon guppy      │
    │    burst fires     │
    │    (all 4 domains) │
    └───────────────────┘
            │
            ▼
    ┌───────────────────┐
    │  CROSS-REFERENCE   │
    │                    │
    │ Both signal  → HIGH│
    │ Recon only   → MED │
    │ Conductor    → LOW │
    │ only               │
    │ Neither     → SKIP │
    └───────────────────┘
            │
            ▼
    ┌───────────────────┐
    │  DIRECTED STRIKE   │
    │                    │
    │ Red team Sonnet    │
    │ deploys for HIGH/  │
    │ MED domains.       │
    │ Fires guppy swarms │
    │ (machine gun).     │
    │ Analyzes results.  │
    │ Produces findings  │
    │ with mandatory     │
    │ shrinking.         │
    └───────────────────┘
            │
            ▼
    ┌───────────────────┐
    │  BLUE TEAM         │
    │  RESPONSE          │
    │                    │
    │ Per finding:       │
    │  • Accept & fix    │
    │  • Rebut with      │
    │    evidence        │
    │  • Dispute →       │
    │    Arbiter         │
    └───────────────────┘
            │
            ▼
    ┌───────────────────┐
    │  ARBITER           │
    │  (disputes only)   │
    │                    │
    │ Kahneman protocol: │
    │ 1. Both sides pre- │
    │    register what   │
    │    evidence would  │
    │    resolve it      │
    │ 2. Arbiter designs │
    │    the test        │
    │ 3. Test runs       │
    │ 4. Result is       │
    │    binding         │
    └───────────────────┘
            │
            ▼
    Bead updated with
    hardening changes +
    adversarial report
    Status → hardened
```

---

## 6. Output Formats

### 6.1 Red Team Finding

```markdown
## Finding: {ID}
**Domain:** functionality | security | usability | resilience
**Severity:** critical | high | medium | low
**Claim:** {One sentence: what is wrong}
**Minimal reproduction:** {The smallest possible demonstration}
**Impact:** {What goes wrong if unaddressed}
**Evidence:** {file:line, guppy output, or test result}
**Confidence:** Verified | Likely | Assumed
```

If a red team agent cannot fill in `Minimal reproduction`, the finding is automatically downgraded to `Assumed` confidence and the blue team can dismiss it without rebuttal.

### 6.2 Blue Team Response

```markdown
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

### 6.3 Arbiter Verdict

```markdown
## Verdict: {Finding ID}
**Decision:** SUSTAINED | DISMISSED | MODIFIED
**Red team claim:** {summary}
**Blue team position:** {summary}
**Test designed:** {description of the fair test}
**Test result:** {observable evidence}
**Reasoning:** {why this evidence resolves the dispute}
**If MODIFIED:** {adjusted scope/severity}
```

### 6.4 Adversarial Quality Report (per bead)

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
- {any findings that could not be fully resolved, or "None"}

### Verdict
> **[HARDENED | PARTIALLY_HARDENED | DEFERRED]**
```

---

## 7. Integration with SDLC OS

### 7.1 Phase Integration

AQS lives inside the Execute phase as a continuous shadow:

```
Execute Phase
│
├── Bead dispatched to Runner (sonnet-implementer)
│   └── Runner completes → L0 self-check → submits
│
├── Sentinel checks bead (haiku-verifier)
│   └── Pass → bead marked "verified"
│
├── Oracle audits (unchanged)
│   └── Test integrity + behavioral proof
│
├── ★ AQS ACTIVATES ★
│   └── Full adversarial cycle (Section 5)
│   └── Bead marked "hardened"
│
└── Bead proceeds to Synthesize
```

### 7.2 Bead Status Extension

New status `hardened` in the canonical bead flow. The full status chain (updated post-implementation to reflect Oracle's `proven` status):

```
pending → running → submitted → verified (L1 Sentinel) → proven (L2 Oracle) → hardened (L2.5 AQS) → merged
```

For trivial tasks that skip AQS, beads go `proven → merged` directly.

> **Note:** The original spec draft used `verified → hardened → merged`. During implementation, the existing `proven` status (from Oracle L2) was discovered between `verified` and `hardened`. The canonical flow above reflects the implemented system.

### 7.3 Loop Integration

AQS inserts at **L2.5** in the existing loop hierarchy:

- **L0 (Runner):** Unchanged
- **L1 (Sentinel):** Unchanged
- **L2 (Oracle):** Unchanged
- **L2.5 (AQS):** Adversarial quality cycle. Budget: 2 full cycles per bead.
  - Cycle 1: Red team attacks → blue team responds → fixes applied
  - Cycle 2 (if Cycle 1 produced fixes): Red team re-attacks fixed code
  - If Cycle 1 produces no findings, AQS completes immediately
  - Budget exhausted → escalate to Conductor with adversarial report
- **L3-L5:** Unchanged

### 7.4 Artifact Persistence

```
docs/sdlc/active/{task-id}/
├── beads/
│   ├── {bead-id}.md           ← existing bead file
│   └── {bead-id}-aqs.md      ← adversarial quality report
└── adversarial/
    ├── recon-{bead-id}.md     ← recon burst results
    ├── findings-{bead-id}.md  ← all red team findings
    ├── responses-{bead-id}.md ← all blue team responses
    └── verdicts-{bead-id}.md  ← arbiter verdicts (if any)
```

### 7.5 Handoff Contract Addition

Existing handoff template gets one new section:

```markdown
**Adversarial quality:** [summary of AQS engagement — domains tested,
findings accepted/rebutted/disputed, hardening changes applied,
residual risk if any]
```

### 7.6 Conductor Orchestration Updates

The `sdlc-orchestrate` skill needs additions for:

1. **Complexity assessment** — extended with AQS activation criteria
2. **Domain selection heuristic** — rules for which domains to activate:
   - Bead touches external input → security
   - Bead creates/modifies user-facing interface → usability
   - Bead implements business logic → functionality
   - Bead touches error handling, I/O, or external services → resilience
3. **Cross-reference logic** — combining Conductor selection with recon signals
4. **AQS budget management** — tracking cycle count, guppy volume, arbiter invocations

### 7.7 Complexity Scaling

| Complexity | AQS Behavior |
|---|---|
| **Trivial** | Skip entirely. Beads go `verified → merged`. |
| **Moderate** | Recon burst fires. Conductor selects 1-2 domains. Only HIGH/MED priority domains get full strike. |
| **Complex** | All four domains active. Full strike on HIGH/MED. Light sweep on LOW. Cycle 2 mandatory if Cycle 1 produced fixes. |
| **Security-sensitive** | All four domains active regardless of complexity. Security domain always HIGH priority. Cycle 2 mandatory. |

---

## 8. New Files

### 8.1 Agents (9 new files)

```
agents/
├── red-functionality.md
├── red-security.md
├── red-usability.md
├── red-resilience.md
├── blue-functionality.md
├── blue-security.md
├── blue-usability.md
├── blue-resilience.md
└── arbiter.md
```

### 8.2 Skill (5 new files)

```
skills/sdlc-adversarial/
├── SKILL.md                    ← Main orchestration logic
├── domain-attack-libraries.md  ← Attack vectors per domain
├── recon-directives.md         ← Guppy prompt templates for recon
├── arbitration-protocol.md     ← Full Kahneman protocol details
└── scaling-heuristics.md       ← Complexity/domain selection rules
```

### 8.3 Command (1 new file)

```
commands/
└── adversarial.md
```

### 8.4 Reference (1 new file)

```
references/
└── adversarial-quality.md
```

### 8.5 Modifications to Existing Files

- `skills/sdlc-orchestrate/SKILL.md` — Add AQS activation logic, domain selection heuristics, L2.5 loop description
- `skills/sdlc-orchestrate/wave-definitions.md` — Add `hardened` bead status, AQS section within Execute phase
- `skills/sdlc-orchestrate/handoff-contract.md` — Add adversarial quality section to template
- `references/artifact-templates.md` — Add finding, response, verdict, and AQS report templates

---

## 9. Anti-Patterns to Guard Against

Based on research, the following failure modes must be structurally prevented:

| Anti-Pattern | Prevention Mechanism |
|---|---|
| Role-played criticism (weak assigned dissent) | Structural independence — red team has never seen the code before, has no dependency on builder |
| Volume gaming (reporting trivial issues as critical) | Mandatory shrinking — no reproduction = downgraded confidence. Steep severity gradient discourages noise. |
| Rubber-stamping (blue team accepts without fixing) | Blue team constraint: "acknowledged" is not a response — must produce fix or evidence-based rebuttal |
| Performative decay over time | Two independent review channels (Oracle + AQS). Cycle 2 re-attack verifies hardening is real. |
| Conductor bias in domain selection | Recon burst cross-references Conductor's judgment — catches blind spots |
| Dispute stalemate | Arbiter protocol with binding verdicts — disputes cannot remain open |
| Collusion between red and blue | Structural separation — different agents, different objectives, no shared context |
| Overwhelming trivial tasks | Complexity scaling — trivial tasks skip AQS entirely |
| Single-channel capture | AQS + Oracle operate independently on different failure modes |

---

## 10. Glossary

- **AQS** — Adversarial Quality System
- **Recon burst** — 8 haiku guppies (2 per domain) fired for broad signal detection
- **Strike swarm** — High-volume haiku guppies fired by a red team commander at specific attack vectors
- **Mandatory shrinking** — Requirement that every finding be reduced to minimal reproducing case
- **Kahneman protocol** — Adversarial collaboration dispute resolution: both sides pre-register resolution criteria, arbiter designs fair test, result is binding
- **Hardened** — Bead status indicating it has passed adversarial quality review
- **L2.5** — Loop level for AQS, between Oracle (L2) and Conductor escalation (L3)
- **Cross-reference** — Combining Conductor domain selection with recon guppy signals to determine strike priority
