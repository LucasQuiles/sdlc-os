# FFT Decision Architecture — Design Specification

**Date:** 2026-03-26
**Status:** Design Approved
**Scope:** Foundational decision backbone for SDLC-OS — 12 FFTs, extended bead spec, decision trace artifact, task profiles, 1 new skill, 1 new hook, updates to sdlc-orchestrate and scaling-heuristics. Defines attachment points for Phase B (safety control) and Phase C (reliability telemetry).

---

## Overview

Replace the Conductor's prose-driven holistic judgment with explicit Fast-and-Frugal Decision Trees (Gigerenzer) at every decision point. This is a Meadows Level 5-6 intervention (changing rules and information flows), not Level 12 (tweaking parameters).

Three implementation phases, layered sequentially:
- **Phase A (this spec):** FFT definitions + decision trace + bead spec extension + task profiles + HRO structural constraints + hook + Evolve skill
- **Phase B (future spec):** STPA control actions + latent condition trace + deviance normalization monitor (Leveson + Reason + Dekker)
- **Phase C (future spec):** March of Nines reliability ledger + deterministic task routing catalog + common/special cause classification (Karpathy + Deming)

## Theoretical Grounding

| Concept | Source | Principle | Where Applied |
|---------|--------|-----------|---------------|
| Fast-and-Frugal Trees | Gigerenzer | Single-cue, binary-exit, ecologically rational | All 12 FFTs |
| Ecological Rationality | Gigerenzer | Match strategy complexity to environment structure | FFT selection criteria |
| Leverage Points Level 5-6 | Meadows | Change rules and information flows, not parameters | Decision trace as new information flow |
| Anti-Tampering | Deming | Stable processes should not be adjusted (Funnel Rule 1) | FFT-06 convergence |
| System over Agents | Deming | "A bad system beats a good person every time" | FFT-07 escalation |
| Barbell Strategy | Taleb | Extreme safety + extreme risk, nothing in the middle | FFT-11 budget allocation |
| Reluctance to Simplify | Weick | Resist premature categorization | FFT-02 Cynefin, HRO constraints |
| Deference to Expertise | Weick | Domain specialists override Conductor judgment | HRO constraint #5 |
| Local Rationality | Dekker | Fix the context, not the runner | FFT-07 escalation |
| Recognition-Primed Decisions | Klein | Fast-path for familiar patterns | FFT-01 + precedent system |
| Four Conditions for Wise Crowds | Surowiecki | Diversity, independence, decentralization, aggregation | Multi-agent consensus verification |
| Certainty Effect | Kahneman | Zero-to-one threshold is qualitatively different | FFT-06 convergence |
| Focusing Illusion | Kahneman | Attention asymmetry within reviewed areas | Phase C proportionality audit |
| Duration Neglect | Kahneman | Turbulence score counters peak-end bias | Bead turbulence field |
| Deterministic Task Routing | Karpathy | Route known-answer tasks away from LLMs | FFT-08 check routing |
| March of Nines | Karpathy | Per-step reliability tracking | Phase C reliability ledger |
| Slopacolypse Defense | Karpathy | Simplicity audit for unnecessary complexity | Phase C simplicity audit |
| Essence vs Accident | Brooks | Classify complexity source for routing | FFT-10 complexity source |

### Anti-Patterns Guarded Against

Each FFT explicitly guards against a named anti-pattern from the thinkers-lab index:

| Anti-Pattern | Source | Mechanism of Failure | FFT Guard |
|-------------|--------|---------------------|-----------|
| Analysis Paralysis | Gigerenzer | Over-analyzing when simple heuristics suffice | FFT-01, FFT-04 skip unnecessary phases |
| Oversimplification | Weick | Premature categorization closing off inquiry | FFT-02 forces explicit classification |
| Parameter Obsession | Meadows | Tuning knobs when structure needs changing | FFT-03, FFT-10 binary activation |
| Over-Engineering for Safety | Taleb | Protection breeding brittleness | FFT-05, FFT-09 skip for Clear beads |
| Tampering | Deming | Reacting to common-cause as special-cause | FFT-06 stable process guard |
| Narrative Fallacy | Taleb | Post-hoc causal stories obscuring multi-causal reality | FFT-07 systemic pattern analysis |
| Garbage In, Gospel Out | Sterman | Model outputs as truth without scrutiny | FFT-08 deterministic routing |
| Normalization of Deviance | Dekker | Gradual acceptance of degraded standards | Evolve profile deviance monitoring |

---

## Section 1: The 12 Fast-and-Frugal Trees

Each FFT follows Gigerenzer's structure: ordered cues (most diagnostic first), binary exits at each node, one traversal path logged per decision.

### FFT-01: Task Profile Classification

**Replaces:** Implicit "always Build" assumption
**Anti-pattern guarded:** Analysis Paralysis — Investigate and Repair profiles skip unnecessary phases
**Source:** thinkers-lab `sdlc-map-23` (Gigerenzer FFT design), `antipattern-10` (Analysis Paralysis)

```
FFT-01: task_profile

  Cue 1: Is the goal to understand, investigate, or research with no code changes expected?
    → YES → INVESTIGATE
    → NO  → continue

  Cue 2: Is this a targeted fix for a known bug, failing test, or specific defect?
    → YES → REPAIR
    → NO  → continue

  Cue 3: Is the quality budget at WARNING or DEPLETED with no user task pending?
    → YES → EVOLVE
    → NO  → continue

  Default → BUILD
```

**Trace log:** Which cue fired, profile assigned.

### FFT-02: Cynefin Domain Classification

**Replaces:** Signal checklists in `scaling-heuristics.md:23-67`
**Anti-pattern guarded:** Oversimplification — forces explicit classification rather than implicit assumption
**Source:** thinkers-lab `sdlc-map-23` (detailed FFT for Cynefin), `antipattern-7` (Oversimplification)

