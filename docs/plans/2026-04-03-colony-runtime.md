# Colony Runtime Implementation Plan

**Goal:** Build a persistent multi-agent colony runtime that bridges sdlc-os beads with tmup task DAG execution, enabling parallel worker dispatch, cross-session correction loops, and autonomous orchestration via a systemd-managed Deacon daemon.

**Architecture:** Deacon (Python daemon) watches tmup SQLite DB for state changes and spawns ephemeral Conductor sessions (Claude Code CLI, Opus). Conductors create tmup tasks from beads, dispatch workers (Claude Code or Codex) into isolated git clones via tmux panes, evaluate completed work, and advance beads through L0-L5 quality loops. A deterministic TypeScript Bridge synchronizes tmup task completion to bead markdown files atomically. All colony features are additive -- sync mode (no Deacon, no tmup) continues to work unchanged.

**Tech Stack:** TypeScript (tmup plugin, Bridge), Python 3.12 + asyncio (Deacon), Bash (clone manager, dispatch), SQLite WAL, systemd user services, tmux, Claude Code CLI, Codex CLI

**Spec:** `docs/specs/2026-04-03-colony-runtime-design.md` (681 lines, v2, council-reviewed)

---

## Section 0: Execution Controller

This section IS the plan entry point. An agent executing this plan reads THIS FIRST, then follows its instructions. Everything below is reference material -- the controller decides what to run and when.

### Dependency DAG

```
T0 (Validation Spike)
 |
 v
T0.5 (Infrastructure Bootstrap)
 |
 v
T1 (tmup Worker Polymorphism)
 |
 +------+------+
 |             |
 v             v
T2 (Git)    T3 (Bridge)    <-- sequential (council S4)
 |             |
 +------+------+
        |
        v
T4 (Conductor Protocol)
        |
        v
T5 (Deacon Service)
        |
        v
    FINAL VERIFICATION
```

### Progress File

All state lives in `colony/PROGRESS.md`. The controller creates it at start and updates it at every gate. This file is the ONLY thing the controller reads between sessions to know where it is.

```markdown
# Colony Runtime Progress
## Format Version: 1

## Current State
**Active trunk:** T1
**Blocked on:** nothing
**Last gate passed:** T0.GATE (2026-04-03T14:22Z)
**Next action:** Start T1.1
**Session count:** 2

## Gate Log
| Gate | Status | Timestamp | Fitness | Notes |
|------|--------|-----------|---------|-------|
| T0.GATE | PASS | 2026-04-03T14:22Z | n/a | 6/6 validations passed |
| T1.GATE | PASS | 2026-04-04T09:15Z | PASS | All tests green, no drift |

## Correction Log
| Trunk | Task | Loop Level | Cycle | Finding | Resolution |
|-------|------|-----------|-------|---------|------------|

## Safety Constraint Verification
| SC-COL-* | Trunk | Verified | Evidence |
|----------|-------|----------|----------|
```

### SDLC-OS Skill Integration Map

Every automation touch point in the controller loop maps to an sdlc-os skill or agent. The controller MUST invoke these -- they are not optional.

| Touch Point | Skill / Agent | When | Purpose |
|-------------|--------------|------|---------|
| **SESSION LIFECYCLE** | | | |
| Session entry | `sdlc-os:sdlc-normalize` | Second action (after PROGRESS.md direct read) | Convention checking only — NOT resume |
| Worktree isolation | `superpowers:using-git-worktrees` | T0 start (once) | Isolated workspace for colony development |
| Branch completion | `superpowers:finishing-a-development-branch` | After FINAL VERIFICATION | Merge/PR/cleanup the development branch |
| **PRE-TRUNK** | | | |
| Reuse check | `sdlc-os:sdlc-reuse` | Before starting T1, T2, T3, T5 | Prevent reinventing existing code |
| Duplicate scan | `superpowers-lab:finding-duplicate-functions` | Before T1, T3 (code-heavy trunks) | Detect semantic duplication before adding more |
| **TASK EXECUTION** | | | |
| Task dispatch | `superpowers:subagent-driven-development` | Each task within a trunk | Fresh agent per task + two-stage review |
| TDD enforcement | `superpowers:test-driven-development` | Every code task (T1.3-T1.7, T2.1, T3.1-T3.3, T5.1) | Red-green-refactor -- no code without failing test first |
| Cross-codebase nav | `progressive-disclosure-coding` | Tasks touching tmup+sdlc-os integration (T1.6, T1.7, T2.2) | Trace call chains across plugin boundaries |
| Task verification | `superpowers:verification-before-completion` | Before marking any task done | Evidence before claims, always |
| **TRUNK GATES** | | | |
| Health check | `sdlc-os:sdlc-gate` | At each T*.GATE | Confidence assessment |
| Fitness audit | `sdlc-os:sdlc-fitness` | At T1.GATE, T3.GATE, T5.GATE | DRY, SSOT, SoC, convention, boundary |
| Drift detection | `drift-detector` agent | At each gate (via sdlc-fitness) | Catch DRY violations, arch drift |
| Convention check | `convention-enforcer` agent | At each gate (via sdlc-fitness) | Naming, styling, structure |
| Safety constraints | `safety-constraints-guardian` agent | At T3.GATE, T5.GATE | Verify SC-COL-* implementation |
| **CROSS-MODEL** | | | |
| Codex independent review | `sdlc-os:sdlc-crossmodel` | Post-T3, Post-T5, Final | Inter-model adversarial — Codex workers in tmux grid review code independently. crossmodel-triage deduplicates. Net-new findings = HIGH corrections. |
| **GATE FAILURE** | | | |
| Correction loop | `sdlc-os:sdlc-loop` | When any gate fails | L1/L2 correction with budget tracking |
| Debugging | `superpowers:systematic-debugging` | When gate failure is non-obvious | Root cause investigation, not guess-and-check |
| Review feedback | `superpowers:receiving-code-review` | When code review flags issues | Technical evaluation, not performative agreement |
| **POST-TRUNK HOOKS** | | | |
| Post-T3 adversarial | `sdlc-os:sdlc-adversarial` | After T3.GATE passes | Bridge red/blue team probe |
| Post-T5 hardening | `sdlc-os:sdlc-harden` | After T5.GATE passes | Premortem, error hardening, WYSIATI |
| **FINAL VERIFICATION** | | | |
| Gap analysis | `sdlc-os:sdlc-gap-analysis` | After all trunks | Finisher mode: spec vs implementation |
| Code review | `superpowers:requesting-code-review` | After all trunks | Cross-trunk integrated review |
| Review response | `superpowers:receiving-code-review` | On review findings | Rigorous technical evaluation of feedback |
| **DOMAIN-SPECIFIC** | | | |
| DB patterns | `database-patterns` | T1.3 (migration), T3.2 (bridge writes) | SQLite WAL patterns, transaction safety |
| TS project setup | `typescript-project-init` | If new TS package needed in colony/ | Consistent tsconfig, vitest, eslint |
| Python project setup | `python-project-init` | T5.1 (deacon.py setup) | Consistent pytest, mypy, ruff, black |
| Plugin development | `superpowers-developing-for-claude-code:developing-claude-code-plugins` | T1 (tmup mods), T4 (skill changes) | Plugin manifest, relative paths, ${CLAUDE_PLUGIN_ROOT} |
| Claude Code reference | `superpowers-developing-for-claude-code:working-with-claude-code` | T4 (conductor prompt), T1.7 (claude -p flags) | CLI flags, plugin loading, MCP server patterns |


