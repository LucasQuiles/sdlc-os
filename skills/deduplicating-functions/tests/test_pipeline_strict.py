"""Regression tests for run_pipeline.py --strict gating and determinism.

These tests invoke run_pipeline.py as a subprocess against a small,
repo-local corpus, so they are slow relative to the unit tests but
exercise the end-to-end CLI behavior.

Parallel safety: every test that mutates scripts/ (e.g. simulating a
missing script) operates on a per-test isolated copy of the repo via
the `isolated_repo` fixture, so tests cannot race each other under
parallel execution (pytest-xdist).
"""
from __future__ import annotations

import filecmp
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

import pytest

PYTHON = sys.executable
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNNER = os.path.join(BASE, "run_pipeline.py")
SCRIPTS_DIR = os.path.join(BASE, "scripts")


def _run_pipeline(
    out_dir: str,
    *extra_args: str,
    env: dict | None = None,
    runner: str | None = None,
    source: str | None = None,
):
    """Invoke run_pipeline.py against scripts/ as the corpus.

    `runner` and `source` default to the live repo paths. Pass explicit
    paths (e.g. from the isolated_repo fixture) to run against a snapshot.
    """
    cmd = [
        PYTHON,
        runner or RUNNER,
        source or SCRIPTS_DIR,
        "-o", out_dir,
        *extra_args,
    ]
    return subprocess.run(
        cmd, capture_output=True, text=True, timeout=180, env=env
    )


# Match ISO-ish timestamps YYYY-MM-DD HH:MM and HH:MM(:SS)? anywhere in text.
_TS_RE = re.compile(
    r"\b\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(?::\d{2})?\b"
    r"|\b\d{2}:\d{2}(?::\d{2})?\b"
)


def _strip_nondeterministic(out_dir: str) -> None:
    """Remove/scrub files that legitimately differ across runs.

    - pipeline.log contains wall-clock timestamps and absolute paths.
    - duplicates-report.md embeds "Generated: YYYY-MM-DD HH:MM" from
      generate-report-enhanced.sh, which can cross a minute boundary
      between two runs in the same test.
    """
    log = os.path.join(out_dir, "pipeline.log")
    if os.path.exists(log):
        os.unlink(log)

    report = os.path.join(out_dir, "duplicates-report.md")
    if os.path.exists(report):
        with open(report) as f:
            content = f.read()
        scrubbed = _TS_RE.sub("<TS>", content)
        with open(report, "w") as f:
            f.write(scrubbed)


@pytest.fixture
def clean_tmpdir():
    d = tempfile.mkdtemp(prefix="dupdetect-strict-")
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def isolated_repo(tmp_path):
    """Per-test snapshot of scripts/, run_pipeline.py, and test fixtures.

    Returns a namespace with .runner, .scripts, .source, .fixtures paths.
    Tests that need to mutate scripts/ (simulate missing files) should
    operate on this snapshot, NOT on the live repo, to remain parallel-safe.
    """
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    # Copy scripts/ (includes lib/, which the detectors import)
    shutil.copytree(SCRIPTS_DIR, str(repo_root / "scripts"))

    # Copy run_pipeline.py
    shutil.copy(RUNNER, str(repo_root / "run_pipeline.py"))

    # Copy test fixtures for --eval-corpus tests
    src_fixtures = os.path.join(BASE, "tests", "fixtures")
    if os.path.exists(src_fixtures):
        shutil.copytree(src_fixtures, str(repo_root / "tests" / "fixtures"))

    class _Repo:
        runner = str(repo_root / "run_pipeline.py")
        scripts = str(repo_root / "scripts")
        source = str(repo_root / "scripts")  # corpus == scripts/ for baseline
        fixtures = str(repo_root / "tests" / "fixtures")

    return _Repo()


def test_strict_success_with_full_environment(clean_tmpdir):
    """--strict should exit 0 when all phases succeed."""
    result = _run_pipeline(clean_tmpdir, "--strict")
    assert result.returncode == 0, (
        f"--strict failed with full environment: {result.stdout[-500:]}"
    )
    # Verify key outputs exist
    assert os.path.exists(os.path.join(clean_tmpdir, "merge", "merged-results.json"))
    assert os.path.exists(os.path.join(clean_tmpdir, "duplicates-report.md"))


