from __future__ import annotations

import hashlib
import json
import os
import signal
import stat
import subprocess
import sys
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

import d6_pressure_monitor as monitor
from d6_pressure_monitor import (
    MonitorError,
    MonitorThresholds,
    PressureSample,
    evaluate_sample,
    parse_darwin_swapusage,
    parse_linux_meminfo,
    parse_loadavg,
    parse_process_census,
)


def sample(**overrides: object) -> PressureSample:
    values: dict[str, object] = {
        "load1": 1.0,
        "swap_used_mb": 2.0,
        "group_rss_mb": 3.0,
        "member_pids": (101,),
        "observed_at_utc": datetime(2026, 8, 26, tzinfo=UTC),
    }
    values.update(overrides)
    return PressureSample(**values)


def test_default_thresholds_and_records_are_immutable():
    thresholds = MonitorThresholds()
    assert thresholds == MonitorThresholds(
        max_load1=8.0,
        max_swap_used_mb=12288.0,
        max_group_rss_mb=6144.0,
        sample_interval_s=1.0,
        term_grace_s=2.0,
        kill_grace_s=2.0,
    )
    with pytest.raises(FrozenInstanceError):
        thresholds.max_load1 = 9.0
    with pytest.raises(FrozenInstanceError):
        sample().load1 = 4.0


@pytest.mark.parametrize(
    "field,value",
    [
        ("max_load1", 0.0),
        ("max_swap_used_mb", -1.0),
        ("max_group_rss_mb", float("inf")),
        ("sample_interval_s", float("nan")),
        ("term_grace_s", 0.0),
        ("kill_grace_s", -0.1),
    ],
)
def test_thresholds_require_finite_positive_values(field: str, value: float):
    with pytest.raises(ValueError, match=field):
        MonitorThresholds(**{field: value})


def test_pressure_boundaries_are_fail_closed():
    assert evaluate_sample(sample(load1=7.99)).breach is False
    assert evaluate_sample(sample(load1=8.0)).code == "D6_LOAD_BREACH"
    assert evaluate_sample(sample(swap_used_mb=12288.0)).breach is False
    assert evaluate_sample(sample(swap_used_mb=12288.01)).code == "D6_SWAP_BREACH"
    assert evaluate_sample(sample(group_rss_mb=6144.0)).breach is False
    assert evaluate_sample(sample(group_rss_mb=6144.01)).code == "D6_RSS_BREACH"


@pytest.mark.parametrize("values", [(), ("bad", 1.0, 1.0), (float("nan"), 1.0, 1.0)])
def test_load_probe_rejects_empty_malformed_and_non_finite(values: tuple[object, ...]):
    with pytest.raises(MonitorError, match="D6_MONITOR_UNAVAILABLE"):
        parse_loadavg(values)


def test_load_probe_uses_one_minute_axis():
    assert parse_loadavg((2.5, 3.0, 4.0)) == 2.5


@pytest.mark.parametrize(
    "text",
    [
        "",
        "total = 4096.00M used = nope free = 4096.00M",
        "total = 4096.00M used = nanM free = 4096.00M",
    ],
)
def test_darwin_swap_probe_rejects_empty_malformed_and_non_finite(text: str):
    with pytest.raises(MonitorError, match="D6_MONITOR_UNAVAILABLE"):
        parse_darwin_swapusage(text)


def test_darwin_swap_probe_parses_vm_swapusage_output():
    text = "vm.swapusage: total = 8192.00M  used = 128.50M  free = 8063.50M\n"
    assert parse_darwin_swapusage(text) == 128.5


@pytest.mark.parametrize(
    "text",
    [
        "",
        "MemTotal: 1024 kB\n",
        "SwapTotal: nope kB\nSwapFree: 1 kB\n",
        "SwapTotal: 10 kB\nSwapFree: nan kB\n",
        "SwapTotal: 10 kB\nSwapFree: 11 kB\n",
    ],
)
def test_linux_swap_probe_rejects_empty_malformed_and_non_finite(text: str):
    with pytest.raises(MonitorError, match="D6_MONITOR_UNAVAILABLE"):
        parse_linux_meminfo(text)


