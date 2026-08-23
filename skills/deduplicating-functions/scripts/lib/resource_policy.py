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
import signal
import subprocess
import threading
import time
from typing import Any, Callable, Iterable

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
    mode: str = "refuse"                    # refuse | truncate

    _INT_FIELDS = (
        "max_input_bytes", "max_pairs", "max_report_rows", "max_output_bytes",
        "max_wall_seconds", "max_tree_rss_bytes", "max_legacy_json_bytes",
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
    table: dict[int, tuple[int, int]] = {}
    for line in out.stdout.splitlines():
        parts = line.split()
        if len(parts) != 3:
            continue
        try:
            table[int(parts[0])] = (int(parts[1]), int(parts[2]))
        except ValueError:
            continue
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


# ---------------------------------------------------------------------------
# Watchdog
# ---------------------------------------------------------------------------

class TreeWatchdog:
    """Background sampler that aborts the owned process tree on a ceiling breach.

    ``owned_pids`` returns pids the runner spawned itself (e.g. Popen children
    started in their own session). They are signaled only if the fresh process
    table still shows them as descendants of ``root_pid`` — ownership is
    re-proven at signal time, never assumed from the earlier spawn.
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
        owned_pids: Callable[[], Iterable[int]] | None = None,
    ) -> None:
        if max_tree_rss_bytes <= 0 or max_wall_seconds <= 0 or interval_s <= 0:
            raise PolicyError("watchdog ceilings must be positive")
        self.root_pid = root_pid
        self.max_tree_rss_bytes = max_tree_rss_bytes
        self.max_wall_seconds = max_wall_seconds
        self.interval_s = interval_s
        self.on_abort = on_abort or (lambda e: None)
        self.owned_pids = owned_pids or (lambda: [])
        self.peak_tree_rss_bytes = 0
        self.peak_process_count = 0
        self.samples = 0
        self.aborted: dict[str, Any] | None = None
        self._started = time.monotonic()
        self._stop = threading.Event()
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

    # -- sampling --------------------------------------------------------------
    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                table = _sample_table()
            except Exception:  # sampler failure must not kill the pipeline; it is reported below
                table = None
            if table is not None:
                self.samples += 1
                rss = tree_rss_bytes_from_table(self.root_pid, table)
                count = 1 + len(descendants_from_table(self.root_pid, table))
                self.peak_tree_rss_bytes = max(self.peak_tree_rss_bytes, rss)
                self.peak_process_count = max(self.peak_process_count, count)
                if rss > self.max_tree_rss_bytes:
                    self._abort("max_tree_rss_bytes", table)
                    return
            if self.elapsed() > self.max_wall_seconds:
                self._abort("max_wall_seconds", table if table is not None else _sample_table())
                return
            self._stop.wait(self.interval_s)

    # -- abort -----------------------------------------------------------------
    def _abort(self, reason: str, table: dict[int, tuple[int, int]]) -> dict[str, Any]:
        """Terminate the owned tree. The event is published (on_abort + self.aborted)
        immediately after SIGTERM so observers never see a dead child without an
        event; the same dict is then updated in place after the grace/KILL phase."""
        owned = set(int(p) for p in self.owned_pids())
        descendants = descendants_from_table(self.root_pid, table)
        desc_set = set(descendants)
        # Signal deepest-first so parents do not respawn children mid-abort.
        targets = list(reversed(descendants))
        skipped_unowned = sorted(p for p in owned if p not in desc_set)
        signaled: list[int] = []
        for pid in targets:
            try:
                os.kill(pid, signal.SIGTERM)
                signaled.append(pid)
            except (ProcessLookupError, PermissionError):
                continue
        event: dict[str, Any] = {
            "event": "resource_abort",
            "reason": reason,
            "ts_utc": _utc_now(),
            "elapsed_seconds": round(self.elapsed(), 3),
            "peak_tree_rss_bytes": self.peak_tree_rss_bytes,
            "limit_tree_rss_bytes": self.max_tree_rss_bytes,
            "limit_wall_seconds": self.max_wall_seconds,
            "signaled_pids": signaled,
            "sigkilled_pids": [],
            "skipped_unowned_pids": skipped_unowned,
            "cleanup": "in_progress",
        }
        self.aborted = event
        try:
            self.on_abort(event)
        except Exception:
            pass
        # Grace period, then SIGKILL survivors whose ownership is re-proven.
        deadline = time.monotonic() + self.GRACE_SECONDS
        survivors = list(signaled)
        while survivors and time.monotonic() < deadline:
            time.sleep(0.1)
            still = []
            for pid in survivors:
                try:
                    os.kill(pid, 0)
                    still.append(pid)
                except ProcessLookupError:
                    continue
                except PermissionError:
                    still.append(pid)
            survivors = still
        killed: list[int] = []
        if survivors:
            fresh = _sample_table()
            fresh_desc = set(descendants_from_table(self.root_pid, fresh))
            for pid in survivors:
                if pid not in fresh_desc:
                    continue
                try:
                    os.kill(pid, signal.SIGKILL)
                    killed.append(pid)
                except (ProcessLookupError, PermissionError):
                    continue
        event["sigkilled_pids"] = killed
        event["cleanup"] = "complete" if not survivors or killed or not signaled else "uncertain"
        event["cleanup_utc"] = _utc_now()
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
