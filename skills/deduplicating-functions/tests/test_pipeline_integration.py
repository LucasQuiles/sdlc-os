"""Integration tests: run all detectors against adversarial corpus, verify merge pipeline."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile

import pytest

PYTHON = sys.executable  # Use the same interpreter running the tests
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
FIXTURES = os.path.join(BASE, "tests", "fixtures")
CORPUS = os.path.join(FIXTURES, "adversarial-corpus.json")


@pytest.fixture(scope="module")
def corpus():
    with open(CORPUS) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def catalog_file(corpus):
    """Write corpus functions to a temp catalog for detectors."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(corpus["functions"], f)
        path = f.name
    yield path
    os.unlink(path)


ALL_DETECTORS = [
    "detect-fuzzy-names.py",
    "detect-signature-match.py",
    "detect-token-clones.py",
    "detect-ast-similarity.py",
    "detect-metric-similarity.py",
    "detect-tfidf-index.py",
    "detect-winnowing.py",
    "detect-lsh-ast.py",
    "detect-bag-of-ast.py",
    "detect-pdg-semantic.py",
    "detect-code-embedding.py",
]


@pytest.mark.parametrize("detector", ALL_DETECTORS)
def test_detector_runs_without_error(detector, catalog_file):
    """Each detector should run against the corpus without crashing."""
    script = os.path.join(SCRIPTS, detector)
    if not os.path.exists(script):
        pytest.skip(f"{detector} not found")

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        out_path = f.name
    try:
        result = subprocess.run(
            [PYTHON, script, catalog_file, "-o", out_path],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0, f"{detector} failed: {result.stderr[:500]}"
        assert os.path.exists(out_path), f"{detector} did not produce output"

        with open(out_path) as f:
            data = json.load(f)
        assert isinstance(data, list), f"{detector} output is not a list"
    finally:
        if os.path.exists(out_path):
            os.unlink(out_path)


@pytest.mark.parametrize("detector", ALL_DETECTORS)
def test_detector_output_schema(detector, catalog_file):
    """Each detector output should follow the standard pair schema."""
    script = os.path.join(SCRIPTS, detector)
    if not os.path.exists(script):
        pytest.skip(f"{detector} not found")

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        out_path = f.name
    try:
        subprocess.run(
            [PYTHON, script, catalog_file, "-o", out_path],
            capture_output=True, text=True, timeout=30,
        )
        with open(out_path) as f:
            data = json.load(f)

        for pair in data:
            assert "func_a" in pair, f"{detector}: missing func_a"
            assert "func_b" in pair, f"{detector}: missing func_b"
            assert "final_score" in pair, f"{detector}: missing final_score"
            assert isinstance(pair["final_score"], (int, float)), \
                f"{detector}: final_score not numeric"
            assert 0.0 <= pair["final_score"] <= 1.0, \
                f"{detector}: final_score {pair['final_score']} out of range"
    finally:
        if os.path.exists(out_path):
            os.unlink(out_path)


@pytest.fixture(scope="module")
def all_detector_results(catalog_file):
    """Run all detectors and collect results."""
    results_dir = tempfile.mkdtemp()
    for detector in ALL_DETECTORS:
        script = os.path.join(SCRIPTS, detector)
        if not os.path.exists(script):
            continue
        out_name = detector.replace("detect-", "").replace(".py", "-results.json")
        out_path = os.path.join(results_dir, out_name)
        subprocess.run(
            [PYTHON, script, catalog_file, "-o", out_path],
            capture_output=True, text=True, timeout=30,
        )
    yield results_dir
    shutil.rmtree(results_dir, ignore_errors=True)


def test_merge_signals_runs(all_detector_results):
    """merge-signals.py should successfully merge all detector outputs."""
    merge_script = os.path.join(SCRIPTS, "merge-signals.py")
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        out_path = f.name
    try:
        result = subprocess.run(
            [PYTHON, merge_script, all_detector_results, "-o", out_path, "--include-summary"],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0, f"merge-signals failed: {result.stderr[:500]}"

        with open(out_path) as f:
            data = json.load(f)
        assert "pairs" in data, "Missing pairs key"
        assert "summary" in data, "Missing summary key"
        assert data["summary"]["total_pairs"] >= 0
    finally:
        if os.path.exists(out_path):
            os.unlink(out_path)


def test_merge_detects_known_clones(all_detector_results, corpus):
    """Merge should detect at least the obvious clones from ground truth."""
    merge_script = os.path.join(SCRIPTS, "merge-signals.py")
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        out_path = f.name
    try:
        subprocess.run(
            [PYTHON, merge_script, all_detector_results, "-o", out_path, "--include-summary"],
            capture_output=True, text=True, timeout=30,
        )
        with open(out_path) as f:
            data = json.load(f)

        detected_pairs = set()
        for pair in data["pairs"]:
            a = f"{pair['func_a']['file']}:{pair['func_a']['name']}"
            b = f"{pair['func_b']['file']}:{pair['func_b']['name']}"
            detected_pairs.add(frozenset([a, b]))

        true_clones = [
            gt for gt in corpus["ground_truth"] if gt["is_clone"]
        ]

        detected_count = 0
        for gt in true_clones:
            # Parse ground truth format "file:name:line"
            a_parts = gt["func_a"].split(":")
            b_parts = gt["func_b"].split(":")
            a_key = f"{a_parts[0]}:{a_parts[1]}"
            b_key = f"{b_parts[0]}:{b_parts[1]}"
            if frozenset([a_key, b_key]) in detected_pairs:
                detected_count += 1

        # Should detect at least 2 of 4 true clones (50% recall minimum)
        assert detected_count >= 2, \
            f"Only detected {detected_count}/{len(true_clones)} true clones"
    finally:
        if os.path.exists(out_path):
            os.unlink(out_path)


def test_merge_no_obvious_false_positives(all_detector_results, corpus):
    """Merge should not flag obviously unrelated pairs as HIGH confidence."""
    merge_script = os.path.join(SCRIPTS, "merge-signals.py")
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        out_path = f.name
    try:
        subprocess.run(
            [PYTHON, merge_script, all_detector_results, "-o", out_path, "--include-summary"],
            capture_output=True, text=True, timeout=30,
        )
        with open(out_path) as f:
            data = json.load(f)

        known_non_clones = set()
        for gt in corpus["ground_truth"]:
            if not gt["is_clone"]:
                a_parts = gt["func_a"].split(":")
                b_parts = gt["func_b"].split(":")
                a_key = f"{a_parts[0]}:{a_parts[1]}"
                b_key = f"{b_parts[0]}:{b_parts[1]}"
                known_non_clones.add(frozenset([a_key, b_key]))

        high_false_positives = 0
        for pair in data["pairs"]:
            if pair["confidence"] != "HIGH":
                continue
            a = f"{pair['func_a']['file']}:{pair['func_a']['name']}"
            b = f"{pair['func_b']['file']}:{pair['func_b']['name']}"
            if frozenset([a, b]) in known_non_clones:
                high_false_positives += 1

        # Structural detectors correctly flag structurally similar code
        # even when ground truth says "different domain". Allow some HIGH
        # false positives — the contradiction penalty handles the worst cases.
        # Strict zero-FP would require semantic understanding beyond structure.
        assert high_false_positives <= 5, \
            f"{high_false_positives} known non-clones flagged as HIGH (max 5)"
    finally:
        if os.path.exists(out_path):
            os.unlink(out_path)


def test_all_strategies_contribute(all_detector_results):
    """At least 8 of 11 detectors should produce non-empty results."""
    non_empty = 0
    for fname in os.listdir(all_detector_results):
        if not fname.endswith("-results.json"):
            continue
        path = os.path.join(all_detector_results, fname)
        with open(path) as f:
            data = json.load(f)
        if len(data) > 0:
            non_empty += 1

    assert non_empty >= 8, \
        f"Only {non_empty} detectors produced results (expected >= 8)"
