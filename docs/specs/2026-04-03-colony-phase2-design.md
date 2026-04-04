# Colony Runtime Phase 2 Design Spec

**Date:** 2026-04-03
**Status:** Draft (pending council review)
**Scope:** 7 items, ~600-800 LOC, no new daemons, no spec violations
**Prerequisite:** Phase 1 complete (council-accepted, 820 tests, all pushed)

---

## 1. Problem Statement

Phase 1 delivered a working colony runtime (Deacon + Conductor + Workers + Bridge). Council acceptance identified 3 remaining gaps, and a 7-agent deep-dive found 5 production reliability issues plus 7 thinker principles not yet embedded. This spec addresses the load-bearing subset — items that prevent the colony from running autonomously in production.

## 2. Design Principles

- **No new daemons.** Boot and Dogs are absorbed into the existing Deacon. The 3-component architecture (Deacon + Conductor + Bridge) is preserved.
- **No spec violations.** Wisps (bypass Git) and Clear fast path (bypass quality loops) are cut.
- **Enhance, don't duplicate.** Existing self-watchdog, clone-manager, and sdlc-crossmodel skill are extended, not replaced.
- **Measure before optimizing.** Convoys, Wisps, and Chaos deferred to Phase 3 pending baseline completion metrics.

## 3. Items

### 3.1 Deacon Behavioral Watchdog (enhance existing)

**Problem:** Self-watchdog only checks timer-fire liveness. Deacon stuck in CONDUCTING for 60 minutes without timeout firing is undetected.

**Fix:** Add time-in-state tracking to `_self_watchdog_task`:
- If CONDUCTING state exceeds `CONDUCTOR_TIMEOUT_SYNTHESIZE_S + 300s` (65 min), force transition to RECOVERING regardless of lock state.
- Log `watchdog_state_timeout state=CONDUCTING elapsed_s=3900 action=force_recover`

**Safety:** New constraint SC-COL-35: Watchdog MUST force RECOVERING if any single state exceeds max-state-duration.

**Tests:** Set `_state_entered_at` to past, run watchdog, assert RECOVERING transition.

**LOC:** ~30

### 3.2 Deacon Escalation (spec SS3.4)

**Problem:** Stuck bead loops to $50 ceiling with no human notification. Spec requires WhatsApp alert after 3 consecutive Conductor failures per bead.

**Fix:**
- Add `_bead_failure_counts: dict[str, list[float]]` to Deacon (bead_id -> failure timestamps)
- In `run_deacon` CONDUCTING exit path: if exit_code != 0, increment failure count for all in-flight bead_ids
- If any bead_id has 3 failures within 1 hour: call `_send_escalation_alert(bead_id, last_error)` and add to `_blacklisted_beads`
- `_send_escalation_alert`: async subprocess with 10s timeout (not blocking curl)
- SIGUSR1 handler: clear blacklist, log `blacklist_cleared`
- `check_for_work()` SQL: exclude blacklisted bead_ids

**Tests:** 3-failure trigger, blacklist exclusion, SIGUSR1 clear, async timeout on alert.

**LOC:** ~120

### 3.3 Deacon Clone Pruning (Dogs absorbed)

**Problem:** RRT-01 — clones never pruned by runtime. Disk fills silently. No log rotation.

**Fix:**
- Add `_prune_stale_clones()` method to Deacon, called at end of each WATCHING evaluation cycle
- Query tmup: find tasks with `bridge_synced=1` AND `clone_dir IS NOT NULL` AND `clone_dir` still exists on disk
- For each: call `colony_clone_prune` (source clone-manager.sh) or delete directly with path validation
- Also prune clones older than 24h regardless of bridge_synced (spec SS6.3 ExecStopPost)
- Add log rotation: truncate log files exceeding 10MB, keeping last 1000 lines

**Safety:** SC-COL-31 (from STPA): MUST check bridge_synced=1 before deleting any clone_dir.

**Tests:** Prune synced clone, refuse unsynced, 24h age override, log rotation.

**LOC:** ~100

### 3.4 Codex Cross-Model Wiring

**Problem:** sdlc-crossmodel skill exists and is fully specified, but conductor-prompt.md EVALUATE section has no FFT-14 trigger.

