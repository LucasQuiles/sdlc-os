"""Red-before-green coverage for the 2026-08-27 independent review findings 1-6.

Findings receipt: round9-tracking/receipts/d6-monitor-review-findings-20260827T005x.json.
Each test targets one finding and fails against 5a48b103 for that finding's reason.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest

import d6_pressure_monitor as monitor
from d6_pressure_monitor import MonitorThresholds
from test_d6_pressure_monitor import (
    FakeChild,
    lifecycle_deps,
    read_receipt,
    run_fake,
    sample,
)


def replace_deps(deps: Any, **overrides: Any) -> Any:
    return monitor.RunnerDependencies(**{**deps.__dict__, **overrides})


def test_fast_exit_before_getpgid_is_scored_and_reaped(tmp_path: Path) -> None:
    """Finding 1: getpgid ESRCH on an already-exited child must not void the run.

    start_new_session guarantees pgid == pid from birth, so an ESRCH here proves
    only that the leader already exited; the zombie keeps identity pinned and the
    normal leader-exited path must score and reap it.
    """
    receipt = tmp_path / "esrch" / "result.json"
    child = FakeChild(exit_code=0)

    def getpgid_raises(pid: int) -> int:
        raise ProcessLookupError(3, "No such process")

    deps = lifecycle_deps(
        tmp_path,
        child=child,
        probes=[sample(group_rss_mb=0.0, member_pids=(), leader_exited=True)],
    )
    deps = replace_deps(deps, getpgid=getpgid_raises)

    assert run_fake(["true"], receipt, deps) == 0
    body = read_receipt(receipt)
    assert body["outcome"] == "Pass"
    assert body["command_exit_code"] == 0
    assert child.reaped is True


def test_second_interrupt_during_cleanup_still_publishes(tmp_path: Path) -> None:
    """Finding 2: a second KeyboardInterrupt during cleanup must not escape

    without a receipt; the exit-code contract (3, D6_INTERRUPTED) must hold.
    """
    receipt = tmp_path / "double-interrupt" / "result.json"

    def probe_interrupt(owned_pgid: int, tracked: frozenset[int]) -> Any:
        raise KeyboardInterrupt

    def census_interrupt(owned_pgid: int, tracked: frozenset[int]) -> Any:
        raise KeyboardInterrupt

    deps = lifecycle_deps(tmp_path)
    deps = replace_deps(deps, probe=probe_interrupt, census=census_interrupt)

    assert run_fake(["cmd"], receipt, deps) == 3
    body = read_receipt(receipt)
    assert body["outcome"] == "Inconclusive"
    assert body["code"] == "D6_INTERRUPTED"
    assert body["cleanup"] == "unavailable"


def test_interrupt_during_publish_returns_inconclusive(tmp_path: Path) -> None:
    """Finding 2: publication failure semantics must cover BaseException."""

    def publish_interrupt(path: Path, payload: dict[str, Any]) -> None:
        raise KeyboardInterrupt

    deps = lifecycle_deps(tmp_path, publish=publish_interrupt)
    assert run_fake(["true"], tmp_path / "missing.json", deps) == 3


def test_probe_timeout_is_configurable_and_retried_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Finding 3: the probe timeout must come from thresholds and tolerate one

    transient TimeoutExpired instead of aborting the run on the first stall.
    """
    calls: list[float] = []

    class Completed:
        stdout = "ok"

    def fake_run(argv: list[str], **kwargs: Any) -> Any:
        calls.append(kwargs["timeout"])
        if len(calls) == 1:
            raise subprocess.TimeoutExpired(cmd=argv, timeout=kwargs["timeout"])
        return Completed()

    monkeypatch.setattr(monitor.subprocess, "run", fake_run)
    assert monitor._run_checked(["ps"], timeout_s=2.5) == "ok"
    assert calls == [2.5, 2.5]

    with pytest.raises(ValueError, match="probe_timeout_s"):
        MonitorThresholds(probe_timeout_s=0.0)


def test_ownership_refusal_terminates_and_reaps_spawned_child(tmp_path: Path) -> None:
    """Finding 4: a refused child was launched by this wrapper and must be

    terminated directly (never via killpg on a foreign pgid) and reaped.
    """
    receipt = tmp_path / "refused" / "result.json"
    child = FakeChild()
    signals: list[tuple[int, int]] = []
    deps = lifecycle_deps(tmp_path, child=child, pgid=9999, signals=signals)

    assert run_fake(["cmd"], receipt, deps) == 3
    assert signals == []
    assert child.terminated is True
    assert child.reaped is True
    assert read_receipt(receipt)["code"] == "D6_OWNERSHIP_REFUSED"


def test_tracked_pids_are_pruned_to_current_membership(tmp_path: Path) -> None:
    """Finding 5: tracked pids must not accumulate exited members forever;

    the escape check for probe N+1 uses probe N's membership, so a recycled
    pid from an old sample cannot raise a false OwnershipLost.
    """
    receipt = tmp_path / "prune" / "result.json"
    seen_tracked: list[frozenset[int]] = []
    probe_values = [
        sample(member_pids=(4100, 4200)),
        sample(member_pids=(4100,)),
        sample(group_rss_mb=0.0, member_pids=(), leader_exited=True),
    ]

    def probe(owned_pgid: int, tracked: frozenset[int]) -> Any:
        seen_tracked.append(tracked)
        return probe_values[len(seen_tracked) - 1]

    deps = lifecycle_deps(tmp_path)
    deps = replace_deps(deps, probe=probe)

    assert run_fake(["cmd"], receipt, deps) == 0
    assert seen_tracked == [
        frozenset(),
        frozenset({4100, 4200}),
        frozenset({4100}),
    ]


def test_slow_probe_resyncs_schedule_without_burst(tmp_path: Path) -> None:
    """Finding 6: a probe slower than the interval must resynchronize the

    schedule (one full-interval breather) instead of busy-probing back to back.
    """
    receipt = tmp_path / "resync" / "result.json"
    deps = lifecycle_deps(tmp_path)
    clock_holder = {"value": 0.0}
    sleeps: list[float] = []
    probe_count = {"n": 0}

    def monotonic() -> float:
        return clock_holder["value"]

    def sleep(duration: float) -> None:
        sleeps.append(duration)
        clock_holder["value"] += duration

    def probe(owned_pgid: int, tracked: frozenset[int]) -> Any:
        probe_count["n"] += 1
        if probe_count["n"] == 1:
            clock_holder["value"] += 3.0  # slow probe: three intervals long
            return sample()
        if probe_count["n"] == 2:
            return sample()
        return sample(group_rss_mb=0.0, member_pids=(), leader_exited=True)

    deps = replace_deps(deps, probe=probe, monotonic=monotonic, sleep=sleep)

    assert run_fake(["cmd"], receipt, deps) == 0
    assert sleeps == [1.0, 1.0]
    assert probe_count["n"] == 3