```
FFT-02: cynefin_domain

  Cue 1: Production incident or active exploitation?
    → YES → CHAOTIC
    → NO  → continue

  Cue 2: Requirements contradictory, success criteria untestable, or scope unboundable?
    → YES → CONFUSION
    → NO  → continue

  Cue 3: Touches auth, user input, credential handling, or authorization logic?
    → YES → COMPLEX + security_sensitive: true
    → NO  → continue

  Cue 4: Single file, <50 lines changed, no new I/O, no exported API change?
    → YES → CLEAR
    → NO  → continue

  Cue 5: 5+ files, new external integration, data model change, or new async pattern?
    → YES → COMPLEX
    → NO  → continue

  Default → COMPLICATED
```

Note: Cue 3 absorbs the security-sensitive override (currently separate in `scaling-heuristics.md:59-67`). Auth touch = Complex immediately. One cue, high ecological validity. This makes 90% of classifications in under one second with one cue (source: thinkers-lab `sdlc-map-23`).

**Trace log:** Which cue fired, domain assigned, security_sensitive flag.

### FFT-03: AQS Domain Activation

**Replaces:** Domain selection heuristics in `scaling-heuristics.md:70-132` and cross-reference matrix in `scaling-heuristics.md:165-194`
**Anti-pattern guarded:** Parameter Obsession — binary activation, not weighted scores
**Source:** thinkers-lab `antipattern-18` (Parameter Obsession)

Applied per domain (functionality, security, usability, resilience):

```
FFT-03: aqs_domain_{domain}

  Cue 1: Recon signal exists AND Conductor selected this domain?
    → YES → priority: HIGH (20-40 guppies)
    → NO  → continue

  Cue 2: Recon signal exists but Conductor did NOT select?
    → YES → priority: MED (10-20 guppies)
              Log: "Recon blind spot override — Conductor missed this domain"
    → NO  → continue

  Cue 3: Conductor selected but NO recon signal?
    → YES → priority: LOW (5-10 guppies, light sweep)
    → NO  → continue

  Default → SKIP (0 guppies)
```

The MED case (Cue 2) is the most important — it catches Conductor blind spots. The Conductor must document why recon found a signal the Conductor missed. This is calibration feedback.

**Trace log:** Per-domain priority, any blind spot overrides noted.

### FFT-04: Phase Configuration

**Replaces:** Prose "Skip when" rules in `sdlc-orchestrate/SKILL.md:135,146,153`
**Anti-pattern guarded:** Analysis Paralysis — profiles skip phases they don't need
**Source:** thinkers-lab `antipattern-10` (Analysis Paralysis)

```
FFT-04: phase_config

  Cue 1: profile == INVESTIGATE?
    → YES → Frame: normal
             Scout: HEAVY (parallel investigators, gap-analyst, feature-finder, convention-scanner)
             Architect: INVESTIGATE_MANIFEST (bead manifest of read-only investigation beads)
             Execute: READ_ONLY (investigation beads dispatched without Write/Edit tools)
             AQS: SKIP
             Harden: SKIP
             Synthesize: DELIVER_REPORT
    → NO  → continue

  Cue 2: profile == REPAIR?
    → YES → Frame: SKIP (bug already known)
             Scout: MINIMAL (broken area + immediate dependencies only)
             Architect: SKIP (decomposition unnecessary for targeted fix)
             Execute: normal
             AQS: resilience_only
             Harden: normal (bug fixes especially need error handling verification)
             Synthesize: normal
    → NO  → continue

  Cue 3: profile == EVOLVE?
    → YES → Frame: SKIP
             Scout: SKIP
             Architect: SKIP
             Execute: evolution_beads (auto-rule, staleness, PDSA, deviance check)
             AQS: SKIP
             Harden: SKIP
             Synthesize: SYSTEM_REPORT
    → NO  → continue

  Cue 4: cynefin == CHAOTIC?
    → YES → Frame: SKIP
             Scout: SKIP
             Architect: SKIP
             Execute: single_runner (act first)
             AQS: SKIP
             Harden: SKIP
             postmortem: MANDATORY (auto-created after merge)
    → NO  → continue

  Cue 5: cynefin == CLEAR and budget == healthy?
    → YES → Frame: SKIP
             Scout: SKIP
             Architect: SKIP
             Execute: single_bead
             AQS: SKIP
             Harden: SKIP (per FFT-09)
    → NO  → continue

  Default → All phases active, depth per Cynefin domain
```

**Trace log:** Phase configuration chosen, which phases skipped, which cue determined config.

### FFT-05: Loop Depth

**Replaces:** Implied loop depth from Cynefin in `sdlc-orchestrate/SKILL.md:291-308`
**Anti-pattern guarded:** Over-Engineering for Safety — Clear beads don't need deep verification loops
**Source:** thinkers-lab `antipattern-24` (Over-Engineering for Safety), `sdlc-map-10` (Taleb barbell)

```
FFT-05: loop_depth

  Cue 1: cynefin == CHAOTIC?
    → YES → L0 only (act-first single runner, postmortem bead handles review retroactively)
    → NO  → continue

  Cue 2: cynefin == CONFUSION?
    → YES → BLOCKED (bead cannot execute — must be decomposed and reclassified first)
    → NO  → continue

  Cue 3: cynefin == CLEAR and budget == healthy?
    → YES → L0 only (runner self-check, auto-advance)
    → NO  → continue

  Cue 4: cynefin == CLEAR and budget != healthy?
    → YES → L0 + L1 (add sentinel verification)
    → NO  → continue

  Cue 5: cynefin == COMPLICATED?
    → YES → L0 + L1 + L2 + L2.5
    → NO  → continue

  Cue 6: cynefin == COMPLEX or security_sensitive == true?
    → YES → L0 + L1 + L2 + L2.5 + L2.75 (full pipeline including hardening)
    → NO  → continue

  Default → L0 + L1 + L2
```

Note: Cues 1-2 handle CHAOTIC and CONFUSION before any depth assignment, ensuring consistency with FFT-02 and FFT-04. CHAOTIC gets L0 only because the act-first single runner path (FFT-04 Cue 4) has no sentinel/oracle involvement during execution — the mandatory postmortem bead created after merge goes through Complicated-level review retroactively. CONFUSION beads are BLOCKED — they never reach loop depth assignment.

**Trace log:** Loop depth assigned, which layers active.

### FFT-06: AQS Convergence (Cycle 2 Decision)