def test_linux_swap_probe_returns_used_mebibytes():
    text = "MemTotal: 1000 kB\nSwapTotal: 3072 kB\nSwapFree: 1024 kB\n"
    assert parse_linux_meminfo(text) == 2.0


@pytest.mark.parametrize(
    "text",
    [
        "",
        "not a process row",
        "101 101 nope S",
        "101 101 1 nan",
    ],
)
def test_process_census_rejects_empty_or_malformed_owned_rows(text: str):
    with pytest.raises(MonitorError, match="D6_MONITOR_UNAVAILABLE"):
        parse_process_census(text, owned_pgid=101, leader_expected_alive=True)


def test_process_census_counts_only_live_owned_members():
    text = "\n".join(
        (
            "101 101 1024 S",
            "102 101 2048 R+",
            "103 101 4096 Z",
            "201 201 999999 S",
            "202 201 malformed S",
        )
    )
    census = parse_process_census(text, owned_pgid=101, leader_expected_alive=True)
    assert census.member_pids == (101, 102)
    assert census.group_rss_mb == 3.0


def test_process_census_accepts_owned_darwin_uninterruptible_state():
    census = parse_process_census(
        "101 101 2048 U\n",
        owned_pgid=101,
        leader_expected_alive=True,
    )

    assert census.member_pids == (101,)
    assert census.group_rss_mb == 2.0


def test_process_census_rejects_no_live_members_while_leader_is_expected():
    with pytest.raises(MonitorError, match="D6_MONITOR_UNAVAILABLE"):
        parse_process_census(
            "101 101 1024 Z\n201 201 2048 S\n",
            owned_pgid=101,
            leader_expected_alive=True,
        )


def test_process_census_allows_empty_owned_group_after_cleanup():
    census = parse_process_census(
        "201 201 2048 S\n",
        owned_pgid=101,
        leader_expected_alive=False,
    )
    assert census.member_pids == ()
    assert census.group_rss_mb == 0.0


class FakeChild:
    def __init__(
        self,
        pid: int = 4100,
        polls: list[int | None] | None = None,
        wait_error: Exception | None = None,
    ):
        self.pid = pid
        self._polls = list(polls or [None, 0])
        self._wait_error = wait_error
        self.wait_timeouts: list[float] = []

    def poll(self) -> int | None:
        if len(self._polls) > 1:
            return self._polls.pop(0)
        return self._polls[0]

    def wait(self, timeout: float) -> int:
        self.wait_timeouts.append(timeout)
        if self._wait_error is not None:
            raise self._wait_error
        return self._polls[-1] or 0


class FakeClock:
    def __init__(self):
        self.value = 0.0

    def monotonic(self) -> float:
        return self.value

    def sleep(self, duration: float) -> None:
        self.value += duration


def lifecycle_deps(
    tmp_path: Path,
    *,
    child: FakeChild | None = None,
    pgid: int = 4100,
    probes: list[PressureSample | Exception] | None = None,
    censuses: list[monitor.ProcessCensus | Exception] | None = None,
    signals: list[tuple[int, int]] | None = None,
    publish: Any = None,
) -> Any:
    assert hasattr(monitor, "RunnerDependencies"), "lifecycle implementation is missing"
    clock = FakeClock()
    child = child or FakeChild()
    probe_values = list(probes or [sample()])
    census_values = list(
        censuses or [monitor.ProcessCensus(group_rss_mb=0.0, member_pids=())]
    )
    signals = signals if signals is not None else []

    def next_value(values: list[Any]) -> Any:
        value = values.pop(0) if len(values) > 1 else values[0]
        if isinstance(value, Exception):
            raise value
        return value

    return monitor.RunnerDependencies(
        launch=lambda argv: child,
        getpgid=lambda pid: pgid,
        probe=lambda owned_pgid, leader_expected_alive, tracked_pids: (
            leader_expected_alive(),
            next_value(probe_values),
        )[1],
        census=lambda owned_pgid, tracked_pids: next_value(census_values),
        killpg=lambda owned_pgid, sig: signals.append((owned_pgid, sig)),
        monotonic=clock.monotonic,
        sleep=clock.sleep,
        utcnow=lambda: datetime(2026, 8, 26, 18, 0, tzinfo=UTC),
        publish=publish or monitor._publish_receipt,
    )


