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

import os
import sqlite3
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from deacon import (
    Deacon,
    DeaconState,
    LOCK_FILE,
    BRIDGE_LOCK_FILE,
    STALE_LOCK_TIMEOUT_S,
    BRIDGE_STALE_TIMEOUT_S,
    COLONY_BASE,
    _is_bridge_lock_stale,
    _parse_conductor_output,
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
            description TEXT
        );
        """
    )
    conn.commit()
    conn.close()
    return db_path


@pytest.fixture
def deacon(tmp_db: str, tmp_path: Path) -> Deacon:
    """Create a Deacon instance with a temp DB."""
    return Deacon(
        db_path=tmp_db,
        project_dir=str(tmp_path),
        conductor_budget="5.00",
    )


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

        with patch("builtins.open", MagicMock()):
            _parse_conductor_output(mock_proc)

        mock_proc.communicate.assert_called_once_with(timeout=10)
        # stdout.read should NOT be called
        mock_proc.stdout.read.assert_not_called()
