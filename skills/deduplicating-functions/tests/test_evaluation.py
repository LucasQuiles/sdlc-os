#!/usr/bin/env python3
# ABOUTME: Tests for the evaluation harness and corpus generator.
# Covers precision/recall/F1 computation, ground truth loading, and corpus generation.

"""Tests for evaluate.py and generate-corpus.py."""

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

# ── Module loading (hyphenated filenames require importlib) ───────────────────

_scripts_dir = Path(__file__).parent.parent / "scripts"


def _load_module(filename: str, modname: str):
    spec = importlib.util.spec_from_file_location(modname, _scripts_dir / filename)
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


_eval = _load_module("evaluate.py", "evaluate")
_gen = _load_module("generate-corpus.py", "generate_corpus")

make_pair_key = _eval.make_pair_key
load_ground_truth = _eval.load_ground_truth
load_detected_pairs = _eval.load_detected_pairs
evaluate = _eval.evaluate

generate_corpus = _gen.generate_corpus
validate_corpus = _gen.validate_corpus

# ── Fixtures ──────────────────────────────────────────────────────────────────

FIXTURE_CORPUS = Path(__file__).parent / "fixtures" / "eval-corpus.json"


def _write_tmp(data: dict | list, suffix: str = ".json") -> Path:
    """Write data to a temp file, return its path."""
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=suffix, delete=False
    )
    json.dump(data, f)
    f.flush()
    return Path(f.name)


# ── make_pair_key ─────────────────────────────────────────────────────────────


def test_pair_key_order_independent():
    a = "a.py:foo:1"
    b = "b.py:bar:2"
    assert make_pair_key(a, b) == make_pair_key(b, a)


def test_pair_key_distinct_different_functions():
    assert make_pair_key("a.py:foo:1", "b.py:bar:2") != make_pair_key("a.py:foo:1", "c.py:baz:3")


def test_pair_key_same_inputs_equal():
    k = make_pair_key("x.py:alpha:10", "y.py:beta:20")
    assert k == make_pair_key("x.py:alpha:10", "y.py:beta:20")


# ── load_ground_truth ─────────────────────────────────────────────────────────


def test_load_ground_truth_fixture_count():
    gt = load_ground_truth(str(FIXTURE_CORPUS))
    assert len(gt) == 15


def test_load_ground_truth_clone_count():
    gt = load_ground_truth(str(FIXTURE_CORPUS))
    clones = [e for e in gt.values() if e["is_clone"]]
    assert len(clones) == 5


def test_load_ground_truth_non_clone_count():
    gt = load_ground_truth(str(FIXTURE_CORPUS))
    non_clones = [e for e in gt.values() if not e["is_clone"]]
    assert len(non_clones) == 10


def test_load_ground_truth_fields_present():
    gt = load_ground_truth(str(FIXTURE_CORPUS))
    for entry in gt.values():
        assert "is_clone" in entry
        assert "clone_type" in entry
        assert "func_a" in entry
        assert "func_b" in entry


def test_load_ground_truth_pair_key_canonical():
    """Same pair in different order produces the same key."""
    gt = load_ground_truth(str(FIXTURE_CORPUS))
    # The fixture has a.py:calc_sum_v1:1 paired with b.py:calc_sum_v2:1
    spec_a = "a.py:calc_sum_v1:1"
    spec_b = "b.py:calc_sum_v2:1"
    key = make_pair_key(spec_a, spec_b)
    assert key in gt
    assert gt[key]["is_clone"] is True
    assert gt[key]["clone_type"] == 1


# ── load_detected_pairs ───────────────────────────────────────────────────────

def _make_results(pairs_data: list[dict]) -> Path:
    """Write a fake merged-results JSON (bare array format)."""
    return _write_tmp(pairs_data)


