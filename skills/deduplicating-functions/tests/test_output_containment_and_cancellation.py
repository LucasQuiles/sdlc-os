"""Behavioral falsifiers for managed publication and abort-safe spawning."""
from __future__ import annotations

import json
import os
import signal
import stat
import sys
import threading
from dataclasses import replace

import pytest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
import run_pipeline as runtime  # noqa: E402


def _api(name):
    value = getattr(runtime, name, None)
    assert value is not None, f"run_pipeline must expose behavioral API {name}"
    return value


def test_managed_run_never_deletes_existing_caller_content(tmp_path):
    root = tmp_path / "managed"
    root.mkdir()
    precious = root / "caller-owned.txt"
    precious.write_text("keep")

    publisher = _api("ManagedRunPublisher")(root, run_id="run-a")
    work = publisher.begin()

    assert precious.read_text() == "keep"
    assert work == root / ".inflight" / "run-a"
    assert work.is_dir()


def test_complete_run_is_atomically_published_without_touching_prior_run(tmp_path):
    root = tmp_path / "managed"
    publisher_type = _api("ManagedRunPublisher")
    first = publisher_type(root, run_id="run-a")
    first_work = first.begin()
    (first_work / "artifact.txt").write_text("one")
    first_path = first.publish_complete({"artifact.txt": "1" * 64})

    second = publisher_type(root, run_id="run-b")
    second_work = second.begin()
    (second_work / "artifact.txt").write_text("two")
    second_path = second.publish_complete({"artifact.txt": "2" * 64})

    pointer = json.loads((root / "latest-complete.json").read_text())
    assert first_path == root / "runs" / "run-a"
    assert second_path == root / "runs" / "run-b"
    assert (first_path / "artifact.txt").read_text() == "one"
    assert pointer["schema_version"] == 1
    assert pointer["run_id"] == "run-b"
    assert pointer["relative_path"] == "runs/run-b"
    assert pointer["outcome"] == "complete"
    assert stat.S_IMODE((root / "latest-complete.json").stat().st_mode) == 0o600
    assert stat.S_IMODE(second_path.stat().st_mode) == 0o700


def test_incomplete_run_never_replaces_latest_pointer(tmp_path):
    root = tmp_path / "managed"
    publisher_type = _api("ManagedRunPublisher")
    complete = publisher_type(root, run_id="good")
    complete.begin()
    complete.publish_complete({})
    before = (root / "latest-complete.json").read_bytes()

    failed = publisher_type(root, run_id="failed")
    failed.begin()
    failed.mark_incomplete("synthetic-failure")

    assert (root / "latest-complete.json").read_bytes() == before
    assert (root / ".inflight" / "failed" / "incomplete.json").is_file()


