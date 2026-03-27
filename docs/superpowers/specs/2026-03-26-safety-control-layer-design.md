# Safety Control Layer (Phase B) — Design Specification

**Date:** 2026-03-26
**Status:** Design Approved
**Scope:** System-level STPA control structure, 4 new agents, 15 safety mechanisms from Leveson/Reason/Dekker (L1-L5, R1-R5, D1-D5), bead field population, safety registries, process model layer. Builds on Phase A FFT backbone.
**Depends on:** Phase A (FFT Decision Architecture, v6.0.0)

---

## Overview

Phase B adds a safety control layer grounded in three complementary accident models:

- **Leveson (STAMP/STPA):** Safety is a control problem. Enumerate control actions and unsafe control actions systematically. Model the system as a control structure with controllers, actuators, controlled processes, and sensors.
- **Reason (Swiss Cheese):** Defenses have holes. Track latent conditions that enlarge holes. Maintain a resident pathogen registry. Monitor production/protection balance.
- **Dekker (Drift Into Failure):** Systems drift into failure through locally rational decisions. Monitor normalization of deviance. Capture successful adaptations (Safety-II). Sunset stale precedents.

Together they address: what controls are inadequate (Leveson), where defense holes are accumulating (Reason), and whether the process itself is drifting (Dekker).

### What Each Framework Catches That the Others Miss

| Framework | Catches | Blind Spot |
|---|---|---|
| Leveson (STPA) | Proactive hazards from inadequate control — catches problems BEFORE they manifest | Does not track how past failures accumulated or whether process standards are drifting |
| Reason (Swiss Cheese) | Retrospective tracing from active failure to latent condition — catches WHY defenses failed | Does not systematically enumerate future hazards; reactive to findings |
| Dekker (Drift) | Process-level trend analysis — catches gradual erosion invisible to point-in-time checks | Does not model control structure or trace specific failure paths |

All three are needed. STPA looks forward (what could go wrong), Swiss Cheese looks backward (why did it go wrong), Drift looks sideways (is the process eroding).

---

## Section 1: STPA Control Structure Model

The SDLC-OS is modeled as a STAMP control structure with 5 layers: external governance, primary controller, subcontrollers, actuators/guards, and controlled processes. Sensors provide feedback. Each controller maintains a process model.

### 1.1 Control Structure Map

