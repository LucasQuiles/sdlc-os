"""Contract tests for run_pipeline.py resource policy integration (plan P1 §6.2–6.4).

- finite ceilings are CLI-configurable and validated;
- the runner never loads the merged document (reads merge/summary.json);
- run.json records policy, phases, counts, peak tree RSS, outcome, artifacts;
- refuse/truncate semantics surface with exit code 3 / explicit truncation;
- the process-tree watchdog aborts the run (exit 3, outcome resource_abort).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from pipeline_test_support import latest_run, only_attempt

BASE = Path(__file__).parent.parent
RUNNER = BASE / "run_pipeline.py"
FIXTURES = BASE / "tests" / "fixtures"
CORPUS = FIXTURES / "eval-corpus.json"
PY = sys.executable
ADAPTER = FIXTURES / "run_pipeline_test_adapter.py"


def _run(out: Path, tmp_path: Path, *args: str, timeout: int = 240) -> subprocess.CompletedProcess:
    return subprocess.run(
        [PY, str(ADAPTER), str(RUNNER), "--from-corpus", str(CORPUS), "-o", str(out),
         "--test-lock-file", str(tmp_path / "lock"), *args],
        capture_output=True, text=True, timeout=timeout,
    )


@pytest.fixture(scope="module")
def baseline_run(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("base")
    out = tmp / "out"
    r = _run(out, tmp, "--strict")
    assert r.returncode == 0, r.stdout[-800:] + r.stderr[-800:]
    return latest_run(out)


def test_runner_source_never_loads_merged_document():
    src = RUNNER.read_text()
    assert "merged = json.load" not in src
    assert "summary.json" in src


def test_run_json_contract(baseline_run):
    run = json.loads((baseline_run / "run.json").read_text())
    assert run["outcome"] == "complete"
    for phase in ("extract", "detect", "merge", "report"):
        assert phase in run["phases"], phase
    assert run["policy"]["max_pairs"] > 0 and run["policy"]["mode"] in ("refuse", "truncate")
    assert run["peak"]["rss_bytes"] > 0
    assert run["peak"]["footprint_status"] in ("unavailable", "ok")
    assert run["artifacts"]["pairs.jsonl"]["sha256"]
    assert run["artifacts"]["summary.json"]["sha256"]
    assert run["artifacts"]["duplicates-report.md"]["sha256"]
    assert run["published_relative_path"] == f"runs/{run['managed_run_id']}"
    for artifact in run["artifacts"].values():
        assert not Path(artifact["path"]).is_absolute()
        if artifact.get("present"):
            assert (baseline_run / artifact["path"]).is_file()
    assert run["started_utc"].endswith("Z") and run["ended_utc"].endswith("Z")
    assert (baseline_run / "merge" / "summary.json").exists()
    assert (baseline_run / "merge" / "pairs.jsonl").exists()
    assert (baseline_run / "merge" / "merged-results.json").exists(), "small runs keep the legacy file"


def test_stdout_reports_counts_from_summary_json(baseline_run, tmp_path):
    out = tmp_path / "out"
    r = _run(out, tmp_path, "--strict")
    assert r.returncode == 0
    summary = json.loads((latest_run(out) / "merge" / "summary.json").read_text())
    assert f"{summary['total_pairs']} pairs:" in r.stdout


@pytest.mark.parametrize("flag,value", [("--max-pairs", "0"), ("--max-wall-seconds", "-5"),
                                        ("--max-tree-rss-bytes", "0"), ("--max-report-rows", "x")])
def test_non_finite_ceiling_rejected(tmp_path, flag, value):
    r = _run(tmp_path / "out", tmp_path, flag, value, timeout=60)
    assert r.returncode == 2, (r.returncode, r.stderr[-300:])
    assert "finite" in (r.stderr + r.stdout).lower()


def test_refuse_policy_exit_3_no_report(tmp_path):
    out = tmp_path / "out"
    r = _run(out, tmp_path, "--max-pairs", "1", "--resource-policy", "refuse")
    assert r.returncode == 3, r.stdout[-800:]
    assert "REFUSED_RESOURCE" in (r.stdout + r.stderr)
    attempt = only_attempt(out)
    assert not (attempt / "duplicates-report.md").exists()
    run = json.loads((attempt / "run.json").read_text())
    assert run["outcome"] == "refused_resource"


def test_truncate_policy_records_truncation(tmp_path):
    out = tmp_path / "out"
    r = _run(out, tmp_path, "--max-pairs", "1", "--resource-policy", "truncate")
    assert r.returncode == 0, r.stdout[-800:]
    run_dir = latest_run(out)
    summary = json.loads((run_dir / "merge" / "summary.json").read_text())
    assert summary["total_pairs"] == 1 and summary["complete"] is False
    run = json.loads((run_dir / "run.json").read_text())
    assert run["truncated"] is True and run["truncation_reason"]
    assert "TRUNCATED" in r.stdout
    assert (run_dir / "duplicates-report.md").exists()


def test_report_rows_cap_forwarded(tmp_path):
    out = tmp_path / "out"
    r = _run(out, tmp_path, "--max-report-rows", "1")
    assert r.returncode == 0, r.stdout[-800:]
    md = (latest_run(out) / "duplicates-report.md").read_text()
    assert "omitted (cap 1)" in md


def test_watchdog_abort_exit_3(tmp_path):
    """A 1-byte tree ceiling trips on the runner itself: exit 3, outcome resource_abort,
    no success artifacts, the abort event recorded."""
    out = tmp_path / "out"
    r = _run(out, tmp_path, "--max-tree-rss-bytes", "1")
    assert r.returncode == 3, (r.returncode, r.stdout[-800:])
    attempt = only_attempt(out)
    run = json.loads((attempt / "run.json").read_text())
    assert run["outcome"] == "resource_abort"
    assert run["abort"]["reason"] == "max_tree_rss_bytes"
    assert run["abort"]["cleanup"] == "complete"
    assert not (attempt / "duplicates-report.md").exists()


def test_missing_resource_policy_module_is_strict_failure(tmp_path):
    """A missing policy/watchdog module must fail in every semantic mode."""
    import shutil
    runner_dir = tmp_path / "runner"
    runner_dir.mkdir()
    shutil.copy(RUNNER, runner_dir / "run_pipeline.py")
    shutil.copy(BASE / "safety.py", runner_dir / "safety.py")
    shutil.copy(BASE / "pipeline_runtime.py", runner_dir / "pipeline_runtime.py")
    r = subprocess.run([PY, str(ADAPTER), str(runner_dir / "run_pipeline.py"),
                        "--from-corpus", str(CORPUS), "-o", str(tmp_path / "out"),
                        "--test-lock-file", str(tmp_path / "lock")],
                       capture_output=True, text=True, timeout=120)
    assert r.returncode == 2
    assert "resource policy" in r.stdout.lower()

    permissive = subprocess.run(
        [PY, str(ADAPTER), str(runner_dir / "run_pipeline.py"),
         "--from-corpus", str(CORPUS), "-o", str(tmp_path / "permissive-out"),
         "--test-lock-file", str(tmp_path / "permissive-lock"), "--permissive"],
        capture_output=True, text=True, timeout=120,
    )
    assert permissive.returncode == 2
    assert "resource policy" in permissive.stdout.lower()


@pytest.mark.parametrize("value", ["0", "301", "unbounded"])
def test_detector_timeout_environment_cannot_disable_or_raise_hard_cap(
    tmp_path, monkeypatch, value
):
    monkeypatch.setenv("DEDUP_DETECTOR_TIMEOUT_S", value)
    r = _run(tmp_path / "out", tmp_path, timeout=60)
    assert r.returncode == 2
    assert "detector_timeout" in (r.stdout + r.stderr).lower()