def test_strict_fails_on_missing_merge_script(clean_tmpdir, isolated_repo):
    """--strict should exit 2 if merge-signals.py is missing.

    Uses isolated_repo snapshot so the live scripts/ is untouched
    and this test is safe to run in parallel with others.

    Passes --skip-ts because the snapshot does not include node_modules/
    and we want to exercise the merge gate, not the TS extraction gate.
    """
    os.unlink(os.path.join(isolated_repo.scripts, "merge-signals.py"))
    result = _run_pipeline(
        clean_tmpdir, "--strict", "--skip-ts",
        runner=isolated_repo.runner, source=isolated_repo.source,
    )
    assert result.returncode == 2, (
        f"Expected exit 2 when merge missing, got {result.returncode}\n"
        f"stdout: {result.stdout[-500:]}"
    )
    # Confirm it was the merge phase, not an earlier phase, that tripped
    assert "phase 2: merge" in result.stdout.lower()
    assert "merge phase failed" in result.stdout.lower()


def test_strict_fails_on_missing_report_script(clean_tmpdir, isolated_repo):
    """--strict should exit 2 if generate-report-enhanced.sh is missing."""
    os.unlink(os.path.join(isolated_repo.scripts, "generate-report-enhanced.sh"))
    result = _run_pipeline(
        clean_tmpdir, "--strict", "--skip-ts",
        runner=isolated_repo.runner, source=isolated_repo.source,
    )
    assert result.returncode == 2, (
        f"Expected exit 2 when report missing, got {result.returncode}\n"
        f"stdout: {result.stdout[-500:]}"
    )
    assert "phase 3: report" in result.stdout.lower()
    assert "report generator missing" in result.stdout.lower()


def test_strict_fails_when_node_missing(clean_tmpdir, tmp_path):
    """--strict should exit 2 with the TS-extraction gate message when node
    is not on PATH.

    Uses a shim PATH that contains python3 but not node, so the only
    discoverable difference from a normal run is the missing node
    binary. This lets us assert the exact gate message instead of just
    "exited nonzero somehow".
    """
    shim_dir = tmp_path / "shimbin-no-node"
    shim_dir.mkdir()
    (shim_dir / "python3").symlink_to(PYTHON)
    env = os.environ.copy()
    env["PATH"] = f"{shim_dir}:/usr/bin:/bin"

    # Sanity: node must NOT be resolvable from this PATH
    if shutil.which("node", path=env["PATH"]):
        pytest.skip("node still on PATH after shim construction")
    # Sanity: python3 must still be resolvable (the shim provides it)
    assert shutil.which("python3", path=env["PATH"]), \
        "shim PATH should expose python3"

    result = _run_pipeline(clean_tmpdir, "--strict", env=env)

    assert result.returncode == 2, (
        f"Expected exit 2 when node missing, got {result.returncode}\n"
        f"stdout: {result.stdout[-500:]}\n"
        f"stderr: {result.stderr[-500:]}"
    )
    # Confirm it was the phase-0 extraction gate that fired, specifically
    # on ast-ts-extraction for the node-missing reason.
    out = result.stdout.lower()
    assert "phase 0: extract" in out
    assert "ast-ts-extraction (node not on path)" in out
    assert "extraction step(s) failed or skipped" in out


def test_strict_succeeds_on_python_only_repo_without_node(clean_tmpdir, tmp_path):
    """--strict should NOT fail on a pure Python repo when node is missing.

    The TS extraction gate should only fire when the source tree contains
    TS/JS files. A repo with only .py files should pass strict mode even
    if node is absent.
    """
    # Create a Python-only source directory
    py_src = tmp_path / "pysrc"
    py_src.mkdir()
    (py_src / "sample.py").write_text("def hello():\n    return 'hi'\n")

    # Shim PATH without node
    shim_dir = tmp_path / "shimbin-pyonly"
    shim_dir.mkdir()
    (shim_dir / "python3").symlink_to(PYTHON)
    env = os.environ.copy()
    env["PATH"] = f"{shim_dir}:/usr/bin:/bin"

    if shutil.which("node", path=env["PATH"]):
        pytest.skip("node still on PATH")

    result = _run_pipeline(
        clean_tmpdir, "--strict",
        source=str(py_src), env=env,
    )
    assert result.returncode == 0, (
        f"Strict on Python-only repo should not require node.\n"
        f"stdout: {result.stdout[-500:]}"
    )