### Agent Dispatch Map (Load-Bearing Only)

Trimmed to ~12 essential agents per council simplicity audit. Agents not listed here are NOT dispatched.

**T1 — tmup Worker Polymorphism:**
| Step | Agent | Why |
|------|-------|-----|
| T1.7 (dispatch script) | `sonnet-investigator` (sonnet) | Investigate existing dispatch-agent.sh patterns before modifying |

**T2 — Git Isolation:**
| Step | Agent | Why |
|------|-------|-----|
| T2.1 (clone-manager) | `safety-analyst` (sonnet) | Clone lifecycle is safety-critical — STPA on clone create/verify/prune |

**T3 — Bead-Task Bridge (safety-critical):**
| Step | Agent | Why |
|------|-------|-----|
| T3.2 (bridge core) | `error-hardener` (sonnet) | Bridge needs exhaustive error handling |
| T3.3 (git commit) | `red-security` (sonnet) | Probe for injection vectors in git operations |
| T3.GATE | `oracle-test-integrity` (sonnet) | Verify bridge tests aren't vacuous |
| T3.GATE | `oracle-adversarial-auditor` (opus) | Bridge is COMPLEX+security — try to break it |
| Post-T3 | Red/blue teams + `arbiter` (via sdlc-adversarial) | Full AQS cycle on bridge (managed by skill) |
| Post-T3 | **Codex cross-model review** (via sdlc-crossmodel) | Independent Codex review of bridge — inter-model adversarial leverage. Codex workers in tmux grid review bridge.ts, bead-parser.ts, bridge.test.ts. Findings deduplicated via `crossmodel-triage` against AQS results. Net-new findings escalated as HIGH. |

**T4 — Conductor Protocol:**
| Step | Agent | Why |
|------|-------|-----|
| T4.1 (conductor prompt) | `llm-self-security` (haiku) | MANDATORY — audit prompt for injection, excessive agency (STPA L-4) |

**T5 — Deacon Service:**
| Step | Agent | Why |
|------|-------|-----|
| T5.1 (state machine) | `safety-analyst` (sonnet) | STPA on deacon control actions |
| T5.2 (async loop) | `error-hardener` (sonnet) | Exhaustive error handling in daemon loop |
| Post-T5 | Hardening via sdlc-harden skill | Premortem, error hardening, WYSIATI (managed by skill) |
| Post-T5 | **Codex cross-model review** (via sdlc-crossmodel) | Independent Codex review of deacon.py — Python-specific blind spots that Claude may miss. Codex reviews state machine logic, recovery paths, subprocess command construction. |

**FINAL VERIFICATION:**
| Step | Agent | Why |
|------|-------|-----|
| Final | `gap-analyst` (sonnet) | Finisher mode — spec SS1-SS13 vs committed code |
| Final | `sonnet-reviewer` (sonnet) | Critical review of integrated tmup + sdlc-os + colony system |
| Final | **Codex cross-model sweep** (via sdlc-crossmodel) | Full codebase sweep — Codex workers review ALL colony/ files + tmup modifications. Stage A: investigator finds issues independently. Stage B: independent review validates/challenges Claude's implementation. `crossmodel-triage` deduplicates. Net-new = HIGH priority corrections before COMPLETE. |

### Controller Loop

