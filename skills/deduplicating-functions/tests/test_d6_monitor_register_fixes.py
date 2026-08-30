"""Red-before-green coverage for the round-3 REGISTERED findings (WP7).

Register receipt: round9-tracking/receipts/d6-monitor-round3-register-20260827T014x.json
(authorized for fix by remediation event 51). Each behavioral test fails
against a1d617a for that finding's reason.
"""

from __future__ import annotations

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
)


def replace_deps(deps: Any, **overrides: Any) -> Any:
    return monitor.RunnerDependencies(**{**deps.__dict__, **overrides})


def test_interrupted_direct_termination_reports_cleanup_unavailable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Register MEDIUM: a second interrupt DURING _terminate_child_directly
    left the receipt claiming cleanup='not_required' although TERM/KILL may
    already have been sent and the reap is unconfirmed. The truthful value is
    'unavailable'."""
    receipt = tmp_path / "term-interrupt" / "result.json"
    child = FakeChild()

    def getpgid_interrupt(pid: int) -> int:
        raise KeyboardInterrupt

    def terminate_interrupted(c: Any, thresholds: Any) -> str:
        raise KeyboardInterrupt

    monkeypatch.setattr(monitor, "_terminate_child_directly", terminate_interrupted)
    deps = lifecycle_deps(tmp_path, child=child)
    deps = replace_deps(deps, getpgid=getpgid_interrupt)

    assert run_fake(["cmd"], receipt, deps) == 3
    body = read_receipt(receipt)
    assert body["code"] == "D6_INTERRUPTED"
    assert body["cleanup"] == "unavailable", (
        "signals may have been sent with reap unconfirmed; "
        f"'not_required' is untruthful (got {body['cleanup']!r})"
    )


def test_interrupted_termination_on_ownership_refusal_reports_unavailable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Review R4 (tranche round): the OWNERSHIP-REFUSED call site needs the
    same pessimistic pre-set as the launch-to-ownership site — a mutant
    removing it survived the suite. A second interrupt during that
    termination must leave cleanup='unavailable', never 'not_required'."""
    receipt = tmp_path / "refused-term-interrupt" / "result.json"
    child = FakeChild()

    def terminate_interrupted(c: Any, thresholds: Any) -> str:
        raise KeyboardInterrupt

    monkeypatch.setattr(monitor, "_terminate_child_directly", terminate_interrupted)
    deps = lifecycle_deps(tmp_path, child=child)
    deps = replace_deps(deps, getpgid=lambda pid: 9999)

    assert run_fake(["cmd"], receipt, deps) == 3
    body = read_receipt(receipt)
    assert body["cleanup"] == "unavailable", (
        f"'not_required' is untruthful after signals may have flown "
        f"(got {body['cleanup']!r})"
    )


class _Boom(BaseException):
    """A non-KeyboardInterrupt, non-SystemExit BaseException."""


def test_non_interrupt_baseexception_still_publishes_receipt(
    tmp_path: Path,
) -> None:
    """Register LOW: the monitoring-loop handlers caught (KI, SystemExit) and
    Exception; any other BaseException escaped receiptless. It must score
    Inconclusive, contain the owned group, publish, and exit 3."""
    receipt = tmp_path / "base-exc" / "result.json"
    signals: list[tuple[int, int]] = []

    def probe_boom(owned_pgid: int, tracked: frozenset[int]) -> Any:
        raise _Boom("loop-layer failure")

    deps = lifecycle_deps(tmp_path, signals=signals)
    deps = replace_deps(deps, probe=probe_boom)

    assert run_fake(["cmd"], receipt, deps) == 3
    body = read_receipt(receipt)
    assert body["outcome"] == "Inconclusive"
    assert body["code"] == "D6_MONITOR_UNAVAILABLE"
    assert body["cleanup"] in ("complete", "unavailable")


def test_receipt_publication_failure_prints_a_diagnostic(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Register CLEANUP: the blanket BaseException on the receipt path hid
    persistent construction/publication bugs as a silent exit 3. The
    non-interrupt branch now emits one stderr diagnostic (the exit-code
    contract is unchanged)."""
    receipt = tmp_path / "publish-fail" / "result.json"

    def publish_boom(path: Path, payload: dict) -> None:
        raise ValueError("disk said no")

    deps = lifecycle_deps(tmp_path)
    deps = replace_deps(deps, publish=publish_boom)

    assert run_fake(["true"], receipt, deps) == 3
    err = capsys.readouterr().err
    assert "receipt" in err and "disk said no" in err


def test_interrupted_receipt_publication_stays_silent(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Companion pin: the interrupt branch of the receipt path keeps its
    original silent exit-3 contract (a second Ctrl+C must not grow new
    failure surface)."""
    receipt = tmp_path / "publish-interrupt" / "result.json"

    def publish_interrupt(path: Path, payload: dict) -> None:
        raise KeyboardInterrupt

    deps = lifecycle_deps(tmp_path)
    deps = replace_deps(deps, publish=publish_interrupt)

    assert run_fake(["true"], receipt, deps) == 3
    assert capsys.readouterr().err == ""
