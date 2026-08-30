"""Register follow-ups R3/R4/NIT-3 (round9 events 39/42, remediation event 51).

R3 — the swapfile-count probe read /private/var/vm, an empty stub directory on
modern macOS: live swapfiles sit at the path named by `sysctl vm.swapfileprefix`
(observed on the review host: /System/Volumes/VM/swapfile, 11 files while the
probe counted 0). The collector now derives the probe directory and name prefix
from that sysctl, falling back to the legacy directory when the sysctl is
unavailable. Because a dynamic pool legitimately holds ~1 swapfile per GiB, the
count axis on dynamic pools becomes ORPHAN/SPRAWL detection relative to pool
size (count > ceil(total_GiB) + slack) instead of a fixed cap; static pools
keep the fixed-cap semantics unchanged.

R4 — a fresh-boot dynamic pool reports `vm.swapusage: total = 0.00M` and the
collector raised ProbeError ("invalid vm.swapusage totals"), refusing the
healthiest possible swap state. total==0 with used==0 is now a valid empty
dynamic pool (pct 0, headroom 0, growth still probed); genuinely invalid
shapes (negative values, used>total) still raise.

NIT-3 — the disk reserve constant is pinned so a silent change fails a test.
"""
from __future__ import annotations

import math
import os
import sys
from unittest import mock

import pytest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
import safety  # noqa: E402
sys.path.pop(0)


_FAKE_VM_STAT = (
    "Mach Virtual Memory Statistics: (page size of 16384 bytes)\n"
    '"Pages free":                              524288.\n'
    '"Pages active":                            1048576.\n'
    '"Pages inactive":                          262144.\n'
    '"Pages occupied by compressor":             65536.\n'
    '"Swapins":                                  100.\n'
    '"Swapouts":                                 200.\n'
)


def _probe_factory(swapusage, swapfileprefix, ls_by_dir):
    """Build a _run_probe fake with controllable sysctl/ls behavior."""
    def _fake(cmd, **kwargs):
        if cmd[0] == "vm_stat":
            return _FAKE_VM_STAT
        if cmd[:3] == ["sysctl", "-n", "vm.swapusage"]:
            return swapusage
        if cmd[:2] == ["sysctl", "-n"] and cmd[2:] == ["vm.swapfileprefix"]:
            if swapfileprefix is None:
                raise safety.ProbeError("sysctl exited 1")
            return swapfileprefix
        if cmd[:3] == ["sysctl", "-n", "vm.swapfileprefix"]:
            if swapfileprefix is None:
                raise safety.ProbeError("sysctl exited 1")
            return swapfileprefix
        if cmd[:2] == ["sysctl", "vm.compressor.segment"]:
            return "vm.compressor.segment.total: 100\nvm.compressor.segment.limit: 1000\n"
        if cmd[0] == "memory_pressure":
            return "System-wide memory free percentage: 70%\n"
        if cmd[0] == "ls":
            return ls_by_dir.get(cmd[1], "")
        raise FileNotFoundError(cmd)
    return _fake


class _FakeStatvfs:
    def __init__(self, free_bytes=80 * 1024 ** 3):
        self.f_bavail = free_bytes // 4096
        self.f_frsize = 4096


# ── R3: probe directory derived from vm.swapfileprefix ──────────────

def test_swapfile_count_uses_swapfileprefix_directory():
    ls = {
        "/System/Volumes/VM/": "swapfile0\nswapfile1\nswapfile2\n",
        "/private/var/vm/": "",
    }
    with mock.patch.object(safety, "_run_probe",
                           side_effect=_probe_factory(
                               "total = 2048.00M  used = 423.50M  free = 1624.50M  (encrypted)\n",
                               "/System/Volumes/VM/swapfile\n", ls)), \
            mock.patch.object(safety.os, "statvfs", return_value=_FakeStatvfs()):
        status = safety.darwin_pressure_status()
    assert status["swapfile_count"] == 3


def test_swapfile_count_falls_back_to_legacy_dir_without_sysctl():
    ls = {"/private/var/vm/": "swapfile0\nswapfile1\n"}
    with mock.patch.object(safety, "_run_probe",
                           side_effect=_probe_factory(
                               "total = 2048.00M  used = 423.50M  free = 1624.50M  (encrypted)\n",
                               None, ls)), \
            mock.patch.object(safety.os, "statvfs", return_value=_FakeStatvfs()):
        status = safety.darwin_pressure_status()
    assert status["swapfile_count"] == 2


def test_swapfile_count_matches_only_the_prefix_basename():
    ls = {"/System/Volumes/VM/": "swapfile0\nswapfile1\nnot-a-swapfile\n.DS_Store\n"}
    with mock.patch.object(safety, "_run_probe",
                           side_effect=_probe_factory(
                               "total = 2048.00M  used = 423.50M  free = 1624.50M  (encrypted)\n",
                               "/System/Volumes/VM/swapfile\n", ls)), \
            mock.patch.object(safety.os, "statvfs", return_value=_FakeStatvfs()):
        status = safety.darwin_pressure_status()
    assert status["swapfile_count"] == 2


# ── R3: pool-proportional sprawl semantics on dynamic pools ─────────