```
ENTRY:
  1. READ colony/PROGRESS.md directly (simple file read)
     - If missing: create it with `## Format Version: 1` header, start at T0
     - If exists: validate format (required fields: Active trunk, Next action, Format Version)
     - If format invalid or unparseable: treat as fresh start (T0), warn
     - Parse: Active trunk, Next action, Correction cycle counts (total across all sessions)
     - Cross-validate: verify last gate's trunk has commits in git log
     - If mismatch between PROGRESS.md and git: warn, re-gate (don't re-execute)
     - THEN invoke sdlc-os:sdlc-normalize for convention checking only

TRUNK LOOP:
  2. FOR EACH trunk T in [T0, T0.5, T1, T2, T3, T4, T5]:
     a. PRE-TRUNK (skip for T0, T0.5, T4):
        - Invoke sdlc-os:sdlc-reuse (6-layer reuse analysis)
        - Inject reuse report into task context
     b. EXECUTE tasks sequentially via superpowers:subagent-driven-development:
        - Fresh subagent per task + two-stage review
        - Subagents MUST use superpowers:test-driven-development for code tasks
        - Each task: commit on completion
        - On failure: diagnose, fix, retry (max 3)
        - Still failing: write to PROGRESS.md correction log, stop
        - Dispatch named agents from Agent Map at their specified steps
     c. GATE (superpowers:verification-before-completion + sdlc-os:sdlc-fitness for T1/T3/T5):
        - Run ALL gate commands, read output, verify against expected
        - Fitness: DRY, convention, boundary checks (BLOCKING score -> correct first)
        - Backward compat: all pre-existing tmup tests still pass
        - Safety: cross-ref SC-COL-* coverage table for this trunk
     d. ON GATE FAIL -> sdlc-os:sdlc-loop:
        - L1: targeted fix, re-gate. Max 2 L1 cycles per gate
        - L2: oracle investigation if L1 exhausted. Max 1 L2 per gate
        - Write cycle count to PROGRESS.md IMMEDIATELY after each cycle
        - BLOCKED after budget: stop, escalate
        - Total plan correction budget: 6 L1 + 2 L2 across ALL trunks
     e. ON GATE PASS:
        - Write PROGRESS.md (trunk, timestamp, fitness score) + git commit ATOMICALLY
        - Single command: write file, git add, git commit (no crash window)

  3. POST-TRUNK HOOKS (inline after specific gates):
     - After T3.GATE: write AQS_STARTED to PROGRESS.md, then invoke sdlc-os:sdlc-adversarial
       (red/blue/arbiter on bridge -- safety-critical, non-negotiable)
     - After T3 AQS: invoke sdlc-os:sdlc-crossmodel on bridge (Codex independent review)
       Codex workers in tmux grid examine bridge.ts, bead-parser.ts independently.
       crossmodel-triage deduplicates against AQS findings. Net-new -> correct before T4.
     - After T5.GATE: invoke sdlc-os:sdlc-harden (premortem, error hardening, WYSIATI)
     - After T5 harden: invoke sdlc-os:sdlc-crossmodel on deacon.py (Codex Python review)

  4. FINAL VERIFICATION:
     - sdlc-os:sdlc-gap-analysis (finisher: spec SS1-SS13 vs committed code)
     - sdlc-os:sdlc-crossmodel (full Codex sweep of all colony/ + tmup changes)
     - superpowers:requesting-code-review (cross-trunk integration review)
     - Correct any net-new Codex findings before proceeding
     - Write COMPLETE to PROGRESS.md with total cost + correction count

EXIT.
```

**Skills invoked (11 total):** normalize, sdlc-reuse, subagent-driven-development (with TDD), verification-before-completion, sdlc-fitness, sdlc-loop, sdlc-adversarial, sdlc-crossmodel (Codex inter-model), sdlc-harden, sdlc-gap-analysis, requesting-code-review.

**Correction budget:** 2 L1 + 1 L2 per gate. 6 L1 + 2 L2 total across plan. Cycle count persisted in PROGRESS.md after every cycle. Total plan budget cap: $200.

### Session Boundaries

This plan spans multiple agent sessions. The controller survives because:

1. All state in `colony/PROGRESS.md` (file, not memory)
2. All code committed at each task (git log = audit trail)
3. New session reads PROGRESS.md directly, then cross-validates against git log

A new session's FIRST action is ALWAYS: read `colony/PROGRESS.md` directly (step 1 of controller loop). THEN invoke `sdlc-os:sdlc-normalize` for convention checking only — normalize does NOT handle resume.

### Gate Failure Protocol

When a GATE fails, the controller invokes `sdlc-os:sdlc-loop`:

1. **L1 (Sentinel):** Read failure output. Classify (test/build/env). Targeted fix. Re-gate.
2. **L2 (Oracle):** If L1 fails twice, dispatch oracle council for deeper analysis. Three-member review of what went wrong.
3. **BLOCKED:** If L2 exhausted, update PROGRESS.md, stop. Do not skip gates.

Correction budget per gate: 2 L1 cycles, 1 L2 cycle. After that, human intervention required.

### Alignment Invariants

Checked at EVERY gate (enforced by sdlc-fitness):

1. **Backward compat:** `npx vitest run` (tmup) passes all pre-existing tests
2. **Safety constraints:** SC-COL-* assigned to completed trunks verified in code
3. **No scope creep:** Changes not in File Structure table -> plan gap (update) or creep (reject)
4. **Convention adherence:** Naming, file location, import patterns match existing codebase
5. **No duplication:** New code doesn't duplicate existing tmup/sdlc-os functionality


---

## Council Verdict (2026-04-03)

Four council members reviewed this plan: Oracle Test Integrity, Oracle Adversarial Auditor, Simplicity Auditor, Safety Analyst (STPA). Consolidated findings below with dispositions.

### CRITICAL — Must Fix Before Execution

| # | Finding | Source | Fix |
|---|---------|--------|-----|
| C1 | sdlc-os has ZERO TypeScript infrastructure — no package.json, tsconfig, vitest. `npx vitest run colony/` guaranteed crash at T3.GATE. Similarly no Python test infra (pytest, pyproject.toml) for T5. | Adversarial | Add T0.7: Bootstrap sdlc-os colony/ as TS+Python sub-package (package.json, tsconfig.json, vitest.config.ts, pyproject.toml with pytest). Run before T1. |
| C2 | SQLite CHECK constraint on `execution_targets` table blocks `'claude_code'` type. Migration v3 hardcoded `CHECK (type IN ('tmux_pane','local_shell','codex_cloud'))`. Migration v4 never fixes this. Runtime INSERT will fail silently. | Adversarial | Option A: Migration v4 recreates execution_targets with expanded CHECK. Option B (simpler): Don't use execution_targets for Claude Code workers — use `worker_type` column on tasks only. Drop T1.1's ExecutionTargetType modification. **Accept Option B.** |
| C3 | Session resume is fictional — `sdlc-normalize` has no knowledge of PROGRESS.md. New sessions will restart from scratch. | Adversarial | Controller step 1 reads PROGRESS.md directly (simple file read + field parse). Do NOT depend on sdlc-normalize for resume. Normalize runs AFTER for convention checking only. |
| C4 | Correction cycle count lost on session restart — enables unbounded correction loop (L-1 loss scenario). PROGRESS.md correction log not written atomically with each cycle. | Safety (STPA) | Write correction cycle count to PROGRESS.md IMMEDIATELY after each L1/L2 cycle, before any other action. Controller reads total count across all sessions, not per-session. Add max total correction budget: 6 L1 + 2 L2 across entire plan. |
| C5 | Missing spec sections with no implementing task: SS6.2 Sequential Merge, SS7.2 RECOVER session, SS4.8 bead-context.md write, SS8 Clear bead fast path, SS9.2 per-phase validation checks. | Test Integrity | Add micro-tasks: T4.4 (SYNTHESIZE merge logic + RECOVER session in conductor prompt), T4.5 (bead-context.md write protocol). Mark SS8 Clear fast path as out-of-scope v1 (optimization). Add SS9.2 checks to respective gate tasks. |
| C6 | Missing safety constraints: SC-COL-06 (check bridge lock before SIGTERM) and SC-COL-13 (cancel stale tasks before retry) referenced in spec prose but absent from plan coverage table. | Test Integrity | Add SC-COL-06 to T5.2 (Deacon SIGTERM logic). Add SC-COL-13 to T4.1 (Conductor prompt EVALUATE logic). Update coverage table. |

### HIGH — Simplicity Cuts (Accept)

The simplicity auditor scored the plan 2/5. The core trunks (T0-T5) are proportionate but the controller wrapping is bloated. Accept these cuts:

| # | Cut | Rationale |
|---|-----|-----------|
| S1 | Collapse controller loop from 14 steps to 6 | 27 skill invocations for 5 trunks is process theater. Core loop: normalize -> for each trunk { reuse-check -> execute -> gate -> on-fail: correct } -> final review -> done. |
| S2 | Cut agent dispatch map from 40 to ~12 load-bearing agents | Keep: sonnet-implementer (tasks), safety-analyst (T2.1, T5.1), error-hardener (T3.2, T5.2), red/blue teams + arbiter (T3 adversarial), oracle council (T3.GATE), llm-self-security (T4.1), sonnet-reviewer (final). Cut: convention-scanner (redundant with convention-enforcer at gates), losa-observer, process-drift-monitor, reliability-ledger, haiku-handoff, observability-engineer, reliability-conductor, reuse-scout (covered by sdlc-reuse skill). |
| S3 | Collapse T0 from 7 tasks to 2 | T0.1: batch validation script (all 6 checks). T0.GATE: verify 6/6 pass. Done in hours, not days. |
| S4 | Remove explicit parallel T2+T3 claim | Controller serializes them anyway. Remove the lie. T2 then T3 sequentially. |
| S5 | Collapse final verification from 6 agents to 2 steps | Gap analysis (finisher) + code review. Remove losa-observer, process-drift-monitor, reliability-ledger, haiku-handoff. |
| S6 | Skills required at gates: 3 not 5 | Gate = verification-before-completion + sdlc-fitness (code trunks only). Remove separate sdlc-gate invocation (redundant when fitness runs). |

### HIGH — Safety Mitigations (Add)

| # | Mitigation | Source | Implementation |
|---|-----------|--------|----------------|
| M1 | PROGRESS.md write must be atomic with git commit | STPA L-3 | Write + `git add colony/PROGRESS.md && git commit` as single bash command. No crash window between write and commit. |
| M2 | Controller must cross-validate PROGRESS.md against git log on resume | STPA L-3 | On resume: verify last gate's claimed trunk has corresponding commits in git log. If mismatch, warn and re-gate (don't re-execute). |
| M3 | `origin/HEAD` fallback in clone-manager | Adversarial #12 | Use `origin/main` or `origin/$(git -C source symbolic-ref --short HEAD)` instead of `origin/HEAD` which may not exist for file:// clones. |
| M4 | Cross-plugin path resolution for clone-manager.sh | Adversarial #4 | Pass clone-manager.sh path via `--clone-manager-path` argument to dispatch-agent.sh, not hardcoded. Default: `${SDLC_OS_PLUGIN:-/home/q/.claude/plugins/sdlc-os}/colony/clone-manager.sh`. |
| M5 | Deacon CLI command construction test | Adversarial #5 (mutation) | T5.1 test must capture the actual `claude -p` command string from spawn_conductor() and assert it contains `--max-budget-usd`, `--permission-mode bypassPermissions`, both `--plugin-dir` flags, and `--model opus`. |
| M6 | AQS checkpoint before post-T3 adversarial | Adversarial #7 | Write `AQS_STARTED` to PROGRESS.md before launching adversarial sweep. On session resume, detect incomplete AQS and re-run. |
| M7 | Total plan budget cap | Adversarial #13 | Add `TOTAL_PLAN_BUDGET_USD=200` to PROGRESS.md header. Controller tracks aggregate cost. Halt and escalate if exceeded. |

### MEDIUM — Line Number Corrections

| Claim | Stated | Actual | Fix |
|-------|--------|--------|-----|
| migrations.ts "~line 280" (spec) | ~280 | 258 | Correct to ~258 |
| migrations.ts closing `];` (plan T1.3) | 258 | 259 | Correct to 259 |
| types.ts "after line 101" (plan T1.1) | 101 | 100 | Correct to 100 |
| tmup_dispatch handler location | not mentioned | 631 | Add to T1.6 |

### MEDIUM — Prompt-Enforced Constraints

SC-COL-04, SC-COL-09, SC-COL-10 are enforced by LLM prompt instruction (conductor-prompt.md), not code. No deterministic test exists. Acknowledged as inherent to the architecture — these are Conductor behavioral constraints. Layer 4 integration tests (spec SS9.5) are the verification point. Note this explicitly in the plan.

### Rejected Simplicity Cuts

| Cut Proposed | Rejection Reason |
|-------------|-----------------|
| Remove bridge.ts (bridge is unnecessary) | Adversarial auditor found 4 CRITICALs in the bridge path in the SPEC council. Bridge is load-bearing. |
| Consolidate PROGRESS.md into tmup task DAG | PROGRESS.md tracks plan-level state (trunk position, correction budget) that is orthogonal to task-level state. tmup tracks tasks; PROGRESS.md tracks the plan controller. Different concerns. |
| Remove sdlc-reuse pre-trunk check | Reuse-scout prevents rebuilding existing functionality. Cost: ~$0.20 per invocation. Value: prevents $5+ of wasted implementation. Keep. |
| Remove sdlc-adversarial post-T3 | Bridge is the safety-critical data integrity layer. Red/blue team is non-negotiable for safety-critical code. Keep, but add AQS checkpoint (M6). |


---

## TRUNK INDEX

| # | Trunk | Branch Count | Est. Days | Deps |
|---|-------|-------------|-----------|------|
| T0 | Validation Spike | 2 branches | 0.5 | None |
| T0.5 | Infrastructure Bootstrap | 1 branch | 0.5 | T0 |
| T1 | tmup Worker Polymorphism | 8 branches | 3-5 | T0, T0.5 |
| T2 | Git Isolation | 3 branches | 2-3 | T1 |
| T3 | Bead-Task Bridge | 5 branches | 3-5 | T1, T2 |
| T4 | Conductor Protocol | 6 branches | 5-8 | T1, T3 |
| T5 | Deacon Service | 5 branches | 2-3 | T1, T3, T4 |

**Total: 34 tasks, 18-27 working days. T2 then T3 sequentially (council S4: removed false parallel claim).**

---

## File Structure

### tmup plugin (~/.claude/plugins/tmup/)

| File | Responsibility | Action |
|------|---------------|--------|
| `shared/src/types.ts` | Type definitions | Modify: add colony types (+25 lines) |
| `shared/src/constants.ts` | Runtime constants | Modify: add colony constants (+15 lines) |
| `shared/src/migrations.ts` | Schema migrations | Modify: add migration v4 (+40 lines) |
| `shared/src/agent-ops.ts` | Agent operations | Modify: extend registerAgent (+10 lines) |
| `mcp-server/src/tools/index.ts` | MCP tool defs + handlers | Modify: add tmup_heartbeat, extend tmup_dispatch (+60 lines) |
| `scripts/dispatch-agent.sh` | Worker launcher | Modify: add --worker-type, clone creation, Claude Code launch (+100 lines) |

### sdlc-os plugin (~/.claude/plugins/sdlc-os/)

| File | Responsibility | Action |
|------|---------------|--------|
| `colony/clone-manager.sh` | Git clone lifecycle | Create (~150 lines) |
| `colony/bead-parser.ts` | Parse bead markdown fields | Create (~150 lines) |
| `colony/bridge.ts` | Deterministic bead status updater | Create (~250 lines) |
| `colony/bridge-cli.ts` | CLI entry point for bridge | Create (~80 lines) |
| `colony/bridge.test.ts` | Bridge + parser tests | Create (~350 lines) |
| `colony/deacon.py` | systemd daemon | Create (~400 lines) |
| `colony/deacon_test.py` | Deacon tests | Create (~250 lines) |
| `colony/conductor-prompt.md` | System prompt for Conductor | Create (~150 lines) |
| `colony/validation/` | Phase 0 scripts | Create (6 scripts) |
| `colony/systemd/sdlc-colony-deacon.service` | systemd unit | Create (~25 lines) |
| `skills/sdlc-orchestrate/colony-mode.md` | Colony dispatch section | Create (~100 lines) |
| `skills/sdlc-orchestrate/SKILL.md` | Orchestration skill | Modify (+15 lines) |

---

## T0: Validation Spike (0.5 days)

Validate 6 environment assumptions in a single batch. Council simplicity cut S3: collapsed from 7 tasks to 2.

### T0.1: Batch validation (V-01 through V-06)

**Files:** Create `colony/validation/run-all.sh` (calls individual V-01..V-06 scripts)

- [ ] Write 6 validation scripts (v01-plugin-loading.sh through v06-shared-db.sh) covering: Claude CLI plugin loading, worker claim/complete round-trip, git clone file:// protocol, SQLite WAL 9-connection concurrency, inotifywait on WAL writes, two processes sharing tmup DB
- [ ] Write `run-all.sh` batch runner: runs all 6 in sequence, reports PASS/FAIL per script, exits 0 only if 6/6 pass
- [ ] Note: V-03 must use `origin/main` not `origin/HEAD` for commit comparison (council M3 fix)
- [ ] Run: `bash colony/validation/run-all.sh` -- expect 6/6 PASS
- [ ] Commit: `test: Phase 0 validation spike (V-01 through V-06)`

### T0.GATE: Phase 0 Gate

- [ ] Verify run-all.sh exits 0 with 6/6 PASS
- [ ] If any FAIL: fix environment issue, re-run. Do NOT proceed with failures.

---


### T0.5: Infrastructure Bootstrap (council C1 fix)

**Purpose:** sdlc-os has zero TypeScript or Python test infrastructure. Create it before any code tasks.

**Files:** Create `colony/package.json`, `colony/tsconfig.json`, `colony/vitest.config.ts`, `colony/pyproject.toml`

- [ ] Create `colony/package.json` with dependencies: vitest, typescript, better-sqlite3, @types/better-sqlite3, @types/node
- [ ] Create `colony/tsconfig.json` extending strict mode, ES2022 target, node module resolution
- [ ] Create `colony/vitest.config.ts` with root at colony/
- [ ] Create `colony/pyproject.toml` with pytest, mypy, ruff, black
- [ ] Run: `cd colony && npm install && npx tsc --noEmit && python3 -m pytest --co -q` -- all succeed
- [ ] Commit: `feat(sdlc-os): bootstrap colony/ TypeScript + Python infrastructure`

---

## T1: tmup Worker Polymorphism (3-5 days)

Extend tmup to support Claude Code workers alongside Codex. Modifies tmup plugin only.

### T1.1: Colony type definitions

**File:** Modify `shared/src/types.ts`

- [ ] Add after line 100 (after LifecycleEventType closing semicolon): `CynefinDomain = 'clear'|'complicated'|'complex'|'chaotic'|'confusion'`, `SdlcLoopLevel = 'L0'|'L1'|'L2'|'L2.5'|'L2.75'`, `SdlcPhase = 'frame'|'scout'|'architect'|'execute'|'synthesize'`, `WorkerType = 'codex'|'claude_code'`, `TaskCorrectionRow` interface
- [ ] NOTE: Do NOT modify ExecutionTargetType (council C2 Option B accepted — use worker_type on tasks table only)
- [ ] Run: `npx tsc --noEmit` -- no errors
- [ ] Commit: `feat(tmup): add colony runtime types`

### T1.2: Colony constants

**File:** Modify `shared/src/constants.ts`

- [ ] Add after EXECUTION_TARGET_TYPES (~line 55): `CYNEFIN_DOMAINS`, `SDLC_LOOP_LEVELS`, `SDLC_PHASES`, `WORKER_TYPES` enum arrays
- [ ] Add budget constants: `CONDUCTOR_BUDGET_USD=10.0`, `WORKER_BUDGET_SONNET_USD=3.0`, `WORKER_BUDGET_HAIKU_USD=0.5`, `BEAD_BUDGET_USD=50.0`
- [ ] Add `HEARTBEAT_THRESHOLDS: Record<CynefinDomain, number>` (clear=300, complicated=900, complex=1800, chaotic=300, confusion=900) per SC-COL-20
- [ ] Verify exports in `shared/src/index.ts`
- [ ] Run: `npx tsc --noEmit` -- no errors
- [ ] Commit: `feat(tmup): add colony constants`

### T1.3: Schema migration v4

**File:** Modify `shared/src/migrations.ts` (add before closing `];` at line 258)

- [ ] Write failing test `shared/src/migrations.test.ts`: verify bead_id/sdlc_loop_level/worker_type/bridge_synced columns exist after migration; verify task_corrections table created; verify CHECK rejects invalid sdlc_loop_level; verify CHECK rejects invalid worker_type; verify NULL sdlc_loop_level allowed (backward compat); verify idx_tasks_bead index; verify idempotent
- [ ] Run test -- expect FAIL (columns don't exist)
- [ ] Add migration v4: `ALTER TABLE tasks ADD COLUMN bead_id TEXT`, `sdlc_loop_level TEXT CHECK(...)`, `output_path TEXT`, `clone_dir TEXT`, `worker_type TEXT DEFAULT 'codex' CHECK(...)`, `bridge_synced INTEGER DEFAULT 0`; `CREATE TABLE task_corrections`; indexes
- [ ] Run test -- expect PASS
- [ ] Commit: `feat(tmup): add schema migration v4 for colony support`

### T1.4: Extend registerAgent (reduced scope per council C2)

**File:** Modify `shared/src/agent-ops.ts` (line 4, registerAgent function)

**Note:** Council C2 accepted Option B — `execution_targets` table is NOT used for Claude Code workers. The `worker_type` column on `tasks` is the discriminator instead. T1.4 scope is reduced to ensuring registerAgent remains backward compatible. No `executionTargetId` parameter needed.

- [ ] Verify registerAgent still works with existing 3-param and 4-param signatures (no regression)
- [ ] Run: `npx tsc --noEmit` -- no errors from colony type additions
- [ ] Commit: `test(tmup): verify registerAgent backward compatibility`

### T1.5: tmup_heartbeat MCP tool

**File:** Modify `mcp-server/src/tools/index.ts`

- [ ] Add to toolDefinitions: name `tmup_heartbeat`, required `agent_id`, optional `codex_session_id`
- [ ] Add handler: call updateHeartbeat(), retry 3x with 500ms backoff on SQLITE_BUSY, return `{ok, next_heartbeat_due}` where next = last_heartbeat + (STALE_THRESHOLD/3) per SC-COL-19
- [ ] Run: `npx tsc --noEmit` -- no errors
- [ ] Commit: `feat(tmup): add tmup_heartbeat MCP tool`

### T1.6: tmup_dispatch worker_type parameter

**File:** Modify `mcp-server/src/tools/index.ts`

- [ ] Add `worker_type: {type:'string', enum:['codex','claude_code']}` to tmup_dispatch inputSchema
- [ ] In handler: extract workerType, add `'--worker-type', workerType` to dispatchArgs
- [ ] Run: `npx tsc --noEmit` -- no errors
- [ ] Commit: `feat(tmup): add worker_type to tmup_dispatch`

### T1.7: dispatch-agent.sh Claude Code launch

**File:** Modify `scripts/dispatch-agent.sh`

- [ ] Add `WORKER_TYPE="codex"` to declarations (line 82), `--worker-type) WORKER_TYPE="$2"; shift 2 ;;` to parser
- [ ] Add Claude Code branch: if WORKER_TYPE==claude_code, write launcher running `claude -p --model sonnet --permission-mode auto --plugin-dir tmup` (no background heartbeat -- uses MCP), capture stdout to session-output.json
- [ ] Keep Codex launch as else branch VERBATIM
- [ ] Run: `bash -n scripts/dispatch-agent.sh` -- no syntax errors
- [ ] Commit: `feat(tmup): add Claude Code worker launch path`

### T1.GATE: Phase 1 Gate

- [ ] Run: `npm run build` -- success
- [ ] Run: `npx vitest run` -- all pass
- [ ] Commit: `feat(tmup): Phase 1 complete -- worker polymorphism`

---

## T2: Git Isolation (2-3 days)

Clone manager for worker isolation. Can run in parallel with T3.

### T2.1: clone-manager.sh

**File:** Create `colony/clone-manager.sh` (~150 lines)

- [ ] Write test `colony/clone-manager.test.sh`: test colony_clone_create (verify .git, path under /tmp/sdlc-colony/, push URL no-push), colony_clone_verify (valid passes, invalid fails), colony_clone_has_commits (detects beyond origin/main), colony_clone_prune (refuses unsynced, succeeds synced), colony_clone_recover_output (copies bead-output.md)
- [ ] Run -- expect FAIL (functions not found)
- [ ] Write clone-manager.sh: `COLONY_BASE="/tmp/sdlc-colony"`; `colony_clone_create()` -- `git clone file://`, verify .git, set no-push (SC-COL-27); `colony_clone_verify()` -- path check + .git + no-push (SC-COL-12); `colony_clone_has_commits()` -- `git log origin/main..HEAD | wc -l >= 1` (use origin/main not origin/HEAD per council M3) (SC-COL-26); `colony_clone_prune()` -- refuse if bridge_synced!=1 (SC-COL-21); `colony_clone_recover_output()` -- copy to recovered-outputs/
- [ ] Run -- expect PASS
- [ ] Commit: `feat(sdlc-os): add clone-manager.sh for worker git isolation`