**Fix:**
- Add to conductor-prompt.md EVALUATE section (after L2.5 AQS inline): "After AQS completes, evaluate FFT-14. If FULL or TARGETED: invoke sdlc-os:sdlc-crossmodel with bead context. Codex workers dispatch via tmup_dispatch with worker_type=codex. crossmodel-triage deduplicates against AQS. Net-new findings are HIGH priority corrections."
- Add to colony-mode.md: note that cross-model workers use worker_type=codex

**Tests:** None (documentation change). Validated by Conductor behavior during live colony run.

**LOC:** ~20 (prompt/doc changes)

### 3.5 SC-COL-05 SYNTHESIZE E2E Test

**Problem:** SYNTHESIZE 60-min timeout path exists but zero tests exercise it. PROGRESS.md self-reports PARTIAL.

**Fix:**
- Add `TestSynthesizeTimeout` to deacon_test.py: mock a conductor that runs past 60 minutes in SYNTHESIZE mode, assert SIGTERM is sent at 60min not 30min
- Add ST-07 to smoke-test.sh: insert all tasks as terminal+synced, verify check_for_work returns "synthesize"

**Tests:** 2 new tests.

**LOC:** ~60

### 3.6 Completion Metrics + Per-Bead Cost Ceiling

**Problem:** Per-bead cost aggregation specified in spec SS3.2 and SS8 but not implemented. $50/bead ceiling not enforced.

**Fix:**
- Add `_aggregate_bead_cost(bead_id) -> float` to Deacon: parse colony-sessions.log, sum cost across sessions sharing bead_id
- In `check_for_work()`: after finding actionable tasks, filter out beads exceeding $50 cost ceiling. Add to blacklist with reason "cost_ceiling"
- Add `bead_completion_rate()` function: `beads_merged / beads_dispatched` from session log
- Add to audit-metrics.sh: per-bead cost report, completion rate, p50/p95 wall_clock

**Tests:** Cost aggregation, ceiling enforcement, completion rate calculation.

**LOC:** ~100

### 3.7 Production Reliability Fixes (RRT-01 through RRT-05)

**RRT-01:** Clone pruning — covered by 3.3 above.

**RRT-02:** inotifywait silent death. Fix: log WARNING when `watch_db_changes` readline returns empty (watcher died). Add `watcher_died` event. Main loop detects watcher task completion and restarts it.

**RRT-03:** `conn.rollback()` on unbound variable. Fix: wrap recovery in `conn = self._get_db()` with explicit `try/except` that catches both `sqlite3.Error` AND `UnboundLocalError`, always transitions to WATCHING.

**RRT-04:** `markBridgeSynced` no busy_timeout. Fix: open Database with `{ timeout: 8000 }` option. Wrap in try/catch returning error result instead of throwing.

**RRT-05:** Bridge lock infinite deferral. Fix: add `MAX_BRIDGE_DEFERRAL_COUNT = 10` constant. After 10 deferrals (~10 minutes), force SIGTERM regardless of lock. Log `bridge_lock_force_kill deferrals=10`.

**Tests:** inotify restart, recovery exception handling, busy_timeout set, max deferral.

**LOC:** ~150

## 4. New Safety Constraints

| ID | Constraint | Item |
|----|-----------|------|
| SC-COL-31 | Dogs/pruning MUST check bridge_synced=1 before deleting clone_dir | 3.3 |
| SC-COL-35 | Watchdog MUST force RECOVERING if any state exceeds max-state-duration | 3.1 |
| SC-COL-36 | Escalation alert MUST NOT block Deacon main loop (async with timeout) | 3.2 |
| SC-COL-37 | Bridge lock deferral MUST have a maximum count before force-kill | 3.7 |

## 5. What Is NOT In This Spec

| Item | Reason | When |
|------|--------|------|
| Boot (separate daemon) | Duplicates systemd + self-watchdog | Never |
| Dogs (separate daemon) | Absorbed into Deacon 3.3 | Done |
| Seancing (session resume) | Pre-flight handoff covers it; -p resume unvalidated | Phase 3 if needed |
| Convoys | Premature; dependency graph suffices | Phase 3 |
| Wisps | Violates SC-COL-29 (Git commit required) | Cut |
| Clear fast path | Undermines quality loops | Cut |
| PDSA watchdog | Already implemented as self-watchdog | Renamed |
| Chaos probing | No baseline metrics yet | Phase 3 |

