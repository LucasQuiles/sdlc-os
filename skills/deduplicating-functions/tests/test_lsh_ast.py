#!/usr/bin/env python3
# ABOUTME: Tests for LSH (MinHash) AST duplicate detector.

import importlib.util
import sys
from pathlib import Path

import pytest

_scripts = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(_scripts))

_spec = importlib.util.spec_from_file_location(
    "detect_lsh_ast", _scripts / "detect-lsh-ast.py"
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

build_minhash = _mod.build_minhash
detect_lsh_duplicates = _mod.detect_lsh_duplicates


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


def _tokens(n: int, prefix: str = "tok") -> list[str]:
    """Generate n distinct tokens."""
    return [f"{prefix}_{i}" for i in range(n)]


# ---------------------------------------------------------------------------
# build_minhash tests
# ---------------------------------------------------------------------------

class TestBuildMinHash:
    def test_returns_minhash_object(self):
        from datasketch import MinHash
        m = build_minhash({"a", "b", "c"})
        assert isinstance(m, MinHash)

    def test_identical_sets_jaccard_near_one(self):
        tokens = set(_tokens(20))
        m1 = build_minhash(tokens, num_perm=128)
        m2 = build_minhash(tokens, num_perm=128)
        estimated = m1.jaccard(m2)
        assert estimated == pytest.approx(1.0, abs=0.1)

    def test_disjoint_sets_jaccard_near_zero(self):
        set_a = set(_tokens(20, prefix="alpha"))
        set_b = set(_tokens(20, prefix="beta"))
        m1 = build_minhash(set_a, num_perm=128)
        m2 = build_minhash(set_b, num_perm=128)
        estimated = m1.jaccard(m2)
        assert estimated == pytest.approx(0.0, abs=0.1)

    def test_custom_num_perm(self):
        from datasketch import MinHash
        m = build_minhash({"x", "y", "z"}, num_perm=64)
        assert isinstance(m, MinHash)

    def test_empty_set_produces_minhash(self):
        """Empty set should still produce a valid (all-zero-hash) MinHash."""
        from datasketch import MinHash
        m = build_minhash(set())
        assert isinstance(m, MinHash)

    def test_single_token_set(self):
        from datasketch import MinHash
        m = build_minhash({"only_token"})
        assert isinstance(m, MinHash)


# ---------------------------------------------------------------------------
# detect_lsh_duplicates tests
# ---------------------------------------------------------------------------

class TestDetectLSHDuplicates:
    def test_finds_identical_token_sequences(self):
        """Identical token sets should be detected as duplicates."""
        shared = _tokens(15)
        catalog = [
            _func("func_a", "a.py", shared),
            _func("func_b", "b.py", shared),
            _func("unrelated", "c.py", _tokens(15, prefix="other")),
        ]
        results = detect_lsh_duplicates(catalog, threshold=0.5, num_perm=128)
        assert len(results) >= 1
        names = {(r["func_a"]["name"], r["func_b"]["name"]) for r in results}
        assert ("func_a", "func_b") in names or ("func_b", "func_a") in names

    def test_empty_catalog_returns_empty(self):
        assert detect_lsh_duplicates([], threshold=0.5) == []

    def test_single_function_returns_empty(self):
        catalog = [_func("lone", "a.py", _tokens(10))]
        assert detect_lsh_duplicates(catalog, threshold=0.5) == []

    def test_no_self_pairs_in_results(self):
        """No function should be paired with itself."""
        shared = _tokens(15)
        catalog = [
            _func("a", "a.py", shared),
            _func("b", "b.py", shared),
        ]
        results = detect_lsh_duplicates(catalog, threshold=0.5)
        for r in results:
            assert not (
                r["func_a"]["name"] == r["func_b"]["name"]
                and r["func_a"]["file"] == r["func_b"]["file"]
                and r["func_a"]["line"] == r["func_b"]["line"]
            )

    def test_output_format(self):
        """Results must include all required fields with correct strategy."""
        shared = _tokens(15)
        catalog = [
            _func("foo", "x.py", shared),
            _func("bar", "y.py", shared),
        ]
        results = detect_lsh_duplicates(catalog, threshold=0.5)
        assert len(results) >= 1
        r = results[0]
        assert "func_a" in r
        assert "func_b" in r
        assert "scores" in r
        assert "estimated_jaccard" in r["scores"]
        assert "final_score" in r
        assert r["strategy"] == "lsh_ast"
        # func_a and func_b must have name, file, line
        for side in ("func_a", "func_b"):
            assert "name" in r[side]
            assert "file" in r[side]
            assert "line" in r[side]

    def test_final_score_matches_estimated_jaccard(self):
        shared = _tokens(15)
        catalog = [
            _func("p", "a.py", shared),
            _func("q", "b.py", shared),
        ]
        results = detect_lsh_duplicates(catalog, threshold=0.5)
        assert len(results) >= 1
        r = results[0]
        assert r["final_score"] == r["scores"]["estimated_jaccard"]

    def test_pairs_deduplicated(self):
        """Each pair should appear at most once."""
        shared = _tokens(15)
        catalog = [
            _func("a", "a.py", shared),
            _func("b", "b.py", shared),
            _func("c", "c.py", shared),
        ]
        results = detect_lsh_duplicates(catalog, threshold=0.5)
        seen = set()
        for r in results:
            fa_key = f"{r['func_a']['file']}:{r['func_a']['line']}"
            fb_key = f"{r['func_b']['file']}:{r['func_b']['line']}"
            pair = (min(fa_key, fb_key), max(fa_key, fb_key))
            assert pair not in seen, f"Duplicate pair found: {pair}"
            seen.add(pair)

    def test_functions_with_fewer_than_5_unique_tokens_skipped(self):
        """Functions with < 5 unique tokens should be silently skipped."""
        tiny = _tokens(3)  # only 3 unique tokens
        normal = _tokens(15)
        catalog = [
            _func("tiny_a", "a.py", tiny),
            _func("tiny_b", "b.py", tiny),
            _func("normal", "c.py", normal),
        ]
        # tiny functions are skipped, so no pairs from them
        results = detect_lsh_duplicates(catalog, threshold=0.5)
        for r in results:
            assert r["func_a"]["name"] not in ("tiny_a", "tiny_b")
            assert r["func_b"]["name"] not in ("tiny_a", "tiny_b")

    def test_results_sorted_by_score_descending(self):
        """Results should be sorted with highest final_score first."""
        catalog = [
            _func("exact_a", "a.py", _tokens(15, "shared")),
            _func("exact_b", "b.py", _tokens(15, "shared")),
            _func("partial_a", "c.py", _tokens(15, "shared") + _tokens(15, "extra_c")),
            _func("partial_b", "d.py", _tokens(15, "shared") + _tokens(15, "extra_d")),
        ]
        results = detect_lsh_duplicates(catalog, threshold=0.3, num_perm=128)
        scores = [r["final_score"] for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_threshold_filters_low_similarity(self):
        """Pairs with estimated Jaccard below threshold should not appear."""
        catalog = [
            _func("a", "a.py", _tokens(20, "set_a")),
            _func("b", "b.py", _tokens(20, "set_b")),  # disjoint
        ]
        results = detect_lsh_duplicates(catalog, threshold=0.9, num_perm=128)
        # Disjoint sets should not pass a high threshold
        assert len(results) == 0

    def test_two_functions_same_file_different_names(self):
        """Two distinct functions in the same file should be compared."""
        shared = _tokens(15)
        catalog = [
            _func("helper_v1", "utils.py", shared, line=1),
            _func("helper_v2", "utils.py", shared, line=20),
        ]
        results = detect_lsh_duplicates(catalog, threshold=0.5)
        assert len(results) >= 1
