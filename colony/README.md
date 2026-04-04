# Colony Runtime

## What It Is

The Colony Runtime is a persistent multi-agent execution layer that bridges sdlc-os (quality-gated software delivery via beads and correction loops) with tmup (SQLite WAL task DAG + tmux grid). It replaces the single-session, sequential Agent tool dispatch with a systemd-managed daemon that watches for work, spawns ephemeral Conductor sessions, dispatches parallel workers into isolated git clones, and synchronizes results back to bead files through a deterministic (no LLM) bridge. The result is parallel bead execution with crash recovery, heartbeat monitoring, and auditable cost tracking -- all while preserving sdlc-os's L0-L2.75 correction loops and adversarial quality system.

## Architecture

```
                          +---------------------+
                          |      systemd         |
                          | sdlc-colony-deacon   |
                          +----------+----------+
                                     |
                          +----------v----------+
                          |      Deacon          |
                          |   (Python daemon)    |
                          |                      |
                          |  WATCHING --------+  |
                          |  CONDUCTING       |  |
                          |  RECOVERING ------+  |
                          +----------+----------+
                                     |
                             spawns claude -p
                                     |
                          +----------v----------+
                          |     Conductor        |
                          |  (Opus, ephemeral)   |
                          |                      |
                          |  DISPATCH / EVALUATE |
                          |  SYNTHESIZE / RECOVER|
                          +--+------+------+----+
                             |      |      |
                     +-------+  +---+  +---+-------+
                     |          |          |        |
               +-----v--+ +----v---+ +---v----+   |
               | Worker  | | Worker | | Worker |   |
               | (Codex) | | (CC)   | | (Codex)|   |
               +----+----+ +---+----+ +---+----+   |
                    |           |           |        |
                    v           v           v        |
              clone-1/     clone-2/    clone-3/      |
              bead-output  bead-output bead-output   |
                    |           |           |        |
                    +-----+-----+-----+-----+        |
                          |                          |
                   +------v------+                   |
                   |   Bridge    |<------------------+
                   | (TS, no LLM)|    Conductor calls
                   +------+------+    bridge-cli.ts
                          |
                    bead-*.md updated
                    git commit
```

**Deacon** -- Persistent Python daemon managed by systemd. Watches the tmup SQLite database for state changes via `inotifywait` (with a 60-second timer fallback). When actionable work exists and no Conductor is running, it spawns a Conductor session. It also recovers stale claims when workers crash or go silent.

**Conductor** -- Ephemeral Claude Code CLI session (Opus model) spawned by the Deacon with `claude -p`. It reads bead manifests, creates tmup tasks, dispatches workers, evaluates completed work, and advances beads through loop levels. Each session handles one session type (DISPATCH, EVALUATE, SYNTHESIZE, or RECOVER) and exits when done.

**Workers** -- Claude Code or Codex CLI agents running in tmux panes. Each worker operates in an isolated git clone created by the Clone Manager. Workers read `bead-context.md` for instructions, write output to `bead-output.md`, and report status via tmup tools. Workers never push to the source repository.

**Bridge** -- Deterministic TypeScript module (no LLM) called by the Conductor after evaluating each completed task. It updates bead markdown files atomically, enforces status transition rules via compare-and-swap, validates output files, and commits changes to git.

**Bead files** -- Markdown files under `docs/sdlc/active/{task-id}/beads/{bead-id}.md` that serve as the single source of truth for what to do, correction history, and quality status. The bridge updates them; workers read them via `bead-context.md`.

## Components

### Deacon (`colony/deacon.py`)

The Deacon is a 3-state async Python daemon:

**State machine:**

| State | What happens | Transitions to |
|-------|-------------|----------------|
| `WATCHING` | Checks DB for work, spawns Conductor if available | `CONDUCTING` (on spawn) |
| `CONDUCTING` | Polls Conductor process, checks wall-clock timeout | `WATCHING` (on exit), `RECOVERING` (on timeout) |
| `RECOVERING` | Resets stale claims, preserves partial output | `WATCHING` (always) |

**How it watches:** The Deacon runs two concurrent asyncio tasks. The primary watcher uses `inotifywait -m` to monitor `.db` and `.db-wal` file modifications in the database directory. Events are debounced by draining the buffer before checking for work. A 60-second timer provides a safety-net fallback if `inotifywait` is unavailable or misses events.