### T2.2: Integrate into dispatch-agent.sh

**File:** Modify `~/.claude/plugins/tmup/scripts/dispatch-agent.sh`

- [ ] Add `CLONE_ISOLATION=0` to declarations, `--clone-isolation) CLONE_ISOLATION=1; shift ;;` to parser
- [ ] After validate_working_dir: if CLONE_ISOLATION==1 and clone-manager.sh exists, source it, colony_clone_create + colony_clone_verify, override WORKING_DIR
- [ ] Run: `bash -n scripts/dispatch-agent.sh` -- OK
- [ ] Commit: `feat(tmup): integrate clone-manager for colony worker isolation`

### T2.GATE: Phase 2 Gate

- [ ] Run: `bash colony/clone-manager.test.sh` -- all pass
- [ ] Commit: `feat: Phase 2 complete -- git isolation`

---

## T3: Bead-Task Bridge (3-5 days)

Deterministic TypeScript bridge. Critical data integrity layer -- every safety constraint matters.

### T3.1: Bead parser

**Files:** Create `colony/bead-parser.ts`, `colony/bead-parser.test.ts`

- [ ] Write failing test: parse well-formed bead (all fields); parse minimal (defaults for missing); throw on missing BeadID; throw on missing Status
- [ ] Run -- expect FAIL
- [ ] Write bead-parser.ts: `parseBeadFile(content) -> BeadFields` (regex on `**FieldName:**`); `updateBeadField(content, name, value) -> string`; `appendCorrection(content, level, cycle, finding) -> string`
- [ ] Run -- expect PASS
- [ ] Commit: `feat(sdlc-os): add deterministic bead markdown parser`

