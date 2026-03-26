# Reliability Engineering Hardening Phase (Phase 4.5)

**Date:** 2026-03-26
**Status:** Design Approved
**Scope:** New SDLC phase, 5 new agents, 1 new skill, 1 new hook

---

## Overview

Phase 4.5 (Harden) is a per-bead reliability engineering pass that instruments the user's project code with deep observability, exhaustive error handling, edge case coverage, circuit breakers, retry logic, and graceful degradation. It runs between Execute (Phase 4) and Synthesize (Phase 5), processing each bead individually after it reaches `hardened` status from AQS.

The phase is grounded in three intellectual traditions:

- **Kahneman** (error detection): System 1/2 dual-process scheduling, noise audits, WYSIATI coverage sweeps, premortem failure analysis, adversarial collaboration for Red/Blue disputes, reference class forecasting for scope estimation, Mediating Assessments Protocol for structured judgment
- **Karpathy** (verification): Every agent output is an unverified proposal (Software 3.0 reality), hypothesis-experiment-evidence loops, one-variable-at-a-time discipline, test-time compute scaling for risk-tiered verification, hard constraints that no agent can violate, earn trust incrementally, design for removal
- **Yegge** (operations): GUPP ("if there is work on your hook, YOU MUST RUN IT"), nondeterministic idempotence (chaotic paths converge on persistent acceptance criteria), Rule of Five (multi-pass review), 40% code health budget, colony thesis (specialized agents > one generalist), sequential merge via Refinery pattern, watchdog chain for health monitoring

---

## Bead Status Flow

```
pending -> running -> submitted -> verified -> proven -> hardened -> reliability-proven -> merged
                                                                        ^ new status
```

- `hardened` (existing): Bead passed AQS adversarial review across 4 domains
- `reliability-proven` (new): Bead passed reliability hardening -- observability instrumented, error paths hardened, Red Team findings resolved, deduplication clean

---

## Phase 4.5 Per-Bead Pipeline (7 Steps)

```
Step 0: Premortem (Kahneman/Klein)
        "This bead failed in production. Why?"
        3 independent haiku agents generate failure narratives
        Deduplicate -> priority gap list

Step 1: Pre-Clean (Yegge 40% health / sandwich bottom)
        /finding-duplicate-functions pipeline + /simplify review
        Parallel dispatch -- consolidate before instrumenting

Step 2: Observe (Karpathy hypothesis-experiment-evidence)
        Observability Engineer instruments logging, tracing, metrics
        Pattern-adherent to project's detected stack

Step 3: Harden (Kahneman MAP -- structured independent assessment)
        Error Hardener adds error handling, edge cases, circuit breakers,
        retries, graceful degradation, edge case tests
        Each dimension assessed independently before aggregation

Step 4: Probe (Kahneman adversarial / System 1->2 escalation)
        Reliability Red Team: 8 haiku guppy recon burst (System 1)
        -> sonnet directed strikes on findings (System 2)
        Raw bead code input -- no anchoring on Blue Team self-assessment

Step 5: Defend (Kahneman adversarial collaboration)
        Reliability Blue Team: accept+fix / rebut / dispute->Arbiter
        Joint report with Red Team -- disagreements are the valuable signal

Step 6: Post-Clean (sandwich top)
        /finding-duplicate-functions + /simplify again
        Catches hardening-induced duplication

Step 7: Report (Karpathy evidence ledger)
        Hardening report with evidence chain per finding
        WYSIATI coverage sweep -- flag unmentioned files as Unknown
```

### Correction Budget

2 cycles maximum (Karpathy test-time compute scaling -- trading compute for reliability). After Blue Team fixes, if Red Team re-probe finds critical issues, re-enter at Step 2. If still failing after 2 cycles, escalate to L3 with full evidence ledger.

### State Persistence (Yegge NDI)

Each step writes state to `docs/sdlc/active/{task-id}/beads/{bead-id}/reliability-state.json`:

