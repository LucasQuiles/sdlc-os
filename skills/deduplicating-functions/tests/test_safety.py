"""Unit tests for the safety module (lock + preflight primitives)."""
from __future__ import annotations

import os
import sys
from unittest import mock

import pytest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
import safety  # noqa: E402
sys.path.pop(0)


# ── Preflight tests ─────────────────────────────────────────────────

def test_check_preflight_passes_when_memory_is_healthy():
    """A system with plenty of free RAM and few swapfiles should be allowed."""
    fake_status = {"free_gb": 32.0, "swap_used_mb": 0.0, "swapfile_count": 1}
    with mock.patch.object(safety, "_collect_status", return_value=fake_status):
        ok, reason = safety.check_preflight(min_free_gb=4.0, max_swapfiles=5)
    assert ok is True, f"Healthy system should pass, got: {reason}"
    assert "32.0gb free" in reason.lower()


def test_check_preflight_refuses_when_free_ram_too_low():
    fake_status = {"free_gb": 1.5, "swap_used_mb": 100.0, "swapfile_count": 2}
    with mock.patch.object(safety, "_collect_status", return_value=fake_status):
        ok, reason = safety.check_preflight(min_free_gb=4.0, max_swapfiles=5)
    assert ok is False
    assert "insufficient free ram" in reason.lower()
    assert "1.5gb" in reason.lower()


def test_check_preflight_refuses_when_swapfiles_exceed_threshold():
    """The 2026-04-11 panic system had 35 swapfiles. Anything > 5 is unsafe."""
    fake_status = {"free_gb": 16.0, "swap_used_mb": 8000.0, "swapfile_count": 35}
    with mock.patch.object(safety, "_collect_status", return_value=fake_status):
        ok, reason = safety.check_preflight(min_free_gb=4.0, max_swapfiles=5)
    assert ok is False
    assert "swapfiles" in reason.lower()
    assert "35" in reason


def test_check_preflight_skips_unsupported_platform():
    with mock.patch("platform.system", return_value="OpenBSD"):
        with mock.patch.object(safety, "_collect_status", return_value=None):
            ok, reason = safety.check_preflight()
    assert ok is True
    assert "skipped" in reason.lower()
    assert "openbsd" in reason.lower()


def test_darwin_pressure_status_parses_vm_stat_output():
    """Verify the vm_stat parser extracts free pages correctly."""
    fake_vm_stat = (
        "Mach Virtual Memory Statistics: (page size of 16384 bytes)\n"
        '"Pages free":                              524288.\n'
        '"Pages active":                            1048576.\n'
        '"Pages inactive":                          262144.\n'
        '"Pages speculative":                       65536.\n'
    )
    fake_swapusage = "total = 2048.00M  used = 423.50M  free = 1624.50M  (encrypted)\n"

    def _fake_check_output(cmd, **kwargs):
        if cmd[0] == "vm_stat":
            return fake_vm_stat
        if cmd[0] == "sysctl":
            return fake_swapusage
        if cmd[0] == "ls":
            return "swapfile0\nswapfile1\nswapfile2\n"
        raise FileNotFoundError(cmd)

    with mock.patch("subprocess.check_output", side_effect=_fake_check_output):
        status = safety.darwin_pressure_status()

    # 524288 free + 262144 inactive = 786432 pages * 16384 bytes = 12 GiB
    expected_free_gb = (524288 + 262144) * 16384 / (1024 ** 3)
    assert abs(status["free_gb"] - expected_free_gb) < 0.01
    assert status["swap_used_mb"] == pytest.approx(423.5)
    assert status["swapfile_count"] == 3


# ── Lock tests ──────────────────────────────────────────────────────

def test_acquire_pipeline_lock_writes_pid_and_blocks_second_attempt(tmp_path):
    """The lock primitive should record its holder's pid and refuse a
    second non-blocking acquisition.

    This is a unit test of the function itself — the integration test in
    test_pipeline_safety.py covers the CLI surface."""
    lock_path = str(tmp_path / "test.lock")

    fd1 = safety.acquire_pipeline_lock(lock_path, wait=False)
    try:
        # Holder pid should be written to the file
        with open(lock_path) as f:
            content = f.read().strip()
        assert content == str(os.getpid()), (
            f"Expected pid {os.getpid()} in lock file, got: {content!r}"
        )

        # Second non-blocking acquisition must raise BlockingIOError
        with pytest.raises(BlockingIOError):
            safety.acquire_pipeline_lock(lock_path, wait=False)
    finally:
        os.close(fd1)

    # After releasing, a fresh acquisition should succeed
    fd2 = safety.acquire_pipeline_lock(lock_path, wait=False)
    os.close(fd2)


def test_acquire_pipeline_lock_handles_bare_filename(tmp_path, monkeypatch):
    """A lock_path with no directory component should still work."""
    monkeypatch.chdir(tmp_path)
    fd = safety.acquire_pipeline_lock("bare.lock", wait=False)
    try:
        assert os.path.exists(tmp_path / "bare.lock")
    finally:
        os.close(fd)