### T3.2: Bridge status update core

**Files:** Create `colony/bridge.ts`, `colony/bridge.test.ts`

- [ ] Write failing test: L0 complete -> running->submitted; compare-and-swap rejects mismatch (SC-COL-15); rejects missing bead-output.md (SC-COL-22); rejects missing sentinel (SC-COL-22); rejects output < 100 bytes; appends correction on failure without status change; idempotent skip when already at target
- [ ] Run -- expect FAIL
- [ ] Write bridge.ts: `bridgeUpdateBead(input) -> BridgeResult`; STATUS_TRANSITIONS (L0->submitted, L1->verified, L2->proven, L2.5->hardened, L2.75->reliability-proven); SC-COL-14 NULL fatal; SC-COL-15 compare-and-swap; SC-COL-22 sentinel+size; SC-COL-28 atomic temp+rename
- [ ] Run -- expect PASS
- [ ] Commit: `feat(sdlc-os): add bridge status update with safety constraints`

### T3.3: Bridge git commit

**File:** Modify `colony/bridge.ts` (add function), extend `colony/bridge.test.ts`

- [ ] Add tests: commits only specific bead file, decoy not in diff (SC-COL-29); rejects wrong branch (SC-COL-30)
- [ ] Run -- expect FAIL
- [ ] Add `bridgeCommitBeadUpdate(projectDir, beadFilePath, beadId, loopLevel, expectedBranch) -> CommitResult`: verify branch, `git add -- specific-file`, commit
- [ ] Run -- expect PASS
- [ ] Commit: `feat(sdlc-os): add bridge git commit with SC-COL-29/30`

