#!/usr/bin/env python3
# ABOUTME: Unit tests for the merge-signals scoring and confidence logic.
"""Tests for merge_pair_signals confidence assignment and multi-signal scoring."""

import importlib.util
import json
import sys
from pathlib import Path

# Allow importing from scripts/ — module has hyphens in name, use importlib
_scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(_scripts_dir))

_spec = importlib.util.spec_from_file_location(
    "merge_signals", _scripts_dir / "merge-signals.py"
)
_mod = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
_spec.loader.exec_module(_mod)  # type: ignore[union-attr]

merge_pair_signals = _mod.merge_pair_signals
classify_clone_type = _mod.classify_clone_type
generate_recommendation = _mod.generate_recommendation
make_pair_key = _mod.make_pair_key
convert_llm_results = _mod.convert_llm_results
STRATEGY_WEIGHTS = _mod.STRATEGY_WEIGHTS
CONFIDENCE_THRESHOLDS = _mod.CONFIDENCE_THRESHOLDS


def _make_pair(
    strategy: str,
    score: float,
    name_a: str = "funcA",
    name_b: str = "funcB",
    file_a: str = "a.py",
    file_b: str = "b.py",
) -> dict:
    """Helper to create a detection result."""
    return {
        "func_a": {"name": name_a, "file": file_a, "line": 1},
        "func_b": {"name": name_b, "file": file_b, "line": 1},
        "scores": {},
        "final_score": score,
        "strategy": strategy,
    }


# ── make_pair_key ──────────────────────────────────────────

def test_pair_key_order_independent():
    fa = {"file": "a.py", "name": "foo", "line": 1}
    fb = {"file": "b.py", "name": "bar", "line": 2}
    assert make_pair_key(fa, fb) == make_pair_key(fb, fa)


def test_pair_key_distinct_for_different_functions():
    fa = {"file": "a.py", "name": "foo", "line": 1}
    fb = {"file": "a.py", "name": "bar", "line": 2}
    fc = {"file": "a.py", "name": "baz", "line": 3}
    assert make_pair_key(fa, fb) != make_pair_key(fa, fc)


# ── Single-strategy capping ──────────────────────────────

def test_single_signature_match_caps_at_medium():
    """A single signature_match with score 1.0 should cap at MEDIUM, not HIGH."""
    results = {"signature_match": [_make_pair("signature_match", 1.0)]}
    merged = merge_pair_signals(results)
    assert len(merged) == 1
    assert merged[0]["confidence"] == "MEDIUM"


def test_single_token_clone_exact_is_high():
    """Type 1 exact token clones (score ~1.0) can solo-HIGH."""
    results = {"token_clone": [_make_pair("token_clone", 1.0)]}
    merged = merge_pair_signals(results)
    assert len(merged) == 1
    assert merged[0]["confidence"] == "HIGH"


def test_single_token_clone_renamed_caps_at_medium():
    """Type 2 renamed clones (score <1.0) need corroboration, cap at MEDIUM."""
    results = {"token_clone": [_make_pair("token_clone", 0.9)]}
    merged = merge_pair_signals(results)
    assert len(merged) == 1
    assert merged[0]["confidence"] == "MEDIUM"


def test_single_fuzzy_name_caps_at_medium():
    results = {"fuzzy_name": [_make_pair("fuzzy_name", 0.95)]}
    merged = merge_pair_signals(results)
    assert len(merged) == 1
    assert merged[0]["confidence"] == "MEDIUM"


# ── Multi-signal defense in depth ─────────────────────────

def test_three_independent_strategies_auto_high():
    """3+ independent strategies with adequate score = automatic HIGH.

    Uses strategies from different correlation groups (token_clone, fuzzy_name,
    signature_match) and scores above MIN_COMPOSITE_FOR_HIGH (0.5).
    """
    results = {
        "token_clone": [_make_pair("token_clone", 0.7)],
        "fuzzy_name": [_make_pair("fuzzy_name", 0.7)],
        "signature_match": [_make_pair("signature_match", 0.7)],
    }
    merged = merge_pair_signals(results, min_strategies_for_high=3)
    assert len(merged) == 1
    assert merged[0]["confidence"] == "HIGH"
    assert merged[0]["num_strategies"] == 3


