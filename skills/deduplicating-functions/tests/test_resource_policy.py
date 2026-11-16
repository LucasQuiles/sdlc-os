"""Contract tests for scripts/lib/resource_policy.py — finite caps, process-tree
watchdog, and run.json accounting used by run_pipeline.py.

Invariant I3: every ceiling is finite; an override may only move it to another
finite value. Invariant I1: the watchdog signals only processes proven to be
descendants of the owning pid at signal time.
"""
from __future__ import annotations

import json
import os
import sys
import threading
import time
from pathlib import Path

import pytest

_LIB = Path(__file__).parent.parent / "scripts" / "lib"
sys.path.insert(0, str(_LIB))
import resource_policy as rp  # noqa: E402


def test_defaults_are_finite_and_documented():
    pol = rp.ResourcePolicy.defaults()
    for name in ("max_input_bytes", "max_pairs", "max_report_rows", "max_output_bytes",
                 "max_wall_seconds", "max_tree_rss_bytes", "max_legacy_json_bytes"):
        v = getattr(pol, name)
        assert isinstance(v, int) and v > 0, name
    assert pol.max_run_output_bytes > 0
    assert pol.max_tree_processes > 0
    assert pol.mode in ("refuse", "truncate")


@pytest.mark.parametrize("field,value", [("max_pairs", 0), ("max_pairs", -1), ("max_wall_seconds", 0),
                                         ("max_tree_rss_bytes", 0)])
def test_non_finite_override_rejected(field, value):
    with pytest.raises(rp.PolicyError):
        rp.ResourcePolicy.defaults().with_overrides(**{field: value})


def test_override_may_lower_but_never_raise_an_immutable_hard_cap():
    pol = rp.ResourcePolicy.defaults().with_overrides(max_pairs=10)
    assert pol.max_pairs == 10
    d = pol.to_dict()
    assert d["max_pairs"] == 10 and d["mode"] in ("refuse", "truncate")
    defaults = rp.ResourcePolicy.defaults()
    for field in defaults._INT_FIELDS:
        with pytest.raises(rp.PolicyError, match="immutable hard cap"):
            defaults.with_overrides(**{field: getattr(defaults, field) + 1})


def test_descendants_walk_uses_parent_chain():
    table = {  # pid -> (ppid, rss_kb)
        1: (0, 10), 100: (1, 100), 200: (100, 50), 201: (100, 60), 300: (200, 70),
        400: (1, 999),  # unrelated
    }
    desc = rp.descendants_from_table(100, table)
    assert set(desc) == {200, 201, 300}
    assert rp.tree_rss_bytes_from_table(100, table) == (100 + 50 + 60 + 70) * 1024


def test_watchdog_delegates_cleanup_over_rss_cap(monkeypatch):
    """The sampler trips; only the identity coordinator callback may actuate."""
    from types import SimpleNamespace
    events = []
    cleanup_reasons = []
    table = {os.getpid(): (1, 100_000)}
    monkeypatch.setattr(rp, "_sample_table", lambda: table)
    wd = rp.TreeWatchdog(root_pid=os.getpid(), max_tree_rss_bytes=64 * 1024 * 1024,
                         max_wall_seconds=600, interval_s=0.2, on_abort=events.append,
                         cleanup_handler=lambda reason: cleanup_reasons.append(reason) or
                         SimpleNamespace(cleanup="complete", reason=reason, term_pids=(4242,),
                                         kill_pids=(), survivors=()))
    wd.start()
    try:
        deadline = time.monotonic() + 15
        while not events and time.monotonic() < deadline:
            threading.Event().wait(0.1)
        assert events and events[0]["reason"] == "max_tree_rss_bytes"
        assert events[0]["peak_tree_rss_bytes"] > 64 * 1024 * 1024
        assert events[0]["signaled_pids"] == [4242]
        assert cleanup_reasons == ["max_tree_rss_bytes"]
    finally:
        wd.stop()


