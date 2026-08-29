"""Cross-cutting safety primitives for run_pipeline.py.

Hosts pure-I/O helpers that protect the pipeline from:
  - Concurrent runs overwhelming shared system resources (flock)
  - Launching on an already-unhealthy system (preflight memory probe)

Both are intentionally unit-testable without running the full pipeline.
See the 2026-04-11 VM-compressor panic incident for context.
"""
from __future__ import annotations

import fcntl  # used only by acquire_pipeline_lock
import math
import os
import platform
import re
import stat
import subprocess
import time

# ── Constants ────────────────────────────────────────────────────────

DEFAULT_LOCK_PATH = os.path.expanduser("~/.cache/sdlc-os/run_pipeline.lock")

# Preflight thresholds chosen so the 2026-04-11 panic state (0GB free,
# 35 swapfiles) would have been refused before any detector launched.
DEFAULT_MIN_FREE_RAM_GB = 4.0
DEFAULT_MAX_SWAPFILES = 5
# 2026-08-22 incident: the pipeline launched with 12.67 GB swap already used
# (645 MB headroom) and drove the box to a 2h18m crisis. NOTE (2026-08-29
# review): the swapfile-count probe reads /private/var/vm, which on modern
# macOS is an empty stub directory — live swapfiles sit at the path named by
# `sysctl vm.swapfileprefix` (e.g. /System/Volumes/VM/swapfile). The count
# axis is therefore inert on macOS because of the PATH, not OS behavior, and
# swap BYTES are the effective gate today. Deriving the probe directory from
# vm.swapfileprefix is a registered follow-up: it must come with a threshold
# recalibration (modern pools legitimately hold ~1 swapfile per GiB, so the
# 2026-04-11-era max of 5 would false-refuse healthy hosts).
DEFAULT_MAX_SWAP_USED_MB = 12288.0
# The pct/headroom axes below are meaningful only for a STATICALLY sized swap
# pool (Linux partition/swapfile). macOS sizes its pool on demand in ~1 GiB
# steps, so used/total hovers near 90% at ANY absolute usage — on 2026-08-28
# an admission was refused at 90.02% (7374.62 MiB used of an auto-grown
# 8192 MiB pool) while the absolute gate above still had ~5 GiB of headroom.
# On a dynamic pool the pct axis therefore defers to the absolute-bytes gate,
# and the headroom axis counts pool headroom PLUS disk-backed growth capacity,
# with the growth credit capped at the absolute line so the incident gate
# stays binding.
DEFAULT_MAX_SWAP_USED_PCT = 90.0
DEFAULT_MIN_SWAP_HEADROOM_MB = 768.0
# Disk kept out of the growth-credit calculation: the pool must never be
# allowed to grow into the last 10 GiB of the VM volume (the 2026-04-11
# panic box had 0 GB free). Mirrors DEFAULT_MIN_OUTPUT_FREE_BYTES.
DEFAULT_SWAP_GROWTH_DISK_RESERVE_MB = 10 * 1024.0
DEFAULT_MAX_SWAPOUT_DELTA = 256
DEFAULT_MAX_COMPRESSOR_OCCUPIED_MB = 24 * 1024.0
DEFAULT_MAX_COMPRESSOR_POOL_USED_PCT = 80.0
DEFAULT_MAX_COMPRESSOR_SEGMENT_GROWTH = 256
DEFAULT_MIN_MEMORY_PRESSURE_FREE_PCT = 20.0
PREFLIGHT_POLICY_VERSION = "dedup-composite-admission-v2"
PREFLIGHT_WINDOW_SECONDS = 1.0
DEFAULT_MIN_OUTPUT_FREE_BYTES = 10 * 1024 ** 3


class ProbeError(RuntimeError):
    """A required admission value was unavailable or malformed."""


def check_output_capacity(path: str, min_free_bytes: int = DEFAULT_MIN_OUTPUT_FREE_BYTES) -> tuple[bool, str]:
    """Fail closed on unsafe output roots or insufficient filesystem capacity."""
    if min_free_bytes <= 0:
        return False, "refused: output free-space threshold is invalid"
    target = os.path.abspath(path)
    if os.path.islink(target):
        return False, "refused: output root is a symlink"
    probe = target
    while not os.path.exists(probe):
        parent = os.path.dirname(probe)
        if parent == probe:
            return False, "refused: no existing output-root ancestor"
        probe = parent
    try:
        stats = os.statvfs(probe)
    except OSError as exc:
        return False, f"refused: output filesystem probe failed ({exc})"
    available = stats.f_bavail * stats.f_frsize
    if available < min_free_bytes:
        return False, (
            f"refused: output filesystem has {available} bytes free < "
            f"{min_free_bytes} required")
    try:
        quota = _run_probe(["quota", "-v"]).strip()
    except (ProbeError, subprocess.TimeoutExpired, OSError, ValueError) as exc:
        return False, f"refused: output quota probe failed ({exc})"
    if not re.search(r"\bnone\b", quota, re.IGNORECASE):
        return False, (
            "refused: an output filesystem quota is configured but bounded "
            "quota-headroom parsing is unavailable")
    return True, (
        f"ok: output filesystem free_bytes={available} required_bytes={min_free_bytes}; "
        "quota=none")


