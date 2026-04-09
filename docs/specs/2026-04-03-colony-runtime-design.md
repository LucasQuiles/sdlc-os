# SDLC-OS Colony Runtime Design Spec

**Date:** 2026-04-03
**Status:** Draft (v2 — post-council review)
**Author:** L (lab agent) + Q (human)
**Scope:** Persistent multi-agent colony runtime bridging sdlc-os and tmup
**Council Review:** 5 experts (adversarial auditor, behavioral prover, test integrity, simplicity auditor, safety analyst). 4 CRITICALs fixed, 8 gaps resolved, 10 safety constraints added, 3 simplifications accepted.

---

## 1. Problem Statement

sdlc-os orchestrates quality-gated software delivery through atomic work units (beads), multi-level correction loops (L0-L5), and adversarial quality review. Today it runs entirely within a single Claude Code session: the Conductor spawns subagents via the Agent tool, receives their output synchronously, and evaluates inline.

This architecture has three limits:

1. **No parallelism.** Subagents run sequentially. Independent beads cannot execute simultaneously.
2. **No persistence.** When the Conductor session ends, orchestration state lives only in bead markdown files.
3. **No colony.** Each task starts fresh. No persistent workforce, no work queue, no heartbeat monitoring.

This spec designs a colony runtime that:
- Uses tmup (SQLite WAL task DAG + tmux grid) as the execution engine
- Uses sdlc-os beads as the intent and quality layer
- Uses a systemd-managed Python daemon (the Deacon) as the persistence layer
- Supports mixed Claude Code and Codex CLI workers
- Preserves sdlc-os's L0-L5 correction loops and adversarial quality system
- Preserves backward compatibility with sync mode (no Deacon, no tmup)

---

## 2. Architecture

### 2.1 Component Roles

```
Deacon (Python daemon, systemd-managed)
  |-- Watches tmup SQLite DB for state changes
  |-- Spawns Conductor sessions when actionable work exists
  |-- Tracks Conductor PID -- prevents double-spawn
  |-- Runs recovery on crash (stale claims, orphaned clones)
  '-- Manages inotifywait + timer safety net

Conductor (Claude Code CLI, Opus model, ephemeral sessions)
  |-- Reads sdlc-os state (beads, state.md)
  |-- Creates tmup tasks from beads (beadToTask translation)
  |-- Dispatches workers via tmup_dispatch
  |-- Evaluates completed work (reads output files from clones)
  |-- Advances bead status through L1-L5 loops via deterministic bridge
  |-- Writes correction directives to bead files
  '-- Exits when all dispatched work is in-flight or terminal

Workers (Claude Code CLI or Codex CLI, in tmux panes)
  |-- Claim tasks via tmup (MCP tools or CLI)
  |-- Execute in isolated git clones
  |-- Write structured output to {clone}/bead-output.md
  |-- Write correction data to {clone}/correction.json on failure
  |-- Report completion/failure via tmup
  '-- Run with --permission-mode auto (NOT bypassPermissions)

Bridge (TypeScript function, deterministic, no LLM)
  |-- Called by Conductor after evaluating each completed task
  |-- Reads task result + output file from clone
  |-- Updates bead markdown file atomically (temp + rename)
  |-- Stages only the specific bead file (never git add -A)
  '-- Commits bead update to Git
```

### 2.2 Single Source of Truth

| Concern | Owner | Format | Location |
|---------|-------|--------|----------|
| What to do | Bead file | Markdown | `docs/sdlc/active/{task-id}/beads/{bead-id}.md` |
| Correction history | Bead file | Markdown (appended) | Same bead file, `**Correction history:**` section |
| Acceptance criteria | Bead file | Markdown | Same bead file, `**Output:**` section |
| Bead context for worker | File in clone | Markdown | `{clone_dir}/bead-context.md` (written by Conductor pre-dispatch) |
| Who is doing it | tmup task | SQLite | `tasks` table: `status`, `owner`, `claimed_at` |
| Retry/heartbeat state | tmup task | SQLite | `tasks` table: `retry_count`, `retry_after` |
| Loop-level tracking | tmup extension | SQLite | `task_corrections` table |
| Quality metadata | tmup task | SQLite + JSON | `description` field (JSON: cynefin_domain, acceptance_criteria, scope_files, sdlc_phase) |
| Worker output | File in clone | Markdown | `{clone_dir}/bead-output.md` |
| Correction data | File in clone | JSON | `{clone_dir}/correction.json` |
| Audit trail | Both | Git + SQLite events | Bead files (Git) + `events` table (SQLite) |