```json
{
  "bead_id": "gt-abc12",
  "phase": "4.5",
  "current_step": 2,
  "completed_steps": [0, 1],
  "cycle": 1,
  "max_cycles": 2,
  "observability_profile": "docs/sdlc/active/.../observability-profile.md",
  "premortem_gaps": ["timeout on external API", "silent JWT expiry"],
  "pre_clean_report": { "duplicates_removed": 3, "simplifications": 7 }
}
```

If an agent crashes mid-step, the next session reads this state and resumes. The path is nondeterministic; the outcome converges because acceptance criteria are explicit and state is persistent.

---

## Agent 1: Reliability Conductor

**Model:** Sonnet (execution-tier runner)
**Identity:** Named, persistent per-task (Yegge Crew pattern)
**Tools:** All tools (dispatches agents, reads/writes artifacts, runs scripts)

### Responsibilities

#### 1. Observability Stack Detection

Before any instrumentation, analyzes the project to build an observability profile. This is the reference class (Kahneman) -- understanding what patterns exist so instrumentation is coherent.

Detects:
- **Logging:** Framework, structured vs unstructured, log levels, standard fields, output targets
- **Tracing:** Framework, span naming conventions, propagation headers, context injection patterns
- **Metrics:** Framework, naming conventions, label cardinality, histogram buckets
- **Error tracking:** Service, capture patterns, breadcrumb conventions
- **Resilience patterns:** Retry libraries, circuit breaker implementations, timeout conventions, degradation strategies

Written to `docs/sdlc/active/{task-id}/observability-profile.md`. Shared with all downstream agents as their anchoring document (Kahneman -- deliberately providing a correct anchor rather than letting agents form wrong ones).

#### 2. Premortem Orchestration (Kahneman/Klein)

Dispatches 3 independent haiku agents with identical prompt:

> "Bead {id} has been deployed to production. 90 days later, a severe incident occurred that the hardening phase failed to prevent. Write the postmortem: what happened, what was the root cause, and why did our instrumentation and error handling miss it?"

Each agent receives the bead's code but NOT each other's output (Kahneman independence requirement for noise reduction). The Conductor deduplicates failure modes. Modes appearing in 2+ narratives become priority targets for Steps 2-3.

This defeats the planning fallacy: instead of "what should we harden?" (optimistic), we ask "what will we fail to harden?" (loss-aversion frame).

#### 3. Sandwich Orchestration

Sequences the 7-step pipeline:

- **Steps 1 and 6 (pre/post clean):** `/finding-duplicate-functions` and `/simplify` dispatched in parallel (independent tasks)
- **Steps 2 and 3 (observe + harden):** Sequential. Observability first so error handlers can emit to the stack
- **Steps 4 and 5 (red + blue):** Sequential per AQS protocol
- **Handoff rule (Kahneman anti-anchoring):** Red Team receives raw bead code + observability profile, NOT the Observability Engineer's or Error Hardener's self-assessment

#### 4. Evidence Ledger (Karpathy)

Maintains a per-bead confidence ledger:

```
| Step | Hypothesis | Evidence | Confidence Update |
|------|-----------|----------|-------------------|
| Premortem | "External API timeout unhandled" | grep: no timeout in http calls | Unknown -> Likely |
| Observe | "Added 30s timeout + span" | span visible in test trace | Likely -> Verified |
| Harden | "Circuit breaker wraps API call" | test: breaker opens after 3 fails | Verified -> Verified |
| Red probe | "Breaker doesn't reset" | test: breaker stays open forever | Verified -> Defect |
| Blue fix | "Added half-open state 60s reset" | integration test: resets correctly | Defect -> Verified |
```

Confidence upgrades require new evidence, never argument (Karpathy principle).

#### 5. WYSIATI Sweep (Kahneman)

After all agents complete, builds a coverage matrix:
- Rows: every file and exported function in the bead
- Columns: mentioned by Observability Engineer? Error Hardener? Red Team? Blue Team?
- Any row with all blanks = WYSIATI gap -> flagged with `Unknown` confidence
- These gaps are the highest-priority items for review -- invisible to context-bounded agents

