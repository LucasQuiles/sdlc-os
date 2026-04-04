# Colony Runtime Phase 2 Implementation Plan

**Goal:** Harden the colony runtime for autonomous production operation. Add behavioral watchdog, escalation alerts, clone pruning, cross-model wiring, SYNTHESIZE E2E coverage, per-bead cost ceiling, and 4 reliability fixes. ~700 LOC across 6 existing files, no new daemons, no new files.

**Architecture:** Same 3-component architecture (Deacon + Conductor + Bridge). All changes enhance existing components. New safety constraints SC-COL-31/35/36/37.

**Tech Stack:** Python 3.12 + asyncio (Deacon), TypeScript + better-sqlite3 (Bridge), Bash (smoke-test, audit-metrics), Markdown (conductor-prompt, colony-mode)

**Spec:** `docs/specs/2026-04-03-colony-phase2-design.md` (219 lines, council-accepted)

## RAG Context

RAG_DEGRADED: No indexed content exists for the colony runtime module. Colony code (deacon.py, bridge.ts, conductor-prompt.md) was written in Phase 1 (2026-04-03) and has not yet been ingested into any Pinecone namespace.

| Query | Index/Namespace | Hits | Takeaway |
|-------|----------------|------|----------|
| "colony deacon watchdog timeout escalation blacklist clone pruning" | oneplatform-codebase-v2 / claude, codex | 0 | Colony module not indexed |
| "bridge.ts markBridgeSynced busy_timeout better-sqlite3 reliability inotifywait watcher restart" | oneplatform-codebase-v2 / claude | 0 | Bridge module not indexed |
| "colony runtime production reliability asyncio watchdog timeout" | oneplatform-codebase-v2 / bes-notes | 0 | No design notes indexed |

**Mitigation:** All implementation context was sourced directly from the spec (`docs/specs/2026-04-03-colony-phase2-design.md`, 219 lines), the Phase 1 source files (`colony/deacon.py` 844 lines, `colony/bridge.ts` 430 lines), and the existing test file (`colony/deacon_test.py`). No reuse candidates exist -- these are enhancements to code written earlier today.

---

## Execution Controller

**Entry:** sdlc-os:sdlc-normalize on entry. sdlc-os:sdlc-reuse before each code task. superpowers:verification-before-completion at each gate.

**Dependency:** T1 -> T2 -> T3 (sequential, shared Deacon state). T4 independent. T5 depends on T1. T6 depends on T2. T7 independent of T1-T6.

**Parallel opportunities:** T4 + T7 can run alongside T1-T3. T5 + T6 after their deps.

**Progress:** Update `colony/PROGRESS.md` Phase 2 section after each task.

**Gate:** `pytest colony/deacon_test.py && npx vitest run colony/ && bash colony/smoke-test.sh`

---

## Task 1: Behavioral Watchdog (spec 3.1, SC-COL-35)

**Files:** `colony/deacon.py` (lines 34-55 constants, lines 487-504 `_self_watchdog_task`), `colony/deacon_test.py`

### Test (RED)

Add to `colony/deacon_test.py`:

```python
class TestBehavioralWatchdog:
    """SC-COL-35: Watchdog forces RECOVERING if state exceeds max duration."""

    def test_watchdog_forces_recovering_on_state_timeout(self, tmp_path: Path) -> None:
        db_path = str(tmp_path / "tasks.db")
        _create_test_db(db_path)
        deacon = Deacon(db_path=db_path, project_dir=str(tmp_path))
        deacon._state_entered_at = time.monotonic() - 5000  # far in the past
        deacon.state = DeaconState.CONDUCTING

        import asyncio
        asyncio.run(_self_watchdog_task_once(deacon))

        assert deacon.state == DeaconState.RECOVERING

    def test_watchdog_respects_configurable_threshold(self, tmp_path: Path) -> None:
        db_path = str(tmp_path / "tasks.db")
        _create_test_db(db_path)
        deacon = Deacon(db_path=db_path, project_dir=str(tmp_path))
        deacon._state_entered_at = time.monotonic() - 100  # only 100s
        deacon.state = DeaconState.CONDUCTING

        import asyncio
        with patch.dict(os.environ, {"WATCHDOG_MAX_STATE_DURATION_S": "3700"}):
            asyncio.run(_self_watchdog_task_once(deacon))

        assert deacon.state == DeaconState.CONDUCTING  # 100 < 3700, no trigger
```

### Implementation (GREEN)

Add constant at `colony/deacon.py` line 55:

```python
WATCHDOG_MAX_STATE_DURATION_S = int(
    os.environ.get("WATCHDOG_MAX_STATE_DURATION_S", str(CONDUCTOR_TIMEOUT_SYNTHESIZE_S + 300))
)
```

Replace `_self_watchdog_task` (lines 487-504) with:

```python
async def _self_watchdog_task(deacon: Deacon) -> None:
    """SC-COL-01 + SC-COL-35: Self-watchdog coroutine."""
    while True:
        await asyncio.sleep(TIMER_INTERVAL_S)
        # SC-COL-01: timer-fire liveness
        elapsed = time.monotonic() - deacon._last_timer_fire
        if elapsed > 60 and elapsed <= WATCHDOG_SELF_TIMEOUT_S:
            log.warning("watchdog_near_miss elapsed_s=%.1f threshold_s=90", elapsed)
        if elapsed > WATCHDOG_SELF_TIMEOUT_S:
            log.error("Self-watchdog triggered: timer hasn't fired in %.0fs, SIGTERM", elapsed)
            os.kill(os.getpid(), signal.SIGTERM)

        # SC-COL-35: time-in-state check
        max_dur = int(os.environ.get("WATCHDOG_MAX_STATE_DURATION_S",
                                      str(CONDUCTOR_TIMEOUT_SYNTHESIZE_S + 300)))
        state_elapsed = time.monotonic() - deacon._state_entered_at
        if state_elapsed > max_dur:
            log.error(
                "watchdog_state_timeout state=%s elapsed_s=%.0f max_s=%d action=force_recover",
                deacon.state.value, state_elapsed, max_dur,
            )
            deacon._transition_to(DeaconState.RECOVERING, "watchdog_state_timeout")
```

Extract single-iteration helper for testing:

```python
async def _self_watchdog_task_once(deacon: Deacon) -> None:
    """Single watchdog iteration (for testing)."""
    max_dur = int(os.environ.get("WATCHDOG_MAX_STATE_DURATION_S",
                                  str(CONDUCTOR_TIMEOUT_SYNTHESIZE_S + 300)))
    state_elapsed = time.monotonic() - deacon._state_entered_at
    if state_elapsed > max_dur:
        log.error(
            "watchdog_state_timeout state=%s elapsed_s=%.0f max_s=%d action=force_recover",
            deacon.state.value, state_elapsed, max_dur,
        )
        deacon._transition_to(DeaconState.RECOVERING, "watchdog_state_timeout")
```

```bash
pytest colony/deacon_test.py::TestBehavioralWatchdog -x
git add colony/deacon.py colony/deacon_test.py && git commit -m "feat(colony): add behavioral watchdog SC-COL-35 (spec 3.1)"
```

---

## Task 2: Escalation (spec 3.2, SC-COL-36)

**Files:** `colony/deacon.py` (Deacon class ~line 134, `check_for_work` ~line 225, `run_deacon` ~line 507), `colony/deacon_test.py`

### Test (RED)

```python
class TestEscalation:
    def test_three_failures_triggers_blacklist(self, tmp_path: Path) -> None:
        db_path = str(tmp_path / "tasks.db")
        _create_test_db(db_path)
        deacon = Deacon(db_path=db_path, project_dir=str(tmp_path))
        bead = "bead-001"
        now = time.time()
        deacon._bead_failure_counts[bead] = [now - 60, now - 30, now]
        deacon._evaluate_escalation(bead, "test error")
        assert bead in deacon._blacklisted_beads

    def test_blacklist_excludes_from_work(self, tmp_path: Path) -> None:
        db_path = str(tmp_path / "tasks.db")
        _create_test_db(db_path)
        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO tasks (id, status, sdlc_loop_level, bead_id) VALUES (?, ?, ?, ?)",
            ("t1", "pending", "L0", "bead-blocked"),
        )
        conn.commit(); conn.close()
        deacon = Deacon(db_path=db_path, project_dir=str(tmp_path))
        deacon._blacklisted_beads.add("bead-blocked")
        assert deacon.check_for_work() is False

    def test_sigusr1_clears_blacklist(self, tmp_path: Path) -> None:
        db_path = str(tmp_path / "tasks.db")
        _create_test_db(db_path)
        deacon = Deacon(db_path=db_path, project_dir=str(tmp_path))
        deacon._blacklisted_beads.add("bead-x")
        deacon._clear_blacklist()
        assert len(deacon._blacklisted_beads) == 0

    def test_dead_letter_on_alert_timeout(self, tmp_path: Path) -> None:
        db_path = str(tmp_path / "tasks.db")
        _create_test_db(db_path)
        deacon = Deacon(db_path=db_path, project_dir=str(tmp_path))
        dl_path = tmp_path / "escalation-deadletter.jsonl"
        with patch.dict(os.environ, {"ESCALATION_DEADLETTER": str(dl_path)}):
            import asyncio
            with patch("asyncio.create_subprocess_exec", side_effect=OSError("fail")):
                asyncio.run(deacon._send_escalation_alert("bead-x", "err"))
        assert dl_path.exists()
        data = json.loads(dl_path.read_text().strip())
        assert data["bead_id"] == "bead-x"
```

### Implementation (GREEN)

Add to Deacon dataclass (after `_db` field, line 155):