**Rules:**
- Bead files are the INPUT to each worker dispatch and the ACCUMULATOR of correction history.
- tmup tasks are the EXECUTION ENVELOPE.
- During execution, bead files may be stale. tmup_status is the real-time view.
- Bead files update at loop-level transitions via the deterministic bridge.
- If the system crashes between task completion and bead update, recovery reads tmup state and regenerates bead updates.

### 2.3 Data Flow

```
Phase 0-2 (Bootstrap Conductor, sync mode, no colony)
  |-- Normalize, Frame, Scout, Architect
  |-- Produces bead manifest
  |-- Calls tmup_init (idempotent reattach)
  |
  v
Conductor creates tmup tasks (beadToTask)
  |
  v
tmup_dispatch -> worker in tmux pane (isolated clone)
  |
  v
Worker executes L0 loop internally (3 attempts)
Worker writes {clone}/bead-output.md (with <!-- BEAD_OUTPUT_COMPLETE --> sentinel)
Worker calls tmup_complete or tmup_fail
Worker writes {clone}/correction.json on failure
  |
  v
Deacon detects state change -> spawns EVALUATE Conductor session
  |
  v
Conductor reads updated beads + tmup state + all output files
  - Completed beads: call bridge to update bead, dispatch Sentinel (L1) as new tmup task
  - Failed beads: read correction.json from clone, update bead correction history, dispatch retry
  - All beads terminal: advance to Synthesize phase
  |
  v
Conductor exits. Deacon watches for next event.
```

### 2.3.1 AQS Colony Topology

The Adversarial Quality System (L2.5) runs INLINE in the Conductor's EVALUATE session using the Agent tool (synchronous subagents). AQS is NOT dispatched as tmup tasks.

Rationale: AQS requires the Conductor to hold red-team and blue-team findings simultaneously, make Arbiter decisions, and route disputed findings — all within a single judgment context. Dispatching AQS as separate tmup tasks would fragment this context across sessions.

The `sdlc_loop_level` value `L2.5` in the tmup schema tracks that a bead has REACHED the AQS stage, not that AQS agents are tmup tasks. The bead status advances from `proven` to `hardened` within a single Conductor session.

Similarly, Phase 4.5 (Harden/L2.75) runs inline in the Conductor.

### 2.4 Phase 0-2 Bootstrap

Phases 0 (Normalize), 1 (Frame), 2 (Scout), and 3 (Architect) run in a **bootstrap Conductor session** — a standard Claude Code session using sync Agent tool dispatch, identical to today's non-colony sdlc-os.

The colony loop starts AFTER Phase 3 produces a bead manifest. The bootstrap Conductor:
1. Runs Phase 0-3 synchronously (existing SKILL.md behavior, unchanged).
2. Calls `tmup_init` to create/reattach a tmup session.
3. Creates tmup tasks from the bead manifest via `beadToTask`.
4. Dispatches the first round of workers.
5. Writes a pre-flight handoff block to `state.md` (SC-COL-04).
6. Exits.
7. Deacon takes over from here.

This means the human triggers the bootstrap (via `/sdlc` or manual bead creation). The Deacon does NOT handle Phase 0-2.

---

## 3. Deacon Service

### 3.1 State Machine

```
WATCHING --(inotifywait fires OR timer fires)--> check_for_work()
  if actionable work: acquire conductor lock, spawn Conductor -> CONDUCTING
  else: continue WATCHING

CONDUCTING --(Conductor PID exits normally)--> debounce 5s -> WATCHING
CONDUCTING --(Conductor PID missing/crash)--> RECOVERING

RECOVERING --(recovery complete)--> WATCHING
ANY --(SIGUSR2)--> RECOVERING
```

Three states: WATCHING, CONDUCTING, RECOVERING.

### 3.2 Implementation

**Location:** `/home/q/.claude/plugins/sdlc-os/colony/deacon.py`
**Runtime:** Python 3.12, asyncio
**Size estimate:** ~350-400 lines

**Primary watch:** `inotifywait -m {tmup_db_path}` monitors SQLite WAL changes. Filter to `.db` and `.db-wal` events only (ignore `.db-shm`). Drain event buffer on each evaluation cycle — act on current DB state, not queued events.
**Safety net:** systemd `WatchdogSec=120` + independent asyncio timer task every 60s. Timer task has self-watchdog: if it hasn't fired in >90s, Deacon sends SIGTERM to itself for systemd restart (SC-COL-01).
**Debounce:** 2-second window after Conductor exit before re-evaluating.

