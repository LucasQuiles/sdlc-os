"""Finite resource policy, process-tree watchdog, and run record for the
duplicate-detection pipeline.

Invariants (plan P1 §2.3):
  I1  A destructive action requires positive ownership: the watchdog signals a
      pid only if, at signal time, it is a descendant of the owning root pid
      (parent-chain walk over a fresh process table) — never by name or age.
  I3  Every ceiling is finite. Overrides may only move a ceiling to another
      finite positive value; there is no "unbounded" setting.
  I4  Missing measurements are reported as unavailable, never substituted:
      RSS is reported as ``rss_bytes``; Apple task footprint is a separate
      field that stays ``None``/``unavailable`` until a native helper exists.

Everything here is standard library only and safe to import from the
pipeline runner, the merger, and tests.
"""
from __future__ import annotations

import dataclasses
import datetime as _dt
import hashlib
import json
import os
import subprocess
import threading
import time
from typing import Any, Callable

try:  # same directory (scripts/lib) — sibling import works both as package and path import
    from . import jsonstream as _jsonstream  # type: ignore
except Exception:  # pragma: no cover - fallback when imported by path
    try:
        import jsonstream as _jsonstream  # type: ignore
    except Exception:  # pragma: no cover
        _jsonstream = None

__all__ = [
    "PolicyError",
    "ResourcePolicy",
    "TreeWatchdog",
    "RunRecord",
    "descendants_from_table",
    "tree_rss_bytes_from_table",
    "sample_tree",
    "EXIT_RESOURCE",
]

EXIT_RESOURCE = 3  # distinct from 1 (input/IO) and 2 (strict-phase failure)

MiB = 1 << 20
GiB = 1 << 30


class PolicyError(ValueError):
    """A non-finite or otherwise invalid resource ceiling."""


@dataclasses.dataclass(frozen=True)
class ResourcePolicy:
    """Finite ceilings for one pipeline run. All byte/row/second values are > 0."""

    max_input_bytes: int = 1 * GiB          # sum of detector output bytes fed to merge
    max_pairs: int = 200_000                # pairs emitted to pairs.jsonl
    max_report_rows: int = 500              # rows per report section
    max_output_bytes: int = 1 * GiB         # pairs.jsonl bytes
    max_wall_seconds: int = 1800            # whole pipeline
    max_tree_rss_bytes: int = 6 * GiB       # runner + all descendants, sampled RSS
    max_legacy_json_bytes: int = 200 * MiB  # merged-results.json compatibility export
    max_run_output_bytes: int = 3 * GiB     # all files in one immutable run directory
    max_tree_processes: int = 64            # runner plus all descendants
    mode: str = "refuse"                    # refuse | truncate

    _INT_FIELDS = (
        "max_input_bytes", "max_pairs", "max_report_rows", "max_output_bytes",
        "max_wall_seconds", "max_tree_rss_bytes", "max_legacy_json_bytes",
        "max_run_output_bytes",
        "max_tree_processes",
    )

    @classmethod
    def defaults(cls) -> "ResourcePolicy":
        return cls()

    def with_overrides(self, **overrides: Any) -> "ResourcePolicy":
        values = dataclasses.asdict(self)
        for key, val in overrides.items():
            if val is None:
                continue
            if key not in values:
                raise PolicyError(f"unknown resource policy field: {key}")
            if key == "mode":
                if val not in ("refuse", "truncate"):
                    raise PolicyError(f"mode must be 'refuse' or 'truncate', got {val!r}")
                values[key] = val
                continue
            if isinstance(val, bool) or not isinstance(val, int) or val <= 0:
                raise PolicyError(
                    f"{key} must be a finite positive integer (got {val!r}); "
                    "unbounded ceilings are not supported"
                )
            hard_cap = getattr(ResourcePolicy(), key)
            if val > hard_cap:
                raise PolicyError(
                    f"{key}={val} exceeds immutable hard cap {hard_cap}; "
                    "CLI and environment may only lower ceilings"
                )
            values[key] = val
        return ResourcePolicy(**values)

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


