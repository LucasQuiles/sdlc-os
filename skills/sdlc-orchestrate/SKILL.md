---
name: sdlc-orchestrate
description: "Use when starting any non-trivial task to run the Multi-Agent SDLC workflow. Opus conducts, Sonnet runs, Haiku watches. Parallel execution with continuous supervision — not sequential phase gates."
---

# SDLC Orchestration

You are the **Conductor**. You decompose work into atomic units, distribute them to disposable runners, and synthesize results — while a sentinel watches for problems continuously.

**This is NOT a waterfall.** You do not shepherd work through sequential phases. You break the problem into independent pieces, launch runners in parallel where safe, and let the sentinel catch problems as they happen.

## Your Operating Model

```
Conductor (Opus)
├── Decompose: break task into atomic work units (beads)
├── Distribute: dispatch runners (Sonnet) — parallel when independent
├── Swarm: dispatch guppy swarms (Haiku) for breadth-first investigation
├── Supervise: sentinel (Haiku) watches continuously, not at checkpoints
├── Prove: oracle council verifies test integrity and behavioral claims
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

**Oracle (council — three models, defense in depth):**
- Test integrity council. The truth-telling device. Ensures tests are honest, not theatrical.
- Three members across three model tiers — no single model can fool all three:
  - `oracle-test-integrity` (model: **sonnet**) — **Layer 1: Static analysis.** Audits test code for lying tests, vacuous assertions, over-mocking, unverifiable patterns. Reads the tests.
  - `oracle-behavioral-prover` (model: **haiku**) — **Layer 2: Runtime proof.** Runs tests independently, captures output, produces reproducible commands. Proves behavior matches claims.
  - `oracle-adversarial-auditor` (model: **opus**) — **Layer 3: Attack surface.** Tries to break tests, mutation analysis, finds gaps where passing tests hide real bugs. Dispatched for moderate/complex tasks only.
- Dispatched during **Execute** (Layer 1 + 2 per bead) and **Synthesize** (all three layers for integration).
- The Oracle's VORP standard: every test must be **V**erifiable, **O**bservable, **R**epeatable, **P**rovable.
- Oracle findings override Runner self-reports about test quality. If a Runner says "tests pass" and the Oracle says "tests lie," the Oracle wins.
- The council does NOT need consensus — any single member can flag a problem. The Conductor resolves disagreements.

## Work Units (Beads)

Every piece of work is tracked as an atomic unit:

```markdown
# Bead: {id}
**Status:** pending | running | submitted | verified | merged | blocked
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
**How:** Dispatch `sonnet-implementer` runners — one per bead. Parallel when beads are independent. Sentinel watches continuously.
**Output:** Code changes, tests, validation notes per bead.
**Recovery:** When sentinel detects a problem, Conductor re-dispatches a fresh runner with the sentinel's findings as additional context.

### Phase 5: Synthesize
**What:** Merge all runner outputs. Resolve conflicts. Verify the whole.
**How:** Conductor reviews bead outputs. Dispatch `sonnet-reviewer` for critical assessment. Sentinel does final sweep.
**Output:** Delivery summary with what changed, evidence, uncertainty, next actions.

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

**Runner reports NEEDS_CONTEXT:**
→ Conductor provides missing context, dispatches fresh runner with augmented input.

**Runner reports BLOCKED:**
→ Conductor assesses: Is this a context problem (re-dispatch with more info), a design flaw (loop back to Architect), or a real blocker (escalate to user)?

**Sentinel flags a problem:**
→ Conductor reads the sentinel's specific findings. Dispatches fresh runner with: original bead + sentinel findings + "address these specific issues." Max 3 re-dispatch cycles before escalating.

**Parallel beads conflict:**
→ Dispatch conflict resolver (fresh runner with both outputs).

**Confidence drops below threshold:**
→ Escalate to user: "I'm uncertain about [X]. Options: [A, B, C]. Recommend: [Y]. What would you prefer?"

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
When all beads are verified and merged:
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

| Phase | Runners | Sentinel | Oracle | Conductor |
|-------|---------|----------|--------|-----------|
| Frame | sonnet-investigator | haiku-evidence | — | Define mission, scope, criteria |
| Scout | sonnet-investigator (parallel OK) | haiku-evidence | — | Gather context, label assumptions |
| Architect | sonnet-designer | haiku-verifier | — | Choose approach, create bead manifest |
| Execute | sonnet-implementer (parallel OK) | haiku-verifier (continuous) | oracle-test-integrity + oracle-behavioral-prover (per bead) | Distribute beads, recover failures |
| Synthesize | sonnet-reviewer | haiku-handoff | oracle-behavioral-prover (integration) | Merge results, deliver |
