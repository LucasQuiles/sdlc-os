#!/usr/bin/env python3
# ABOUTME: Tests for PDG-inspired semantic clone detector.

import importlib.util
import sys
from pathlib import Path

import pytest

_scripts = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(_scripts))

_spec = importlib.util.spec_from_file_location(
    "detect_pdg_semantic", _scripts / "detect-pdg-semantic.py"
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

segment_into_blocks = _mod.segment_into_blocks
compute_pdg_fingerprint = _mod.compute_pdg_fingerprint
detect_pdg_duplicates = _mod.detect_pdg_duplicates


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
# segment_into_blocks
# ---------------------------------------------------------------------------

class TestSegmentIntoBlocks:
    def test_empty_sequence_returns_empty(self):
        assert segment_into_blocks([]) == []

    def test_single_boundary_token_makes_one_block(self):
        blocks = segment_into_blocks(["If"])
        assert blocks == [["If"]]

    def test_non_boundary_tokens_before_first_boundary_form_own_block(self):
        # Tokens before the first boundary go into their own block
        blocks = segment_into_blocks(["Name", "Load", "If", "Return"])
        assert len(blocks) == 3
        assert blocks[0] == ["Name", "Load"]
        assert blocks[1] == ["If"]
        assert blocks[2] == ["Return"]

    def test_boundary_starts_new_block(self):
        blocks = segment_into_blocks(["If", "Name", "Call", "Return", "Name"])
        assert len(blocks) == 2
        assert blocks[0] == ["If", "Name", "Call"]
        assert blocks[1] == ["Return", "Name"]

    def test_consecutive_boundaries_each_get_own_block(self):
        blocks = segment_into_blocks(["If", "Return", "Assign"])
        assert len(blocks) == 3
        assert blocks[0] == ["If"]
        assert blocks[1] == ["Return"]
        assert blocks[2] == ["Assign"]

    def test_no_boundaries_is_single_block(self):
        tokens = ["Name", "Load", "Call", "Attribute"]
        blocks = segment_into_blocks(tokens)
        assert blocks == [tokens]

    def test_all_boundary_types_recognised(self):
        boundary_tokens = [
            "FunctionDef", "AsyncFunctionDef", "If", "For", "While",
            "Try", "With", "Return", "Assign", "AugAssign", "Expr",
            "Raise", "Assert", "Delete", "Import", "ClassDef",
        ]
        blocks = segment_into_blocks(boundary_tokens)
        assert len(blocks) == len(boundary_tokens)
        for i, tok in enumerate(boundary_tokens):
            assert blocks[i][0] == tok


# ---------------------------------------------------------------------------
# compute_pdg_fingerprint
# ---------------------------------------------------------------------------

class TestComputePdgFingerprint:
    def test_returns_set_of_ints(self):
        func = _func("f", "a.py", ["If", "Name", "Return", "Name"])
        fp = compute_pdg_fingerprint(func)
        assert isinstance(fp, set)
        for h in fp:
            assert isinstance(h, int)

    def test_identical_token_sequences_produce_same_fingerprint(self):
        tokens = ["If", "Name", "Call", "Return", "Name", "Assign", "Name"]
        f1 = _func("f1", "a.py", tokens)
        f2 = _func("f2", "b.py", tokens)
        assert compute_pdg_fingerprint(f1) == compute_pdg_fingerprint(f2)

    def test_identical_sequences_jaccard_is_1(self):
        from lib.common import jaccard
        tokens = ["If", "Name", "Call", "Return", "Name", "Assign", "Name"]
        fp1 = compute_pdg_fingerprint(_func("f1", "a.py", tokens))
        fp2 = compute_pdg_fingerprint(_func("f2", "b.py", tokens))
        assert jaccard(fp1, fp2) == pytest.approx(1.0)

    def test_completely_different_sequences_low_jaccard(self):
        from lib.common import jaccard
        # Distinct boundary tokens → distinct block hashes
        f1 = _func("f1", "a.py", ["If", "Name", "Return", "Name"])
        f2 = _func("f2", "b.py", ["For", "Call", "While", "Call", "Assign"])
        fp1 = compute_pdg_fingerprint(f1)
        fp2 = compute_pdg_fingerprint(f2)
        assert jaccard(fp1, fp2) < 0.5

    def test_shared_prefix_different_tail_moderate_similarity(self):
        from lib.common import jaccard
        # Two functions sharing the same opening blocks but diverging at the end.
        # Blocks 0-1 share identical shape AND identical context (same prev/next),
        # while the final blocks differ — giving a score between 0 and 1.
        s1 = ["Assign", "Name", "If", "Name", "Call", "Return", "Name", "For", "Call"]
        s2 = ["Assign", "Name", "If", "Name", "Call", "Return", "Name", "While", "Call"]
        fp1 = compute_pdg_fingerprint(_func("f1", "a.py", s1))
        fp2 = compute_pdg_fingerprint(_func("f2", "b.py", s2))
        score = jaccard(fp1, fp2)
        # Shared prefix hashes → non-zero; differing tail hashes → not 1
        assert 0.0 < score < 1.0

    def test_empty_token_sequence_returns_empty_set(self):
        func = _func("f", "a.py", [])
        assert compute_pdg_fingerprint(func) == set()

    def test_missing_token_sequence_returns_empty_set(self):
        func = {"name": "f", "file": "a.py", "line": 1}
        assert compute_pdg_fingerprint(func) == set()

    def test_very_short_sequence_single_non_boundary_returns_empty(self):
        # A single non-boundary token produces one block, which is non-empty
        func = _func("f", "a.py", ["Name"])
        fp = compute_pdg_fingerprint(func)
        # One block → one hash
        assert len(fp) == 1

    def test_very_short_boundary_only_returns_nonempty(self):
        func = _func("f", "a.py", ["Return"])
        fp = compute_pdg_fingerprint(func)
        assert len(fp) == 1

    def test_accepts_typed_token_dicts(self):
        # token_sequence may contain {"type": "If", "value": "if"} dicts
        tokens = [
            {"type": "If", "value": "if"},
            {"type": "Name", "value": "x"},
            {"type": "Return", "value": "return"},
        ]
        func = _func("f", "a.py", tokens)
        fp = compute_pdg_fingerprint(func)
        assert isinstance(fp, set)
        assert len(fp) >= 1

    def test_fingerprint_size_grows_with_more_blocks(self):
        small = _func("f", "a.py", ["If", "Return"])
        large = _func("g", "b.py", ["If", "Name", "Return", "Assign", "Name", "For", "Call"])
        fp_small = compute_pdg_fingerprint(small)
        fp_large = compute_pdg_fingerprint(large)
        assert len(fp_large) >= len(fp_small)


# ---------------------------------------------------------------------------
# detect_pdg_duplicates — edge cases
# ---------------------------------------------------------------------------

class TestDetectEdgeCases:
    def test_empty_catalog_returns_empty(self):
        assert detect_pdg_duplicates([]) == []

    def test_single_function_returns_empty(self):
        catalog = [_func("f", "a.py", ["If", "Name", "Return", "Name"])]
        assert detect_pdg_duplicates(catalog) == []

    def test_functions_with_empty_token_sequences_excluded(self):
        catalog = [
            _func("f", "a.py", []),
            _func("g", "b.py", []),
        ]
        assert detect_pdg_duplicates(catalog) == []

    def test_one_empty_one_nonempty(self):
        catalog = [
            _func("f", "a.py", []),
            _func("g", "b.py", ["If", "Name", "Return", "Name", "Assign"]),
        ]
        assert detect_pdg_duplicates(catalog) == []

    def test_no_self_pairs(self):
        tokens = ["If", "Name", "Call", "Return", "Name"]
        catalog = [
            {"name": "f", "file": "a.py", "line": 1,
             "token_sequence": tokens, "body_lines": 5, "params": []},
            {"name": "f", "file": "a.py", "line": 1,
             "token_sequence": tokens, "body_lines": 5, "params": []},
        ]
        results = detect_pdg_duplicates(catalog, threshold=0.0)
        assert results == []


# ---------------------------------------------------------------------------
# detect_pdg_duplicates — clone detection
# ---------------------------------------------------------------------------

class TestDetectDuplicates:
    def test_finds_identical_functions(self):
        tokens = ["If", "Name", "Call", "Return", "Name", "Assign", "Name", "For", "Call"]
        catalog = [
            _func("process", "a.py", tokens),
            _func("handle", "b.py", tokens),
            _func("unrelated", "c.py", ["While", "Call", "Try", "Return"]),
        ]
        results = detect_pdg_duplicates(catalog, threshold=0.9)
        assert len(results) >= 1
        names = {(r["func_a"]["name"], r["func_b"]["name"]) for r in results}
        assert ("process", "handle") in names or ("handle", "process") in names

    def test_no_false_positives_for_dissimilar_functions(self):
        catalog = [
            _func("read_file", "a.py", ["With", "Name", "Call", "Return", "Name"]),
            _func("sort_data", "b.py", ["For", "If", "Assign", "Name", "AugAssign", "Return"]),
        ]
        results = detect_pdg_duplicates(catalog, threshold=0.9)
        assert results == []

    def test_threshold_respected(self):
        tokens = ["If", "Name", "Return", "Name"] * 4
        catalog = [
            _func("f", "a.py", tokens),
            _func("g", "b.py", tokens),
        ]
        assert len(detect_pdg_duplicates(catalog, threshold=0.0)) >= 1
        assert len(detect_pdg_duplicates(catalog, threshold=1.1)) == 0

    def test_deduplication_no_repeated_pairs(self):
        tokens = ["If", "Name", "Call", "Return", "Name", "Assign", "Name"]
        catalog = [
            _func("f1", "a.py", tokens),
            _func("f2", "b.py", tokens),
        ]
        results = detect_pdg_duplicates(catalog, threshold=0.0)
        assert len(results) == 1

    def test_results_sorted_by_score_descending(self):
        # Three functions: (a,b) perfectly identical, (a,c) partial overlap
        tokens_ab = ["If", "Name", "Return", "Name", "Assign", "Name"] * 3
        tokens_c = ["If", "Name", "Return", "Name"] * 2 + ["While", "Call"] * 5
        catalog = [
            _func("a", "a.py", tokens_ab),
            _func("b", "b.py", tokens_ab),
            _func("c", "c.py", tokens_c),
        ]
        results = detect_pdg_duplicates(catalog, threshold=0.0)
        assert len(results) >= 1
        scores = [r["final_score"] for r in results]
        assert scores == sorted(scores, reverse=True)


# ---------------------------------------------------------------------------
# Output format
# ---------------------------------------------------------------------------

class TestOutputFormat:
    def test_strategy_is_pdg_semantic(self):
        tokens = ["If", "Name", "Return", "Name", "Assign", "Name", "For", "Call"]
        catalog = [
            _func("alpha", "a.py", tokens),
            _func("beta", "b.py", tokens),
        ]
        results = detect_pdg_duplicates(catalog, threshold=0.0)
        assert len(results) >= 1
        assert results[0]["strategy"] == "pdg_semantic"

    def test_required_top_level_keys_present(self):
        tokens = ["If", "Name", "Return", "Name", "Assign", "Name"]
        catalog = [
            _func("alpha", "a.py", tokens),
            _func("beta", "b.py", tokens),
        ]
        results = detect_pdg_duplicates(catalog, threshold=0.0)
        assert len(results) >= 1
        r = results[0]
        assert "func_a" in r
        assert "func_b" in r
        assert "scores" in r
        assert "final_score" in r
        assert "strategy" in r

    def test_scores_has_pdg_jaccard_key(self):
        tokens = ["If", "Name", "Return", "Name", "Assign", "Name"]
        catalog = [
            _func("alpha", "a.py", tokens),
            _func("beta", "b.py", tokens),
        ]
        results = detect_pdg_duplicates(catalog, threshold=0.0)
        assert len(results) >= 1
        assert "pdg_jaccard" in results[0]["scores"]

    def test_final_score_equals_pdg_jaccard(self):
        tokens = ["If", "Name", "Return", "Name", "Assign", "Name"]
        catalog = [
            _func("alpha", "a.py", tokens),
            _func("beta", "b.py", tokens),
        ]
        results = detect_pdg_duplicates(catalog, threshold=0.0)
        assert len(results) >= 1
        r = results[0]
        assert r["final_score"] == r["scores"]["pdg_jaccard"]

    def test_func_ref_fields_present(self):
        tokens = ["If", "Name", "Return", "Name", "Assign", "Name"]
        catalog = [
            _func("alpha", "a.py", tokens, line=10),
            _func("beta", "b.py", tokens, line=20),
        ]
        results = detect_pdg_duplicates(catalog, threshold=0.0)
        assert len(results) >= 1
        r = results[0]
        for ref_key in ("func_a", "func_b"):
            assert "name" in r[ref_key]
            assert "file" in r[ref_key]
            assert "line" in r[ref_key]

    def test_pdg_jaccard_is_float_between_0_and_1(self):
        tokens = ["If", "Name", "Return", "Name", "Assign", "Name"]
        catalog = [
            _func("alpha", "a.py", tokens),
            _func("beta", "b.py", tokens),
        ]
        results = detect_pdg_duplicates(catalog, threshold=0.0)
        assert len(results) >= 1
        score = results[0]["scores"]["pdg_jaccard"]
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