```python
_bead_failure_counts: dict[str, list[float]] = field(default_factory=dict)
_blacklisted_beads: set[str] = field(default_factory=set)
```

Add methods to Deacon class:

```python
def _record_bead_failure(self, bead_ids: list[str], error: str) -> None:
    """Record failure timestamps per bead. Trigger escalation at 3 within 1 hour."""
    now = time.time()
    for bead_id in bead_ids:
        timestamps = self._bead_failure_counts.setdefault(bead_id, [])
        timestamps.append(now)
        # Keep only last hour
        cutoff = now - 3600
        self._bead_failure_counts[bead_id] = [t for t in timestamps if t > cutoff]
        if len(self._bead_failure_counts[bead_id]) >= 3:
            self._evaluate_escalation(bead_id, error)

def _evaluate_escalation(self, bead_id: str, error: str) -> None:
    """Blacklist bead and fire async alert."""
    self._blacklisted_beads.add(bead_id)
    log.warning("bead_blacklisted bead_id=%s reason=3_failures_1h", bead_id)
    asyncio.ensure_future(self._send_escalation_alert(bead_id, error))

async def _send_escalation_alert(self, bead_id: str, error: str) -> None:
    """SC-COL-36: Non-blocking alert. Dead-letter on failure."""
    dl_path = os.environ.get("ESCALATION_DEADLETTER",
                             os.path.expanduser("~/agents/lab/escalation-deadletter.jsonl"))
    record = {"bead_id": bead_id, "error": error, "timestamp": time.time()}
    try:
        proc = await asyncio.create_subprocess_exec(
            "curl", "-sf", "-X", "POST",
            "-H", "Content-Type: application/json",
            "-d", json.dumps({"text": f"Colony escalation: bead {bead_id} failed 3x: {error}"}),
            os.environ.get("ESCALATION_WEBHOOK_URL", "http://localhost:9999/noop"),
            stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL,
        )
        await asyncio.wait_for(proc.wait(), timeout=10)
        if proc.returncode != 0:
            raise RuntimeError(f"curl exit {proc.returncode}")
    except Exception:
        log.warning("escalation_deadletter bead_id=%s", bead_id)
        with open(dl_path, "a") as f:
            f.write(json.dumps(record) + "\n")

def _clear_blacklist(self) -> None:
    """SIGUSR1 handler target: clear blacklist and drain dead-letter."""
    self._blacklisted_beads.clear()
    self._bead_failure_counts.clear()
    log.info("blacklist_cleared")
```

Modify `check_for_work()` SQL (line 236) -- add blacklist exclusion:

```python
# After the main query, before returning True:
if self._blacklisted_beads:
    placeholders = ",".join("?" * len(self._blacklisted_beads))
    row = conn.execute(
        f"""
        SELECT COUNT(*) as cnt FROM tasks
        WHERE sdlc_loop_level IS NOT NULL
          AND bead_id NOT IN ({placeholders})
          AND (status = 'pending'
               OR (status = 'completed' AND bridge_synced = 0)
               OR status = 'needs_review')
        """,
        tuple(self._blacklisted_beads),
    ).fetchone()
    if not (row and row["cnt"] > 0):
        # All remaining work is blacklisted
        return False
```

Add SIGUSR1 handler in `main()` (after SIGUSR2 handler, line 838):

```python
def _sigusr1_handler(signum: int, frame: Any) -> None:
    log.info("SIGUSR1 received, clearing blacklist")
    deacon._clear_blacklist()
signal.signal(signal.SIGUSR1, _sigusr1_handler)
```

```bash
pytest colony/deacon_test.py::TestEscalation -x
git add colony/deacon.py colony/deacon_test.py && git commit -m "feat(colony): add escalation + blacklist SC-COL-36 (spec 3.2)"
```

---

## Task 3: Clone Pruning (spec 3.3, SC-COL-31)

**Files:** `colony/deacon.py` (Deacon class), `colony/deacon_test.py`

### Test (RED)

