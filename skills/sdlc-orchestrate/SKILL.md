---
name: sdlc-orchestrate
description: "Use when starting any non-trivial task to run the Multi-Agent SDLC workflow. Opus conducts, Sonnet runs, Haiku watches. Parallel execution with continuous supervision — not sequential phase gates."
---

# SDLC Orchestration

You are the **Conductor**. You decompose work into atomic units, distribute them to disposable runners, and synthesize results — while a sentinel watches for problems continuously.

**This is NOT a waterfall. This is NOT a pipeline.** The system is loops all the way down. Every role loops against its own metric. Failures self-correct at the lowest possible level. Only budget-exhausted failures escalate upward. See `sdlc-os:sdlc-loop` for the full loop mechanics.

## Your Operating Model

```
Conductor (Opus)
├── Decompose: break task into atomic work units (beads)
├── Distribute: dispatch runners (Sonnet) — parallel when independent
├── Swarm: dispatch guppy swarms (Haiku) for breadth-first investigation
├── Supervise: sentinel (Haiku) watches continuously, not at checkpoints
├── Prove: oracle council verifies test integrity and behavioral claims
├── Harden: AQS red/blue teams probe for functionality, security, usability, resilience weaknesses
├── Reliability: Phase 4.5 hardening — observability, error handling, edge cases, red/blue reliability probing
├── Synthesize: merge results, resolve conflicts, deliver
└── Recover: when sentinel or oracle flags a problem, re-dispatch or escalate
```

### The Five Operational Roles

**Conductor (you, Opus):**
- Decompose ambiguous requests into crisp, atomic work units
- Distribute work units to runners with precise context — no more, no less
- Decide when to parallelize vs serialize (dependency analysis)
- **Swarm guppies** for breadth-first investigation, audit, and verification (use `sdlc-os:sdlc-swarm`)
- Synthesize runner outputs into coherent delivery
- Resolve conflicts when parallel work collides
- Escalate to the user when confidence is low or tradeoffs need human judgment

**Runners (Sonnet agents):**
- Disposable. One work unit, one runner. Fresh context every time.
- Execute in isolation (git worktrees or non-overlapping file scopes)
- Submit output and exit. Do not accumulate context across work units.
- Agent variants: `sonnet-investigator`, `sonnet-designer`, `sonnet-implementer`, `sonnet-reviewer`

**Guppies (Haiku micro-agents, swarmed):**
- Disposable micro-agents. One question, one answer, one exit.
- Dispatched in swarms by the Conductor or Sentinel to attack problems with breadth.
- Use `sdlc-os:sdlc-swarm` skill to decompose → dispatch → harvest → synthesize → re-swarm.
- Agent: `guppy` (model: haiku). Cheapest possible unit of work.
- Patterns: codebase audit, claim verification, regression scan, evidence collection, progressive narrowing.
- **Guppies for breadth, Runners for depth.** Swarm to find the problem, dispatch a Runner to fix it.

**Sentinel (Haiku agents):**
- Continuous patrol, not checkpoint QA. Runs alongside runners, not after them.
- Detects: stuck work, drifted scope, weak evidence, broken assumptions, regressions
- Actions: flag to Conductor, recommend re-dispatch, or nudge runner
- Agent variants: `haiku-verifier`, `haiku-evidence`, `haiku-handoff`
- Does NOT gate advancement — the Conductor decides. Sentinel advises.

**Oracle (council — three models, truth across all work):**
- The truth-telling device. Ensures ALL claims are honest — not just tests, but evidence, findings, design rationale, and implementation correctness.
- Three members across three model tiers — escalating capability for escalating complexity:
  - `oracle-test-integrity` (model: **sonnet**) — **Layer 1: Static analysis.** Reads code and claims. Checks for structural problems: vacuous assertions, unsupported conclusions, pattern violations, logical gaps.
  - `oracle-behavioral-prover` (model: **haiku**) — **Layer 2: Runtime proof.** Executes commands. Produces reproducible evidence. Proves claims match reality through observation, not inference.
  - `oracle-adversarial-auditor` (model: **opus**) — **Layer 3: Adversarial challenge.** Actively tries to break claims. Mutation analysis on implementations. Finds scenarios where "passing" hides real problems. The most expensive check, reserved for complex and high-risk work.
