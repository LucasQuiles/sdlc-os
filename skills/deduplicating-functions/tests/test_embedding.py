#!/usr/bin/env python3
# ABOUTME: Tests for Code2Vec-lite AST path embedding duplicate detector.
# Covers: extract_ast_paths, build_embedding, embedding_cosine, detect_embedding_duplicates.

import importlib.util
import sys
from collections import Counter
from pathlib import Path

import pytest

_scripts = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(_scripts))

_spec = importlib.util.spec_from_file_location(
    "detect_code_embedding", _scripts / "detect-code-embedding.py"
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

extract_ast_paths = _mod.extract_ast_paths
build_embedding = _mod.build_embedding
embedding_cosine = _mod.embedding_cosine
detect_embedding_duplicates = _mod.detect_embedding_duplicates


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
# extract_ast_paths
# ---------------------------------------------------------------------------

class TestExtractAstPaths:
    def test_extracts_3_4_5_grams_from_example(self):
        tokens = ["If", "Compare", "Call", "Return", "Name"]
        paths = extract_ast_paths(tokens, min_len=3, max_len=5)
        # 3-grams
        assert ("If", "Compare", "Call") in paths
        assert ("Compare", "Call", "Return") in paths
        assert ("Call", "Return", "Name") in paths
        # 4-grams
        assert ("If", "Compare", "Call", "Return") in paths
        assert ("Compare", "Call", "Return", "Name") in paths
        # 5-gram
        assert ("If", "Compare", "Call", "Return", "Name") in paths

    def test_correct_count_for_known_sequence(self):
        tokens = ["If", "Compare", "Call", "Return", "Name"]
        paths = extract_ast_paths(tokens, min_len=3, max_len=5)
        # 3 three-grams + 2 four-grams + 1 five-gram = 6
        assert len(paths) == 6

    def test_empty_sequence_returns_empty_list(self):
        assert extract_ast_paths([], min_len=3, max_len=5) == []

    def test_non_list_returns_empty(self):
        assert extract_ast_paths(None, min_len=3, max_len=5) == []  # type: ignore[arg-type]

    def test_sequence_shorter_than_min_len_returns_empty(self):
        assert extract_ast_paths(["If", "Return"], min_len=3, max_len=5) == []

    def test_sequence_exactly_min_len(self):
        tokens = ["If", "Return", "Call"]
        paths = extract_ast_paths(tokens, min_len=3, max_len=5)
        assert paths == [("If", "Return", "Call")]

    def test_only_3_grams_when_max_equals_min(self):
        tokens = ["A", "B", "C", "D"]
        paths = extract_ast_paths(tokens, min_len=3, max_len=3)
        assert paths == [("A", "B", "C"), ("B", "C", "D")]

    def test_all_paths_are_tuples(self):
        tokens = ["X", "Y", "Z", "W", "V"]
        paths = extract_ast_paths(tokens, min_len=2, max_len=4)
        for p in paths:
            assert isinstance(p, tuple)

    def test_handles_typed_token_dicts(self):
        tokens = [
            {"type": "If", "value": "if"},
            {"type": "Compare", "value": "compare"},
            {"type": "Call", "value": "call"},
        ]
        paths = extract_ast_paths(tokens, min_len=3, max_len=3)
        assert ("If", "Compare", "Call") in paths

    def test_mixed_str_and_dict_tokens(self):
        tokens = ["If", {"type": "Compare", "value": "compare"}, "Call"]
        paths = extract_ast_paths(tokens, min_len=3, max_len=3)
        assert ("If", "Compare", "Call") in paths

    def test_single_element_min_len_1(self):
        paths = extract_ast_paths(["X"], min_len=1, max_len=1)
        assert paths == [("X",)]

    def test_paths_respect_max_len_cap(self):
        tokens = ["A", "B", "C", "D", "E", "F"]
        paths = extract_ast_paths(tokens, min_len=2, max_len=3)
        for p in paths:
            assert 2 <= len(p) <= 3


# ---------------------------------------------------------------------------
# build_embedding
# ---------------------------------------------------------------------------

class TestBuildEmbedding:
    def test_returns_counter(self):
        func = _func("f", "a.py", ["If", "Call", "Return", "For", "Return"])
        emb = build_embedding(func)
        assert isinstance(emb, Counter)

    def test_empty_token_sequence_returns_empty_counter(self):
        func = _func("f", "a.py", [])
        assert build_embedding(func) == Counter()

    def test_missing_token_sequence_returns_empty_counter(self):
        func = {"name": "f", "file": "a.py", "line": 1}
        assert build_embedding(func) == Counter()

    def test_path_counts_accumulated(self):
        # Two occurrences of the same 3-gram
        tokens = ["If", "Return", "Call", "If", "Return", "Call"]
        emb = build_embedding(func={"name": "f", "file": "a.py", "line": 1,
                                     "token_sequence": tokens})
        assert emb[("If", "Return", "Call")] == 2

    def test_sequence_too_short_returns_empty(self):
        func = _func("f", "a.py", ["If", "Return"])  # length 2, min_len default 3
        assert build_embedding(func) == Counter()

    def test_custom_min_max_len_used(self):
        tokens = ["A", "B", "C"]
        func = _func("f", "a.py", tokens)
        emb2 = build_embedding(func, min_len=2, max_len=2)
        assert ("A", "B") in emb2
        assert ("B", "C") in emb2
        # No 3-grams because max_len=2
        assert ("A", "B", "C") not in emb2

    def test_identical_token_sequences_same_embedding(self):
        tokens = ["If", "Call", "Return", "For", "Assign", "Return"]
        fa = _func("f", "a.py", tokens)
        fb = _func("g", "b.py", tokens)
        assert build_embedding(fa) == build_embedding(fb)


# ---------------------------------------------------------------------------
# embedding_cosine
# ---------------------------------------------------------------------------

class TestEmbeddingCosine:
    def test_identical_embeddings_score_1(self):
        c: Counter = Counter({("If", "Return", "Call"): 3, ("Call", "For", "While"): 2})
        assert embedding_cosine(c, c) == pytest.approx(1.0)

    def test_identical_different_counter_objects_score_1(self):
        a: Counter = Counter({("A", "B", "C"): 2, ("B", "C", "D"): 1})
        b: Counter = Counter({("A", "B", "C"): 2, ("B", "C", "D"): 1})
        assert embedding_cosine(a, b) == pytest.approx(1.0)

    def test_disjoint_embeddings_score_0(self):
        a: Counter = Counter({("If", "Return", "Call"): 2})
        b: Counter = Counter({("For", "While", "Break"): 3})
        assert embedding_cosine(a, b) == 0.0

    def test_partial_overlap_intermediate_score(self):
        shared = ("If", "Return", "Call")
        a: Counter = Counter({shared: 3, ("UniqueA", "X", "Y"): 10})
        b: Counter = Counter({shared: 3, ("UniqueB", "P", "Q"): 10})
        score = embedding_cosine(a, b)
        assert 0.0 < score < 1.0

    def test_empty_a_returns_0(self):
        b: Counter = Counter({("A", "B", "C"): 1})
        assert embedding_cosine(Counter(), b) == 0.0

    def test_empty_b_returns_0(self):
        a: Counter = Counter({("A", "B", "C"): 1})
        assert embedding_cosine(a, Counter()) == 0.0

    def test_both_empty_returns_0(self):
        assert embedding_cosine(Counter(), Counter()) == 0.0

    def test_symmetry(self):
        a: Counter = Counter({("A", "B", "C"): 3, ("B", "C", "D"): 1})
        b: Counter = Counter({("A", "B", "C"): 1, ("C", "D", "E"): 4})
        assert embedding_cosine(a, b) == pytest.approx(embedding_cosine(b, a))

    def test_score_bounded_0_to_1(self):
        a: Counter = Counter({("X", "Y", "Z"): 3, ("A", "B", "C"): 2})
        b: Counter = Counter({("X", "Y", "Z"): 1, ("A", "B", "C"): 4, ("D", "E", "F"): 3})
        score = embedding_cosine(a, b)
        assert 0.0 <= score <= 1.0


# ---------------------------------------------------------------------------
# detect_embedding_duplicates — edge cases
# ---------------------------------------------------------------------------

class TestDetectEdgeCases:
    def test_empty_catalog(self):
        assert detect_embedding_duplicates([]) == []

    def test_single_function(self):
        catalog = [_func("lone", "a.py", ["If", "Return", "Call", "For", "Return"])]
        assert detect_embedding_duplicates(catalog) == []

    def test_both_empty_token_sequences_excluded(self):
        catalog = [
            _func("f", "a.py", []),
            _func("g", "b.py", []),
        ]
        assert detect_embedding_duplicates(catalog) == []

    def test_one_empty_one_nonempty_no_results(self):
        catalog = [
            _func("f", "a.py", []),
            _func("g", "b.py", ["If", "Return", "Call", "For", "While"]),
        ]
        assert detect_embedding_duplicates(catalog) == []

    def test_both_too_short_excluded(self):
        # Sequences of length 2 < default min_len=3, so embeddings are empty
        catalog = [
            _func("f", "a.py", ["If", "Return"]),
            _func("g", "b.py", ["If", "Return"]),
        ]
        assert detect_embedding_duplicates(catalog) == []


# ---------------------------------------------------------------------------
# detect_embedding_duplicates — detection quality
# ---------------------------------------------------------------------------

class TestDetectDuplicates:
    def test_finds_identical_structural_duplicates(self):
        tokens = ["FunctionDef", "If", "Compare", "Call", "Return", "For", "Call", "Return"]
        catalog = [
            _func("process_items", "a.py", tokens),
            _func("handle_items", "b.py", tokens),
            _func("connect_socket", "c.py", ["Try", "Assign", "Call", "Except", "Return",
                                              "Finally", "Close", "Log"]),
        ]
        results = detect_embedding_duplicates(catalog, threshold=0.9)
        assert len(results) >= 1
        names = {(r["func_a"]["name"], r["func_b"]["name"]) for r in results}
        assert ("process_items", "handle_items") in names or \
               ("handle_items", "process_items") in names

    def test_no_false_positives_for_dissimilar_functions(self):
        catalog = [
            _func("file_reader", "a.py",
                  ["Open", "Read", "Close", "Return", "With", "For", "Line"]),
            _func("db_writer", "b.py",
                  ["Connect", "Insert", "Commit", "Try", "Except", "Finally", "Rollback"]),
        ]
        results = detect_embedding_duplicates(catalog, threshold=0.9)
        assert results == []

    def test_threshold_respected(self):
        # Pairs with partial overlap: detectable at low threshold, not at high
        shared = ["If", "Return", "Call"] * 4
        a_tokens = shared + ["UniqueA1", "UniqueA2", "UniqueA3"] * 5
        b_tokens = shared + ["UniqueB1", "UniqueB2", "UniqueB3"] * 5
        catalog = [
            _func("func_a", "a.py", a_tokens),
            _func("func_b", "b.py", b_tokens),
        ]
        results_low = detect_embedding_duplicates(catalog, threshold=0.05)
        results_high = detect_embedding_duplicates(catalog, threshold=0.99)
        assert len(results_low) >= 1
        assert len(results_high) == 0

    def test_no_self_pairs(self):
        tokens = ["If", "Return", "Call", "For", "Return", "While"]
        catalog = [
            {"name": "f", "file": "a.py", "line": 1,
             "token_sequence": tokens, "body_lines": 6, "params": []},
            {"name": "f", "file": "a.py", "line": 1,
             "token_sequence": tokens, "body_lines": 6, "params": []},
        ]
        results = detect_embedding_duplicates(catalog, threshold=0.0)
        assert results == []

    def test_no_duplicate_pairs(self):
        tokens = ["If", "Return", "Call", "For", "While"] * 3
        catalog = [
            _func("f1", "a.py", tokens),
            _func("f2", "b.py", tokens),
        ]
        results = detect_embedding_duplicates(catalog, threshold=0.0)
        assert len(results) == 1

    def test_sorted_by_score_descending(self):
        tokens_ab = ["If", "Return", "Call"] * 5
        tokens_c = ["If", "Return", "Call"] * 2 + ["Unique1", "Unique2", "Unique3"] * 8
        catalog = [
            _func("a", "a.py", tokens_ab),
            _func("b", "b.py", tokens_ab),
            _func("c", "c.py", tokens_c),
        ]
        results = detect_embedding_duplicates(catalog, threshold=0.0)
        assert len(results) >= 2
        scores = [r["final_score"] for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_captures_structural_paths_not_just_unigrams(self):
        # Two functions with same node-type unigrams but different ordering.
        # One pair has matching paths; the other just shares the same bag of nodes.
        ordered_tokens = ["If", "Call", "Return", "For", "Call", "Return",
                          "If", "Call", "Return", "For", "Call", "Return"]
        shuffled_tokens = ["Call", "Return", "For", "If", "Return", "Call",
                           "For", "Return", "Call", "If", "Call", "Return"]
        catalog = [
            _func("ordered_a", "a.py", ordered_tokens),
            _func("ordered_b", "b.py", ordered_tokens),
            _func("shuffled", "c.py", shuffled_tokens),
        ]
        results = detect_embedding_duplicates(catalog, threshold=0.0)
        # ordered_a vs ordered_b should score higher than ordered_a vs shuffled
        scores = {
            frozenset([r["func_a"]["name"], r["func_b"]["name"]]): r["final_score"]
            for r in results
        }
        ordered_score = scores.get(frozenset(["ordered_a", "ordered_b"]), 0.0)
        shuffled_score = scores.get(
            frozenset(["ordered_a", "shuffled"]),
            scores.get(frozenset(["ordered_b", "shuffled"]), 0.0),
        )
        assert ordered_score >= shuffled_score


# ---------------------------------------------------------------------------
# Output format
# ---------------------------------------------------------------------------

class TestOutputFormat:
    def test_required_top_level_keys(self):
        tokens = ["If", "Return", "Call", "For", "While", "Assign"]
        catalog = [
            _func("alpha", "a.py", tokens),
            _func("beta", "b.py", tokens),
        ]
        results = detect_embedding_duplicates(catalog, threshold=0.0)
        assert len(results) >= 1
        r = results[0]
        for key in ("func_a", "func_b", "scores", "final_score", "strategy"):
            assert key in r, f"missing key: {key}"

    def test_strategy_is_code_embedding(self):
        tokens = ["If", "Return", "Call", "For", "While", "Assign"]
        catalog = [
            _func("alpha", "a.py", tokens),
            _func("beta", "b.py", tokens),
        ]
        results = detect_embedding_duplicates(catalog, threshold=0.0)
        for r in results:
            assert r["strategy"] == "code_embedding"

    def test_scores_has_path_cosine_key(self):
        tokens = ["If", "Return", "Call", "For", "While", "Assign"]
        catalog = [
            _func("alpha", "a.py", tokens),
            _func("beta", "b.py", tokens),
        ]
        results = detect_embedding_duplicates(catalog, threshold=0.0)
        assert len(results) >= 1
        assert "path_cosine" in results[0]["scores"]

    def test_final_score_equals_path_cosine(self):
        tokens = ["If", "Return", "Call", "For", "While", "Assign"]
        catalog = [
            _func("alpha", "a.py", tokens),
            _func("beta", "b.py", tokens),
        ]
        results = detect_embedding_duplicates(catalog, threshold=0.0)
        assert len(results) >= 1
        r = results[0]
        assert r["final_score"] == r["scores"]["path_cosine"]

    def test_func_ref_has_name_file_line(self):
        tokens = ["If", "Return", "Call", "For", "While", "Assign"]
        catalog = [
            _func("alpha", "a.py", tokens, line=10),
            _func("beta", "b.py", tokens, line=20),
        ]
        results = detect_embedding_duplicates(catalog, threshold=0.0)
        assert len(results) >= 1
        r = results[0]
        for ref_key in ("func_a", "func_b"):
            ref = r[ref_key]
            assert "name" in ref
            assert "file" in ref
            assert "line" in ref

    def test_func_ref_values_correct(self):
        tokens = ["If", "Return", "Call", "For", "While", "Assign"]
        catalog = [
            _func("alpha", "a.py", tokens, line=10),
            _func("beta", "b.py", tokens, line=20),
        ]
        results = detect_embedding_duplicates(catalog, threshold=0.0)
        assert len(results) >= 1
        r = results[0]
        names = {r["func_a"]["name"], r["func_b"]["name"]}
        assert names == {"alpha", "beta"}

    def test_scores_path_cosine_is_float_in_range(self):
        tokens = ["If", "Return", "Call", "For", "While", "Assign"]
        catalog = [
            _func("alpha", "a.py", tokens),
            _func("beta", "b.py", tokens),
        ]
        results = detect_embedding_duplicates(catalog, threshold=0.0)
        assert len(results) >= 1
        score = results[0]["scores"]["path_cosine"]
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