**Conductor spawn command:**
```bash
cd "${PROJECT_DIR}" && claude -p \
  --model opus \
  --output-format json \
  --permission-mode bypassPermissions \
  --plugin-dir /home/q/.claude/plugins/tmup \
  --plugin-dir /home/q/.claude/plugins/sdlc-os \
  --max-budget-usd ${BUDGET_CEILING} \
  --system-prompt "$(cat ${CONDUCTOR_PROMPT_FILE})" \
  --add-dir "${PROJECT_DIR}" \
  < /dev/null
```

**Verified Claude CLI flags (v2.1.91):**
- `--model opus|sonnet|haiku` -- selects model tier
- `--output-format json` -- returns `{"session_id": "UUID", "total_cost_usd": N, ...}`
- `--permission-mode bypassPermissions` -- full tool access (Conductor ONLY)
- `--plugin-dir <path>` -- loads plugins (repeatable)
- `--max-budget-usd <amount>` -- cost ceiling per session
- `--system-prompt <prompt>` -- sets system prompt
- `--add-dir <path>` -- grants tool access to directory
- No `--working-dir` flag -- must `cd` into project directory before launch

**PID tracking:** Conductor runs as a subprocess. Deacon holds the `Popen` handle.

**Double-spawn prevention:** File lock at `/tmp/sdlc-colony-conductor.lock`. Lock file contains Deacon PID + timestamp. Stale lock timeout: 3 minutes (not 10 — reduced per SC-COL-02).

**Wall-clock timeout on Conductor:** 30 minutes for DISPATCH/EVALUATE sessions, 60 minutes for SYNTHESIZE. If exceeded, Deacon sends SIGTERM (after checking bridge lock per SC-COL-06), waits 10s, then SIGKILL (SC-COL-05).

**Conductor session tracking:** JSON output includes `session_id` and `total_cost_usd`. Deacon logs both to `colony-sessions.log`. Aggregates cost by `bead_id` across tasks for per-bead budget enforcement.

### 3.3 Recovery

On entering RECOVERING state:

1. Query tmup DB: find tasks with `status='claimed'` where owning agent has `last_heartbeat_at` older than threshold (calibrated per cynefin_domain: CLEAR=5min, COMPLICATED=15min, COMPLEX=30min per SC-COL-20).
2. For each stale claim: check `{clone_dir}/bead-output.md` exists. If yes: copy to `/tmp/sdlc-colony/recovered-outputs/{task_id}/` before any action (SC-COL-21). Then if `retry_count < max_retries`, set `status='pending'` with backoff. Otherwise `status='needs_review'`.
3. Prune orphaned clones: only prune if corresponding tmup task has bridge_synced=true OR task status='cancelled'. Never prune clones whose output hasn't been consumed (SC-COL-21).
4. Remove stale lock files: check age > 3 minutes and no matching PID.
5. Verify tmux session exists. If dead: log warning, set all active agents to `status='shutdown'`.
6. Check for bead files with dirty working tree state (uncommitted bridge writes): run bridge recovery to replay from tmup state.
7. Transition to WATCHING.

### 3.4 Escalation

If the same bead causes 3 consecutive Conductor session failures (tracked by counting `task_failed` events per `bead_id` in tmup events table within 1 hour):

1. Send alert via shell: `curl` to WhatSoup REST API or `node -e` script (Deacon is Python, cannot use MCP tools).
2. Message: "Colony stuck on bead {id}: {last error}. {N} failures in {M} minutes."
3. Enter WATCHING with this bead blacklisted until SIGUSR1 (manual resume) or new bead files appear.

### 3.5 systemd Unit

**Location:** `~/.config/systemd/user/sdlc-colony-deacon.service`

```ini
[Unit]
Description=SDLC-OS Colony Deacon
After=network.target

[Service]
Type=notify
ExecStart=/usr/bin/python3 /home/q/.claude/plugins/sdlc-os/colony/deacon.py
Restart=on-failure
RestartSec=15
RestartSteps=5
RestartMaxDelaySec=120
WatchdogSec=120
Environment=PYTHONUNBUFFERED=1
Environment=SDLC_PROJECT_DIR=/path/to/project
Environment=TMUP_DB_PATH=/path/to/tmup.db
Environment=CONDUCTOR_BUDGET_USD=10.00
Environment=EXPECTED_BRANCH=main

[Install]
WantedBy=default.target
```

---

## 4. tmup Modifications

