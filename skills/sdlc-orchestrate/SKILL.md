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
- **Trivial beads:** Oracle Layer 1 only (Sonnet static check). Cheap, fast.
- **Moderate beads:** Oracle Layers 1 + 2 (Sonnet static + Haiku runtime proof). Standard rigor.
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
  - **Trivial beads:** Skip AQS entirely. Beads go `proven → merged`.
  - **Moderate beads:** Recon burst + Conductor selects 1-2 domains.
  - **Complex beads:** All four domains active.
  - **Security-sensitive beads:** All four domains, security always HIGH.

## Work Units (Beads)

Every piece of work is tracked as an atomic unit:

```markdown
# Bead: {id}
**Status:** pending | running | submitted | verified | proven | hardened | merged | blocked
**Type:** investigate | design | implement | verify | review
**Runner:** [agent name or "unassigned"]
**Dependencies:** [list of bead IDs that must complete first]
**Scope:** [files/areas this bead touches — used for conflict detection]
**Input:** [what context the runner needs]
**Output:** [what the runner must produce]
**Sentinel notes:** [anything the sentinel flagged]
```

Beads are written to `docs/sdlc/active/{task-id}/beads/` as individual markdown files. They persist in Git — surviving agent sessions, crashes, and context resets.

## Workflow Phases (Lightweight, Not Gates)

Phases exist for orientation, not approval. The Conductor flows through them as fast as the work allows.

### Phase 1: Frame
**What:** Understand the task. Clarify ambiguity. Define done.
**How:** Dispatch `sonnet-investigator` to analyze requirements. Sentinel checks for gaps.
**Output:** Mission brief with objective, scope, constraints, success criteria.
**Skip when:** Task is trivial and well-specified.

### Phase 2: Scout
**What:** Gather evidence about the codebase and problem space.
**How:** Dispatch `sonnet-investigator` to explore. Sentinel validates evidence quality.
**Output:** Discovery brief with findings, evidence, assumptions labeled.
**Skip when:** You already have sufficient context (e.g., from prior conversation).
**Parallelize:** Multiple investigators can scout different areas simultaneously.

### Phase 3: Architect
**What:** Choose an approach. Define the bead decomposition.
**How:** Dispatch `sonnet-designer` to produce options. Conductor selects.
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
   - Oracle audits test integrity (L2)
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
**Output:** Code changes, tests, validation notes, reuse reports per bead.
**Recovery:** Handled by loop mechanics. See `sdlc-os:sdlc-loop`.

### Phase 5: Synthesize
**What:** Merge all runner outputs. Resolve conflicts. Verify the whole.
**How:**
1. Run **fitness check** (`sdlc-os:sdlc-fitness`) across all changed files — full report
2. Dispatch `sonnet-reviewer` for critical assessment of the integrated result
3. Dispatch `drift-detector` for final cross-bead duplication check
4. `haiku-handoff` packages delivery summary
**Output:** Delivery summary with fitness report, evidence, uncertainty, next actions.

## How to Dispatch Runners

Each runner gets a precisely crafted context packet — never your full session history.

```
Agent tool:
  subagent_type: general-purpose
  model: sonnet
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

For Sentinel dispatch:
```
Agent tool:
  subagent_type: general-purpose
  model: haiku
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

**Safe to parallelize:**
- Beads touching different files/modules
- Investigation beads (read-only)
- Independent test authoring

**Must serialize:**
- Beads modifying the same file
- Implementation that depends on a design decision
- Beads with explicit dependency links

**Conflict resolution:**
When parallel beads produce conflicting changes, the Conductor:
1. Reads both outputs
2. Dispatches a fresh runner with both outputs + conflict description
3. The resolver produces a merged result
4. Sentinel verifies the merge

## Complexity Scaling

**Trivial** (< 5 min, single file, obvious approach):
- Skip Frame/Scout/Architect. Go straight to Execute with one bead.
- Sentinel does a quick post-check. Synthesize is just the delivery summary.

**Moderate** (multi-file, some ambiguity):
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

| Phase | Runners | Sentinel | Oracle | Reuse/Fitness | Conductor |
|-------|---------|----------|--------|---------------|-----------|
| Frame | sonnet-investigator | haiku-evidence | — | — | Define mission, scope, criteria |
| Scout | sonnet-investigator (parallel OK) | haiku-evidence | — | — | Gather context, label assumptions |
| Architect | sonnet-designer | haiku-verifier | — | — | Choose approach, create bead manifest |
| Execute | sonnet-implementer (parallel OK) | haiku-verifier + drift-detector | oracle L1+L2 (per bead) | reuse-scout (pre-dispatch) | Distribute beads, recover failures |
| Synthesize | sonnet-reviewer | haiku-handoff | oracle L1+L2+L3 (integration) | fitness report (full) | Merge results, deliver |
