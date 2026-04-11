#!/usr/bin/env python3
# ABOUTME: Tests for TF-IDF inverted index duplicate detector.

import importlib.util
import sys
from pathlib import Path

import pytest

_scripts = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(_scripts))

_spec = importlib.util.spec_from_file_location(
    "detect_tfidf", _scripts / "detect-tfidf-index.py"
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

build_inverted_index = _mod.build_inverted_index
compute_idf = _mod.compute_idf
retrieve_candidates = _mod.retrieve_candidates
score_pair_tfidf = _mod.score_pair_tfidf
detect_tfidf_duplicates = _mod.detect_tfidf_duplicates


def _func(name, file, tokens, line=1):
    return {
        "name": name, "file": file, "line": line,
        "qualified_name": name,
        "token_sequence": tokens,
        "body_lines": max(len(tokens), 5),
        "params": [],
    }


class TestInvertedIndex:
    def test_builds_index(self):
        catalog = [
            _func("a", "a.py", ["if", "return", "rare_token"]),
            _func("b", "b.py", ["for", "return", "rare_token"]),
            _func("c", "c.py", ["if", "return", "other"]),
        ]
        index = build_inverted_index(catalog)
        assert "rare_token" in index
        assert len(index["rare_token"]) == 2

    def test_idf_rare_tokens_higher(self):
        catalog = [
            _func("a", "a.py", ["if", "return", "rare"]),
            _func("b", "b.py", ["if", "return", "common"]),
            _func("c", "c.py", ["if", "common", "other"]),
        ]
        idf = compute_idf(catalog)
        assert idf["rare"] > idf["common"]
        assert idf["if"] < idf["rare"]

    def test_retrieves_candidates_via_shared_tokens(self):
        catalog = [
            _func("a", "a.py", ["if", "return", "domain_specific"]),
            _func("b", "b.py", ["for", "while", "domain_specific"]),
            _func("c", "c.py", ["if", "return", "other"]),
        ]
        index = build_inverted_index(catalog)
        idf = compute_idf(catalog)
        candidates = retrieve_candidates(catalog, index, idf, min_shared_idf=0.1)
        pair_names = set()
        for fa, fb in candidates:
            pair_names.add((fa["name"], fb["name"]))
        assert ("a", "b") in pair_names or ("b", "a") in pair_names


class TestTFIDFScoring:
    def test_identical_functions_score_1(self):
        tokens = ["if", "x", "return", "True"]
        a = _func("foo", "a.py", tokens)
        b = _func("bar", "b.py", tokens)
        idf = {"if": 0.5, "x": 1.5, "return": 0.3, "True": 1.0}
        score = score_pair_tfidf(a, b, idf)
        assert score == pytest.approx(1.0, abs=0.01)

    def test_disjoint_functions_score_0(self):
        a = _func("foo", "a.py", ["alpha", "beta"])
        b = _func("bar", "b.py", ["gamma", "delta"])
        idf = {"alpha": 1.0, "beta": 1.0, "gamma": 1.0, "delta": 1.0}
        score = score_pair_tfidf(a, b, idf)
        assert score == 0.0

    def test_partial_overlap_intermediate_score(self):
        a = _func("foo", "a.py", ["shared", "unique_a"])
        b = _func("bar", "b.py", ["shared", "unique_b"])
        idf = {"shared": 1.0, "unique_a": 1.5, "unique_b": 1.5}
        score = score_pair_tfidf(a, b, idf)
        assert 0.1 < score < 0.9


class TestFullPipeline:
    def test_finds_duplicates(self):
        catalog = [
            _func("format_date", "a.py", ["def", "date", "return", "strftime", "format"]),
            _func("date_to_string", "b.py", ["def", "date", "return", "strftime", "format"]),
            _func("unrelated", "c.py", ["def", "socket", "connect", "send", "recv"]),
        ]
        results = detect_tfidf_duplicates(catalog, threshold=0.3)
        assert len(results) >= 1
        names = set()
        for r in results:
            names.add((r["func_a"]["name"], r["func_b"]["name"]))
        assert ("format_date", "date_to_string") in names or ("date_to_string", "format_date") in names

    def test_empty_catalog(self):
        assert detect_tfidf_duplicates([], threshold=0.3) == []

    def test_single_function(self):
        catalog = [_func("lone", "a.py", ["if", "return"])]
        assert detect_tfidf_duplicates(catalog, threshold=0.3) == []

    def test_output_format(self):
        catalog = [
            _func("a", "a.py", ["x", "y", "z"]),
            _func("b", "b.py", ["x", "y", "z"]),
        ]
        results = detect_tfidf_duplicates(catalog, threshold=0.1)
        if results:
            r = results[0]
            assert "func_a" in r
            assert "func_b" in r
            assert "final_score" in r
            assert r["strategy"] == "tfidf_index"
            assert "name" in r["func_a"]
            assert "file" in r["func_a"]
