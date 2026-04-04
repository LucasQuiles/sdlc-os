"""
Deacon Service -- persistent daemon that watches tmup DB and spawns Conductor sessions.

State machine: WATCHING -> CONDUCTING -> RECOVERING -> WATCHING
Runtime: Python 3.12, asyncio
Spec: docs/specs/2026-04-03-colony-runtime-design.md sections 3.1-3.5

Safety constraints:
  SC-COL-01: Self-watchdog at 90s -- SIGTERM if timer hasn't fired
  SC-COL-05: Wall-clock timeout on Conductor (30min/60min)
  SC-COL-06: Check bridge lock file before sending SIGTERM to conductor
"""

from __future__ import annotations

import asyncio
import calendar
import enum
import json
import logging
import os
import signal
import sqlite3
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

log = logging.getLogger("deacon")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LOCK_FILE = Path("/tmp/sdlc-colony-conductor.lock")
BRIDGE_LOCK_FILE = Path("/tmp/sdlc-colony-bridge.lock")
COLONY_BASE = "/tmp/sdlc-colony/"
STALE_LOCK_TIMEOUT_S = 180  # 3 minutes
BRIDGE_STALE_TIMEOUT_S = 60  # 1 minute
HEARTBEAT_STALE_THRESHOLD_S = 300  # 5 minutes default

# SC-COL-20: Per-domain heartbeat thresholds (seconds)
HEARTBEAT_THRESHOLDS: dict[str, int] = {
    "clear": 300,
    "complicated": 900,
    "complex": 1800,
    "chaotic": 300,
    "confusion": 900,
}
CONDUCTOR_TIMEOUT_DISPATCH_S = 30 * 60  # 30 minutes
CONDUCTOR_TIMEOUT_SYNTHESIZE_S = 60 * 60  # 60 minutes
DEBOUNCE_S = 2.0
TIMER_INTERVAL_S = 60
WATCHDOG_SELF_TIMEOUT_S = 90  # SC-COL-01
WATCHDOG_MAX_STATE_DURATION_S = int(
    os.environ.get("WATCHDOG_MAX_STATE_DURATION_S", str(CONDUCTOR_TIMEOUT_SYNTHESIZE_S + 300))
)
CONDUCTOR_PROMPT_FILE = Path(__file__).parent / "conductor-prompt.md"
TMUP_PLUGIN_DIR = Path("/home/q/.claude/plugins/tmup")
SDLC_PLUGIN_DIR = Path("/home/q/.claude/plugins/sdlc-os")


# ---------------------------------------------------------------------------
# State Machine
# ---------------------------------------------------------------------------


class DeaconState(enum.Enum):
    WATCHING = "WATCHING"
    CONDUCTING = "CONDUCTING"
    RECOVERING = "RECOVERING"


class SessionType(enum.Enum):
    DISPATCH = "DISPATCH"
    EVALUATE = "EVALUATE"
    SYNTHESIZE = "SYNTHESIZE"
    RECOVER = "RECOVER"


# ---------------------------------------------------------------------------
# Lock staleness helper (BLOCKING-1 fix: single implementation)
# ---------------------------------------------------------------------------


def _is_lock_stale(lock_path: Path, timeout_s: float) -> bool:
    """Check if a PID+timestamp lock file is stale.

    A lock is stale if:
    - The file does not exist
    - The file content is malformed (< 2 lines, unparseable)
    - The PID recorded in the file is dead
    - The timestamp is older than timeout_s seconds

    Returns True if stale or unreadable, False if valid.
    """
    if not lock_path.exists():
        return True
    try:
        content = lock_path.read_text().strip()
        parts = content.split("\n")
        if len(parts) < 2:
            return True

        pid = int(parts[0])
        timestamp = float(parts[1])

        # Check PID liveness
        try:
            os.kill(pid, 0)
        except (OSError, ProcessLookupError):
            log.info("Stale lock: PID %d is dead (%s)", pid, lock_path)
            return True

        # Check timestamp staleness
        if time.time() - timestamp > timeout_s:
            log.info(
                "Stale lock: timestamp %.0f older than %ds (%s)",
                timestamp,
                int(timeout_s),
                lock_path,
            )
            return True

        return False
    except (ValueError, OSError):
        log.exception("Error reading lock file %s", lock_path)
        return True


