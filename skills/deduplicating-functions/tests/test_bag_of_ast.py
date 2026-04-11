#!/usr/bin/env python3
# ABOUTME: Tests for bag-of-AST-nodes cosine similarity duplicate detector.

import importlib.util
import sys
from collections import Counter
from pathlib import Path

import pytest

_scripts = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(_scripts))

_spec = importlib.util.spec_from_file_location(
    "detect_bag_of_ast", _scripts / "detect-bag-of-ast.py"
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

ast_node_vector = _mod.ast_node_vector
cosine_similarity = _mod.cosine_similarity
detect_bag_of_ast_duplicates = _mod.detect_bag_of_ast_duplicates


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _func(name: str, file: str, tokens: list, line: int = 1) -> dict:
    return {
        "name": name,
        "file": file,
        "line": line,
        "qualified_name": name,
        "token_sequence": tokens,
        "body_lines": max(len(tokens), 5),
        "params": [],
    }


# ---------------------------------------------------------------------------
# ast_node_vector
# ---------------------------------------------------------------------------

class TestAstNodeVector:
    def test_returns_counter_of_token_types(self):
        func = _func("f", "a.py", ["If", "Return", "Call", "If", "Return"])
        vec = ast_node_vector(func)
        assert isinstance(vec, Counter)
        assert vec["If"] == 2
        assert vec["Return"] == 2
        assert vec["Call"] == 1

    def test_empty_token_sequence_returns_empty_counter(self):
        func = _func("f", "a.py", [])
        vec = ast_node_vector(func)
        assert vec == Counter()
        assert len(vec) == 0

    def test_missing_token_sequence_returns_empty_counter(self):
        func = {"name": "f", "file": "a.py", "line": 1}
        vec = ast_node_vector(func)
        assert vec == Counter()

    def test_handles_typed_token_dicts(self):
        # token_sequence entries may be dicts with a "type" key
        func = _func("f", "a.py", [
            {"type": "If", "value": "if"},
            {"type": "Return", "value": "return"},
            {"type": "If", "value": "if"},
        ])
        vec = ast_node_vector(func)
        assert vec["If"] == 2
        assert vec["Return"] == 1

    def test_all_node_types_counted(self):
        tokens = ["FunctionDef", "arguments", "If", "Call", "Return", "For", "Call"]
        func = _func("f", "a.py", tokens)
        vec = ast_node_vector(func)
        assert vec["FunctionDef"] == 1
        assert vec["Call"] == 2
        assert vec["For"] == 1
        assert sum(vec.values()) == len(tokens)


# ---------------------------------------------------------------------------
# cosine_similarity
# ---------------------------------------------------------------------------

class TestCosineSimilarity:
    def test_identical_vectors_score_1(self):
        c = Counter({"If": 3, "Return": 2, "Call": 5})
        score = cosine_similarity(c, c)
        assert score == pytest.approx(1.0)

    def test_identical_different_counter_objects_score_1(self):
        a = Counter({"If": 2, "For": 1, "Return": 3})
        b = Counter({"If": 2, "For": 1, "Return": 3})
        assert cosine_similarity(a, b) == pytest.approx(1.0)

    def test_disjoint_vectors_score_0(self):
        a = Counter({"If": 2, "For": 1})
        b = Counter({"While": 3, "Return": 2})
        assert cosine_similarity(a, b) == 0.0

    def test_partial_overlap_intermediate_score(self):
        a = Counter({"If": 2, "Return": 1, "UniqueA": 5})
        b = Counter({"If": 2, "Return": 1, "UniqueB": 5})
        score = cosine_similarity(a, b)
        assert 0.0 < score < 1.0

    def test_empty_counter_a_returns_0(self):
        a = Counter()
        b = Counter({"If": 1, "Return": 2})
        assert cosine_similarity(a, b) == 0.0

    def test_empty_counter_b_returns_0(self):
        a = Counter({"If": 1, "Return": 2})
        b = Counter()
        assert cosine_similarity(a, b) == 0.0

    def test_both_empty_returns_0(self):
        assert cosine_similarity(Counter(), Counter()) == 0.0

    def test_score_bounded_between_0_and_1(self):
        a = Counter({"If": 3, "Call": 2, "Return": 1})
        b = Counter({"If": 1, "Call": 4, "Return": 2, "For": 3})
        score = cosine_similarity(a, b)
        assert 0.0 <= score <= 1.0

    def test_symmetry(self):
        a = Counter({"If": 3, "Return": 1})
        b = Counter({"If": 1, "For": 2, "Return": 3})
        assert cosine_similarity(a, b) == pytest.approx(cosine_similarity(b, a))


# ---------------------------------------------------------------------------
# detect_bag_of_ast_duplicates — empty / trivial cases
# ---------------------------------------------------------------------------

class TestDetectEdgeCases:
    def test_empty_catalog(self):
        assert detect_bag_of_ast_duplicates([]) == []

    def test_single_function(self):
        catalog = [_func("f", "a.py", ["If", "Return", "Call", "For", "Return"])]
        assert detect_bag_of_ast_duplicates(catalog) == []

    def test_functions_with_empty_token_sequences_excluded(self):
        catalog = [
            _func("f", "a.py", []),
            _func("g", "b.py", []),
        ]
        assert detect_bag_of_ast_duplicates(catalog) == []

    def test_one_empty_one_nonempty(self):
        catalog = [
            _func("f", "a.py", []),
            _func("g", "b.py", ["If", "Return", "Call", "For", "While"]),
        ]
        assert detect_bag_of_ast_duplicates(catalog) == []


# ---------------------------------------------------------------------------
# detect_bag_of_ast_duplicates — duplicate detection
# ---------------------------------------------------------------------------

class TestDetectDuplicates:
    def test_finds_known_duplicates(self):
        # Two functions with identical AST node distribution
        tokens = ["FunctionDef", "arguments", "If", "Call", "Return", "For", "Call", "Return"]
        catalog = [
            _func("process_items", "a.py", tokens),
            _func("handle_items", "b.py", tokens),
            _func("connect_socket", "c.py", ["FunctionDef", "Try", "Assign", "Call", "Except", "Return"]),
        ]
        results = detect_bag_of_ast_duplicates(catalog, threshold=0.9)
        assert len(results) >= 1
        names = {(r["func_a"]["name"], r["func_b"]["name"]) for r in results}
        assert ("process_items", "handle_items") in names or \
               ("handle_items", "process_items") in names

    def test_no_false_positives_for_dissimilar_functions(self):
        catalog = [
            _func("file_reader", "a.py", ["Open", "Read", "Close", "Return", "With"]),
            _func("db_writer", "b.py", ["Connect", "Insert", "Commit", "Try", "Except", "Finally"]),
        ]
        results = detect_bag_of_ast_duplicates(catalog, threshold=0.9)
        assert results == []

    def test_threshold_respected(self):
        # Partial overlap pair — should be found at low threshold, not at high
        a_tokens = ["If", "Return", "Call"] * 4 + ["UniqueA"] * 10
        b_tokens = ["If", "Return", "Call"] * 4 + ["UniqueB"] * 10
        catalog = [
            _func("func_a", "a.py", a_tokens),
            _func("func_b", "b.py", b_tokens),
        ]
        results_low = detect_bag_of_ast_duplicates(catalog, threshold=0.1)
        results_high = detect_bag_of_ast_duplicates(catalog, threshold=0.99)
        assert len(results_low) >= 1
        assert len(results_high) == 0

    def test_no_self_pairs(self):
        # Same file + same line should never appear
        tokens = ["If", "Return", "Call", "For", "Return"]
        catalog = [
            {"name": "f", "file": "a.py", "line": 1,
             "token_sequence": tokens, "body_lines": 5, "params": []},
            {"name": "f", "file": "a.py", "line": 1,
             "token_sequence": tokens, "body_lines": 5, "params": []},
        ]
        results = detect_bag_of_ast_duplicates(catalog, threshold=0.0)
        assert results == []

    def test_deduplication_no_repeated_pairs(self):
        tokens = ["If", "Return", "Call", "For", "While"] * 3
        catalog = [
            _func("f1", "a.py", tokens),
            _func("f2", "b.py", tokens),
        ]
        results = detect_bag_of_ast_duplicates(catalog, threshold=0.0)
        assert len(results) == 1  # Exactly one pair, not duplicated


# ---------------------------------------------------------------------------
# Output format
# ---------------------------------------------------------------------------

class TestOutputFormat:
    def test_output_fields_present(self):
        tokens = ["If", "Return", "Call", "For", "While", "Assign"]
        catalog = [
            _func("alpha", "a.py", tokens),
            _func("beta", "b.py", tokens),
        ]
        results = detect_bag_of_ast_duplicates(catalog, threshold=0.0)
        assert len(results) >= 1
        r = results[0]
        assert "func_a" in r
        assert "func_b" in r
        assert "scores" in r
        assert "final_score" in r
        assert r["strategy"] == "bag_of_ast"

    def test_func_ref_fields(self):
        tokens = ["If", "Return", "Call", "For", "While", "Assign"]
        catalog = [
            _func("alpha", "a.py", tokens, line=10),
            _func("beta", "b.py", tokens, line=20),
        ]
        results = detect_bag_of_ast_duplicates(catalog, threshold=0.0)
        assert len(results) >= 1
        r = results[0]
        assert "name" in r["func_a"]
        assert "file" in r["func_a"]
        assert "line" in r["func_a"]
        assert "name" in r["func_b"]
        assert "file" in r["func_b"]
        assert "line" in r["func_b"]

    def test_scores_has_cosine_key(self):
        tokens = ["If", "Return", "Call", "For", "While", "Assign"]
        catalog = [
            _func("alpha", "a.py", tokens),
            _func("beta", "b.py", tokens),
        ]
        results = detect_bag_of_ast_duplicates(catalog, threshold=0.0)
        assert len(results) >= 1
        assert "cosine" in results[0]["scores"]

    def test_final_score_equals_cosine_score(self):
        tokens = ["If", "Return", "Call", "For", "While", "Assign"]
        catalog = [
            _func("alpha", "a.py", tokens),
            _func("beta", "b.py", tokens),
        ]
        results = detect_bag_of_ast_duplicates(catalog, threshold=0.0)
        assert len(results) >= 1
        r = results[0]
        assert r["final_score"] == r["scores"]["cosine"]

    def test_results_sorted_by_score_descending(self):
        # Three functions: pair (a,b) should score higher than pair (a,c)
        tokens_ab = ["If", "Return", "Call"] * 5
        tokens_c = ["If", "Return", "Call"] * 2 + ["Unique"] * 20
        catalog = [
            _func("a", "a.py", tokens_ab),
            _func("b", "b.py", tokens_ab),
            _func("c", "c.py", tokens_c),
        ]
        results = detect_bag_of_ast_duplicates(catalog, threshold=0.0)
        assert len(results) >= 2
        scores = [r["final_score"] for r in results]
        assert scores == sorted(scores, reverse=True)
