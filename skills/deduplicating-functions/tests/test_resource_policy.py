"""Contract tests for scripts/lib/resource_policy.py — finite caps, process-tree
watchdog, and run.json accounting used by run_pipeline.py.

Invariant I3: every ceiling is finite; an override may only move it to another
finite value. Invariant I1: the watchdog signals only processes proven to be
descendants of the owning pid at signal time.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
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
    assert pol.mode in ("refuse", "truncate")


@pytest.mark.parametrize("field,value", [("max_pairs", 0), ("max_pairs", -1), ("max_wall_seconds", 0),
                                         ("max_tree_rss_bytes", 0)])
def test_non_finite_override_rejected(field, value):
    with pytest.raises(rp.PolicyError):
        rp.ResourcePolicy.defaults().with_overrides(**{field: value})


def test_override_to_larger_finite_value_allowed():
    pol = rp.ResourcePolicy.defaults().with_overrides(max_pairs=10)
    assert pol.max_pairs == 10
    d = pol.to_dict()
    assert d["max_pairs"] == 10 and d["mode"] in ("refuse", "truncate")


def test_descendants_walk_uses_parent_chain():
    table = {  # pid -> (ppid, rss_kb)
        1: (0, 10), 100: (1, 100), 200: (100, 50), 201: (100, 60), 300: (200, 70),
        400: (1, 999),  # unrelated
    }
    desc = rp.descendants_from_table(100, table)
    assert set(desc) == {200, 201, 300}
    assert rp.tree_rss_bytes_from_table(100, table) == (100 + 50 + 60 + 70) * 1024


def test_watchdog_aborts_tree_over_rss_cap(tmp_path):
    """Spawn a child that allocates ~150 MB; cap at 64 MB; watchdog must kill it,
    record resource_abort, and never touch unrelated pids."""
    child = subprocess.Popen(
        [sys.executable, "-c",
         "import time; b = bytearray(150*1024*1024); b[::4096] = b'x'*len(b[::4096]); time.sleep(30)"],
        start_new_session=True,
    )
    events = []
    wd = rp.TreeWatchdog(root_pid=os.getpid(), max_tree_rss_bytes=64 * 1024 * 1024,
                         max_wall_seconds=600, interval_s=0.2, on_abort=events.append,
                         owned_pids=lambda: [child.pid])
    wd.start()
    try:
        deadline = time.monotonic() + 15
        while child.poll() is None and time.monotonic() < deadline:
            time.sleep(0.1)
        assert child.poll() is not None, "watchdog did not terminate the over-cap child"
        assert events and events[0]["reason"] == "max_tree_rss_bytes"
        assert events[0]["peak_tree_rss_bytes"] > 64 * 1024 * 1024
        assert child.pid in events[0]["signaled_pids"]
    finally:
        wd.stop()
        if child.poll() is None:
            child.kill()


def test_watchdog_aborts_on_wall_clock(tmp_path):
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"], start_new_session=True)
    events = []
    wd = rp.TreeWatchdog(root_pid=os.getpid(), max_tree_rss_bytes=8 << 30, max_wall_seconds=1,
                         interval_s=0.2, on_abort=events.append, owned_pids=lambda: [child.pid])
    wd.start()
    try:
        deadline = time.monotonic() + 10
        while child.poll() is None and time.monotonic() < deadline:
            time.sleep(0.1)
        assert child.poll() is not None
        assert events[0]["reason"] == "max_wall_seconds"
    finally:
        wd.stop()
        if child.poll() is None:
            child.kill()


def test_watchdog_never_signals_non_descendant(monkeypatch):
    """If the table says a pid is not our descendant at signal time, it is skipped."""
    signaled = []
    monkeypatch.setattr(rp.os, "kill", lambda pid, sig: signaled.append((pid, sig)))
    table = {1: (0, 1), os.getpid(): (1, 1), 5555: (1, 999999)}
    monkeypatch.setattr(rp, "_sample_table", lambda: table)
    wd = rp.TreeWatchdog(root_pid=os.getpid(), max_tree_rss_bytes=1, max_wall_seconds=600,
                         interval_s=0.1, on_abort=lambda e: None, owned_pids=lambda: [5555])
    res = wd._abort("max_tree_rss_bytes", table)
    assert res["signaled_pids"] == []
    assert signaled == []
    assert res["skipped_unowned_pids"] == [5555]


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