def test_watchdog_aborts_on_wall_clock():
    from types import SimpleNamespace
    events = []
    wd = rp.TreeWatchdog(root_pid=os.getpid(), max_tree_rss_bytes=8 << 30, max_wall_seconds=1,
                         interval_s=0.2, on_abort=events.append,
                         cleanup_handler=lambda reason: SimpleNamespace(
                             cleanup="complete", reason=reason, term_pids=(), kill_pids=(),
                             survivors=()))
    wd.start()
    try:
        deadline = time.monotonic() + 10
        while not events and time.monotonic() < deadline:
            threading.Event().wait(0.1)
        assert events[0]["reason"] == "max_wall_seconds"
    finally:
        wd.stop()


def test_watchdog_never_signals_non_descendant(monkeypatch):
    """If the table says a pid is not our descendant at signal time, it is skipped."""
    signaled = []
    monkeypatch.setattr(rp.os, "kill", lambda pid, sig: signaled.append((pid, sig)))
    table = {1: (0, 1), os.getpid(): (1, 1), 5555: (1, 999999)}
    monkeypatch.setattr(rp, "_sample_table", lambda: table)
    calls = []
    wd = rp.TreeWatchdog(root_pid=os.getpid(), max_tree_rss_bytes=1, max_wall_seconds=600,
                         interval_s=0.1, on_abort=lambda e: None,
                         cleanup_handler=lambda reason: calls.append(reason))
    res = wd._abort("max_tree_rss_bytes", table)
    assert signaled == []
    assert calls == ["max_tree_rss_bytes"]
    assert res["cleanup"] == "uncertain"


def test_watchdog_sampler_failure_aborts_instead_of_continuing(monkeypatch):
    from types import SimpleNamespace
    events = []
    monkeypatch.setattr(
        rp, "_sample_table", lambda: (_ for _ in ()).throw(rp.PolicyError("ps failed")))
    wd = rp.TreeWatchdog(
        root_pid=os.getpid(), max_tree_rss_bytes=8 << 30, max_wall_seconds=600,
        interval_s=0.01, on_abort=events.append,
        cleanup_handler=lambda reason: SimpleNamespace(
            cleanup="uncertain", reason=reason, term_pids=(), kill_pids=(), survivors=()),
    )
    wd.start()
    wd._thread.join(timeout=1)
    assert events and events[0]["reason"] == "sampler-unavailable"
    assert events[0]["cleanup"] == "uncertain"


def test_watchdog_aborts_when_aggregate_run_output_exceeds_hard_cap(tmp_path, monkeypatch):
    from types import SimpleNamespace
    events = []
    (tmp_path / "large.bin").write_bytes(b"xx")
    monkeypatch.setattr(rp, "_sample_table", lambda: {os.getpid(): (1, 1)})
    wd = rp.TreeWatchdog(
        root_pid=os.getpid(), max_tree_rss_bytes=8 << 30, max_wall_seconds=600,
        interval_s=0.01, on_abort=events.append,
        cleanup_handler=lambda reason: SimpleNamespace(
            cleanup="complete", reason=reason, term_pids=(), kill_pids=(), survivors=()),
        output_root=str(tmp_path), max_run_output_bytes=1,
    )
    wd.start()
    wd._thread.join(timeout=1)
    assert events and events[0]["reason"] == "max_run_output_bytes"
    assert events[0]["cleanup"] == "complete"


def test_watchdog_aborts_when_process_tree_exceeds_hard_cap(monkeypatch):
    from types import SimpleNamespace
    events = []
    root = os.getpid()
    monkeypatch.setattr(
        rp, "_sample_table", lambda: {root: (1, 1), root + 1: (root, 1)})
    wd = rp.TreeWatchdog(
        root_pid=root, max_tree_rss_bytes=8 << 30, max_wall_seconds=600,
        max_tree_processes=1, interval_s=0.01, on_abort=events.append,
        cleanup_handler=lambda reason: SimpleNamespace(
            cleanup="complete", reason=reason, term_pids=(), kill_pids=(), survivors=()),
    )
    wd.start()
    wd._thread.join(timeout=1)
    assert events and events[0]["reason"] == "max_tree_processes"


