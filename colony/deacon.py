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
STALE_LOCK_TIMEOUT_S = 180  # 3 minutes
HEARTBEAT_STALE_THRESHOLD_S = 300  # 5 minutes default
CONDUCTOR_TIMEOUT_DISPATCH_S = 30 * 60  # 30 minutes
CONDUCTOR_TIMEOUT_SYNTHESIZE_S = 60 * 60  # 60 minutes
DEBOUNCE_S = 2.0
TIMER_INTERVAL_S = 60
WATCHDOG_SELF_TIMEOUT_S = 90  # SC-COL-01
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
    _last_timer_fire: float = field(default_factory=time.monotonic)

    # -- DB helpers ----------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=8000")
        conn.row_factory = sqlite3.Row
        return conn

    # -- check_for_work ------------------------------------------------------

    def check_for_work(self) -> bool:
        """Query tmup DB for actionable colony tasks.

        Returns True if there are:
        - pending tasks with sdlc_loop_level IS NOT NULL
        - completed tasks with bridge_synced=0
        - tasks needing review (status='needs_review')
        """
        try:
            conn = self._connect()
            try:
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
                return bool(row and row["cnt"] > 0)
            finally:
                conn.close()
        except sqlite3.Error:
            log.exception("check_for_work DB error")
            return False

    # -- can_spawn_conductor -------------------------------------------------

    def can_spawn_conductor(self) -> bool:
        """Check if we can spawn a new Conductor.

        Returns False if lock file exists with a live PID and fresh timestamp.
        Returns True if no lock, stale lock (dead PID or old timestamp), etc.
        """
        if not LOCK_FILE.exists():
            return True

        try:
            content = LOCK_FILE.read_text().strip()
            parts = content.split("\n")
            if len(parts) < 2:
                return True

            pid = int(parts[0])
            timestamp = float(parts[1])

            # Check if PID is still alive
            try:
                os.kill(pid, 0)
            except (OSError, ProcessLookupError):
                # PID is dead -- stale lock
                log.info("Stale lock: PID %d is dead", pid)
                return True

            # Check if timestamp is stale
            if time.time() - timestamp > STALE_LOCK_TIMEOUT_S:
                log.info("Stale lock: timestamp %.0f is older than %ds", timestamp, STALE_LOCK_TIMEOUT_S)
                return True

            # Lock is valid -- another conductor is running
            return False

        except (ValueError, OSError):
            log.exception("Error reading lock file")
            return True

    # -- spawn_conductor -----------------------------------------------------

    def spawn_conductor(self, session_type: str = "DISPATCH") -> subprocess.Popen[bytes]:
        """Spawn a Conductor Claude Code session.

        Writes lock file, builds claude -p command, launches via Popen.
        Returns the Popen handle.
        """
        # Write lock file
        LOCK_FILE.write_text(f"{os.getpid()}\n{time.time()}\n")

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
        self.conductor_process = proc
        self.state = DeaconState.CONDUCTING
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

    def recover_stale_claims(self) -> int:
        """Find claimed tasks with stale heartbeats and reset them.

        Returns count of recovered tasks.
        """
        self.state = DeaconState.RECOVERING
        recovered = 0

        try:
            conn = self._connect()
            try:
                threshold = time.time() - HEARTBEAT_STALE_THRESHOLD_S
                threshold_iso = time.strftime(
                    "%Y-%m-%dT%H:%M:%SZ", time.gmtime(threshold)
                )

                # Find stale claimed tasks
                stale = conn.execute(
                    """
                    SELECT t.id, t.retry_count, t.max_retries, t.clone_dir
                    FROM tasks t
                    JOIN agents a ON t.owner = a.id
                    WHERE t.status = 'claimed'
                      AND t.sdlc_loop_level IS NOT NULL
                      AND a.last_heartbeat_at < ?
                    """,
                    (threshold_iso,),
                ).fetchall()

                for task in stale:
                    task_id = task["id"]
                    retry_count = task["retry_count"] or 0
                    max_retries = task["max_retries"] or 3
                    clone_dir = task["clone_dir"]

                    # SC-COL-21: preserve output before reset
                    if clone_dir:
                        output_path = Path(clone_dir) / "bead-output.md"
                        if output_path.exists():
                            recover_dir = Path(f"/tmp/sdlc-colony/recovered-outputs/{task_id}")
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
            finally:
                conn.close()
        except sqlite3.Error:
            log.exception("recover_stale_claims DB error")

        # Clean up stale lock file
        if LOCK_FILE.exists():
            try:
                content = LOCK_FILE.read_text().strip()
                parts = content.split("\n")
                if len(parts) >= 2:
                    pid = int(parts[0])
                    timestamp = float(parts[1])
                    pid_dead = False
                    try:
                        os.kill(pid, 0)
                    except (OSError, ProcessLookupError):
                        pid_dead = True
                    if pid_dead or time.time() - timestamp > STALE_LOCK_TIMEOUT_S:
                        LOCK_FILE.unlink(missing_ok=True)
            except (ValueError, OSError):
                LOCK_FILE.unlink(missing_ok=True)

        self.state = DeaconState.WATCHING
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

    # Launch inotifywait watcher as concurrent task
    watcher_task = asyncio.create_task(watch_db_changes(deacon))

    try:
        while True:
            deacon._last_timer_fire = time.monotonic()
            _sd_notify("WATCHDOG=1")

            if deacon.state == DeaconState.WATCHING:
                if deacon.check_for_work() and deacon.can_spawn_conductor():
                    deacon.spawn_conductor("DISPATCH")

            elif deacon.state == DeaconState.CONDUCTING:
                proc = deacon.conductor_process
                if proc is not None:
                    ret = proc.poll()
                    if ret is not None:
                        # Conductor exited
                        _parse_conductor_output(proc)
                        deacon.conductor_process = None
                        LOCK_FILE.unlink(missing_ok=True)
                        log.info("Conductor exited with code %d, debouncing", ret)
                        await asyncio.sleep(DEBOUNCE_S)
                        deacon.state = DeaconState.WATCHING
                    else:
                        # SC-COL-05: Check wall-clock timeout
                        _check_conductor_timeout(deacon)

            elif deacon.state == DeaconState.RECOVERING:
                recovered = deacon.recover_stale_claims()
                log.info("Recovery complete: %d tasks reset", recovered)
                # state is set to WATCHING by recover_stale_claims

            # SC-COL-01: Self-watchdog
            elapsed = time.monotonic() - deacon._last_timer_fire
            if elapsed > WATCHDOG_SELF_TIMEOUT_S:
                log.error(
                    "Self-watchdog triggered: timer hasn't fired in %.0fs (>%ds), sending SIGTERM",
                    elapsed,
                    WATCHDOG_SELF_TIMEOUT_S,
                )
                os.kill(os.getpid(), signal.SIGTERM)

            await asyncio.sleep(TIMER_INTERVAL_S)
    finally:
        watcher_task.cancel()
        try:
            await watcher_task
        except asyncio.CancelledError:
            pass


