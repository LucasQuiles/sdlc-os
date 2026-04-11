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

        # Give the waiter thread a generous second to start, attempt lock
        # acquisition, and block on flock. 1.0s is deliberately generous:
        # a slow Python startup under CI load could delay the subprocess
        # launch, and we want "alive after 1s" to genuinely mean "blocked
        # on the lock" rather than "hasn't started yet".
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


import json


def test_jobs_cap_limits_concurrent_detector_processes(clean_tmpdir, tmp_path):
    """With --jobs=2, no more than 2 detector subprocesses should run at once.

    We probe this by polling pgrep for detect-*.py processes during the run.
    """
    samples = []
    stop = threading.Event()

    def _sampler():
        while not stop.is_set():
            try:
                out = subprocess.check_output(
                    ["pgrep", "-fl", "detect-.*\\.py"], text=True,
                    stderr=subprocess.DEVNULL,
                )
                count = sum(1 for line in out.splitlines() if "detect-" in line)
                samples.append(count)
            except subprocess.CalledProcessError:
                samples.append(0)
            time.sleep(0.05)

    sampler = threading.Thread(target=_sampler, daemon=True)
    sampler.start()
    try:
        result = subprocess.run(
            [PYTHON, RUNNER, SCRIPTS_DIR, "-o", clean_tmpdir,
             "--skip-ts", "--jobs", "2",
             "--lock-file", str(tmp_path / "lock")],
            capture_output=True, text=True, timeout=180,
        )
    finally:
        stop.set()
        sampler.join(timeout=2)

    assert result.returncode == 0, f"Pipeline failed: {result.stdout[-500:]}"
    # We may sample 0 between phases, but we must NEVER sample > 2
    peak = max(samples) if samples else 0
    assert peak <= 2, (
        f"--jobs=2 should cap concurrent detectors at 2, observed peak={peak}\n"
        f"sample distribution: {sorted(set(samples))}"
    )
    # Sanity: we should have observed at least one detector running at
    # some point. If peak is 0, the sampler was too slow for this machine
    # — skip rather than fail, because "too fast to observe" is not a
    # safety failure.
    if peak < 1:
        pytest.skip(
            f"Sampler never saw a detector running (peak=0). "
            f"Environment is likely too fast for the 50ms sampling interval, "
            f"or pgrep is unavailable. samples count={len(samples)}"
        )


def test_resolve_jobs_priority_order(monkeypatch):
    """CLI > env var > default."""
    # Import here so the test fails clearly if the helper is missing
    sys.path.insert(0, BASE)
    import run_pipeline  # noqa: E402
    sys.path.pop(0)

    monkeypatch.delenv("SDLC_OS_DETECTOR_JOBS", raising=False)
    default = run_pipeline._resolve_jobs(None)
    assert 1 <= default <= 4, f"Default {default} should be in [1, 4]"

    monkeypatch.setenv("SDLC_OS_DETECTOR_JOBS", "7")
    assert run_pipeline._resolve_jobs(None) == 7

    # CLI overrides env
    assert run_pipeline._resolve_jobs(2) == 2

    # Garbage env falls through to default
    monkeypatch.setenv("SDLC_OS_DETECTOR_JOBS", "garbage")
    assert run_pipeline._resolve_jobs(None) == default


SHIM_SAFETY_PY = (
    "import os\n"
    "import fcntl\n"
    "DEFAULT_LOCK_PATH = os.path.expanduser('~/.cache/sdlc-os/run_pipeline.lock')\n"
    "DEFAULT_MIN_FREE_RAM_GB = 4.0\n"
    "DEFAULT_MAX_SWAPFILES = 5\n"
    "def check_preflight(*a, **kw):\n"
    "    return False, 'synthetic test refusal'\n"
    "def acquire_pipeline_lock(lock_path, wait):\n"
    "    parent = os.path.dirname(lock_path) or '.'\n"
    "    os.makedirs(parent, exist_ok=True)\n"
    "    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o644)\n"
    "    flags = fcntl.LOCK_EX if wait else (fcntl.LOCK_EX | fcntl.LOCK_NB)\n"
    "    try:\n"
    "        fcntl.flock(fd, flags)\n"
    "    except BlockingIOError:\n"
    "        os.close(fd); raise\n"
    "    return fd\n"
)


def _make_shim_runner(tmp_path):
    """Copy run_pipeline.py into a temp dir and drop the shim safety.py beside it.

    Because Python adds the script's own directory to sys.path[0], placing
    the shim safety.py next to the runner ensures it shadows the real one.
    """
    import shutil as _shutil
    runner_dir = tmp_path / "runner"
    runner_dir.mkdir()
    shim_runner = str(runner_dir / "run_pipeline.py")
    _shutil.copy(RUNNER, shim_runner)
    (runner_dir / "safety.py").write_text(SHIM_SAFETY_PY)
    return shim_runner


def test_preflight_refusal_blocks_pipeline_launch(clean_tmpdir, tmp_path):
    """When preflight reports unsafe, the pipeline must exit 1 before launching detectors."""
    shim_runner = _make_shim_runner(tmp_path)

    result = subprocess.run(
        [PYTHON, shim_runner, SCRIPTS_DIR, "-o", clean_tmpdir,
         "--skip-ts", "--lock-file", str(tmp_path / "lock")],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 1, (
        f"Expected exit 1 from preflight refusal, got {result.returncode}\n"
        f"stdout: {result.stdout[-500:]}"
    )
    assert "preflight refused launch" in result.stdout.lower()
    assert "synthetic test refusal" in result.stdout.lower()


def test_ignore_preflight_bypasses_check(clean_tmpdir, tmp_path):
    """--ignore-preflight should run the pipeline even when preflight would refuse."""
    shim_runner = _make_shim_runner(tmp_path)

    result = subprocess.run(
        [PYTHON, shim_runner, SCRIPTS_DIR, "-o", clean_tmpdir,
         "--skip-ts", "--ignore-preflight",
         "--lock-file", str(tmp_path / "lock")],
        capture_output=True, text=True, timeout=180,
    )
    assert result.returncode == 0, (
        f"--ignore-preflight should bypass refusal, got {result.returncode}\n"
        f"stdout: {result.stdout[-500:]}"
    )
    assert "bypassed via --ignore-preflight" in result.stdout.lower()
