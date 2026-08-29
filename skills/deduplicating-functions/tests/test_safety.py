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


def _healthy_status(**overrides):
    status = {
        "free_gb": 32.0,
        "swap_used_mb": 1024.0,
        "swap_total_mb": 8192.0,
        "swap_used_pct": 12.5,
        "swap_headroom_mb": 7168.0,
        # Static pool by default: pins the original strict pct/headroom
        # semantics; dynamic-pool cases live in test_safety_dynamic_pool.py.
        "swap_pool_dynamic": False,
        "swap_growth_headroom_mb": 0.0,
        "swapfile_count": 1,
        "swapins": 100,
        "swapouts": 100,
        "compressor_occupied_mb": 1024.0,
        "compressor_segments": 1000,
        "compressor_segment_limit": 10000,
        "compressor_pool_used_pct": 10.0,
        "memory_pressure": "normal",
    }
    status.update(overrides)
    return status


# ── Preflight tests ─────────────────────────────────────────────────

def test_check_preflight_passes_when_memory_is_healthy():
    """A system with plenty of free RAM and few swapfiles should be allowed."""
    with mock.patch.object(safety, "_collect_window", return_value=(_healthy_status(), _healthy_status())):
        ok, reason = safety.check_preflight(min_free_gb=4.0, max_swapfiles=5)
    assert ok is True, f"Healthy system should pass, got: {reason}"
    assert "32.0gb free" in reason.lower()


def test_check_preflight_refuses_when_free_ram_too_low():
    with mock.patch.object(safety, "_collect_window", return_value=(
            _healthy_status(free_gb=1.5), _healthy_status(free_gb=1.5))):
        ok, reason = safety.check_preflight(min_free_gb=4.0, max_swapfiles=5)
    assert ok is False
    assert "insufficient free ram" in reason.lower()
    assert "1.5gb" in reason.lower()


def test_check_preflight_refuses_when_swapfiles_exceed_threshold():
    """The 2026-04-11 panic system had 35 swapfiles. Anything > 5 is unsafe."""
    with mock.patch.object(safety, "_collect_window", return_value=(
            _healthy_status(free_gb=16.0, swapfile_count=35),
            _healthy_status(free_gb=16.0, swapfile_count=35))):
        ok, reason = safety.check_preflight(min_free_gb=4.0, max_swapfiles=5)
    assert ok is False
    assert "swapfiles" in reason.lower()
    assert "35" in reason


def test_check_preflight_refuses_unsupported_platform():
    with mock.patch("platform.system", return_value="OpenBSD"):
        with mock.patch.object(safety, "_collect_window", return_value=None):
            ok, reason = safety.check_preflight()
    assert ok is False
    assert "refused" in reason.lower()
    assert "openbsd" in reason.lower()


def test_check_preflight_refuses_high_swap_utilization():
    high = _healthy_status(swap_used_mb=7600.0, swap_used_pct=92.8,
                           swap_headroom_mb=592.0)
    with mock.patch.object(safety, "_collect_window", return_value=(high, high)):
        ok, reason = safety.check_preflight()
    assert ok is False
    assert "swap utilization" in reason.lower()


def test_check_preflight_refuses_swapout_growth_over_window():
    first = _healthy_status(swapouts=100)
    second = _healthy_status(swapouts=500)
    with mock.patch.object(safety, "_collect_window", return_value=(first, second)):
        ok, reason = safety.check_preflight()
    assert ok is False
    assert "swapout" in reason.lower()


def test_check_preflight_refuses_compressor_pool_growth_over_window():
    first = _healthy_status(compressor_segments=1000)
    second = _healthy_status(compressor_segments=1400)
    with mock.patch.object(safety, "_collect_window", return_value=(first, second)):
        ok, reason = safety.check_preflight()
    assert ok is False
    assert "compressor pool growth" in reason.lower()