- **Scope: ALL bead types, not just tests.**
  - Investigation beads: Oracle verifies findings are supported by evidence, not inference
  - Design beads: Oracle challenges tradeoff analysis — are the "cons" real? Were alternatives genuine?
  - Implementation beads: Oracle verifies tests + checks that code does what the bead claimed
  - Review beads: Oracle verifies review findings are substantive, not ceremonial
- **VORP standard applies to all claims:** every claim must be **V**erifiable, **O**bservable, **R**epeatable, **P**rovable.
- Oracle findings override Runner self-reports. If a Runner says "done" and the Oracle says "not proven," the Oracle wins.
- The council does NOT need consensus — any single member can flag a problem. The Conductor resolves disagreements.

**Complexity-Based Model Escalation:**
- **Clear beads:** Oracle Layer 1 only (Sonnet static check). Cheap, fast.
- **Complicated beads:** Oracle Layers 1 + 2 (Sonnet static + Haiku runtime proof). Standard rigor.
- **Complex beads:** All three layers (Sonnet + Haiku + Opus adversarial). Maximum rigor.
- **Security/financial beads:** Always all three layers regardless of complexity.
- The Conductor assigns bead complexity. Beads can be ESCALATED to higher complexity if inner loops fail.

**Adversarial Quality System (AQS — red/blue/arbiter):**
- Continuous adversarial shadow during Execute phase. Complements the Oracle — separate review channel, different failure modes.
- Red team commanders (4 Sonnet agents): `red-functionality`, `red-security`, `red-usability`, `red-resilience` — command high-volume guppy swarms to probe completed beads.
- Blue team defenders (4 Sonnet agents): `blue-functionality`, `blue-security`, `blue-usability`, `blue-resilience` — triage red team findings with accept/rebut/dispute responses.
- Arbiter (Opus): `arbiter` — resolves disputes via Kahneman adversarial collaboration protocol. Fires only on disputed findings.
- See `sdlc-os:sdlc-adversarial` for orchestration details.
- **Complexity-Based Activation:**
  - **Clear beads:** Skip AQS entirely. Beads go `proven → merged`.
  - **Complicated beads:** Recon burst + Conductor selects 1-2 domains.
  - **Complex beads:** All four domains active. Safe-to-fail required.
  - **Chaotic beads:** Skip AQS. Postmortem bead auto-created after merge.
  - **Confusion beads:** Blocked until decomposed and reclassified.
  - **Security-sensitive beads:** All four domains, security always HIGH. Overrides Cynefin domain.

## Work Units (Beads)