**How it spawns Conductors:** When `check_for_work()` returns truthy and `can_spawn_conductor()` confirms no active lock, the Deacon launches `claude -p` with:
- `--model opus`
- `--output-format json`
- `--permission-mode bypassPermissions`
- `--plugin-dir` for both tmup and sdlc-os plugins
- `--max-budget-usd` from `CONDUCTOR_BUDGET_USD` (default `10.00`)
- `--system-prompt` loaded from `conductor-prompt.md`

The lock file (`/tmp/sdlc-colony-conductor.lock`) is written _after_ `Popen` succeeds, containing the Conductor PID (not the Deacon PID) and a Unix timestamp. Lock acquisition uses atomic `O_CREAT | O_EXCL` to prevent TOCTOU races.

**Work detection:** `check_for_work()` queries the `tasks` table for colony tasks (`sdlc_loop_level IS NOT NULL`) that are `pending`, `completed` with `bridge_synced = 0`, or `needs_review`. If all bead tasks are terminal (`completed` or `cancelled`) and bridge-synced, it returns `"synthesize"` to trigger a SYNTHESIZE session.

**Recovery behavior:** `recover_stale_claims()` finds claimed tasks whose agent heartbeat exceeds a per-domain threshold (SC-COL-20). Before resetting a task to `pending`, it preserves any partial output by copying `bead-output.md` from the clone to `/tmp/sdlc-colony/recovered-outputs/{task-id}/`. If `retry_count` exceeds `max_retries`, the task is set to `needs_review` instead. Clone directory paths are validated against `COLONY_BASE` to prevent path traversal.

**Self-watchdog (SC-COL-01):** An independent asyncio task checks that the main timer loop has fired within the last 90 seconds. If not, it sends `SIGTERM` to the Deacon's own PID.

**Wall-clock timeout (SC-COL-05):** DISPATCH sessions time out at 30 minutes, SYNTHESIZE at 60 minutes. Before sending `SIGTERM`, the Deacon checks whether the bridge lock is active (SC-COL-06) and defers termination if so.

**Signal handling:** `SIGUSR2` forces a transition to `RECOVERING` state for manual recovery triggers.

**Configuration:**

| Env var | Default | Description |
|---------|---------|-------------|
| `TMUP_DB_PATH` | (required) | Path to tmup SQLite database |
| `SDLC_PROJECT_DIR` | (required) | Project directory for Conductor sessions |
| `CONDUCTOR_BUDGET_USD` | `10.00` | Per-session budget ceiling |
| `EXPECTED_BRANCH` | `main` | Expected git branch name |

**systemd unit:** `colony/systemd/sdlc-colony-deacon.service`

```
Type=notify
WatchdogSec=120
Restart=on-failure
RestartSec=15 (escalates to 120s over 5 steps)
```

Install to `~/.config/systemd/user/`:
```bash
cp colony/systemd/sdlc-colony-deacon.service ~/.config/systemd/user/
# Edit the service file to set SDLC_PROJECT_DIR and TMUP_DB_PATH
systemctl --user daemon-reload
systemctl --user enable --now sdlc-colony-deacon
```

**Telemetry:** On Conductor exit, the Deacon parses JSON stdout for `session_id` and `total_cost_usd`, then appends a JSONL record to `colony/colony-sessions.log` with fields: `session_id`, `total_cost_usd`, `timestamp`, `session_type`, `exit_code`, `wall_clock_s`, `bead_ids`.

### Bridge (`colony/bridge.ts`)

The Bridge is a deterministic (no LLM) TypeScript module that synchronizes tmup task completion to sdlc-os bead markdown files. It is called by the Conductor via `bridge-cli.ts` after evaluating each completed or failed task.

**Status transitions:**

| Loop Level | From | To |
|-----------|------|----|
| L0 | `running` | `submitted` |
| L1 | `submitted` | `verified` |
| L2 | `verified` | `proven` |
| L2.5 | `proven` | `hardened` |
| L2.75 | `hardened` | `reliability-proven` |

