#!/usr/bin/env python3
"""Run one command while monitoring pressure on its owned process group."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import secrets
import signal
import stat
import subprocess
import sys
import time
from collections import deque
from collections.abc import Callable
from dataclasses import asdict
from dataclasses import dataclass, fields
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable
from typing import Any, Protocol


class MonitorError(RuntimeError):
    """A pressure probe could not produce a trustworthy value."""


class OwnershipLost(MonitorError):
    """A previously owned process escaped to another process group."""


class MissingLeaderIdentity(MonitorError):
    """The pinned process-group leader is absent from a canonical census."""


@dataclass(frozen=True)
class MonitorThresholds:
    max_load1: float = 8.0
    max_swap_used_mb: float = 12288.0
    max_group_rss_mb: float = 6144.0
    sample_interval_s: float = 1.0
    term_grace_s: float = 2.0
    kill_grace_s: float = 2.0

    def __post_init__(self) -> None:
        for field in fields(self):
            value = getattr(self, field.name)
            if not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
                raise ValueError(f"{field.name} must be finite and positive")


@dataclass(frozen=True)
class PressureSample:
    load1: float
    swap_used_mb: float
    group_rss_mb: float
    member_pids: tuple[int, ...]
    observed_at_utc: datetime
    leader_exited: bool = False


@dataclass(frozen=True)
class PressureDecision:
    breach: bool
    code: str | None


@dataclass(frozen=True)
class ProcessCensus:
    group_rss_mb: float
    member_pids: tuple[int, ...]
    leader_exited: bool = False


class ChildProcess(Protocol):
    pid: int

    def wait(self, timeout: float) -> int: ...


@dataclass(frozen=True)
class RunnerDependencies:
    launch: Callable[[list[str]], ChildProcess]
    getpgid: Callable[[int], int]
    probe: Callable[[int, frozenset[int]], PressureSample]
    census: Callable[[int, frozenset[int]], ProcessCensus]
    killpg: Callable[[int, int], None]
    monotonic: Callable[[], float]
    sleep: Callable[[float], None]
    utcnow: Callable[[], datetime]
    publish: Callable[[Path, dict[str, Any]], None]


def _unavailable(detail: str) -> MonitorError:
    return MonitorError(f"D6_MONITOR_UNAVAILABLE: {detail}")


def _missing_leader_identity(detail: str) -> MissingLeaderIdentity:
    return MissingLeaderIdentity(f"D6_LEADER_IDENTITY_MISSING: {detail}")


def _finite_nonnegative(value: object, label: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise _unavailable(f"malformed {label}") from exc
    if not math.isfinite(number) or number < 0:
        raise _unavailable(f"invalid {label}")
    return number


def evaluate_sample(
    sample: PressureSample,
    thresholds: MonitorThresholds = MonitorThresholds(),
) -> PressureDecision:
    axes = (
        (sample.load1, thresholds.max_load1, True, "D6_LOAD_BREACH"),
        (sample.swap_used_mb, thresholds.max_swap_used_mb, False, "D6_SWAP_BREACH"),
        (sample.group_rss_mb, thresholds.max_group_rss_mb, False, "D6_RSS_BREACH"),
    )
    for value, limit, equality_breaches, code in axes:
        value = _finite_nonnegative(value, code)
        if value > limit or (equality_breaches and value == limit):
            return PressureDecision(breach=True, code=code)
    return PressureDecision(breach=False, code=None)


def parse_loadavg(values: Iterable[object]) -> float:
    try:
        load1 = tuple(values)[0]
    except (IndexError, TypeError) as exc:
        raise _unavailable("missing load average") from exc
    return _finite_nonnegative(load1, "load average")


_DARWIN_USED_RE = re.compile(r"\bused\s*=\s*([^\s]+)", re.IGNORECASE)


def parse_darwin_swapusage(text: str) -> float:
    match = _DARWIN_USED_RE.search(text)
    if match is None:
        raise _unavailable("malformed vm.swapusage")
    token = match.group(1)
    if not token.lower().endswith("m"):
        raise _unavailable("unexpected vm.swapusage unit")
    return _finite_nonnegative(token[:-1], "swap used")


def parse_linux_meminfo(text: str) -> float:
    values: dict[str, float] = {}
    for line in text.splitlines():
        parts = line.split()
        if not parts or parts[0] not in {"SwapTotal:", "SwapFree:"}:
            continue
        if len(parts) != 3 or parts[2].lower() != "kb":
            raise _unavailable("malformed /proc/meminfo swap row")
        values[parts[0]] = _finite_nonnegative(parts[1], parts[0])
    if set(values) != {"SwapTotal:", "SwapFree:"}:
        raise _unavailable("missing /proc/meminfo swap row")
    used_kb = values["SwapTotal:"] - values["SwapFree:"]
    if used_kb < 0:
        raise _unavailable("swap free exceeds total")
    return used_kb / 1024.0


def parse_process_census(
    text: str,
    *,
    owned_pgid: int,
    leader_identity_pinned: bool,
    tracked_pids: frozenset[int] = frozenset(),
) -> ProcessCensus:
    if not text.strip():
        if leader_identity_pinned:
            raise _missing_leader_identity("empty process census")
        return ProcessCensus(group_rss_mb=0.0, member_pids=(), leader_exited=False)

    members: list[int] = []
    rss_kb = 0.0
    leader_seen = False
    leader_exited = False
    for raw_line in text.splitlines():
        parts = raw_line.split()
        if len(parts) != 4:
            raise _unavailable("malformed process row")
        try:
            pid = int(parts[0])
            pgid = int(parts[1])
        except ValueError as exc:
            raise _unavailable("malformed process identity") from exc
        state = parts[3].upper()
        if not state or state[0] not in "RSDITTUWXZ":
            if pgid == owned_pgid or pid in tracked_pids:
                raise _unavailable("malformed owned process state")
            continue
        if pgid != owned_pgid:
            if pid in tracked_pids and not state.startswith("Z"):
                raise OwnershipLost(f"pid {pid} moved to pgid {pgid}")
            continue
        if pid == owned_pgid:
            leader_seen = True
            leader_exited = state.startswith("Z")
        rss = _finite_nonnegative(parts[2], "owned RSS")
        if state.startswith("Z"):
            continue
        members.append(pid)
        rss_kb += rss

    if leader_identity_pinned and not leader_seen:
        raise _missing_leader_identity(
            "owned process-group leader identity is absent"
        )
    return ProcessCensus(
        group_rss_mb=rss_kb / 1024.0,
        member_pids=tuple(sorted(members)),
        leader_exited=leader_exited,
    )


def _run_checked(argv: list[str]) -> str:
    try:
        completed = subprocess.run(
            argv,
            check=True,
            capture_output=True,
            text=True,
            timeout=1.0,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise _unavailable(f"probe failed: {argv[0]}") from exc
    return completed.stdout


def _read_swap_used_mb() -> float:
    if sys.platform == "darwin":
        return parse_darwin_swapusage(_run_checked(["/usr/sbin/sysctl", "-n", "vm.swapusage"]))
    if sys.platform.startswith("linux"):
        try:
            return parse_linux_meminfo(Path("/proc/meminfo").read_text(encoding="utf-8"))
        except OSError as exc:
            raise _unavailable("cannot read /proc/meminfo") from exc
    raise _unavailable(f"unsupported platform: {sys.platform}")


def _read_census(
    owned_pgid: int,
    tracked_pids: frozenset[int],
) -> ProcessCensus:
    output = _run_checked(["ps", "-axo", "pid=,pgid=,rss=,state="])
    return parse_process_census(
        output,
        owned_pgid=owned_pgid,
        leader_identity_pinned=True,
        tracked_pids=tracked_pids,
    )


def _probe_pressure(
    owned_pgid: int,
    tracked_pids: frozenset[int],
) -> PressureSample:
    try:
        load1 = parse_loadavg(os.getloadavg())
    except OSError as exc:
        raise _unavailable("load average failed") from exc
    swap_used_mb = _read_swap_used_mb()
    census = _read_census(owned_pgid, tracked_pids)
    return PressureSample(
        load1=load1,
        swap_used_mb=swap_used_mb,
        group_rss_mb=census.group_rss_mb,
        member_pids=census.member_pids,
        observed_at_utc=datetime.now(UTC),
        leader_exited=census.leader_exited,
    )


def _launch(argv: list[str]) -> ChildProcess:
    return subprocess.Popen(argv, start_new_session=True)


def _open_private_receipt_parent(parent: Path) -> int:
    try:
        parent_status = parent.lstat()
    except FileNotFoundError:
        try:
            parent.mkdir(mode=0o700)
        except FileExistsError:
            pass
        parent_status = parent.lstat()

    expected_mode = stat.S_IMODE(parent_status.st_mode)
    if (
        not stat.S_ISDIR(parent_status.st_mode)
        or parent_status.st_uid != os.geteuid()
        or expected_mode != 0o700
    ):
        raise PermissionError(
            f"receipt parent must be an owned non-symlink directory with exact mode 0700: {parent}"
        )

    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    directory_fd = os.open(parent, flags)
    opened_status = os.fstat(directory_fd)
    if (
        (opened_status.st_dev, opened_status.st_ino)
        != (parent_status.st_dev, parent_status.st_ino)
        or not stat.S_ISDIR(opened_status.st_mode)
        or opened_status.st_uid != os.geteuid()
        or stat.S_IMODE(opened_status.st_mode) != 0o700
    ):
        os.close(directory_fd)
        raise PermissionError(f"receipt parent changed during validation: {parent}")
    return directory_fd


def _publish_receipt(receipt_path: Path, payload: dict[str, Any]) -> None:
    parent_fd = _open_private_receipt_parent(receipt_path.parent)
    encoded = (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode()
    temp_fd = -1
    temp_name = ""
    try:
        for _ in range(100):
            temp_name = f".{receipt_path.name}.{secrets.token_hex(8)}"
            try:
                temp_fd = os.open(
                    temp_name,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
                    0o600,
                    dir_fd=parent_fd,
                )
            except FileExistsError:
                continue
            break
        else:
            raise FileExistsError("could not allocate private receipt temporary file")
        os.fchmod(temp_fd, 0o600)
        with os.fdopen(temp_fd, "wb") as handle:
            temp_fd = -1
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(
            temp_name,
            receipt_path.name,
            src_dir_fd=parent_fd,
            dst_dir_fd=parent_fd,
        )
        temp_name = ""
        os.fsync(parent_fd)
    finally:
        if temp_fd >= 0:
            os.close(temp_fd)
        if temp_name:
            try:
                os.unlink(temp_name, dir_fd=parent_fd)
            except FileNotFoundError:
                pass
        os.close(parent_fd)


def _iso_utc(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _sample_record(sample: PressureSample) -> dict[str, Any]:
    return {
        "load1": sample.load1,
        "swap_used_mb": sample.swap_used_mb,
        "group_rss_mb": sample.group_rss_mb,
        "member_count": len(sample.member_pids),
        "observed_at_utc": _iso_utc(sample.observed_at_utc),
    }


def _wait_for_empty_group(
    owned_pgid: int,
    known_pids: set[int],
    grace_s: float,
    interval_s: float,
    deps: RunnerDependencies,
) -> tuple[str, ProcessCensus | None]:
    deadline = deps.monotonic() + grace_s
    last_census: ProcessCensus | None = None
    while True:
        try:
            last_census = deps.census(owned_pgid, frozenset(known_pids))
        except OwnershipLost:
            return "unavailable", None
        except Exception:
            if deps.monotonic() >= deadline:
                return "unavailable", None
        else:
            known_pids.update(last_census.member_pids)
            if not last_census.member_pids:
                return "complete", last_census
        remaining = deadline - deps.monotonic()
        if remaining <= 0:
            return "survivors", last_census
        deps.sleep(min(interval_s, remaining))


def _cleanup_group(
    child: ChildProcess,
    owned_pgid: int,
    tracked_pids: frozenset[int],
    thresholds: MonitorThresholds,
    deps: RunnerDependencies,
) -> str:
    known_pids = set(tracked_pids)
    try:
        initial = deps.census(owned_pgid, frozenset(known_pids))
    except Exception:
        return "unavailable"
    known_pids.update(initial.member_pids)
    if not initial.member_pids:
        return _reap_and_confirm_empty(child, thresholds.term_grace_s)

    try:
        deps.killpg(owned_pgid, signal.SIGTERM)
    except Exception:
        pass
    status, _ = _wait_for_empty_group(
        owned_pgid,
        known_pids,
        thresholds.term_grace_s,
        thresholds.sample_interval_s,
        deps,
    )
    if status == "complete":
        status = _reap_and_confirm_empty(child, thresholds.term_grace_s)
    if status != "survivors":
        return status

    try:
        deps.killpg(owned_pgid, signal.SIGKILL)
    except Exception:
        pass
    status, _ = _wait_for_empty_group(
        owned_pgid,
        known_pids,
        thresholds.kill_grace_s,
        thresholds.sample_interval_s,
        deps,
    )
    if status == "complete":
        return _reap_and_confirm_empty(child, thresholds.kill_grace_s)
    return status


def _reap_and_confirm_empty(
    child: ChildProcess,
    grace_s: float,
) -> str:
    try:
        child.wait(timeout=grace_s)
    except Exception:
        return "unavailable"
    return "complete"


def _receipt(
    *,
    argv: list[str],
    thresholds: MonitorThresholds,
    outcome: str,
    code: str | None,
    command_exit_code: int | None,
    started_at: datetime,
    completed_at: datetime,
    samples: deque[dict[str, Any]],
    peaks: dict[str, float],
    cleanup: str,
) -> dict[str, Any]:
    digest = hashlib.sha256(b"\0".join(os.fsencode(arg) for arg in argv)).hexdigest()
    return {
        "schema_version": 1,
        "outcome": outcome,
        "code": code,
        "command_exit_code": command_exit_code,
        "command_sha256": digest,
        "started_at_utc": _iso_utc(started_at),
        "completed_at_utc": _iso_utc(completed_at),
        "thresholds": asdict(thresholds),
        "samples": list(samples),
        "peaks": peaks,
        "cleanup": cleanup,
    }


def _code_from_error(error: MonitorError) -> str:
    if isinstance(error, OwnershipLost):
        return "D6_OWNERSHIP_LOSS"
    if isinstance(error, MissingLeaderIdentity):
        return "D6_LEADER_IDENTITY_MISSING"
    return "D6_MONITOR_UNAVAILABLE"


def _run_monitored(
    argv: list[str],
    receipt_path: Path,
    thresholds: MonitorThresholds,
    deps: RunnerDependencies,
) -> int:
    if not argv or not receipt_path.is_absolute():
        return 2

    started_at = deps.utcnow()
    retained: deque[dict[str, Any]] = deque(maxlen=60)
    peaks = {"load1": 0.0, "swap_used_mb": 0.0, "group_rss_mb": 0.0}
    outcome = "Inconclusive"
    code: str | None = "D6_MONITOR_UNAVAILABLE"
    command_exit_code: int | None = None
    cleanup = "not_required"
    tracked_pids: frozenset[int] = frozenset()
    owned_pgid: int | None = None

    try:
        child = deps.launch(argv)
        observed_pgid = deps.getpgid(child.pid)
        if observed_pgid != child.pid:
            code = "D6_OWNERSHIP_REFUSED"
            cleanup = "not_admitted"
        else:
            owned_pgid = child.pid
            next_sample_at = deps.monotonic()

            while True:
                try:
                    pressure = deps.probe(owned_pgid, tracked_pids)
                    decision = evaluate_sample(pressure, thresholds)
                except MonitorError as error:
                    code = _code_from_error(error)
                    if isinstance(error, (MissingLeaderIdentity, OwnershipLost)):
                        cleanup = "unavailable"
                    else:
                        cleanup = _cleanup_group(
                            child, owned_pgid, tracked_pids, thresholds, deps
                        )
                    break
                tracked_pids = tracked_pids.union(pressure.member_pids)
                retained.append(_sample_record(pressure))
                peaks["load1"] = max(peaks["load1"], pressure.load1)
                peaks["swap_used_mb"] = max(peaks["swap_used_mb"], pressure.swap_used_mb)
                peaks["group_rss_mb"] = max(peaks["group_rss_mb"], pressure.group_rss_mb)
                if decision.breach:
                    code = decision.code
                    cleanup = _cleanup_group(
                        child, owned_pgid, tracked_pids, thresholds, deps
                    )
                    break
                if pressure.leader_exited:
                    if pressure.member_pids:
                        code = "D6_OWNERSHIP_LOSS"
                        cleanup = _cleanup_group(
                            child, owned_pgid, tracked_pids, thresholds, deps
                        )
                    else:
                        try:
                            command_exit_code = child.wait(
                                timeout=thresholds.term_grace_s
                            )
                        except Exception:
                            code = "D6_MONITOR_UNAVAILABLE"
                            cleanup = "unavailable"
                        else:
                            outcome = "Pass" if command_exit_code == 0 else "Fail"
                            code = None if command_exit_code == 0 else "D6_COMMAND_FAIL"
                    break
                next_sample_at += thresholds.sample_interval_s
                delay = next_sample_at - deps.monotonic()
                if delay > 0:
                    deps.sleep(delay)
    except (KeyboardInterrupt, SystemExit):
        code = "D6_INTERRUPTED"
        if owned_pgid is not None:
            cleanup = _cleanup_group(child, owned_pgid, tracked_pids, thresholds, deps)
    except Exception:
        code = "D6_MONITOR_UNAVAILABLE"
        if owned_pgid is not None:
            cleanup = _cleanup_group(child, owned_pgid, tracked_pids, thresholds, deps)

    payload = _receipt(
        argv=argv,
        thresholds=thresholds,
        outcome=outcome,
        code=code,
        command_exit_code=command_exit_code,
        started_at=started_at,
        completed_at=deps.utcnow(),
        samples=retained,
        peaks=peaks,
        cleanup=cleanup,
    )
    try:
        deps.publish(receipt_path, payload)
    except Exception:
        return 3
    if outcome == "Pass":
        return 0
    if outcome == "Fail":
        return 1
    return 3


def _default_dependencies() -> RunnerDependencies:
    return RunnerDependencies(
        launch=_launch,
        getpgid=os.getpgid,
        probe=_probe_pressure,
        census=_read_census,
        killpg=os.killpg,
        monotonic=time.monotonic,
        sleep=time.sleep,
        utcnow=lambda: datetime.now(UTC),
        publish=_publish_receipt,
    )


def run_monitored(
    argv: list[str],
    receipt_path: Path,
    thresholds: MonitorThresholds = MonitorThresholds(),
) -> int:
    """Run ``argv`` in a new session and publish a private pressure receipt."""
    return _run_monitored(argv, receipt_path, thresholds, _default_dependencies())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    if raw_argv not in (["-h"], ["--help"]):
        if len(raw_argv) < 4 or raw_argv[0] != "--receipt" or raw_argv[2] != "--":
            parser.error("expected --receipt ABSOLUTE_PATH -- COMMAND [ARG ...]")
    args = parser.parse_args(raw_argv)
    command = args.command
    if command and command[0] == "--":
        command = command[1:]
    if not command or not args.receipt.is_absolute():
        parser.error("an absolute --receipt and command after -- are required")
    return run_monitored(command, args.receipt)


if __name__ == "__main__":
    raise SystemExit(main())