def _make_pair_result(
    file_a: str, name_a: str, line_a: int,
    file_b: str, name_b: str, line_b: int,
    confidence: str = "HIGH",
) -> dict:
    return {
        "func_a": {"file": file_a, "name": name_a, "line": line_a},
        "func_b": {"file": file_b, "name": name_b, "line": line_b},
        "confidence": confidence,
        "composite_score": 0.9,
        "num_strategies": 1,
        "strategies": {},
    }


def test_load_detected_pairs_high_only():
    pairs = [
        _make_pair_result("a.py", "foo", 1, "b.py", "bar", 1, "HIGH"),
        _make_pair_result("c.py", "baz", 1, "d.py", "qux", 1, "LOW"),
    ]
    path = _make_results(pairs)
    detected = load_detected_pairs(str(path), min_confidence="HIGH")
    assert len(detected) == 1


def test_load_detected_pairs_medium_includes_high():
    pairs = [
        _make_pair_result("a.py", "foo", 1, "b.py", "bar", 1, "HIGH"),
        _make_pair_result("c.py", "baz", 1, "d.py", "qux", 1, "MEDIUM"),
        _make_pair_result("e.py", "alpha", 1, "f.py", "beta", 1, "LOW"),
    ]
    path = _make_results(pairs)
    detected = load_detected_pairs(str(path), min_confidence="MEDIUM")
    assert len(detected) == 2


def test_load_detected_pairs_low_includes_all():
    pairs = [
        _make_pair_result("a.py", "foo", 1, "b.py", "bar", 1, "HIGH"),
        _make_pair_result("c.py", "baz", 1, "d.py", "qux", 1, "MEDIUM"),
        _make_pair_result("e.py", "alpha", 1, "f.py", "beta", 1, "LOW"),
    ]
    path = _make_results(pairs)
    detected = load_detected_pairs(str(path), min_confidence="LOW")
    assert len(detected) == 3


def test_load_detected_pairs_include_summary_format():
    """Should handle {pairs: [...], summary: {...}} format."""
    data = {
        "pairs": [_make_pair_result("a.py", "foo", 1, "b.py", "bar", 1, "HIGH")],
        "summary": {"total_pairs": 1},
    }
    path = _write_tmp(data)
    detected = load_detected_pairs(str(path), min_confidence="LOW")
    assert len(detected) == 1


def test_load_detected_pairs_empty():
    path = _make_results([])
    detected = load_detected_pairs(str(path), min_confidence="LOW")
    assert len(detected) == 0


# ── evaluate() ───────────────────────────────────────────────────────────────


def _build_gt_from_fixture() -> dict:
    return load_ground_truth(str(FIXTURE_CORPUS))


def test_evaluate_perfect_detection():
    """All clones detected, no false positives → P=1.0, R=1.0, F1=1.0."""
    gt = _build_gt_from_fixture()
    # detected = exactly the actual clone keys
    detected = {key for key, entry in gt.items() if entry["is_clone"]}
    result = evaluate(detected, gt)

    assert result["overall"]["precision"] == 1.0
    assert result["overall"]["recall"] == 1.0
    assert result["overall"]["f1"] == 1.0
    assert result["overall"]["tp"] == 5
    assert result["overall"]["fp"] == 0
    assert result["overall"]["fn"] == 0


def test_evaluate_no_detection():
    """Nothing detected → R=0, F1=0; precision undefined → 0."""
    gt = _build_gt_from_fixture()
    result = evaluate(set(), gt)

    assert result["overall"]["precision"] == 0.0
    assert result["overall"]["recall"] == 0.0
    assert result["overall"]["f1"] == 0.0
    assert result["overall"]["tp"] == 0
    assert result["overall"]["fn"] == 5  # 5 actual clones missed