def test_check_preflight_refuses_missing_composite_field():
    broken = _healthy_status()
    del broken["compressor_pool_used_pct"]
    with mock.patch.object(safety, "_collect_window", return_value=(broken, broken)):
        ok, reason = safety.check_preflight()
    assert ok is False
    assert "missing" in reason.lower()


def test_output_capacity_refuses_symlink_and_low_space(tmp_path, monkeypatch):
    target = tmp_path / "target"
    target.mkdir()
    link = tmp_path / "link"
    link.symlink_to(target, target_is_directory=True)
    ok, reason = safety.check_output_capacity(str(link), 1024)
    assert ok is False and "symlink" in reason

    fake = mock.Mock(f_bavail=1, f_frsize=512)
    monkeypatch.setattr(safety.os, "statvfs", lambda path: fake)
    ok, reason = safety.check_output_capacity(str(target), 1024)
    assert ok is False and "free" in reason


def test_output_capacity_requires_a_conclusive_quota_probe(tmp_path, monkeypatch):
    target = tmp_path / "target"
    target.mkdir()
    fake = mock.Mock(f_bavail=10_000, f_frsize=4096)
    monkeypatch.setattr(safety.os, "statvfs", lambda path: fake)
    monkeypatch.setattr(safety, "_run_probe", lambda argv: "Disk quotas: none\n")
    ok, reason = safety.check_output_capacity(str(target), 1024)
    assert ok is True and "quota=none" in reason

    def fail_quota(argv):
        raise safety.ProbeError("quota unavailable")

    monkeypatch.setattr(safety, "_run_probe", fail_quota)
    ok, reason = safety.check_output_capacity(str(target), 1024)
    assert ok is False and "quota probe failed" in reason


def test_preflight_timeout_is_a_refusal():
    with mock.patch.object(
        safety, "_collect_window",
        side_effect=__import__("subprocess").TimeoutExpired(["vm_stat"], 5),
    ):
        ok, reason = safety.check_preflight()
    assert ok is False and "fail-closed" in reason


def test_darwin_pressure_status_parses_vm_stat_output():
    """Verify the vm_stat parser extracts free pages correctly."""
    fake_vm_stat = (
        "Mach Virtual Memory Statistics: (page size of 16384 bytes)\n"
        '"Pages free":                              524288.\n'
        '"Pages active":                            1048576.\n'
        '"Pages inactive":                          262144.\n'
        '"Pages speculative":                       65536.\n'
        '"Pages occupied by compressor":             65536.\n'
        '"Swapins":                                  100.\n'
        '"Swapouts":                                 200.\n'
    )
    fake_swapusage = "total = 2048.00M  used = 423.50M  free = 1624.50M  (encrypted)\n"
    fake_segments = (
        "vm.compressor.segment.total: 100\n"
        "vm.compressor.segment.limit: 1000\n"
    )

    def _fake_check_output(cmd, **kwargs):
        if cmd[0] == "vm_stat":
            return fake_vm_stat
        if cmd[:2] == ["sysctl", "-n"]:
            return fake_swapusage
        if cmd[:2] == ["sysctl", "vm.compressor.segment"]:
            return fake_segments
        if cmd[0] == "memory_pressure":
            return "System-wide memory free percentage: 70%\n"
        if cmd[0] == "ls":
            return "swapfile0\nswapfile1\nswapfile2\n"
        raise FileNotFoundError(cmd)

    class _FakeStatvfs:
        f_bavail = (40 * 1024 ** 3) // 4096  # 40 GiB free on the VM volume
        f_frsize = 4096

    with mock.patch.object(safety, "_run_probe", side_effect=_fake_check_output), \
            mock.patch.object(safety.os, "statvfs", return_value=_FakeStatvfs()):
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


def test_acquire_pipeline_lock_refuses_symlink_path(tmp_path):
    target = tmp_path / "target.lock"
    target.write_text("caller")
    alias = tmp_path / "alias.lock"
    alias.symlink_to(target)
    with pytest.raises(ValueError, match="symlink"):
        safety.acquire_pipeline_lock(str(alias), wait=False)
    assert target.read_text() == "caller"