**Core function `bridgeUpdateBead()`:**
1. Checks SC-COL-14: rejects `null`/`undefined`/empty loop level as fatal
2. Reads the bead file and parses fields
3. On task failure: appends a correction entry (no status change) and returns `action: 'correction'`
4. On task success: validates output (SC-COL-22), then performs compare-and-swap on bead status (SC-COL-15)
5. If bead is already at or beyond the target status, returns `action: 'skipped'` (idempotent)
6. At L0, verifies the clone has commits beyond `origin/main` or `origin/master` (SC-COL-26)
7. Writes updated bead file atomically via temp + rename (SC-COL-28)

**`bridgeCommitBeadUpdate()`:**
1. Verifies current git branch matches `expectedBranch` (SC-COL-30)
2. Stages only the specific bead file with `git add -- <file>` (SC-COL-29) -- never `git add -A`
3. Commits with message `fix(sdlc): bridge update bead {beadId} [{loopLevel}]`
4. Uses `execFileSync` throughout (no shell injection)

**`markBridgeSynced()`:** Sets `bridge_synced = 1` on the tmup task after a successful bead commit, so the Deacon's `check_for_work()`, clone pruning, and recovery know the bead file is up to date.

**Safety constraints enforced:**

| ID | Description |
|----|-------------|
| SC-COL-14 | NULL loop level is a fatal error |
| SC-COL-15 | Compare-and-swap on bead status (rejects unexpected current status) |
| SC-COL-22 | Output validation: file exists, >100 bytes, contains `<!-- BEAD_OUTPUT_COMPLETE -->` sentinel |
| SC-COL-26 | Clone must have commits beyond source HEAD before L0 advancement |
| SC-COL-28 | Atomic file write via temp + rename |
| SC-COL-29 | `git add -- <specific-file>` only |
| SC-COL-30 | Verify branch before commit |

**Telemetry:** Every bridge call appends a JSONL entry to the bridge log (default `/tmp/sdlc-colony/colony-bridge.log`, override via `COLONY_BRIDGE_LOG` env var). Fields: `timestamp`, `bead_id`, `loop_level`, `action`, `elapsed_ms`, `safety_constraints`, `error`.

**CLI usage (`bridge-cli.ts`):**

Successful completion:
```bash
npx tsx colony/bridge-cli.ts \
  --bead-file docs/sdlc/active/{task-id}/beads/{bead-id}.md \
  --clone-dir /tmp/sdlc-colony/{session}/worker-{agent-id} \
  --loop-level L0 \
  --completed \
  --project-dir /path/to/project \
  --expected-branch main \
  --expected-status running \
  --task-id <tmup-task-id> \
  --db-path /path/to/tmup.db
```

Failed task (append correction):
```bash
npx tsx colony/bridge-cli.ts \
  --bead-file docs/sdlc/active/{task-id}/beads/{bead-id}.md \
  --clone-dir /tmp/sdlc-colony/{session}/worker-{agent-id} \
  --loop-level L0 \
  --finding "Tests failed: src/foo.test.ts line 42" \
  --cycle 1 \
  --project-dir /path/to/project \
  --expected-branch main
```

Required arguments: `--bead-file`, `--clone-dir`, `--loop-level`, `--project-dir`, `--expected-branch`.
Optional: `--completed` (flag), `--finding`, `--cycle`, `--expected-status` (CAS), `--task-id`, `--db-path`.

Output: JSON on stdout. Exit code 0 on success, 1 on failure. When `--task-id` and `--db-path` are provided and the bridge advances a bead successfully, `bridge_synced` is automatically set to 1.

### Bead Parser (`colony/bead-parser.ts`)

Deterministic markdown parser for bead files. Uses regex (`**FieldName:** value` format) with no LLM involvement.

**Required fields:** `BeadID`, `Status` (throws if missing).

**Optional fields with defaults:** `LoopLevel` (`L0`), `WorkerType` (`codex`), `Phase` (`execute`), `CynefinDomain` (`complicated`), `Description`, `AcceptanceCriteria`, `ScopeFiles`, `Output`, `CorrectionHistory`.

**Exports:**
- `parseBeadFile(content)` -- Parse markdown into `BeadFields` struct
- `updateBeadField(content, fieldName, newValue)` -- Replace or append a field value
- `appendCorrection(content, level, cycle, finding)` -- Append a `- [L{level} cycle {cycle}] {finding}` entry to `CorrectionHistory`

### Clone Manager (`colony/clone-manager.sh`)

Bash library providing git clone lifecycle management for colony workers. Source it and call functions directly.

**Functions:**