def run_fake(
    argv: list[str], receipt_path: Path, deps: Any, thresholds: MonitorThresholds | None = None
) -> int:
    assert hasattr(monitor, "_run_monitored"), "lifecycle implementation is missing"
    return monitor._run_monitored(
        argv,
        receipt_path,
        thresholds or MonitorThresholds(),
        deps,
    )


def read_receipt(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_healthy_child_exit_zero_sends_no_signal_and_publishes_pass(tmp_path: Path):
    receipt = tmp_path / "healthy" / "result.json"
    signals: list[tuple[int, int]] = []
    deps = lifecycle_deps(tmp_path, signals=signals)
    assert run_fake(["python3", "-c", "pass"], receipt, deps) == 0
    assert signals == []
    assert read_receipt(receipt)["outcome"] == "Pass"


def test_immediate_exit_cannot_bypass_initial_pressure_sample(tmp_path: Path):
    receipt = tmp_path / "immediate-exit" / "result.json"
    leader_expected_alive: list[bool] = []
    deps = lifecycle_deps(
        tmp_path,
        child=FakeChild(polls=[0]),
        probes=[sample(load1=8.0, group_rss_mb=0.0, member_pids=())],
    )
    original_probe = deps.probe
    deps = monitor.RunnerDependencies(
        **{
            **deps.__dict__,
            "probe": lambda pgid, alive, tracked: (
                leader_expected_alive.append(alive()),
                original_probe(pgid, alive, tracked),
            )[1],
        }
    )

    assert run_fake(["true"], receipt, deps) == 3
    body = read_receipt(receipt)
    assert body["outcome"] == "Inconclusive"
    assert body["code"] == "D6_LOAD_BREACH"
    assert len(body["samples"]) == 1
    assert leader_expected_alive == [False]


@pytest.mark.parametrize(
    ("command", "expected_result", "expected_outcome", "expected_code"),
    [
        (["/usr/bin/true"], 0, "Pass", None),
        (["/usr/bin/false"], 1, "Fail", "D6_COMMAND_FAIL"),
    ],
)
def test_real_immediate_exit_gets_host_sample_and_command_outcome(
    tmp_path: Path,
    command: list[str],
    expected_result: int,
    expected_outcome: str,
    expected_code: str | None,
):
    receipt = tmp_path / f"immediate-{expected_outcome.lower()}.json"
    thresholds = MonitorThresholds(max_load1=1_000_000.0)

    assert monitor.run_monitored(command, receipt, thresholds) == expected_result
    body = read_receipt(receipt)
    assert body["outcome"] == expected_outcome
    assert body["code"] == expected_code
    assert len(body["samples"]) == 1
    assert body["samples"][0]["group_rss_mb"] == 0.0


def test_ordinary_nonzero_is_fail_not_inconclusive(tmp_path: Path):
    receipt = tmp_path / "failure" / "result.json"
    deps = lifecycle_deps(tmp_path, child=FakeChild(polls=[None, 7]))
    assert run_fake(["false"], receipt, deps) == 1
    body = read_receipt(receipt)
    assert (body["outcome"], body["command_exit_code"]) == ("Fail", 7)


def test_pgid_mismatch_refuses_ownership_before_monitoring(tmp_path: Path):
    receipt = tmp_path / "mismatch" / "result.json"
    probe_calls: list[int] = []
    signals: list[tuple[int, int]] = []
    deps = lifecycle_deps(tmp_path, pgid=9999, signals=signals)
    deps = monitor.RunnerDependencies(
        **{
            **deps.__dict__,
            "probe": lambda *args: probe_calls.append(1),
        }
    )
    assert run_fake(["cmd"], receipt, deps) == 3
    assert probe_calls == []
    assert signals == []
    assert read_receipt(receipt)["code"] == "D6_OWNERSHIP_REFUSED"


@pytest.mark.parametrize(
    "probe_value,expected_code",
    [
        (sample(load1=8.0), "D6_LOAD_BREACH"),
        (MonitorError("D6_MONITOR_UNAVAILABLE: ps failed"), "D6_MONITOR_UNAVAILABLE"),
        (RuntimeError("unexpected probe failure"), "D6_MONITOR_UNAVAILABLE"),
    ],
)
def test_breach_and_probe_uncertainty_signal_only_owned_pgid(
    tmp_path: Path, probe_value: PressureSample | Exception, expected_code: str
):
    receipt = tmp_path / expected_code / "result.json"
    signals: list[tuple[int, int]] = []
    deps = lifecycle_deps(
        tmp_path,
        probes=[probe_value],
        censuses=[
            monitor.ProcessCensus(group_rss_mb=1.0, member_pids=(4100,)),
            monitor.ProcessCensus(group_rss_mb=0.0, member_pids=()),
        ],
        signals=signals,
    )
    assert run_fake(["cmd"], receipt, deps) == 3
    assert signals == [(4100, signal.SIGTERM)]
    assert read_receipt(receipt)["code"] == expected_code


def test_term_resistant_group_receives_kill_for_same_pgid(tmp_path: Path):
    receipt = tmp_path / "resistant" / "result.json"
    live = monitor.ProcessCensus(group_rss_mb=1.0, member_pids=(4100, 4101))
    signals: list[tuple[int, int]] = []
    deps = lifecycle_deps(
        tmp_path,
        probes=[sample(group_rss_mb=6144.01)],
        censuses=[live, live, live, live, monitor.ProcessCensus(0.0, ())],
        signals=signals,
    )
    assert run_fake(["cmd"], receipt, deps) == 3
    assert signals == [(4100, signal.SIGTERM), (4100, signal.SIGKILL)]
    assert read_receipt(receipt)["cleanup"] == "complete"


@pytest.mark.parametrize(
    "wait_error",
    [subprocess.TimeoutExpired("cmd", 2.0), RuntimeError("wait failed")],
)
def test_cleanup_wait_uncertainty_cannot_report_complete(
    tmp_path: Path,
    wait_error: Exception,
):
    receipt = tmp_path / "wait-uncertain" / "result.json"
    child = FakeChild(wait_error=wait_error)
    live = monitor.ProcessCensus(group_rss_mb=1.0, member_pids=(child.pid,))
    empty = monitor.ProcessCensus(group_rss_mb=0.0, member_pids=())
    deps = lifecycle_deps(
        tmp_path,
        child=child,
        probes=[sample(group_rss_mb=6144.01)],
        censuses=[live, empty],
    )

    assert run_fake(["cmd"], receipt, deps) == 3
    assert read_receipt(receipt)["cleanup"] != "complete"
    assert child.wait_timeouts


@pytest.mark.parametrize(
    "final_census,cleanup",
    [
        (monitor.ProcessCensus(group_rss_mb=1.0, member_pids=(4101,)), "survivors"),
        (MonitorError("D6_MONITOR_UNAVAILABLE: final ps failed"), "unavailable"),
    ],
)
def test_survivor_or_unavailable_final_census_stays_inconclusive(
    tmp_path: Path, final_census: monitor.ProcessCensus | Exception, cleanup: str
):
    receipt = tmp_path / cleanup / "result.json"
    live = monitor.ProcessCensus(group_rss_mb=1.0, member_pids=(4100,))
    deps = lifecycle_deps(
        tmp_path,
        probes=[sample(load1=8.0)],
        censuses=[live, live, live, final_census],
    )
    assert run_fake(["cmd"], receipt, deps) == 3
    body = read_receipt(receipt)
    assert body["outcome"] == "Inconclusive"
    assert body["cleanup"] == cleanup


def test_escaped_descendant_is_ownership_loss_without_signalling_escaped_group(
    tmp_path: Path,
):
    receipt = tmp_path / "escaped" / "result.json"
    signals: list[tuple[int, int]] = []
    deps = lifecycle_deps(
        tmp_path,
        probes=[monitor.OwnershipLost("pid 4101 moved to pgid 9000")],
        censuses=[monitor.ProcessCensus(group_rss_mb=0.0, member_pids=())],
        signals=signals,
    )
    assert run_fake(["cmd"], receipt, deps) == 3
    assert signals == []
    assert read_receipt(receipt)["code"] == "D6_OWNERSHIP_LOSS"


@pytest.mark.parametrize("failure", [OSError("disk unavailable"), RuntimeError("encoder failed")])
def test_receipt_publication_failure_cannot_return_clean(
    tmp_path: Path, failure: Exception
):
    def fail_publish(path: Path, payload: dict[str, Any]) -> None:
        raise failure

    deps = lifecycle_deps(tmp_path, publish=fail_publish)
    assert run_fake(["true"], tmp_path / "missing.json", deps) == 3


def test_receipt_is_closed_bounded_private_and_contains_only_command_digest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    secret = "D6_TEST_SECRET_8bb886b1"
    monkeypatch.setenv("D6_PRIVATE_VALUE", secret)
    receipt = tmp_path / "private" / "result.json"
    argv = [sys.executable, "-c", "pass", "--label", "safe"]
    probes = [sample(load1=float(index % 7)) for index in range(100)]
    child = FakeChild(polls=[None] * 100 + [0])
    deps = lifecycle_deps(tmp_path, child=child, probes=probes)
    assert run_fake(argv, receipt, deps) == 0
    body = read_receipt(receipt)
    assert set(body) == {
        "schema_version",
        "outcome",
        "code",
        "command_exit_code",
        "command_sha256",
        "started_at_utc",
        "completed_at_utc",
        "thresholds",
        "samples",
        "peaks",
        "cleanup",
    }
    expected_digest = hashlib.sha256(b"\0".join(os.fsencode(arg) for arg in argv)).hexdigest()
    assert body["command_sha256"] == expected_digest
    assert len(body["samples"]) == 60
    assert stat.S_IMODE(receipt.stat().st_mode) == 0o600
    assert stat.S_IMODE(receipt.parent.stat().st_mode) == 0o700
    assert secret not in receipt.read_text(encoding="utf-8")


def test_cli_requires_separator_and_preserves_exact_command_argv(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    receipt = tmp_path / "cli.json"
    calls: list[tuple[list[str], Path]] = []
    monkeypatch.setattr(
        monitor,
        "run_monitored",
        lambda argv, path: calls.append((argv, path)) or 1,
    )
    with pytest.raises(SystemExit) as refused:
        monitor.main(["--receipt", str(receipt), "python3", "-V"])
    assert refused.value.code == 2
    assert calls == []
    assert monitor.main(["--receipt", str(receipt), "--", "python3", "-V"]) == 1
    assert calls == [(["python3", "-V"], receipt)]


def test_real_isolated_cleanup_reaps_leader_and_leaves_foreign_helper_alive(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    foreign = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(30)"],
        start_new_session=True,
    )
    launched: list[subprocess.Popen[bytes]] = []
    original_launch = monitor._launch

    def capture_launch(argv: list[str]) -> subprocess.Popen[bytes]:
        child = original_launch(argv)
        launched.append(child)
        return child

    monkeypatch.setattr(monitor, "_launch", capture_launch)
    try:
        receipt = tmp_path / "integration" / "result.json"
        thresholds = MonitorThresholds(
            max_load1=1_000_000.0,
            max_swap_used_mb=12288.0,
            max_group_rss_mb=1e-12,
            sample_interval_s=0.01,
            term_grace_s=0.2,
            kill_grace_s=0.2,
        )
        result = monitor.run_monitored(
            [sys.executable, "-c", "import time; time.sleep(30)"],
            receipt,
            thresholds,
        )
        assert result == 3
        body = read_receipt(receipt)
        assert body["outcome"] == "Inconclusive"
        assert body["code"] == "D6_RSS_BREACH"
        assert body["cleanup"] == "complete"
        assert len(launched) == 1
        with pytest.raises(ChildProcessError):
            os.waitpid(launched[0].pid, os.WNOHANG)
        assert foreign.poll() is None
    finally:
        if foreign.poll() is None:
            os.killpg(foreign.pid, signal.SIGTERM)
            foreign.wait(timeout=5)