```python
class TestClonePruning:
    def test_prune_synced_clone(self, tmp_path: Path) -> None:
        db_path = str(tmp_path / "tasks.db")
        _create_test_db(db_path)
        clone = tmp_path / "clone-1"
        clone.mkdir()
        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO tasks (id, status, bead_id, bridge_synced, clone_dir, sdlc_loop_level) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("t1", "completed", "b1", 1, str(clone), "L0"),
        )
        conn.commit(); conn.close()
        deacon = Deacon(db_path=db_path, project_dir=str(tmp_path))
        deacon._prune_stale_clones()
        assert not clone.exists()

    def test_refuse_if_active_tasks_remain(self, tmp_path: Path) -> None:
        db_path = str(tmp_path / "tasks.db")
        _create_test_db(db_path)
        clone = tmp_path / "clone-shared"
        clone.mkdir()
        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO tasks (id, status, bead_id, bridge_synced, clone_dir, sdlc_loop_level) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("t1", "completed", "b1", 1, str(clone), "L0"),
        )
        conn.execute(
            "INSERT INTO tasks (id, status, bead_id, bridge_synced, clone_dir, sdlc_loop_level) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("t2", "claimed", "b2", 0, str(clone), "L1"),
        )
        conn.commit(); conn.close()
        deacon = Deacon(db_path=db_path, project_dir=str(tmp_path))
        deacon._prune_stale_clones()
        assert clone.exists()  # NOT pruned

    def test_24h_age_override(self, tmp_path: Path) -> None:
        db_path = str(tmp_path / "tasks.db")
        _create_test_db(db_path)
        clone = tmp_path / "clone-old"
        clone.mkdir()
        # Set mtime to 25h ago
        old_time = time.time() - 25 * 3600
        os.utime(str(clone), (old_time, old_time))
        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO tasks (id, status, bead_id, bridge_synced, clone_dir, sdlc_loop_level) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("t1", "completed", "b1", 0, str(clone), "L0"),  # NOT synced
        )
        conn.commit(); conn.close()
        deacon = Deacon(db_path=db_path, project_dir=str(tmp_path))
        deacon._prune_stale_clones()
        assert not clone.exists()  # pruned by age

    def test_log_rotation(self, tmp_path: Path) -> None:
        log_file = tmp_path / "colony-sessions.log"
        # Write >10MB
        log_file.write_text("x" * (11 * 1024 * 1024))
        _rotate_log(str(log_file), max_bytes=10 * 1024 * 1024, keep_lines=1000)
        content = log_file.read_text()
        assert len(content) < 10 * 1024 * 1024
```

### Implementation (GREEN)

Add to Deacon class:

```python
def _prune_stale_clones(self) -> None:
    """Prune clone dirs for synced/completed tasks. SC-COL-31: check zero active tasks."""
    try:
        conn = self._get_db()
        candidates = conn.execute(
            """
            SELECT DISTINCT clone_dir FROM tasks
            WHERE bridge_synced = 1
              AND clone_dir IS NOT NULL
              AND sdlc_loop_level IS NOT NULL
            """
        ).fetchall()

        for row in candidates:
            clone_dir = row["clone_dir"]
            if not os.path.isdir(clone_dir):
                continue
            # SC-COL-31: verify zero active tasks share this clone_dir
            active = conn.execute(
                "SELECT COUNT(*) as cnt FROM tasks WHERE clone_dir = ? "
                "AND status NOT IN ('completed', 'cancelled')",
                (clone_dir,),
            ).fetchone()
            if active and active["cnt"] > 0:
                continue
            # Path validation
            real = os.path.realpath(clone_dir)
            if not Path(real).is_relative_to(Path(os.path.realpath(COLONY_BASE))):
                log.warning("clone_prune_path_blocked dir=%s", clone_dir)
                continue
            import shutil
            shutil.rmtree(real, ignore_errors=True)
            log.info("clone_pruned dir=%s reason=bridge_synced", clone_dir)
            self._last_timer_fire = time.monotonic()

        # 24h age override: prune any clone older than 24h
        colony_base = Path(os.path.realpath(COLONY_BASE))
        if colony_base.is_dir():
            now = time.time()
            for entry in colony_base.iterdir():
                if not entry.is_dir():
                    continue
                try:
                    age = now - entry.stat().st_mtime
                except OSError:
                    continue
                if age > 24 * 3600:
                    active = conn.execute(
                        "SELECT COUNT(*) as cnt FROM tasks WHERE clone_dir = ? "
                        "AND status NOT IN ('completed', 'cancelled')",
                        (str(entry),),
                    ).fetchone()
                    if active and active["cnt"] > 0:
                        continue
                    import shutil
                    shutil.rmtree(str(entry), ignore_errors=True)
                    log.info("clone_pruned dir=%s reason=age_24h", entry)
                    self._last_timer_fire = time.monotonic()

    except sqlite3.Error:
        log.exception("clone_prune_db_error")

    # Log rotation
    for log_name in ("colony-sessions.log", "colony-bridge.log"):
        log_path = str(Path(__file__).parent / log_name)
        _rotate_log(log_path)
```

Add module-level helper:

```python
def _rotate_log(path: str, max_bytes: int = 10 * 1024 * 1024, keep_lines: int = 1000) -> None:
    """Truncate log file if it exceeds max_bytes, keeping last keep_lines lines."""
    try:
        if not os.path.isfile(path):
            return
        if os.path.getsize(path) <= max_bytes:
            return
        with open(path) as f:
            lines = f.readlines()
        with open(path, "w") as f:
            f.writelines(lines[-keep_lines:])
        log.info("log_rotated path=%s kept=%d", path, keep_lines)
    except OSError:
        log.exception("log_rotate_error path=%s", path)
```

Call `_prune_stale_clones` in `run_deacon` WATCHING block (line 533), after `check_for_work`:

```python
# After the spawn_conductor block:
await asyncio.to_thread(deacon._prune_stale_clones)
```

```bash
pytest colony/deacon_test.py::TestClonePruning -x
git add colony/deacon.py colony/deacon_test.py && git commit -m "feat(colony): add clone pruning SC-COL-31 (spec 3.3)"
```

---

## Task 4: Cross-Model Wiring (spec 3.4)

**Files:** `colony/conductor-prompt.md` (line 103), `skills/sdlc-orchestrate/colony-mode.md` (line 80)

### Changes

Insert after line 103 of `colony/conductor-prompt.md` (after "After AQS and Harden complete inline..."):

```markdown
### FFT-14: Cross-Model Review (post-AQS)

After AQS completes, evaluate FFT-14. If the fitness function returns FULL or TARGETED:
1. Invoke `sdlc-os:sdlc-crossmodel` with the bead context.
2. Codex workers dispatch via `tmup_dispatch` with `worker_type=codex`.
3. `crossmodel-triage` deduplicates against AQS findings.
4. Net-new findings are HIGH priority corrections — append to the bead and re-enter L2.
```

Add to `skills/sdlc-orchestrate/colony-mode.md` after line 85:

```markdown
- **Cross-model workers** use `worker_type=codex` and are dispatched by the Conductor post-AQS via FFT-14.
```

No tests (documentation only).

```bash
git add colony/conductor-prompt.md skills/sdlc-orchestrate/colony-mode.md
git commit -m "docs(colony): add FFT-14 cross-model wiring (spec 3.4)"
```

---

## Task 5: SC-COL-05 SYNTHESIZE E2E Test (spec 3.5)

**Files:** `colony/deacon_test.py`, `colony/smoke-test.sh` (line 473)

### Test

Add to `colony/deacon_test.py`:

```python
class TestSynthesizeTimeout:
    """SC-COL-05: SYNTHESIZE uses 60-min timeout, not 30-min."""

    def test_synthesize_timeout_is_60min(self, tmp_path: Path) -> None:
        db_path = str(tmp_path / "tasks.db")
        _create_test_db(db_path)
        deacon = Deacon(db_path=db_path, project_dir=str(tmp_path))
        deacon.active_session_type = SessionType.SYNTHESIZE

        # Mock conductor running for 35 min -- should NOT be killed
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        mock_proc.pid = 99999
        deacon.conductor_process = mock_proc
        deacon._conductor_start_time = time.monotonic() - 35 * 60

        # Write lock file with start time 35 min ago
        LOCK_FILE.write_text(f"99999\n{time.time() - 35 * 60}\n")
        try:
            _check_conductor_timeout(deacon)
            mock_proc.terminate.assert_not_called()  # 35 min < 60 min
        finally:
            LOCK_FILE.unlink(missing_ok=True)

    def test_synthesize_timeout_triggers_at_60min(self, tmp_path: Path) -> None:
        db_path = str(tmp_path / "tasks.db")
        _create_test_db(db_path)
        deacon = Deacon(db_path=db_path, project_dir=str(tmp_path))
        deacon.active_session_type = SessionType.SYNTHESIZE

        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        mock_proc.pid = 99999
        mock_proc.communicate.return_value = (b'{}', b'')
        deacon.conductor_process = mock_proc
        deacon._conductor_start_time = time.monotonic() - 61 * 60

        LOCK_FILE.write_text(f"99999\n{time.time() - 61 * 60}\n")
        try:
            _check_conductor_timeout(deacon)
            mock_proc.terminate.assert_called_once()
        finally:
            LOCK_FILE.unlink(missing_ok=True)
```

Add ST-07 to `colony/smoke-test.sh` before the Runner section (line 474):

```bash
# ST-07: check_for_work returns "synthesize" when all tasks terminal+synced
st07_synthesize_trigger() {
  local db_path
  db_path="$(do_setup)"
  echo "ST-07: Synthesize trigger"

  local conn
  conn="$(mktemp)"
  sqlite3 "$db_path" <<SQL
INSERT INTO tasks (id, status, bead_id, bridge_synced, sdlc_loop_level)
VALUES ('t1', 'completed', 'b1', 1, 'L0'),
       ('t2', 'cancelled', 'b2', 1, 'L1');
SQL

  local output
  output="$(python3 -c "
import sys
sys.path.insert(0, '${SCRIPT_DIR}')
from deacon import Deacon
d = Deacon(db_path='${db_path}', project_dir='/tmp')
print(d.check_for_work())
" 2>/dev/null)"

  if [[ "$output" == "synthesize" ]]; then
    pass "ST-07"
  else
    fail "ST-07" "Expected synthesize, got: ${output}"
  fi

  do_cleanup
}
```

Add `st07_synthesize_trigger` call to Runner section (line 489).

```bash
pytest colony/deacon_test.py::TestSynthesizeTimeout -x && bash colony/smoke-test.sh
git add colony/deacon_test.py colony/smoke-test.sh && git commit -m "test(colony): add SYNTHESIZE E2E tests SC-COL-05 (spec 3.5)"
```