### 4.1 Schema Migration v4

**File:** `/home/q/.claude/plugins/tmup/shared/src/migrations.ts`
**Insert after:** migration v3 (line ~280)

```sql
-- Migration v4: SDLC-OS Colony Support

-- Essential execution columns (queried by Deacon/Conductor)
ALTER TABLE tasks ADD COLUMN bead_id TEXT;
ALTER TABLE tasks ADD COLUMN sdlc_loop_level TEXT
  CHECK (sdlc_loop_level IS NULL OR sdlc_loop_level IN ('L0','L1','L2','L2.5','L2.75'));
ALTER TABLE tasks ADD COLUMN output_path TEXT;
ALTER TABLE tasks ADD COLUMN clone_dir TEXT;
ALTER TABLE tasks ADD COLUMN worker_type TEXT DEFAULT 'codex'
  CHECK (worker_type IN ('codex','claude_code'));
ALTER TABLE tasks ADD COLUMN bridge_synced INTEGER DEFAULT 0;

-- cynefin_domain, acceptance_criteria, scope_files, sdlc_phase stored in description JSON

CREATE TABLE IF NOT EXISTS task_corrections (
  task_id TEXT NOT NULL REFERENCES tasks(id),
  level TEXT NOT NULL CHECK (level IN ('L0','L1','L2','L2.5','L2.75')),
  cycle INTEGER NOT NULL DEFAULT 0,
  max_cycles INTEGER NOT NULL DEFAULT 2,
  last_finding TEXT,
  PRIMARY KEY (task_id, level)
);

CREATE INDEX IF NOT EXISTS idx_tasks_bead ON tasks(bead_id) WHERE bead_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_tasks_colony ON tasks(sdlc_loop_level, status) WHERE sdlc_loop_level IS NOT NULL;
```

Note: `sdlc_loop_level` should be NOT NULL for colony tasks. The CHECK allows NULL for backward compatibility with non-colony tmup usage. The bridge MUST treat NULL as a fatal error (SC-COL-14).

### 4.2 New Type Definitions

**File:** `/home/q/.claude/plugins/tmup/shared/src/types.ts` (append after line 396)

```typescript
export type CynefinDomain = 'clear' | 'complicated' | 'complex' | 'chaotic' | 'confusion';
export type SdlcLoopLevel = 'L0' | 'L1' | 'L2' | 'L2.5' | 'L2.75';
export type SdlcPhase = 'frame' | 'scout' | 'architect' | 'execute' | 'synthesize';
export type WorkerType = 'codex' | 'claude_code';

export interface TaskCorrectionRow {
  task_id: string;
  level: SdlcLoopLevel;
  cycle: number;
  max_cycles: number;
  last_finding: string | null;
}
```

### 4.3 Execution Target Activation

**File:** `/home/q/.claude/plugins/tmup/shared/src/agent-ops.ts` (line ~4)

Extend `registerAgent()` to accept optional `executionTargetId`. Write to `agents.execution_target_id` column (exists from migration v3, line 232 of migrations.ts).

### 4.4 New Execution Target Type

**File:** `/home/q/.claude/plugins/tmup/shared/src/types.ts` (line 89)

Add `'claude_code'` to `ExecutionTargetType` union. Add to `EXECUTION_TARGET_TYPES` in constants.ts.

### 4.5 New MCP Tool: tmup_heartbeat

**File:** `/home/q/.claude/plugins/tmup/mcp-server/src/tools/index.ts`

Wraps internal `updateHeartbeat()` from `agent-ops.ts` (lines 23-42). Response MUST include `next_heartbeat_due` timestamp (SC-COL-19). Retries with backoff on SQLITE_BUSY instead of failing silently.

### 4.6 tmup_dispatch Polymorphism

**File:** `/home/q/.claude/plugins/tmup/mcp-server/src/tools/index.ts` (tmup_dispatch, line ~236)

Add `worker_type` parameter (`'codex' | 'claude_code'`, default `'codex'`). Pass `--worker-type` to dispatch-agent.sh.

### 4.7 dispatch-agent.sh Changes

**File:** `/home/q/.claude/plugins/tmup/scripts/dispatch-agent.sh` (362 lines)

1. **Add `--worker-type`** to argument parser (lines 82-97).