| Function | Description |
|----------|-------------|
| `colony_clone_create <source> <session> <agent_id>` | Full `git clone file://` into `$COLONY_BASE/{session}/worker-{agent_id}`. Sets push URL to `no-push` (SC-COL-27). Prints clone path on stdout. |
| `colony_clone_verify <clone_dir>` | Validates clone: path under `$COLONY_BASE` (SC-COL-12), `.git` exists (SC-COL-12), push URL is `no-push` (SC-COL-27). Returns 0/1. |
| `colony_clone_has_commits <clone_dir>` | Checks for commits beyond `origin/main` (SC-COL-26). Returns 0 if commits exist, 1 otherwise. |
| `colony_clone_prune <clone_dir> <bridge_synced>` | Removes clone. Refuses if `bridge_synced != 1` (SC-COL-21). Validates path under `$COLONY_BASE` before `rm -rf`. |
| `colony_clone_recover_output <clone_dir> <task_id>` | Copies `bead-output.md` and `correction.json` to `$COLONY_BASE/recovered-outputs/{task_id}/`. |

**`COLONY_BASE`** defaults to `/tmp/sdlc-colony`.

**Telemetry:** All functions log to `$COLONY_BASE/clone-events.log` as JSONL via the `_colony_log` helper. Fields include `timestamp`, `event`, and function-specific key-value pairs (`clone_dir`, `elapsed_ms`, `clone_bytes`, `valid`, etc.).

### Conductor Protocol (`colony/conductor-prompt.md`)

The Conductor is an Opus-tier Claude Code session launched by the Deacon. Its system prompt defines four session types:

**DISPATCH:** Triggered when pending beads exist. Reads the bead manifest from `state.md` and bead files on disk. For each dispatchable bead (respecting dependency order per SC-COL-10 and checking for duplicate active tasks per SC-COL-09), it creates a tmup task, writes `bead-context.md` to the worker's clone, and calls `tmup_dispatch` with `worker_type` and `clone_isolation: true`.

**EVALUATE:** Triggered when workers complete or fail tasks. For each bead, the Conductor reads output from the clone, calls the bridge CLI to update the bead file, and dispatches the next loop level. L0 completion leads to L1 (Sentinel), L1 to L2 (Oracle), L2 to L2.5 (AQS, runs inline), L2.5 to L2.75 (Harden, runs inline). AQS (L2.5) and Harden (L2.75) run inline within the Conductor session using the Agent tool -- they are not dispatched as tmup tasks.

**SYNTHESIZE:** Triggered when all beads reach terminal status. Performs sequential merge of completed clones into the main checkout using the Refinery Pattern: orders clones by dependency graph, attempts fast-forward merges, dispatches resolver workers on conflicts. Runs fitness checks and writes `delivery.md`.

**RECOVER:** Triggered when the Deacon detects stale state. Reconciles tmup task status against bead files, re-runs bridge for unsynced completions, resets stale claims, and verifies clone integrity.

**Session bootstrap protocol (all types):**
1. `tmup_init` (idempotent reattach)
2. Write pre-flight handoff block to `state.md` (SC-COL-04)
3. `tmup_status` -- read session state
4. `tmup_inbox` -- read unread messages

**Colony mode detection:** Defined in `skills/sdlc-orchestrate/colony-mode.md`. After Phase 3 (Architect) produces a bead manifest, the Conductor calls `tmup_status`. If it returns a valid session, colony mode is active. Otherwise, sync mode (Agent tool dispatch) is used. Colony mode is detected, not configured -- there is no flag.

**Cost controls:**

| Control | Default |
|---------|---------|
| Per-session ceiling (Conductor) | $10.00 |
| Per-bead ceiling (Deacon-enforced) | $50.00 |
| Worker ceiling (sonnet/claude_code) | $3.00 |
| Worker ceiling (haiku) | $0.50 |

### tmup Extensions

Colony mode extends tmup with new types, schema columns, and tool parameters.

**New types (`tmup/shared/src/types.ts`):**

| Type | Values |
|------|--------|
| `CynefinDomain` | `clear`, `complicated`, `complex`, `chaotic`, `confusion` |
| `SdlcLoopLevel` | `L0`, `L1`, `L2`, `L2.5`, `L2.75` |
| `SdlcPhase` | `frame`, `scout`, `architect`, `execute`, `synthesize` |
| `WorkerType` | `codex`, `claude_code` |