---

## Task 6: Completion Metrics + Cost Ceiling (spec 3.6)

**Files:** `colony/deacon.py` (Deacon class, `check_for_work`), `colony/audit-metrics.sh` (line 70), `colony/deacon_test.py`

### Test (RED)

```python
class TestCompletionMetrics:
    def test_aggregate_bead_cost(self, tmp_path: Path) -> None:
        log_path = tmp_path / "colony-sessions.log"
        log_path.write_text(
            json.dumps({"total_cost_usd": 10.0, "bead_ids": ["b1", "b2"]}) + "\n"
            + json.dumps({"total_cost_usd": 6.0, "bead_ids": ["b1"]}) + "\n"
        )
        db_path = str(tmp_path / "tasks.db")
        _create_test_db(db_path)
        deacon = Deacon(db_path=db_path, project_dir=str(tmp_path))
        # b1: 10/2 + 6/1 = 11.0
        cost = deacon._aggregate_bead_cost("b1", str(log_path))
        assert cost == 11.0

    def test_cost_ceiling_blocks_bead(self, tmp_path: Path) -> None:
        log_path = tmp_path / "colony-sessions.log"
        log_path.write_text(
            json.dumps({"total_cost_usd": 55.0, "bead_ids": ["b-expensive"]}) + "\n"
        )
        db_path = str(tmp_path / "tasks.db")
        _create_test_db(db_path)
        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO tasks (id, status, sdlc_loop_level, bead_id) VALUES (?, ?, ?, ?)",
            ("t1", "pending", "L0", "b-expensive"),
        )
        conn.commit(); conn.close()
        deacon = Deacon(db_path=db_path, project_dir=str(tmp_path))
        with patch.object(deacon, "_aggregate_bead_cost", return_value=55.0):
            work = deacon.check_for_work()
        assert "b-expensive" in deacon._blacklisted_beads

    def test_bead_completion_rate(self, tmp_path: Path) -> None:
        log_path = tmp_path / "colony-sessions.log"
        log_path.write_text(
            json.dumps({"session_type": "DISPATCH", "bead_ids": ["b1", "b2", "b3"]}) + "\n"
            + json.dumps({"session_type": "SYNTHESIZE", "bead_ids": ["b1", "b2"]}) + "\n"
        )
        rate = bead_completion_rate(str(log_path))
        assert abs(rate - 2 / 3) < 0.01
```

### Implementation (GREEN)

Add to Deacon class:

```python
def _aggregate_bead_cost(self, bead_id: str, log_path: str | None = None) -> float:
    """Sum cost attributed to bead_id across all sessions. Cost apportioned equally."""
    if log_path is None:
        log_path = str(Path(__file__).parent / "colony-sessions.log")
    total = 0.0
    try:
        with open(log_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    bead_ids = data.get("bead_ids", [])
                    cost = data.get("total_cost_usd", 0.0)
                    if bead_id in bead_ids and len(bead_ids) > 0:
                        total += cost / len(bead_ids)
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        pass
    return total
```

Add module-level function:

```python
BEAD_COST_CEILING_USD = float(os.environ.get("BEAD_COST_CEILING_USD", "50.0"))

def bead_completion_rate(log_path: str | None = None) -> float:
    """Compute beads_merged / beads_dispatched from session log."""
    if log_path is None:
        log_path = str(Path(__file__).parent / "colony-sessions.log")
    dispatched: set[str] = set()
    merged: set[str] = set()
    try:
        with open(log_path) as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    bead_ids = data.get("bead_ids", [])
                    st = data.get("session_type", "")
                    if st == "DISPATCH":
                        dispatched.update(bead_ids)
                    elif st == "SYNTHESIZE":
                        merged.update(bead_ids)
                except (json.JSONDecodeError, AttributeError):
                    continue
    except FileNotFoundError:
        pass
    return len(merged) / len(dispatched) if dispatched else 0.0
```

In `check_for_work()`, after the main actionable-work check returns True, add cost ceiling filter:

```python
# Cost ceiling check -- blacklist beads exceeding $50
if row and row["cnt"] > 0:
    bead_rows = conn.execute(
        "SELECT DISTINCT bead_id FROM tasks WHERE sdlc_loop_level IS NOT NULL "
        "AND bead_id IS NOT NULL AND status = 'pending'"
    ).fetchall()
    for br in bead_rows:
        bid = br["bead_id"]
        if self._aggregate_bead_cost(bid) > BEAD_COST_CEILING_USD:
            self._blacklisted_beads.add(bid)
            log.warning("bead_cost_ceiling bead_id=%s", bid)
```

Append to `colony/audit-metrics.sh` before the "End of Report" line (line 141):

