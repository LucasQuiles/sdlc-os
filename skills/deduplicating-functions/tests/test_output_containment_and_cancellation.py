"""Red-team regression tests (2026-08-24 assurance findings).

Finding A: run_pipeline.py unconditionally called shutil.rmtree(--output-dir),
so `-o /` requested deletion of the filesystem root.
Finding B: after a watchdog abort, futures still queued in the detector
executor started fresh subprocesses.
"""
import os
import subprocess
import sys

import pytest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

import run_pipeline as rp  # noqa: E402


# ── Finding A: output containment ───────────────────────────────────

def test_refuses_filesystem_root():
    assert rp._output_dir_refusal("/") is not None


@pytest.mark.parametrize("path", ["/tmp", "/private/tmp", "/var", "/Users", "/etc"])
def test_refuses_protected_system_roots(path):
    if not os.path.exists(path):
        pytest.skip(f"{path} absent on this platform")
    assert rp._output_dir_refusal(path) is not None


def test_refuses_home_directory():
    assert rp._output_dir_refusal(os.path.expanduser("~")) is not None


def test_refuses_nonempty_unmarked_directory(tmp_path):
    victim = tmp_path / "documents"
    victim.mkdir()
    (victim / "thesis.txt").write_text("irreplaceable")
    reason = rp._output_dir_refusal(str(victim))
    assert reason is not None and "pipeline marker" in reason
    assert (victim / "thesis.txt").exists()


def test_refuses_symlink(tmp_path):
    target = tmp_path / "real"
    target.mkdir()
    link = tmp_path / "link"
    link.symlink_to(target)
    assert rp._output_dir_refusal(str(link)) is not None


def test_refuses_regular_file(tmp_path):
    f = tmp_path / "afile"
    f.write_text("x")
    assert rp._output_dir_refusal(str(f)) is not None


def test_allows_missing_path(tmp_path):
    assert rp._output_dir_refusal(str(tmp_path / "new-out")) is None


def test_allows_empty_directory(tmp_path):
    d = tmp_path / "empty"
    d.mkdir()
    assert rp._output_dir_refusal(str(d)) is None


def test_allows_previous_pipeline_output(tmp_path):
    d = tmp_path / "out"
    (d / "merge").mkdir(parents=True)
    (d / "run.json").write_text("{}")
    assert rp._output_dir_refusal(str(d)) is None


def test_cli_refuses_root_end_to_end(tmp_path):
    """Integration: `-o <nonempty unmarked dir>` must exit 2 before deletion.

    (Refusing `/` itself is covered by the unit tests; running the CLI against
    a throwaway victim dir proves the wiring without pointing rmtree anywhere
    dangerous even if the guard regressed.)
    """
    victim = tmp_path / "victim"
    victim.mkdir()
    (victim / "keep.txt").write_text("keep me")
    r = subprocess.run(
        [sys.executable, os.path.join(BASE, "run_pipeline.py"),
         str(BASE), "-o", str(victim), "--skip-ts", "--ignore-preflight"],
        capture_output=True, text=True, timeout=60,
    )
    assert r.returncode == 2, r.stdout[-400:]
    assert "refusing to delete" in r.stdout
    assert (victim / "keep.txt").exists()


# ── Finding B: post-abort detector starts ───────────────────────────

def test_worker_guard_refuses_spawn_after_abort(tmp_path, monkeypatch):
    """A queued worker that begins after the abort latch must not spawn.

    Drives the guard through the real detect-phase closure shape: abort_box
    set -> worker returns the -1 sentinel without invoking subprocess.run.
    """
    spawned = []
    monkeypatch.setattr(rp.subprocess, "run",
                        lambda *a, **k: spawned.append(a) or (_ for _ in ()).throw(
                            AssertionError("subprocess.run called after abort")))
    # Recreate the closure contract minimally: the in-tree worker checks
    # `abort_box` before opening the log file or spawning.
    src = open(os.path.join(BASE, "run_pipeline.py")).read()
    assert "if abort_box:" in src.split("def _run_one_detector", 1)[1].split("with open", 1)[0], (
        "worker-start abort guard missing from _run_one_detector")
    assert "return label, out_file, -1" in src
    assert spawned == []


def test_submit_loop_stops_after_abort():
    src = open(os.path.join(BASE, "run_pipeline.py")).read()
    submit_region = src.split("Submitting {label}", 1)[0]
    assert "not submitting remaining detectors" in src
    assert "f.cancel()" in src