def test_skip_ts_allows_strict_without_node(clean_tmpdir, tmp_path):
    """--skip-ts --strict should succeed even without node (intentional opt-out)."""
    # Create a shim PATH that contains python3 but NOT node.
    # We do this by creating a new directory with just a python3 symlink.
    shim_dir = tmp_path / "shimbin"
    shim_dir.mkdir()
    (shim_dir / "python3").symlink_to(PYTHON)
    # bash and node-absent; python3 is the only thing in PATH that
    # matters for the runner.
    env = os.environ.copy()
    env["PATH"] = f"{shim_dir}:/usr/bin:/bin"

    # Sanity: node must NOT be resolvable from this PATH
    if shutil.which("node", path=env["PATH"]):
        pytest.skip("node still on PATH after shim construction")

    result = _run_pipeline(clean_tmpdir, "--strict", "--skip-ts", env=env)
    assert result.returncode == 0, (
        f"--skip-ts --strict failed: {result.stdout[-500:]}\n"
        f"stderr: {result.stderr[-500:]}"
    )


def test_default_mode_tolerates_failures(clean_tmpdir, isolated_repo):
    """Without --strict, missing merge script should still exit 0 (permissive).

    Uses --skip-ts to avoid a TS-extraction failure dominating the signal
    (the snapshot does not include node_modules/).
    """
    os.unlink(os.path.join(isolated_repo.scripts, "merge-signals.py"))
    result = _run_pipeline(
        clean_tmpdir, "--skip-ts",
        runner=isolated_repo.runner, source=isolated_repo.source,
    )
    # Permissive default: exit 0 even though merge failed
    assert result.returncode == 0, (
        f"Default mode should tolerate failures, got exit {result.returncode}"
    )


def test_pipeline_is_byte_deterministic():
    """Two successive runs must produce byte-identical output (excluding log)."""
    with tempfile.TemporaryDirectory(prefix="dupdet-det1-") as d1, \
         tempfile.TemporaryDirectory(prefix="dupdet-det2-") as d2:
        r1 = _run_pipeline(d1, "--strict")
        r2 = _run_pipeline(d2, "--strict")
        assert r1.returncode == 0, f"Run 1 failed: {r1.stdout[-500:]}"
        assert r2.returncode == 0, f"Run 2 failed: {r2.stdout[-500:]}"

        _strip_nondeterministic(d1)
        _strip_nondeterministic(d2)

        # Compare all files recursively
        diff = filecmp.dircmp(d1, d2)
        assert not diff.diff_files, (
            f"Non-deterministic output: {diff.diff_files}"
        )
        assert not diff.left_only, f"Only in run 1: {diff.left_only}"
        assert not diff.right_only, f"Only in run 2: {diff.right_only}"

        # Recurse into subdirs
        def _check_subdirs(dcmp):
            assert not dcmp.diff_files, (
                f"Non-deterministic in {dcmp.left}: {dcmp.diff_files}"
            )
            for sub in dcmp.subdirs.values():
                _check_subdirs(sub)

        _check_subdirs(diff)


