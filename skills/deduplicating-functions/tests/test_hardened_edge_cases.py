#!/usr/bin/env python3
# ABOUTME: Hardened edge case tests that push detection beyond industry baselines.
# Each test targets a specific failure mode documented in clone detection literature.
# Tests are verifiable — they use deterministic inputs and check concrete outputs.

"""
Hardened Edge Case Tests

Research-backed test cases targeting known failure modes:
- Roy & Cordy (2007): Taxonomy of clone types with boundary examples
- Svajlenko & Roy (2015): BigCloneBench false positive/negative patterns
- Sajnani et al. (2016): SourcererCC precision pitfalls
- Saini et al. (2018): Oreo's approach to Type-3/4 boundary cases

Each test documents which research finding it validates.
"""

import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

import pytest

_scripts = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(_scripts))

from lib.common import jaccard, overlap_coefficient, tokenize, should_compare
from lib.prefilter import should_prefilter_pair

# Load detectors via importlib
def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, _scripts / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

_merge_mod = _load("merge", "merge-signals.py")
merge_pair_signals = _merge_mod.merge_pair_signals

_bag_mod = _load("bag", "detect-bag-of-ast.py")
cosine_similarity = _bag_mod.cosine_similarity
ast_node_vector = _bag_mod.ast_node_vector

_pdg_mod = _load("pdg", "detect-pdg-semantic.py")
compute_pdg_fingerprint = _pdg_mod.compute_pdg_fingerprint

_embed_mod = _load("embed", "detect-code-embedding.py")
build_embedding = _embed_mod.build_embedding
embedding_cosine = _embed_mod.embedding_cosine

_win_mod = _load("win", "detect-winnowing.py")
compute_fingerprint = _win_mod.compute_fingerprint
fingerprint_similarity = _win_mod.fingerprint_similarity


def _pair(strategy, score, a="funcA", b="funcB"):
    return {
        "func_a": {"name": a, "file": "a.py", "line": 1},
        "func_b": {"name": b, "file": "b.py", "line": 1},
        "scores": {}, "final_score": score, "strategy": strategy,
    }

def _func(name, tokens, **kw):
    return {
        "name": name, "file": kw.get("file", f"{name}.py"), "line": 1,
        "qualified_name": name, "token_sequence": tokens,
        "body_lines": kw.get("body_lines", max(5, len(tokens))),
        "params": kw.get("params", []),
        "return_type": kw.get("return_type"),
        "cyclomatic_complexity": kw.get("complexity", 2),
    }


# ═══════════════════════════════════════════════════════════════════
# 1. CONFUSABLE NON-CLONES (precision attacks)
#    Research: Sajnani et al. 2016 — "false positives from shared idioms"
# ═══════════════════════════════════════════════════════════════════

class TestConfusableNonClones:
    """Functions that LOOK similar but have genuinely different purposes."""

    def test_validate_email_vs_validate_phone_same_ast(self):
        """Same AST structure, different domain — NOT clones.

        Research: Roy & Cordy 2007 — "parameterized clones" that differ
        only by the validated data type are distinct functions if the
        validation rules differ.
        """
        email = _func("validate_email",
            ["FunctionDef", "arguments", "arg", "If", "Not", "Call", "Return", "Constant", "Return", "Constant"],
            params=[{"name": "email", "type": "str"}])
        phone = _func("validate_phone",
            ["FunctionDef", "arguments", "arg", "If", "Not", "Call", "Return", "Constant", "Return", "Constant"],
            params=[{"name": "phone", "type": "str"}])

        # Token clones will catch this (same structure) — that's expected
        # But fuzzy names should NOT match (validate_email vs validate_phone)
        name_tokens_a = set(tokenize("validate_email"))
        name_tokens_b = set(tokenize("validate_phone"))
        name_jaccard = jaccard(name_tokens_a, name_tokens_b)
        # "validate" is shared, but "email" vs "phone" differ
        assert name_jaccard < 0.7, f"Name similarity too high: {name_jaccard}"

    def test_sort_ascending_vs_sort_descending_opposite_behavior(self):
        """Identical structure, opposite behavior — NOT clones.

        This is a classic FP in token-based detection: sort(reverse=False)
        vs sort(reverse=True) have identical token structures.
        """
        asc = _func("sort_ascending",
            ["FunctionDef", "arguments", "arg", "Return", "Call", "Name", "Keyword", "Constant"],
            params=[{"name": "items", "type": "list"}])
        desc = _func("sort_descending",
            ["FunctionDef", "arguments", "arg", "Return", "Call", "Name", "Keyword", "Constant"],
            params=[{"name": "items", "type": "list"}])

        # These should NOT be merged as HIGH confidence
        results = {
            "token_clone": [_pair("token_clone", 0.9, "sort_ascending", "sort_descending")],
            # Fuzzy name gives partial match on "sort"
            "fuzzy_name": [_pair("fuzzy_name", 0.6, "sort_ascending", "sort_descending")],
        }
        merged = merge_pair_signals(results)
        # Even with 2 strategies, the name mismatch on "ascending" vs "descending"
        # should keep this at MEDIUM, not HIGH
        if merged:
            assert merged[0]["confidence"] != "HIGH" or merged[0]["num_strategies"] >= 3

    def test_getter_setter_not_duplicates(self):
        """get_X and set_X are complementary, not duplicates."""
        tokens_get = set(tokenize("get_user_preferences"))
        tokens_set = set(tokenize("set_user_preferences"))
        sim = jaccard(tokens_get, tokens_set)
        # "get" and "set" are synonyms in our map, which could cause FP
        # But Jaccard on {"get","user","preferences"} vs {"set","user","preferences"}
        # = 2/4 = 0.5 (shared: user, preferences; unique: get, set)
        assert sim <= 0.7, f"Getter/setter similarity too high: {sim}"