### T3.4: Bridge CLI wrapper

**File:** Create `colony/bridge-cli.ts`

- [ ] Write CLI: parse --bead-file, --clone-dir, --loop-level, --completed, --finding, --cycle, --project-dir, --expected-branch, --expected-status; call bridgeUpdateBead then bridgeCommitBeadUpdate; output JSON
- [ ] Run: `npx tsc --noEmit colony/bridge-cli.ts` -- no errors
- [ ] Commit: `feat(sdlc-os): add bridge CLI wrapper`

### T3.GATE: Phase 3 Gate

- [ ] Run: `npx vitest run colony/` -- all pass
- [ ] Commit: `feat(sdlc-os): Phase 3 complete -- bead-task bridge`

---

## T4: Conductor Protocol (5-8 days)

Create Conductor prompt and colony detection gate in orchestration skill.

### T4.1: Conductor system prompt

**File:** Create `colony/conductor-prompt.md`

- [ ] Write prompt: session protocol (tmup_init first, pre-flight handoff second, tmup_status third); session types (DISPATCH, EVALUATE, SYNTHESIZE) with full pseudocode from spec SS7.5; rules (no re-decompose, write bead-context.md, workers --permission-mode auto, $10 budget); bridge CLI usage; AQS inline note (spec SS2.3.1)
- [ ] Commit: `docs(sdlc-os): add Conductor system prompt`