2. **Clone creation** (new, before launch): Create isolated git clone:
   ```bash
   CLONE_DIR="/tmp/sdlc-colony/${TMUP_SESSION_NAME}/worker-${AGENT_ID}"
   git clone "file://${WORKING_DIR}" "${CLONE_DIR}" || die "Clone creation failed"
   [ -d "${CLONE_DIR}/.git" ] || die "Clone invalid: no .git directory"  # SC-COL-12
   WORKING_DIR="${CLONE_DIR}"
   # Prevent accidental pushes from workers (SC-COL-27)
   git -C "${CLONE_DIR}" remote set-url --push origin no-push
   ```
   Note: full clones, not shallow. `file://` for speed but no `--depth 1`.

3. **Verify WORKING_DIR** before launch (SC-COL-12):
   ```bash
   [[ "$WORKING_DIR" == /tmp/sdlc-colony/* ]] || die "WORKING_DIR not under /tmp/sdlc-colony/"
   ```

4. **Worker launch branch** on worker type:
   - `codex`: existing launch path (unchanged)
   - `claude_code`:
     ```bash
     cd "${WORKING_DIR}" && claude -p \
       --model "${CLAUDE_MODEL:-sonnet}" \
       --output-format json \
       --permission-mode auto \
       --plugin-dir /home/q/.claude/plugins/tmup \
       --max-budget-usd "${WORKER_BUDGET:-3.00}" \
       --system-prompt "${CLAUDE_PROMPT}" \
       --add-dir "${WORKING_DIR}"
     ```
     Note: `--permission-mode auto` (NOT bypassPermissions) for workers (SC-COL-04 variant). Do NOT `exec` into claude — run as subprocess, capture stdout to `${CLONE_DIR}/session-output.json` for session ID extraction (SC-COL-12 variant).

5. **Skip background heartbeat loop** for Claude Code workers (they use MCP heartbeat).

### 4.8 Worker Prompt Delivery

Bead content is NOT passed via `--system-prompt` (too large). Instead:

1. Conductor writes `{clone_dir}/bead-context.md` containing the full bead spec, context, and correction history.
2. `--system-prompt` contains only: role identity, tool usage instructions (tmup MCP tools), output protocol, and the instruction "Read bead-context.md in your working directory as your first action."
3. Worker reads the file, executes, writes `bead-output.md`.

This avoids CLI argument length limits and makes the bead context file-system verifiable.

---

## 5. Bridge

### 5.1 Purpose

Deterministic (non-LLM) TypeScript function called by the Conductor after evaluating each completed task. Synchronizes tmup task completion to sdlc-os bead files.

### 5.2 Location

- `/home/q/.claude/plugins/sdlc-os/colony/bridge.ts` (~250 lines)
- `/home/q/.claude/plugins/sdlc-os/colony/bead-parser.ts` (~150 lines)

### 5.3 Bead Status Mapping

| Loop Level | Task completed | Bead Transition |
|------------|---------------|-----------------|
| L0 | completed | `running -> submitted` |
| L1 | completed | `submitted -> verified` |
| L2 | completed | `verified -> proven` |
| L2.5 | completed (inline) | `proven -> hardened` |
| L2.75 | completed (inline) | `hardened -> reliability-proven` |
| any | needs_review | no status change; append failure to correction history |

### 5.4 Safety Constraints

- **SC-COL-14:** Bridge MUST treat NULL `sdlc_loop_level` as fatal error.
- **SC-COL-15:** Bridge MUST acquire file lock BEFORE reading bead state. MUST verify source status matches expected pre-transition status (compare-and-swap). If bead is already at or beyond target status, log warning and skip.
- **SC-COL-22:** Bridge MUST verify `bead-output.md` exists, exceeds 100 bytes, and contains `<!-- BEAD_OUTPUT_COMPLETE -->` sentinel before processing. Poll up to 60s if absent.
- **SC-COL-26:** Bridge MUST verify clone has at least one commit beyond source HEAD (`git -C ${CLONE_DIR} log --oneline origin/HEAD..HEAD` returns >= 1 entry) before advancing bead to `submitted` or beyond.
- **SC-COL-28:** Bridge MUST write bead file updates atomically: write to `{bead-id}.md.tmp`, then `rename()`. Never write in-place.
- **SC-COL-29:** Bridge MUST use `git add -- {bead_file_path}` (explicit file). Never `git add -A`.
- **SC-COL-30:** Bridge MUST verify main checkout is on expected branch before committing.
- After successful commit: set `bridge_synced = 1` on the tmup task.

---

## 6. Git Isolation

### 6.1 Strategy: Full Clones via file:// Protocol

```bash
git clone "file://${PROJECT_DIR}" "${CLONE_DIR}"
```