**Replaces:** Convergence assessment in `sdlc-adversarial/SKILL.md` Cycle Budget section
**Anti-pattern guarded:** Tampering — Cycle 2 fires only on genuine signal, not noise
**Incorporates:** Certainty Effect (Kahneman) — zero-to-one threshold
**Source:** Deming Funnel Rule 1, Kahneman prospect theory, thinkers-lab `antipattern-1` (Tampering)

```
FFT-06: aqs_convergence

  Cue 1: Any CRITICAL finding in Cycle 1?
    → YES → Cycle 2 MANDATORY
             If cynefin was CLEAR: auto-escalate to COMPLICATED (zero-to-one signal)
             Log: "Certainty effect triggered — zero-findings assumption broken"
    → NO  → continue

  Cue 2: Any accepted fix that changed code in Cycle 1?
    → YES → Cycle 2 fires (verify fix holds, check no new attack surface)
    → NO  → continue

  Cue 3: Process is stable — no findings, no fixes, no code changes?
    → YES → Cycle 2 SKIP
             Log: "Deming Rule 1 — stable process, do not adjust"
    → NO  → continue

  Default → Cycle 2 SKIP
```

**Trace log:** Convergence decision, whether zero-to-one signal fired, Deming Rule 1 invocation.

### FFT-07: Escalation Strategy (at L3+)

**Replaces:** Prose recovery patterns in `sdlc-loop/SKILL.md:310-320`
**Anti-pattern guarded:** Narrative Fallacy — don't construct a clean single-cause story; address the systemic pattern
**Incorporates:** Sunk Cost Protocol (Kahneman), Local Rationality (Dekker)
**Source:** thinkers-lab `antipattern-3` (Narrative Fallacy), `sdlc-map-18` (Dekker local rationality)

```
FFT-07: escalation_strategy

  Cue 1: Same error type failed 3+ times across beads in this task?
    → YES → ROOT_CAUSE_ANALYSIS
             Fix the system (prompts, specs, conventions), not the bead.
             Dekker: "the runner is not defective; it is behaving rationally given locally rational inputs"
    → NO  → continue

  Cue 2: Bead has been re-decomposed once already?
    → YES → ESCALATE_TO_USER (prevent infinite re-decomposition loop)
    → NO  → continue

  Cue 3: Runner reported NEEDS_CONTEXT?
    → YES → ENRICH_AND_REDISPATCH (provide missing context, don't redesign)
    → NO  → continue

  Cue 4: Sunk cost check — "If starting fresh with everything I know, would I choose this design?"
    → NO  → REDESIGN_BEAD (abandon sunk cost, fresh approach)
    → YES → INCREASE_BUDGET (approach is right, needs more iterations)

  Default → REDESIGN_BEAD
```

**Trace log:** Escalation type, sunk cost check result, root cause pattern if detected, Dekker local rationality applied.

### FFT-08: Deterministic vs LLM Check Routing

**Replaces:** Implicit assumption that all checks go through LLM agents
**Anti-pattern guarded:** Garbage In, Gospel Out — don't use LLMs for questions with deterministic answers
**Source:** Karpathy deterministic task routing, thinkers-lab `antipattern-8` (Garbage In, Gospel Out)

```
FFT-08: check_routing

  Cue 1: Is this check answerable by running a command with binary pass/fail?
         (type-check, lint, test suite, file-exists, grep, import-cycle-detection,
          schema validation, coverage threshold, secret pattern scan, license header)
    → YES → DETERMINISTIC (shell script, p=1.0)
    → NO  → continue

  Cue 2: Does this check require reading code and reasoning about behavior,
         architecture, intent, or design quality?
    → YES → LLM_AGENT (agent dispatch, p<1.0)
    → NO  → continue

  Default → LLM_AGENT
```

A reference file `references/deterministic-checks.md` catalogs known deterministic checks. New checks classified at authoring time. The routing decision itself is deterministic — no LLM overhead.

**Trace log:** Per-check routing decision (DETERMINISTIC or LLM_AGENT), check name.

### FFT-09: Hardening Skip Decision

**Replaces:** Prose conditions in `sdlc-harden/SKILL.md` Quality Budget Scaling table
**Anti-pattern guarded:** Over-Engineering for Safety — don't harden code that doesn't need it
**Source:** thinkers-lab `antipattern-24` (Over-Engineering for Safety)

```
FFT-09: hardening_skip

  Cue 1: profile == INVESTIGATE or profile == EVOLVE?
    → YES → SKIP hardening entirely (no code changes to harden)
    → NO  → continue

  Cue 2: cynefin == CLEAR and budget == healthy?
    → YES → SKIP (low complexity + healthy budget = trust the code)
    → NO  → continue

  Cue 3: Bead has zero external calls and zero state mutations?
    → YES → PARTIAL — run Observe + Harden (Steps 2-3) only, skip Red/Blue (Steps 4-5)
    → NO  → continue

  Default → FULL hardening pipeline (all 7 steps)
```

**Trace log:** Hardening decision (FULL/PARTIAL/SKIP), skip reason.

### FFT-10: Complexity Source Classification

**New decision point** — classifies whether bead complexity is essential or accidental (Brooks)
**Anti-pattern guarded:** Parameter Obsession — essential complexity needs scrutiny; accidental needs simplification
**Source:** Brooks "No Silver Bullet", thinkers-lab `antipattern-18` (Parameter Obsession)

```
FFT-10: complexity_source

  Cue 1: Is this bead implementing novel business logic, a new state machine,
         or a new domain model?
    → YES → ESSENTIAL (full AQS + hardening — this is where real bugs live)
    → NO  → continue

  Cue 2: Is this bead framework boilerplate, configuration, migration script,
         or build tooling?
    → YES AND security_sensitive == false → ACCIDENTAL (skip AQS adversarial, run deterministic checks only)
    → YES AND security_sensitive == true  → ESSENTIAL (security-sensitive config/auth/CORS/filesystem changes
                                            look "accidental" but carry real risk — security_sensitive overrides)
    → NO  → continue

  Cue 3: Is this bead refactoring existing logic without changing behavior?
    → YES → ACCIDENTAL (behavioral equivalence proof needed, not adversarial probing)
    → NO  → continue

  Default → ESSENTIAL (when in doubt, treat as essential)
```