`TaskCorrectionRow`: tracks per-task correction state with fields `task_id`, `level`, `cycle`, `max_cycles`, `last_finding`.

**Migration v4 (`tmup/shared/src/migrations.ts`, line 259):**

New columns on `tasks` table:
- `bead_id TEXT` -- links task to bead
- `sdlc_loop_level TEXT` -- constrained to `L0`/`L1`/`L2`/`L2.5`/`L2.75`
- `output_path TEXT` -- path to worker output
- `clone_dir TEXT` -- path to isolated clone
- `worker_type TEXT DEFAULT 'codex'` -- constrained to `codex`/`claude_code`
- `bridge_synced INTEGER DEFAULT 0` -- whether bridge has updated bead file

New table `task_corrections`:
- Primary key: `(task_id, level)`
- Columns: `cycle`, `max_cycles` (default 2), `last_finding`

Indexes: `idx_tasks_bead` (partial, on `bead_id`), `idx_tasks_colony` (partial, on `sdlc_loop_level` + `status`).

**Constants (`tmup/shared/src/constants.ts`, line 57):**
- `CONDUCTOR_BUDGET_USD = 10.0`
- `WORKER_BUDGET_SONNET_USD = 3.0`
- `WORKER_BUDGET_HAIKU_USD = 0.5`
- `BEAD_BUDGET_USD = 50.0`
- `HEARTBEAT_THRESHOLDS`: per-domain (`clear`: 300s, `complicated`: 900s, `complex`: 1800s, `chaotic`: 300s, `confusion`: 900s)

**`tmup_heartbeat` tool:** Registers agent liveness. Accepts `agent_id` (required) and optional `codex_session_id`. Retries up to 3 times with 500ms backoff on `SQLITE_BUSY`. Returns `next_heartbeat_due` timestamp (SC-COL-19).

**`tmup_dispatch` tool:** Extended with two colony parameters:
- `worker_type` (`'codex'` | `'claude_code'`) -- determines launch path in `dispatch-agent.sh`
- `clone_isolation` (`boolean`) -- if true, creates an isolated git clone before launching the worker

**`dispatch-agent.sh` launch path (`tmup/scripts/dispatch-agent.sh`):**

When `--clone-isolation` is set, the script sources `clone-manager.sh`, calls `colony_clone_create` to create the clone, and `colony_clone_verify` to validate it. The `WORKING_DIR` is then set to the clone path.

Worker type determines the launch command:
- `claude_code`: Launches `claude -p --model sonnet --permission-mode bypassPermissions --plugin-dir tmup --max-budget-usd 3.00`. Reads prompt from a file, writes output to `session-output.json`. Uses MCP heartbeat (no background loop).
- `codex`: Starts a background heartbeat loop via `disown`, then `exec codex -s danger-full-access --no-alt-screen -C $WORKING_DIR`. Sends the prompt via `tmux send-keys` after detecting codex readiness.

After codex launch, the script captures the Codex session ID from `~/.codex/history.jsonl` (with a cwd correlation check to prevent cross-contamination in multi-dispatch scenarios) and stores it in both grid-state and the agents table via heartbeat.

## How To Use

### Starting a Colony Session

1. Ensure tmup is installed and the plugin is loaded in Claude Code.
2. Configure the systemd service file with your project paths:
   ```bash
   cp colony/systemd/sdlc-colony-deacon.service ~/.config/systemd/user/
   # Edit: set SDLC_PROJECT_DIR, TMUP_DB_PATH
   systemctl --user daemon-reload
   ```
3. Start the Deacon:
   ```bash
   systemctl --user start sdlc-colony-deacon
   ```
4. Start an SDLC workflow via the Conductor (e.g., `/sdlc` skill). After Phase 3 (Architect) produces beads, the Conductor detects colony mode via `tmup_status` and dispatches beads as tmup tasks.
5. The Deacon watches the DB and spawns Conductor sessions as work progresses through loop levels.

Alternatively, run the Deacon manually for development:
```bash
TMUP_DB_PATH=/path/to/tmup.db \
SDLC_PROJECT_DIR=/path/to/project \
python3 colony/deacon.py
```

### Monitoring

**Log files:**