---

## Agent 2: Observability Engineer

**Model:** Sonnet (cross-file reasoning about instrumentation patterns)
**Identity:** Ephemeral per-bead (Yegge Polecat pattern)
**Tools:** Read, Write, Edit, Bash, Grep, Glob

### Input
Bead code + observability profile + premortem gap list

### Core Behavior: Hypothesis-Experiment-Evidence Per Function (Karpathy)

For each function/method:
1. **Hypothesis:** "This function needs {specific instrumentation}" -- based on what it does
2. **Experiment:** Add instrumentation following project patterns from the observability profile
3. **Evidence:** Verify instrumentation compiles, doesn't change behavior, follows conventions

### Instrumentation Taxonomy (Pattern-Adherent)

**Structured Logging** (using detected framework and conventions):
- Function entry with parameters (redacting sensitive fields per project patterns)
- Decision branches with the branch taken and why
- External call initiation and completion with latency
- Error paths with full error context chain
- Log levels match project conventions

**Tracing Spans** (if tracing framework detected):
- Span per public function / API handler / message consumer
- Span naming follows detected conventions
- Span attributes match project's attribute vocabulary
- Context propagation verified across async boundaries
- Parent-child span relationships correct

**Metrics** (if metrics framework detected):
- Counters: function invocations, errors by type, external call attempts/successes/failures
- Histograms: function latency, external call latency, queue depth
- Gauges: active connections, in-flight requests, circuit breaker state
- Naming and label conventions match existing metrics

### Hard Constraints (Karpathy -- Non-Negotiable Invariants)

- Instrumentation MUST NOT change function behavior (no side effects beyond observability)
- Instrumentation MUST NOT add dependencies not already in the project
- Instrumentation MUST NOT log sensitive data (PII, secrets, tokens)
- All added code MUST compile/pass type checking

### One Variable at a Time (Karpathy)

Each function instrumented as an atomic unit. If instrumentation breaks a test, the specific function's instrumentation is wrong -- not a cascading multi-file change.

---

## Agent 3: Error Hardener

**Model:** Sonnet (reasoning about failure modes, edge cases, system interactions)
**Identity:** Ephemeral per-bead (Polecat)
**Tools:** Read, Write, Edit, Bash, Grep, Glob

### Input
Bead code (post-observability instrumentation) + observability profile + premortem gap list

### Structured Judgment Protocol (Kahneman MAP)

For each function, assess dimensions independently before aggregating:

| Dimension | Assessment |
|---|---|
| **Uncaught paths** | Async operations without error handling? Promises without catch? Callbacks without error params? |
| **Error context** | Caught errors preserve original chain? Context attached? |
| **Error typing** | Bare `catch(e)` replaced with typed handling using project's error hierarchy? |
| **Timeout coverage** | Every external call has explicit timeout? |
| **Retry logic** | Transient failures retried with exponential backoff + jitter? Using project's retry library? |
| **Circuit breakers** | External dependencies wrapped in circuit breakers? |
| **Graceful degradation** | Dependency unavailable -> degrade gracefully rather than propagate? |
| **Silent failure detection** | Can this function fail without any caller knowing? |

Each dimension scored independently BEFORE overall judgment -- prevents halo effects.

### Edge Case Exploration

Per function, generates scenarios:
- **Empty/null inputs:** Empty collections, null/undefined parameters, zero-length strings
- **Boundary values:** Max int, empty arrays, single-element collections, off-by-one
- **Concurrent access:** Simultaneous calls from two threads/requests
- **Partial failures:** Operation succeeds partially (3 of 5 items written)
- **Resource exhaustion:** Low memory, full disk, exhausted connection pool
- **Clock skew / timing:** System clock jump, lease expiry mid-operation

For each scenario:
- Add defensive code (guard clause, validation, fallback), OR
- Generate a test case exercising the edge case, OR
- Document as known limitation with observability if fix is out of scope