```
EXTERNAL GOVERNANCE
┌──────────────────────────────────────────────────────────────┐
│  User                                                        │
│  Task requests, approvals, overrides, /evolve                │
│  Process model: intent, priorities, quality expectations      │
└──────────────────────────┬───────────────────────────────────┘
                           │ Interface 1
PRIMARY CONTROLLER         ▼
┌──────────────────────────────────────────────────────────────┐
│  Conductor (Opus)                                            │
│  FFT routing, bead dispatch, synthesis, escalation           │
│  Process model: task intent, bead graph, FFT decisions,      │
│    quality budget, active profiles, Cynefin assignments      │
└──┬──────────┬──────────┬──────────┬──────────────────────────┘
   │          │          │          │
   │ Interface 2 (Conductor → Subcontrollers)
   ▼          ▼          ▼          ▼
SUBCONTROLLERS
┌────────┐ ┌──────────┐ ┌───────────┐ ┌──────────────────────┐
│Delivery│ │Adversarl │ │Reliability│ │Safety                │
│        │ │          │ │           │ │                      │
│runners │ │red cmds  │ │reliability│ │safety-analyst        │
│(Sonnet)│ │blue defs │ │-conductor │ │safety-constraints-   │
│        │ │arbiter   │ │(Sonnet)   │ │  guardian             │
│        │ │(Son/Opus)│ │           │ │process-drift-monitor │
│        │ │          │ │           │ │latent-condition-     │
│        │ │          │ │           │ │  tracer              │
│        │ │          │ │           │ │(Haiku/Sonnet)        │
├────────┤ ├──────────┤ ├───────────┤ ├──────────────────────┤
│Process │ │Process   │ │Process    │ │Process model:        │
│model:  │ │model:    │ │model:     │ │constraints registry, │
│bead    │ │active    │ │observ.    │ │resident pathogen     │
│spec,   │ │domains,  │ │profile,   │ │registry, channel     │
│context │ │precedent │ │hardening  │ │health model,         │
│packet, │ │context,  │ │state,     │ │deviance baselines,   │
│reuse   │ │expected  │ │premortem  │ │UCA catalog           │
│report  │ │attack    │ │gaps       │ │                      │
│        │ │surface   │ │           │ │                      │
└───┬────┘ └───┬──────┘ └────┬──────┘ └──────┬───────────────┘
    │          │             │               │
    │ Interface 3 (Subcontrollers → Actuators/Guards)
    ▼          ▼             ▼               ▼
ACTUATORS
┌──────────────────────────────────────────────────────────────┐
│  Write/Edit/Bash, deterministic scripts (FFT-08),            │
│  guppy probes, artifact writes                               │
└──────────────────────────┬───────────────────────────────────┘
                           │
GUARDS (can block or redirect — not pure sensors)              │
┌──────────────────────────────────────────────────────────────┐
│  Hook validators: guard-bead-status, validate-decision-trace,│
│  validate-hardening-report, validate-aqs-artifact,           │
│  lint-domain-vocabulary, check-naming-convention,             │
│  validate-consistency-artifacts, validate-runner-output       │
│  Deterministic checks: type-check, lint, test suite,         │
│  schema validation, secret scan (from FFT-08 catalog)        │
└──────────────────────────┬───────────────────────────────────┘
                           │ Interface 4 (Actuators/Guards → Controlled Processes)
                           ▼
CONTROLLED PROCESSES
┌──────────────────────────┬───────────────────────────────────┐
│  Product/Code            │  Orchestration/State              │
│  source files            │  beads + decision traces          │
│  tests                   │  quality budget                   │
│  configs                 │  precedent DB                     │
│  APIs                    │  code constitution                │
│  dependencies            │  convention map                   │
│                          │  safety registries (NEW)          │
│                          │  resident pathogen registry (NEW) │
└──────────────────────────┴───────────────────────────────────┘

SENSORS (feedback to Controllers)
┌────────┐┌──────┐┌────┐┌───────────┐
│Sentinel││Oracle││LOSA││Calibration│
│(Haiku) ││Councl││    ││Loop (L6)  │
└────────┘└──────┘└────┘└───────────┘

TELEMETRY ARTIFACTS (outputs of Safety subcontroller agents)
┌─────────────────┐┌──────────────────┐┌─────────────────────┐
│Drift reports    ││Latent trace      ││Feedback channel     │
│(from process-   ││reports (from     ││health alerts (from  │
│drift-monitor)   ││latent-condition- ││safety-analyst +     │
│                 ││tracer)           ││process-drift-monitor│
└─────────────────┘└──────────────────┘└─────────────────────┘

Interface 5: Sensors/Guards → Controllers
Interface 6: Calibration/Drift/Safety → Evolve/Conductor (meta-feedback)
```

### 1.2 The 6 STPA Interfaces

| # | Interface | Direction | What Flows | UCAs Analyzed |
|---|---|---|---|---|
| 1 | User → Conductor | Control | Task requests, approvals, overrides | Vague request, premature approval, missing override |
| 2 | Conductor → Subcontrollers | Control | Bead dispatch, context packets, FFT decisions | Missing context, wrong Cynefin, anti-anchoring violation, stale process model |
| 3 | Subcontrollers → Actuators/Guards | Control | Tool calls, guppy probes, artifact writes | Wrong file targeted, incomplete probe, guard bypassed |
| 4 | Actuators/Guards → Controlled Processes | Action | Code mutations, state mutations, artifact creation | Write to wrong file, state corruption, guard false-block, guard missed-block |
| 5 | Sensors/Guards → Controllers | Feedback | Findings, verifications, drift signals, block/redirect | Feedback not provided (silent sensor), feedback too late (Sterman delay), false clean report |
| 6 | Calibration/Drift/Safety → Evolve/Conductor | Meta-feedback | System health, deviance trends, reliability data, pathogen accumulation | Calibration delayed too long, deviance signal ignored, pathogen registry stale |

### 1.3 Process Models

Every controller maintains a process model — its understanding of the current state of what it controls. Unsafe control actions occur when the process model diverges from reality. Monitoring process model freshness is how STPA prevents accidents proactively.

| Controller | Process Model Contents | Staleness Risk |
|---|---|---|
| Conductor | Task intent, bead graph, FFT decisions, quality budget, active profiles | Intent drift if user changes mind mid-task; budget stale if not refreshed between beads |
| Delivery (runners) | Bead spec, context packet, reuse report | Context packet missing recent changes from parallel beads |
| Adversarial (red/blue) | Active domains, precedent context, expected attack surface | Precedent DB stale, attack library outdated, domain priorities from stale recon |
| Reliability | Observability profile, hardening state, premortem gaps | Observability profile from project scan may miss runtime-only frameworks |
| Safety | Constraints registry, resident pathogen registry, channel health model, deviance baselines, UCA catalog | Constraints not updated after architecture changes; baselines from different project phase |

