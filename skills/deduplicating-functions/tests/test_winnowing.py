#!/usr/bin/env python3
# ABOUTME: Tests for Winnowing fingerprint duplicate detector.
# Covers: kgrams, winnow, compute_fingerprint, fingerprint_similarity, detect_winnowing_duplicates.

import importlib.util
import sys
from pathlib import Path

import pytest

_scripts = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(_scripts))

_spec = importlib.util.spec_from_file_location(
    "detect_winnowing", _scripts / "detect-winnowing.py"
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

kgrams = _mod.kgrams
winnow = _mod.winnow
compute_fingerprint = _mod.compute_fingerprint
fingerprint_similarity = _mod.fingerprint_similarity
detect_winnowing_duplicates = _mod.detect_winnowing_duplicates


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _func(name: str, file: str, tokens: list[str], line: int = 1) -> dict:
    """Build a minimal catalog entry with a flat token_sequence."""
    return {
        "name": name,
        "file": file,
        "line": line,
        "qualified_name": name,
        "token_sequence": tokens,
        "body_lines": max(len(tokens), 5),
        "params": [],
    }


def _func_context(name: str, file: str, context: str, line: int = 1) -> dict:
    """Build a minimal catalog entry that uses the context field (no token_sequence)."""
    return {
        "name": name,
        "file": file,
        "line": line,
        "qualified_name": name,
        "context": context,
        "body_lines": 10,
        "params": [],
    }


# ---------------------------------------------------------------------------
# kgrams()
# ---------------------------------------------------------------------------

class TestKgrams:
    def test_basic_bigrams(self):
        result = kgrams(["a", "b", "c", "d"], 2)
        assert result == [("a", "b"), ("b", "c"), ("c", "d")]

    def test_trigrams(self):
        result = kgrams(["x", "y", "z", "w"], 3)
        assert result == [("x", "y", "z"), ("y", "z", "w")]

    def test_exact_k_length(self):
        result = kgrams(["a", "b", "c"], 3)
        assert result == [("a", "b", "c")]

    def test_seq_shorter_than_k_returns_empty(self):
        assert kgrams(["a", "b"], 5) == []

    def test_empty_sequence_returns_empty(self):
        assert kgrams([], 3) == []

    def test_k_equals_one(self):
        result = kgrams(["a", "b", "c"], 1)
        assert result == [("a",), ("b",), ("c",)]

    def test_single_token_k1(self):
        result = kgrams(["only"], 1)
        assert result == [("only",)]

    def test_single_token_k2_returns_empty(self):
        assert kgrams(["only"], 2) == []

    def test_preserves_token_values(self):
        tokens = ["def", "foo", "(", "x", ")", ":"]
        result = kgrams(tokens, 3)
        assert result[0] == ("def", "foo", "(")
        assert result[-1] == ("x", ")", ":")


# ---------------------------------------------------------------------------
# winnow()
# ---------------------------------------------------------------------------

class TestWinnow:
    def test_returns_set(self):
        hashes = [7, 3, 5, 2, 8, 4, 1, 6]
        result = winnow(hashes, 4)
        assert isinstance(result, set)

    def test_empty_hashes(self):
        assert winnow([], 4) == set()

    def test_window_larger_than_input_returns_all(self):
        hashes = [5, 3, 8]
        result = winnow(hashes, 10)
        assert result == {3, 5, 8}

    def test_window_equals_length(self):
        hashes = [5, 3, 8, 1]
        result = winnow(hashes, 4)
        # Single window: minimum is 1
        assert 1 in result

    def test_minimum_always_selected(self):
        # Any window of 4 must contribute at least one hash
        hashes = [10, 9, 8, 7, 6, 5, 4, 3]
        result = winnow(hashes, 4)
        assert len(result) >= 1

    def test_identical_sequences_same_fingerprint(self):
        hashes = [4, 1, 7, 3, 9, 2, 8]
        assert winnow(hashes, 3) == winnow(hashes, 3)

    def test_very_distinct_sequences_differ(self):
        # Two hash sequences with completely different values
        hashes_a = [100, 200, 300, 400, 500]
        hashes_b = [1, 2, 3, 4, 5]
        fp_a = winnow(hashes_a, 3)
        fp_b = winnow(hashes_b, 3)
        assert fp_a != fp_b
        assert fp_a.isdisjoint(fp_b)

    def test_window_1_returns_all_unique(self):
        hashes = [3, 1, 4, 1, 5, 9]
        result = winnow(hashes, 1)
        # Every position is its own window — all become fingerprint entries
        assert result == set(hashes)

    def test_guarantee_coverage(self):
        # With window=w, every window of w hashes must contribute at least one hash.
        import random
        random.seed(42)
        hashes = [random.randint(0, 1000) for _ in range(20)]
        w = 4
        fp = winnow(hashes, w)
        for i in range(len(hashes) - w + 1):
            window_set = set(hashes[i:i + w])
            assert window_set & fp, (
                f"Window at position {i} has no hash in fingerprint: {hashes[i:i+w]}"
            )


# ---------------------------------------------------------------------------
# compute_fingerprint()
# ---------------------------------------------------------------------------

class TestComputeFingerprint:
    def test_returns_set(self):
        func = _func("f", "a.py", ["if", "x", "return", "y", "else", "z"])
        result = compute_fingerprint(func)
        assert isinstance(result, set)

    def test_empty_token_sequence_returns_empty(self):
        func = _func("f", "a.py", [])
        assert compute_fingerprint(func) == set()

    def test_too_short_returns_empty(self):
        # k=5, only 3 tokens — cannot form any k-gram
        func = _func("f", "a.py", ["a", "b", "c"])
        assert compute_fingerprint(func, k=5) == set()

    def test_identical_functions_same_fingerprint(self):
        tokens = ["def", "foo", "x", "return", "x", "+", "1", "end"]
        fa = _func("foo", "a.py", tokens)
        fb = _func("bar", "b.py", tokens)
        fp_a = compute_fingerprint(fa)
        fp_b = compute_fingerprint(fb)
        assert fp_a == fp_b

    def test_different_functions_different_fingerprints(self):
        fa = _func("foo", "a.py", ["alpha", "beta", "gamma", "delta", "epsilon"])
        fb = _func("bar", "b.py", ["one", "two", "three", "four", "five"])
        fp_a = compute_fingerprint(fa, k=3, window=2)
        fp_b = compute_fingerprint(fb, k=3, window=2)
        assert fp_a.isdisjoint(fp_b)

    def test_uses_context_fallback(self):
        # No token_sequence — should use context
        func = _func_context(
            "f", "a.py",
            "def f(x): return x + 1 if x > 0 else 0"
        )
        result = compute_fingerprint(func, k=3, window=2)
        assert isinstance(result, set)
        # Should produce some fingerprint hashes (enough tokens in the context)
        assert len(result) >= 1

    def test_custom_k_and_window(self):
        tokens = ["a", "b", "c", "d", "e", "f", "g", "h"]
        func = _func("f", "a.py", tokens)
        fp_k3 = compute_fingerprint(func, k=3, window=2)
        fp_k5 = compute_fingerprint(func, k=5, window=2)
        # Different k produces different fingerprints (different k-grams)
        assert fp_k3 != fp_k5

    def test_dict_token_sequence(self):
        # token_sequence as list of {"type": ..., "value": ...} dicts
        func = {
            "name": "f", "file": "a.py", "line": 1,
            "token_sequence": [
                {"type": "keyword", "value": "def"},
                {"type": "identifier", "value": "foo"},
                {"type": "punctuation", "value": "("},
                {"type": "identifier", "value": "x"},
                {"type": "punctuation", "value": ")"},
                {"type": "punctuation", "value": ":"},
                {"type": "keyword", "value": "return"},
                {"type": "identifier", "value": "x"},
            ],
            "body_lines": 5,
        }
        result = compute_fingerprint(func, k=3, window=2)
        assert isinstance(result, set)
        assert len(result) >= 1


# ---------------------------------------------------------------------------
# fingerprint_similarity()
# ---------------------------------------------------------------------------

class TestFingerprintSimilarity:
    def test_identical_fingerprints_score_1(self):
        fp = {1, 2, 3, 4, 5}
        assert fingerprint_similarity(fp, fp) == pytest.approx(1.0)

    def test_disjoint_fingerprints_score_0(self):
        fp_a = {1, 2, 3}
        fp_b = {4, 5, 6}
        assert fingerprint_similarity(fp_a, fp_b) == pytest.approx(0.0)

    def test_partial_overlap(self):
        fp_a = {1, 2, 3, 4}
        fp_b = {3, 4, 5, 6}
        score = fingerprint_similarity(fp_a, fp_b)
        assert 0.0 < score < 1.0

    def test_empty_both_returns_0(self):
        assert fingerprint_similarity(set(), set()) == pytest.approx(0.0)

    def test_empty_one_returns_0(self):
        assert fingerprint_similarity({1, 2, 3}, set()) == pytest.approx(0.0)
        assert fingerprint_similarity(set(), {1, 2, 3}) == pytest.approx(0.0)

    def test_containment_high_overlap_coefficient(self):
        # fp_b is a strict subset of fp_a — overlap_coefficient should be 1.0
        fp_a = {1, 2, 3, 4, 5, 6, 7, 8}
        fp_b = {3, 4, 5}  # fully contained in fp_a
        score = fingerprint_similarity(fp_a, fp_b)
        # overlap_coefficient = 3/3 = 1.0
        assert score == pytest.approx(1.0)

    def test_returns_max_of_jaccard_and_overlap(self):
        # Construct case where overlap > jaccard
        fp_a = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10}
        fp_b = {1, 2}  # overlap = 2/2=1.0, jaccard = 2/10=0.2
        score = fingerprint_similarity(fp_a, fp_b)
        assert score == pytest.approx(1.0)

    def test_symmetric(self):
        fp_a = {1, 2, 3, 7}
        fp_b = {2, 3, 5, 6}
        assert fingerprint_similarity(fp_a, fp_b) == fingerprint_similarity(fp_b, fp_a)