def test_peak_sampler_reports_rss_not_footprint():
    s = rp.sample_tree(os.getpid())
    assert s["rss_bytes"] >= 0
    assert "footprint_bytes" in s and s["footprint_status"] in ("unavailable", "ok")
    if s["footprint_status"] == "unavailable":
        assert s["footprint_bytes"] is None


def test_run_record_roundtrip(tmp_path):
    rec = rp.RunRecord.start(policy=rp.ResourcePolicy.defaults(), base_dir=str(tmp_path))
    rec.note_phase("merge", {"candidates_seen": 3})
    rec.finish(outcome="complete", artifacts={"pairs.jsonl": str(tmp_path / "p.jsonl")})
    p = tmp_path / "run.json"
    (tmp_path / "p.jsonl").write_text("{}\n")
    rec.write(str(p))
    d = json.loads(p.read_text())
    assert d["outcome"] == "complete"
    assert d["policy"]["max_pairs"] > 0
    assert d["phases"]["merge"]["candidates_seen"] == 3
    assert d["artifacts"]["pairs.jsonl"]["sha256"]
    assert d["started_utc"].endswith("Z") and d["ended_utc"].endswith("Z")


# ── 2026-08-25 round-9 regression tests (finding 3) ───────────────────────


def test_output_sampler_tolerates_entry_vanishing_mid_scan(tmp_path, monkeypatch):
    """Round-9 finding 3: the atomic-replacement pattern (write temp,
    os.replace) deletes listed entries between scandir and stat; one ENOENT
    must count as zero bytes for the sample, not become a resource abort."""
    (tmp_path / "merge.tmp").write_bytes(b"x" * 128)
    (tmp_path / "kept.bin").write_bytes(b"y" * 64)
    real_scandir = os.scandir

    class _Proxy:
        def __init__(self, entry, vanished):
            self._entry = entry
            self._vanished = vanished

        @property
        def path(self):
            return self._entry.path

        def is_symlink(self):
            return self._entry.is_symlink()

        def is_dir(self, follow_symlinks=True):
            return False if self._vanished else self._entry.is_dir(
                follow_symlinks=follow_symlinks)

        def is_file(self, follow_symlinks=True):
            return True if self._vanished else self._entry.is_file(
                follow_symlinks=follow_symlinks)

        def stat(self, follow_symlinks=True):
            if self._vanished:
                raise FileNotFoundError(self.path)
            return self._entry.stat(follow_symlinks=follow_symlinks)

    class _Scan:
        def __init__(self, path):
            self._inner = real_scandir(path)

        def __iter__(self):
            return (_Proxy(e, e.name == "merge.tmp") for e in self._inner)

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            self._inner.close()
            return False

    monkeypatch.setattr(rp.os, "scandir", _Scan)
    assert rp._output_tree_bytes(str(tmp_path)) == 64


def test_output_sampler_tolerates_directory_vanishing_mid_scan(tmp_path):
    """A queued subdirectory that disappears before its own scandir is a
    vanished entry, not a probe failure."""
    survivor = tmp_path / "kept.bin"
    survivor.write_bytes(b"y" * 32)
    ghost = tmp_path / "ghost-dir"
    ghost.mkdir()
    real_scandir = os.scandir

    def racing_scandir(path):
        if os.path.abspath(str(path)) == str(ghost):
            raise FileNotFoundError(str(path))
        return real_scandir(path)

    import unittest.mock as mock
    with mock.patch.object(rp.os, "scandir", racing_scandir):
        assert rp._output_tree_bytes(str(tmp_path)) == 32


def test_output_sampler_still_refuses_symlinks(tmp_path):
    """ENOENT tolerance must not weaken the symlink refusal."""
    real = tmp_path / "real.bin"
    real.write_bytes(b"z")
    (tmp_path / "link").symlink_to(real)
    with pytest.raises(rp.PolicyError, match="symlink"):
        rp._output_tree_bytes(str(tmp_path))


def test_output_sampler_fails_when_root_itself_vanishes(tmp_path):
    """ENOENT tolerance covers listed entries only; a missing output root is
    a probe failure, never zero bytes."""
    with pytest.raises(rp.PolicyError, match="output root missing"):
        rp._output_tree_bytes(str(tmp_path / "never-existed"))