### Reference Class Check (Kahneman)

Before adding a new pattern (e.g., circuit breaker), searches the codebase: has this pattern been used before? If yes, follow exactly. If no, flag as **new pattern introduction** in the hardening report.

### Karpathy "Don't Be a Hero"

Add the simplest defense that works. Circuit breakers use existing libraries, not hand-rolled implementations.

---

## Agent 4: Reliability Red Team

**Model:** Haiku swarms for recon + Sonnet for directed strikes (System 1/2 tiering)
**Identity:** Ephemeral swarm (Guppy pattern)
**Tools:** Read, Bash, Grep, Glob (read-only + test execution)

### Input
Raw bead code + observability profile (NOT the Observability Engineer's or Error Hardener's self-assessment -- Kahneman anti-anchoring)

### Phase 1: Recon Burst (System 1 -- Fast, Parallel)

8 haiku guppies, 2 per reliability domain:

| Domain | Guppy Focus |
|---|---|
| **Observability gaps** | Dark code paths without log/span? Error paths that don't emit? |
| **Error handling gaps** | Uncaught exceptions? Error handlers that throw? Bare catch blocks? Retries without backoff? |
| **Degradation gaps** | Dependency down -> what happens? Fallback exists? Circuit breaker opens? |
| **Edge case coverage** | Generated tests actually test edges? Boundary conditions not covered? Concurrent corruption? |

Each guppy tests exactly one thing (Karpathy one-variable-at-a-time). Each produces:
- Claim: what's wrong
- Evidence: reproducible proof
- Severity: CRITICAL / HIGH / MEDIUM / LOW

**Overfit-one-case gate (Karpathy):** Before scaling the swarm, commander verifies the most obvious probe works.

### Phase 2: Directed Strike (System 2 -- Focused, Deep)

Sonnet-class agents for deep probes:
- **Observability bypass:** Inject request, trace every hop, verify span continuity
- **Error handler torture:** Inject failures at every boundary. Do error handlers handle their own failures?
- **Circuit breaker verification:** Open breaker programmatically. Verify stops calls, half-open works, metrics emit
- **Degradation path testing:** Kill each dependency. Verify graceful degradation is observable

### Phase 3: Mandatory Shrinking

Every finding minimally reproduced -- strip irrelevant context. Prevents noise (Kahneman).

### Premortem Cross-Reference

Cross-reference findings against premortem gap list. Unprobed predictions become coverage gaps.

---

## Agent 5: Reliability Blue Team

**Model:** Sonnet (reasoning about fixes, trade-offs, rebuttals)
**Identity:** Ephemeral per-bead (Polecat)
**Tools:** Read, Write, Edit, Bash, Grep, Glob

### Input
Red Team findings + bead code + observability profile

### Response Protocol

For each finding:

**Accept + Fix:**
- Implement fix following project patterns
- Evidence the fix works (test passes, behavior demonstrated)
- Fix is unverified proposal (Karpathy) -- must pass hard constraints

**Rebut:**
- Evidence-based rebuttal (not argument -- evidence per Karpathy)
- Reproducible counter-evidence required

**Dispute -> Arbiter:**
- Existing Arbiter with Kahneman adversarial collaboration
- Both sides jointly design decisive test
- Pre-registered predictions
- Binding result enters precedent system (stare decisis)

### Joint Report (Kahneman)

Red and Blue jointly produce findings section: "we disagreed about Z, designed test T, ran it, learned W." Disagreement reveals the reliability boundary.

---

## Sandwich Integration (Simplify + Dedup)

### Pre-Clean (Step 1)

Run in parallel:

**Duplicate Detection** (`/finding-duplicate-functions` pipeline):
1. Extract function catalog from bead files
2. Categorize by domain (haiku)
3. Detect duplicates per category (opus for semantic comparison)
4. Consolidate duplicates BEFORE instrumentation