def test_evaluate_partial_detection():
    """Detect 3 of 5 clones, no FP → P=1.0, R=0.6, F1=0.75."""
    gt = _build_gt_from_fixture()
    clone_keys = [key for key, entry in gt.items() if entry["is_clone"]]
    detected = set(clone_keys[:3])  # detect only 3 of 5

    result = evaluate(detected, gt)
    assert result["overall"]["tp"] == 3
    assert result["overall"]["fp"] == 0
    assert result["overall"]["fn"] == 2
    assert result["overall"]["precision"] == 1.0
    assert result["overall"]["recall"] == 0.6
    assert abs(result["overall"]["f1"] - 0.75) < 0.001


def test_evaluate_with_false_positives():
    """Detect 5 real clones + 2 non-clones → P < 1.0, R=1.0."""
    gt = _build_gt_from_fixture()
    clone_keys = [key for key, entry in gt.items() if entry["is_clone"]]
    non_clone_keys = [key for key, entry in gt.items() if not entry["is_clone"]]

    detected = set(clone_keys) | set(non_clone_keys[:2])

    result = evaluate(detected, gt)
    assert result["overall"]["tp"] == 5
    assert result["overall"]["fp"] == 2
    assert result["overall"]["fn"] == 0
    assert result["overall"]["recall"] == 1.0
    expected_p = 5 / 7
    assert abs(result["overall"]["precision"] - expected_p) < 0.001


def test_evaluate_empty_inputs():
    """Empty detected set and empty ground truth → zeros, no crash."""
    result = evaluate(set(), {})
    assert result["overall"]["tp"] == 0
    assert result["overall"]["fp"] == 0
    assert result["overall"]["fn"] == 0
    assert result["overall"]["precision"] == 0.0
    assert result["overall"]["recall"] == 0.0
    assert result["overall"]["f1"] == 0.0


def test_evaluate_per_type_breakdown():
    """by_type should have entries for each clone type present in ground truth."""
    gt = _build_gt_from_fixture()
    detected = {key for key, entry in gt.items() if entry["is_clone"]}
    result = evaluate(detected, gt)

    # Fixture has types 1, 2, and 4
    assert "1" in result["by_type"]
    assert "2" in result["by_type"]
    assert "4" in result["by_type"]


def test_evaluate_per_type_type1_perfect():
    """With perfect detection, type 1 should show TP=1, FP=0, FN=0."""
    gt = _build_gt_from_fixture()
    detected = {key for key, entry in gt.items() if entry["is_clone"]}
    result = evaluate(detected, gt)

    t1 = result["by_type"]["1"]
    assert t1["tp"] == 1
    assert t1["fn"] == 0


def test_evaluate_summary_format():
    """Summary string should follow 'P=X.XX R=X.XX F1=X.XX' pattern."""
    gt = _build_gt_from_fixture()
    detected = {key for key, entry in gt.items() if entry["is_clone"]}
    result = evaluate(detected, gt)

    summary = result["summary"]
    assert summary.startswith("P=")
    assert "R=" in summary
    assert "F1=" in summary


def test_evaluate_output_structure():
    """Result dict should have 'overall', 'by_type', 'summary' keys."""
    gt = _build_gt_from_fixture()
    result = evaluate(set(), gt)
    assert "overall" in result
    assert "by_type" in result
    assert "summary" in result


# ── generate-corpus.py ────────────────────────────────────────────────────────


def test_generate_corpus_default():
    corpus = generate_corpus(num_per_type=5, seed=42)
    assert "functions" in corpus
    assert "ground_truth" in corpus


def test_generate_corpus_function_count():
    """Clone functions (4 types × N × 2) plus diverse decoy functions."""
    corpus = generate_corpus(num_per_type=5, seed=42)
    # 4 types × 5 pairs × 2 functions = 40 clone functions + diverse decoys
    assert len(corpus["functions"]) >= 40


def test_generate_corpus_clone_pair_count():
    """Should produce num_per_type pairs for each of the 4 clone types."""
    corpus = generate_corpus(num_per_type=5, seed=42)
    clones = [p for p in corpus["ground_truth"] if p["is_clone"]]
    assert len(clones) == 20  # 4 types × 5 per type