Full clones (no `--depth 1`). `file://` protocol for faster local transport. Workers have full git history available for blame, log, and merge operations.

### 6.2 Sequential Merge (Refinery Pattern)

Conductor merges completed clones one at a time during Synthesize. On conflict: abort merge, dispatch resolver worker with both diffs, retry from resolver's output.

### 6.3 Clone Lifecycle

- **Normal:** deleted after successful merge AND bridge_synced=true.
- **Gated:** clones preserved until bead reaches `proven` status (post-L2). Sentinel and Oracle tasks read output from the clone via `task.output_path`. Clones MUST NOT be deleted while any loop-level task references them.
- **Stale:** Deacon prunes only clones where bridge_synced=true OR task status='cancelled'. Never prune clones with unread output.
- **Crash:** systemd ExecStopPost cleanup for truly abandoned clones (>24 hours old).

---

## 7. Conductor Adaptation

### 7.0 Session Bootstrap Protocol

Every Conductor session MUST call `tmup_init` as its first action (idempotent reattach if session exists). `tmup_teardown` is called only by a SYNTHESIZE Conductor session after all beads reach terminal status.

Workers inherit the session via `TMUP_SESSION_NAME` env var set by dispatch-agent.sh (existing launcher script, line 171).

### 7.1 Event-Driven Batch Sessions

No polling. Conductor sessions spawn, evaluate, dispatch, exit. Deacon watches tmup DB for state changes and spawns next session.

Every Conductor session writes a **pre-flight handoff block** to `state.md` BEFORE entering its evaluation loop (SC-COL-04):
```markdown
## Pre-Flight Handoff
**Session type:** DISPATCH | EVALUATE | SYNTHESIZE
**Beads in manifest:** [list of bead IDs]
**In-flight tasks:** [list of tmup task IDs currently claimed]
**Timestamp:** [ISO8601]
```

This ensures a successor Conductor can determine what is already running without re-decomposing.

### 7.2 Session Types

| Type | Trigger | Action | Est. Cost |
|------|---------|--------|-----------|
| BOOTSTRAP | Human-triggered | Phase 0-3 + tmup_init + first dispatch | $3-8 |
| DISPATCH | New pending beads, no in-flight tasks | Create tmup tasks, dispatch workers | $1-2 |
| EVALUATE | Workers completed/failed | Read outputs, advance beads, dispatch next loop | $1-3 |
| SYNTHESIZE | All beads terminal | Sequential merge, fitness check, delivery | $2-5 |
| RECOVER | Stale state detected | Reconcile tmup + beads, re-dispatch | $1-2 |

### 7.3 Correction Flow

1. Worker calls `tmup_fail` with reason + brief message. For retriable failures (crash, timeout), tmup auto-retries -- no structured correction needed.
2. For non-retriable failures (logic_error, artifact_missing, dependency_invalid), worker writes `{clone}/correction.json`:
   ```json
   {
     "what_failed": "specific finding",
     "evidence": "file:line or test output",
     "what_to_try": "specific suggestion",
     "what_not_to_try": ["approach 1 already failed"]
   }
   ```
3. Deacon spawns Conductor.
4. Conductor reads `correction.json` from clone (file-based, not tmup messages).
5. Conductor appends correction to bead file.
6. Conductor checks for existing active tasks at same bead_id + loop_level before creating retry (SC-COL-09). Cancels any stale active tasks first (SC-COL-13).
7. Conductor creates new tmup task for retry.

### 7.4 Pre-Flight Handoff (replaces separate Handoff Protocol)

Every Conductor session writes a pre-flight handoff block at START (SC-COL-04). This replaces the heavyweight Phase 6 handoff protocol. The pre-flight block records the session's current state so any successor can resume without re-decomposing.

New Conductor MUST NOT re-decompose beads or change the design.

Per-session budget: $10.00 (increased from $5 to make handoff rare).

### 7.5 EVALUATE Session Logic

```
1. Call tmup_init (idempotent reattach)
2. Write pre-flight handoff block to state.md
3. Read all unread messages from tmup inbox (SC-COL-08 variant)
4. Query all tasks grouped by bead_id
5. For each bead:
   a. Determine current loop level from task statuses + task_corrections
   b. If latest task completed:
      - Read bead-output.md from clone (via task.output_path)
      - Call bridge to update bead status
      - If bead ready for next loop level: dispatch next-level task
        * L0 complete -> dispatch L1 (Sentinel) as new tmup task
        * L1 complete -> dispatch L2 (Oracle) as new tmup task
        * L2 complete -> run AQS inline (L2.5), run Harden inline (L2.75)
        * L2.75 complete -> bead ready for merge
   c. If latest task failed (needs_review):
      - Read correction.json from clone
      - Append correction to bead file
      - Create retry task (after cancelling stale tasks per SC-COL-09/13)
   d. If latest task still in-flight: skip (wait for next cycle)
6. Check bead dependency graph before dispatching downstream beads (SC-COL-10)
7. If all beads at terminal state: transition to SYNTHESIZE
8. Exit
```