# ---------------------------------------------------------------------------
# detect_winnowing_duplicates() — full pipeline
# ---------------------------------------------------------------------------

class TestDetectWinnowingDuplicates:
    def test_empty_catalog_returns_empty(self):
        assert detect_winnowing_duplicates([]) == []

    def test_single_function_returns_empty(self):
        catalog = [_func("lone", "a.py", ["a", "b", "c", "d", "e", "f"])]
        assert detect_winnowing_duplicates(catalog) == []

    def test_identical_functions_score_1(self):
        tokens = ["def", "compute", "(", "x", ")", ":", "return", "x", "*", "2", "+", "1"]
        catalog = [
            _func("compute", "a.py", tokens),
            _func("compute_copy", "b.py", tokens),
        ]
        results = detect_winnowing_duplicates(catalog, threshold=0.0)
        assert len(results) == 1
        assert results[0]["final_score"] == pytest.approx(1.0)

    def test_completely_different_functions_below_threshold(self):
        catalog = [
            _func("alpha", "a.py", ["aaa", "bbb", "ccc", "ddd", "eee", "fff", "ggg"]),
            _func("beta", "b.py", ["zzz", "yyy", "xxx", "www", "vvv", "uuu", "ttt"]),
        ]
        results = detect_winnowing_duplicates(catalog, threshold=0.1)
        assert len(results) == 0

    def test_partial_clone_detected_via_overlap(self):
        # fa is a superset of fb — fb is a copied fragment of fa
        shared = ["if", "x", ">", "0", "return", "x", "*", "factor", "else", "return", "0"]
        long_tokens = ["def", "compute"] + shared + ["log", "result", "done"]
        short_tokens = shared  # copied fragment — exactly contained

        catalog = [
            _func("long_func", "a.py", long_tokens),
            _func("fragment", "b.py", short_tokens),
        ]
        # Use low k and window so short sequence still gets fingerprinted
        results = detect_winnowing_duplicates(catalog, threshold=0.3, k=3, window=2)
        assert len(results) >= 1
        # Overlap coefficient should be high (fragment is contained)
        r = results[0]
        assert r["scores"]["overlap"] > 0.5

    def test_output_format(self):
        tokens = ["def", "foo", "(", "x", ")", ":", "return", "x", "+", "1", "end", "bar"]
        catalog = [
            _func("foo", "a.py", tokens),
            _func("bar", "b.py", tokens),
        ]
        results = detect_winnowing_duplicates(catalog, threshold=0.0)
        assert len(results) >= 1
        r = results[0]
        # Required top-level keys
        assert "func_a" in r
        assert "func_b" in r
        assert "scores" in r
        assert "final_score" in r
        assert r["strategy"] == "winnowing"
        # func_a / func_b shape
        for ref_key in ("func_a", "func_b"):
            ref = r[ref_key]
            assert "name" in ref
            assert "file" in ref
            assert "line" in ref
        # scores sub-keys
        assert "jaccard" in r["scores"]
        assert "overlap" in r["scores"]

    def test_strategy_field_is_winnowing(self):
        tokens = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"]
        catalog = [
            _func("f1", "a.py", tokens),
            _func("f2", "b.py", tokens),
        ]
        results = detect_winnowing_duplicates(catalog, threshold=0.0)
        for r in results:
            assert r["strategy"] == "winnowing"

    def test_no_self_pairs(self):
        tokens = ["x", "y", "z", "w", "v", "u"]
        catalog = [_func("f", "a.py", tokens, line=1)]
        results = detect_winnowing_duplicates(catalog, threshold=0.0)
        assert len(results) == 0

    def test_no_duplicate_pairs(self):
        tokens = ["a", "b", "c", "d", "e", "f"]
        catalog = [
            _func("f1", "a.py", tokens),
            _func("f2", "b.py", tokens),
            _func("f3", "c.py", tokens),
        ]
        results = detect_winnowing_duplicates(catalog, threshold=0.0)
        # 3 functions -> at most 3 pairs (C(3,2))
        assert len(results) <= 3
        # No duplicate pair keys
        seen = set()
        for r in results:
            key = (r["func_a"]["file"], r["func_b"]["file"])
            rev_key = (r["func_b"]["file"], r["func_a"]["file"])
            assert key not in seen and rev_key not in seen
            seen.add(key)

    def test_threshold_filters_low_scores(self):
        tokens_a = ["aaa", "bbb", "ccc", "ddd", "eee", "fff"]
        tokens_b = ["aaa", "zzz", "yyy", "xxx", "www", "vvv"]
        catalog = [
            _func("f1", "a.py", tokens_a),
            _func("f2", "b.py", tokens_b),
        ]
        # Compute actual score
        results_low = detect_winnowing_duplicates(catalog, threshold=0.0, k=3, window=2)
        results_high = detect_winnowing_duplicates(catalog, threshold=0.99, k=3, window=2)
        if results_low:
            score = results_low[0]["final_score"]
            if score < 0.99:
                assert len(results_high) == 0

    def test_sorted_by_score_descending(self):
        # Create catalog where one pair is more similar than another
        shared_tokens = ["def", "foo", "(", "x", ")", ":", "return", "x", "*", "2"]
        unique_a = shared_tokens + ["log", "debug", "trace", "info"]
        unique_b = shared_tokens + ["socket", "connect", "recv", "send"]
        unrelated_a = ["network", "socket", "host", "port", "listen", "accept"]
        unrelated_b = ["parse", "json", "decode", "encode", "string", "buffer"]

        catalog = [
            _func("f1", "a.py", unique_a),
            _func("f2", "b.py", unique_b),
            _func("f3", "c.py", unrelated_a),
            _func("f4", "d.py", unrelated_b),
        ]
        results = detect_winnowing_duplicates(catalog, threshold=0.0, k=3, window=2)
        scores = [r["final_score"] for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_functions_with_no_tokens_skipped(self):
        catalog = [
            _func("empty_a", "a.py", []),
            _func("empty_b", "b.py", []),
            _func("real", "c.py", ["a", "b", "c", "d", "e", "f"]),
        ]
        results = detect_winnowing_duplicates(catalog, threshold=0.0)
        # empty functions have no fingerprint — they produce no pairs
        for r in results:
            assert r["func_a"]["name"] != "empty_a"
            assert r["func_b"]["name"] != "empty_b"

    def test_custom_k_and_window_params(self):
        tokens = ["a", "b", "c", "d", "e", "f", "g", "h"]
        catalog = [
            _func("f1", "a.py", tokens),
            _func("f2", "b.py", tokens),
        ]
        results = detect_winnowing_duplicates(catalog, threshold=0.0, k=2, window=2)
        assert len(results) >= 1

    def test_final_score_is_max_of_jaccard_and_overlap(self):
        tokens = ["def", "foo", "(", "x", ")", ":", "return", "x", "+", "1"]
        catalog = [
            _func("f1", "a.py", tokens),
            _func("f2", "b.py", tokens),
        ]
        results = detect_winnowing_duplicates(catalog, threshold=0.0)
        if results:
            r = results[0]
            expected = max(r["scores"]["jaccard"], r["scores"]["overlap"])
            assert r["final_score"] == pytest.approx(expected, abs=0.001)