def test_generate_corpus_each_clone_type_present():
    """All four clone types should appear in the ground truth."""
    corpus = generate_corpus(num_per_type=5, seed=42)
    clone_types = {p["clone_type"] for p in corpus["ground_truth"] if p["is_clone"]}
    assert {1, 2, 3, 4} == clone_types


def test_generate_corpus_non_clone_pairs_present():
    corpus = generate_corpus(num_per_type=5, seed=42)
    non_clones = [p for p in corpus["ground_truth"] if not p["is_clone"]]
    assert len(non_clones) > 0


def test_generate_corpus_no_duplicate_keys():
    """No pair should appear twice in ground truth."""
    corpus = generate_corpus(num_per_type=5, seed=42)
    keys = [
        "|".join(sorted([p["func_a"], p["func_b"]]))
        for p in corpus["ground_truth"]
    ]
    assert len(keys) == len(set(keys))


def test_generate_corpus_required_function_fields():
    """Every function must have required fields."""
    corpus = generate_corpus(num_per_type=3, seed=0)
    for func in corpus["functions"]:
        assert "name" in func
        assert "file" in func
        assert "line" in func
        assert "token_sequence" in func
        assert "body_lines" in func
        assert "params" in func
        assert isinstance(func["token_sequence"], list)
        assert isinstance(func["params"], list)


def test_generate_corpus_required_pair_fields():
    """Every ground truth entry must have required fields."""
    corpus = generate_corpus(num_per_type=3, seed=0)
    for entry in corpus["ground_truth"]:
        assert "func_a" in entry
        assert "func_b" in entry
        assert "is_clone" in entry
        assert "clone_type" in entry
        assert isinstance(entry["is_clone"], bool)


def test_generate_corpus_deterministic():
    """Same seed produces identical corpus."""
    c1 = generate_corpus(num_per_type=5, seed=99)
    c2 = generate_corpus(num_per_type=5, seed=99)
    assert c1 == c2


def test_generate_corpus_different_seeds_differ():
    c1 = generate_corpus(num_per_type=5, seed=1)
    c2 = generate_corpus(num_per_type=5, seed=2)
    # At least the ground truth should differ
    assert c1["ground_truth"] != c2["ground_truth"]


def test_validate_corpus_valid():
    corpus = generate_corpus(num_per_type=5, seed=42)
    errors = validate_corpus(corpus)
    assert errors == []


def test_validate_corpus_missing_function_field():
    corpus = generate_corpus(num_per_type=2, seed=0)
    del corpus["functions"][0]["name"]
    errors = validate_corpus(corpus)
    assert any("name" in e for e in errors)


def test_validate_corpus_duplicate_pair_keys():
    corpus = generate_corpus(num_per_type=2, seed=0)
    corpus["ground_truth"].append(corpus["ground_truth"][0])
    errors = validate_corpus(corpus)
    assert any("duplicate" in e.lower() for e in errors)


# ── Integration: evaluate using generated corpus ──────────────────────────────


def test_evaluate_on_generated_corpus_perfect_recall():
    """Build GT from generated corpus, detect all clones → R=1."""
    corpus = generate_corpus(num_per_type=3, seed=7)
    corpus_path = _write_tmp(corpus)
    gt = load_ground_truth(str(corpus_path))

    detected = {key for key, entry in gt.items() if entry["is_clone"]}
    result = evaluate(detected, gt)
    assert result["overall"]["recall"] == 1.0


def test_evaluate_on_generated_corpus_zero_detection():
    """Detect nothing on generated corpus → R=0."""
    corpus = generate_corpus(num_per_type=3, seed=7)
    corpus_path = _write_tmp(corpus)
    gt = load_ground_truth(str(corpus_path))

    result = evaluate(set(), gt)
    assert result["overall"]["recall"] == 0.0
    assert result["overall"]["f1"] == 0.0


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
