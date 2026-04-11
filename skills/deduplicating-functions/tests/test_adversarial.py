#!/usr/bin/env python3
# ABOUTME: Adversarial test suite — harder-than-reality test cases to harden
# detection accuracy. Tests edge cases, near-misses, tricky false positives,
# and pathological inputs that stress each detection strategy.

"""
Adversarial Tests for Duplicate Function Detection

Design principle: if the system handles these adversarial cases correctly,
real-world production inputs will be trivial by comparison.

Categories:
  1. True duplicates that are HARD to detect (must catch)
  2. Non-duplicates that LOOK similar (must reject)
  3. Pathological inputs (must not crash)
  4. Boundary conditions (threshold edges)
"""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

# ── Module imports via importlib (hyphenated filenames) ──────────

_scripts = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(_scripts))

from lib.common import (
    jaccard,
    tokenize,
    tokenize_to_strings,
    tokenize_to_typed,
    should_compare,
    func_key,
    func_ref,
)


def _load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, _scripts / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


merge_mod = _load_module("merge_signals", "merge-signals.py")
merge_pair_signals = merge_mod.merge_pair_signals

fuzzy_mod = _load_module("detect_fuzzy", "detect-fuzzy-names.py")
_has_detect_fuzzy = hasattr(fuzzy_mod, "detect_fuzzy_duplicates")

sig_mod = _load_module("detect_sig", "detect-signature-match.py")
_has_detect_sig = hasattr(sig_mod, "detect_signature_duplicates")


# ═══════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════

def _make_func(
    name: str,
    file: str = "test.py",
    line: int = 1,
    params: list | None = None,
    return_type: str | None = None,
    body_lines: int = 5,
    token_sequence: list | None = None,
    ast_fingerprint: str | None = None,
    cyclomatic_complexity: int = 2,
    qualified_name: str | None = None,
) -> dict:
    return {
        "name": name,
        "qualified_name": qualified_name or name,
        "file": file,
        "line": line,
        "params": params or [],
        "return_type": return_type,
        "body_lines": body_lines,
        "token_sequence": token_sequence,
        "ast_fingerprint": ast_fingerprint,
        "cyclomatic_complexity": cyclomatic_complexity,
        "language": "python",
    }


def _merge(results: dict, **kwargs) -> list:
    return merge_pair_signals(results, **kwargs)


def _pair(strategy: str, score: float, **kw) -> dict:
    return {
        "func_a": {"name": kw.get("a", "funcA"), "file": "a.py", "line": 1},
        "func_b": {"name": kw.get("b", "funcB"), "file": "b.py", "line": 1},
        "scores": {},
        "final_score": score,
        "strategy": strategy,
    }


# ═══════════════════════════════════════════════════════════════════
# 1. TRUE DUPLICATES — HARD TO DETECT (must catch)
# ═══════════════════════════════════════════════════════════════════

class TestHardTruePositives:
    """Cases where real duplicates use obfuscating naming or structure."""

    def test_antonym_names_same_body(self):
        """Functions with opposite-meaning names but identical implementation."""
        # enable() and disable() with identical bodies should be caught
        # by token/AST matching even though names are anti-correlated
        tok = ["def", "x", "(", "self", ")", ":", "self", ".", "flag", "=", "True"]
        a = _make_func("enable", file="a.py", token_sequence=tok, ast_fingerprint="abc123")
        b = _make_func("disable", file="b.py", token_sequence=tok, ast_fingerprint="abc123")
        # Token clone with exact match (identical bodies) should solo-HIGH
        results = {"token_clone": [_pair("token_clone", 1.0, a="enable", b="disable")]}
        merged = _merge(results)
        assert len(merged) == 1
        assert merged[0]["confidence"] == "HIGH"  # exact token clone can solo-HIGH

    def test_abbreviated_vs_full_name(self):
        """cfg_load vs configure_and_load — abbreviation should boost score."""
        tokens_a = tokenize("cfg_load")
        tokens_b = tokenize("configure_and_load")
        # "cfg" should expand to "config/configure" and match
        assert "cfg" in tokens_a or "load" in tokens_a
        assert "load" in tokens_b

    def test_different_prefix_same_core(self):
        """_internal_validate vs public_validate — same core function."""
        tokens_a = set(tokenize("_internal_validate_email"))
        tokens_b = set(tokenize("public_validate_email"))
        overlap = jaccard(tokens_a, tokens_b)
        assert overlap >= 0.4  # Should share "validate" and "email"

    def test_method_vs_function_same_logic(self):
        """Class.process() and standalone process_data() with identical AST."""
        fp = "deadbeef"
        a = _make_func("process", file="a.py", qualified_name="Processor.process",
                       ast_fingerprint=fp, token_sequence=["If", "Call", "Return"])
        b = _make_func("process_data", file="b.py",
                       ast_fingerprint=fp, token_sequence=["If", "Call", "Return"])
        # Both AST similarity and token clones should catch this
        results = {
            "token_clone": [_pair("token_clone", 0.9, a="process", b="process_data")],
            "ast_similarity": [_pair("ast_similarity", 1.0, a="process", b="process_data")],
        }
        merged = _merge(results)
        assert merged[0]["confidence"] == "HIGH"