## 6. Estimated Totals

| Metric | Value |
|--------|-------|
| New/modified LOC | ~580 |
| New tests | ~15 |
| New safety constraints | 4 |
| Files modified | deacon.py, bridge.ts, conductor-prompt.md, colony-mode.md, smoke-test.sh, audit-metrics.sh |
| New files | None |
| Risk | LOW — all changes enhance existing components |

---

## 7. Council Review Findings (2026-04-03)

### Test Integrity: ACCEPT_WITH_CONDITIONS

Conditions addressed inline:

**C1 — Cost apportionment:** Per-session cost is split equally across bead_ids in that session: `cost_per_bead = total_cost_usd / len(bead_ids)`. This is approximate but sufficient for ceiling enforcement ($50 is a guard rail, not accounting).

**C2 — Thinker principles tracking:** 7 HIGH-priority thinker principles from the deep-dive are tracked in `docs/research/2026-03-26-reconciled-delta.md` items NE-6, NE-11, NE-13, NE-15, NE-22, NE-23, NE-24. Phase 3 backlog.

**C3 — Clone prune dependency:** Item 3.3 must execute after 3.6 blacklist initialization within the same Deacon loop tick. Ordering enforced by calling `_prune_stale_clones()` after `check_for_work()` which runs the cost ceiling check.

### Adversarial: FRAGILE — Fixes Applied

**CRITICAL-1 — Clone pruning race with higher loop levels:**
Fix: `_prune_stale_clones` must check ALL tasks sharing a `clone_dir`, not just bridge_synced. SQL: `SELECT COUNT(*) FROM tasks WHERE clone_dir = ? AND status NOT IN ('completed','cancelled')`. Only prune when zero active tasks remain for that clone.

**CRITICAL-2 — Escalation no delivery guarantee:**
Fix: On curl failure, append alert to `~/agents/lab/escalation-deadletter.jsonl`. SIGUSR1 handler re-drains dead-letter on next successful connection. Alert is never silently lost.

**HIGH-1 — Watchdog 65-min threshold not configurable:**
Fix: Read from env `WATCHDOG_MAX_STATE_DURATION_S` with default `CONDUCTOR_TIMEOUT_SYNTHESIZE_S + 300`. Configurable per deployment.

**HIGH-2 — Clone pruning blocks main loop:**
Fix: Run `_prune_stale_clones` via `asyncio.to_thread()`. Update `_last_timer_fire` after each clone deletion to prevent watchdog false alarm.

**HIGH-3 — RRT-05 force-kill during git commit:**
Fix: Before force-SIGTERM, check for `.git/index.lock` in project dir. If present, wait up to 30s for it to clear. Only then kill.

**HIGH-4 — Synthesize query scope mismatch:**
Fix: Add `sdlc_loop_level IS NOT NULL` filter to synthesize total-count query, matching the actionable-work query scope.

### Pre-existing Gap (not Phase 2 regression)

Bridge lock file (`BRIDGE_LOCK_FILE`): SC-COL-06/37 check this file but bridge.ts never writes it. Tracked for Phase 3.

---

## 8. Revised Safety Constraints

| ID | Constraint | Item |
|----|-----------|------|
| SC-COL-31 | Clone prune MUST verify zero active tasks share the clone_dir (not just bridge_synced) | 3.3 |
| SC-COL-35 | Watchdog MUST force RECOVERING if state exceeds configurable max-state-duration | 3.1 |
| SC-COL-36 | Escalation MUST NOT block main loop; failed alerts go to dead-letter file | 3.2 |
| SC-COL-37 | Bridge lock deferral MUST have max count; check .git/index.lock before force-kill | 3.7 |

## 9. Revised Totals

| Metric | Value |
|--------|-------|
| New/modified LOC | ~700 (was ~580, +120 for adversarial fixes) |
| New tests | ~20 (was ~15, +5 for adversarial) |
| New safety constraints | 4 (SC-COL-31/35/36/37, revised per adversarial) |
| Files modified | deacon.py, bridge.ts, conductor-prompt.md, colony-mode.md, smoke-test.sh, audit-metrics.sh |
| New files | None |
| Risk | LOW — all changes enhance existing components |

## 10. Council Verdict

**ACCEPT** — both reviewers' findings incorporated. No remaining CRITICAL or HIGH issues.