def _parse_conductor_output(proc: subprocess.Popen[bytes]) -> None:
    """Parse JSON output from Conductor for cost tracking."""
    try:
        stdout = proc.stdout.read() if proc.stdout else b""
        if stdout:
            data: dict[str, Any] = json.loads(stdout)
            session_id = data.get("session_id", "unknown")
            cost = data.get("total_cost_usd", 0.0)
            log.info("Conductor session %s cost $%.4f", session_id, cost)

            # Append to session log
            log_path = Path(__file__).parent / "colony-sessions.log"
            with open(log_path, "a") as f:
                f.write(
                    json.dumps(
                        {
                            "session_id": session_id,
                            "total_cost_usd": cost,
                            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        }
                    )
                    + "\n"
                )
    except (json.JSONDecodeError, OSError):
        log.exception("Failed to parse conductor output")


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
                timeout = CONDUCTOR_TIMEOUT_DISPATCH_S  # default

                if elapsed > timeout:
                    log.warning("Conductor timeout after %.0fs", elapsed)
                    # SC-COL-06: Check bridge lock before SIGTERM
                    if BRIDGE_LOCK_FILE.exists():
                        log.warning(
                            "Bridge lock active, waiting for bridge to finish"
                        )
                        return

                    proc.terminate()  # SIGTERM
                    try:
                        proc.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        proc.kill()  # SIGKILL
                    deacon.conductor_process = None
                    deacon.state = DeaconState.RECOVERING
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
                if (
                    deacon.state == DeaconState.WATCHING
                    and deacon.check_for_work()
                    and deacon.can_spawn_conductor()
                ):
                    deacon.spawn_conductor("DISPATCH")
                continue

            if not line:
                break

            # Drain buffer -- read any additional lines without blocking
            while True:
                try:
                    extra = await asyncio.wait_for(
                        proc.stdout.readline(), timeout=0.1
                    )
                    if not extra:
                        break
                except asyncio.TimeoutError:
                    break

            # Check for work after draining
            if (
                deacon.state == DeaconState.WATCHING
                and deacon.check_for_work()
                and deacon.can_spawn_conductor()
            ):
                deacon.spawn_conductor("DISPATCH")
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

    asyncio.run(run_deacon(deacon))


if __name__ == "__main__":
    main()
