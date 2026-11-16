"""Fail-closed publication and subprocess ownership for the pipeline.

This module is deliberately standard-library only.  The pipeline owns only processes
admitted through :class:`SpawnCoordinator` and only run directories created by
:class:`ManagedRunPublisher`.
"""
from __future__ import annotations

import dataclasses
import datetime as dt
import fcntl
import json
import math
import os
import re
import signal
import stat
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Callable, Mapping


class AbortInProgress(RuntimeError):
    """A subprocess was offered after the coordinator stopped admission."""


class IdentityUnproven(RuntimeError):
    """A newly spawned child could not be bound to a process identity."""


@dataclasses.dataclass(frozen=True)
class ProcessIdentity:
    pid: int
    ppid: int
    uid: int
    pgid: int
    start_token: str
    ancestor_pid: int


@dataclasses.dataclass(frozen=True)
class CensusOutcome:
    status: str
    table: Mapping[int, ProcessIdentity]
    reason: str | None = None

    @classmethod
    def ok(cls, table: Mapping[int, ProcessIdentity]) -> "CensusOutcome":
        return cls("ok", dict(table), None)

    @classmethod
    def unknown(cls, reason: str) -> "CensusOutcome":
        return cls("unknown", {}, reason)


@dataclasses.dataclass(frozen=True)
class CleanupResult:
    cleanup: str
    reason: str
    term_pids: tuple[int, ...] = ()
    kill_pids: tuple[int, ...] = ()
    survivors: tuple[int, ...] = ()


