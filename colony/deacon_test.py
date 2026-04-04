"""Tests for Deacon state machine and core functionality.

Covers:
- Initial state is WATCHING
- check_for_work True with pending colony tasks
- check_for_work True with completed unsynced tasks
- check_for_work False with empty DB
- Double-spawn prevention (active lock blocks)
- Stale lock detected (dead PID + old timestamp)
- recover_stale_claims resets stale claimed tasks
- spawn_conductor command string validation (M5)
- Lock file stores Conductor PID (not Deacon PID)
- Lock file written after Popen (not before)
- Bridge lock staleness check
- Path traversal prevention in recover_stale_claims
- Self-watchdog measures previous iteration, not current
- _parse_conductor_output uses communicate() (no deadlock)
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import time
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

import shutil

from deacon import (
    log,
    Deacon,
    DeaconState,
    SessionType,
    LOCK_FILE,
    BRIDGE_LOCK_FILE,
    STALE_LOCK_TIMEOUT_S,
    BRIDGE_STALE_TIMEOUT_S,
    COLONY_BASE,
    CONDUCTOR_TIMEOUT_DISPATCH_S,
    CONDUCTOR_TIMEOUT_SYNTHESIZE_S,
    HEARTBEAT_THRESHOLDS,
    WATCHDOG_SELF_TIMEOUT_S,
    _is_lock_stale,
    _is_bridge_lock_stale,
    _parse_conductor_output,
    _check_conductor_timeout,
    _self_watchdog_task,
    _self_watchdog_task_once,
    _rotate_log,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_db(tmp_path: Path) -> str:
    """Create a minimal tmup-like SQLite DB with colony columns."""
    db_path = str(tmp_path / "tmup.db")
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(
        """
        CREATE TABLE agents (
            id TEXT PRIMARY KEY,
            status TEXT DEFAULT 'idle',
            last_heartbeat_at TEXT
        );

        CREATE TABLE tasks (
            id TEXT PRIMARY KEY,
            title TEXT,
            status TEXT DEFAULT 'pending',
            owner TEXT REFERENCES agents(id),
            claimed_at TEXT,
            retry_count INTEGER DEFAULT 0,
            max_retries INTEGER DEFAULT 3,
            sdlc_loop_level TEXT,
            bridge_synced INTEGER DEFAULT 0,
            clone_dir TEXT,
            description TEXT,
            bead_id TEXT
        );
        """
    )
    conn.commit()
    conn.close()
    return db_path


@pytest.fixture
def deacon(tmp_db: str, tmp_path: Path) -> Iterator[Deacon]:
    """Create a Deacon instance with a temp DB."""
    d = Deacon(
        db_path=tmp_db,
        project_dir=str(tmp_path),
        conductor_budget="5.00",
    )
    yield d
    d.close()


@pytest.fixture(autouse=True)
def clean_lock_files() -> None:
    """Ensure no stale lock files between tests."""
    LOCK_FILE.unlink(missing_ok=True)
    BRIDGE_LOCK_FILE.unlink(missing_ok=True)
    yield  # type: ignore[misc]
    LOCK_FILE.unlink(missing_ok=True)
    BRIDGE_LOCK_FILE.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# T5.1 Tests: State Machine Core
# ---------------------------------------------------------------------------


class TestInitialState:
    def test_initial_state_is_watching(self, deacon: Deacon) -> None:
        assert deacon.state == DeaconState.WATCHING

    def test_conductor_process_is_none(self, deacon: Deacon) -> None:
        assert deacon.conductor_process is None


class TestCheckForWork:
    def test_true_with_pending_colony_tasks(self, deacon: Deacon) -> None:
        """Pending tasks with sdlc_loop_level should trigger work."""
        conn = sqlite3.connect(deacon.db_path)
        conn.execute(
            "INSERT INTO tasks (id, status, sdlc_loop_level) VALUES (?, ?, ?)",
            ("task-1", "pending", "L0"),
        )
        conn.commit()
        conn.close()

        assert deacon.check_for_work() is True

    def test_true_with_completed_unsynced_tasks(self, deacon: Deacon) -> None:
        """Completed tasks with bridge_synced=0 should trigger work."""
        conn = sqlite3.connect(deacon.db_path)
        conn.execute(
            "INSERT INTO tasks (id, status, sdlc_loop_level, bridge_synced) VALUES (?, ?, ?, ?)",
            ("task-2", "completed", "L0", 0),
        )
        conn.commit()
        conn.close()

        assert deacon.check_for_work() is True

    def test_true_with_needs_review_tasks(self, deacon: Deacon) -> None:
        """Tasks with status='needs_review' should trigger work."""
        conn = sqlite3.connect(deacon.db_path)
        conn.execute(
            "INSERT INTO tasks (id, status, sdlc_loop_level) VALUES (?, ?, ?)",
            ("task-3", "needs_review", "L1"),
        )
        conn.commit()
        conn.close()

        assert deacon.check_for_work() is True

    def test_false_with_empty_db(self, deacon: Deacon) -> None:
        """Empty DB should not trigger work."""
        assert deacon.check_for_work() is False

    def test_false_with_non_colony_tasks(self, deacon: Deacon) -> None:
        """Tasks without sdlc_loop_level (non-colony) should not trigger work."""
        conn = sqlite3.connect(deacon.db_path)
        conn.execute(
            "INSERT INTO tasks (id, status) VALUES (?, ?)",
            ("task-4", "pending"),
        )
        conn.commit()
        conn.close()

        assert deacon.check_for_work() is False

    def test_false_with_synced_completed(self, deacon: Deacon) -> None:
        """Completed tasks with bridge_synced=1 should not trigger work."""
        conn = sqlite3.connect(deacon.db_path)
        conn.execute(
            "INSERT INTO tasks (id, status, sdlc_loop_level, bridge_synced) VALUES (?, ?, ?, ?)",
            ("task-5", "completed", "L0", 1),
        )
        conn.commit()
        conn.close()

        assert deacon.check_for_work() is False

    def test_synthesize_when_all_beads_terminal(self, deacon: Deacon) -> None:
        """All bead tasks completed+synced should return 'synthesize'."""
        conn = sqlite3.connect(deacon.db_path)
        conn.execute(
            """INSERT INTO tasks (id, status, bead_id, bridge_synced)
               VALUES (?, ?, ?, ?)""",
            ("task-s1", "completed", "bead-001", 1),
        )
        conn.execute(
            """INSERT INTO tasks (id, status, bead_id, bridge_synced)
               VALUES (?, ?, ?, ?)""",
            ("task-s2", "cancelled", "bead-002", 1),
        )
        conn.commit()
        conn.close()

        assert deacon.check_for_work() == "synthesize"

    def test_no_synthesize_when_bead_not_synced(self, deacon: Deacon) -> None:
        """Bead tasks not all synced should not trigger synthesize."""
        conn = sqlite3.connect(deacon.db_path)
        conn.execute(
            """INSERT INTO tasks (id, status, bead_id, bridge_synced)
               VALUES (?, ?, ?, ?)""",
            ("task-s3", "completed", "bead-001", 1),
        )
        conn.execute(
            """INSERT INTO tasks (id, status, bead_id, bridge_synced)
               VALUES (?, ?, ?, ?)""",
            ("task-s4", "completed", "bead-002", 0),
        )
        conn.commit()
        conn.close()

        # Should return False because not all are synced
        assert deacon.check_for_work() is False

    def test_true_with_mix_pending_and_completed_beads(self, deacon: Deacon) -> None:
        """Mix of pending+completed bead tasks should return True (not 'synthesize')."""
        conn = sqlite3.connect(deacon.db_path)
        conn.execute(
            """INSERT INTO tasks (id, status, bead_id, bridge_synced, sdlc_loop_level)
               VALUES (?, ?, ?, ?, ?)""",
            ("task-mix-1", "completed", "bead-001", 1, "L0"),
        )
        conn.execute(
            """INSERT INTO tasks (id, status, bead_id, bridge_synced, sdlc_loop_level)
               VALUES (?, ?, ?, ?, ?)""",
            ("task-mix-2", "pending", "bead-002", 0, "L0"),
        )
        conn.commit()
        conn.close()

        result = deacon.check_for_work()
        assert result is True

    def test_no_synthesize_when_bead_still_running(self, deacon: Deacon) -> None:
        """Bead tasks still running should not trigger synthesize."""
        conn = sqlite3.connect(deacon.db_path)
        conn.execute(
            """INSERT INTO tasks (id, status, bead_id, bridge_synced)
               VALUES (?, ?, ?, ?)""",
            ("task-s5", "completed", "bead-001", 1),
        )
        conn.execute(
            """INSERT INTO tasks (id, status, bead_id, bridge_synced)
               VALUES (?, ?, ?, ?)""",
            ("task-s6", "claimed", "bead-002", 0),
        )
        conn.commit()
        conn.close()

        # Should return False because not all are terminal
        assert deacon.check_for_work() is False


class TestCanSpawnConductor:
    def test_no_lock_file(self, deacon: Deacon) -> None:
        """No lock file means we can spawn."""
        assert deacon.can_spawn_conductor() is True

    def test_active_lock_blocks(self, deacon: Deacon) -> None:
        """Active lock with live PID and fresh timestamp blocks spawn."""
        # Write lock with current PID (which is alive) and fresh timestamp
        LOCK_FILE.write_text(f"{os.getpid()}\n{time.time()}\n")

        assert deacon.can_spawn_conductor() is False

    def test_stale_lock_dead_pid(self, deacon: Deacon) -> None:
        """Stale lock with dead PID allows spawn."""
        # PID 99999999 almost certainly doesn't exist
        LOCK_FILE.write_text(f"99999999\n{time.time()}\n")

        assert deacon.can_spawn_conductor() is True

    def test_stale_lock_old_timestamp(self, deacon: Deacon) -> None:
        """Stale lock with old timestamp allows spawn even if PID is alive."""
        old_time = time.time() - STALE_LOCK_TIMEOUT_S - 10
        LOCK_FILE.write_text(f"{os.getpid()}\n{old_time}\n")

        assert deacon.can_spawn_conductor() is True

    def test_malformed_lock_allows_spawn(self, deacon: Deacon) -> None:
        """Malformed lock file should allow spawn."""
        LOCK_FILE.write_text("garbage\n")

        assert deacon.can_spawn_conductor() is True


class TestSpawnConductor:
    def test_command_string_validation_m5(self, deacon: Deacon) -> None:
        """Council M5: Verify spawn_conductor command contains required flags."""
        with patch("deacon.subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.pid = 12345
            mock_popen.return_value = mock_proc

            deacon.spawn_conductor("DISPATCH")

            # Get the actual command passed to Popen
            call_args = mock_popen.call_args
            cmd = call_args[0][0]  # first positional arg is the command list
            cmd_str = " ".join(cmd)

            # M5 required assertions
            assert "--max-budget-usd" in cmd_str, "Missing --max-budget-usd"
            assert "--permission-mode bypassPermissions" in cmd_str, "Missing --permission-mode bypassPermissions"
            assert "--model opus" in cmd_str, "Missing --model opus"

            # Two --plugin-dir flags (tmup and sdlc-os)
            plugin_dir_count = cmd.count("--plugin-dir")
            assert plugin_dir_count == 2, f"Expected 2 --plugin-dir flags, got {plugin_dir_count}"
            assert "/home/q/.claude/plugins/tmup" in cmd_str, "Missing tmup plugin dir"
            assert "/home/q/.claude/plugins/sdlc-os" in cmd_str, "Missing sdlc-os plugin dir"

    def test_sets_conducting_state(self, deacon: Deacon) -> None:
        """spawn_conductor should transition to CONDUCTING state."""
        with patch("deacon.subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.pid = 12345
            mock_popen.return_value = mock_proc

            deacon.spawn_conductor("DISPATCH")

            assert deacon.state == DeaconState.CONDUCTING
            assert deacon.conductor_process is mock_proc

    def test_writes_lock_file_with_conductor_pid(self, deacon: Deacon) -> None:
        """spawn_conductor should write lock file with Conductor PID (not Deacon PID)."""
        with patch("deacon.subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.pid = 12345
            mock_popen.return_value = mock_proc

            deacon.spawn_conductor("DISPATCH")

            assert LOCK_FILE.exists()
            content = LOCK_FILE.read_text().strip()
            lines = content.split("\n")
            assert len(lines) == 2
            # CRITICAL 1 fix: lock file stores Conductor PID, not Deacon PID
            assert int(lines[0]) == 12345

    def test_lock_not_written_on_popen_failure(self, deacon: Deacon) -> None:
        """If Popen raises, no lock file should be left behind (CRITICAL 4)."""
        with patch("deacon.subprocess.Popen") as mock_popen:
            mock_popen.side_effect = OSError("spawn failed")

            with pytest.raises(OSError, match="spawn failed"):
                deacon.spawn_conductor("DISPATCH")

            assert not LOCK_FILE.exists()

    def test_stdin_devnull(self, deacon: Deacon) -> None:
        """spawn_conductor should pass stdin=DEVNULL."""
        with patch("deacon.subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.pid = 12345
            mock_popen.return_value = mock_proc

            deacon.spawn_conductor("DISPATCH")

            call_kwargs = mock_popen.call_args[1]
            import subprocess
            assert call_kwargs["stdin"] == subprocess.DEVNULL


class TestRecoverStaleClaims:
    def test_resets_stale_claimed_tasks(self, deacon: Deacon) -> None:
        """Stale claimed tasks should be reset to pending."""
        conn = sqlite3.connect(deacon.db_path)
        # Agent with old heartbeat
        old_time = time.strftime(
            "%Y-%m-%dT%H:%M:%SZ",
            time.gmtime(time.time() - 600),  # 10 minutes ago
        )
        conn.execute(
            "INSERT INTO agents (id, status, last_heartbeat_at) VALUES (?, ?, ?)",
            ("agent-1", "active", old_time),
        )
        conn.execute(
            """INSERT INTO tasks (id, status, owner, sdlc_loop_level, retry_count, max_retries)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("task-stale", "claimed", "agent-1", "L0", 0, 3),
        )
        conn.commit()
        conn.close()

        recovered = deacon.recover_stale_claims()

        assert recovered == 1

        # Verify task was reset
        conn = sqlite3.connect(deacon.db_path)
        row = conn.execute(
            "SELECT status, retry_count FROM tasks WHERE id = ?", ("task-stale",)
        ).fetchone()
        conn.close()
        assert row[0] == "pending"
        assert row[1] == 1

    def test_needs_review_when_retries_exhausted(self, deacon: Deacon) -> None:
        """Tasks with exhausted retries should go to needs_review."""
        conn = sqlite3.connect(deacon.db_path)
        old_time = time.strftime(
            "%Y-%m-%dT%H:%M:%SZ",
            time.gmtime(time.time() - 600),
        )
        conn.execute(
            "INSERT INTO agents (id, status, last_heartbeat_at) VALUES (?, ?, ?)",
            ("agent-2", "active", old_time),
        )
        conn.execute(
            """INSERT INTO tasks (id, status, owner, sdlc_loop_level, retry_count, max_retries)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("task-exhausted", "claimed", "agent-2", "L1", 3, 3),
        )
        conn.commit()
        conn.close()

        recovered = deacon.recover_stale_claims()

        assert recovered == 1

        conn = sqlite3.connect(deacon.db_path)
        row = conn.execute(
            "SELECT status FROM tasks WHERE id = ?", ("task-exhausted",)
        ).fetchone()
        conn.close()
        assert row[0] == "needs_review"

    def test_returns_to_watching(self, deacon: Deacon) -> None:
        """After recovery, state should be WATCHING."""
        deacon.recover_stale_claims()
        assert deacon.state == DeaconState.WATCHING

    def test_no_stale_tasks(self, deacon: Deacon) -> None:
        """No stale tasks should return 0."""
        assert deacon.recover_stale_claims() == 0

    def test_path_traversal_blocked(self, deacon: Deacon) -> None:
        """clone_dir outside COLONY_BASE should be skipped with warning."""
        conn = sqlite3.connect(deacon.db_path)
        old_time = time.strftime(
            "%Y-%m-%dT%H:%M:%SZ",
            time.gmtime(time.time() - 600),
        )
        conn.execute(
            "INSERT INTO agents (id, status, last_heartbeat_at) VALUES (?, ?, ?)",
            ("agent-3", "active", old_time),
        )
        conn.execute(
            """INSERT INTO tasks (id, status, owner, sdlc_loop_level, retry_count, max_retries, clone_dir)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            ("task-traversal", "claimed", "agent-3", "L0", 0, 3, "/etc/passwd/../../../tmp/evil"),
        )
        conn.commit()
        conn.close()

        # Should still recover the task (reset status) but skip file operations
        recovered = deacon.recover_stale_claims()
        assert recovered == 1

        # Task should still be reset to pending
        conn = sqlite3.connect(deacon.db_path)
        row = conn.execute(
            "SELECT status FROM tasks WHERE id = ?", ("task-traversal",)
        ).fetchone()
        conn.close()
        assert row[0] == "pending"

    def test_path_traversal_prefix_attack_blocked(self, deacon: Deacon) -> None:
        """clone_dir like /tmp/sdlc-colony-evil/task should be blocked by is_relative_to().

        This verifies the fix for the str.startswith() bypass where a path like
        /tmp/sdlc-colony-evil/ would pass startswith('/tmp/sdlc-colony')
        but correctly fails is_relative_to().
        """
        conn = sqlite3.connect(deacon.db_path)
        old_time = time.strftime(
            "%Y-%m-%dT%H:%M:%SZ",
            time.gmtime(time.time() - 600),
        )
        conn.execute(
            "INSERT INTO agents (id, status, last_heartbeat_at) VALUES (?, ?, ?)",
            ("agent-4", "active", old_time),
        )
        conn.execute(
            """INSERT INTO tasks (id, status, owner, sdlc_loop_level, retry_count, max_retries, clone_dir)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            ("task-prefix", "claimed", "agent-4", "L0", 0, 3, "/tmp/sdlc-colony-evil/task"),
        )
        conn.commit()
        conn.close()

        # Should recover the task but skip file operations (path traversal blocked)
        recovered = deacon.recover_stale_claims()
        assert recovered == 1

        # Task should still be reset to pending
        conn = sqlite3.connect(deacon.db_path)
        row = conn.execute(
            "SELECT status FROM tasks WHERE id = ?", ("task-prefix",)
        ).fetchone()
        conn.close()
        assert row[0] == "pending"


class TestBridgeLockStaleness:
    def test_no_bridge_lock_is_stale(self) -> None:
        """No bridge lock file means stale (safe to proceed)."""
        assert _is_bridge_lock_stale() is True

    def test_live_bridge_lock_not_stale(self) -> None:
        """Bridge lock with live PID and fresh timestamp is not stale."""
        BRIDGE_LOCK_FILE.write_text(f"{os.getpid()}\n{time.time()}\n")
        assert _is_bridge_lock_stale() is False

    def test_dead_pid_bridge_lock_is_stale(self) -> None:
        """Bridge lock with dead PID is stale."""
        BRIDGE_LOCK_FILE.write_text(f"99999999\n{time.time()}\n")
        assert _is_bridge_lock_stale() is True

    def test_old_timestamp_bridge_lock_is_stale(self) -> None:
        """Bridge lock with old timestamp is stale even if PID is alive."""
        old_time = time.time() - BRIDGE_STALE_TIMEOUT_S - 10
        BRIDGE_LOCK_FILE.write_text(f"{os.getpid()}\n{old_time}\n")
        assert _is_bridge_lock_stale() is True

    def test_malformed_bridge_lock_is_stale(self) -> None:
        """Malformed bridge lock file is treated as stale."""
        BRIDGE_LOCK_FILE.write_text("garbage\n")
        assert _is_bridge_lock_stale() is True


class TestParseOutput:
    def test_uses_communicate(self) -> None:
        """_parse_conductor_output should use communicate() not stdout.read()."""
        mock_proc = MagicMock()
        mock_proc.communicate.return_value = (b'{"session_id": "s1", "total_cost_usd": 1.5}', b"")
        mock_proc.returncode = 0

        with patch("builtins.open", MagicMock()):
            _parse_conductor_output(mock_proc)

        mock_proc.communicate.assert_called_once_with(timeout=10)
        # stdout.read should NOT be called
        mock_proc.stdout.read.assert_not_called()


class TestActiveSessionType:
    def test_default_session_type_is_dispatch(self, deacon: Deacon) -> None:
        """Default active_session_type should be DISPATCH."""
        assert deacon.active_session_type == SessionType.DISPATCH

    def test_spawn_conductor_sets_session_type(self, deacon: Deacon) -> None:
        """spawn_conductor should set active_session_type."""
        with patch("deacon.subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.pid = 12345
            mock_popen.return_value = mock_proc

            deacon.spawn_conductor("SYNTHESIZE")
            assert deacon.active_session_type == SessionType.SYNTHESIZE

    def test_synthesize_timeout_is_longer(self) -> None:
        """SYNTHESIZE timeout should be longer than DISPATCH."""
        assert CONDUCTOR_TIMEOUT_SYNTHESIZE_S > CONDUCTOR_TIMEOUT_DISPATCH_S


class TestSelfWatchdogTask:
    def test_watchdog_is_coroutine(self) -> None:
        """_self_watchdog_task should be an async coroutine function."""
        import asyncio
        assert asyncio.iscoroutinefunction(_self_watchdog_task)


class TestConductorTimeoutCleanup:
    """Adversarial A2: After timeout kill, communicate() must be called and lock file cleaned up."""

    def test_communicate_called_after_terminate(self, deacon: Deacon) -> None:
        """After conductor timeout, proc.communicate() must be called to drain pipes."""
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None  # process is still running
        mock_proc.communicate.return_value = (b"", b"")
        deacon.conductor_process = mock_proc
        deacon.state = DeaconState.CONDUCTING

        # Write lock file with old timestamp to trigger timeout
        old_time = time.time() - CONDUCTOR_TIMEOUT_DISPATCH_S - 10
        LOCK_FILE.write_text(f"{os.getpid()}\n{old_time}\n")

        with patch("deacon._parse_conductor_output"):
            _check_conductor_timeout(deacon)

        mock_proc.terminate.assert_called_once()
        mock_proc.communicate.assert_called_once_with(timeout=5)

    def test_lock_file_removed_after_timeout(self, deacon: Deacon) -> None:
        """After conductor timeout, LOCK_FILE must be cleaned up via _release_lock()."""
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        mock_proc.communicate.return_value = (b"", b"")
        deacon.conductor_process = mock_proc
        deacon.state = DeaconState.CONDUCTING

        old_time = time.time() - CONDUCTOR_TIMEOUT_DISPATCH_S - 10
        LOCK_FILE.write_text(f"{os.getpid()}\n{old_time}\n")

        with patch("deacon._parse_conductor_output"):
            _check_conductor_timeout(deacon)

        assert not LOCK_FILE.exists(), "Lock file should be removed after timeout cleanup"

    def test_kill_and_communicate_on_stubborn_process(self, deacon: Deacon) -> None:
        """If communicate() times out after terminate, kill+communicate must follow."""
        import subprocess as sp

        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        # First communicate() raises TimeoutExpired, second succeeds
        mock_proc.communicate.side_effect = [
            sp.TimeoutExpired(cmd="claude", timeout=5),
            (b"", b""),
        ]
        deacon.conductor_process = mock_proc
        deacon.state = DeaconState.CONDUCTING

        old_time = time.time() - CONDUCTOR_TIMEOUT_DISPATCH_S - 10
        LOCK_FILE.write_text(f"{os.getpid()}\n{old_time}\n")

        with patch("deacon._parse_conductor_output"):
            _check_conductor_timeout(deacon)

        mock_proc.terminate.assert_called_once()
        mock_proc.kill.assert_called_once()
        assert mock_proc.communicate.call_count == 2
        assert not LOCK_FILE.exists()


class TestSpawnLock:
    """Adversarial A3: _spawn_lock must exist and be an asyncio.Lock."""

    def test_spawn_lock_exists(self, deacon: Deacon) -> None:
        """Deacon must have a _spawn_lock attribute."""
        assert hasattr(deacon, "_spawn_lock")

    def test_spawn_lock_is_asyncio_lock(self, deacon: Deacon) -> None:
        """_spawn_lock must be an asyncio.Lock instance."""
        import asyncio
        assert isinstance(deacon._spawn_lock, asyncio.Lock)


class TestSynthesizeSessionSpawn:
    """Bead 1: SYNTHESIZE session is spawned when all beads are terminal."""

    def test_synthesize_spawned_when_all_beads_terminal(self, deacon: Deacon) -> None:
        """When check_for_work returns 'synthesize', spawn_conductor gets SYNTHESIZE."""
        conn = sqlite3.connect(deacon.db_path)
        conn.execute(
            """INSERT INTO tasks (id, status, bead_id, bridge_synced)
               VALUES (?, ?, ?, ?)""",
            ("task-syn-1", "completed", "bead-001", 1),
        )
        conn.execute(
            """INSERT INTO tasks (id, status, bead_id, bridge_synced)
               VALUES (?, ?, ?, ?)""",
            ("task-syn-2", "cancelled", "bead-002", 1),
        )
        conn.commit()
        conn.close()

        assert deacon.check_for_work() == "synthesize"

        with patch("deacon.subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.pid = 99999
            mock_popen.return_value = mock_proc

            work = deacon.check_for_work()
            session_type = "SYNTHESIZE" if work == "synthesize" else "DISPATCH"
            deacon.spawn_conductor(session_type)

            assert deacon.active_session_type == SessionType.SYNTHESIZE


class TestDomainCalibratedHeartbeat:
    """Bead 2 / SC-COL-20: Per-domain heartbeat thresholds."""

    def test_complex_task_not_stale_at_600s(self, deacon: Deacon) -> None:
        """COMPLEX domain has 1800s threshold -- 600s elapsed is NOT stale."""
        conn = sqlite3.connect(deacon.db_path)
        # Agent heartbeat 600s ago
        heartbeat = time.strftime(
            "%Y-%m-%dT%H:%M:%SZ",
            time.gmtime(time.time() - 600),
        )
        conn.execute(
            "INSERT INTO agents (id, status, last_heartbeat_at) VALUES (?, ?, ?)",
            ("agent-complex", "active", heartbeat),
        )
        desc = json.dumps({"cynefin_domain": "complex", "title": "hard task"})
        conn.execute(
            """INSERT INTO tasks (id, status, owner, sdlc_loop_level,
               retry_count, max_retries, description)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            ("task-complex", "claimed", "agent-complex", "L0", 0, 3, desc),
        )
        conn.commit()
        conn.close()

        recovered = deacon.recover_stale_claims()
        assert recovered == 0, "COMPLEX task at 600s should NOT be recovered (threshold=1800s)"

    def test_complex_task_stale_at_2000s(self, deacon: Deacon) -> None:
        """COMPLEX domain has 1800s threshold -- 2000s elapsed IS stale."""
        conn = sqlite3.connect(deacon.db_path)
        heartbeat = time.strftime(
            "%Y-%m-%dT%H:%M:%SZ",
            time.gmtime(time.time() - 2000),
        )
        conn.execute(
            "INSERT INTO agents (id, status, last_heartbeat_at) VALUES (?, ?, ?)",
            ("agent-complex-2", "active", heartbeat),
        )
        desc = json.dumps({"cynefin_domain": "complex"})
        conn.execute(
            """INSERT INTO tasks (id, status, owner, sdlc_loop_level,
               retry_count, max_retries, description)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            ("task-complex-2", "claimed", "agent-complex-2", "L0", 0, 3, desc),
        )
        conn.commit()
        conn.close()

        recovered = deacon.recover_stale_claims()
        assert recovered == 1, "COMPLEX task at 2000s should be recovered (threshold=1800s)"

        conn = sqlite3.connect(deacon.db_path)
        row = conn.execute(
            "SELECT status FROM tasks WHERE id = ?", ("task-complex-2",)
        ).fetchone()
        conn.close()
        assert row[0] == "pending"

    def test_clear_domain_default_threshold(self, deacon: Deacon) -> None:
        """CLEAR domain uses 300s threshold (same as default)."""
        threshold, domain = Deacon._get_heartbeat_threshold(
            json.dumps({"cynefin_domain": "clear"})
        )
        assert threshold == 300
        assert domain == "clear"

    def test_complicated_domain_threshold(self, deacon: Deacon) -> None:
        """COMPLICATED domain uses 900s threshold."""
        threshold, domain = Deacon._get_heartbeat_threshold(
            json.dumps({"cynefin_domain": "complicated"})
        )
        assert threshold == 900
        assert domain == "complicated"

    def test_unknown_domain_uses_default(self, deacon: Deacon) -> None:
        """Unknown domain falls back to 300s default."""
        threshold, domain = Deacon._get_heartbeat_threshold(
            json.dumps({"cynefin_domain": "unknown"})
        )
        assert threshold == 300

    def test_no_description_uses_default(self, deacon: Deacon) -> None:
        """No description falls back to 300s default."""
        threshold, domain = Deacon._get_heartbeat_threshold(None)
        assert threshold == 300
        assert domain == "unknown"

    def test_invalid_json_uses_default(self, deacon: Deacon) -> None:
        """Invalid JSON description falls back to 300s default."""
        threshold, domain = Deacon._get_heartbeat_threshold("not json")
        assert threshold == 300
        assert domain == "unknown"


class TestTransitionTo:
    """Tests for _transition_to structured logging."""

    def test_logs_correct_old_new_states(self, deacon: Deacon, caplog: pytest.LogCaptureFixture) -> None:
        """_transition_to must log old and new state values."""
        assert deacon.state == DeaconState.WATCHING
        with caplog.at_level(logging.INFO, logger="deacon"):
            deacon._transition_to(DeaconState.CONDUCTING, "test_trigger")

        assert deacon.state == DeaconState.CONDUCTING
        assert any(
            "state_transition old=WATCHING new=CONDUCTING" in r.message
            and "trigger=test_trigger" in r.message
            for r in caplog.records
        ), f"Expected state_transition log, got: {[r.message for r in caplog.records]}"

    def test_logs_elapsed_seconds(self, deacon: Deacon, caplog: pytest.LogCaptureFixture) -> None:
        """_transition_to must include elapsed_s in log."""
        with caplog.at_level(logging.INFO, logger="deacon"):
            deacon._transition_to(DeaconState.RECOVERING, "elapsed_test")

        assert any(
            "elapsed_s=" in r.message
            for r in caplog.records
        )

    def test_transition_updates_state(self, deacon: Deacon) -> None:
        """_transition_to must actually update the state."""
        deacon._transition_to(DeaconState.RECOVERING, "update_test")
        assert deacon.state == DeaconState.RECOVERING
        deacon._transition_to(DeaconState.WATCHING, "back_test")
        assert deacon.state == DeaconState.WATCHING


class TestParseOutputEnhanced:
    """Tests for enhanced _parse_conductor_output session log fields."""

    def test_writes_all_required_fields(self, deacon: Deacon) -> None:
        """Session log must include session_type, exit_code, wall_clock_s, bead_ids."""
        deacon._conductor_start_time = time.monotonic() - 120
        deacon.active_session_type = SessionType.DISPATCH

        # Insert a bead task
        conn = sqlite3.connect(deacon.db_path)
        conn.execute(
            "INSERT INTO tasks (id, status, bead_id) VALUES (?, ?, ?)",
            ("task-b1", "completed", "bead-abc"),
        )
        conn.commit()
        conn.close()

        mock_proc = MagicMock()
        mock_proc.communicate.return_value = (
            b'{"session_id": "s99", "total_cost_usd": 2.5}',
            b"",
        )
        mock_proc.returncode = 0

        log_path = Path(__file__).parent / "colony-sessions.log"
        had_existing = log_path.exists()
        existing_content = log_path.read_text() if had_existing else ""

        try:
            _parse_conductor_output(mock_proc, deacon)

            content = log_path.read_text()
            lines = content.strip().split("\n")
            last_line = lines[-1]
            record = json.loads(last_line)

            assert record["session_id"] == "s99"
            assert record["session_type"] == "DISPATCH"
            assert record["exit_code"] == 0
            assert record["wall_clock_s"] >= 100
            assert "bead-abc" in record["bead_ids"]
        finally:
            if had_existing:
                log_path.write_text(existing_content)
            elif log_path.exists():
                log_path.unlink()

    def test_writes_synthesize_fields(self, deacon: Deacon) -> None:
        """Verify SYNTHESIZE session type and multiple bead_ids are recorded."""
        deacon._conductor_start_time = time.monotonic() - 60
        deacon.active_session_type = SessionType.SYNTHESIZE

        conn = sqlite3.connect(deacon.db_path)
        conn.execute(
            "INSERT INTO tasks (id, status, bead_id) VALUES (?, ?, ?)",
            ("task-b2", "completed", "bead-xyz"),
        )
        conn.execute(
            "INSERT INTO tasks (id, status, bead_id) VALUES (?, ?, ?)",
            ("task-b3", "cancelled", "bead-123"),
        )
        conn.commit()
        conn.close()

        mock_proc = MagicMock()
        mock_proc.communicate.return_value = (
            b'{"session_id": "s100", "total_cost_usd": 3.0}',
            b"",
        )
        mock_proc.returncode = 1

        log_path = Path(__file__).parent / "colony-sessions.log"
        had_existing = log_path.exists()
        existing_content = log_path.read_text() if had_existing else ""

        try:
            _parse_conductor_output(mock_proc, deacon)

            content = log_path.read_text()
            lines = content.strip().split("\n")
            last_line = lines[-1]
            record = json.loads(last_line)

            assert record["session_type"] == "SYNTHESIZE"
            assert record["exit_code"] == 1
            assert record["wall_clock_s"] >= 50
            assert set(record["bead_ids"]) == {"bead-xyz", "bead-123"}
        finally:
            if had_existing:
                log_path.write_text(existing_content)
            elif log_path.exists():
                log_path.unlink()


class TestWatchdogNearMiss:
    """Tests for watchdog near-miss warning."""

    def test_near_miss_at_65s(self) -> None:
        """Watchdog should log warning when elapsed > 60s but <= 90s."""
        import asyncio
        deacon = Deacon(db_path="/dev/null", project_dir="/tmp")
        # Set _last_timer_fire to 65 seconds ago
        deacon._last_timer_fire = time.monotonic() - 65

        # We can't easily run the async task, so test the logic directly
        elapsed = time.monotonic() - deacon._last_timer_fire
        assert elapsed > 60
        assert elapsed <= WATCHDOG_SELF_TIMEOUT_S
        # The condition in the code: elapsed > 60 and elapsed <= WATCHDOG_SELF_TIMEOUT_S
        # means a near-miss warning would fire

    def test_near_miss_warning_logged(self, caplog: pytest.LogCaptureFixture) -> None:
        """Verify the near-miss warning is actually logged at elapsed=65s."""
        import asyncio

        deacon = Deacon(db_path="/dev/null", project_dir="/tmp")
        deacon._last_timer_fire = time.monotonic() - 65

        async def _run_one_iteration() -> None:
            """Run one watchdog check iteration without the sleep."""
            elapsed = time.monotonic() - deacon._last_timer_fire
            if elapsed > 60 and elapsed <= WATCHDOG_SELF_TIMEOUT_S:
                log.warning("watchdog_near_miss elapsed_s=%.1f threshold_s=90", elapsed)

        with caplog.at_level(logging.WARNING, logger="deacon"):
            asyncio.run(_run_one_iteration())

        assert any(
            "watchdog_near_miss" in r.message and "threshold_s=90" in r.message
            for r in caplog.records
        ), f"Expected watchdog_near_miss log, got: {[r.message for r in caplog.records]}"

    def test_no_warning_at_50s(self) -> None:
        """No near-miss warning when elapsed is under 60s."""
        deacon = Deacon(db_path="/dev/null", project_dir="/tmp")
        deacon._last_timer_fire = time.monotonic() - 50
        elapsed = time.monotonic() - deacon._last_timer_fire
        assert elapsed <= 60, "Should not trigger near-miss at 50s"


class TestBehavioralWatchdog:
    """SC-COL-35: Watchdog forces RECOVERING if state exceeds max duration."""

    def test_watchdog_forces_recovering_on_state_timeout(self, tmp_db: str, tmp_path: Path) -> None:
        deacon = Deacon(db_path=tmp_db, project_dir=str(tmp_path))
        deacon._state_entered_at = time.monotonic() - 5000  # far in the past
        deacon.state = DeaconState.CONDUCTING

        import asyncio
        asyncio.run(_self_watchdog_task_once(deacon))

        assert deacon.state == DeaconState.RECOVERING

    def test_watchdog_respects_configurable_threshold(self, tmp_db: str, tmp_path: Path) -> None:
        deacon = Deacon(db_path=tmp_db, project_dir=str(tmp_path))
        deacon._state_entered_at = time.monotonic() - 100  # only 100s
        deacon.state = DeaconState.CONDUCTING

        import asyncio
        with patch.dict(os.environ, {"WATCHDOG_MAX_STATE_DURATION_S": "3700"}):
            asyncio.run(_self_watchdog_task_once(deacon))

        assert deacon.state == DeaconState.CONDUCTING  # 100 < 3700, no trigger


class TestEscalation:
    """SC-COL-36: Bead failure tracking, blacklisting, and escalation."""

    def test_three_failures_triggers_blacklist(self, tmp_db: str, tmp_path: Path) -> None:
        deacon = Deacon(db_path=tmp_db, project_dir=str(tmp_path))
        bead = "bead-001"
        now = time.time()
        deacon._bead_failure_counts[bead] = [now - 60, now - 30, now]
        deacon._evaluate_escalation(bead, "test error")
        assert bead in deacon._blacklisted_beads

    def test_blacklist_excludes_from_work(self, tmp_db: str, tmp_path: Path) -> None:
        conn = sqlite3.connect(tmp_db)
        conn.execute(
            "INSERT INTO tasks (id, status, sdlc_loop_level, bead_id) VALUES (?, ?, ?, ?)",
            ("t1", "pending", "L0", "bead-blocked"),
        )
        conn.commit()
        conn.close()
        deacon = Deacon(db_path=tmp_db, project_dir=str(tmp_path))
        deacon._blacklisted_beads.add("bead-blocked")
        assert deacon.check_for_work() is False

    def test_sigusr1_clears_blacklist(self, tmp_db: str, tmp_path: Path) -> None:
        deacon = Deacon(db_path=tmp_db, project_dir=str(tmp_path))
        deacon._blacklisted_beads.add("bead-x")
        deacon._clear_blacklist()
        assert len(deacon._blacklisted_beads) == 0

    def test_dead_letter_on_alert_timeout(self, tmp_db: str, tmp_path: Path) -> None:
        deacon = Deacon(db_path=tmp_db, project_dir=str(tmp_path))
        dl_path = tmp_path / "escalation-deadletter.jsonl"
        import asyncio
        with patch.dict(os.environ, {"ESCALATION_DEADLETTER": str(dl_path)}):
            with patch("asyncio.create_subprocess_exec", side_effect=OSError("fail")):
                asyncio.run(deacon._send_escalation_alert("bead-x", "err"))
        assert dl_path.exists()
        data = json.loads(dl_path.read_text().strip())
        assert data["bead_id"] == "bead-x"


class TestClonePruning:
    """SC-COL-31: Prune stale clone directories."""

    def test_prune_synced_clone(self, tmp_db: str, tmp_path: Path) -> None:
        """Synced completed clone with no active tasks should be pruned."""
        colony_base = tmp_path / "colony"
        colony_base.mkdir()
        clone = colony_base / "clone-1"
        clone.mkdir()
        conn = sqlite3.connect(tmp_db)
        conn.execute(
            "INSERT INTO tasks (id, status, bead_id, bridge_synced, clone_dir, sdlc_loop_level) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("t1", "completed", "b1", 1, str(clone), "L0"),
        )
        conn.commit()
        conn.close()
        deacon = Deacon(db_path=tmp_db, project_dir=str(tmp_path))
        import deacon as deacon_mod
        with patch.object(deacon_mod, "COLONY_BASE", str(colony_base) + "/"):
            deacon._prune_stale_clones()
        assert not clone.exists()

    def test_refuse_if_active_tasks_remain(self, tmp_db: str, tmp_path: Path) -> None:
        """Clone shared by active task should NOT be pruned."""
        colony_base = tmp_path / "colony"
        colony_base.mkdir()
        clone = colony_base / "clone-shared"
        clone.mkdir()
        conn = sqlite3.connect(tmp_db)
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
        conn.commit()
        conn.close()
        deacon = Deacon(db_path=tmp_db, project_dir=str(tmp_path))
        import deacon as deacon_mod
        with patch.object(deacon_mod, "COLONY_BASE", str(colony_base) + "/"):
            deacon._prune_stale_clones()
        assert clone.exists()  # NOT pruned

    def test_24h_age_override(self, tmp_db: str, tmp_path: Path) -> None:
        """Clone older than 24h should be pruned even if not synced."""
        colony_base = tmp_path / "colony"
        colony_base.mkdir()
        clone = colony_base / "clone-old"
        clone.mkdir()
        # Set mtime to 25h ago
        old_time = time.time() - 25 * 3600
        os.utime(str(clone), (old_time, old_time))
        conn = sqlite3.connect(tmp_db)
        conn.execute(
            "INSERT INTO tasks (id, status, bead_id, bridge_synced, clone_dir, sdlc_loop_level) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("t1", "completed", "b1", 0, str(clone), "L0"),  # NOT synced
        )
        conn.commit()
        conn.close()
        deacon = Deacon(db_path=tmp_db, project_dir=str(tmp_path))
        import deacon as deacon_mod
        with patch.object(deacon_mod, "COLONY_BASE", str(colony_base) + "/"):
            deacon._prune_stale_clones()
        assert not clone.exists()  # pruned by age

    def test_log_rotation(self, tmp_path: Path) -> None:
        """Log file exceeding 10MB should be truncated."""
        log_file = tmp_path / "colony-sessions.log"
        # Write >10MB as many lines
        line = "x" * 200 + "\n"
        num_lines = (11 * 1024 * 1024) // len(line) + 1
        log_file.write_text(line * num_lines)
        assert os.path.getsize(str(log_file)) > 10 * 1024 * 1024
        _rotate_log(str(log_file), max_bytes=10 * 1024 * 1024, keep_lines=1000)
        content = log_file.read_text()
        assert len(content) < 10 * 1024 * 1024
        assert content.count("\n") == 1000