def test_managed_root_refuses_symlink_and_run_id_collision(tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    link = tmp_path / "link"
    link.symlink_to(target, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        _api("ManagedRunPublisher")(link, run_id="run-a").begin()

    root = tmp_path / "managed"
    publisher_type = _api("ManagedRunPublisher")
    first = publisher_type(root, run_id="same")
    first.begin()
    first.mark_incomplete("fixture")
    with pytest.raises(FileExistsError):
        publisher_type(root, run_id="same").begin()


@pytest.mark.parametrize("broad_root", ["/", os.path.expanduser("~"), "/tmp"])
def test_managed_root_refuses_broad_system_or_home_roots(broad_root):
    with pytest.raises(ValueError, match="too broad"):
        _api("ManagedRunPublisher")(broad_root, run_id="must-not-create").begin()


def test_managed_root_refuses_symlink_ancestor(tmp_path):
    target = tmp_path / "real"
    target.mkdir()
    link = tmp_path / "alias"
    link.symlink_to(target, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink ancestor"):
        _api("ManagedRunPublisher")(link / "nested", run_id="run-a").begin()


def test_pointer_replace_failure_never_changes_previous_latest(tmp_path, monkeypatch):
    publisher_type = _api("ManagedRunPublisher")
    root = tmp_path / "managed"
    first = publisher_type(root, run_id="good")
    first.begin()
    first.publish_complete({})
    before = (root / "latest-complete.json").read_bytes()

    second = publisher_type(root, run_id="new")
    second.begin()
    real_replace = runtime.os.replace

    def fail_pointer(source, destination):
        if os.fspath(destination).endswith("latest-complete.json"):
            raise OSError("synthetic pointer failure")
        return real_replace(source, destination)

    monkeypatch.setattr(runtime.os, "replace", fail_pointer)
    with pytest.raises(OSError, match="synthetic pointer failure"):
        second.publish_complete({})
    assert (root / "latest-complete.json").read_bytes() == before
    assert not (root / "runs" / "new").exists()
    assert (root / ".inflight" / "new" / "incomplete.json").is_file()


def test_pointer_manifest_rejects_unbounded_or_unsafe_artifact_metadata(tmp_path):
    publisher_type = _api("ManagedRunPublisher")
    root = tmp_path / "managed"
    bad_hash = publisher_type(root, run_id="bad-hash")
    bad_hash.begin()
    with pytest.raises(ValueError, match="invalid SHA-256"):
        bad_hash.publish_complete({"artifact.txt": "not-a-digest"})
    bad_hash.mark_incomplete("invalid-artifact-manifest")

    bad_path = publisher_type(root, run_id="bad-path")
    bad_path.begin()
    with pytest.raises(ValueError, match="unsafe artifact"):
        bad_path.publish_complete({"../escape": "0" * 64})
    bad_path.mark_incomplete("invalid-artifact-manifest")
    assert not (root / "latest-complete.json").exists()


def test_preexisting_caller_pointer_is_refused_not_overwritten(tmp_path):
    root = tmp_path / "managed"
    root.mkdir()
    pointer = root / "latest-complete.json"
    pointer.write_text("caller content")
    before = pointer.read_bytes()
    publisher = _api("ManagedRunPublisher")(root, run_id="run-a")
    publisher.begin()
    with pytest.raises(ValueError, match="not tool-owned"):
        publisher.publish_complete({})
    assert pointer.read_bytes() == before
    publisher.mark_incomplete("caller-pointer-refused")


class _FakeProcess:
    def __init__(self, pid: int):
        self.pid = pid
        self.returncode = None

    def poll(self):
        return self.returncode

    def wait(self, timeout=None):
        self.returncode = 0
        return 0

    def communicate(self, timeout=None):
        self.returncode = 0
        return b"", b""


class _FakeBackend:
    def __init__(self, identity):
        self.current = identity
        self.outcome = _api("CensusOutcome").ok({identity.pid: identity})
        self.signals: list[tuple[int, int]] = []

    def census(self, timeout_s: float):
        return self.outcome

    def signal(self, pid: int, sig: int) -> None:
        self.signals.append((pid, sig))
        self.outcome = _api("CensusOutcome").ok(
            {key: value for key, value in self.outcome.table.items() if key != pid})


def _identity(pid: int = 4242):
    return _api("ProcessIdentity")(
        pid=pid, ppid=os.getpid(), uid=os.getuid(), pgid=pid,
        start_token="start-a", ancestor_pid=os.getpid())


def test_abort_latch_and_spawn_share_one_admission_lock():
    identity = _identity()
    backend = _FakeBackend(identity)
    entered = threading.Event()
    release = threading.Event()

    def factory(*args, **kwargs):
        entered.set()
        assert release.wait(2)
        return _FakeProcess(identity.pid)

    coordinator = _api("SpawnCoordinator")(backend=backend, popen_factory=factory)
    spawn_result: list[object] = []
    abort_result: list[object] = []
    spawn_thread = threading.Thread(
        target=lambda: spawn_result.append(coordinator.popen(["fake-detector"])))
    spawn_thread.start()
    assert entered.wait(1)

    abort_thread = threading.Thread(target=lambda: abort_result.append(coordinator.abort()))
    abort_thread.start()
    assert abort_thread.is_alive(), "abort must wait for the in-lock Popen admission"
    release.set()
    spawn_thread.join(2)
    abort_thread.join(2)

    assert len(spawn_result) == 1
    assert abort_result[0].cleanup == "complete"
    assert backend.signals == [(identity.pid, signal.SIGTERM)]


def test_spawn_after_abort_is_rejected_without_invoking_popen():
    identity = _identity()
    backend = _FakeBackend(identity)
    calls = []
    coordinator = _api("SpawnCoordinator")(
        backend=backend,
        popen_factory=lambda *a, **k: calls.append((a, k)),
    )
    coordinator.abort()
    with pytest.raises(_api("AbortInProgress")):
        coordinator.popen(["must-not-spawn"])
    assert calls == []


def test_communication_failure_freezes_admission_and_runs_cleanup():
    identity = _identity()
    backend = _FakeBackend(identity)

    class BrokenCommunication(_FakeProcess):
        def communicate(self, timeout=None):
            raise OSError("synthetic pipe failure")

    coordinator = _api("SpawnCoordinator")(
        backend=backend,
        popen_factory=lambda *a, **k: BrokenCommunication(identity.pid),
    )
    with pytest.raises(OSError, match="synthetic pipe failure"):
        coordinator.run(["fake"])
    assert coordinator.state == "CLOSED"
    assert backend.signals == [(identity.pid, signal.SIGTERM)]


def test_pid_reuse_before_term_suppresses_signal_and_is_uncertain():
    identity = _identity()
    backend = _FakeBackend(identity)
    coordinator = _api("SpawnCoordinator")(
        backend=backend, popen_factory=lambda *a, **k: _FakeProcess(identity.pid))
    coordinator.popen(["fake"])
    backend.outcome = _api("CensusOutcome").ok(
        {identity.pid: replace(identity, start_token="reused")})

    result = coordinator.abort()

    assert result.cleanup == "uncertain"
    assert result.reason == "identity-mismatch"
    assert backend.signals == []


def test_reparenting_before_term_suppresses_signal_and_is_uncertain():
    identity = _identity()
    backend = _FakeBackend(identity)
    coordinator = _api("SpawnCoordinator")(
        backend=backend, popen_factory=lambda *a, **k: _FakeProcess(identity.pid))
    coordinator.popen(["fake"])
    backend.outcome = _api("CensusOutcome").ok(
        {identity.pid: replace(identity, ppid=1)})

    result = coordinator.abort()

    assert result.cleanup == "uncertain"
    assert result.reason == "identity-mismatch"
    assert backend.signals == []


def test_unknown_census_is_never_treated_as_zero_survivors():
    identity = _identity()
    backend = _FakeBackend(identity)
    coordinator = _api("SpawnCoordinator")(
        backend=backend, popen_factory=lambda *a, **k: _FakeProcess(identity.pid))
    coordinator.popen(["fake"])
    backend.outcome = _api("CensusOutcome").unknown("backend-failed")

    result = coordinator.abort()

    assert result.cleanup == "uncertain"
    assert result.reason == "backend-failed"
    assert backend.signals == []


def test_new_descendant_discovered_during_grace_is_not_called_clean():
    root = _identity()
    child = replace(_identity(4343), ppid=root.pid, pgid=root.pgid)

    class BirthBackend(_FakeBackend):
        def signal(self, pid, sig):
            self.signals.append((pid, sig))
            if sig == signal.SIGTERM:
                self.outcome = _api("CensusOutcome").ok({child.pid: child})
            else:
                self.outcome = _api("CensusOutcome").ok({})

    backend = BirthBackend(root)
    coordinator = _api("SpawnCoordinator")(
        backend=backend,
        popen_factory=lambda *a, **k: _FakeProcess(root.pid),
        term_grace_s=0.02,
        poll_s=0.005,
    )
    coordinator.popen(["fake"])

    result = coordinator.abort()

    assert result.cleanup == "complete"
    assert (root.pid, signal.SIGTERM) in backend.signals
    assert (child.pid, signal.SIGKILL) in backend.signals


def test_pid_reuse_immediately_before_kill_suppresses_kill():
    identity = _identity()

    class KillReuseBackend(_FakeBackend):
        def __init__(self, original):
            super().__init__(original)
            self.after_term_censuses = 0
            self.term_seen = False

        def census(self, timeout_s):
            if self.term_seen:
                self.after_term_censuses += 1
                if self.after_term_censuses >= 2:
                    return _api("CensusOutcome").ok(
                        {identity.pid: replace(identity, start_token="reused-before-kill")})
            return self.outcome

        def signal(self, pid, sig):
            self.signals.append((pid, sig))
            if sig == signal.SIGTERM:
                self.term_seen = True

    backend = KillReuseBackend(identity)
    coordinator = _api("SpawnCoordinator")(
        backend=backend,
        popen_factory=lambda *a, **k: _FakeProcess(identity.pid),
        term_grace_s=0.001,
        poll_s=0.01,
    )
    coordinator.popen(["fake"])

    result = coordinator.abort()

    assert result.cleanup == "uncertain"
    assert result.reason == "identity-mismatch"
    assert backend.signals == [(identity.pid, signal.SIGTERM)]


# ── 2026-08-25 round-9 regression tests (findings 1, 2, 4, 5) ─────────────


class _ReapableProcess(_FakeProcess):
    """Fake child that mirrors Popen handle semantics for terminate/kill."""

    def __init__(self, pid: int):
        super().__init__(pid)
        self.terminated = False
        self.killed = False

    def terminate(self):
        self.terminated = True
        self.returncode = -signal.SIGTERM

    def kill(self):
        self.killed = True
        self.returncode = -signal.SIGKILL

    def wait(self, timeout=None):
        if self.returncode is None:
            self.returncode = 0
        return self.returncode


def test_unproven_identity_admission_reaps_the_live_child():
    """Round-9 finding 1: a census that cannot prove the child must not
    abandon it — the direct child is terminated through its own handle."""
    identity = _identity()
    child = _ReapableProcess(identity.pid)
    backend = _FakeBackend(identity)
    backend.outcome = _api("CensusOutcome").unknown("census-timeout")
    coordinator = _api("SpawnCoordinator")(
        backend=backend, popen_factory=lambda *a, **k: child,
        term_grace_s=0.05, poll_s=0.01)

    with pytest.raises(_api("IdentityUnproven")):
        coordinator.popen(["fake-detector"])

    assert child.terminated or child.killed, "unproven live child must be signaled"
    assert child.poll() is not None, "unproven child must be reaped, not abandoned"
    assert coordinator.registered_pids() == ()
    assert coordinator.state == "ABORTING"


def test_foreign_ppid_census_row_is_refused_and_child_reaped():
    """Round-9 finding 4: a census row whose ppid is not this process is a
    reused or raced pid — never register it for later signaling."""
    identity = replace(_identity(), ppid=1)
    child = _ReapableProcess(identity.pid)
    backend = _FakeBackend(identity)
    coordinator = _api("SpawnCoordinator")(
        backend=backend, popen_factory=lambda *a, **k: child,
        term_grace_s=0.05, poll_s=0.01)

    with pytest.raises(_api("IdentityUnproven"), match="ppid-mismatch"):
        coordinator.popen(["fake-detector"])

    assert coordinator.registered_pids() == ()
    assert child.poll() is not None
    assert backend.signals == [], "the foreign census pid must never be signaled"


def test_detector_timeout_cleans_one_child_and_keeps_admission_open():
    """Round-9 finding 2: one slow detector is a per-child failure; the
    coordinator must stay open for later spawns (--permissive contract)."""
    import subprocess as sp

    first = _identity(5050)
    second = _identity(5051)

    class TimeoutProcess(_ReapableProcess):
        def communicate(self, timeout=None):
            raise sp.TimeoutExpired(cmd="slow-detector", timeout=1)

    procs: list[object] = [TimeoutProcess(first.pid)]
    backend = _FakeBackend(first)
    coordinator = _api("SpawnCoordinator")(
        backend=backend, popen_factory=lambda *a, **k: procs.pop(0),
        term_grace_s=0.05, poll_s=0.01)

    with pytest.raises(sp.TimeoutExpired):
        coordinator.run(["slow-detector"])

    assert coordinator.state == "RUNNING", "one timeout must not freeze admission"
    assert (first.pid, signal.SIGTERM) in backend.signals
    assert coordinator.registered_pids() == ()

    backend.outcome = _api("CensusOutcome").ok({second.pid: second})
    procs.append(_FakeProcess(second.pid))
    admitted = coordinator.popen(["next-phase"])
    assert admitted.pid == second.pid, "later phases must still be admitted"


@pytest.mark.parametrize("kwargs", [
    {"term_grace_s": 0}, {"poll_s": 0}, {"census_timeout_s": 0},
    {"term_grace_s": -1.0},
])
def test_nonpositive_timing_construction_is_rejected(kwargs):
    """Round-9 finding 5: zero/negative grace must fail at construction, not
    crash inside cleanup with an unbound survivor set."""
    with pytest.raises(ValueError, match="positive"):
        _api("SpawnCoordinator")(backend=_FakeBackend(_identity()), **kwargs)


@pytest.mark.parametrize("name", ["census_timeout_s", "term_grace_s", "poll_s"])
@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_nonfinite_timing_construction_is_rejected(name, value):
    with pytest.raises(ValueError, match="finite positive"):
        _api("SpawnCoordinator")(
            backend=_FakeBackend(_identity()), **{name: value})


# ── 2026-08-25 preliminary-verification gap closures ──────────────────────


class _UnkillableProcess(_ReapableProcess):
    """Fake child that survives TERM and KILL (wait always times out)."""

    def terminate(self):
        self.terminated = True

    def kill(self):
        self.killed = True

    def wait(self, timeout=None):
        import subprocess as sp
        raise sp.TimeoutExpired(cmd="unkillable", timeout=timeout or 0)


def test_unproven_unkillable_child_is_reported_cleanup_uncertain():
    """Silent return while the child may live is not allowed: the raised
    admission error must disclose the uncertain handle cleanup."""
    identity = _identity()
    child = _UnkillableProcess(identity.pid)
    backend = _FakeBackend(identity)
    backend.outcome = _api("CensusOutcome").unknown("census-timeout")
    coordinator = _api("SpawnCoordinator")(
        backend=backend, popen_factory=lambda *a, **k: child,
        term_grace_s=0.02, poll_s=0.01)

    with pytest.raises(_api("IdentityUnproven"),
                       match="direct-child-cleanup-uncertain"):
        coordinator.popen(["fake-detector"])

    assert child.terminated and child.killed


def test_uncertain_timeout_cleanup_freezes_admission():
    """An uncertain per-child cleanup must escalate to a coordinator abort
    instead of leaving admission open over an uncleaned tree."""
    import subprocess as sp
    identity = _identity(7070)

    class UnkillableTimeout(_UnkillableProcess):
        def communicate(self, timeout=None):
            raise sp.TimeoutExpired(cmd="slow-detector", timeout=1)

    backend = _FakeBackend(identity)
    coordinator = _api("SpawnCoordinator")(
        backend=backend,
        popen_factory=lambda *a, **k: UnkillableTimeout(identity.pid),
        term_grace_s=0.02, poll_s=0.005)

    with pytest.raises(sp.TimeoutExpired):
        coordinator.run(["slow-detector"])

    assert coordinator.state in ("ABORTING", "CLOSED")
    with pytest.raises(_api("AbortInProgress")):
        coordinator.popen(["must-not-spawn"])


def test_detector_timeout_leaves_concurrent_child_untouched():
    """The scoped cleanup must not signal or unregister an unrelated
    concurrently running child."""
    import subprocess as sp
    slow = _identity(6060)
    steady = _identity(6061)

    class TimeoutProcess(_ReapableProcess):
        def communicate(self, timeout=None):
            raise sp.TimeoutExpired(cmd="slow-detector", timeout=1)

    backend = _FakeBackend(slow)
    backend.outcome = _api("CensusOutcome").ok({slow.pid: slow, steady.pid: steady})
    procs: list[object] = [_FakeProcess(steady.pid), TimeoutProcess(slow.pid)]
    coordinator = _api("SpawnCoordinator")(
        backend=backend, popen_factory=lambda *a, **k: procs.pop(0),
        term_grace_s=0.05, poll_s=0.01)

    coordinator.popen(["steady-detector"])
    with pytest.raises(sp.TimeoutExpired):
        coordinator.run(["slow-detector"])

    assert coordinator.state == "RUNNING"
    assert steady.pid in coordinator.registered_pids()
    assert (steady.pid, signal.SIGTERM) not in backend.signals
    assert (steady.pid, signal.SIGKILL) not in backend.signals
    assert (slow.pid, signal.SIGTERM) in backend.signals


def test_dead_child_with_census_row_is_returned_unregistered():
    """A child that already exited is never registered, even when a census
    row for its pid exists (zombie or reused pid)."""
    identity = _identity()
    dead = _FakeProcess(identity.pid)
    dead.returncode = 0
    backend = _FakeBackend(identity)
    coordinator = _api("SpawnCoordinator")(
        backend=backend, popen_factory=lambda *a, **k: dead,
        term_grace_s=0.05, poll_s=0.01)

    result = coordinator.popen(["fast-exit"])

    assert result is dead
    assert coordinator.registered_pids() == ()
    assert coordinator.state == "RUNNING"