def _status(**overrides):
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


def test_dynamic_pool_healthy_swapfile_census_passes():
    """The live-host shape that a fixed cap of 5 would false-refuse:
    11 x 1 GiB files backing an 11 GiB pool."""
    status = _status(swapfile_count=11, swap_total_mb=11264.0,
                     swap_used_mb=10000.0, swap_used_pct=88.8,
                     swap_headroom_mb=1264.0)
    with _window(status):
        ok, reason = safety.check_preflight()
    assert ok is True, f"pool-proportional census must pass: {reason}"


def test_dynamic_pool_swapfile_sprawl_refuses():
    """Counts far beyond pool size mean orphaned files (2026-04-11 shape)."""
    status = _status(swapfile_count=35, swap_total_mb=8192.0)
    with _window(status):
        ok, reason = safety.check_preflight()
    assert ok is False
    assert "swapfile" in reason.lower()


def test_static_pool_swapfile_cap_unchanged():
    status = _status(swap_pool_dynamic=False, swap_growth_headroom_mb=0.0,
                     swapfile_count=35)
    with _window(status):
        ok, reason = safety.check_preflight()
    assert ok is False
    assert "35" in reason and "swapfiles" in reason


# ── mutant-killing pins for the sprawl FORMULA (review R3) ──────────
# The constant pin alone does not bind the formula: these shapes sit in the
# discriminating bands so dropping the slack term, dropping the ceil, or
# dropping the total validation each fails a named test.

def test_sprawl_slack_band_passes():
    """count inside (ceil, ceil+slack]: 13 files on an 11 GiB pool must pass
    (a mutant without the slack term would refuse at 11)."""
    status = _status(swapfile_count=13, swap_total_mb=11264.0,
                     swap_used_mb=10000.0, swap_used_pct=88.8,
                     swap_headroom_mb=1264.0)
    with _window(status):
        ok, reason = safety.check_preflight()
    assert ok is True, reason


def test_sprawl_fractional_total_uses_ceil():
    """total=11500MB: ceil gives 12+4=16 allowed; a mutant using raw division
    allows only 15.23 and refuses count=16."""
    status = _status(swapfile_count=16, swap_total_mb=11500.0,
                     swap_used_mb=10000.0, swap_used_pct=87.0,
                     swap_headroom_mb=1500.0)
    with _window(status):
        ok, reason = safety.check_preflight()
    assert ok is True, reason


def test_malformed_swap_total_refuses_not_crashes():
    """NaN total must refuse with the invalid-total reason on BOTH branch
    selectors — a mutant without the validation crashes at math.ceil
    (dynamic) or admits printing nan (static)."""
    for dyn in (True, False):
        status = _status(swap_pool_dynamic=dyn, swap_total_mb=float("nan"))
        with _window(status):
            ok, reason = safety.check_preflight()
        assert ok is False, f"dyn={dyn} must refuse"
        assert "invalid swap total" in reason, f"dyn={dyn}: {reason}"


# ── R4: empty dynamic pool is healthy, invalid shapes still raise ───

def test_zero_total_swap_pool_is_valid_on_darwin():
    ls = {"/System/Volumes/VM/": ""}
    with mock.patch.object(safety, "_run_probe",
                           side_effect=_probe_factory(
                               "total = 0.00M  used = 0.00M  free = 0.00M  (encrypted)\n",
                               "/System/Volumes/VM/swapfile\n", ls)), \
            mock.patch.object(safety.os, "statvfs", return_value=_FakeStatvfs()):
        status = safety.darwin_pressure_status()
    assert status["swap_total_mb"] == 0.0
    assert status["swap_used_mb"] == 0.0
    assert status["swap_used_pct"] == 0.0
    assert status["swap_headroom_mb"] == 0.0
    assert status["swap_pool_dynamic"] is True


def test_zero_total_empty_pool_admits_via_growth():
    status = _status(swap_total_mb=0.0, swap_used_mb=0.0, swap_used_pct=0.0,
                     swap_headroom_mb=0.0, swapfile_count=0)
    with _window(status):
        ok, reason = safety.check_preflight()
    assert ok is True, f"fresh-boot empty pool must admit: {reason}"


def test_used_exceeding_total_still_raises():
    ls = {"/System/Volumes/VM/": ""}
    with mock.patch.object(safety, "_run_probe",
                           side_effect=_probe_factory(
                               "total = 1024.00M  used = 2048.00M  free = 0.00M  (encrypted)\n",
                               "/System/Volumes/VM/swapfile\n", ls)), \
            mock.patch.object(safety.os, "statvfs", return_value=_FakeStatvfs()):
        with pytest.raises(safety.ProbeError):
            safety.darwin_pressure_status()


# ── NIT-3: reserve constant pinned ──────────────────────────────────

def test_growth_disk_reserve_constant_pinned():
    assert safety.DEFAULT_SWAP_GROWTH_DISK_RESERVE_MB == 10 * 1024.0
    assert math.isfinite(safety.DEFAULT_SWAPFILE_ORPHAN_SLACK)
    assert safety.DEFAULT_SWAPFILE_ORPHAN_SLACK == 4