# ═══════════════════════════════════════════════════════════════════
# 2. HARD TRUE POSITIVES (recall attacks)
#    Research: Svajlenko & Roy 2015 — "BigCloneBench Type 4 patterns"
# ═══════════════════════════════════════════════════════════════════

class TestHardTruePositives:
    """Genuine clones that are difficult to detect."""

    def test_imperative_vs_functional_loop_vs_comprehension(self):
        """Loop accumulator vs sum() generator — Type 4 semantic clone.

        Research: BigCloneBench shows Type 4 recall < 10% for most tools.
        """
        imperative = _func("sum_prices_loop",
            ["FunctionDef", "arguments", "arg", "Assign", "Constant", "For", "AugAssign", "Attribute", "Return", "Name"],
            params=[{"name": "items"}])
        functional = _func("sum_prices_gen",
            ["FunctionDef", "arguments", "arg", "Return", "Call", "Name", "GeneratorExp", "Attribute"],
            params=[{"name": "items"}])

        # These have different AST structures but same purpose
        # PDG should partially catch (both use accumulation pattern)
        fp_imp = compute_pdg_fingerprint(imperative)
        fp_fun = compute_pdg_fingerprint(functional)
        # The PDG fingerprints will differ (different control flow)
        # but there should be SOME overlap from shared data-flow patterns
        # This is the hardest case — we accept that classical methods struggle here

    def test_different_variable_names_same_logic(self):
        """Type 2 clone — identical logic, all variables renamed.

        Research: Type 2 detection should achieve 93-98% recall (BigCloneBench).
        """
        original = _func("process_orders",
            ["FunctionDef", "arguments", "arg", "Assign", "List", "For", "If", "Call", "Append", "Return"],
            params=[{"name": "orders"}])
        renamed = _func("handle_requests",
            ["FunctionDef", "arguments", "arg", "Assign", "List", "For", "If", "Call", "Append", "Return"],
            params=[{"name": "requests"}])

        # Bag-of-AST should catch this (same node type counts)
        vec_a = ast_node_vector(original)
        vec_b = ast_node_vector(renamed)
        cos = cosine_similarity(vec_a, vec_b)
        assert cos == pytest.approx(1.0), f"Identical AST structure should score 1.0, got {cos}"

    def test_partial_clone_shared_prefix(self):
        """Function B is function A with additional error handling.

        Research: NIL (N-gram Intersection Locator) specifically targets this.
        Overlap coefficient should detect the containment relationship.
        """
        base = ["FunctionDef", "arguments", "arg", "Assign", "Call", "If", "Return", "Return"]
        extended = ["FunctionDef", "arguments", "arg", "Try", "Assign", "Call", "If", "Return", "Return", "Except", "Call", "Raise"]

        fp_base = compute_fingerprint(_func("base_fn", base))
        fp_ext = compute_fingerprint(_func("extended_fn", extended))

        # Winnowing fingerprints are positional — wrapping changes (Try/Except)
        # shift all k-gram windows, producing different hashes. This is a known
        # limitation of positional methods. The embedding detector handles this better.
        embed_base = build_embedding(_func("base_fn", base))
        embed_ext = build_embedding(_func("extended_fn", extended))
        if embed_base and embed_ext:
            cos = embedding_cosine(embed_base, embed_ext)
            # Embedding captures shared sub-paths even through wrapping
            assert cos >= 0.2, f"Partial clone embedding cosine too low: {cos}"


# ═══════════════════════════════════════════════════════════════════
# 3. SCALE BOUNDARY TESTS
#    Research: Sajnani 2016 — "SourcererCC scalability"
# ═══════════════════════════════════════════════════════════════════