# ---------------------------------------------------------------------------
# Process-table helpers (pure functions over a {pid: (ppid, rss_kb)} table)
# ---------------------------------------------------------------------------

def _sample_table() -> dict[int, tuple[int, int]]:
    """Return {pid: (ppid, rss_kb)} for every process visible to ``ps``."""
    out = subprocess.run(
        ["ps", "-axo", "pid=,ppid=,rss="], capture_output=True, text=True, timeout=20,
    )
    if out.returncode != 0:
        raise PolicyError(f"process-table probe exited {out.returncode}")
    table: dict[int, tuple[int, int]] = {}
    malformed = 0
    for line in out.stdout.splitlines():
        parts = line.split()
        if len(parts) != 3:
            if line.strip():
                malformed += 1
            continue
        try:
            table[int(parts[0])] = (int(parts[1]), int(parts[2]))
        except ValueError:
            malformed += 1
    if malformed or not table:
        raise PolicyError(
            f"process-table probe incomplete: malformed={malformed}, rows={len(table)}")
    return table


def descendants_from_table(root: int, table: dict[int, tuple[int, int]]) -> list[int]:
    """All pids whose parent chain reaches ``root`` (root itself excluded), depth-first."""
    children: dict[int, list[int]] = {}
    for pid, (ppid, _) in table.items():
        children.setdefault(ppid, []).append(pid)
    result: list[int] = []
    stack = list(children.get(root, []))
    seen = {root}
    while stack:
        pid = stack.pop()
        if pid in seen:
            continue
        seen.add(pid)
        result.append(pid)
        stack.extend(children.get(pid, []))
    return result


def tree_rss_bytes_from_table(root: int, table: dict[int, tuple[int, int]]) -> int:
    total = table.get(root, (0, 0))[1]
    for pid in descendants_from_table(root, table):
        total += table[pid][1]
    return total * 1024


def sample_tree(root: int) -> dict[str, Any]:
    """One sample of the tree rooted at ``root``. RSS only; footprint unavailable."""
    table = _sample_table()
    desc = descendants_from_table(root, table)
    return {
        "sampled_utc": _utc_now(),
        "root_pid": root,
        "process_count": 1 + len(desc),
        "rss_bytes": tree_rss_bytes_from_table(root, table),
        "footprint_bytes": None,
        "footprint_status": "unavailable",
    }


def _output_tree_bytes(root: str) -> int:
    """Return allocated logical bytes without following links or hiding probe errors."""
    total = 0
    stack = [root]
    while stack:
        current = stack.pop()
        with os.scandir(current) as entries:
            for entry in entries:
                if entry.is_symlink():
                    raise PolicyError(f"output tree contains symlink: {entry.path}")
                if entry.is_dir(follow_symlinks=False):
                    stack.append(entry.path)
                elif entry.is_file(follow_symlinks=False):
                    total += entry.stat(follow_symlinks=False).st_size
                else:
                    raise PolicyError(f"output tree contains nonregular entry: {entry.path}")
    return total


# ---------------------------------------------------------------------------
# Watchdog
# ---------------------------------------------------------------------------