**Trace log:** Classification (ESSENTIAL or ACCIDENTAL), reason.

### FFT-11: Budget Allocation

**Replaces:** Priority-to-guppy-count table in `scaling-heuristics.md:137-151`
**Anti-pattern guarded:** Barbell violation — avoid "medium" scrutiny
**Source:** Taleb barbell strategy, thinkers-lab `sdlc-map-10`

```
FFT-11: budget_allocation

  Cue 1: domain priority == HIGH?
    → YES → 20-40 guppies (barbell maximum — full attack)
    → NO  → continue

  Cue 2: domain priority == SKIP or (complexity_source == ACCIDENTAL and security_sensitive == false)?
    → YES → 0 guppies (barbell minimum — no scrutiny needed)
    → NO  → continue

  Cue 3: domain priority == MED (recon blind spot override)?
    → YES → 10-20 guppies (justified middle — recon surfaced something unexpected)
    → NO  → continue

  Default → 5-10 guppies (LOW priority light sweep)
```

The barbell principle: most beads get minimal scrutiny (Clear/SKIP), a few get maximum (Complex/HIGH). MED is the only justified middle — recon surfaced a genuine blind spot the Conductor missed.

**Trace log:** Per-domain guppy allocation, barbell position (max/min/justified-middle).

### FFT-12: Parallelization Safety

**Replaces:** Safe/must-serialize lists in `sdlc-orchestrate/SKILL.md:272-289`

```
FFT-12: parallelization

  Cue 1: Do beads modify the same file?
    → YES → SERIALIZE
    → NO  → continue

  Cue 2: Does bead B depend on bead A's output (explicit dependency in manifest)?
    → YES → SERIALIZE
    → NO  → continue

  Cue 3: Are both beads read-only (investigation, audit, evolve)?
    → YES → PARALLELIZE
    → NO  → continue

  Default → PARALLELIZE (independent beads run in parallel by default)
```

**Trace log:** Per-bead-pair parallelization decision, reason.

---

## Section 2: Decision Trace Artifact

Every FFT traversal produces a decision trace — a structured log recording which cues were checked and what decision resulted. This is the core Meadows Level 6 intervention: a new information flow making the Conductor's judgment visible, auditable, and queryable.

**Location:** `docs/sdlc/active/{task-id}/beads/{bead-id}-decision-trace.md`

Stored alongside the bead file in the flat `beads/` directory — NOT in a subdirectory. This preserves the existing flat bead artifact layout that `guard-bead-status.sh` watches via `docs/sdlc/active/*/beads/*.md`. The trace file uses the `{bead-id}-decision-trace.md` naming convention so it sits next to `{bead-id}.md` without conflicting with the status hook's bead file pattern match.

### Format

```markdown
# Decision Trace: {bead-id}
**Generated:** {timestamp}
**Task:** {task-id}

## FFT-01: Task Profile
- Cue 1 (investigation, no code changes?): {YES/NO}
- Cue 2 (targeted fix for known bug?): {YES/NO}
- Cue 3 (budget WARNING/DEPLETED?): {YES/NO}
- **Decision:** {BUILD|INVESTIGATE|REPAIR|EVOLVE}

## FFT-02: Cynefin Domain
- Cue 1 (production incident?): {YES/NO}
- Cue 2 (requirements contradictory?): {YES/NO}
- Cue 3 (touches auth/user-input?): {YES/NO}
- Cue 4 (single file, <50 lines, no I/O?): {YES/NO}
- Cue 5 (5+ files, new integration?): {YES/NO}
- **Decision:** {CLEAR|COMPLICATED|COMPLEX|CHAOTIC|CONFUSION}
- **Security sensitive:** {true|false}

## FFT-03: AQS Domain Activation
| Domain | Recon Signal | Conductor Selected | Priority | Guppies |
|--------|-------------|-------------------|----------|---------|
| functionality | {YES/NO} | {YES/NO} | {HIGH/MED/LOW/SKIP} | {count} |
| security | {YES/NO} | {YES/NO} | {HIGH/MED/LOW/SKIP} | {count} |
| usability | {YES/NO} | {YES/NO} | {HIGH/MED/LOW/SKIP} | {count} |
| resilience | {YES/NO} | {YES/NO} | {HIGH/MED/LOW/SKIP} | {count} |
**Blind spot overrides:** {list or "none"}

## FFT-04: Phase Configuration
- **Cue fired:** {cue number and condition}
- **Config:** {phase list with status}

## FFT-05: Loop Depth
- **Decision:** {loop levels active}

## FFT-06: AQS Convergence
*(populated after Cycle 1 completes)*
- Cue 1 (CRITICAL finding?): {YES/NO}
- Cue 2 (accepted fix changed code?): {YES/NO}
- Cue 3 (process stable?): {YES/NO}
- **Decision:** {Cycle 2 MANDATORY|FIRES|SKIP}
- **Zero-to-one signal:** {fired|not applicable}
- **Deming Rule 1:** {invoked|not applicable}

## FFT-07: Escalation Strategy
*(populated if escalation occurs)*
- Cue 1 (same error 3+ times?): {YES/NO}
- Cue 2 (already re-decomposed?): {YES/NO}
- Cue 3 (NEEDS_CONTEXT?): {YES/NO}
- Cue 4 (sunk cost check — would I choose this again?): {YES/NO}
- **Decision:** {ROOT_CAUSE|ESCALATE_TO_USER|ENRICH|REDESIGN|INCREASE_BUDGET}

## FFT-08: Check Routing
| Check | Routing | Reason |
|-------|---------|--------|
| {check name} | {DETERMINISTIC|LLM_AGENT} | {reason} |

## FFT-09: Hardening Skip
- **Decision:** {FULL|PARTIAL|SKIP}
- **Reason:** {reason}

## FFT-10: Complexity Source
- **Decision:** {ESSENTIAL|ACCIDENTAL}
- **Reason:** {reason}

## FFT-11: Budget Allocation
| Domain | Priority | Guppies | Barbell Position |
|--------|----------|---------|------------------|
| {domain} | {priority} | {count} | {max|min|justified-middle} |

## FFT-12: Parallelization
| Bead Pair | Decision | Reason |
|-----------|----------|--------|
| {A, B} | {SERIALIZE|PARALLELIZE} | {reason} |

## Anti-Pattern Guards Fired
| FFT | Anti-Pattern | Guard Fired? | Details |
|-----|-------------|-------------|---------|
| {fft} | {pattern} | {YES/NO} | {details if fired} |

## HRO Constraint Checks
- Preoccupation with failure (zero-findings note): {recorded|N/A}
- Reluctance to simplify: {pending Phase 5 check}
- Sensitivity to operations (raw log review this bead): {YES/NO}
- Deference to expertise (specialist override): {none|{details}}
```