| File | Location | Contents |
|------|----------|----------|
| `colony-sessions.log` | `colony/colony-sessions.log` | JSONL. One record per Conductor session: session ID, cost, wall clock time, exit code, bead IDs |
| `colony-bridge.log` | `/tmp/sdlc-colony/colony-bridge.log` | JSONL. One record per bridge call: bead ID, loop level, action, elapsed ms, constraints checked, errors |
| `clone-events.log` | `/tmp/sdlc-colony/clone-events.log` | JSONL. Clone lifecycle events: create, verify, commit check, prune, output recovery |
| systemd journal | `journalctl --user -u sdlc-colony-deacon` | Deacon state transitions, errors, watchdog events |

**`audit-metrics.sh`:**
```bash
bash colony/audit-metrics.sh
# Or with custom log paths:
bash colony/audit-metrics.sh --sessions-log /path/to/sessions.log --bridge-log /path/to/bridge.log
```

Outputs: total sessions, total cost (USD), average cost per session, average/total wall clock time, bridge action counts by type, average/max bridge latency, and SC-COL constraint hit counts.

**Key metrics to watch:**
- Conductor session cost (should stay under $10.00 per session)
- Bridge error rate (high `error` action count indicates systemic issues)
- Wall clock time (sessions near 30-minute timeout may need investigation)
- SC-COL constraint hits in bridge errors (reveals safety system activations)
- Stale heartbeat recoveries in Deacon logs (reveals worker reliability issues)

### Smoke Testing

```bash
bash colony/smoke-test.sh
```

Runs 6 self-contained integration tests, each with its own temp directories and cleanup:

| Test | What it validates |
|------|-------------------|
| ST-01 | Bridge CLI round-trip: `running` -> `submitted`, git commit created |
| ST-02 | Bridge rejects missing output sentinel |
| ST-03 | Bridge CAS rejects status mismatch |
| ST-04 | Clone Manager lifecycle: create, verify, has_commits, prune (synced/unsynced) |
| ST-05 | Deacon recognizes stale lock (dead PID, old timestamp) |
| ST-06 | Deacon `check_for_work()` detects pending colony tasks |

Exit code 0 if all 6 pass, 1 otherwise.

### Troubleshooting

**Lock file issues:**
- Symptom: Deacon logs "cannot spawn conductor" but no Conductor is running.
- Check: `cat /tmp/sdlc-colony-conductor.lock` -- contains PID and timestamp.
- Fix: If the PID is dead (`kill -0 <pid>` fails), remove the lock: `rm /tmp/sdlc-colony-conductor.lock`. The Deacon does this automatically for locks older than 180 seconds.

**Bridge lock blocking timeout:**
- Symptom: Deacon logs `bridge_lock_deferral` repeatedly.
- Check: `cat /tmp/sdlc-colony-bridge.lock`. If PID is dead or timestamp > 60 seconds, the Deacon treats it as stale.
- Fix: Remove `/tmp/sdlc-colony-bridge.lock` if the bridge process is dead.

**Stale claims:**
- Symptom: Tasks stuck in `claimed` status with no worker activity.
- Check: `journalctl --user -u sdlc-colony-deacon | grep heartbeat_stale`.
- Fix: Send `SIGUSR2` to the Deacon PID to force a recovery cycle: `kill -USR2 $(pidof python3 deacon.py)`. Or wait -- the Deacon checks heartbeats every 60 seconds.
- Per-domain thresholds: `clear`/`chaotic` = 5min, `complicated`/`confusion` = 15min, `complex` = 30min.

**Bridge failures:**
- Symptom: Tasks complete but bead files do not advance.
- Check: `colony-bridge.log` for error entries. Common causes:
  - `SC-COL-14`: Task dispatched without a loop level. Fix the dispatch logic.
  - `SC-COL-15`: Bead status changed between dispatch and bridge call. The bead may already be advanced (check `action: 'skipped'`).
  - `SC-COL-22`: Worker did not produce valid output. Check `bead-output.md` in the clone for size, sentinel.
  - `SC-COL-26`: Worker clone has no commits. The worker may have crashed before committing.
  - `SC-COL-30`: Branch mismatch. Verify `EXPECTED_BRANCH` matches the project's current branch.

**Workers not starting:**
- Check tmux panes: `tmux list-panes -t <session>`.
- Check grid state: `cat <state-dir>/grid/grid-state.json | jq '.panes'`.
- Verify `codex` or `claude` CLI is on PATH.