```bash
echo "--- Per-Bead Cost & Completion ---"

if [[ -f "$SESSIONS_LOG" ]]; then
  python3 -c "
import json, sys
from collections import defaultdict

bead_costs = defaultdict(float)
dispatched = set()
merged = set()
wall_clocks = []

for line in open('${SESSIONS_LOG}'):
    line = line.strip()
    if not line: continue
    try:
        data = json.loads(line)
        bead_ids = data.get('bead_ids', [])
        cost = data.get('total_cost_usd', 0)
        st = data.get('session_type', '')
        wc = data.get('wall_clock_s', 0)
        if isinstance(wc, (int, float)) and wc > 0:
            wall_clocks.append(wc)
        if st == 'DISPATCH': dispatched.update(bead_ids)
        elif st == 'SYNTHESIZE': merged.update(bead_ids)
        if bead_ids and isinstance(cost, (int, float)):
            share = cost / len(bead_ids)
            for b in bead_ids:
                bead_costs[b] += share
    except: continue

if bead_costs:
    print('Per-bead costs:')
    for b, c in sorted(bead_costs.items(), key=lambda x: -x[1]):
        print(f'  {b}: \${c:.2f}')

rate = len(merged) / len(dispatched) if dispatched else 0
print(f'Completion rate: {rate:.1%} ({len(merged)}/{len(dispatched)})')

if wall_clocks:
    wall_clocks.sort()
    p50 = wall_clocks[len(wall_clocks)//2]
    p95 = wall_clocks[int(len(wall_clocks)*0.95)]
    print(f'Wall clock p50: {p50:.0f}s  p95: {p95:.0f}s')
" 2>/dev/null || echo "  (parse error)"
fi
echo ""
```

```bash
pytest colony/deacon_test.py::TestCompletionMetrics -x
git add colony/deacon.py colony/deacon_test.py colony/audit-metrics.sh
git commit -m "feat(colony): add per-bead cost ceiling + completion metrics (spec 3.6)"
```

---

## Task 7: Reliability Fixes (spec 3.7, SC-COL-37)

**Files:** `colony/deacon.py` (lines 656-707, 715-790, 359-468), `colony/bridge.ts` (lines 175-182), `colony/deacon_test.py`

### Test (RED)

```python
class TestReliabilityFixes:
    def test_rrt02_watcher_restart_on_empty_readline(self, tmp_path: Path) -> None:
        """RRT-02: watch_db_changes logs WARNING and restarts on empty readline."""
        db_path = str(tmp_path / "tasks.db")
        _create_test_db(db_path)
        deacon = Deacon(db_path=db_path, project_dir=str(tmp_path))
        # Empty readline = watcher died. The function should return (breaking out of loop).
        # Verified by the watcher_task restarting in run_deacon.
        # Unit test: verify the log message is emitted.
        import asyncio
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_proc = MagicMock()
            mock_proc.stdout.readline = asyncio.coroutine(lambda: b"")
            mock_proc.returncode = None
            mock_proc.terminate = MagicMock()
            mock_proc.wait = asyncio.coroutine(lambda: 0)
            mock_exec.return_value = mock_proc
            with self.assertLogs("deacon", level="WARNING") as cm:
                asyncio.run(watch_db_changes(deacon))
            assert any("watcher_died" in m for m in cm.output)

    def test_rrt03_recovery_handles_unbound_local(self, tmp_path: Path) -> None:
        """RRT-03: recover_stale_claims catches UnboundLocalError."""
        db_path = str(tmp_path / "tasks.db")
        _create_test_db(db_path)
        deacon = Deacon(db_path=db_path, project_dir=str(tmp_path))
        with patch.object(deacon, "_get_db", side_effect=sqlite3.OperationalError("locked")):
            recovered = deacon.recover_stale_claims()
        assert recovered == 0
        assert deacon.state == DeaconState.WATCHING

    def test_rrt05_max_bridge_deferral(self, tmp_path: Path) -> None:
        """RRT-05: Force-kill after MAX_BRIDGE_DEFERRAL_COUNT deferrals."""
        db_path = str(tmp_path / "tasks.db")
        _create_test_db(db_path)
        deacon = Deacon(db_path=db_path, project_dir=str(tmp_path))
        deacon.active_session_type = SessionType.DISPATCH
        deacon._bridge_deferral_count = MAX_BRIDGE_DEFERRAL_COUNT

        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        mock_proc.pid = 99999
        mock_proc.communicate.return_value = (b'{}', b'')
        deacon.conductor_process = mock_proc

        LOCK_FILE.write_text(f"99999\n{time.time() - 35 * 60}\n")
        BRIDGE_LOCK_FILE.write_text(f"99999\n{time.time()}\n")
        try:
            _check_conductor_timeout(deacon)
            mock_proc.terminate.assert_called_once()  # forced despite bridge lock
        finally:
            LOCK_FILE.unlink(missing_ok=True)
            BRIDGE_LOCK_FILE.unlink(missing_ok=True)

    def test_rrt05_synthesize_query_scope(self, tmp_path: Path) -> None:
        """RRT-05: Synthesize total-count query matches actionable-work scope."""
        db_path = str(tmp_path / "tasks.db")
        _create_test_db(db_path)
        conn = sqlite3.connect(db_path)
        # Non-colony task (no sdlc_loop_level) should not affect synthesize check
        conn.execute(
            "INSERT INTO tasks (id, status, bead_id, bridge_synced) VALUES (?, ?, ?, ?)",
            ("t-non-colony", "pending", "b-nc", 0),
        )
        conn.execute(
            "INSERT INTO tasks (id, status, bead_id, bridge_synced, sdlc_loop_level) "
            "VALUES (?, ?, ?, ?, ?)",
            ("t1", "completed", "b1", 1, "L0"),
        )
        conn.commit(); conn.close()
        deacon = Deacon(db_path=db_path, project_dir=str(tmp_path))
        result = deacon.check_for_work()
        assert result == "synthesize"  # non-colony task excluded
```

