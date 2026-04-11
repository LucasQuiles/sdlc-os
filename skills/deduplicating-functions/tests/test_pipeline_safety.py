"""Safety tests for run_pipeline.py — lockfile, jobs cap, preflight."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import threading
import time

import pytest

PYTHON = sys.executable
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNNER = os.path.join(BASE, "run_pipeline.py")
SCRIPTS_DIR = os.path.join(BASE, "scripts")


@pytest.fixture
def clean_tmpdir():
    with tempfile.TemporaryDirectory(prefix="dupdetect-safety-") as d:
        yield d


@pytest.fixture
def isolated_lock(tmp_path):
    """Provide a per-test lock path so tests don't collide with the user's real lock."""
    return str(tmp_path / "run_pipeline.lock")


def test_second_run_blocks_when_lock_held(clean_tmpdir, tmp_path, isolated_lock):
    """A second run_pipeline.py invocation must exit non-zero with a clear
    lock-conflict message while the first is still running."""
    out1 = str(tmp_path / "out1")
    out2 = str(tmp_path / "out2")

    # Start a long-ish first run in the background
    proc1 = subprocess.Popen(
        [PYTHON, RUNNER, SCRIPTS_DIR, "-o", out1,
         "--lock-file", isolated_lock, "--skip-ts"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    try:
        # Wait for proc1 to actually acquire the lock — poll the lock file
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline and not os.path.exists(isolated_lock):
            time.sleep(0.05)
        assert os.path.exists(isolated_lock), "First run never created lock file"

        # Now try a second run — should fail fast
        result2 = subprocess.run(
            [PYTHON, RUNNER, SCRIPTS_DIR, "-o", out2,
             "--lock-file", isolated_lock, "--skip-ts"],
            capture_output=True, text=True, timeout=15,
        )
        assert result2.returncode == 1, (
            f"Second run should exit 1 on lock conflict, got {result2.returncode}\n"
            f"stdout: {result2.stdout[-300:]}\nstderr: {result2.stderr[-300:]}"
        )
        assert "another run_pipeline.py" in result2.stdout.lower() or \
               "another run_pipeline.py" in result2.stderr.lower(), \
            "Lock conflict message missing"
    finally:
        proc1.terminate()
        proc1.wait(timeout=10)


def test_wait_flag_blocks_until_first_run_completes(clean_tmpdir, tmp_path, isolated_lock):
    """--wait should block instead of failing fast when the lock is held."""
    out1 = str(tmp_path / "out1")
    out2 = str(tmp_path / "out2")

    proc1 = subprocess.Popen(
        [PYTHON, RUNNER, SCRIPTS_DIR, "-o", out1,
         "--lock-file", isolated_lock, "--skip-ts"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    try:
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline and not os.path.exists(isolated_lock):
            time.sleep(0.05)
        assert os.path.exists(isolated_lock)

        # Start the waiter in a thread so we can observe it not exiting
        result_holder = {}
        def _runner():
            result_holder["res"] = subprocess.run(
                [PYTHON, RUNNER, SCRIPTS_DIR, "-o", out2,
                 "--lock-file", isolated_lock, "--skip-ts", "--wait"],
                capture_output=True, text=True, timeout=180,
            )
        t = threading.Thread(target=_runner, daemon=True)
        t.start()

        # The waiter should be blocked while proc1 is alive
        time.sleep(1.0)
        assert t.is_alive(), "--wait should block while first run holds the lock"

        # Let proc1 finish naturally — the waiter should then proceed
        proc1.wait(timeout=180)
        t.join(timeout=180)
        assert "res" in result_holder, "--wait runner never finished"
        assert result_holder["res"].returncode == 0, (
            f"Waiter run failed: {result_holder['res'].stdout[-300:]}"
        )
    finally:
        if proc1.poll() is None:
            proc1.terminate()
            proc1.wait(timeout=10)