The safety-analyst agent checks process model freshness at the start of every Phase 3 (Architect) for the Conductor's model, and the process-drift-monitor checks all models during Evolve cycles.

---

## Section 2: The 15 Safety Mechanisms

All 15 mechanisms from the safety science research (L1-L5, R1-R5, D1-D5), grouped by framework, with implementation details.

### STPA Skip Rule (canonical — referenced by all mechanisms)

STPA analysis and safety constraint enforcement apply when ANY of:
- `cynefin == COMPLEX`
- `security_sensitive == true`

STPA is skipped when BOTH of:
- `cynefin != COMPLEX` (i.e., CLEAR or COMPLICATED)
- AND `security_sensitive == false`

Note: `complexity_source` (ESSENTIAL/ACCIDENTAL) does NOT independently trigger STPA. It governs AQS scrutiny depth (FFT-10/FFT-11) but not safety analysis. A COMPLICATED+ESSENTIAL bead gets full AQS but no STPA — STPA's systematic enumeration is justified only by the emergent-interaction risks of COMPLEX beads or the attack surface of security-sensitive beads.

ACCIDENTAL beads that are security-sensitive still get full STPA — security_sensitive overrides everything. This mirrors the FFT-10 correction from Phase A.

### Leveson Mechanisms (STPA)

**L1. STPA Check During Bead Decomposition**
- **Trigger:** Phase 3 (Architect) for BUILD profile; **pre-Execute** for REPAIR profile (which skips Architect). When the REPAIR profile creates beads directly, the safety-analyst runs on those beads before runners are dispatched — effectively an inline mini-Architect step for safety analysis only.
- **Agent:** safety-analyst (Sonnet)
- **Protocol:**
  1. For each bead, enumerate control actions (API calls, state transitions, auth checks, data writes, external calls)
  2. For each control action, derive UCAs in 4 categories:
     - Not provided when needed (missing validation, absent auth check)
     - Provided when not needed (redundant write, unnecessary lock)
     - Wrong timing or order (race condition, out-of-sequence transition)
     - Stopped too soon or applied too long (premature timeout, held lock)
  3. UCAs populate the bead's `unsafe_control_actions` field
  4. UCAs become automatic Red Team probe targets — systematic, not heuristic
- **Output:** `control_actions` and `unsafe_control_actions` fields on each bead
- **Skip for:** Beads where the STPA skip rule evaluates to "skip" (not COMPLEX AND not security_sensitive)

**L2. Process Model Consistency Audit**
- **Trigger:** Every Evolve cycle
- **Agent:** process-drift-monitor (Haiku)
- **Protocol:**
  1. For each controller in the STPA map, check: does the controller's process model match the current state of what it controls?
  2. Conductor: are FFT decisions consistent with current quality budget? Are Cynefin assignments still valid given code changes?
  3. Adversarial: does the precedent DB reflect current architecture? Are domain attack libraries current?
  4. Reliability: does the observability profile match the actual tech stack?
  5. Safety: are safety constraints still architecturally valid?
- **Output:** Process model freshness report with staleness flags

**L3. Feedback Channel Health Monitor**
- **Trigger:** Every Evolve cycle + after any L3+ escalation
- **Agent:** safety-analyst (Sonnet)
- **Protocol:**
  1. For each sensor/guard in the STPA map, check: is it functioning?
  2. Sentinel: are sentinel dispatches producing findings proportional to bead complexity? (Zero findings on Complex beads = potential sensor failure)
  3. Oracle: are VORP checks catching claim types they historically catch? Declining catch rate = sensor degradation
  4. Hooks: are blocking hooks actually blocking? Since Claude Code does not persist hook execution telemetry natively, the safety-analyst infers hook health indirectly: dispatch a guppy to attempt a known-invalid write (e.g., a bead with missing Profile field) and verify the hook blocks it. This is a probe-based health check, not a log-based one. If Claude Code adds hook telemetry in the future, this mechanism should switch to log-based.
  5. LOSA: is sampling rate matching the configured cadence?
  6. Deterministic checks: are all catalog entries still executable? (Dependency changes may break scripts)