### 7.6 Backward Compatibility

Sync mode (Agent tool dispatch, no Deacon, no tmup) is preserved. The colony dispatch is an ADDITIVE section in SKILL.md, gated on whether a tmup session is active.

Detection: the Conductor checks `tmup_status`. If it returns a valid session, use colony dispatch. If no session exists (or tmup plugin not loaded), use sync Agent tool dispatch. No `COLONY_MODE` flag needed.

---

## 8. Cost Controls

| Control | Mechanism | Default |
|---------|-----------|---------|
| Per-session ceiling | `--max-budget-usd` on Claude CLI | $10.00 |
| Per-bead ceiling | Deacon aggregates cost by bead_id across tasks | $50.00 |
| Worker ceiling | `--max-budget-usd` on worker launch | $3.00 (sonnet), $0.50 (haiku) |
| Clear bead fast path | Deterministic checks only, skip Conductor eval | saves ~$3/bead |
| Escalation | Shell alert at budget ceiling | automatic |

Expected cost per COMPLICATED bead: ~$3.70 (vs ~$2.00 sync). Colony overhead: ~85%.
Offset by parallelism: 5-bead task wall time reduced ~60%.

---

## 9. Validation Chains

### 9.1 Pre-Implementation (Phase 0)

- [ ] V-01: `claude -p --plugin-dir tmup` can access tmup MCP tools
- [ ] V-02: Claude `-p` worker calls tmup_claim/complete/heartbeat successfully
- [ ] V-03: `git clone file:///path` creates a valid clone usable for commits and fetch-merge
- [ ] V-04: SQLite WAL handles 9 concurrent connections without lock timeout (realistic transaction durations, not just connection counts)
- [ ] V-05: `inotifywait -m tmup.db` fires on WAL writes
- [ ] V-06: Two Claude `-p` processes share same tmup.db via separate MCP servers

### 9.2 Per-Phase Validation

**Phase 1:** Claude worker dispatches, claims, completes via MCP. Dead-claim recovery works. Heartbeat includes next_heartbeat_due.
**Phase 2:** Clones isolated. Sequential merge succeeds. Conflict detected and aborted cleanly. No-push remote URL set.
**Phase 3:** beadToTask parses correctly. Bridge updates bead status and turbulence. Parser handles missing fields. Atomic write via temp+rename. Compare-and-swap on status. Completion sentinel checked.
**Phase 4:** Conductor dispatches via tmup. Evaluates outputs. Reads corrections from clone files. Exits cleanly. Pre-flight handoff written. Duplicate task detection works.
**Phase 5:** Deacon starts via systemd. Spawns Conductor on work. Prevents double-spawn. Recovers from crash. Preserves unread clone output.

### 9.5 Test Architecture

**Layer 1: Deterministic unit tests ($0)**
- Bridge parser (bead-parser.test.ts) — well-formed, missing fields, extra fields, unusual formatting
- Bridge status mapping — every loop level transition
- Bridge compare-and-swap — regression detection
- Deacon state machine with mocked subprocess (deacon_test.py)
- Schema migration idempotency (SQLite in-memory)
- clone-manager.sh with stub git repos

**Layer 2: Tool connectivity tests (~$0.05 each)**
- V-01 through V-06 as automated scripts
- Verify MCP tool round-trips with minimal prompt

**Layer 3: Worker behavior tests (~$0.50 each)**
- Synthetic "clear" bead: "write DONE to bead-output.md"
- Verify: output file format, completion sentinel, tmup_complete called, correction.json on failure

**Layer 4: Colony integration tests (~$5 per run)**
- Two synthetic beads, independent scopes, no real code
- Full Deacon + Conductor + worker pipeline
- Verify: bead transitions, bridge updates, Deacon state machine
- Manual run before each phase gate, not in CI

---

## 10. Implementation Phases

### Phase 0: Validation Spike (2 days)
Validate V-01 through V-06. Each validation is a standalone test script.