**Database locked errors:**
- The Deacon uses WAL mode with `busy_timeout=8000`. If locks persist, check for other processes holding the DB.
- tmup_heartbeat retries 3 times with 500ms backoff on `SQLITE_BUSY`.

## Safety Constraints

| ID | Description | Enforced in | How tested |
|----|-------------|-------------|------------|
| SC-COL-01 | Self-watchdog: SIGTERM if timer hasn't fired in 90s | `deacon.py` `_self_watchdog_task()` | `deacon_test.py` |
| SC-COL-04 | Pre-flight handoff block written before evaluation | `conductor-prompt.md` bootstrap protocol | Manual (Conductor behavior) |
| SC-COL-05 | Wall-clock timeout on Conductor (30min dispatch, 60min synthesize) | `deacon.py` `_check_conductor_timeout()` | `deacon_test.py` |
| SC-COL-06 | Check bridge lock before sending SIGTERM to Conductor | `deacon.py` `_check_conductor_timeout()` | `deacon_test.py` |
| SC-COL-09 | Check existing active tasks before creating duplicates | `conductor-prompt.md` DISPATCH rules | Manual (Conductor behavior) |
| SC-COL-10 | Check bead dependency graph before dispatch | `conductor-prompt.md` DISPATCH rules | Manual (Conductor behavior) |
| SC-COL-12 | Verify clone path under COLONY_BASE + .git exists | `clone-manager.sh` `colony_clone_verify()` | `clone-manager.test.sh`, `smoke-test.sh` ST-04 |
| SC-COL-13 | Cancel stale active tasks before retry dispatch | `conductor-prompt.md` EVALUATE rules | Manual (Conductor behavior) |
| SC-COL-14 | NULL loop level is a fatal error | `bridge.ts` `bridgeUpdateBead()` | `bridge.test.ts` (3 tests), `smoke-test.sh` ST-02 |
| SC-COL-15 | Compare-and-swap on bead status | `bridge.ts` `bridgeUpdateBead()` | `bridge.test.ts` (3 tests), `smoke-test.sh` ST-03 |
| SC-COL-19 | tmup_heartbeat returns next_heartbeat_due | `tmup/mcp-server` heartbeat handler | tmup test suite |
| SC-COL-20 | Per-domain heartbeat stale thresholds | `deacon.py` `recover_stale_claims()` | `deacon_test.py` |
| SC-COL-21 | Refuse clone prune if bridge not synced; recover output first | `clone-manager.sh` `colony_clone_prune()`, `deacon.py` | `smoke-test.sh` ST-04, `clone-manager.test.sh` |
| SC-COL-22 | Verify bead-output.md: exists, >100 bytes, has sentinel | `bridge.ts` `validateOutput()` | `bridge.test.ts` (4 tests), `smoke-test.sh` ST-02 |
| SC-COL-26 | Verify clone has commits beyond source HEAD at L0 | `bridge.ts` `verifyCloneHasCommits()`, `clone-manager.sh` | `bridge.test.ts` (3 tests), `clone-manager.test.sh` |
| SC-COL-27 | Set no-push remote URL on clones | `clone-manager.sh` `colony_clone_create()` | `smoke-test.sh` ST-04, `clone-manager.test.sh` |
| SC-COL-28 | Atomic write via temp + rename | `bridge.ts` `atomicWriteFile()` | `bridge.test.ts` |
| SC-COL-29 | `git add -- <specific-file>` only (never `git add -A`) | `bridge.ts` `bridgeCommitBeadUpdate()` | `bridge.test.ts` |
| SC-COL-30 | Verify branch before commit | `bridge.ts` `bridgeCommitBeadUpdate()` | `bridge.test.ts` |

## Configuration Reference

### Environment Variables