### Properties of the Decision Trace

1. **Meadows Level 6 (Information Flow):** Makes invisible Conductor judgment visible and auditable
2. **Primary input to Evolve loop:** Queryable — "how often does FFT-02 Cue 4 fire?" "what % of REPAIR beads stay at L0?"
3. **Substrate for March of Nines (Phase C):** Per-step success rates computed FROM decision traces + turbulence fields
4. **Deviance normalization detection (Phase B):** Trend analysis on Clear classification rate, skip frequency, barbell distribution
5. **Retrospective analysis:** After incidents, trace backward through FFT decisions to find where routing went wrong

---

## Section 3: Extended Bead Specification

The bead format in `sdlc-orchestrate/SKILL.md` gains new fields. Each field annotated with which phase introduces it:

```markdown
# Bead: {id}
**Status:** pending | running | submitted | verified | proven | hardened | reliability-proven | merged | blocked | stuck | escalated
**Type:** investigate | design | implement | verify | review | evolve          [evolve new in Phase A]
**Profile:** BUILD | INVESTIGATE | REPAIR | EVOLVE                             [new - Phase A]
**Runner:** [agent name or "unassigned"]
**Dependencies:** [list of bead IDs]
**Scope:** [files/areas]
**Input:** [context needed]
**Output:** [what must be produced]
**Sentinel notes:** [flags]
**Cynefin domain:** clear | complicated | complex | chaotic | confusion
**Security sensitive:** true | false                                            [new - Phase A]
**Complexity source:** essential | accidental                                   [new - Phase A]
**Decision trace:** [path to decision-trace.md]                                 [new - Phase A]
**Deterministic checks:** [list of checks routed to scripts]                    [new - Phase A]
**Control actions:** [Phase B — control actions this bead performs]              [placeholder - Phase B]
**Unsafe control actions:** [Phase B — UCAs derived via STPA]                   [placeholder - Phase B]
**Latent condition trace:** [Phase B — upstream layer hole identification]       [placeholder - Phase B]
**Turbulence:** {L0: 0, L1: 0, L2: 0, L2.5: 0, L2.75: 0}                     [new - Phase A]
**Assumptions:** [explicit list]
**Safe-to-fail:** [rollback plan]
**Confidence:** [0.0-1.0 with rationale]
```

**New fields summary:**
- `Profile` — task profile from FFT-01
- `Security sensitive` — from FFT-02 Cue 3
- `Complexity source` — from FFT-10
- `Decision trace` — path to decision-trace.md artifact
- `Deterministic checks` — checks routed to scripts per FFT-08
- `Turbulence` — loop cycle counts, populated during execution
- `Type: evolve` — new bead type for Evolve profile

**Phase B placeholders** (defined but not populated until Phase B):
- `Control actions` — STPA enumeration (Leveson)
- `Unsafe control actions` — UCA derivation (Leveson)
- `Latent condition trace` — upstream hole identification (Reason)

---

## Section 4: Task Profile Behaviors

Four profiles emerge as routing outcomes from FFT-01, implemented within the existing orchestration skill — not as separate orchestration systems.

### BUILD (current default — unchanged)

Full Frame -> Scout -> Architect -> Execute -> Synthesize. All Cynefin routing applies. AQS per domain activation. Phase 4.5 per hardening skip FFT. This is the existing behavior.

### INVESTIGATE

**Purpose:** Understand a codebase, research a question, find dependencies, map architecture — with no code changes.

- Phase 1 (Frame): normal — clarify the investigation question
- Phase 2 (Scout): HEAVY — parallel investigators, gap-analyst Finder, feature-finder, convention-scanner all fire
- Phase 3 (Architect): Creates a bead manifest of read-only investigation beads (type: `investigate`). Each bead targets a specific investigation question or code area. The output is a structured discovery report, not a design decision.
- Phase 4 (Execute): Investigation beads dispatched with no Write/Edit tools in runner context. Runners can Read, Grep, Glob, Bash (read-only commands) only. Each bead produces investigation findings, not code changes. Decision traces are bead-scoped as normal.
- Phase 4.5 (Harden): SKIP — no code changes to harden
- Phase 5 (Synthesize): DELIVER_REPORT — delivers the investigation findings as a structured report
- AQS: SKIP — no code to probe
- Loop depth: L0 + L1 only (runner self-check + sentinel verification of report quality)
- Bead type: `investigate`

### REPAIR

**Purpose:** Fix a known bug, failing test, specific defect, or targeted vulnerability — fast, focused, with appropriate verification.

- Phase 1 (Frame): SKIP — the bug is already known
- Phase 2 (Scout): MINIMAL — scan the broken area and its immediate dependencies only. No gap-analyst, no feature-finder.
- Phase 3 (Architect): SKIP — decomposition unnecessary for a targeted fix
- Phase 4 (Execute): normal — focused beads implementing the fix
- Phase 4.5 (Harden): normal — bug fixes especially need error handling verification (the area was already broken once)
- Phase 5 (Synthesize): normal — fitness check + delivery
- AQS: resilience domain only — the most relevant domain for bug fixes (was the failure path handled? does the fix degrade gracefully?)
- Loop depth: L0 + L1 + L2 + L2.5 (resilience-focused)
- Bead type: `implement`

### EVOLVE

**Purpose:** System self-improvement. No user-facing code changes. Maintains and improves the SDLC system itself.

