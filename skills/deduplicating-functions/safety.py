"""Cross-cutting safety primitives for run_pipeline.py.

Hosts pure-I/O helpers that protect the pipeline from:
  - Concurrent runs overwhelming shared system resources (flock)
  - Launching on an already-unhealthy system (preflight memory probe)

Both are intentionally unit-testable without running the full pipeline.
See the 2026-04-11 VM-compressor panic incident for context.
"""
from __future__ import annotations

import fcntl  # used only by acquire_pipeline_lock
import os
import platform
import re
import subprocess

# ── Constants ────────────────────────────────────────────────────────

DEFAULT_LOCK_PATH = os.path.expanduser("~/.cache/sdlc-os/run_pipeline.lock")

# Preflight thresholds chosen so the 2026-04-11 panic state (0GB free,
# 35 swapfiles) would have been refused before any detector launched.
DEFAULT_MIN_FREE_RAM_GB = 4.0
DEFAULT_MAX_SWAPFILES = 5


# ── Preflight memory probes ─────────────────────────────────────────

def darwin_pressure_status() -> dict:
    """Return memory status on macOS."""
    out = subprocess.check_output(["vm_stat"], text=True)
    page_size = 4096
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

    free_pages = pages.get("Pages free", 0) + pages.get("Pages inactive", 0)
    free_gb = free_pages * page_size / (1024 ** 3)

    # vm.swapusage looks like: "total = 2048.00M  used = 423.50M  free = 1624.50M"
    swap_used_mb = 0.0
    try:
        swap_out = subprocess.check_output(
            ["sysctl", "-n", "vm.swapusage"], text=True
        )
        m = re.search(r"used\s*=\s*([\d.]+)([MG])", swap_out)
        if m:
            val = float(m.group(1))
            if m.group(2) == "G":
                val *= 1024
            swap_used_mb = val
    except (subprocess.CalledProcessError, FileNotFoundError, PermissionError):
        pass

    swapfile_count = 0
    try:
        ls_out = subprocess.check_output(
            ["ls", "/private/var/vm/"], text=True, stderr=subprocess.DEVNULL
        )
        swapfile_count = sum(
            1 for name in ls_out.splitlines() if name.startswith("swapfile")
        )
    except (subprocess.CalledProcessError, FileNotFoundError, PermissionError):
        pass

    return {
        "free_gb": free_gb,
        "swap_used_mb": swap_used_mb,
        "swapfile_count": swapfile_count,
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
    except FileNotFoundError:
        pass

    return {
        "free_gb": free_gb,
        "swap_used_mb": swap_used_mb,
        "swapfile_count": swapfile_count,
    }


def _collect_status() -> dict | None:
    """Dispatch to the platform-specific collector. Returns None if unsupported."""
    system = platform.system()
    if system == "Darwin":
        return darwin_pressure_status()
    if system == "Linux":
        return linux_pressure_status()
    return None


def check_preflight(
    min_free_gb: float = DEFAULT_MIN_FREE_RAM_GB,
    max_swapfiles: int = DEFAULT_MAX_SWAPFILES,
) -> tuple[bool, str]:
    """Check if it is safe to launch the detector pipeline.

    Returns (ok, reason). On unsupported platforms, returns
    (True, "skipped: <platform>") so the runner does not block.
    On any probe error, returns (True, "skipped: <reason>") — fail-open.
    """
    # NB: the reason strings below are part of an implicit contract with
    # the test suite (test_safety.py asserts substrings like "insufficient
    # free ram", "swapfiles", "bypassed via --ignore-preflight", and
    # "<N.N>gb free"). If you change the format, update the tests.
    try:
        status = _collect_status()
    except (subprocess.CalledProcessError, FileNotFoundError, OSError, ValueError) as e:
        return True, f"skipped: probe failed ({e})"

    if status is None:
        return True, f"skipped: unsupported platform {platform.system()}"

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
    return True, (
        f"ok: {status['free_gb']:.1f}GB free, "
        f"{status['swapfile_count']} swapfiles, "
        f"{status['swap_used_mb']:.0f}MB swap used"
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
    # Handle bare filenames like "pipeline.lock" where dirname is empty
    parent = os.path.dirname(lock_path) or "."
    os.makedirs(parent, exist_ok=True)
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o644)
    try:
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