# ---------------------------------------------------------------------------
# Deacon Core
# ---------------------------------------------------------------------------


@dataclass
class Deacon:
    """Core Deacon state machine.

    Watches tmup DB for colony tasks, spawns Conductor sessions,
    and recovers stale claims.
    """

    db_path: str
    project_dir: str
    conductor_budget: str = "10.00"
    expected_branch: str = "main"
    state: DeaconState = DeaconState.WATCHING
    conductor_process: subprocess.Popen[bytes] | None = None
    active_session_type: SessionType = SessionType.DISPATCH
    _last_timer_fire: float = field(default_factory=time.monotonic)
    _state_entered_at: float = field(default_factory=time.monotonic)
    _spawn_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    _conductor_start_time: float = 0.0
    _bridge_deferral_count: int = 0
    _bridge_deferral_start: float = 0.0
    _db: sqlite3.Connection | None = None
    _bead_failure_counts: dict[str, list[float]] = field(default_factory=dict)
    _blacklisted_beads: set[str] = field(default_factory=set)

    # -- State transition helper -----------------------------------------------

    def _transition_to(self, new_state: DeaconState, trigger: str) -> None:
        """Log and execute a state machine transition."""
        old_state = self.state
        elapsed = time.monotonic() - self._state_entered_at
        self._state_entered_at = time.monotonic()
        log.info(
            "state_transition old=%s new=%s elapsed_s=%.1f trigger=%s",
            old_state.value,
            new_state.value,
            elapsed,
            trigger,
        )
        self.state = new_state

    # -- Lock helpers --------------------------------------------------------

    def _release_lock(self) -> None:
        """Remove the conductor lock file."""
        LOCK_FILE.unlink(missing_ok=True)

    # -- DB helpers ----------------------------------------------------------

    def _get_db(self) -> sqlite3.Connection:
        """Return a persistent DB connection, lazily opened with WAL mode."""
        if self._db is None:
            conn = sqlite3.connect(self.db_path, timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=8000")
            conn.row_factory = sqlite3.Row
            self._db = conn
        return self._db

    def close(self) -> None:
        """Close the persistent DB connection."""
        if self._db is not None:
            try:
                self._db.close()
            except sqlite3.Error:
                pass
            self._db = None

    # -- Escalation helpers (SC-COL-36) ---------------------------------------

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
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._send_escalation_alert(bead_id, error))
        except RuntimeError:
            # No running event loop (called from sync context / tests)
            pass

    async def _send_escalation_alert(self, bead_id: str, error: str) -> None:
        """SC-COL-36: Non-blocking alert. Dead-letter on failure."""
        dl_path = os.environ.get(
            "ESCALATION_DEADLETTER",
            os.path.expanduser("~/agents/lab/escalation-deadletter.jsonl"),
        )
        record = {"bead_id": bead_id, "error": error, "timestamp": time.time()}
        try:
            proc = await asyncio.create_subprocess_exec(
                "curl", "-sf", "-X", "POST",
                "-H", "Content-Type: application/json",
                "-d", json.dumps({"text": f"Colony escalation: bead {bead_id} failed 3x: {error}"}),
                os.environ.get("ESCALATION_WEBHOOK_URL", "http://localhost:9999/noop"),
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await asyncio.wait_for(proc.wait(), timeout=10)
            if proc.returncode != 0:
                raise RuntimeError(f"curl exit {proc.returncode}")
        except Exception:
            log.warning("escalation_deadletter bead_id=%s", bead_id)
            with open(dl_path, "a") as f:
                f.write(json.dumps(record) + "\n")

    def _clear_blacklist(self) -> None:
        """SIGUSR1 handler target: clear blacklist and failure counts."""
        self._blacklisted_beads.clear()
        self._bead_failure_counts.clear()
        log.info("blacklist_cleared")

    # -- can_spawn_conductor -------------------------------------------------

    def can_spawn_conductor(self) -> bool:
        """Check if we can spawn a new Conductor.

        Returns False if lock file exists with a live PID and fresh timestamp.
        Returns True if no lock, stale lock (dead PID or old timestamp), etc.

        Uses atomic file creation (open with 'x' mode) to prevent TOCTOU races.
        """
        try:
            # Attempt atomic lock acquisition: create-or-fail
            fd = os.open(str(LOCK_FILE), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            os.close(fd)
            # We created the file -- remove it (spawn_conductor will recreate)
            LOCK_FILE.unlink(missing_ok=True)
            return True
        except FileExistsError:
            pass

        # Lock file exists -- check staleness via shared helper
        return _is_lock_stale(LOCK_FILE, STALE_LOCK_TIMEOUT_S)

    # -- check_for_work ------------------------------------------------------

    def check_for_work(self) -> str | bool:
        """Query tmup DB for actionable colony tasks.

        Returns:
        - "synthesize" if all colony beads are at terminal status and bridge-synced
        - True if there are actionable tasks (pending, unsynced completed, needs_review)
        - False if no work to do
        """
        try:
            conn = self._get_db()
            row = conn.execute(
                """
                SELECT COUNT(*) as cnt FROM tasks
                WHERE sdlc_loop_level IS NOT NULL
                  AND (
                    status = 'pending'
                    OR (status = 'completed' AND bridge_synced = 0)
                    OR status = 'needs_review'
                  )
                """
            ).fetchone()
            if row and row["cnt"] > 0:
                # SC-COL-36: If blacklisted beads exist, re-check excluding them
                if self._blacklisted_beads:
                    placeholders = ",".join("?" * len(self._blacklisted_beads))
                    row2 = conn.execute(
                        f"""
                        SELECT COUNT(*) as cnt FROM tasks
                        WHERE sdlc_loop_level IS NOT NULL
                          AND (bead_id IS NULL OR bead_id NOT IN ({placeholders}))
                          AND (
                            status = 'pending'
                            OR (status = 'completed' AND bridge_synced = 0)
                            OR status = 'needs_review'
                          )
                        """,
                        tuple(self._blacklisted_beads),
                    ).fetchone()
                    if not (row2 and row2["cnt"] > 0):
                        return False
                return True

            # Check if all colony beads are terminal (completed/cancelled)
            # and bridge_synced -- triggers SYNTHESIZE session
            total_row = conn.execute(
                """
                SELECT COUNT(*) as total FROM tasks
                WHERE bead_id IS NOT NULL
                """
            ).fetchone()
            total = total_row["total"] if total_row else 0

            if total > 0:
                terminal_row = conn.execute(
                    """
                    SELECT COUNT(*) as terminal FROM tasks
                    WHERE bead_id IS NOT NULL
                      AND status IN ('completed', 'cancelled')
                      AND bridge_synced = 1
                    """
                ).fetchone()
                terminal = terminal_row["terminal"] if terminal_row else 0
                if terminal == total:
                    return "synthesize"

            return False
        except sqlite3.Error:
            log.exception("check_for_work DB error")
            return False

    # -- spawn_conductor -----------------------------------------------------

    def spawn_conductor(self, session_type: str = "DISPATCH") -> subprocess.Popen[bytes]:
        """Spawn a Conductor Claude Code session.

        Launches via Popen first, then writes lock file with Conductor PID.
        If Popen fails, no lock file is written (CRITICAL 4 fix).
        Returns the Popen handle.
        """
        # Resolve to enum
        st = SessionType(session_type)

        # Read conductor prompt
        prompt_text = CONDUCTOR_PROMPT_FILE.read_text() if CONDUCTOR_PROMPT_FILE.exists() else ""

        # Build command
        cmd = self._build_conductor_command(session_type, prompt_text)

        log.info("Spawning conductor: %s", " ".join(cmd))

        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=self.project_dir,
        )

        # Write lock file AFTER Popen succeeds, with Conductor PID (not Deacon PID)
        LOCK_FILE.write_text(f"{proc.pid}\n{time.time()}\n")

        self.conductor_process = proc
        self.active_session_type = st
        self._conductor_start_time = time.monotonic()
        self._transition_to(DeaconState.CONDUCTING, f"spawn_conductor:{st.value}")
        return proc

    def _build_conductor_command(self, session_type: str, prompt_text: str) -> list[str]:
        """Build the claude -p command for the Conductor."""
        cmd = [
            "claude",
            "-p",
            "--model",
            "opus",
            "--output-format",
            "json",
            "--permission-mode",
            "bypassPermissions",
            "--plugin-dir",
            str(TMUP_PLUGIN_DIR),
            "--plugin-dir",
            str(SDLC_PLUGIN_DIR),
            "--max-budget-usd",
            self.conductor_budget,
            "--add-dir",
            self.project_dir,
        ]

        if prompt_text:
            cmd.extend(["--system-prompt", prompt_text])

        return cmd

    # -- recover_stale_claims ------------------------------------------------

    @staticmethod
    def _get_heartbeat_threshold(description: str | None) -> tuple[int, str]:
        """Extract cynefin_domain from task description JSON and return threshold + domain.

        SC-COL-20: Per-domain heartbeat thresholds.
        Returns (threshold_seconds, domain_string).
        """
        if not description:
            return HEARTBEAT_STALE_THRESHOLD_S, "unknown"
        try:
            desc_data = json.loads(description)
            domain = desc_data.get("cynefin_domain", "").lower().strip()
            threshold = HEARTBEAT_THRESHOLDS.get(domain, HEARTBEAT_STALE_THRESHOLD_S)
            return threshold, domain or "unknown"
        except (json.JSONDecodeError, AttributeError):
            return HEARTBEAT_STALE_THRESHOLD_S, "unknown"

    def recover_stale_claims(self) -> int:
        """Find claimed tasks with stale heartbeats and reset them.

        SC-COL-20: Uses per-domain heartbeat thresholds based on cynefin_domain.
        Returns count of recovered tasks.
        """
        self._transition_to(DeaconState.RECOVERING, "recover_stale_claims")
        recovered = 0

        try:
            conn = self._get_db()
            # Fetch all claimed colony tasks with their agent heartbeats
            candidates = conn.execute(
                """
                SELECT t.id, t.retry_count, t.max_retries, t.clone_dir,
                       t.description, a.last_heartbeat_at
                FROM tasks t
                JOIN agents a ON t.owner = a.id
                WHERE t.status = 'claimed'
                  AND t.sdlc_loop_level IS NOT NULL
                """
            ).fetchall()

            now = time.time()
            stale = []
            for candidate in candidates:
                heartbeat_iso = candidate["last_heartbeat_at"]
                if not heartbeat_iso:
                    stale.append(candidate)
                    continue
                try:
                    heartbeat_epoch = calendar.timegm(
                        time.strptime(heartbeat_iso, "%Y-%m-%dT%H:%M:%SZ")
                    )
                except (ValueError, OverflowError):
                    stale.append(candidate)
                    continue

                threshold_s, domain = self._get_heartbeat_threshold(
                    candidate["description"]
                )
                actual_elapsed_s = now - heartbeat_epoch
                log.debug(
                    "heartbeat_check domain=%s threshold_s=%d actual_elapsed_s=%.1f task=%s",
                    domain,
                    threshold_s,
                    actual_elapsed_s,
                    candidate["id"],
                )
                if actual_elapsed_s > threshold_s:
                    log.info(
                        "heartbeat_stale domain=%s threshold_s=%d actual_elapsed_s=%.1f task=%s",
                        domain,
                        threshold_s,
                        actual_elapsed_s,
                        candidate["id"],
                    )
                    stale.append(candidate)

            for task in stale:
                task_id = task["id"]
                retry_count = task["retry_count"] or 0
                max_retries = task["max_retries"] or 3
                clone_dir = task["clone_dir"]

                # SC-COL-21: preserve output before reset
                # Validate clone_dir against COLONY_BASE to prevent path traversal
                if clone_dir:
                    real_clone = os.path.realpath(clone_dir)
                    if not Path(real_clone).is_relative_to(Path(os.path.realpath(COLONY_BASE))):
                        log.warning(
                            "Path traversal blocked: %s",
                            clone_dir,
                        )
                    else:
                        output_path = Path(real_clone) / "bead-output.md"
                        if output_path.exists():
                            recover_dir = Path(COLONY_BASE) / "recovered-outputs" / task_id
                            recover_dir.mkdir(parents=True, exist_ok=True)
                            (recover_dir / "bead-output.md").write_text(
                                output_path.read_text()
                            )

                if retry_count < max_retries:
                    conn.execute(
                        """
                        UPDATE tasks SET status = 'pending',
                          owner = NULL, claimed_at = NULL,
                          retry_count = retry_count + 1
                        WHERE id = ?
                        """,
                        (task_id,),
                    )
                else:
                    conn.execute(
                        "UPDATE tasks SET status = 'needs_review' WHERE id = ?",
                        (task_id,),
                    )
                recovered += 1

            conn.commit()
        except sqlite3.Error:
            conn.rollback()
            log.exception("recover_stale_claims DB error")

        # Clean up stale lock file via shared helper
        if _is_lock_stale(LOCK_FILE, STALE_LOCK_TIMEOUT_S):
            LOCK_FILE.unlink(missing_ok=True)

        self._transition_to(DeaconState.WATCHING, "recovery_complete")
        return recovered


# ---------------------------------------------------------------------------
# Async Event Loop (T5.2)
# ---------------------------------------------------------------------------


def _sd_notify(msg: str) -> None:
    """Send systemd notification, silently no-op if unavailable."""
    try:
        import systemd.daemon  # type: ignore[import-untyped]

        systemd.daemon.notify(msg)
    except ImportError:
        pass


async def _self_watchdog_task_once(deacon: Deacon) -> None:
    """Single watchdog iteration (for testing)."""
    # SC-COL-35: time-in-state check
    max_dur = int(
        os.environ.get(
            "WATCHDOG_MAX_STATE_DURATION_S", str(CONDUCTOR_TIMEOUT_SYNTHESIZE_S + 300)
        )
    )
    state_elapsed = time.monotonic() - deacon._state_entered_at
    if state_elapsed > max_dur:
        log.warning(
            "watchdog_state_timeout state=%s elapsed_s=%.1f max_s=%.1f",
            deacon.state.value,
            state_elapsed,
            float(max_dur),
        )
        deacon._transition_to(DeaconState.RECOVERING, "watchdog_state_timeout")


async def _self_watchdog_task(deacon: Deacon) -> None:
    """SC-COL-01 + SC-COL-35: Independent self-watchdog coroutine.

    Runs as a separate asyncio task so it can fire even if the main loop blocks.
    Checks that deacon._last_timer_fire has been updated within WATCHDOG_SELF_TIMEOUT_S.
    Also checks time-in-state to force RECOVERING if stuck too long.
    """
    while True:
        await asyncio.sleep(TIMER_INTERVAL_S)
        # SC-COL-01: timer-fire liveness
        elapsed = time.monotonic() - deacon._last_timer_fire
        if elapsed > 60 and elapsed <= WATCHDOG_SELF_TIMEOUT_S:
            log.warning("watchdog_near_miss elapsed_s=%.1f threshold_s=90", elapsed)
        if elapsed > WATCHDOG_SELF_TIMEOUT_S:
            log.error(
                "Self-watchdog triggered: timer hasn't fired in %.0fs (>%ds), sending SIGTERM",
                elapsed,
                WATCHDOG_SELF_TIMEOUT_S,
            )
            os.kill(os.getpid(), signal.SIGTERM)

        # SC-COL-35: time-in-state check
        await _self_watchdog_task_once(deacon)


async def run_deacon(deacon: Deacon) -> None:
    """Main Deacon async event loop.

    States:
    - WATCHING: check for work, spawn conductor if needed
    - CONDUCTING: poll conductor process, parse JSON cost on exit
    - RECOVERING: recover stale claims, then return to WATCHING
    """
    _sd_notify("READY=1")
    log.info(
        "Deacon started: db=%s project=%s budget=%s",
        deacon.db_path,
        deacon.project_dir,
        deacon.conductor_budget,
    )

    # Launch inotifywait watcher and self-watchdog as concurrent tasks
    watcher_task = asyncio.create_task(watch_db_changes(deacon))
    watchdog_task = asyncio.create_task(_self_watchdog_task(deacon))

    try:
        while True:
            _sd_notify("WATCHDOG=1")

            if deacon.state == DeaconState.WATCHING:
                async with deacon._spawn_lock:
                    work = deacon.check_for_work()
                    if work and deacon.can_spawn_conductor():
                        session_type = SessionType.SYNTHESIZE.value if work == "synthesize" else SessionType.DISPATCH.value
                        deacon.spawn_conductor(session_type)

            elif deacon.state == DeaconState.CONDUCTING:
                proc = deacon.conductor_process
                if proc is not None:
                    ret = proc.poll()
                    if ret is not None:
                        # Conductor exited
                        await asyncio.to_thread(_parse_conductor_output, proc, deacon)
                        deacon.conductor_process = None
                        LOCK_FILE.unlink(missing_ok=True)
                        log.info("Conductor exited with code %d, debouncing", ret)
                        # SC-COL-36: Record bead failures on non-zero exit
                        if ret != 0:
                            try:
                                conn = deacon._get_db()
                                bead_rows = conn.execute(
                                    "SELECT DISTINCT bead_id FROM tasks "
                                    "WHERE bead_id IS NOT NULL AND sdlc_loop_level IS NOT NULL"
                                ).fetchall()
                                bead_ids = [r["bead_id"] for r in bead_rows]
                                if bead_ids:
                                    deacon._record_bead_failure(bead_ids, f"conductor_exit:{ret}")
                            except sqlite3.Error:
                                log.exception("Failed to record bead failure")
                        await asyncio.sleep(DEBOUNCE_S)
                        deacon._transition_to(DeaconState.WATCHING, f"conductor_exit:{ret}")

                    else:
                        # SC-COL-05: Check wall-clock timeout
                        _check_conductor_timeout(deacon)

            elif deacon.state == DeaconState.RECOVERING:
                recovered = deacon.recover_stale_claims()
                log.info("Recovery complete: %d tasks reset", recovered)
                # state is set to WATCHING by recover_stale_claims

            # Update timestamp AFTER work, so watchdog task measures real elapsed time
            deacon._last_timer_fire = time.monotonic()

            await asyncio.sleep(TIMER_INTERVAL_S)
    finally:
        watcher_task.cancel()
        watchdog_task.cancel()
        for task in (watcher_task, watchdog_task):
            try:
                await task
            except asyncio.CancelledError:
                pass
        deacon.close()


def _parse_conductor_output(
    proc: subprocess.Popen[bytes],
    deacon: Deacon | None = None,
    stdout_override: bytes | None = None,
) -> None:
    """Parse JSON output from Conductor for cost tracking.

    Args:
        proc: The conductor subprocess.
        deacon: Optional Deacon instance for session metadata.
        stdout_override: Pre-captured stdout (from timeout drain). If provided,
            communicate() is not called.
    """
    try:
        if stdout_override is not None:
            stdout = stdout_override
        else:
            stdout, _stderr = proc.communicate(timeout=10)

        # Parse output or use sentinel values
        session_id = "unknown"
        cost = 0.0
        if stdout:
            try:
                data: dict[str, Any] = json.loads(stdout)
                session_id = data.get("session_id", "unknown")
                cost = data.get("total_cost_usd", 0.0)
            except json.JSONDecodeError:
                log.warning("Failed to parse conductor JSON output, using sentinel values")

        log.info("Conductor session %s cost $%.4f", session_id, cost)

        # Compute wall clock time
        wall_clock_s = 0.0
        if deacon is not None and deacon._conductor_start_time > 0:
            wall_clock_s = time.monotonic() - deacon._conductor_start_time

        # Collect bead_ids from DB
        bead_ids: list[str] = []
        if deacon is not None:
            try:
                conn = deacon._get_db()
                rows = conn.execute(
                    "SELECT bead_id FROM tasks WHERE bead_id IS NOT NULL"
                ).fetchall()
                bead_ids = [r["bead_id"] for r in rows]
            except sqlite3.Error:
                log.exception("Failed to fetch bead_ids for session log")

        # Build log record
        record: dict[str, Any] = {
            "session_id": session_id,
            "total_cost_usd": cost,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "session_type": deacon.active_session_type.value if deacon else "unknown",
            "exit_code": proc.returncode,
            "wall_clock_s": round(wall_clock_s, 1),
            "bead_ids": bead_ids,
        }

        # Append to session log
        log_path = Path(__file__).parent / "colony-sessions.log"
        with open(log_path, "a") as f:
            f.write(json.dumps(record) + "\n")
    except subprocess.TimeoutExpired:
        log.warning("Timeout reading conductor output, killing process")
        proc.kill()
        proc.wait()
    except OSError:
        log.exception("Failed to write conductor session log")


def _is_bridge_lock_stale() -> bool:
    """Check if the bridge lock file is stale (dead PID or old timestamp).

    Returns True if the bridge lock is stale or unreadable, False if it is valid.
    Delegates to the shared _is_lock_stale helper.
    """
    return _is_lock_stale(BRIDGE_LOCK_FILE, BRIDGE_STALE_TIMEOUT_S)


def _check_conductor_timeout(deacon: Deacon) -> None:
    """SC-COL-05: Kill conductor if it exceeds wall-clock timeout."""
    proc = deacon.conductor_process
    if proc is None or proc.poll() is not None:
        return

    # Use create_time approximation from lock file
    if LOCK_FILE.exists():
        try:
            parts = LOCK_FILE.read_text().strip().split("\n")
            if len(parts) >= 2:
                start_time = float(parts[1])
                elapsed = time.time() - start_time
                timeout = CONDUCTOR_TIMEOUT_SYNTHESIZE_S if deacon.active_session_type == SessionType.SYNTHESIZE else CONDUCTOR_TIMEOUT_DISPATCH_S

                if elapsed > timeout:
                    log.warning(
                        "conductor_timeout elapsed_s=%.1f session_type=%s timeout_threshold_s=%d",
                        elapsed,
                        deacon.active_session_type,
                        timeout,
                    )
                    # SC-COL-06: Check bridge lock before SIGTERM
                    # Use staleness check so dead bridge processes don't block forever
                    if BRIDGE_LOCK_FILE.exists() and not _is_bridge_lock_stale():
                        deacon._bridge_deferral_count += 1
                        if deacon._bridge_deferral_start == 0.0:
                            deacon._bridge_deferral_start = time.monotonic()
                        total_wait = time.monotonic() - deacon._bridge_deferral_start
                        log.warning(
                            "bridge_lock_deferral deferral_count=%d total_wait_s=%.1f",
                            deacon._bridge_deferral_count,
                            total_wait,
                        )
                        return

                    # Reset deferral counters on actual termination
                    deacon._bridge_deferral_count = 0
                    deacon._bridge_deferral_start = 0.0
                    proc.terminate()  # SIGTERM
                    try:
                        stdout, _stderr = proc.communicate(timeout=5)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        stdout, _stderr = proc.communicate()
                    # Pass stdout directly to parser instead of side-channel
                    _parse_conductor_output(proc, deacon, stdout_override=stdout)
                    deacon._release_lock()
                    deacon.conductor_process = None
                    deacon._transition_to(DeaconState.RECOVERING, "conductor_timeout")
        except (ValueError, OSError):
            pass


# ---------------------------------------------------------------------------
# inotifywait Integration (T5.3)
# ---------------------------------------------------------------------------


async def watch_db_changes(deacon: Deacon) -> None:
    """Watch tmup DB for changes using inotifywait.

    Spawns inotifywait as an asyncio subprocess monitoring for modify/create
    events on .db and .db-wal files. On event, drains buffer, checks for work,
    and spawns conductor if needed.

    Falls back to timer-only mode if inotifywait is not available.
    """
    db_dir = str(Path(deacon.db_path).parent)

    try:
        proc = await asyncio.create_subprocess_exec(
            "inotifywait",
            "-m",
            "-e",
            "modify,create",
            "--include",
            r"\.(db|db-wal)$",
            db_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
    except FileNotFoundError:
        log.warning("inotifywait not found, falling back to timer-only mode")
        return

    assert proc.stdout is not None

    try:
        while True:
            try:
                line = await asyncio.wait_for(
                    proc.stdout.readline(), timeout=TIMER_INTERVAL_S
                )
            except asyncio.TimeoutError:
                # Safety net: check anyway on timeout
                log.info("timer_fallback reason=no_inotify_events")
                if deacon.state == DeaconState.WATCHING:
                    async with deacon._spawn_lock:
                        work = deacon.check_for_work()
                        if work and deacon.can_spawn_conductor():
                            session_type = SessionType.SYNTHESIZE.value if work == "synthesize" else SessionType.DISPATCH.value
                            deacon.spawn_conductor(session_type)
                continue

            if not line:
                break

            # Drain buffer -- read any additional lines without blocking
            drain_count = 1  # count the initial line
            while True:
                try:
                    extra = await asyncio.wait_for(
                        proc.stdout.readline(), timeout=0.1
                    )
                    if not extra:
                        break
                    drain_count += 1
                except asyncio.TimeoutError:
                    break
            log.debug("inotify_drain count=%d", drain_count)

            # Check for work after draining
            if deacon.state == DeaconState.WATCHING:
                async with deacon._spawn_lock:
                    work = deacon.check_for_work()
                    if work and deacon.can_spawn_conductor():
                        session_type = SessionType.SYNTHESIZE.value if work == "synthesize" else SessionType.DISPATCH.value
                        deacon.spawn_conductor(session_type)
    except asyncio.CancelledError:
        proc.terminate()
        await proc.wait()
        raise
    finally:
        if proc.returncode is None:
            proc.terminate()
            await proc.wait()


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------


def main() -> None:
    """Entry point for the Deacon daemon.

    Reads configuration from environment variables:
    - TMUP_DB_PATH: path to tmup SQLite database
    - SDLC_PROJECT_DIR: project directory for Conductor sessions
    - CONDUCTOR_BUDGET_USD: per-session budget ceiling
    - EXPECTED_BRANCH: expected git branch name
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    db_path = os.environ.get("TMUP_DB_PATH", "")
    project_dir = os.environ.get("SDLC_PROJECT_DIR", "")
    conductor_budget = os.environ.get("CONDUCTOR_BUDGET_USD", "10.00")
    expected_branch = os.environ.get("EXPECTED_BRANCH", "main")

    if not db_path:
        log.error("TMUP_DB_PATH not set")
        raise SystemExit(1)
    if not project_dir:
        log.error("SDLC_PROJECT_DIR not set")
        raise SystemExit(1)

    deacon = Deacon(
        db_path=db_path,
        project_dir=project_dir,
        conductor_budget=conductor_budget,
        expected_branch=expected_branch,
    )

    # SIGUSR2 handler -> RECOVERING state
    def _sigusr2_handler(signum: int, frame: Any) -> None:
        log.info("SIGUSR2 received, entering RECOVERING state")
        deacon.state = DeaconState.RECOVERING

    signal.signal(signal.SIGUSR2, _sigusr2_handler)

    # SIGUSR1 handler -> clear blacklist
    def _sigusr1_handler(signum: int, frame: Any) -> None:
        log.info("SIGUSR1 received, clearing blacklist")
        deacon._clear_blacklist()

    signal.signal(signal.SIGUSR1, _sigusr1_handler)

    asyncio.run(run_deacon(deacon))


if __name__ == "__main__":
    main()