- Phases 1-3: SKIP — no task to frame, scout, or architect
- Phase 4 (Execute): dispatches evolution beads:
  - **Auto-rule generation:** Scan precedent database for findings appearing 3+ times across tasks. Draft candidate constitution rules. Present to Conductor for approval (not auto-apply).
  - **Constitution staleness check:** For each constitution rule, check: is the defect type still appearing in external sources (CVE databases, security research)? Is the rule's confirmation rate declining? Apply Lindy-weighted trust (Taleb): older externally-validated rules checked less frequently; younger internally-validated rules checked more aggressively.
  - **Calibration parameter tuning:** PDSA cycle (Deming) on system parameters — propose a change, execute a calibration bead under new parameters, study results, adopt/abandon/modify.
  - **Precedent coherence audit:** Check for contradicting precedents in the precedent database. Flag inconsistencies for Conductor review.
  - **Deviance normalization check:** Trend analysis on leading indicators — Clear classification rate expanding? Fast-track resolution rate increasing? Average loop depth decreasing? Budget "healthy" duration growing without recalibration? Co-trending in the deviance direction triggers a system-level alert.
- Phase 4.5 (Harden): SKIP — no user code to harden
- Phase 5 (Synthesize): SYSTEM_REPORT — produces system health report with evolution outcomes
- AQS: SKIP
- Loop depth: L0 only
- Bead type: `evolve`
- **Triggers:** Automatically when quality budget reaches WARNING. Every 20th task. Manually via `/evolve` command.

---

## Section 5: Weick HRO Structural Constraints

Five principles of High Reliability Organizations (Weick & Sutcliffe) implemented as hard constraints across the system — not optional checks, not aspirational goals.

**Source:** thinkers-lab `methods/cd9a69a45aa7421e` (Five Principles of HRO)

### 1. Preoccupation with Failure

Every all-clean bead (zero findings across ALL loop layers) gets a mandatory "Why was this clean?" note in the decision trace. Clean results are suspicious until explained — they may indicate inadequate scrutiny rather than genuine quality.

**Implementation:** After Phase 4/4.5 completes for a bead with zero findings at all layers, the Conductor adds to the decision trace:
```
## Zero-Findings Note (HRO Preoccupation with Failure)
This bead produced zero findings across L0-L2.75. Possible explanations:
- [ ] Genuinely simple, well-constructed code (CLEAR domain, accidental complexity)
- [ ] Insufficient scrutiny (loop depth too shallow for actual complexity)
- [ ] Agent blind spot (correlated failure across verification layers)
Conductor assessment: {explanation}
```

### 2. Reluctance to Simplify

Phase 5 delivery summary MUST contain at least one uncertainty, unknown, or open question. If the summary contains zero unknowns, flag it as "suspiciously clean — reluctance-to-simplify gate failed."

**Implementation:** The `haiku-handoff` agent at Phase 5 is instructed: "Your delivery summary MUST include at least one item under 'Uncertainties and Open Questions.' If you genuinely cannot identify any uncertainty, state that explicitly and explain why — this itself requires Conductor review."

### 3. Sensitivity to Operations

Every 3rd bead, the Conductor reads raw sentinel logs (not just the summary). This prevents the Conductor from operating on abstractions that have drifted from operational reality.

**Implementation:** The decision trace includes:
```
## Raw Log Review (HRO Sensitivity to Operations)
Bead number in task: {N}
Raw review required (every 3rd): {YES/NO}
Raw review completed: {YES/NO — populated after review}
```

### 4. Commitment to Resilience

The loop hierarchy (L0-L2.75) IS the commitment to resilience. The system bounces back through structured self-correction at every level. No change needed — already strong.

### 5. Deference to Expertise

When a domain-specialist agent flags a finding, the Conductor CANNOT dismiss it — it MUST proceed to the Blue Team regardless of the Conductor's own judgment. Domain expertise overrides hierarchical authority.

**Applies to:** `red-functionality`, `red-security`, `red-usability`, `red-resilience`, `red-reliability-engineering`, `observability-engineer`, `error-hardener`

**Implementation:** A new constraint in the Conductor's operating model: "You may disagree with a specialist agent's finding, but you may NOT suppress it. All specialist findings proceed to their corresponding Blue Team. Your disagreement is logged in the decision trace for retrospective analysis, not used as a filter."

---

## Section 6: Phase B Attachment Points (Safety Control Layer — Future Spec)

Phase B adds three capabilities that attach to the decision backbone created in Phase A.

### 6.1 STPA Control Analysis (Leveson)

**Attaches to:** Phase 3 (Architect), bead `control_actions` and `unsafe_control_actions` fields
**Trigger:** FFT-02 assigns COMPLEX or security_sensitive == true
**Source:** thinkers-lab `methods/f113956e89ee7b0e` (STPA Hazard Analysis)

**Mechanism:** For Complex/security-sensitive beads, the Architect phase adds a control analysis step:
1. Enumerate control actions the bead performs (API calls, state transitions, auth checks, data writes)
2. For each control action, derive Unsafe Control Actions (UCAs) in four categories:
   - Not provided when needed (missing auth check, missing validation)
   - Provided when not needed (unnecessary writes, redundant locks)
   - Wrong timing or order (race condition, out-of-sequence transition)
   - Stopped too soon or applied too long (premature timeout, held lock)
3. UCAs become automatic Red Team probe targets — replacing heuristic attack selection with systematic control-theoretic analysis

### 6.2 Latent Condition Trace (Reason)

**Attaches to:** AQS and Phase 4.5 finding reports, bead `latent_condition_trace` field
**Trigger:** Any finding with action == accepted
**Source:** thinkers-lab `scenarios/scenario-1` (Swiss Cheese analysis for recurring failures)

**Mechanism:** Blue Team response format gains a new field:
```
**Latent condition:** Which upstream layer should have caught this?
- [ ] L0 Runner (prompt gap, spec ambiguity, missing context)
- [ ] L1 Sentinel (drift-detector blind spot, convention gap)
- [ ] L2 Oracle (VORP check missed this claim type)
- [ ] L2.5 AQS (attack library gap, domain selection miss)
- [ ] Convention Map (unmapped pattern)
- [ ] Code Constitution (missing rule)
- [ ] Other: {specify}
```