### Phase 1: tmup Worker Polymorphism (3-5 days)
**Files modified:** types.ts (+20), constants.ts (+5), migrations.ts (+30), agent-ops.ts (+10), tools/index.ts (+40), dispatch-agent.sh (+80), policy.yaml (+15)
10 micro-tasks (P1-01 through P1-10).

### Phase 2: Git Isolation (2-3 days)
**Files created:** colony/clone-manager.sh (~150 lines)
**Files modified:** dispatch-agent.sh (+20)
7 micro-tasks (P2-01 through P2-07).

### Phase 3: Bead-Task Bridge (3-5 days)
**Files created:** colony/bridge.ts (~250), colony/bead-parser.ts (~150), colony/bridge.test.ts (~300)
8 micro-tasks (P3-01 through P3-08).

### Phase 4: Conductor Async + Session Protocol (5-8 days)
**Files created:** colony/conductor-prompt.md (~150), skills/sdlc-orchestrate/colony-mode.md (~200)
**Files modified:** skills/sdlc-orchestrate/SKILL.md (+20, additive, preserves sync mode)
9 micro-tasks (P4-01 through P4-09). Includes EVALUATE session logic, pre-flight handoff, backward compatibility gate.

### Phase 5: Deacon Service (2-3 days)
**Files created:** colony/deacon.py (~400), colony/deacon_test.py (~200), systemd unit (~20)
10 micro-tasks (P5-01 through P5-10).

**Total: 17-26 working days. Phases 2 and 3 can run in parallel.**

---

## 11. Safety Constraints Registry

Tier 1 constraints (must implement):

| ID | Constraint | Phase |
|----|-----------|-------|
| SC-COL-01 | Deacon timer as independent asyncio task with self-watchdog | 5 |
| SC-COL-04 | Pre-flight handoff block at Conductor session START | 4 |
| SC-COL-05 | Wall-clock timeout on Conductor sessions (30/60 min) | 5 |
| SC-COL-09 | Check for existing active tasks before creating duplicates | 4 |
| SC-COL-10 | Bead dependency graph check before dispatch | 4 |
| SC-COL-12 | Verify WORKING_DIR under /tmp/sdlc-colony/ + clone .git exists | 2 |
| SC-COL-15 | Compare-and-swap on bead status in bridge | 3 |
| SC-COL-22 | Verify bead-output.md exists + completion sentinel | 3 |
| SC-COL-26 | Verify clone has commits beyond source HEAD | 3 |
| SC-COL-27 | Set no-push remote URL on clones | 2 |
| SC-COL-28 | Atomic bead file writes via temp + rename | 3 |
| SC-COL-29 | Stage only specific bead file, never git add -A | 3 |

---

## 12. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| SQLite WAL contention at 9 connections | Low | High | V-04 validates; busy_timeout=8000ms; heartbeat retries with backoff |
| Conductor loses correction quality across sessions | Medium | Medium | Pre-flight handoff; no-re-decompose rule; file-based corrections in clones |
| Git merge conflicts from parallel workers | Medium | Medium | FFT-12 serializes overlapping scopes; resolver worker for conflicts |
| inotifywait misses events | Low | Low | Timer safety net every 60s; drain event buffer on evaluation |
| Bridge parser fails on unusual bead format | Medium | Medium | Error file + Deacon alert; completion sentinel; compare-and-swap |
| Colony costs exceed budget | Medium | Medium | Per-session ($10), per-bead ($50) ceilings; shell alerts |
| Two Deacons running | Very Low | Critical | Deacon-level flock on startup; systemd singleton; lock with PID+timestamp |
| Worker writes to main checkout | Low | High | WORKING_DIR check + clone .git check + no-push remote URL |
| Worker hallucinates destructive commands | Low | High | Workers use --permission-mode auto (not bypassPermissions) |
| Clone pruned before output consumed | Low | High | Prune gated on bridge_synced flag; output preserved to recovery staging |

---

## 13. Success Criteria

1. Deacon automatically orchestrates bead execution through all loop levels without manual intervention.
2. Multiple workers execute in parallel on independent beads in isolated git clones.
3. L0-L5 correction loops work across Conductor sessions.
4. Crashed worker's task is automatically recovered and re-dispatched.
5. Crashed Conductor session is restarted by Deacon with state recovery.
6. Cost per COMPLICATED bead < $8.
7. Wall-clock time for 5-bead task with 3 parallel beads < 50% of sequential time.
8. Sync mode (no Deacon) continues to work unchanged.
