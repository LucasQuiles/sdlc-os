# FFT Decision Trees

All Fast-and-Frugal Trees for Conductor routing decisions. This is the single source of truth — all skills and agents reference this file.

**Structure:** Each FFT has ordered cues (most diagnostic first), binary exits at each node, one traversal path logged per decision. Based on Gigerenzer's ecological rationality: match strategy complexity to environment structure.

---

## FFT-01: Task Profile Classification

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

## FFT-02: Cynefin Domain Classification

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

## FFT-03: AQS Domain Activation

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

## FFT-04: Phase Configuration

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

## FFT-05: Loop Depth

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

## FFT-06: AQS Convergence (Cycle 2 Decision)

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

## FFT-07: Escalation Strategy (at L3+)

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

## FFT-08: Deterministic vs LLM Check Routing

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

## FFT-09: Hardening Skip Decision

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

## FFT-10: Complexity Source Classification

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

## FFT-11: Budget Allocation

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

## FFT-12: Parallelization Safety

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

## FFT-14: Cross-Model Escalation

**Replaces:** Implicit "always same-model AQS only" assumption
**Anti-pattern guarded:** Single-Model Blind Spot — same model family cannot catch its own systematic failure modes
**Source:** Cross-model adversarial review spec (2026-03-28), Milvus research (53% → 80% detection with debate)

```
FFT-14: cross_model_escalation

  Evaluated: after same-model AQS completes, BEFORE bead status → hardened
  Input: AQS structured exit block (aqs_exit) from references/artifact-templates.md

  Cue 0: Is tmup available and fully operational?
    (crossmodel-preflight.sh: MCP reachable + codex in PATH + tmux
     available + writable artifact path + no conflicting session)
    → NO  → SKIP_UNAVAILABLE
             Log: "tmup unavailable: {specific failure}, continuing Claude-only path"
    → YES → continue

  Cue 1: Is aqs_exit.aqs_verdict == DEFERRED?
    → YES → ESCALATE_L3 (no cross-model — bead stays at proven,
             escalates to Conductor per AQS protocol)
    → NO  → continue

  Cue 2: Is the bead COMPLEX domain or security_sensitive?
    → YES → FULL CROSS-MODEL (4 domain investigators + 1 reviewer)
    → NO  → continue

  Cue 3: Is the quality budget DEPLETED?
    → YES → FULL CROSS-MODEL (4 domain investigators + 1 reviewer)
    → NO  → continue

  Cue 4: Is the quality budget WARNING?
    → YES → TARGETED CROSS-MODEL (1 domain investigator + 1 reviewer)
    → NO  → continue

  Cue 5: Is aqs_exit.arbiter_invoked == true?
    → YES → TARGETED CROSS-MODEL (1 domain investigator + 1 reviewer)
    → NO  → continue

  Cue 6: Is aqs_exit.turbulence_sum > 3?
    → YES → TARGETED CROSS-MODEL (1 domain investigator + 1 reviewer)
    → NO  → continue

  Cue 7: Is any aqs_exit.residual_risk_per_domain >= MEDIUM?
    → YES → TARGETED CROSS-MODEL (1 domain investigator + 1 reviewer)
    → NO  → continue

  Default → SKIP CROSS-MODEL
```

**Outcomes:**
- **FULL:** 5 Codex workers (4 domain investigators + 1 independent reviewer). Grid: 2×3 layout.
- **TARGETED:** 2 Codex workers (1 investigator for `aqs_exit.dominant_residual_risk_domain` + 1 independent reviewer). Grid: 1×2 layout.
- **SKIP_UNAVAILABLE:** Log in decision trace, continue Claude-only. Not a failure.
- **SKIP:** No cross-model review needed. Bead proceeds directly to `hardened`.
- **ESCALATE_L3:** AQS DEFERRED — no cross-model, standard L3 escalation.

**TARGETED worker selection:** Domain investigator chosen from `aqs_exit.dominant_residual_risk_domain`. Tie-break order: security > functionality > resilience > usability (security wins ties because its failure modes are highest-consequence).