This traces from the active failure (the code defect) back to the resident pathogen (the system gap that allowed it through). Over time, latent condition traces reveal which upstream layers have the most holes — directing system improvement effort to the highest-leverage points.

### 6.3 Deviance Normalization Monitor (Dekker)

**Attaches to:** Evolve profile, calibration protocol
**Trigger:** Every Evolve cycle
**Source:** thinkers-lab `antipattern-2` (Normalization of Deviance), `netnew-012` (Deviance Normalization Detector)

**Mechanism:** Trend analysis on leading indicators computed from decision traces:
- Clear classification rate (% of beads classified CLEAR over rolling 10-task window)
- Fast-track resolution rate (% of AQS findings resolved via plea bargaining)
- Average loop depth (mean active loop layers per bead)
- Scrutiny skip rate (% of beads where FFT-09 returned SKIP)
- Budget "healthy" duration (tasks since last WARNING/DEPLETED)

No single metric triggers an alert. Co-trending of 3+ indicators in the deviance direction over a sustained window triggers a system-level review requirement — the pattern must be named and addressed as a whole.

---

## Section 7: Phase C Attachment Points (Reliability Telemetry — Future Spec)

Phase C adds three capabilities that measure the backbone.

### 7.1 March of Nines Reliability Ledger (Karpathy)

**Attaches to:** Bead `turbulence` field, decision traces
**Source:** thinkers-lab `netnew-005` (March of Nines)

**Mechanism:** Aggregate turbulence fields across tasks:
- L0 first-pass success rate: {beads passing L0 on first attempt} / {total beads}
- L1 first-pass approval rate: {beads approved by sentinel first submission} / {total beads reaching L1}
- L2 first-pass proof rate: {beads proven by oracle first audit} / {total beads reaching L2}
- L2.5 first-pass hardening rate: {beads hardened first AQS cycle} / {total beads reaching L2.5}

Per-step rates enable bottleneck identification. If L0 passes 60% but L2 passes 95%, invest in runner context quality (prompts, specs), not oracle prompts.

### 7.2 Common/Special Cause Classification (Deming)

**Attaches to:** Calibration protocol noise audit
**Source:** thinkers-lab `antipattern-1` (Tampering), `methods/781821076d04250f` (Red Bead Experiment)

**Mechanism:** Before any corrective action triggered by calibration or noise audit:
1. Plot the metric on a control chart (mean ± 3 sigma)
2. Is the signal within control limits? → Common cause. Fix the SYSTEM (prompts, rubrics, temperature). Do NOT adjust individual agents.
3. Is the signal outside control limits? → Special cause. Investigate and fix THAT specific agent/configuration.
4. Deming Funnel Rule 1: If the control chart shows a stable process, do NOT adjust. Tampering is worse than inaction.

### 7.3 Slopacolypse Defense / Simplicity Audit (Karpathy)

**Attaches to:** L1 Sentinel loop
**Source:** thinkers-lab `netnew-004` (Slopacolypse Defense)

**Mechanism:** After runner submission, before full sentinel verification:
1. Compute solution complexity: lines of code, number of abstractions, dependency count, nesting depth
2. Estimate problem complexity from bead spec: scope (files), domain (ESSENTIAL/ACCIDENTAL), FFT-10 classification
3. Compute simplicity coefficient: problem_complexity / solution_complexity
4. If coefficient < threshold (solution is disproportionately complex): flag for mandatory justification
5. Check for: dead code paths, premature generalization, factory patterns wrapping single functions, strategy patterns for two-branch conditionals

---

## Section 8: Hook Enforcement

### New Hook: validate-decision-trace.sh

**Event:** PostToolUse on Write|Edit
**Target:** Bead files in `docs/sdlc/active/*/beads/*.md`
**Mode:** Blocking (exit 2 = validation error)

**Validates (bead field checks):**
- `Profile` field present and one of BUILD|INVESTIGATE|REPAIR|EVOLVE
- `Security sensitive` field present (true|false)
- `Complexity source` field present (essential|accidental)
- `Decision trace` field contains a file path
- `Deterministic checks` field present (may be empty list)
- `Turbulence` field present with valid structure

**Validates (trace artifact checks):**
- The file path in `Decision trace` actually exists on disk
- The trace file contains at least `## FFT-01` and `## FFT-02` section headers (minimum viable trace)
- The trace file contains a `**Decision:**` line under both FFT-01 and FFT-02 (decisions were actually recorded, not just headers)

The bead field checks run on every bead write. The trace artifact checks run only when the bead status transitions past `pending` (a bead can be created with a trace path before the trace is written, but it cannot advance to `running` without the trace existing).

This ensures no bead advances without its FFT traversal recorded AND the trace artifact is structurally valid.

### Updated Hook: guard-bead-status.sh

Two changes required:

1. Add `evolve` as a valid bead type.

2. Add an evolve-specific status flow. Evolve beads do not produce user-facing code, so they skip proven/hardened/reliability-proven. The valid flow is:

```
pending → running → submitted → verified → merged
```

This requires a new case in `guard-bead-status.sh`:
```bash
  verified)
    # Normal: verified -> proven (existing)
    # Evolve beads: verified -> merged (no code to prove/harden)
    if bead type == evolve:
      [[ "$CURRENT_STATUS" =~ ^(proven|merged|blocked|stuck|escalated)$ ]] && VALID=true
    else:
      [[ "$CURRENT_STATUS" =~ ^(proven|blocked|stuck|escalated)$ ]] && VALID=true
```

The hook must check the bead's `Type` field to determine which transitions are valid. This is a real status-flow change, not a no-op.

Note: The `blocked|stuck|escalated` recovery states remain valid for ALL bead types including evolve — they were inadvertently omitted from the bead spec in Section 3. The full status line should read:
```
**Status:** pending | running | submitted | verified | proven | hardened | reliability-proven | merged | blocked | stuck | escalated
```

---

## Section 9: New Skill — sdlc-evolve

**File:** `skills/sdlc-evolve/SKILL.md`

Execution playbook for the EVOLVE profile. Defines the five evolution bead types and their protocols:

1. **Auto-Rule Generation** — precedent database scan, candidate rule drafting, Conductor approval gate
2. **Constitution Staleness Check** — Lindy-weighted audit, external ground truth verification, quarantine protocol
3. **Calibration Parameter Tuning** — Deming PDSA cycle on system parameters
4. **Precedent Coherence Audit** — contradiction detection, resolution protocol
5. **Deviance Normalization Check** — leading indicator trend analysis, co-movement detection, system-level alert

Trigger conditions, output formats, and integration with the calibration protocol documented in full.

---

## Section 10: Files Changed

### New Files
| File | Purpose |
|------|---------|
| `references/fft-decision-trees.md` | All 12 FFTs in one reference document for agent consumption |
| `references/deterministic-checks.md` | Catalog of checks routable to scripts (FFT-08) |
| `references/anti-patterns.md` | Named anti-patterns each FFT guards against |
| `hooks/scripts/validate-decision-trace.sh` | Decision trace schema validator |
| `skills/sdlc-evolve/SKILL.md` | Evolve profile execution playbook |
| `commands/evolve.md` | Slash command invoking sdlc-evolve skill |

### Modified Files
| File | Changes |
|------|---------|
| `skills/sdlc-orchestrate/SKILL.md` | Replace prose routing with FFT references. Add task profiles (FFT-01/FFT-04). Add bead spec extension. Add HRO constraints to Phase 5. Add Evolve profile reference. |
| `skills/sdlc-adversarial/scaling-heuristics.md` | Replace signal checklists with FFT-02/FFT-03. Replace convergence prose with FFT-06. Replace budget table with FFT-11. |
| `skills/sdlc-loop/SKILL.md` | Replace recovery prose with FFT-07. Add FFT-08 deterministic routing to L1 sentinel. Add turbulence tracking to bead status extensions. L0 budget remains at 3 (let-it-crash deferred to Phase C). |
| `hooks/hooks.json` | Register validate-decision-trace.sh |
| `hooks/scripts/guard-bead-status.sh` | Add `evolve` bead type |
| `.claude-plugin/plugin.json` | Bump version to 6.0.0 |

---

## Section 11: Design Decisions (Open Questions Resolved)

**Q: Flat bead files or per-bead directories?**
A: **Flat files.** The existing `beads/` directory remains flat. Decision traces go alongside bead files as `{bead-id}-decision-trace.md`, not in subdirectories. This preserves compatibility with `guard-bead-status.sh`'s glob pattern `docs/sdlc/active/*/beads/*.md`. No migration needed.

**Q: Is `/evolve` a real slash command or only a skill?**
A: **Both.** Add a slash command `commands/evolve.md` that invokes the `sdlc-evolve` skill. This parallels the existing `/sdlc` → `sdlc-orchestrate`, `/adversarial` → `sdlc-adversarial` pattern. Add `commands/evolve.md` to the Files Changed inventory.

**Q: Is the L0 budget reduction (3 → 1) intentional?**
A: **Deferred to Phase C.** The let-it-crash principle (Armstrong) argues for 1 attempt, but this is a material behavior change that needs telemetry data (Phase C March of Nines) to justify. The current 3-attempt L0 budget remains unchanged in Phase A. Phase C will evaluate whether reducing to 1 improves or degrades end-to-end reliability using per-step success rate data. Remove L0 budget change from `sdlc-loop/SKILL.md` modifications in Section 10.

---

## Section 12: Implementation Sequence

1. Create reference files (`fft-decision-trees.md`, `deterministic-checks.md`, `anti-patterns.md`)
2. Create `validate-decision-trace.sh` hook + register in `hooks.json`
3. Create `skills/sdlc-evolve/SKILL.md`
4. Update bead spec in `sdlc-orchestrate/SKILL.md` (add new fields)
5. Update `sdlc-orchestrate/SKILL.md` Phase 1 to use FFT-01 and FFT-02
6. Update `scaling-heuristics.md` to FFT format (FFT-02, FFT-03, FFT-06, FFT-11)
7. Update `sdlc-orchestrate/SKILL.md` with task profile phase configurations (FFT-04)
8. Update `sdlc-loop/SKILL.md` with FFT-05, FFT-07, FFT-08, turbulence tracking (L0 budget unchanged)
9. Update `sdlc-orchestrate/SKILL.md` Phase 5 with HRO constraints
10. Add FFT-10 (complexity source) and FFT-12 (parallelization) to `sdlc-orchestrate/SKILL.md`
11. Update `guard-bead-status.sh` for evolve type
12. Bump `plugin.json` to 6.0.0

---

## Theoretical Grounding Quick Reference

| FFT | Primary Thinker | Anti-Pattern Guarded | Thinker Connection |
|-----|----------------|---------------------|--------------------|
| FFT-01 Task Profile | Gigerenzer | Analysis Paralysis | Klein RPD for familiar patterns |
| FFT-02 Cynefin | Gigerenzer + Snowden | Oversimplification (Weick) | Simon bounded rationality |
| FFT-03 AQS Domains | Gigerenzer | Parameter Obsession (Meadows) | Surowiecki aggregation |
| FFT-04 Phase Config | Gigerenzer | Analysis Paralysis | March exploration/exploitation |
| FFT-05 Loop Depth | Taleb + Gigerenzer | Over-Engineering (Taleb) | Deming anti-tampering |
| FFT-06 Convergence | Kahneman + Deming | Tampering (Deming) | Taleb zero-to-one = black swan micro |
| FFT-07 Escalation | Dekker + Kahneman | Narrative Fallacy (Taleb) | Leveson control inadequacy |
| FFT-08 Check Routing | Karpathy | Garbage In, Gospel Out (Sterman) | Gigerenzer ecological rationality |
| FFT-09 Hardening Skip | Taleb | Over-Engineering (Taleb) | Deming Funnel Rule 1 |
| FFT-10 Complexity | Brooks | Parameter Obsession (Meadows) | Simon near-decomposability |
| FFT-11 Budget | Taleb | Barbell violation | Meadows leverage allocation |
| FFT-12 Parallelization | (structural) | (structural) | Helland saga pattern (Phase B) |