class TreeWatchdog:
    """Background sampler that aborts the owned process tree on a ceiling breach.

    This object only measures and trips the abort latch.  Process actuation is
    delegated to the runner's synchronized spawn coordinator, which owns the
    registered identities and performs fresh per-PID reproof.
    """

    GRACE_SECONDS = 3.0

    def __init__(
        self,
        *,
        root_pid: int,
        max_tree_rss_bytes: int,
        max_wall_seconds: int,
        interval_s: float = 2.0,
        on_abort: Callable[[dict[str, Any]], None] | None = None,
        cleanup_handler: Callable[[str], Any] | None = None,
        output_root: str | None = None,
        max_run_output_bytes: int | None = None,
        max_tree_processes: int = 64,
    ) -> None:
        if (max_tree_rss_bytes <= 0 or max_wall_seconds <= 0
                or interval_s <= 0 or max_tree_processes <= 0):
            raise PolicyError("watchdog ceilings must be positive")
        if (output_root is None) != (max_run_output_bytes is None):
            raise PolicyError("output_root and max_run_output_bytes must be set together")
        if max_run_output_bytes is not None and max_run_output_bytes <= 0:
            raise PolicyError("run output ceiling must be positive")
        self.root_pid = root_pid
        self.max_tree_rss_bytes = max_tree_rss_bytes
        self.max_wall_seconds = max_wall_seconds
        self.interval_s = interval_s
        self.on_abort = on_abort or (lambda e: None)
        self.cleanup_handler = cleanup_handler or (lambda reason: None)
        self.output_root = output_root
        self.max_run_output_bytes = max_run_output_bytes
        self.max_tree_processes = max_tree_processes
        self.peak_tree_rss_bytes = 0
        self.peak_process_count = 0
        self.samples = 0
        self.aborted: dict[str, Any] | None = None
        self._started = time.monotonic()
        self._stop = threading.Event()
        self._abort_complete = threading.Event()
        self._thread = threading.Thread(target=self._loop, name="dedup-tree-watchdog", daemon=True)

    # -- lifecycle -----------------------------------------------------------
    def start(self) -> None:
        self._started = time.monotonic()
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread.is_alive():
            self._thread.join(timeout=self.interval_s * 3 + self.GRACE_SECONDS + 2)

    def elapsed(self) -> float:
        return time.monotonic() - self._started

    def wait_abort(self, timeout_s: float) -> dict[str, Any] | None:
        """Return the settled abort event, or explicit uncertainty at the deadline."""
        if self.aborted is None:
            return None
        if self._abort_complete.wait(timeout_s):
            return dict(self.aborted)
        unsettled = dict(self.aborted)
        unsettled["cleanup"] = "uncertain"
        unsettled["cleanup_reason"] = "cleanup-result-timeout"
        return unsettled

    # -- sampling --------------------------------------------------------------
    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                table = _sample_table()
            except Exception:
                self._abort("sampler-unavailable", {})
                return
            self.samples += 1
            rss = tree_rss_bytes_from_table(self.root_pid, table)
            count = 1 + len(descendants_from_table(self.root_pid, table))
            self.peak_tree_rss_bytes = max(self.peak_tree_rss_bytes, rss)
            self.peak_process_count = max(self.peak_process_count, count)
            if count > self.max_tree_processes:
                self._abort("max_tree_processes", table)
                return
            if rss > self.max_tree_rss_bytes:
                self._abort("max_tree_rss_bytes", table)
                return
            if self.output_root is not None:
                try:
                    output_bytes = _output_tree_bytes(self.output_root)
                except Exception:
                    self._abort("output-sampler-unavailable", table)
                    return
                if output_bytes > self.max_run_output_bytes:
                    self._abort("max_run_output_bytes", table)
                    return
            if self.elapsed() > self.max_wall_seconds:
                self._abort("max_wall_seconds", table)
                return
            self._stop.wait(self.interval_s)

    # -- abort -----------------------------------------------------------------
    def _abort(self, reason: str, table: dict[int, tuple[int, int]]) -> dict[str, Any]:
        """Freeze admission and delegate cleanup to the identity coordinator."""
        event: dict[str, Any] = {
            "event": "resource_abort",
            "reason": reason,
            "ts_utc": _utc_now(),
            "elapsed_seconds": round(self.elapsed(), 3),
            "peak_tree_rss_bytes": self.peak_tree_rss_bytes,
            "limit_tree_rss_bytes": self.max_tree_rss_bytes,
            "limit_wall_seconds": self.max_wall_seconds,
            "cleanup": "in_progress",
        }
        self.aborted = event
        try:
            self.on_abort(event)
        except Exception:
            pass
        try:
            cleanup = self.cleanup_handler(reason)
            event["cleanup"] = getattr(cleanup, "cleanup", "uncertain")
            event["cleanup_reason"] = getattr(cleanup, "reason", "missing-result")
            event["signaled_pids"] = list(getattr(cleanup, "term_pids", ()))
            event["sigkilled_pids"] = list(getattr(cleanup, "kill_pids", ()))
            event["survivors"] = list(getattr(cleanup, "survivors", ()))
        except Exception as exc:
            event["cleanup"] = "uncertain"
            event["cleanup_reason"] = f"handler-failed:{type(exc).__name__}"
        event["cleanup_utc"] = _utc_now()
        self._abort_complete.set()
        return event