def _run_probe(argv: list[str], timeout: float = 5.0) -> str:
    result = subprocess.run(
        argv, capture_output=True, text=True, timeout=timeout, check=False)
    if result.returncode != 0:
        raise ProbeError(f"{argv[0]} exited {result.returncode}")
    return result.stdout


def _number(text: str, pattern: str, name: str) -> float:
    match = re.search(pattern, text, re.MULTILINE)
    if not match:
        raise ProbeError(f"missing {name}")
    try:
        value = float(match.group(1))
    except ValueError as exc:
        raise ProbeError(f"malformed {name}") from exc
    if value < 0:
        raise ProbeError(f"negative {name}")
    return value


def _unit_mb(value: float, unit: str) -> float:
    if unit == "G":
        return value * 1024.0
    if unit == "K":
        return value / 1024.0
    return value


# ── Preflight memory probes ─────────────────────────────────────────

def darwin_pressure_status() -> dict:
    """Return one complete macOS admission sample or raise ``ProbeError``."""
    out = _run_probe(["vm_stat"])
    page_size = int(_number(out, r"page size of (\d+)", "page size"))
    pages: dict[str, int] = {}
    for line in out.splitlines():
        m = re.search(r"page size of (\d+)", line)
        if m:
            page_size = int(m.group(1))
            continue
        # Lines look like:  "Pages free":                              524288.
        m = re.match(r'^"?([^":]+?)"?:\s+(\d+)\.?', line.strip())
        if m:
            pages[m.group(1).strip()] = int(m.group(2))

    required_pages = ("Pages free", "Pages inactive", "Pages occupied by compressor",
                      "Swapins", "Swapouts")
    missing_pages = [name for name in required_pages if name not in pages]
    if missing_pages:
        raise ProbeError(f"missing vm_stat field(s): {', '.join(missing_pages)}")
    free_pages = pages["Pages free"] + pages["Pages inactive"]
    free_gb = free_pages * page_size / (1024 ** 3)

    swap_out = _run_probe(["sysctl", "-n", "vm.swapusage"])
    total_match = re.search(r"total\s*=\s*([\d.]+)([KMG])", swap_out)
    used_match = re.search(r"used\s*=\s*([\d.]+)([KMG])", swap_out)
    if not total_match or not used_match:
        raise ProbeError("missing vm.swapusage total/used")
    swap_total_mb = _unit_mb(float(total_match.group(1)), total_match.group(2))
    swap_used_mb = _unit_mb(float(used_match.group(1)), used_match.group(2))
    if swap_total_mb <= 0 or swap_used_mb > swap_total_mb:
        raise ProbeError("invalid vm.swapusage totals")

    segments = _run_probe(["sysctl", "vm.compressor.segment"])
    segment_total = _number(
        segments, r"^vm\.compressor\.segment\.total:\s*(\d+)\s*$", "segment total")
    segment_limit = _number(
        segments, r"^vm\.compressor\.segment\.limit:\s*(\d+)\s*$", "segment limit")
    if segment_limit <= 0 or segment_total > segment_limit:
        raise ProbeError("invalid compressor segment totals")

    pressure = _run_probe(["memory_pressure"])
    pressure_free_pct = _number(
        pressure, r"System-wide memory free percentage:\s*([\d.]+)%", "memory pressure")
    if pressure_free_pct > 100:
        raise ProbeError("memory pressure percentage out of range")

    ls_out = _run_probe(["ls", "/private/var/vm/"])
    swapfile_count = sum(
        1 for name in ls_out.splitlines() if name.startswith("swapfile")
    )

    # macOS grows the swap pool on demand; report how far it could still
    # grow (free space on the VM volume minus a hard disk reserve) so the
    # preflight can judge headroom on the pool the OS WILL provide, not
    # just the pool it has provided so far.
    try:
        vm_fs = os.statvfs("/private/var/vm")
    except OSError as exc:
        raise ProbeError("unable to statvfs /private/var/vm") from exc
    vm_free_mb = vm_fs.f_bavail * vm_fs.f_frsize / (1024 ** 2)
    growth_headroom_mb = max(0.0, vm_free_mb - DEFAULT_SWAP_GROWTH_DISK_RESERVE_MB)

    return {
        "free_gb": free_gb,
        "swap_total_mb": swap_total_mb,
        "swap_used_mb": swap_used_mb,
        "swap_used_pct": 100.0 * swap_used_mb / swap_total_mb,
        "swap_headroom_mb": swap_total_mb - swap_used_mb,
        "swap_pool_dynamic": True,
        "swap_growth_headroom_mb": growth_headroom_mb,
        "swapfile_count": swapfile_count,
        "swapins": pages["Swapins"],
        "swapouts": pages["Swapouts"],
        "compressor_occupied_mb": pages["Pages occupied by compressor"] * page_size / (1024 ** 2),
        "compressor_segments": segment_total,
        "compressor_segment_limit": segment_limit,
        "compressor_pool_used_pct": 100.0 * segment_total / segment_limit,
        "memory_pressure": "normal" if pressure_free_pct >= DEFAULT_MIN_MEMORY_PRESSURE_FREE_PCT else "critical",
        "memory_pressure_free_pct": pressure_free_pct,
    }