- **Output:** Feedback channel health report — GREEN/YELLOW/RED per channel
- **New SLI:** Feedback channel health added to quality-slos.md

**L4. Bead Boundary Integration Constraints**
- **Trigger:** Phase 3 (Architect) for BUILD; pre-Execute for REPAIR (same attachment as L1). Only fires when the bead manifest has dependent beads.
- **Agent:** safety-analyst (Sonnet)
- **Protocol:**
  1. For each dependency edge in the bead graph, identify what crosses the boundary (data format, state assumption, API contract)
  2. Derive integration UCAs: what if the upstream bead's output doesn't match what the downstream bead expects?
  3. Add integration constraints to both beads: upstream bead's output must satisfy constraint X; downstream bead must validate constraint X on input
- **Output:** Integration constraints added to bead `control_actions` field

**L5. Safety Constraints Registry**
- **Location:** `references/safety-constraints.md` (NEW)
- **Agent:** safety-constraints-guardian (Sonnet) maintains the registry
- **Contents:** Invariants that must hold across all beads:
  - Auth checks must precede data access
  - All external calls must have explicit timeouts
  - User input must be validated before reaching business logic
  - Database transactions must have rollback paths
  - Error handlers must not swallow errors silently
  - Secrets must not appear in logs or error messages
  - (Project-specific constraints added during Scout phase)
- **Enforcement:** safety-constraints-guardian validates bead outputs against the registry during L1 sentinel loop. Violations are BLOCKING.

### Reason Mechanisms (Swiss Cheese)

**R1. Latent Condition Trace on Findings**
- **Trigger:** Every accepted finding (AQS or Phase 4.5)
- **Agent:** latent-condition-tracer (Haiku)
- **Protocol:**
  1. For each accepted finding, trace backward: which upstream layer should have caught this?
  2. Classify the latent condition:
     - L0 Runner: prompt gap, spec ambiguity, missing context
     - L1 Sentinel: drift-detector blind spot, convention gap
     - L2 Oracle: VORP check missed this claim type
     - L2.5 AQS: attack library gap, domain selection miss
     - L2.75 Hardening: observability gap, error handling gap
     - Convention Map: unmapped pattern
     - Code Constitution: missing rule
     - Safety Constraints: missing constraint
     - Hook/Guard: validator didn't catch this pattern
  3. Populate bead `latent_condition_trace` field
  4. Update Resident Pathogen Registry
- **Output:** Per-finding latent condition classification + registry update

**R2. Resident Pathogen Registry**
- **Location:** `docs/sdlc/resident-pathogens.md` (NEW, persistent across tasks)
- **Agent:** latent-condition-tracer (Haiku) maintains the registry
- **Contents:** Cross-task accumulation of latent conditions grouped by upstream layer:
  ```
  | Layer | Pathogen Type | Count | Last Seen | Trend |
  |-------|--------------|-------|-----------|-------|
  | L0 Runner | Missing error handling context in prompts | 7 | task-42 | GROWING |
  | L2.5 AQS | Security domain attack library missing CORS probes | 3 | task-38 | STABLE |
  | Convention Map | No convention for retry patterns | 4 | task-40 | GROWING |
  ```
- **Evolve integration:** GROWING pathogens automatically generate Evolve beads — auto-rule generation targets the layer with the most pathogens