### T4.2: Colony mode additive section

**File:** Create `skills/sdlc-orchestrate/colony-mode.md`

- [ ] Write: detection (tmup_status valid session = colony, no session = sync); colony dispatch sequence (tmup_init, handoff, per-bead: tmup_task_create with JSON desc, write bead-context.md, tmup_dispatch); sync mode unchanged
- [ ] Commit: `docs(sdlc-os): add colony mode dispatch protocol`

### T4.3: Colony gate in SKILL.md

**File:** Modify `skills/sdlc-orchestrate/SKILL.md`

- [ ] Append: "If tmup available, use colony dispatch. See colony-mode.md. Detection: after Phase 3, check tmup_status. Backward compatible."
- [ ] Commit: `feat(sdlc-os): add colony mode gate to orchestration skill`


### T4.4: SYNTHESIZE + RECOVER session logic (council C5 fix)

**Purpose:** Spec SS6.2 (Sequential Merge) and SS7.2 (RECOVER session) have no implementing task.

- [ ] Add SYNTHESIZE section to conductor-prompt.md: sequential merge of clones (one at a time), conflict detection (abort merge, dispatch resolver worker), call tmup_teardown after all beads terminal
- [ ] Add RECOVER section: reconcile tmup task state vs bead file state, re-dispatch stale tasks, re-run bridge for completed-but-unsynced tasks
- [ ] Commit: `docs(sdlc-os): add SYNTHESIZE merge and RECOVER session to conductor prompt`

### T4.5: bead-context.md write protocol (council C5 fix)

**Purpose:** Spec SS4.8 (Worker Prompt Delivery) has no code task. Conductor must write bead-context.md to each clone before dispatch.