# ---------------------------------------------------------------------------
# Run record
# ---------------------------------------------------------------------------

def _utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _git_head(base_dir: str) -> str | None:
    try:
        out = subprocess.run(["git", "-C", base_dir, "rev-parse", "HEAD"],
                             capture_output=True, text=True, timeout=10)
        return out.stdout.strip() or None if out.returncode == 0 else None
    except Exception:
        return None


class RunRecord:
    """Accumulates the ``run.json`` contract (plan §6.2) and writes it atomically."""

    SCHEMA_VERSION = 1

    def __init__(self, data: dict[str, Any]) -> None:
        self.data = data

    @classmethod
    def start(cls, *, policy: ResourcePolicy, base_dir: str, extra: dict[str, Any] | None = None) -> "RunRecord":
        data: dict[str, Any] = {
            "schema_version": cls.SCHEMA_VERSION,
            "started_utc": _utc_now(),
            "ended_utc": None,
            "outcome": "running",
            "policy": policy.to_dict(),
            "base_commit": _git_head(base_dir),
            "host": {"platform": os.uname().sysname, "release": os.uname().release, "pid": os.getpid()},
            "phases": {},
            "counts": {},
            "truncated": False,
            "truncation_reason": None,
            "peak": None,
            "artifacts": {},
            "errors": [],
        }
        if extra:
            data.update(extra)
        return cls(data)

    def note_phase(self, name: str, info: dict[str, Any]) -> None:
        self.data["phases"].setdefault(name, {}).update(info)

    def note_error(self, message: str) -> None:
        self.data["errors"].append({"ts_utc": _utc_now(), "message": message})

    def finish(
        self,
        *,
        outcome: str,
        artifacts: dict[str, str] | None = None,
        counts: dict[str, Any] | None = None,
        truncated: bool = False,
        truncation_reason: str | None = None,
        peak: dict[str, Any] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        d = self.data
        d["ended_utc"] = _utc_now()
        d["outcome"] = outcome
        if counts:
            d["counts"].update(counts)
        # A truncation noted earlier in the run must survive finish().
        d["truncated"] = bool(truncated) or bool(d.get("truncated"))
        d["truncation_reason"] = truncation_reason or d.get("truncation_reason")
        if peak is not None:
            d["peak"] = peak
        if artifacts:
            for name, path in artifacts.items():
                if path and os.path.exists(path):
                    d["artifacts"][name] = {
                        "path": os.path.abspath(path),
                        "bytes": os.path.getsize(path),
                        "sha256": _sha256_file(path),
                    }
                else:
                    d["artifacts"][name] = {"path": path, "bytes": None, "sha256": None, "present": False}
        if extra:
            d.update(extra)

    def write(self, path: str) -> None:
        # Re-hash artifacts at write time so the record matches what is on disk.
        for name, meta in list(self.data["artifacts"].items()):
            p = meta.get("path")
            if p and os.path.exists(p):
                meta["bytes"] = os.path.getsize(p)
                meta["sha256"] = _sha256_file(p)
                meta["present"] = True
        text = json.dumps(self.data, indent=2, sort_keys=True)
        if _jsonstream is not None:
            _jsonstream.atomic_write_text(path, lambda fh: fh.write(text + "\n"))
        else:  # pragma: no cover
            tmp = f"{path}.{os.getpid()}.tmp"
            with open(tmp, "w", encoding="utf-8") as fh:
                fh.write(text + "\n")
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, path)