def test_pipeline_matches_checked_in_baseline(clean_tmpdir):
    """Strict run against scripts/ must byte-match the checked-in merge baseline.

    Any drift in pair contents, ordering, scoring, or strategy attribution
    is a regression, not just a count mismatch.
    """
    checked_in = os.path.join(BASE, "output", "merge", "merged-results.json")
    if not os.path.exists(checked_in):
        pytest.skip("No checked-in baseline to compare against")

    result = _run_pipeline(clean_tmpdir, "--strict")
    assert result.returncode == 0, f"Strict run failed: {result.stdout[-500:]}"

    fresh = os.path.join(clean_tmpdir, "merge", "merged-results.json")
    assert os.path.exists(fresh), "Fresh run produced no merge output"

    # Full deep equality — catches drift in pair contents, ordering, scores
    with open(checked_in) as f:
        baseline = json.load(f)
    with open(fresh) as f:
        current = json.load(f)

    # Start with summary for clear error messages on common drift cases
    baseline_summary = baseline.get("summary", {})
    current_summary = current.get("summary", {})
    assert baseline_summary == current_summary, (
        f"Summary drift:\n"
        f"  baseline: {baseline_summary}\n"
        f"  current:  {current_summary}"
    )

    # Then full pair list — catches reordering, score drift, content changes
    baseline_pairs = baseline.get("pairs", [])
    current_pairs = current.get("pairs", [])
    assert len(baseline_pairs) == len(current_pairs), (
        f"Pair count drift: baseline {len(baseline_pairs)} vs current {len(current_pairs)}"
    )

    # Per-pair comparison to pinpoint first drift on failure
    for i, (b, c) in enumerate(zip(baseline_pairs, current_pairs)):
        assert b == c, (
            f"Pair {i} drift:\n"
            f"  baseline: {json.dumps(b, sort_keys=True)[:300]}\n"
            f"  current:  {json.dumps(c, sort_keys=True)[:300]}"
        )

    # Final byte-level check on the merged JSON structure
    assert baseline == current, "Baseline drift in non-pair merge fields"

    # Also verify all per-detector output files match
    for detector_file in os.listdir(os.path.join(BASE, "output", "detect")):
        if not detector_file.endswith("-results.json"):
            continue
        baseline_det = os.path.join(BASE, "output", "detect", detector_file)
        current_det = os.path.join(clean_tmpdir, "detect", detector_file)
        assert os.path.exists(current_det), f"Missing {detector_file} in fresh run"
        with open(baseline_det) as f:
            b_data = json.load(f)
        with open(current_det) as f:
            c_data = json.load(f)
        assert b_data == c_data, (
            f"{detector_file} drift: "
            f"baseline has {len(b_data)} pairs, current has {len(c_data)}"
        )


# ─── Phase 4 (evaluate) strict coverage ────────────────────────────

ADVERSARIAL_CORPUS = os.path.join(BASE, "tests", "fixtures", "adversarial-corpus.json")


def test_strict_eval_success_with_valid_corpus(clean_tmpdir):
    """--strict --eval-corpus should exit 0 when evaluation runs cleanly."""
    if not os.path.exists(ADVERSARIAL_CORPUS):
        pytest.skip("adversarial-corpus.json fixture missing")

    result = _run_pipeline(
        clean_tmpdir, "--strict", "--eval-corpus", ADVERSARIAL_CORPUS
    )
    assert result.returncode == 0, (
        f"--strict --eval-corpus failed: {result.stdout[-500:]}"
    )
    eval_out = os.path.join(clean_tmpdir, "evaluation.json")
    assert os.path.exists(eval_out), "Evaluation phase produced no output"

    # Verify evaluation.json has the expected shape
    with open(eval_out) as f:
        ev = json.load(f)
    assert "overall" in ev, "evaluation.json missing 'overall' block"
    for key in ("precision", "recall", "f1"):
        assert key in ev["overall"], f"overall block missing {key}"
        assert isinstance(ev["overall"][key], (int, float)), f"{key} not numeric"


def test_strict_eval_fails_on_missing_corpus(clean_tmpdir, tmp_path):
    """--strict --eval-corpus with a nonexistent corpus should exit 2."""
    missing_corpus = str(tmp_path / "does-not-exist.json")
    result = _run_pipeline(
        clean_tmpdir, "--strict", "--eval-corpus", missing_corpus
    )
    # evaluate.py itself will exit non-zero when corpus is unreadable,
    # and --strict should propagate that.
    assert result.returncode == 2, (
        f"Expected exit 2 for missing eval corpus, got {result.returncode}\n"
        f"stdout: {result.stdout[-500:]}"
    )