### Implementation (GREEN)

**RRT-02** -- `watch_db_changes` (line 761): After `if not line: break`, add warning:

```python
if not line:
    log.warning("watcher_died reason=empty_readline action=restart")
    break
```

In `run_deacon` (line 524), wrap watcher_task in restart loop:

```python
async def _managed_watcher(deacon: Deacon) -> None:
    """Auto-restart watcher on silent death (RRT-02)."""
    while True:
        await watch_db_changes(deacon)
        log.warning("watcher_restarting after_death")
        await asyncio.sleep(1)

watcher_task = asyncio.create_task(_managed_watcher(deacon))
```

**RRT-03** -- `recover_stale_claims` (lines 459-462): Replace except block:

```python
except (sqlite3.Error, UnboundLocalError):
    try:
        conn = self._get_db()
        conn.rollback()
    except Exception:
        pass
    log.exception("recover_stale_claims error")
```

And ensure the method always transitions to WATCHING even on exception (move the final transition outside the try/except, or add it in the except).

**RRT-04** -- `bridge.ts` `markBridgeSynced` (line 176): Add timeout + try/catch:

```typescript
export function markBridgeSynced(dbPath: string, taskId: string): { success: boolean; error?: string } {
  try {
    const db = new Database(dbPath, { timeout: 8000 });
    try {
      db.prepare('UPDATE tasks SET bridge_synced = 1 WHERE id = ?').run(taskId);
      return { success: true };
    } finally {
      db.close();
    }
  } catch (err) {
    return { success: false, error: (err as Error).message };
  }
}
```

**RRT-05** -- `_check_conductor_timeout` (line 680): Add max deferral + git lock check:

```python
MAX_BRIDGE_DEFERRAL_COUNT = 10

# In the bridge lock deferral block (line 681):
if BRIDGE_LOCK_FILE.exists() and not _is_bridge_lock_stale():
    deacon._bridge_deferral_count += 1
    if deacon._bridge_deferral_start == 0.0:
        deacon._bridge_deferral_start = time.monotonic()
    total_wait = time.monotonic() - deacon._bridge_deferral_start
    log.warning(
        "bridge_lock_deferral deferral_count=%d total_wait_s=%.1f",
        deacon._bridge_deferral_count, total_wait,
    )
    if deacon._bridge_deferral_count < MAX_BRIDGE_DEFERRAL_COUNT:
        return
    log.warning("bridge_lock_force_kill deferrals=%d", deacon._bridge_deferral_count)

# Before proc.terminate(), check .git/index.lock:
git_lock = Path(deacon.project_dir) / ".git" / "index.lock"
if git_lock.exists():
    for _ in range(6):  # wait up to 30s
        time.sleep(5)
        if not git_lock.exists():
            break
```

**RRT-05 synthesize scope** -- `check_for_work` total-count query (line 252): Add filter:

```python
total_row = conn.execute(
    """
    SELECT COUNT(*) as total FROM tasks
    WHERE bead_id IS NOT NULL
      AND sdlc_loop_level IS NOT NULL
    """
).fetchone()
```

```bash
pytest colony/deacon_test.py::TestReliabilityFixes -x && npx vitest run colony/
git add colony/deacon.py colony/deacon_test.py colony/bridge.ts
git commit -m "fix(colony): reliability fixes RRT-02/03/04/05 SC-COL-37 (spec 3.7)"
```

---

## Final Gate

```bash
pytest colony/deacon_test.py -x > /tmp/phase2-pytest.log 2>&1 && echo PASS || echo FAIL
npx vitest run colony/ > /tmp/phase2-vitest.log 2>&1 && echo PASS || echo FAIL
bash colony/smoke-test.sh > /tmp/phase2-smoke.log 2>&1 && echo PASS || echo FAIL
# Update PROGRESS.md Phase 2 section
git add colony/PROGRESS.md && git commit -m "docs(colony): mark Phase 2 complete"
```