class PsProcessBackend:
    """Bounded Darwin/Linux ``ps`` census with explicit unknown outcomes."""

    def census(self, timeout_s: float) -> CensusOutcome:
        try:
            result = subprocess.run(
                ["ps", "-axo", "pid=,ppid=,uid=,pgid=,lstart="],
                capture_output=True,
                text=True,
                timeout=timeout_s,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return CensusOutcome.unknown("census-timeout")
        except (OSError, ValueError) as exc:
            return CensusOutcome.unknown(f"census-backend-failed:{type(exc).__name__}")
        if result.returncode != 0:
            return CensusOutcome.unknown(f"census-nonzero:{result.returncode}")
        table: dict[int, ProcessIdentity] = {}
        malformed = 0
        for raw in result.stdout.splitlines():
            parts = raw.split(None, 4)
            if not raw.strip():
                continue
            if len(parts) != 5:
                malformed += 1
                continue
            try:
                pid, ppid, uid, pgid = (int(value) for value in parts[:4])
            except ValueError:
                malformed += 1
                continue
            start = " ".join(parts[4].split())
            if not start or pid <= 0 or ppid < 0 or uid < 0 or pgid <= 0:
                malformed += 1
                continue
            table[pid] = ProcessIdentity(pid, ppid, uid, pgid, start, 0)
        if malformed:
            return CensusOutcome.unknown(f"census-incomplete:{malformed}")
        if not table:
            return CensusOutcome.unknown("census-empty")
        return CensusOutcome.ok(table)

    def signal(self, pid: int, sig: int) -> None:
        os.kill(pid, sig)


def _same_process(expected: ProcessIdentity, current: ProcessIdentity) -> bool:
    return (
        expected.pid == current.pid
        and expected.ppid == current.ppid
        and expected.uid == current.uid
        and expected.pgid == current.pgid
        and expected.start_token == current.start_token
    )


def _is_descendant(pid: int, root: int, table: Mapping[int, ProcessIdentity]) -> bool:
    seen: set[int] = set()
    current = pid
    while current in table and current not in seen:
        seen.add(current)
        parent = table[current].ppid
        if parent == root:
            return True
        current = parent
    return False


class SpawnCoordinator:
    """Synchronize spawn admission with abort and signal only re-proven PIDs."""

    def __init__(
        self,
        *,
        backend: Any | None = None,
        popen_factory: Callable[..., Any] = subprocess.Popen,
        census_timeout_s: float = 5.0,
        term_grace_s: float = 1.0,
        poll_s: float = 0.05,
    ) -> None:
        timing_values = (census_timeout_s, term_grace_s, poll_s)
        if not all(math.isfinite(value) and value > 0 for value in timing_values):
            raise ValueError(
                "census_timeout_s, term_grace_s, and poll_s must all be finite positive values")
        self._backend = backend or PsProcessBackend()
        self._popen_factory = popen_factory
        self._census_timeout_s = census_timeout_s
        self._term_grace_s = term_grace_s
        self._poll_s = poll_s
        self._lock = threading.Lock()
        self._cleanup_lock = threading.Lock()
        self._state = "RUNNING"
        self.abort_event = threading.Event()
        self._registered: dict[int, ProcessIdentity] = {}

    @property
    def state(self) -> str:
        with self._lock:
            return self._state

    def registered_pids(self) -> tuple[int, ...]:
        with self._lock:
            return tuple(sorted(self._registered))

    def popen(self, argv: list[str] | tuple[str, ...], **kwargs: Any) -> Any:
        with self._lock:
            if self._state != "RUNNING" or self.abort_event.is_set():
                raise AbortInProgress("subprocess admission is frozen")
            process = self._popen_factory(argv, **kwargs)
            outcome = self._backend.census(self._census_timeout_s)
            current = outcome.table.get(process.pid) if outcome.status == "ok" else None
            unproven_reason = outcome.reason
            if current is not None and current.ppid != os.getpid():
                # The census row for this pid is not our direct child (pid reuse
                # after a fast exit, or a raced table): registering that identity
                # would let a later cleanup signal a foreign process.
                current = None
                unproven_reason = unproven_reason or "ppid-mismatch"
            if current is None:
                if process.poll() is not None:
                    return process
                reaped = self._reap_direct_child(process)
                self._state = "ABORTING"
                self.abort_event.set()
                reason = unproven_reason or "spawned-child-missing"
                if not reaped:
                    reason += "; direct-child-cleanup-uncertain"
                raise IdentityUnproven(reason)
            if process.poll() is not None:
                # Already exited: the census row may describe a zombie or a
                # reused pid — never register a dead child for later signaling.
                return process
            self._registered[process.pid] = dataclasses.replace(
                current, ancestor_pid=os.getpid())
            return process

    def complete(self, process: Any) -> None:
        if process.poll() is None:
            raise RuntimeError("cannot unregister a live process")
        with self._lock:
            self._registered.pop(process.pid, None)

    def run(self, argv: list[str] | tuple[str, ...], *, timeout: float | None = None,
            **kwargs: Any) -> subprocess.CompletedProcess:
        process = self.popen(argv, **kwargs)
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            # One slow child is a per-child failure, not a coordinator-wide
            # event: clean up that child and its descendants only, leaving
            # admission open for the remaining phases (--permissive contract).
            self.terminate_child(process)
            raise
        except BaseException:
            self.abort(reason="child-communication-failed")
            raise
        finally:
            if process.poll() is not None:
                self.complete(process)
        return subprocess.CompletedProcess(argv, process.returncode, stdout, stderr)

    def _fresh_targets(
        self, expected: Mapping[int, ProcessIdentity], outcome: CensusOutcome
    ) -> tuple[dict[int, ProcessIdentity], str | None]:
        if outcome.status != "ok":
            return {}, outcome.reason or "census-unknown"
        targets: dict[int, ProcessIdentity] = {}
        for pid, identity in expected.items():
            current = outcome.table.get(pid)
            if current is not None and not _same_process(identity, current):
                return {}, "identity-mismatch"
            if current is not None:
                targets[pid] = identity
        for pid, identity in expected.items():
            for child_pid, child in outcome.table.items():
                if (child.uid == identity.uid
                        and _is_descendant(child_pid, pid, outcome.table)):
                    targets.setdefault(
                        child_pid, dataclasses.replace(child, ancestor_pid=pid))
        return targets, None

    def _survivors(
        self, expected: Mapping[int, ProcessIdentity]
    ) -> tuple[dict[int, ProcessIdentity], str | None]:
        outcome = self._backend.census(self._census_timeout_s)
        return self._fresh_targets(expected, outcome)

    def _reap_direct_child(self, process: Any) -> bool:
        """Terminate an unproven direct child through its Popen handle.

        The handle names the exact process we spawned, so no census identity
        is required before signaling it; ``wait`` also reaps the zombie.
        Returns True when the child is confirmed exited, False when it may
        still be alive after TERM+KILL and both grace waits."""
        if process.poll() is not None:
            return True
        try:
            process.terminate()
        except OSError:
            pass
        try:
            process.wait(timeout=self._term_grace_s)
            return True
        except subprocess.TimeoutExpired:
            pass
        try:
            process.kill()
        except OSError:
            pass
        try:
            process.wait(timeout=self._term_grace_s)
            return True
        except subprocess.TimeoutExpired:
            return False

    def terminate_child(self, process: Any) -> CleanupResult:
        """Clean up one owned child and its descendants without freezing admission.

        The identity-proven sweep runs first, while the direct child is still
        alive, so its descendants remain chained to it in the process table;
        the handle-based reap then confirms the direct child is gone. Any
        uncertainty (sweep or reap) escalates to a full coordinator abort —
        admission must not stay open over an uncleaned tree."""
        with self._cleanup_lock:
            with self._lock:
                identity = self._registered.pop(process.pid, None)
            if identity is None:
                if self._reap_direct_child(process):
                    return CleanupResult("complete", "child-timeout")
                result = CleanupResult("uncertain", "direct-child-cleanup-uncertain",
                                       survivors=(process.pid,))
            else:
                result = self._sweep({process.pid: identity}, "child-timeout")
                if not self._reap_direct_child(process):
                    result = CleanupResult(
                        "uncertain", "direct-child-cleanup-uncertain",
                        result.term_pids, result.kill_pids,
                        tuple(sorted(set(result.survivors) | {process.pid})))
        if result.cleanup != "complete":
            # Escalate outside _cleanup_lock (abort re-acquires it).
            self.abort(reason=f"child-timeout-{result.reason}")
        return result

    def abort(self, reason: str = "abort-requested") -> CleanupResult:
        """Freeze admission and serialize the one cleanup owner."""
        with self._cleanup_lock:
            return self._abort_once(reason)

    def _abort_once(self, reason: str) -> CleanupResult:
        with self._lock:
            self._state = "ABORTING"
            self.abort_event.set()
            expected = dict(self._registered)
        if not expected:
            with self._lock:
                self._state = "CLOSED"
            return CleanupResult("complete", reason)
        result = self._sweep(expected, reason)
        if result.cleanup == "complete":
            with self._lock:
                self._registered.clear()
                self._state = "CLOSED"
        return result

    def _sweep(self, expected: Mapping[int, ProcessIdentity], reason: str) -> CleanupResult:
        """TERM/grace/KILL the given identity-proven pids and their descendants."""
        targets, error = self._fresh_targets(
            dict(expected), self._backend.census(self._census_timeout_s))
        if error:
            return CleanupResult("uncertain", error, survivors=tuple(sorted(expected)))

        term_pids: list[int] = []
        for pid in sorted(targets, reverse=True):
            current, fresh_error = self._survivors({pid: targets[pid]})
            if fresh_error:
                return CleanupResult("uncertain", fresh_error,
                                     tuple(term_pids), survivors=tuple(sorted(expected)))
            if not current:
                continue
            try:
                self._backend.signal(pid, signal.SIGTERM)
                term_pids.append(pid)
            except ProcessLookupError:
                continue
            except (PermissionError, OSError):
                return CleanupResult("uncertain", "term-failed",
                                     tuple(term_pids), survivors=(pid,))

        deadline = time.monotonic() + self._term_grace_s
        survivors: dict[int, ProcessIdentity] = dict(targets)
        zero_count = 0
        while time.monotonic() < deadline:
            survivors, error = self._survivors(targets)
            if error:
                return CleanupResult("uncertain", error, tuple(term_pids),
                                     survivors=tuple(sorted(targets)))
            targets.update(survivors)
            if not survivors:
                zero_count += 1
                if zero_count >= 2:
                    return CleanupResult("complete", reason, tuple(term_pids))
            else:
                zero_count = 0
            time.sleep(self._poll_s)

        kill_pids: list[int] = []
        for pid in sorted(survivors, reverse=True):
            current, fresh_error = self._survivors({pid: survivors[pid]})
            if fresh_error:
                return CleanupResult("uncertain", fresh_error, tuple(term_pids),
                                     tuple(kill_pids), tuple(sorted(survivors)))
            if not current:
                continue
            try:
                self._backend.signal(pid, signal.SIGKILL)
                kill_pids.append(pid)
            except ProcessLookupError:
                continue
            except (PermissionError, OSError):
                return CleanupResult("uncertain", "kill-failed", tuple(term_pids),
                                     tuple(kill_pids), (pid,))

        final: dict[int, ProcessIdentity] = dict(survivors)
        zero_count = 0
        deadline = time.monotonic() + self._term_grace_s
        while time.monotonic() < deadline:
            final, error = self._survivors(targets)
            if error:
                return CleanupResult("uncertain", error, tuple(term_pids),
                                     tuple(kill_pids), tuple(sorted(targets)))
            targets.update(final)
            if not final:
                zero_count += 1
                if zero_count >= 2:
                    return CleanupResult("complete", reason, tuple(term_pids),
                                         tuple(kill_pids))
            else:
                zero_count = 0
            time.sleep(self._poll_s)
        return CleanupResult("uncertain", "survivor-timeout", tuple(term_pids),
                             tuple(kill_pids), tuple(sorted(final)))


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _atomic_json(path: Path, payload: Mapping[str, Any], *, max_bytes: int = 65536) -> None:
    data = (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode()
    if len(data) > max_bytes:
        raise ValueError(f"serialized manifest exceeds {max_bytes} bytes")
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb", closefd=False) as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        os.close(descriptor)
    os.replace(temporary, path)
    _fsync_directory(path.parent)


class ManagedRunPublisher:
    """Create immutable run directories and publish only completed runs."""

    def __init__(self, root: str | os.PathLike[str], *, run_id: str) -> None:
        self.root = Path(root)
        if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", run_id or "") is None:
            raise ValueError("run_id must be one safe path component")
        self.run_id = run_id
        self.work_path = self.root / ".inflight" / run_id
        self._lock_fd: int | None = None
        self._begun = False

    def _validate_root(self) -> None:
        supplied = self.root.expanduser()
        if ".." in supplied.parts:
            raise ValueError("managed output root contains a parent traversal")
        absolute = Path(os.path.abspath(supplied))
        forbidden = {
            Path("/"), Path.home(), Path("/Users"), Path("/home"), Path("/tmp"),
            Path("/private/tmp"), Path("/var"), Path("/System"),
            Path("/private"), Path("/private/var"), Path("/Library"),
            Path("/Applications"), Path("/usr"), Path("/opt"), Path("/etc"),
            Path("/bin"), Path("/sbin"),
        }
        if absolute in forbidden:
            raise ValueError(f"managed output root is too broad: {absolute}")
        if os.path.ismount(absolute):
            raise ValueError(f"managed output root is a filesystem mount: {absolute}")
        if absolute.resolve(strict=False) != absolute:
            raise ValueError("managed output root has a symlink ancestor")
        self.root = absolute
        if self.root.exists() and not self.root.is_dir():
            raise ValueError("managed output root is not a directory")
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.root.is_symlink():
            raise ValueError("managed output root became a symlink")
        root_stat = self.root.stat()
        if root_stat.st_uid != os.getuid():
            raise ValueError("managed output root is not owned by the current user")

    def begin(self) -> Path:
        self._validate_root()
        lock_path = self.root / ".pipeline.lock"
        if lock_path.is_symlink():
            raise ValueError("managed output lock is a symlink")
        flags = os.O_RDWR | os.O_CREAT
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        self._lock_fd = os.open(lock_path, flags, 0o600)
        lock_stat = os.fstat(self._lock_fd)
        if (not stat.S_ISREG(lock_stat.st_mode) or lock_stat.st_uid != os.getuid()
                or lock_stat.st_nlink != 1):
            self._release()
            raise ValueError("managed output lock identity is unsafe")
        try:
            fcntl.flock(self._lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except Exception:
            os.close(self._lock_fd)
            self._lock_fd = None
            raise
        try:
            for directory in (self.root / ".inflight", self.root / "runs"):
                directory.mkdir(mode=0o700, exist_ok=True)
                if directory.is_symlink():
                    raise ValueError(f"managed directory is a symlink: {directory}")
            self.work_path = self.root / ".inflight" / self.run_id
            self.work_path.mkdir(mode=0o700)
            _fsync_directory(self.root / ".inflight")
            self._begun = True
            return self.work_path
        except Exception:
            self._release()
            raise

    def publish_complete(self, artifact_hashes: Mapping[str, str]) -> Path:
        if not self._begun:
            raise RuntimeError("run has not begun")
        if len(artifact_hashes) > 64:
            raise ValueError("artifact manifest exceeds 64 entries")
        normalized_hashes: dict[str, str] = {}
        for name, digest in artifact_hashes.items():
            artifact = Path(name)
            if (not name or artifact.is_absolute() or ".." in artifact.parts
                    or len(name.encode()) > 512):
                raise ValueError(f"unsafe artifact name: {name!r}")
            if re.fullmatch(r"[0-9a-f]{64}", digest) is None:
                raise ValueError(f"invalid SHA-256 for artifact {name!r}")
            normalized_hashes[name] = digest
        destination = self.root / "runs" / self.run_id
        if destination.exists() or destination.is_symlink():
            raise FileExistsError(destination)
        pointer_path = self.root / "latest-complete.json"
        if pointer_path.exists() or pointer_path.is_symlink():
            pointer_stat = pointer_path.lstat()
            if (not stat.S_ISREG(pointer_stat.st_mode)
                    or pointer_stat.st_uid != os.getuid()
                    or pointer_stat.st_nlink != 1):
                raise ValueError("existing latest pointer identity is unsafe")
            try:
                previous = json.loads(pointer_path.read_text())
            except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                raise ValueError("existing latest pointer is not tool-owned JSON") from exc
            expected_keys = {
                "schema_version", "run_id", "relative_path", "outcome",
                "artifact_hashes", "completed_at_utc",
            }
            if (set(previous) != expected_keys
                    or previous.get("schema_version") != 1
                    or previous.get("outcome") != "complete"
                    or previous.get("relative_path") != f"runs/{previous.get('run_id')}"):
                raise ValueError("existing latest pointer is not tool-owned schema v1")
        os.replace(self.work_path, destination)
        _fsync_directory(destination.parent)
        pointer = {
            "schema_version": 1,
            "run_id": self.run_id,
            "relative_path": f"runs/{self.run_id}",
            "outcome": "complete",
            "artifact_hashes": dict(sorted(normalized_hashes.items())),
            "completed_at_utc": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        try:
            _atomic_json(pointer_path, pointer)
        except Exception:
            try:
                os.replace(destination, self.work_path)
                _fsync_directory(destination.parent)
                _fsync_directory(self.work_path.parent)
                _atomic_json(self.work_path / "incomplete.json", {
                    "schema_version": 1,
                    "run_id": self.run_id,
                    "outcome": "incomplete",
                    "reason": "latest-pointer-publication-failed",
                })
            finally:
                self._release()
            raise
        finally:
            self._release()
        return destination

    def mark_incomplete(self, reason: str) -> None:
        if not self._begun:
            raise RuntimeError("run has not begun")
        if not reason or len(reason.encode()) > 1024:
            raise ValueError("incomplete reason must be 1..1024 bytes")
        _atomic_json(self.work_path / "incomplete.json", {
            "schema_version": 1,
            "run_id": self.run_id,
            "outcome": "incomplete",
            "reason": reason,
        })
        self._release()

    def _release(self) -> None:
        if self._lock_fd is not None:
            os.close(self._lock_fd)
            self._lock_fd = None