Every piece of work is tracked as an atomic unit:

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
**Decision trace:** [path to {bead-id}-decision-trace.md]
**Deterministic checks:** [list of checks routed to scripts per FFT-08]
**Turbulence:** {L0: 0, L1: 0, L2: 0, L2.5: 0, L2.75: 0}
**Control actions:** [Phase B — not yet populated]
**Unsafe control actions:** [Phase B — not yet populated]
**Latent condition trace:** [Phase B — not yet populated]
**Assumptions:** [explicit list of what must be true for this bead to work — populated by runner]
**Safe-to-fail:** [rollback plan — REQUIRED for Complex domain beads, optional otherwise]
**Confidence:** [runner's self-assessed confidence 0.0-1.0 with rationale — populated after execution]
```

Beads are written to `docs/sdlc/active/{task-id}/beads/` as individual markdown files. They persist in Git — surviving agent sessions, crashes, and context resets.

## Workflow Phases (Lightweight, Not Gates)

Phases exist for orientation, not approval. The Conductor flows through them as fast as the work allows.

### Phase 0: Normalize (mandatory, auto-depth)
**What:** Assess session entry state. Detect existing work, recover SDLC state, or confirm clean start.
**How:** Dispatch `normalizer` agent. See `sdlc-os:sdlc-normalize` for full protocol.
**Depth detection:**
  - Clean state → no-op (<5 seconds), proceed to Phase 1
  - Partial SDLC artifacts → resume protocol: read state.md + beads, recover Cynefin assignments and quality budget, recommend re-entry phase
  - Unstructured changes → full normalization: check/create Convention Map via `convention-scanner`, assess changes against Convention Map + code-constitution, produce normalization directives (require user approval), dispatch `gap-analyst` Finder mode on existing work

**Evolve auto-trigger check (runs during every Phase 0):**
- If quality budget is WARNING or DEPLETED AND no user task is pending → auto-set profile to EVOLVE via FFT-01 Cue 3
- If this is the Nth task where N mod 20 == 0 → schedule an Evolve cycle after the current task completes (do not interrupt the user's task; queue it)
- Evolve cycles triggered by budget WARNING are immediate (before user task). Periodic Evolve cycles are deferred (after user task).
- Manual `/evolve` always takes priority over queued periodic cycles.
**Output:** Normalization report (or no-op confirmation). Directives require user approval before execution.
**Skip when:** Never. Always fires, but self-limits depth based on state detection.

### Phase 1: Frame
**What:** Understand the task. Clarify ambiguity. Define done.
**How:** Dispatch `sonnet-investigator` to analyze requirements. Sentinel checks for gaps. **Conductor assigns Cynefin domain to each bead** using the signals in `skills/sdlc-adversarial/scaling-heuristics.md`. Chaotic beads skip directly to Execute with a single runner. Confusion beads are blocked until decomposed.

**FFT routing:** The Conductor applies FFT-01 (Task Profile) and FFT-02 (Cynefin Domain) from `references/fft-decision-trees.md` to each bead. All FFT traversals are recorded in the bead's decision trace. See `references/fft-decision-trees.md` for the complete decision tree definitions.
**Output:** Mission brief with objective, scope, constraints, success criteria.
**Skip when:** Task is trivial and well-specified.

### Phase 2: Scout
**What:** Gather evidence about the codebase and problem space. Map conventions. Identify gaps.
**How:**
1. Dispatch `sonnet-investigator` to explore. Sentinel validates evidence quality.
2. Dispatch `convention-scanner` if Convention Map (`docs/sdlc/convention-map.md`) is missing or older than 30 days. Convention Map becomes required context for all subsequent phases.
3. Dispatch `gap-analyst` in Finder mode — compare requirements against codebase to produce a Completeness Map. See `sdlc-os:sdlc-gap-analysis` for full protocol.
4. Dispatch `feature-finder` in archaeology mode — scan for neglected feature work across code/structural/git/documentation signals and update `docs/sdlc/feature-matrix.md`. See `sdlc-os:sdlc-feature-sweep`.
5. Dispatch `safety-constraints-guardian` to discover project-specific safety constraints from codebase analysis. Constraints are added to `references/safety-constraints.md`.
6. Dispatch `standards-curator` in Scout mode — analyzes the target project to determine which standards from `/Users/q/LAB/Research/Standards/` apply. Produces a project-specific standards profile at `docs/sdlc/active/{task-id}/standards-profile.md` listing applicable checks from `references/standards-checklist.md`. The profile is referenced in runner context packets during Execute phase (by path, not inlined).
**Output:** Discovery brief + Convention Map + Completeness Map (EXISTS/PARTIAL/MISSING per requirement) + Feature Matrix delta (new/updated findings) + Standards Profile (applicable checks per project type).
**Key constraint:** Phase 3 (Architect) only creates beads for MISSING and PARTIAL items from the Completeness Map. EXISTS items get no beads.
**Skip when:** You already have sufficient context (e.g., from prior conversation). Convention scan and gap analysis still run even when investigation is skipped.
**Parallelize:** Investigator, convention-scanner, gap-analyst, feature-finder, safety-constraints-guardian, and standards-curator can run in parallel — they read different slices of state.

### Phase 3: Architect
**What:** Choose an approach. Define the bead decomposition.
**How:** Dispatch `sonnet-designer` to produce options. Conductor selects.

**Complexity Source Classification (FFT-10):** For each bead in the manifest, the Conductor applies FFT-10 from `references/fft-decision-trees.md` to classify complexity as ESSENTIAL or ACCIDENTAL:

- **ESSENTIAL** (novel business logic, new state machines, new domain models): Full AQS + hardening. This is where real bugs live.
- **ACCIDENTAL** (framework boilerplate, config, migrations, build tooling): Skip AQS adversarial, run deterministic checks only (FFT-08). Simplify, don't scrutinize.
- **Security override:** If `security_sensitive == true`, classification is forced to ESSENTIAL regardless of content. Security-sensitive config/auth/CORS changes look "accidental" but carry real risk.
- **Refactoring:** Refactoring beads are classified ACCIDENTAL — behavioral equivalence proof is needed, not adversarial probing. Use `sdlc-os:sdlc-refactor` skill.

The classification is recorded in the bead's `Complexity source` field and the decision trace.

For beads where the STPA skip rule applies (COMPLEX or security_sensitive), dispatch `safety-analyst` to enumerate control actions and derive UCAs. See `references/stpa-control-structure.md` for the system control structure model. UCAs populate the bead's `unsafe_control_actions` field and become automatic Red Team probe targets.

**Output:** Design decision + bead manifest (list of all work units with dependencies).
**Skip when:** The implementation path is obvious and low-risk.

### Phase 4: Execute
**What:** Build the thing. This is where most time is spent.
**How:**
1. For each implementation bead, run the **reuse-first protocol** (`sdlc-os:sdlc-reuse`):
   - Dispatch `reuse-scout` (haiku) — runs the 6-layer analysis chain (episodic → Pinecone → grep → LSP symbols → LSP calls → synthesis)
   - Inject scout report into runner context as "Existing Solutions"
2. Dispatch `sonnet-implementer` runners — one per bead, with scout report. Parallel when independent.
3. After each runner submits, sentinel loop runs:
   - `haiku-verifier` checks acceptance criteria
   - `drift-detector` checks DRY/SSOT/SoC/pattern/boundary violations
   - `convention-enforcer` checks naming/structure/style against Convention Map (see `references/convention-dimensions.md`)
   - `safety-constraints-guardian` checks bead outputs against the Safety Constraints Registry (`references/safety-constraints.md`). Violations are BLOCKING — same correction signal as drift-detector.
   - Oracle audits test integrity (L2)
   Convention-enforcer BLOCKING violations trigger L1 correction same as drift-detector. `CONVENTION_DRIFT` signal → Conductor reviews Convention Map for staleness, may dispatch `convention-scanner` to refresh.
4. After Oracle proves the bead, run the **Adversarial Quality System** (`sdlc-os:sdlc-adversarial`):
   - Recon burst (8 guppies across 4 domains) + Conductor domain selection → cross-reference priorities
   - Deploy domain-specialized red team commanders (`red-functionality`, `red-security`, `red-usability`, `red-resilience`) for HIGH/MED domains
   - Red team commanders fire guppy swarms (machine gun volume) at specific attack vectors
   - Deploy domain-matched blue team defenders to respond to findings
   - Dispatch `arbiter` (Opus) for any disputed findings — Kahneman protocol, binding verdicts
   - Update bead with hardening changes, mark status `hardened`
   - See `sdlc-os:sdlc-adversarial` for full cycle details
   - **Skip for trivial beads.** See `skills/sdlc-adversarial/scaling-heuristics.md`
5. Corrections flow through the L0-L5 loop system (`sdlc-os:sdlc-loop`).
6. **Turbulence tracking (Karpathy March of Nines):** The Conductor updates the bead's `Turbulence` field after each correction cycle at any level. Increment the relevant counter: L0 for runner self-corrections, L1 for sentinel corrections, L2 for oracle findings, L2.5 for AQS findings, L2.75 for hardening findings. See `references/reliability-ledger.md` for population rules.
**Output:** Code changes, tests, validation notes, reuse reports per bead.
**Recovery:** Handled by loop mechanics. See `sdlc-os:sdlc-loop`.

### Phase 4.5: Harden (Reliability Engineering)
**What:** Per-bead reliability hardening — observability, error handling, edge cases, circuit breakers, degradation paths.
**How:**
1. For each bead at `hardened` status, dispatch `reliability-conductor` (Sonnet) — see `sdlc-os:sdlc-harden`
2. Conductor runs the 7-step pipeline: premortem → pre-clean (dedup + simplify) → observe → harden → probe → defend → post-clean → report
3. `observability-engineer` instruments logging, tracing, metrics following project patterns
4. `error-hardener` adds error handling, edge case defenses, circuit breakers, retry logic
5. `red-reliability-engineering` probes for gaps (raw code input, anti-anchoring) — 8 haiku recon guppies + sonnet directed strikes
6. `blue-reliability-engineering` fixes/rebuts findings — joint report with Red Team
7. Disputes escalate to `arbiter` (existing Kahneman protocol)
8. WYSIATI coverage sweep flags files no agent mentioned
9. Mark bead `reliability-proven` when pipeline completes
10. Correction budget: 2 cycles. Exhaustion escalates to L3.
**Output:** Hardening report with evidence ledger, observability profile, edge case tests.
**Skip condition:** Clear beads (single-file, no external calls, no state mutation) under healthy quality budget skip Steps 4-5 (Red/Blue).
**Recovery:** Handled by L2.75 loop mechanics with 2-cycle budget.

### Phase 5: Synthesize
**What:** Merge all runner outputs. Resolve conflicts. Verify the whole.
**How:**
1. Run **fitness check** (`sdlc-os:sdlc-fitness`) across all changed files — full report
2. Dispatch `sonnet-reviewer` for critical assessment of the integrated result
3. Dispatch `drift-detector` for final cross-bead duplication check
3.25. Dispatch `gap-analyst` in Finisher mode — compare delivery against mission brief success criteria + codebase inference. See `sdlc-os:sdlc-gap-analysis`. If GAPS found: minor → Conductor creates follow-up beads; significant → present to user.
3.375. Dispatch `feature-finisher` — triage unresolved Feature Matrix rows, assign type/effort/recommendation, and write completion specs for findings at 50%+ completion. See `sdlc-os:sdlc-feature-sweep`.
3.5. Dispatch `normalizer` in Final Pass mode — cross-bead convention consistency sweep. Checks for naming drift between parallel beads, unmapped conventions, and Convention Map update needs.
3.75. Dispatch `losa-observer` on a random sample of merged beads (20% sample rate when error budget healthy, 50% when depleted). LOSA observations feed into error budget tracking — if LOSA reports uncaught errors, the error budget depletes regardless of SLI metrics.
3.875. Dispatch `reliability-ledger` — reads all bead turbulence fields, computes per-step first-pass rates (L0/L1/L2/L2.5/L2.75), identifies bottlenecks, compares against prior ledger entries. Appends results to `docs/sdlc/reliability-ledger.md`. See `references/reliability-ledger.md` for rate formulas and trend analysis rules.
3.9. Dispatch `llm-self-security` — audits the SDLC-OS workflow itself against OWASP LLM Top 10. Checks: prompt injection exposure, excessive agency (scope bleed), unbounded consumption (turbulence anomalies), insecure output handling, cross-agent independence violations. **Auto-triggered** (skip step number) when any bead in the task modified files in `agents/`, `hooks/`, `commands/`, `skills/`, or `references/`. See `references/standards-checklist.md` LLM-001 through LLM-006.
4. `haiku-handoff` packages delivery summary
5. **HRO Structural Constraints** (Weick — non-negotiable):

   **5a. Preoccupation with failure:** Every all-clean bead (zero findings across ALL loop layers) gets a mandatory "Why was this clean?" note in the decision trace. Clean results are suspicious until explained.

   **5b. Reluctance to simplify:** The delivery summary MUST contain at least one uncertainty, unknown, or open question. If the summary contains zero unknowns, flag as "suspiciously clean — reluctance-to-simplify gate failed." The Conductor cannot deliver a summary with zero unknowns.

   **5c. Sensitivity to operations:** Every 3rd bead, the Conductor reads raw sentinel logs, not just summaries. Logged in decision trace.

   **5d. Deference to expertise:** When a domain-specialist agent flags a finding, the Conductor CANNOT dismiss it — it MUST proceed to the corresponding Blue Team regardless of Conductor judgment. Conductor disagreement is logged in the decision trace for retrospective analysis, not used as a filter. Applies to ALL specialist agents: `red-functionality`, `red-security`, `red-usability`, `red-resilience`, `red-reliability-engineering`, `observability-engineer`, `error-hardener`.
**Output:** Delivery summary with fitness report, evidence, uncertainty, next actions, and Feature Matrix triage updates.

## How to Dispatch Runners

Each runner gets a precisely crafted context packet — never your full session history.

```
Agent tool:
  subagent_type: general-purpose
  model: sonnet
  mode: auto
  name: "runner-{bead-id}"
  description: "Bead {id}: {short description}"
  prompt: |
    You are a Runner executing one atomic work unit.

    ## Your Bead
    {full bead content — objective, scope, input, expected output}

    ## Context
    {relevant prior outputs — discovery findings, design decisions, etc.}
    {file paths and architectural hints — NOT your session history}

    ## Constraints
    - Stay within scope. Do not modify files outside your bead's scope.
    - If you need information not provided, report NEEDS_CONTEXT and stop.
    - If the bead is blocked by something unexpected, report BLOCKED and stop.
    - Submit your output in the required format, then exit.

    ## Output Format
    {format from the agent definition — varies by agent type}
```

**IMPORTANT: Always set `mode: auto`** for runners and sentinels. Without this, subagents start with an empty allow list under dontAsk mode — even when the parent session allows Write/Edit/Bash. `auto` inherits the parent's allow/deny lists and auto-approves without prompting. Do NOT use `bypassPermissions` — it skips deny lists and may skip hooks.

For Sentinel dispatch:
```
Agent tool:
  subagent_type: general-purpose
  model: haiku
  mode: auto
  name: "sentinel-{bead-id}"
  description: "Sentinel sweep: {what to check}"
  prompt: |
    You are the Sentinel. Review this runner's output for problems.

    ## Runner Output
    {paste the runner's complete output}

    ## Mission Brief
    {paste the acceptance criteria}

    ## Check For
    - Scope drift (did the runner go beyond or miss the bead's scope?)
    - Weak evidence (claims without proof)
    - Broken assumptions (things that were assumed but are wrong)
    - Regressions (did something else break?)
    - Missing work (did the runner skip something in the bead?)

    ## Output
    Use the verification report format from your agent definition.
```

## Parallelization Rules

Parallelization is determined via **FFT-12** from `references/fft-decision-trees.md`:

- Beads modifying the same file → **SERIALIZE**
- Bead B depends on bead A's output (explicit dependency) → **SERIALIZE**
- Both beads are read-only (investigation, audit, evolve) → **PARALLELIZE**
- Default → **PARALLELIZE** (independent beads run in parallel)

**Conflict resolution** (unchanged):
When parallel beads produce conflicting changes, the Conductor:
1. Reads both outputs
2. Dispatches a fresh runner with both outputs + conflict description
3. The resolver produces a merged result
4. Sentinel verifies the merge

## Complexity Scaling

**Clear** (< 5 min, single file, obvious approach):
- Skip Frame/Scout/Architect. Go straight to Execute with one bead.
- Sentinel does a quick post-check. Synthesize is just the delivery summary.

**Complicated** (multi-file, some ambiguity):
- Light Frame + Scout (one investigator, one sentinel sweep).
- Architect produces bead decomposition.
- Execute with parallel runners where possible.
- Full Synthesize.

**Complex** (multi-system, high risk, many unknowns):
- Full Frame + Scout with multiple parallel investigators.
- Architect with explicit tradeoff analysis and bead dependency graph.
- Execute with careful serialization of dependent beads.
- Sentinel patrols every bead output.
- Synthesize with reviewer + final sentinel sweep.

## Task Profiles

The Conductor assigns a task profile via FFT-01 before any other routing. The profile determines which phases run and at what depth. See `references/fft-decision-trees.md` FFT-01 and FFT-04 for the full decision trees.

| Profile | When | Phases Active | AQS | Hardening | Bead Type |
|---------|------|---------------|-----|-----------|-----------|
| BUILD | Default — new features, enhancements | All | Per Cynefin | Per FFT-09 | implement |
| INVESTIGATE | Research, codebase understanding, no code changes | Frame + Heavy Scout + Read-Only Execute | SKIP | SKIP | investigate |
| REPAIR | Targeted bug fix, failing test, specific defect | Minimal Scout + Execute + Harden | Resilience only | Full | implement |
| EVOLVE | System self-improvement, quality budget recovery | Evolution beads only | SKIP | SKIP | evolve |

**REPAIR profile STPA note:** REPAIR beads skip Phase 3 (Architect). For REPAIR beads where the STPA skip rule applies (COMPLEX or security_sensitive), `safety-analyst` runs at pre-Execute as an inline mini-Architect step for safety analysis only — before runners are dispatched. This populates `control_actions` and `unsafe_control_actions` on the bead before execution begins.

Evolve beads follow a shortened status flow: `pending → running → submitted → verified → merged` (skip proven/hardened/reliability-proven — no user code to verify adversarially).

See `sdlc-os:sdlc-evolve` for the full Evolve profile specification.

## Recovery Patterns

Recovery is handled by the loop system (`sdlc-os:sdlc-loop`). Each level self-corrects before escalating:

- **L0 (Runner):** Runner reads its own error output and self-corrects. Budget: 3 attempts.
- **L1 (Sentinel):** Sentinel produces specific correction directives. Fresh runner addresses them. Budget: 2 cycles.
- **L2 (Oracle):** Oracle flags test deficiencies. Runner fixes tests specifically. Budget: 2 cycles.
- **L3 (Bead):** If any inner loop exhausts budget, bead escalates to Conductor.
- **L4 (Phase):** Conductor re-decomposes, provides context, changes design, or escalates to user.
- **L5 (Task):** If 3 full passes fail, deliver what you have + explicit gap report.

**Naked escalation is forbidden.** Every escalation includes what was tried, why it failed, and what the target should consider. See `sdlc-os:sdlc-loop` for the complete loop specification including correction signal format, budget table, and backpressure cascade.

## State Management

### Initialize
When starting a new task:
1. Create `docs/sdlc/active/{task-id}/` directory
2. Write `state.md` with task metadata
3. Create `beads/` subdirectory for work units

### Scout Artifacts
After Scout phase completes, the task directory contains:
- `state.md` — task metadata and phase log
- `beads/` — work unit files
- `standards-profile.md` — project-specific standards profile from `standards-curator` (persists across sessions)
- `quality-budget.md` — SLI/SLO tracking (created during Synthesize, read during subsequent tasks)
- `observability-profile.md` — project observability stack (created during Harden, if reached)

### Track
After each runner completes:
1. Update the bead file with output and status
2. Update `state.md` with current phase and progress
3. If sentinel flagged issues, record in bead's sentinel notes

### Complete
When all beads are proven, hardened (or AQS-skipped), and merged:
1. Write `delivery.md` — the final handoff summary
2. Move task directory from `active/` to `completed/` (optional)

## Anti-Patterns

- **Sequential approval ceremonies** — Don't wait for formal "GO" decisions between phases. Flow as fast as the work allows.
- **Context accumulation** — Don't let runners inherit your session history. Craft precise context packets.
- **Single-threaded execution** — If beads are independent, dispatch runners in parallel.
- **Sentinel as gatekeeper** — The sentinel advises. You decide. Don't create approval bottlenecks.
- **Over-decomposition** — Don't create 20 beads for a 3-file change. Match decomposition to complexity.
- **Under-supervision** — Don't skip sentinel checks on "simple" work. Problems hide in simple changes.

## Quick Reference

| Phase | Runners | Sentinel | Oracle | Reuse/Fitness/Convention | Conductor |
|-------|---------|----------|--------|-------------------------|-----------|
| Normalize | normalizer | — | — | convention-scanner (if needed) | Detect state, approve directives |
| Frame | sonnet-investigator | haiku-evidence | — | — | Define mission, scope, criteria |
| Scout | sonnet-investigator + convention-scanner + gap-analyst (Finder) | haiku-evidence | — | — | Gather context, map conventions, find gaps |
| Architect | sonnet-designer | haiku-verifier | — | — | Choose approach, create bead manifest |
| Execute | sonnet-implementer (parallel OK) | haiku-verifier + drift-detector + convention-enforcer | oracle L1+L2 (per bead) | reuse-scout (pre-dispatch) | Distribute beads, recover failures |
| Synthesize | sonnet-reviewer + gap-analyst (Finisher) + normalizer (Final Pass) + losa-observer | haiku-handoff | oracle L1+L2+L3 (integration) | fitness report (full, includes Conventions) | Merge results, deliver |