def linux_pressure_status() -> dict:
    """Return memory status on Linux via /proc/meminfo and /proc/swaps.

    Prefers MemAvailable (kernel >= 3.14, 2014) as it accounts for
    reclaimable cache. Falls back to MemFree on older kernels, which
    under-reports usable memory and may cause preflight to refuse launch
    on a system that actually has enough headroom — acceptable given
    the age threshold.
    """
    info: dict[str, int] = {}
    with open("/proc/meminfo") as f:
        for line in f:
            parts = line.split()
            if len(parts) >= 2 and parts[1].isdigit():
                info[parts[0].rstrip(":")] = int(parts[1])  # kB

    free_kb = info.get("MemAvailable", info.get("MemFree", 0))
    free_gb = free_kb / (1024 ** 2)

    swap_used_kb = info.get("SwapTotal", 0) - info.get("SwapFree", 0)
    swap_used_mb = swap_used_kb / 1024

    swapfile_count = 0
    try:
        with open("/proc/swaps") as f:
            lines = f.readlines()
            # First line is the header
            swapfile_count = max(0, len(lines) - 1)
    except OSError as exc:
        raise ProbeError("unable to read /proc/swaps") from exc

    if "MemTotal" not in info or "SwapTotal" not in info or "SwapFree" not in info:
        raise ProbeError("missing required /proc/meminfo fields")
    vmstat: dict[str, int] = {}
    with open("/proc/vmstat") as stream:
        for line in stream:
            parts = line.split()
            if len(parts) == 2 and parts[1].isdigit():
                vmstat[parts[0]] = int(parts[1])
    if "pswpin" not in vmstat or "pswpout" not in vmstat:
        raise ProbeError("missing required /proc/vmstat swap counters")
    total_mb = info["SwapTotal"] / 1024
    used_pct = 0.0 if total_mb == 0 else 100.0 * swap_used_mb / total_mb
    return {
        "free_gb": free_gb,
        "swap_total_mb": total_mb,
        "swap_used_mb": swap_used_mb,
        "swap_used_pct": used_pct,
        "swap_headroom_mb": total_mb - swap_used_mb,
        # Linux swap capacity is fixed at configuration time; the static
        # pct/headroom axes apply as-is and there is no growth credit.
        "swap_pool_dynamic": False,
        "swap_growth_headroom_mb": 0.0,
        "swapfile_count": swapfile_count,
        "swapins": vmstat["pswpin"],
        "swapouts": vmstat["pswpout"],
        # Linux has no Darwin compressor pool.  This platform decision treats
        # the axis as not applicable while retaining swap and MemAvailable.
        "compressor_occupied_mb": 0.0,
        "compressor_segments": 0.0,
        "compressor_segment_limit": 0.0,
        "compressor_pool_used_pct": 0.0,
        "memory_pressure": "normal",
    }


def _collect_status() -> dict | None:
    """Dispatch to the platform-specific collector. Returns None if unsupported."""
    system = platform.system()
    if system == "Darwin":
        return darwin_pressure_status()
    if system == "Linux":
        return linux_pressure_status()
    return None