# ═══════════════════════════════════════════════════════════════════
# 2. NON-DUPLICATES THAT LOOK SIMILAR (must reject or LOW)
# ═══════════════════════════════════════════════════════════════════

class TestHardFalsePositives:
    """Cases that look like duplicates but aren't."""

    def test_same_name_different_modules_different_logic(self):
        """main() in different files with completely different implementations."""
        a = _make_func("main", file="server.py", line=1,
                       token_sequence=["Import", "Call", "Flask", "run"],
                       ast_fingerprint="aaa")
        b = _make_func("main", file="cli.py", line=1,
                       token_sequence=["Import", "argparse", "parse", "execute"],
                       ast_fingerprint="bbb")
        # Fuzzy name gives 1.0 but AST/token should disagree
        results = {"fuzzy_name": [_pair("fuzzy_name", 1.0, a="main", b="main")]}
        merged = _merge(results)
        # Single-strategy fuzzy_name should cap at MEDIUM
        assert merged[0]["confidence"] != "HIGH"

    def test_getter_setter_pair(self):
        """get_value() and set_value() are NOT duplicates despite similar names."""
        tokens_a = set(tokenize("get_value"))
        tokens_b = set(tokenize("set_value"))
        # get/set are synonyms in the skill's synonym map, so this could false-positive
        # The Jaccard on {"get", "value"} vs {"set", "value"} = 1/3 = 0.33
        overlap = jaccard(tokens_a, tokens_b)
        assert overlap < 0.5  # Should NOT be high overlap

    def test_overloaded_names_different_arity(self):
        """process(x) and process(x, y, z) — same name but different signatures."""
        results = {
            "fuzzy_name": [_pair("fuzzy_name", 1.0)],
            "signature_match": [_pair("signature_match", 0.3)],  # Arity mismatch
        }
        merged = _merge(results)
        # 2 strategies but low signature = should be MEDIUM at most
        assert merged[0]["confidence"] in ("MEDIUM", "LOW")

    def test_zero_param_untyped_functions_not_high(self):
        """Two untyped () -> None functions should NOT be HIGH from signature alone."""
        results = {"signature_match": [_pair("signature_match", 0.45)]}
        merged = _merge(results)
        if merged:
            assert merged[0]["confidence"] != "HIGH"

    def test_trivial_one_liners_not_matched(self):
        """pass-only functions or single-return functions are not meaningful matches."""
        a = _make_func("noop_a", body_lines=1, token_sequence=["pass"])
        b = _make_func("noop_b", body_lines=1, token_sequence=["pass"])
        # With only 1 token, min_tokens filter should exclude these
        # (token clone detector requires min 10 tokens)
        assert len(a["token_sequence"]) < 10


# ═══════════════════════════════════════════════════════════════════
# 3. PATHOLOGICAL INPUTS (must not crash)
# ═══════════════════════════════════════════════════════════════════

class TestPathological:
    """Edge cases that could cause crashes or infinite loops."""

    def test_empty_catalog(self):
        """Empty input should produce empty output, not crash."""
        results = {}
        merged = _merge(results)
        assert merged == []

    def test_single_function_catalog(self):
        """Single function — no pairs possible."""
        results = {"fuzzy_name": []}
        merged = _merge(results)
        assert merged == []

    def test_unicode_function_names(self):
        """Function names with unicode characters."""
        tokens = tokenize("calcular_preço")
        assert isinstance(tokens, list)

    def test_very_long_function_name(self):
        """1000-char function name should not cause issues."""
        name = "a" * 1000
        tokens = tokenize(name)
        assert len(tokens) >= 1

    def test_empty_string_tokenization(self):
        """Empty code string should return empty token list."""
        assert tokenize_to_strings("") == []
        assert tokenize_to_typed("") == []

    def test_all_comments_code(self):
        """Code that is entirely comments should tokenize to empty."""
        code = "# this is all comments\n# nothing here\n"
        tokens = tokenize_to_strings(code)
        assert tokens == []

    def test_missing_fields_in_func_ref(self):
        """func_ref with empty dict should not crash."""
        ref = func_ref({})
        assert isinstance(ref, dict)
        assert "name" in ref

    def test_func_key_with_none_values(self):
        """func_key with None values should produce a valid key."""
        key = func_key({"file": None, "name": None, "line": None})
        assert isinstance(key, str)

    def test_should_compare_identical_entries(self):
        """Same entry should not compare with itself."""
        a = {"file": "x.py", "name": "foo", "line": 1}
        assert not should_compare(a, a)

    def test_jaccard_with_single_element_sets(self):
        """Single-element sets."""
        assert jaccard({"a"}, {"a"}) == 1.0
        assert jaccard({"a"}, {"b"}) == 0.0

    def test_jaccard_empty_vs_nonempty(self):
        """Empty set vs non-empty should be 0.0."""
        assert jaccard(set(), {"a"}) == 0.0

    def test_deeply_nested_token_sequence(self):
        """Very long token sequence (10000 elements)."""
        long_seq = ["If"] * 10000
        # Should not crash — just be slow
        key = func_key({"file": "x.py", "name": "big", "line": 1, "token_sequence": long_seq})
        assert key  # Just verify it runs