- [ ] Add to colony-mode.md: explicit protocol for writing `{clone_dir}/bead-context.md` with full bead spec + context + correction history before each `tmup_dispatch` call
- [ ] Specify file format: bead fields, acceptance criteria, scope files, correction history, output protocol instructions
- [ ] Commit: `docs(sdlc-os): add bead-context.md write protocol to colony mode`

### T4.GATE: Phase 4 Gate

- [ ] Verify colony/*.ts compile: `npx tsc --noEmit`
- [ ] Run: `npx vitest run colony/` -- all pass
- [ ] Commit: `feat(sdlc-os): Phase 4 complete -- Conductor protocol`

---

## T5: Deacon Service (2-3 days)

Python daemon that watches tmup DB and spawns Conductor sessions.

### T5.1: Deacon state machine core

**Files:** Create `colony/deacon.py`, `colony/deacon_test.py`

- [ ] Write failing test: initial state WATCHING; check_for_work True with pending colony tasks; True with completed unsynced; False with empty DB; double-spawn prevention (active lock blocks); stale lock detected (dead PID + old timestamp)
- [ ] Run -- expect FAIL
- [ ] Write deacon.py: DeaconState enum (WATCHING, CONDUCTING, RECOVERING); Deacon dataclass; check_for_work() queries colony tasks; can_spawn_conductor() checks lock PID+timestamp (STALE=180s); spawn_conductor() writes lock, Popen claude -p; recover_stale_claims() resets stale claimed tasks
- [ ] Run -- expect PASS
- [ ] Commit: `feat(sdlc-os): add Deacon state machine`

### T5.2: Deacon async event loop

**File:** Modify `colony/deacon.py`

- [ ] Add run_deacon() async: sd_notify READY; main loop with watchdog; WATCHING checks+spawns; CONDUCTING polls process exit+parses JSON cost; RECOVERING calls recover; self-watchdog 90s (SC-COL-01)
- [ ] Add main(): read env vars, SIGUSR2 handler -> RECOVERING, asyncio.run
- [ ] Run: `python3 -m py_compile colony/deacon.py` -- OK
- [ ] Commit: `feat(sdlc-os): add Deacon async event loop`

### T5.3: Deacon inotifywait integration

**File:** Modify `colony/deacon.py`

- [ ] Add watch_db_changes() async: spawn `inotifywait -m -e modify,create --include '\.(db|db-wal)$'` as asyncio subprocess; on event drain buffer then check_for_work; timeout = TIMER_INTERVAL safety net
- [ ] Wire into run_deacon as concurrent task
- [ ] Run: `python3 -m py_compile colony/deacon.py` -- OK
- [ ] Commit: `feat(sdlc-os): add inotifywait DB watching`

### T5.4: systemd unit file

**File:** Create `colony/systemd/sdlc-colony-deacon.service`

- [ ] Write: Type=notify, ExecStart python3 deacon.py, Restart=on-failure, RestartSec=15, RestartSteps=5, RestartMaxDelaySec=120, WatchdogSec=120, env vars
- [ ] Commit: `feat(sdlc-os): add systemd unit for Deacon`

### T5.GATE: Phase 5 Gate

- [ ] Run: `python3 -m pytest colony/deacon_test.py -v` -- all pass
- [ ] Run: `npx vitest run colony/` -- all pass
- [ ] Run: `bash colony/clone-manager.test.sh` -- all pass
- [ ] Run: `cd /home/q/.claude/plugins/tmup && npm run build && npx vitest run` -- all pass
- [ ] Final commit: `feat(sdlc-os): Phase 5 complete -- Colony runtime implementation complete`

---

## Safety Constraint Coverage

| Constraint | Task | Implementation |
|-----------|------|----------------|
| SC-COL-01 | T5.2 | Deacon self-watchdog 90s |
| SC-COL-04 | T4.1 | Conductor prompt pre-flight handoff |
| SC-COL-05 | T5.2 | CONDUCTOR_TIMEOUT constants |
| SC-COL-09 | T4.1 | Conductor checks existing active tasks |
| SC-COL-10 | T4.1 | Conductor checks dependency graph |
| SC-COL-12 | T2.1 | colony_clone_verify path check |
| SC-COL-14 | T3.2 | bridge NULL loop level fatal |
| SC-COL-15 | T3.2 | bridge compare-and-swap |
| SC-COL-19 | T1.5 | tmup_heartbeat next_heartbeat_due |
| SC-COL-20 | T1.2 | HEARTBEAT_THRESHOLDS per domain |
| SC-COL-21 | T2.1 | clone prune gated on bridge_synced |
| SC-COL-22 | T3.2 | bridge sentinel + size check |
| SC-COL-26 | T2.1 | colony_clone_has_commits |
| SC-COL-27 | T2.1 | colony_clone_create no-push URL |
| SC-COL-28 | T3.2 | bridge atomic write temp+rename |
| SC-COL-29 | T3.3 | bridge git add specific file |
| SC-COL-30 | T3.3 | bridge verify expected branch |
| SC-COL-06 | T5.2 | Deacon checks bridge lock before SIGTERM (council C6) |
| SC-COL-13 | T4.1 | Conductor cancels stale tasks before retry (council C6) |

## Spec Coverage

Every section of the 681-line spec (SS1-SS13) maps to at least one task:
- SS1 Problem Statement: context only
- SS2.1-2.4 Architecture: T1-T5 (all components)
- SS3.1-3.5 Deacon: T5.1-T5.4
- SS4.1-4.8 tmup Mods: T1.1-T1.7
- SS5.1-5.4 Bridge: T3.1-T3.4
- SS6.1-6.3 Git Isolation: T2.1-T2.2
- SS4.8 Worker Prompt Delivery: T4.5
- SS6.2 Sequential Merge: T4.4
- SS7.0-7.6 Conductor: T4.1-T4.5 (includes RECOVER session T4.4)
- SS8 Cost Controls: T1.2 constants
- SS7.2 RECOVER Session: T4.4
- SS9.1 Pre-Implementation: T0.1 (batch validation)
- SS9.5 Test Architecture: T1.3, T3.2, T5.1
- SS10 Phases: this plan
- SS11 Safety Constraints: table above (all 12 Tier-1)
- SS12 Risk Register: mitigations in T1.3, T2.1, T3.2, T5.1
- SS13 Success Criteria: validated by gate tasks