| Variable | Default | Used by | Description |
|----------|---------|---------|-------------|
| `TMUP_DB_PATH` | (required) | Deacon | Path to tmup SQLite database |
| `SDLC_PROJECT_DIR` | (required) | Deacon | Project root directory |
| `CONDUCTOR_BUDGET_USD` | `10.00` | Deacon | Per-session budget for Conductor |
| `EXPECTED_BRANCH` | `main` | Deacon, Bridge | Expected git branch for commits |
| `COLONY_BASE` | `/tmp/sdlc-colony` | Clone Manager | Base directory for clones and logs |
| `COLONY_BRIDGE_LOG` | `/tmp/sdlc-colony/colony-bridge.log` | Bridge | Path for bridge telemetry log |
| `CODEX_BIN` | `$(which codex)` or `~/.local/bin/codex` | dispatch-agent.sh | Path to Codex CLI binary |
| `SDLC_OS_PLUGIN` | `/home/q/.claude/plugins/sdlc-os` | dispatch-agent.sh | Path to sdlc-os plugin directory |

### Constants (code-level)

| Constant | Value | File | Description |
|----------|-------|------|-------------|
| `STALE_LOCK_TIMEOUT_S` | 180 | `deacon.py` | Conductor lock staleness threshold |
| `BRIDGE_STALE_TIMEOUT_S` | 60 | `deacon.py` | Bridge lock staleness threshold |
| `CONDUCTOR_TIMEOUT_DISPATCH_S` | 1800 (30min) | `deacon.py` | Wall-clock timeout for DISPATCH |
| `CONDUCTOR_TIMEOUT_SYNTHESIZE_S` | 3600 (60min) | `deacon.py` | Wall-clock timeout for SYNTHESIZE |
| `DEBOUNCE_S` | 2.0 | `deacon.py` | Delay after Conductor exit before re-check |
| `TIMER_INTERVAL_S` | 60 | `deacon.py` | Main loop poll interval |
| `WATCHDOG_SELF_TIMEOUT_S` | 90 | `deacon.py` | Self-watchdog threshold (SC-COL-01) |
| `OUTPUT_SENTINEL` | `<!-- BEAD_OUTPUT_COMPLETE -->` | `bridge.ts` | Required sentinel in bead-output.md |
| `MIN_OUTPUT_BYTES` | 100 | `bridge.ts` | Minimum bead-output.md size |

### File Paths

| Path | Description |
|------|-------------|
| `/tmp/sdlc-colony-conductor.lock` | Conductor process lock (PID + timestamp) |
| `/tmp/sdlc-colony-bridge.lock` | Bridge process lock |
| `/tmp/sdlc-colony/` | Clone base directory |
| `/tmp/sdlc-colony/{session}/worker-{agent}` | Isolated worker clone |
| `/tmp/sdlc-colony/recovered-outputs/{task-id}/` | Preserved output from crashed workers |
| `/tmp/sdlc-colony/colony-bridge.log` | Bridge telemetry log |
| `/tmp/sdlc-colony/clone-events.log` | Clone Manager telemetry log |
| `colony/colony-sessions.log` | Conductor session cost/timing log |
| `colony/conductor-prompt.md` | Conductor system prompt |

## Test Coverage

| Suite | File | Framework | Count | What it covers |
|-------|------|-----------|-------|----------------|
| Bridge unit tests | `colony/bridge.test.ts` | vitest | 31 | Status transitions, SC-COL-14/15/22/26/28/29/30, CAS bypass rejection, idempotent skip, correction append, commit isolation |
| Bead parser unit tests | `colony/bead-parser.test.ts` | vitest | 9 | Field parsing, defaults, required field validation, field update, correction append |
| Deacon unit tests | `colony/deacon_test.py` | pytest | 59 | State machine transitions, check_for_work (7 scenarios), can_spawn_conductor (5 lock states), spawn_conductor, recover_stale_claims, per-domain heartbeat thresholds, wall-clock timeout, bridge lock deferral, watchdog, inotifywait |
| Clone Manager tests | `colony/clone-manager.test.sh` | bash | -- | Clone create, verify, has_commits, prune, recover_output |
| Smoke tests | `colony/smoke-test.sh` | bash | 6 | End-to-end: bridge CLI round-trip (ST-01), sentinel rejection (ST-02), CAS rejection (ST-03), clone lifecycle (ST-04), Deacon lock (ST-05), check_for_work (ST-06) |

**How to run:**

```bash
# TypeScript tests (bridge + bead-parser)
cd colony && npx vitest run

# Python tests (deacon)
cd colony && python3 -m pytest deacon_test.py -v

# Clone Manager tests
bash colony/clone-manager.test.sh

# Smoke tests (integration, creates temp repos)
bash colony/smoke-test.sh
```