**R3. Protection Erosion Monitor**
- **Trigger:** Every Evolve cycle
- **Agent:** process-drift-monitor (Haiku)
- **Protocol:**
  1. Track the ratio of production work (beads implementing features) to protection work (beads improving quality infrastructure)
  2. Healthy ratio: at least 20% protection (Yegge's 40% is aspirational; 20% is minimum)
  3. If protection ratio drops below 20% for 3 consecutive tasks: alert
  4. Track per-layer: is any defensive layer getting less maintenance attention than others?
- **Output:** Protection erosion metric in system health report

**R4. Just Culture Classification for Agents**
- **Trigger:** Every L3+ escalation
- **Agent:** latent-condition-tracer (Haiku)
- **Protocol:** Classify each agent failure using Reason's three categories:
  - **Error** (stochastic LLM failure — normal variation): Retry. Do not adjust prompts.
  - **At-Risk** (pattern of shortcuts — prompt/convention gap): Update the context that produced the behavior.
  - **Reckless** (systematic circumvention — agent gaming or structural misdesign): Replace the configuration.
- **Output:** Classification guides whether the Evolve response is retry, context fix, or redesign
- **Anti-pattern guard:** Tampering (Deming) — do not treat Error as At-Risk. Only sustained patterns warrant context changes.

**R5. Safety Culture Components Check**
- **Trigger:** Every 10th task (periodic health check)
- **Agent:** process-drift-monitor (Haiku)
- **Protocol:** Verify Reason's 5 safety culture components:
  1. Informed: are fitness functions covering all quality dimensions?
  2. Reporting: are agents surfacing findings in structured format?
  3. Just: are failures traced to system factors, not individual agents?
  4. Learning: has the Code Constitution grown in the last 10 tasks?
  5. Flexible: is Cynefin scaling actually producing different process depths?
- **Output:** Safety culture health score (5 dimensions)

### Dekker Mechanisms (Drift Into Failure)

**D1. Deviance Normalization Monitor**
- **Trigger:** Every Evolve cycle
- **Agent:** process-drift-monitor (Haiku)
- **Protocol:** (as defined in Phase A spec Section 6.3, now with full implementation)
  1. Compute from decision traces over rolling 10-task window:
     - Clear classification rate
     - Fast-track resolution rate
     - Average loop depth
     - Scrutiny skip rate (FFT-09 SKIP frequency)
     - Budget "healthy" duration
  2. Co-trending of 3+ indicators in deviance direction → system-level alert
  3. Alert names the normalization pattern, requires Conductor acknowledgment
- **Integration:** Feeds into Evolve cycle as a mandatory check

**D2. Verification Depth Assessment**
- **Trigger:** Every Evolve cycle
- **Agent:** process-drift-monitor (Haiku)
- **Protocol:**
  1. Compare verification depth (how thoroughly each loop level examines beads) against historical baselines
  2. Detect ritualistic compliance: sentinel checks that always pass, oracle audits with identical boilerplate responses, AQS cycles that converge in exactly one round every time
  3. Ritualistic patterns signal that verification has become performative rather than substantive
- **Output:** Verification depth score — SUBSTANTIVE/RITUALISTIC per loop level

**D3. Precedent Sunset Protocol**
- **Trigger:** Every Evolve cycle
- **Agent:** latent-condition-tracer (Haiku)
- **Protocol:**
  1. For each precedent in the precedent DB, check: when was it last relevant?
  2. Precedents unused for 20+ tasks: flag as potentially stale
  3. Precedents that conflict with newer architecture: flag for retirement
  4. Precedents from before a major refactoring: flag for review
  5. Apply Lindy-weighted trust (Taleb): old validated precedents get longer runway; new precedents get shorter
- **Output:** Precedent health report — active/stale/conflicting/retired

**D4. Work-as-Done vs Work-as-Prescribed Audit**
- **Trigger:** Every 5th task
- **Agent:** process-drift-monitor (Haiku)
- **Protocol:**
  1. Compare what the decision traces say happened (work-as-done) against what the skills prescribe (work-as-prescribed)
  2. Detect systematic deviations: phases that are always skipped even when prescribed, FFT cues that are never checked, fields that are always empty
  3. Deviations may be rational (the prescription is wrong) or drift (the prescription is right but not followed)
  4. For rational deviations: recommend updating the prescription
  5. For drift deviations: recommend enforcement or investigation
- **Output:** Work-as-done delta report

**D5. Safety-II Success Library**
- **Trigger:** Every LOSA observation
- **Agent:** LOSA Observer (existing, extended)
- **Protocol:**
  1. In addition to looking for defects, LOSA captures successful adaptations: cases where agents correctly handled ambiguity, novel situations, or conflicting requirements
  2. Successful adaptations are logged in a Success Library
  3. The Success Library is the positive reference: "what does good look like?"
  4. Used during Evolve cycles to reinforce effective patterns, not just fix broken ones
- **Output:** Success entries in `docs/sdlc/success-library.md` (NEW)

---

## Section 3: The 4 New Agents

### Agent 1: safety-analyst

```
---
name: safety-analyst
description: "Performs STPA analysis during Phase 3 — enumerates control actions and unsafe control actions for Complex/security-sensitive beads, checks bead boundary integration constraints, and monitors feedback channel health. Produces control_actions and unsafe_control_actions bead fields."
model: sonnet
---
```

**Responsibilities:**
- L1: STPA check during bead decomposition (Phase 3)
- L3: Feedback channel health monitor (Evolve + post-escalation)
- L4: Bead boundary integration constraints (Phase 3)
- System-level STPA on the 6 interfaces (periodic, during Evolve)

**Dispatched by:** Conductor during Phase 3 (for COMPLEX/security-sensitive beads) and during Evolve cycles

### Agent 2: latent-condition-tracer

```
---
name: latent-condition-tracer
description: "Traces accepted findings backward through loop layers to identify which upstream defense had the hole. Maintains the Resident Pathogen Registry. Classifies agent failures using Reason Just Culture categories. Runs Dekker precedent sunset protocol."
model: haiku
---
```

**Responsibilities:**
- R1: Latent condition trace on every accepted finding
- R2: Resident Pathogen Registry maintenance
- R4: Just Culture classification for agent failures
- D3: Precedent sunset protocol

**Dispatched by:** Conductor after every accepted AQS/Phase 4.5 finding, and during Evolve cycles

### Agent 3: process-drift-monitor

```
---
name: process-drift-monitor
description: "Monitors normalization of deviance, verification depth degradation, protection erosion, process model staleness, and work-as-done vs work-as-prescribed drift. Computes safety culture health scores. Produces deviance alerts from decision trace trend analysis."
model: haiku
---
```

**Responsibilities:**
- D1: Deviance normalization monitor
- D2: Verification depth assessment
- D4: Work-as-done vs work-as-prescribed audit
- R3: Protection erosion monitor
- R5: Safety culture components check
- L2: Process model consistency audit

**Dispatched by:** Conductor during Evolve cycles and every 5th/10th task for periodic checks

### Agent 4: safety-constraints-guardian

```
---
name: safety-constraints-guardian
description: "Maintains the Safety Constraints Registry — system-wide invariants that must hold across all beads. Validates bead outputs against constraints during L1 sentinel loop. Discovers new constraints during Scout phase from codebase analysis."
model: sonnet
---
```

**Responsibilities:**
- L5: Safety Constraints Registry maintenance and enforcement
- Constraint discovery during Phase 2 (Scout) — analyze codebase for implicit invariants
- Constraint validation during L1 sentinel — check bead outputs against registry

**Dispatched by:** Sentinel during L1 (for validation), Conductor during Scout (for discovery)

---

## Section 4: Bead Field Population

Phase A defined placeholder fields. Phase B populates them:

| Field | Populated By | When | Content |
|---|---|---|---|
| `control_actions` | safety-analyst | Phase 3 for BUILD; pre-Execute for REPAIR (COMPLEX/security-sensitive beads) | List of control actions this bead performs |
| `unsafe_control_actions` | safety-analyst | Phase 3 for BUILD; pre-Execute for REPAIR (COMPLEX/security-sensitive beads) | 4-category UCA enumeration per control action |
| `latent_condition_trace` | latent-condition-tracer | After accepted finding | Which upstream layer had the hole |

For beads where the STPA skip rule evaluates to "skip" (not COMPLEX AND not security_sensitive), these fields remain empty.

---

## Section 5: New Artifacts

### 5.1 Safety Constraints Registry
**Location:** `references/safety-constraints.md`
**Format:**
```markdown
# Safety Constraints Registry

System-wide invariants maintained by safety-constraints-guardian.
Violations are BLOCKING during L1 sentinel.

## Universal Constraints (apply to all beads)
- SC-001: Auth checks must precede data access
- SC-002: All external calls must have explicit timeouts
- SC-003: User input must be validated before reaching business logic
- SC-004: Error handlers must not swallow errors silently
- SC-005: Secrets must not appear in logs or error messages

## Project-Specific Constraints (discovered during Scout)
{populated per project}

## Constraint Lifecycle
- ACTIVE: enforced during L1
- SUSPENDED: temporarily disabled with documented reason
- RETIRED: no longer applicable, with retirement rationale
```

### 5.2 Resident Pathogen Registry
**Location:** `docs/sdlc/resident-pathogens.md`
**Persistent across tasks.** Updated by latent-condition-tracer.

### 5.3 Success Library
**Location:** `docs/sdlc/success-library.md`
**Updated by LOSA Observer.** Positive reference for effective patterns.

### 5.4 STPA Control Structure Reference
**Location:** `references/stpa-control-structure.md`
**The control structure map from Section 1 as a standalone reference for agent consumption.**

---

## Section 6: Integration Points

### With Phase A (FFT Backbone)

- FFT-02 (Cynefin) determines which beads get STPA analysis: COMPLEX + security_sensitive
- FFT-10 (Complexity Source) determines which beads skip STPA: ACCIDENTAL (non-security)
- Decision traces are the primary data source for deviance normalization (D1), work-as-done audit (D4), and verification depth assessment (D2)
- Evolve profile dispatches process-drift-monitor and latent-condition-tracer during evolution beads

### With Existing Agents

- **Sentinel (L1):** safety-constraints-guardian validates alongside existing drift-detector and convention-enforcer
- **LOSA Observer:** extended with Safety-II success capture (D5)
- **Blue Team agents:** response format extended with `Latent condition` field for R1
- **Red Team agents:** receive UCA list from safety-analyst as probe targets (replaces heuristic attack selection for COMPLEX beads)
- **Evolve skill:** expanded with 9 new evolution bead types from safety mechanisms (D1-D5, R3, R5, L2, L3)

### With Phase C (Future — Reliability Telemetry)

- Feedback channel health (L3) provides sensor reliability data for March of Nines
- Resident pathogen trends feed into common/special cause classification
- Protection erosion ratio feeds into quality budget velocity tracking

---

## Section 7: Hook Updates

### Updated Hook: validate-decision-trace.sh

Add Phase B field enforcement. When a bead's STPA skip rule evaluates to "apply" (COMPLEX or security_sensitive, per the canonical rule), the hook validates:

- `control_actions` field is non-empty (must contain at least one control action)
- `unsafe_control_actions` field is non-empty (must contain at least one UCA)

This check fires when the bead transitions past `submitted` (the safety-analyst runs during Phase 3, so fields should be populated before runners execute).

For beads where STPA is skipped, these fields may remain empty — the hook checks the skip rule using the bead's `Cynefin domain`, `Security sensitive`, and `Complexity source` fields.

For `latent_condition_trace`: this field is populated after findings are accepted, not during Phase 3. The hook does NOT enforce its presence — it is populated asynchronously by the latent-condition-tracer agent. Enforcement is via the Evolve cycle's resident pathogen check: if accepted findings exist without traces, the Evolve cycle flags it.

### Updated Hook: hooks.json

Register the expanded validate-decision-trace.sh (no new hook file needed — same hook, additional validation logic).

### New Validation: safety-constraints check

Not a separate hook — the safety-constraints-guardian agent runs during L1 sentinel alongside existing agents. Blocking violations produce the same L1 correction signal as drift-detector violations.

### Universal Constraints on L0-Only Paths

**Problem:** CLEAR beads with healthy budget skip L1 entirely (FFT-05 Cue 1 → L0 only). This bypasses the safety-constraints-guardian, making "universal" constraints not actually universal.

**Solution:** Safety constraints that are deterministic (checkable by script, not requiring LLM reasoning) are enforced via hooks, not agents. Add a lightweight `validate-safety-constraints.sh` hook that runs on PostToolUse Write|Edit for source files. This hook checks the subset of constraints from `references/safety-constraints.md` that can be expressed as grep/AST patterns:

- SC-005: Secrets in logs (grep for common secret patterns near log statements)
- SC-004: Bare catch blocks (grep for empty catch/except blocks)

Constraints requiring LLM reasoning (SC-001 auth-before-data, SC-003 input-validation) can only be enforced during L1 by the safety-constraints-guardian agent. For L0-only beads, these constraints are checked post-merge by the LOSA observer's sampling — making them probabilistically enforced rather than universally enforced. The spec acknowledges this gap: L0-only beads accept the risk of missing LLM-only constraints in exchange for speed. The quality budget's healthy state is the precondition for this tradeoff.

**New hook file:** `hooks/scripts/validate-safety-constraints.sh` — lightweight deterministic constraint checks on source file writes.

**L0-only vs blocking mode:** The hook cannot determine bead context from a source-file write path alone (hooks receive file path + content, not bead metadata). Therefore: the hook runs in **advisory mode for all source-file writes** (exit 0 with stderr warning). It is always-on, always-advisory at the hook level.

The **blocking enforcement** happens at the agent level during L1: the safety-constraints-guardian **re-runs the same deterministic checks directly** on the bead's changed files (using the same grep/AST patterns as the hook), plus adds LLM-reasoning checks for constraints that require semantic analysis (SC-001 auth-before-data, SC-003 input-validation). The guardian does NOT consume hook output — it runs its own checks independently. This avoids any transport-path dependency between hooks and agents.

For L0-only beads (no L1 sentinel), the advisory hook warnings are visible in stderr during the runner's session but not blocking — the LOSA observer catches them probabilistically post-merge.

This is a clean separation: hooks provide early warning (always, advisory), agents provide enforcement with full context (when L1 is active). No hook needs bead-level context. No agent needs hook output.

---

## Section 8: Files Changed

### New Files
| File | Purpose |
|------|---------|
| `agents/safety-analyst.md` | STPA analysis, feedback channel health, bead boundary constraints |
| `agents/latent-condition-tracer.md` | Latent condition tracing, pathogen registry, just culture, precedent sunset |
| `agents/process-drift-monitor.md` | Deviance normalization, verification depth, protection erosion, process model audit |
| `agents/safety-constraints-guardian.md` | Constraints registry maintenance and L1 enforcement |
| `references/safety-constraints.md` | System-wide invariants registry |
| `references/stpa-control-structure.md` | Control structure map for agent consumption |
| `docs/sdlc/resident-pathogens.md` | Cross-task latent condition accumulation |
| `docs/sdlc/success-library.md` | Safety-II successful adaptation library |
| `hooks/scripts/validate-safety-constraints.sh` | Deterministic safety constraint checks on source file writes |

### Modified Files
| File | Changes |
|------|---------|
| `skills/sdlc-orchestrate/SKILL.md` | Add safety-analyst dispatch to Phase 3 (BUILD) and pre-Execute (REPAIR), safety-constraints-guardian to L1 and Phase 2 (Scout) for constraint discovery, Phase B agents to subcontroller references |
| `skills/sdlc-evolve/SKILL.md` | Add 9 new evolution bead types from safety mechanisms (D1-D5, R3, R5, L2, L3) |
| `skills/sdlc-loop/SKILL.md` | Add safety-constraints-guardian as L1 sentinel participant alongside haiku-verifier, drift-detector, convention-enforcer |
| `skills/sdlc-adversarial/SKILL.md` | Red Team receives UCA list for COMPLEX beads; Blue Team response format gains latent condition field |
| `agents/losa-observer.md` | Extended with Safety-II success capture (D5) |
| `agents/blue-functionality.md` | Add latent condition field to response format |
| `agents/blue-security.md` | Add latent condition field to response format |
| `agents/blue-usability.md` | Add latent condition field to response format |
| `agents/blue-resilience.md` | Add latent condition field to response format |
| `agents/blue-reliability-engineering.md` | Add latent condition field to response format |
| `references/quality-slos.md` | Add feedback channel health SLI |
| `hooks/scripts/validate-decision-trace.sh` | Add Phase B field enforcement (control_actions, unsafe_control_actions for STPA-required beads) |
| `hooks/hooks.json` | Register validate-safety-constraints.sh |
| `hooks/tests/test-hooks.sh` | Add test fixtures for validate-safety-constraints.sh and Phase B field validation in validate-decision-trace.sh |
| `.claude-plugin/plugin.json` | Bump version to 7.0.0 |

---

## Section 9: Implementation Sequence

1. Create `references/stpa-control-structure.md` (the control structure map)
2. Create `references/safety-constraints.md` (initial universal constraints)
3. Create `docs/sdlc/resident-pathogens.md` (empty initial registry)
4. Create `docs/sdlc/success-library.md` (empty initial library)
5. Create `agents/safety-analyst.md`
6. Create `agents/latent-condition-tracer.md`
7. Create `agents/process-drift-monitor.md`
8. Create `agents/safety-constraints-guardian.md`
9. Create `hooks/scripts/validate-safety-constraints.sh` + register in `hooks/hooks.json`
10. Update `hooks/scripts/validate-decision-trace.sh` (add Phase B field enforcement for STPA-required beads)
11. Update `skills/sdlc-orchestrate/SKILL.md` (Phase 3 STPA dispatch for BUILD, pre-Execute STPA for REPAIR, Phase 2 Scout constraint discovery, L1 constraints guardian)
12. Update `skills/sdlc-loop/SKILL.md` (add safety-constraints-guardian to L1 sentinel participant list)
13. Update `skills/sdlc-evolve/SKILL.md` (add 9 safety evolution bead types: D1-D5, R3, R5, L2, L3)
14. Update `skills/sdlc-adversarial/SKILL.md` (UCA list for Red Team, latent condition for Blue Team)
15. Update all 5 Blue Team agents (add latent condition field)
16. Update `agents/losa-observer.md` (Safety-II success capture)
17. Update `references/quality-slos.md` (add feedback channel health SLI)
18. Update `hooks/tests/test-hooks.sh` (add test fixtures for validate-safety-constraints.sh and Phase B field validation)
19. Bump `plugin.json` to 7.0.0