**Simplification** (`/simplify` pipeline):
1. Code reuse review -- existing utilities reimplemented?
2. Code quality review -- redundant state, parameter sprawl, copy-paste?
3. Efficiency review -- unnecessary work, missed concurrency, hot-path bloat?
4. Fix issues found

### Post-Clean (Step 6)

Same pipeline targeting hardening-induced duplication:
- Duplicate error handlers, logging patterns, retry wrappers?
- Overly verbose instrumentation?

Significant post-clean findings = feedback that agents are over-instrumenting (Karpathy design for removal).

---

## Hardening Report Format

Each bead produces `docs/sdlc/active/{task-id}/beads/{bead-id}/hardening-report.md`:

```markdown
# Hardening Report: {bead-id}

## Observability Profile
- Logging: {framework}, {pattern summary}
- Tracing: {framework}, {span convention}
- Metrics: {framework}, {naming convention}
- Error tracking: {service}

## Premortem Analysis
- Failure narratives generated: {N}
- Unique failure modes identified: {M}
- Priority gaps targeted: {list}

## Pre-Clean Results
- Duplicates consolidated: {count} functions -> {count} survivors
- Simplifications applied: {count}

## Instrumentation Summary
| File | Functions Instrumented | Spans Added | Metrics Added | Error Paths Hardened |
|------|----------------------|-------------|---------------|---------------------|

## Edge Case Tests Generated
- {count} new test cases across {count} files
- Coverage dimensions: {list}

## Red Team Findings
| ID | Domain | Severity | Claim | Evidence | Resolution |
|----|--------|----------|-------|----------|------------|

## Disputes & Arbitration
| Dispute | Red Position | Blue Position | Test Designed | Outcome | Precedent ID |
|---------|-------------|---------------|---------------|---------|--------------|

## Post-Clean Results
- Hardening-induced duplicates removed: {count}
- Simplifications applied: {count}

## WYSIATI Coverage Sweep
- Files in bead: {total}
- Files mentioned by >= 1 agent: {covered}
- WYSIATI gaps (0 mentions): {list with Unknown confidence}

## Evidence Ledger
| Hypothesis | Initial Confidence | Final Confidence | Evidence Chain |
|-----------|-------------------|-----------------|----------------|

## Verdict
- Status: reliability-proven | escalated
- Cycles used: {1|2} of 2
- Risk accepted: {any WYSIATI gaps or rebutted findings}
```

---

## Integration with Existing SDLC-OS

### Phase Integration

```
Phase 0: Normalize
Phase 1: Frame
Phase 2: Scout
Phase 3: Architect
Phase 4: Execute (beads through L0 -> L1 -> L2 -> L2.5 AQS)
Phase 4.5: Harden (NEW -- per-bead reliability engineering)
Phase 5: Synthesize
```

Conductor dispatches Reliability Conductor when bead reaches `hardened`. Runs per-bead, not batch.

### Loop Integration

```
L0:    Runner self-correction (3 attempts)
L1:    Sentinel correction (2 cycles) -- drift-detector + convention-enforcer
L2:    Oracle audit (2 cycles) -- VORP standard
L2.5:  AQS (2 cycles) -- red/blue on 4 domains
L2.75: Reliability Hardening (2 cycles) -- NEW
L3-L5: Bead -> Phase -> Task escalation
L6:    Calibration loop
```

### Sentinel Patrol During Hardening

L1 Sentinel patrols during Phase 4.5:
- **Drift-detector:** Hardening doesn't introduce architectural drift
- **Convention-enforcer:** Added logging/metrics follow detected conventions

### Quality Budget Impact

- Hardening findings count against quality budget SLOs
- Budget `depleted`: maximum scrutiny -- 5 premortem agents, double Red Team guppies
- Budget `healthy`: Clear beads (single-file, no external calls, no state mutation, low cyclomatic complexity) skip Red/Blue cycle, go Steps 2-3 direct to Step 6. Clearness is assessed by the Reliability Conductor during stack detection.

### Existing Agent Reuse