def _collect_window() -> tuple[dict, dict] | None:
    first = _collect_status()
    if first is None:
        return None
    time.sleep(PREFLIGHT_WINDOW_SECONDS)
    second = _collect_status()
    if second is None:
        return None
    return first, second


def check_preflight(
    min_free_gb: float = DEFAULT_MIN_FREE_RAM_GB,
    max_swapfiles: int = DEFAULT_MAX_SWAPFILES,
    max_swap_used_mb: float = DEFAULT_MAX_SWAP_USED_MB,
) -> tuple[bool, str]:
    """Evaluate a two-sample composite resource window, failing closed."""
    # NB: reason strings below are asserted by test_safety.py.
    try:
        window = _collect_window()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired,
            FileNotFoundError, OSError, ValueError, ProbeError) as e:
        return False, (
            f"refused: probe failed ({e}); cannot verify memory pressure — "
            "fail-closed."
        )

    if window is None:
        return False, f"refused: unsupported platform {platform.system()}"
    first, status = window
    required = {
        "free_gb", "swap_used_mb", "swap_total_mb", "swap_used_pct",
        "swap_headroom_mb", "swap_pool_dynamic", "swap_growth_headroom_mb",
        "swapfile_count", "swapins", "swapouts",
        "compressor_occupied_mb", "compressor_pool_used_pct", "memory_pressure",
        "compressor_segments", "compressor_segment_limit",
    }
    missing = sorted(required - set(first) | required - set(status))
    if missing:
        return False, f"refused: missing composite field(s): {', '.join(missing)}"

    if status["free_gb"] < min_free_gb:
        return False, (
            f"insufficient free RAM: {status['free_gb']:.1f}GB "
            f"< {min_free_gb}GB threshold"
        )
    if status["swapfile_count"] > max_swapfiles:
        return False, (
            f"too many swapfiles: {status['swapfile_count']} "
            f"> {max_swapfiles} threshold "
            f"(system already under heavy memory pressure)"
        )
    if status["swap_used_mb"] > max_swap_used_mb:
        return False, (
            f"swap already heavily used: {status['swap_used_mb']:.0f}MB "
            f"> {max_swap_used_mb:.0f}MB threshold (the 2026-08-22 incident "
            "launched at 12.67GB swap used; refusing to add multi-GB detector "
            "load to a box already deep in swap)"
        )
    pool_dynamic = status["swap_pool_dynamic"]
    if not isinstance(pool_dynamic, bool):
        # The branch selector decides which swap axes apply; a truthy
        # non-bool must not fail OPEN into the more permissive branch.
        return False, (
            f"refused: invalid swap pool dynamic flag ({pool_dynamic!r})")
    if pool_dynamic:
        # A dynamically sized pool (macOS): utilization of the CURRENT
        # allocation is pool-sizing behavior, not memory pressure — the
        # absolute-bytes gate above owns that axis. Headroom counts the
        # pool the OS can still provide, credited only up to the absolute
        # line so the incident gate stays binding.
        growth_mb = status["swap_growth_headroom_mb"]
        if not isinstance(growth_mb, (int, float)) or isinstance(growth_mb, bool) \
                or math.isnan(growth_mb) or growth_mb < 0:
            return False, (
                f"refused: invalid swap growth headroom ({growth_mb!r})")
        head_mb = status["swap_headroom_mb"]
        if not isinstance(head_mb, (int, float)) or isinstance(head_mb, bool) \
                or math.isnan(head_mb) or head_mb < 0:
            # NaN in either operand of headroom + credit poisons the
            # comparison below into a silent pass; negative means the
            # collector's used<=total invariant was violated upstream.
            return False, f"refused: invalid swap headroom ({head_mb!r})"
        growth_credit = min(
            float(growth_mb),
            max(0.0, max_swap_used_mb - status["swap_used_mb"]))
        effective_headroom = head_mb + growth_credit
        if effective_headroom < DEFAULT_MIN_SWAP_HEADROOM_MB:
            return False, (
                f"swap effective headroom {effective_headroom:.0f}MB "
                f"(pool {status['swap_headroom_mb']:.0f}MB + growth credit "
                f"{growth_credit:.0f}MB, capped at the {max_swap_used_mb:.0f}MB "
                f"absolute line) < {DEFAULT_MIN_SWAP_HEADROOM_MB:.0f}MB threshold")
    else:
        if status["swap_used_pct"] >= DEFAULT_MAX_SWAP_USED_PCT:
            return False, (
                f"swap utilization {status['swap_used_pct']:.1f}% >= "
                f"{DEFAULT_MAX_SWAP_USED_PCT:.1f}% threshold")
        if status["swap_headroom_mb"] < DEFAULT_MIN_SWAP_HEADROOM_MB:
            return False, (
                f"swap headroom {status['swap_headroom_mb']:.0f}MB < "
                f"{DEFAULT_MIN_SWAP_HEADROOM_MB:.0f}MB threshold")
    swapout_delta = status["swapouts"] - first["swapouts"]
    if swapout_delta < 0:
        return False, "refused: swapout counter regressed"
    if swapout_delta > DEFAULT_MAX_SWAPOUT_DELTA:
        return False, (
            f"swapout growth {swapout_delta} pages > "
            f"{DEFAULT_MAX_SWAPOUT_DELTA} page window threshold")
    if status["compressor_occupied_mb"] > DEFAULT_MAX_COMPRESSOR_OCCUPIED_MB:
        return False, (
            f"compressor occupancy {status['compressor_occupied_mb']:.0f}MB > "
            f"{DEFAULT_MAX_COMPRESSOR_OCCUPIED_MB:.0f}MB threshold")
    if status["compressor_pool_used_pct"] >= DEFAULT_MAX_COMPRESSOR_POOL_USED_PCT:
        return False, (
            f"compressor pool utilization {status['compressor_pool_used_pct']:.1f}% >= "
            f"{DEFAULT_MAX_COMPRESSOR_POOL_USED_PCT:.1f}% threshold")
    compressor_growth = status["compressor_segments"] - first["compressor_segments"]
    if compressor_growth > DEFAULT_MAX_COMPRESSOR_SEGMENT_GROWTH:
        return False, (
            f"compressor pool growth {compressor_growth:.0f} segments > "
            f"{DEFAULT_MAX_COMPRESSOR_SEGMENT_GROWTH} segment window threshold")
    if status["memory_pressure"] != "normal":
        return False, f"memory pressure verdict is {status['memory_pressure']}"
    return True, (
        f"ok: policy={PREFLIGHT_POLICY_VERSION}, {status['free_gb']:.1f}GB free, "
        f"{status['swapfile_count']} swapfiles, "
        f"{status['swap_used_mb']:.0f}/{status['swap_total_mb']:.0f}MB swap "
        f"({status['swap_used_pct']:.1f}%), "
        f"swap_pool={'dynamic' if pool_dynamic else 'static'}, "
        f"swapout_delta={swapout_delta}, "
        f"compressor_pool={status['compressor_pool_used_pct']:.1f}%, "
        f"compressor_growth={compressor_growth:.0f}"
    )