def test_strict_eval_fails_when_evaluate_script_missing(clean_tmpdir, isolated_repo):
    """--strict --eval-corpus should exit 2 if evaluate.py is missing."""
    os.unlink(os.path.join(isolated_repo.scripts, "evaluate.py"))
    result = _run_pipeline(
        clean_tmpdir, "--strict", "--skip-ts",
        "--eval-corpus", ADVERSARIAL_CORPUS,
        runner=isolated_repo.runner, source=isolated_repo.source,
    )
    assert result.returncode == 2, (
        f"Expected exit 2 when evaluate.py missing, got {result.returncode}\n"
        f"stdout: {result.stdout[-500:]}"
    )
    assert "phase 4: evaluate" in result.stdout.lower()


def test_default_mode_tolerates_eval_failure(clean_tmpdir, tmp_path):
    """Without --strict, missing eval corpus should not fail the pipeline."""
    missing_corpus = str(tmp_path / "does-not-exist.json")
    result = _run_pipeline(clean_tmpdir, "--eval-corpus", missing_corpus)
    # Permissive default: exit 0 even with evaluation failures
    assert result.returncode == 0, (
        f"Default mode should tolerate eval failures, got exit {result.returncode}"
    )


# ─── --from-corpus regression tests ────────────────────────────────

def _run_from_corpus(out_dir: str, corpus: str, *extra_args: str):
    """Invoke run_pipeline.py in corpus mode (no source positional arg)."""
    cmd = [
        PYTHON, RUNNER,
        "--from-corpus", corpus,
        "-o", out_dir,
        *extra_args,
    ]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=180)


def test_from_corpus_mode_runs_without_source(clean_tmpdir):
    """--from-corpus should work without a source positional argument."""
    if not os.path.exists(ADVERSARIAL_CORPUS):
        pytest.skip("adversarial-corpus.json fixture missing")
    result = _run_from_corpus(clean_tmpdir, ADVERSARIAL_CORPUS, "--strict")
    assert result.returncode == 0, (
        f"--from-corpus failed: {result.stdout[-500:]}"
    )
    # Should have loaded functions from corpus
    assert "loading functions from corpus" in result.stdout.lower()


def test_from_corpus_produces_real_eval_metrics(clean_tmpdir):
    """--from-corpus + --eval-corpus should produce non-zero recall.

    The adversarial corpus has 4 true clones. A pipeline that actually
    runs detectors on corpus functions should catch at least one.
    """
    if not os.path.exists(ADVERSARIAL_CORPUS):
        pytest.skip("adversarial-corpus.json fixture missing")

    result = _run_from_corpus(
        clean_tmpdir,
        ADVERSARIAL_CORPUS,
        "--eval-corpus", ADVERSARIAL_CORPUS,
        "--strict",
    )
    assert result.returncode == 0, (
        f"--from-corpus --eval-corpus failed: {result.stdout[-500:]}"
    )

    eval_out = os.path.join(clean_tmpdir, "evaluation.json")
    assert os.path.exists(eval_out), "Evaluation phase produced no output"
    with open(eval_out) as f:
        ev = json.load(f)
    overall = ev["overall"]

    # Regression guard: previously eval signal was broken (0/0/0). The
    # pipeline must now detect at least one true clone from the corpus.
    assert overall["tp"] >= 1, (
        f"Eval signal regression: tp={overall['tp']}, "
        f"summary={ev['summary']}"
    )
    assert overall["recall"] > 0.0, (
        f"Eval signal regression: recall={overall['recall']}, "
        f"summary={ev['summary']}"
    )


def test_from_corpus_mode_skips_extraction_phase(clean_tmpdir):
    """In --from-corpus mode, no extractor scripts should be invoked.

    The catalog should come from the corpus file, not from extraction.
    Verify by checking that no per-extractor catalog files are produced.
    """
    if not os.path.exists(ADVERSARIAL_CORPUS):
        pytest.skip("adversarial-corpus.json fixture missing")

    result = _run_from_corpus(clean_tmpdir, ADVERSARIAL_CORPUS, "--strict")
    assert result.returncode == 0

    extract_dir = os.path.join(clean_tmpdir, "extract")
    # Only catalog-corpus.json and catalog-unified.json should exist
    files = sorted(os.listdir(extract_dir))
    assert "catalog-corpus.json" in files, f"Missing catalog-corpus.json: {files}"
    assert "catalog-unified.json" in files, f"Missing catalog-unified.json: {files}"
    # No extractor-specific catalogs in corpus mode
    assert "catalog-regex.json" not in files, "Regex extractor should not run in corpus mode"
    assert "catalog-ast-py.json" not in files, "Python AST should not run in corpus mode"
    assert "catalog-ast-ts.json" not in files, "TS AST should not run in corpus mode"


