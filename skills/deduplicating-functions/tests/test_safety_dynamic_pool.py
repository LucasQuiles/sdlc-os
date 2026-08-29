"""Dynamic-swap-pool preflight semantics (2026-08-28 D6 admission refusal).

macOS sizes its swap pool on demand (~1 GiB steps), so used/total utilization
hovers near 90% at ANY absolute usage: 7.4 GiB used of an auto-grown 8 GiB
pool refused at 90.02% while the incident-derived absolute gate (12,288 MiB)
had almost 5 GiB of headroom left. safety.py's own constants comment says
"swap BYTES are the effective gate" on modern macOS; these tests pin the
contract that makes the code agree with it:

  - collectors report ``swap_pool_dynamic`` and ``swap_growth_headroom_mb``;
  - on a DYNAMIC pool the pct axis defers to the absolute-bytes gate, and the
    headroom gate evaluates pool headroom + growth credit, with the credit
    CAPPED at the absolute line so the incident gate stays binding;
  - on a STATIC pool (Linux) every axis behaves exactly as before;
  - the new fields are part of the fail-closed required composite set.
"""
from __future__ import annotations

import os
import sys
from unittest import mock

import pytest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
import safety  # noqa: E402
sys.path.pop(0)


def _dynamic_status(**overrides):
    """A healthy Darwin-shaped composite sample (dynamic swap pool)."""
    status = {
        "free_gb": 32.0,
        "swap_used_mb": 1024.0,
        "swap_total_mb": 8192.0,
        "swap_used_pct": 12.5,
        "swap_headroom_mb": 7168.0,
        "swap_pool_dynamic": True,
        "swap_growth_headroom_mb": 70000.0,
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


def _window(status):
    return mock.patch.object(
        safety, "_collect_window", return_value=(status, dict(status)))


# ── The window-2 regression: high pct on a growable pool must pass ──

def test_dynamic_pool_high_utilization_with_growth_capacity_passes():
    """Exact 2026-08-28 refusal shape: 7374.62/8192 MiB = 90.02% dynamic."""
    status = _dynamic_status(
        swap_used_mb=7374.62, swap_total_mb=8192.0,
        swap_used_pct=90.02, swap_headroom_mb=817.38)
    with _window(status):
        ok, reason = safety.check_preflight()
    assert ok is True, f"dynamic pool at 90% with growth room must pass: {reason}"
    assert "swap_pool=dynamic" in reason


def test_dynamic_pool_absolute_line_still_binds():
    """The 2026-08-22 incident gate (absolute bytes) is unaffected."""
    status = _dynamic_status(
        swap_used_mb=12289.0, swap_total_mb=16384.0,
        swap_used_pct=75.0, swap_headroom_mb=4095.0)
    with _window(status):
        ok, reason = safety.check_preflight()
    assert ok is False
    assert "swap already heavily used" in reason


def test_dynamic_pool_growth_credit_capped_at_absolute_line():
    """Growth credit never extends past the absolute gate: a pool that could
    only grow BEYOND 12,288 MiB used gets no credit for that headroom."""
    status = _dynamic_status(
        swap_used_mb=12000.0, swap_total_mb=12200.0,
        swap_used_pct=98.4, swap_headroom_mb=200.0,
        swap_growth_headroom_mb=70000.0)
    with _window(status):
        ok, reason = safety.check_preflight()
    assert ok is False
    assert "effective headroom" in reason
    assert "capped" in reason


def test_dynamic_pool_no_growth_capacity_uses_raw_headroom():
    """With no disk room to grow the pool, only real pool headroom counts."""
    status = _dynamic_status(
        swap_used_mb=7600.0, swap_total_mb=8192.0,
        swap_used_pct=92.8, swap_headroom_mb=592.0,
        swap_growth_headroom_mb=0.0)
    with _window(status):
        ok, reason = safety.check_preflight()
    assert ok is False
    assert "effective headroom" in reason
    assert "592" in reason


# ── Static pools keep the original strict semantics ─────────────────

def test_static_pool_high_utilization_still_refused():
    status = _dynamic_status(
        swap_pool_dynamic=False, swap_growth_headroom_mb=0.0,
        swap_used_mb=7600.0, swap_used_pct=92.8, swap_headroom_mb=592.0)
    with _window(status):
        ok, reason = safety.check_preflight()
    assert ok is False
    assert "swap utilization" in reason


# ── Fail-closed on the new fields ───────────────────────────────────

def test_missing_pool_dynamic_field_refuses():
    status = _dynamic_status()
    del status["swap_pool_dynamic"]
    with _window(status):
        ok, reason = safety.check_preflight()
    assert ok is False
    assert "missing" in reason.lower()


def test_missing_growth_field_refuses():
    status = _dynamic_status()
    del status["swap_growth_headroom_mb"]
    with _window(status):
        ok, reason = safety.check_preflight()
    assert ok is False
    assert "missing" in reason.lower()


def test_negative_growth_headroom_refuses():
    status = _dynamic_status(swap_growth_headroom_mb=-1.0)
    with _window(status):
        ok, reason = safety.check_preflight()
    assert ok is False
    assert "invalid swap growth headroom" in reason


def test_nan_growth_headroom_refuses():
    """NaN compares False against every bound, so an explicit guard must
    catch it before it poisons the effective-headroom comparison into a
    silent pass."""
    status = _dynamic_status(swap_growth_headroom_mb=float("nan"),
                             swap_used_mb=7600.0, swap_used_pct=92.8,
                             swap_headroom_mb=592.0)
    with _window(status):
        ok, reason = safety.check_preflight()
    assert ok is False
    assert "invalid swap growth headroom" in reason


# ── Collector contract ──────────────────────────────────────────────

_FAKE_VM_STAT = (
    "Mach Virtual Memory Statistics: (page size of 16384 bytes)\n"
    '"Pages free":                              524288.\n'
    '"Pages active":                            1048576.\n'
    '"Pages inactive":                          262144.\n'
    '"Pages occupied by compressor":             65536.\n'
    '"Swapins":                                  100.\n'
    '"Swapouts":                                 200.\n'
)


def _fake_probe(cmd, **kwargs):
    if cmd[0] == "vm_stat":
        return _FAKE_VM_STAT
    if cmd[:2] == ["sysctl", "-n"]:
        return "total = 2048.00M  used = 423.50M  free = 1624.50M  (encrypted)\n"
    if cmd[:2] == ["sysctl", "vm.compressor.segment"]:
        return "vm.compressor.segment.total: 100\nvm.compressor.segment.limit: 1000\n"
    if cmd[0] == "memory_pressure":
        return "System-wide memory free percentage: 70%\n"
    if cmd[0] == "ls":
        return "swapfile0\n"
    raise FileNotFoundError(cmd)


class _FakeStatvfs:
    def __init__(self, free_bytes):
        self.f_bavail = free_bytes // 4096
        self.f_frsize = 4096


def test_darwin_collector_reports_dynamic_pool_fields():
    free_bytes = 80 * 1024 ** 3  # 80 GiB free on the VM volume
    with mock.patch.object(safety, "_run_probe", side_effect=_fake_probe), \
            mock.patch.object(safety.os, "statvfs",
                              return_value=_FakeStatvfs(free_bytes)):
        status = safety.darwin_pressure_status()
    assert status["swap_pool_dynamic"] is True
    expected = 80 * 1024.0 - safety.DEFAULT_SWAP_GROWTH_DISK_RESERVE_MB
    assert status["swap_growth_headroom_mb"] == pytest.approx(expected)


def test_darwin_collector_growth_floor_is_zero_below_reserve():
    with mock.patch.object(safety, "_run_probe", side_effect=_fake_probe), \
            mock.patch.object(safety.os, "statvfs",
                              return_value=_FakeStatvfs(1 * 1024 ** 3)):
        status = safety.darwin_pressure_status()
    assert status["swap_growth_headroom_mb"] == 0.0


def test_darwin_collector_statvfs_failure_is_probe_error():
    with mock.patch.object(safety, "_run_probe", side_effect=_fake_probe), \
            mock.patch.object(safety.os, "statvfs",
                              side_effect=OSError("nope")):
        with pytest.raises(safety.ProbeError):
            safety.darwin_pressure_status()