# ── Cross-process lock ──────────────────────────────────────────────


def acquire_pipeline_lock(lock_path: str, wait: bool) -> int:
    """Acquire an exclusive flock on lock_path. Return the open file descriptor.

    The caller is responsible for keeping the fd open for the lifetime of
    the run; closing it (or process exit) releases the lock automatically.

    Raises BlockingIOError if wait=False and the lock is already held.
    Any other exception (e.g. OSError on an unsupported filesystem) is
    re-raised after closing the fd to avoid a descriptor leak.
    """
    lock_path = os.path.abspath(os.path.expanduser(lock_path))
    if os.path.realpath(lock_path) != lock_path:
        raise ValueError("pipeline lock path has a symlink ancestor")
    parent = os.path.dirname(lock_path) or "."
    os.makedirs(parent, exist_ok=True)
    open_flags = os.O_CREAT | os.O_RDWR
    if hasattr(os, "O_NOFOLLOW"):
        open_flags |= os.O_NOFOLLOW
    fd = os.open(lock_path, open_flags, 0o600)
    try:
        lock_stat = os.fstat(fd)
        if (not stat.S_ISREG(lock_stat.st_mode) or lock_stat.st_uid != os.getuid()
                or lock_stat.st_nlink != 1):
            raise ValueError("pipeline lock identity is unsafe")
        os.fchmod(fd, 0o600)
        flags = fcntl.LOCK_EX if wait else (fcntl.LOCK_EX | fcntl.LOCK_NB)
        fcntl.flock(fd, flags)
        # Record our pid for diagnostics. Best-effort — if this fails
        # we still hold the lock and should not leak it.
        os.ftruncate(fd, 0)
        os.write(fd, f"{os.getpid()}\n".encode())
    except BlockingIOError:
        os.close(fd)
        raise
    except Exception:
        # Any other failure: release the fd before propagating so we
        # don't leak on unsupported filesystems or partial writes.
        os.close(fd)
        raise
    return fd