def test_missing_source_and_corpus_errors(clean_tmpdir):
    """Running with neither positional source nor --from-corpus should fail."""
    cmd = [PYTHON, RUNNER, "-o", clean_tmpdir]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    assert result.returncode != 0, (
        "Expected non-zero exit when no source given"
    )
    assert "source" in result.stderr.lower() or "corpus" in result.stderr.lower()


# ─── Scalability smoke tests ───────────────────────────────────────

def _synthesize_corpus(n_functions: int, tmp_path) -> str:
    """Generate a synthetic corpus of N functions with realistic structure.

    Half the functions share a common template (to exercise the detectors),
    half are unique. Each has token_sequence, params, complexity metrics,
    and ast_fingerprint — everything the detectors need.
    """
    functions = []
    common_tokens = [
        "FunctionDef", "arguments", "arg", "arg", "If", "Compare",
        "Name", "Constant", "Return", "BinOp", "Name", "Mult", "Name",
    ]
    for i in range(n_functions):
        is_common = i % 2 == 0
        if is_common:
            tokens = common_tokens + [f"Constant_{i % 5}"]
            fingerprint = f"common_{i % 5}"
        else:
            tokens = ["FunctionDef"] + [f"Token_{i}_{j}" for j in range(12)]
            fingerprint = f"unique_{i}"
        functions.append({
            "name": f"func_{i}",
            "file": f"module_{i // 10}.py",
            "line": (i % 100) * 10 + 1,
            "qualified_name": f"module_{i // 10}.func_{i}",
            "token_sequence": tokens,
            "body_lines": 5 + (i % 10),
            "params": [
                {"name": "x", "type": "int"},
                {"name": "y", "type": "int"},
            ],
            "return_type": "int",
            "cyclomatic_complexity": 2 + (i % 3),
            "ast_fingerprint": fingerprint,
            "language": "python",
        })
    corpus = {"functions": functions, "ground_truth": []}
    corpus_path = str(tmp_path / f"synthetic-{n_functions}.json")
    with open(corpus_path, "w") as f:
        json.dump(corpus, f)
    return corpus_path


def test_pipeline_handles_500_function_corpus(clean_tmpdir, tmp_path):
    """Regression guard: pipeline must complete on a 500-function corpus.

    O(n²) pair generation could produce up to ~125k candidate pairs.
    This test verifies the pipeline doesn't crash, hang, or OOM at
    that scale. Timeout is 180s (same as other pipeline tests).
    """
    corpus_path = _synthesize_corpus(500, tmp_path)
    result = _run_from_corpus(clean_tmpdir, corpus_path, "--strict")
    assert result.returncode == 0, (
        f"500-function corpus failed: {result.stdout[-500:]}\n"
        f"stderr: {result.stderr[-500:]}"
    )
    # Sanity check: merged output exists and is non-empty
    merged = os.path.join(clean_tmpdir, "merge", "merged-results.json")
    assert os.path.exists(merged)
    with open(merged) as f:
        data = json.load(f)
    # 250 common-template functions × shared fingerprints → many pairs
    assert data["summary"]["total_pairs"] > 0


def test_pipeline_completes_under_runtime_budget(clean_tmpdir, tmp_path):
    """Runtime regression guard: 200 functions should complete in <60s.

    This is a loose budget — actual runtime on modern hardware is
    a few seconds. The budget catches order-of-magnitude regressions
    (e.g. accidentally quadratic loops inside what should be linear).
    """
    import time
    corpus_path = _synthesize_corpus(200, tmp_path)
    start = time.monotonic()
    result = _run_from_corpus(clean_tmpdir, corpus_path, "--strict")
    elapsed = time.monotonic() - start
    assert result.returncode == 0, f"200-function run failed: {result.stdout[-500:]}"
    assert elapsed < 60.0, (
        f"Pipeline took {elapsed:.1f}s on 200 functions (budget: 60s). "
        f"Possible O(n^k) regression."
    )