def test_two_strategies_medium_or_high():
    """2 strategies with moderate scores should be at least MEDIUM."""
    results = {
        "fuzzy_name": [_make_pair("fuzzy_name", 0.6)],
        "ast_similarity": [_make_pair("ast_similarity", 0.7)],
    }
    merged = merge_pair_signals(results)
    assert len(merged) == 1
    assert merged[0]["confidence"] in ("MEDIUM", "HIGH")
    assert merged[0]["num_strategies"] == 2


# ── Threshold customization ──────────────────────────────

def test_custom_high_threshold():
    """Passing a high threshold via parameter should affect confidence."""
    results = {
        "fuzzy_name": [_make_pair("fuzzy_name", 0.7)],
        "ast_similarity": [_make_pair("ast_similarity", 0.7)],
    }
    strict_thresholds = {"HIGH": 0.99, "MEDIUM": 0.55, "LOW": 0.35}
    merged = merge_pair_signals(
        results, confidence_thresholds=strict_thresholds
    )
    assert len(merged) == 1
    # With very strict HIGH threshold, should be MEDIUM
    assert merged[0]["confidence"] == "MEDIUM"


# ── Below-threshold filtering ─────────────────────────────

def test_below_low_threshold_excluded():
    """Pairs below LOW threshold should not appear in output."""
    results = {"fuzzy_name": [_make_pair("fuzzy_name", 0.1)]}
    merged = merge_pair_signals(results)
    assert len(merged) == 0


# ── Clone type classification ─────────────────────────────

def test_token_clone_type_1():
    strategies = {
        "token_clone": {"scores": {"clone_type": 1}, "final_score": 1.0}
    }
    assert "Type 1" in classify_clone_type(strategies)


def test_token_clone_type_2():
    strategies = {
        "token_clone": {"scores": {"clone_type": 2}, "final_score": 0.9}
    }
    assert "Type 2" in classify_clone_type(strategies)


def test_ast_similarity_type_3():
    strategies = {
        "ast_similarity": {"final_score": 0.7}
    }
    assert "Type 3" in classify_clone_type(strategies)


def test_llm_semantic_type_4():
    strategies = {
        "llm_semantic": {"final_score": 0.8}
    }
    assert "Type 4" in classify_clone_type(strategies)


# ── Recommendation generation ─────────────────────────────

def test_high_confidence_recommends_consolidate():
    rec = generate_recommendation("HIGH", 3, {"a": {}, "b": {}, "c": {}})
    assert rec["action"] == "CONSOLIDATE"


def test_medium_confidence_recommends_investigate():
    rec = generate_recommendation("MEDIUM", 1, {"a": {}})
    assert rec["action"] == "INVESTIGATE"


def test_low_confidence_recommends_review():
    rec = generate_recommendation("LOW", 1, {"a": {}})
    assert rec["action"] == "REVIEW"


# ── LLM result conversion ────────────────────────────────

def test_convert_llm_results_pairwise():
    """LLM group format should convert to pairwise format."""
    groups = [{
        "intent": "format dates",
        "confidence": "HIGH",
        "functions": [
            {"name": "formatDate", "file": "a.py", "line": 1},
            {"name": "dateToStr", "file": "b.py", "line": 2},
            {"name": "fmtDate", "file": "c.py", "line": 3},
        ],
    }]
    pairs = convert_llm_results(groups)
    # 3 functions = 3 pairs (3 choose 2)
    assert len(pairs) == 3
    assert all(p["strategy"] == "llm_semantic" for p in pairs)
    assert all(p["final_score"] == 0.95 for p in pairs)


# ── Deduplication ─────────────────────────────────────────

def test_same_pair_from_multiple_strategies_merged():
    """Same function pair from different strategies should merge, not duplicate."""
    results = {
        "fuzzy_name": [_make_pair("fuzzy_name", 0.6)],
        "signature_match": [_make_pair("signature_match", 0.7)],
    }
    merged = merge_pair_signals(results)
    assert len(merged) == 1  # One merged pair, not two


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