| Existing Agent | Role in Phase 4.5 |
|---|---|
| Arbiter | Resolves Red/Blue disputes (same Kahneman protocol) |
| LOSA Observer | Random-samples hardening reports for noise audit |
| Convention Enforcer | Validates instrumentation follows project conventions |
| Drift Detector | Validates hardening doesn't introduce architectural drift |
| Guppy | Red Team recon swarms |

### Noise Audit Integration (Kahneman)

Every 5th bead, LOSA observer samples hardening report and re-runs Red Team probes independently. Findings diverge >20% = occasion noise signal.

---

## New Components Required

### 5 New Agents

| Agent | File | Model | Role |
|---|---|---|---|
| Reliability Conductor | `agents/reliability-conductor.md` | Sonnet | Orchestrates per-bead hardening pipeline |
| Observability Engineer | `agents/observability-engineer.md` | Sonnet | Instruments logging, tracing, metrics |
| Error Hardener | `agents/error-hardener.md` | Sonnet | Error handling, edge cases, circuit breakers, retries, degradation |
| Reliability Red Team | `agents/red-reliability-engineering.md` | Haiku + Sonnet | Probes hardened code for gaps |
| Reliability Blue Team | `agents/blue-reliability-engineering.md` | Sonnet | Fixes/rebuts Red Team findings |

### 1 New Skill

**sdlc-harden** (`skills/sdlc-harden/SKILL.md`): Execution playbook for Phase 4.5

### 1 New Hook

**validate-hardening-report.sh** (`hooks/validate-hardening-report.sh`): PostToolUse on Write|Edit, blocking

### Dual-Process Scheduling Summary

| Step | System 1 (Haiku) | System 2 (Sonnet/Opus) |
|---|---|---|
| 0: Premortem | 3 haiku narratives | Conductor deduplicates |
| 1: Pre-clean | Haiku categorizes dupes | Opus semantic detection |
| 2: Observe | -- | Sonnet cross-file instrumentation |
| 3: Harden | -- | Sonnet failure mode reasoning |
| 4: Probe | 8 haiku guppy recon | Sonnet directed strikes |
| 5: Defend | -- | Sonnet evidence-based fixes |
| 6: Post-clean | Haiku categorizes dupes | Opus semantic detection |
| 7: Report | -- | Conductor WYSIATI sweep |

---

## Theoretical Grounding Quick Reference

| Concept | Source | Where Applied |
|---|---|---|
| System 1/2 dual process | Kahneman | Haiku recon vs Sonnet deliberation |
| Noise audits | Kahneman | LOSA samples every 5th bead |
| WYSIATI | Kahneman | Coverage sweep at Step 7 |
| Premortem | Kahneman/Klein | Step 0 failure narratives |
| Adversarial collaboration | Kahneman | Red/Blue joint report, dispute -> Arbiter |
| Reference class forecasting | Kahneman | Observability profile as anchor |
| Mediating Assessments Protocol | Kahneman | Error Hardener 8-dimension assessment |
| Hypothesis-Experiment-Evidence | Karpathy | Observability Engineer per-function loop |
| One variable at a time | Karpathy | Atomic instrumentation per function |
| Overfit-one-case gate | Karpathy | Red Team first-probe verification |
| Test-time compute scaling | Karpathy | 2-cycle correction budget |
| Hard constraints | Karpathy | Non-negotiable invariants |
| Design for removal | Karpathy | Post-clean feedback loop |
| Software 3.0 verification | Karpathy | Every output is unverified proposal |
| Earn trust incrementally | Karpathy | Clear beads skip Red/Blue |
| GUPP | Yegge | Conductor claims work relentlessly |
| Nondeterministic Idempotence | Yegge | Persistent state survives crashes |
| Rule of Five | Yegge | 7-step multi-pass pipeline |
| 40% code health budget | Yegge | Phase 4.5 IS the health budget |
| Colony thesis | Yegge | 5 specialized agents > 1 generalist |
| Refinery pattern | Yegge | Sequential merge per bead |
| Watchdog chain | Yegge | Sentinel watches Conductor watches workers |