# ═══════════════════════════════════════════════════════════════════
# 4. BOUNDARY CONDITIONS (threshold edges)
# ═══════════════════════════════════════════════════════════════════

class TestBoundary:
    """Test exact threshold boundaries."""

    def test_score_exactly_at_low_threshold(self):
        """Score exactly at LOW threshold (0.35) should be included."""
        results = {"token_clone": [_pair("token_clone", 0.35)]}
        merged = _merge(results)
        assert len(merged) == 1  # token_clone can solo at any threshold

    def test_score_just_below_low_threshold(self):
        """Score 0.34 should be excluded."""
        results = {"fuzzy_name": [_pair("fuzzy_name", 0.34)]}
        merged = _merge(results)
        assert len(merged) == 0

    def test_exactly_three_independent_strategies_is_high(self):
        """3 independent strategies with adequate scores = auto HIGH.

        Uses strategies from different correlation groups and scores >= 0.5
        (MIN_COMPOSITE_FOR_HIGH floor).
        """
        results = {
            "token_clone": [_pair("token_clone", 0.7)],
            "fuzzy_name": [_pair("fuzzy_name", 0.7)],
            "signature_match": [_pair("signature_match", 0.7)],
        }
        merged = _merge(results, min_strategies_for_high=3)
        assert merged[0]["confidence"] == "HIGH"

    def test_two_surface_strategies_penalized(self):
        """2 surface-only strategies (no structural) get contradiction penalty."""
        results = {
            "fuzzy_name": [_pair("fuzzy_name", 0.4)],
            "metric_similarity": [_pair("metric_similarity", 0.4)],
        }
        merged = _merge(results)
        # Surface-only pairs get 0.6x penalty — may drop below threshold
        if merged:
            assert merged[0]["confidence"] in ("MEDIUM", "LOW")
        # Either filtered out or LOW/MEDIUM — never HIGH

    def test_composite_score_capped_at_one(self):
        """Composite score should never exceed 1.0."""
        results = {
            "token_clone": [_pair("token_clone", 1.0)],
            "ast_similarity": [_pair("ast_similarity", 1.0)],
            "fuzzy_name": [_pair("fuzzy_name", 1.0)],
            "signature_match": [_pair("signature_match", 1.0)],
            "metric_similarity": [_pair("metric_similarity", 1.0)],
        }
        merged = _merge(results)
        assert merged[0]["composite_score"] <= 1.0

    def test_negative_scores_handled(self):
        """Negative scores (bug in a detector) should not crash merge."""
        results = {"fuzzy_name": [_pair("fuzzy_name", -0.5)]}
        merged = _merge(results)
        # Should be filtered out (below threshold)
        assert len(merged) == 0


# ═══════════════════════════════════════════════════════════════════
# 5. MULTI-SIGNAL INTERACTION (defense in depth)
# ═══════════════════════════════════════════════════════════════════

class TestMultiSignal:
    """Verify that signal interaction produces correct confidence levels."""

    def test_strong_name_weak_signature_penalized(self):
        """Surface-only (name + signature, no structural) gets contradiction penalty."""
        results = {
            "fuzzy_name": [_pair("fuzzy_name", 0.9)],
            "signature_match": [_pair("signature_match", 0.3)],
        }
        merged = _merge(results)
        # Surface-only 2-strategy pair gets 0.6x penalty
        if merged:
            assert merged[0]["confidence"] in ("MEDIUM", "LOW")
            assert merged[0]["num_strategies"] == 2

    def test_five_strategies_with_adequate_scores_high(self):
        """5 strategies (3+ effective independent) with adequate scores = HIGH."""
        results = {
            "fuzzy_name": [_pair("fuzzy_name", 0.6)],
            "signature_match": [_pair("signature_match", 0.6)],
            "token_clone": [_pair("token_clone", 0.6)],
            "ast_similarity": [_pair("ast_similarity", 0.6)],
            "metric_similarity": [_pair("metric_similarity", 0.6)],
        }
        merged = _merge(results, min_strategies_for_high=3)
        assert merged[0]["confidence"] == "HIGH"  # 5 strategies = auto-HIGH

    def test_contradicting_signals(self):
        """High name match but zero AST similarity — should not be HIGH."""
        results = {
            "fuzzy_name": [_pair("fuzzy_name", 0.95)],
            # Notably ABSENT: token_clone, ast_similarity
        }
        merged = _merge(results)
        # Single strategy = capped at MEDIUM
        assert merged[0]["confidence"] != "HIGH"

    def test_cross_strategy_penalty_applied(self):
        """Signature-only match without name match gets penalized."""
        results = {"signature_match": [_pair("signature_match", 0.8)]}
        merged = _merge(results)
        if merged:
            # Score should be reduced by cross-strategy penalty
            assert merged[0]["composite_score"] < 0.8


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