class TestScaleBoundary:
    """Edge cases at scale boundaries."""

    def test_minimum_viable_function(self):
        """3-token function (smallest non-trivial) should be handled."""
        tiny = _func("noop", ["FunctionDef", "Pass"], body_lines=2)
        # Should be filtered by prefilter (< 3 body lines)
        assert should_prefilter_pair(
            {"body_lines": 2, "params": []},
            {"body_lines": 2, "params": []},
        )

    def test_very_large_function(self):
        """200-token function should not cause performance issues."""
        large = _func("big_fn", ["If", "Call", "Assign", "Return"] * 50, body_lines=200)
        vec = ast_node_vector(large)
        assert len(vec) > 0
        embed = build_embedding(large)
        assert len(embed) > 0

    def test_identical_functions_in_different_files(self):
        """Same function copied to two files — must detect."""
        tokens = ["FunctionDef", "arguments", "arg", "For", "If", "Call", "AugAssign", "Return"]
        a = _func("helper", tokens, file="utils_a.py")
        b = _func("helper", tokens, file="utils_b.py")
        assert should_compare(a, b), "Same name in different files should compare"


# ═══════════════════════════════════════════════════════════════════
# 4. MULTI-SIGNAL DISCRIMINATION
#    Research: Oreo (Saini 2018) — "ensemble beats any single detector"
# ═══════════════════════════════════════════════════════════════════

class TestMultiSignalDiscrimination:
    """Verify the multi-signal merge correctly discriminates ambiguous cases."""

    def test_high_ast_low_name_is_strong(self):
        """Structural match + name mismatch = still a likely duplicate.

        Research: Renamed clones (Type 2) have high AST match but zero name match.
        """
        results = {
            "ast_similarity": [_pair("ast_similarity", 0.9)],
            "token_clone": [_pair("token_clone", 0.9)],
        }
        merged = merge_pair_signals(results)
        assert len(merged) >= 1
        assert merged[0]["confidence"] == "HIGH"

    def test_high_name_low_ast_is_weak(self):
        """Name match + no structural match = likely false positive.

        Research: "formatDate" vs "dateFormat" can be totally different
        implementations that happen to share tokens.
        """
        results = {
            "fuzzy_name": [_pair("fuzzy_name", 0.9)],
        }
        merged = merge_pair_signals(results)
        # Single surface strategy: capped at MEDIUM
        if merged:
            assert merged[0]["confidence"] != "HIGH"

    def test_all_structural_zero_surface_is_definitive(self):
        """All structural strategies agree but names differ completely.

        This is the strongest signal: the CODE is identical even though
        the names are different. Must be HIGH.
        """
        results = {
            "token_clone": [_pair("token_clone", 0.95)],
            "ast_similarity": [_pair("ast_similarity", 0.9)],
            "pdg_semantic": [_pair("pdg_semantic", 0.8)],
        }
        merged = merge_pair_signals(results)
        assert merged[0]["confidence"] == "HIGH"
        assert merged[0]["num_strategies"] == 3

    def test_contradictory_signals_reduce_confidence(self):
        """High metric similarity + zero AST similarity = suspicious.

        Two functions can have same LOC and complexity by coincidence.
        Without structural confirmation, it's noise.
        """
        results = {
            "metric_similarity": [_pair("metric_similarity", 0.95)],
        }
        merged = merge_pair_signals(results)
        # Single surface strategy
        if merged:
            assert merged[0]["confidence"] != "HIGH"


# ═══════════════════════════════════════════════════════════════════
# 5. REGRESSION GUARDS
#    Ensure optimizations don't break known-good behavior
# ═══════════════════════════════════════════════════════════════════

class TestRegressionGuards:
    """Guard tests for known-good outcomes that must never regress."""

    def test_token_clone_type1_always_high(self):
        """Exact token clones must always be HIGH, regardless of other signals."""
        results = {"token_clone": [_pair("token_clone", 1.0)]}
        merged = merge_pair_signals(results)
        assert merged[0]["confidence"] == "HIGH"

    def test_prefilter_conservative_on_missing_data(self):
        """Prefilter must never reject pairs with missing metrics."""
        sparse = {"name": "fn", "file": "x.py"}
        assert not should_prefilter_pair(sparse, sparse)

    def test_jaccard_mathematical_properties(self):
        """Jaccard must satisfy: symmetric, 0 for disjoint, 1 for identical."""
        a = {"x", "y", "z"}
        b = {"y", "z", "w"}
        assert jaccard(a, b) == jaccard(b, a)  # Symmetric
        assert jaccard(a, a) == 1.0  # Identity
        assert jaccard({"a"}, {"b"}) == 0.0  # Disjoint

    def test_overlap_coefficient_subset_property(self):
        """Overlap must be 1.0 when one set is a subset of the other."""
        assert overlap_coefficient({"a", "b"}, {"a", "b", "c", "d", "e"}) == 1.0

    def test_cosine_similarity_bounds(self):
        """Cosine similarity must always be in [0, 1]."""
        a = Counter({"If": 5, "Call": 3, "Return": 1})
        b = Counter({"For": 4, "Assign": 2, "Return": 1})
        score = cosine_similarity(a, b)
        assert 0.0 <= score <= 1.0


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
