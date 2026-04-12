#!/usr/bin/env python3
"""Tests for noise suppression in merge-signals pipeline."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

# merge-signals.py has hyphens in the name; use importlib like other tests do
_scripts_dir = Path(__file__).parent.parent / "scripts"
_spec = importlib.util.spec_from_file_location(
    "merge_signals", _scripts_dir / "merge-signals.py"
)
_mod = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
_spec.loader.exec_module(_mod)  # type: ignore[union-attr]

suppress_noise_patterns = _mod.suppress_noise_patterns


def _pair(
    name_a: str,
    name_b: str,
    file_a: str = "a.ts",
    file_b: str = "b.ts",
    score: float = 0.9,
    clone_type: str = "Type 1 (exact clone)",
    confidence: str = "HIGH",
):
    return {
        "func_a": {"name": name_a, "file": file_a, "line": 1},
        "func_b": {"name": name_b, "file": file_b, "line": 1},
        "composite_score": score,
        "confidence": confidence,
        "clone_type": clone_type,
        "strategies": {"token_clone": 1.0},
        "strategy_count": 1,
    }


class TestSuppressNoisePatterns:
    def test_suppresses_selfcontained_pairs(self):
        pairs = [
            _pair("getAllTablesSelfContained", "getAvailableEquipmentSelfContained"),
            _pair("deleteClient", "deleteTemplate"),
        ]
        result = suppress_noise_patterns(pairs, rules=["selfcontained_wrappers"])
        assert len(result) == 1
        assert result[0]["func_a"]["name"] == "deleteClient"

    def test_suppresses_storage_error_factories(self):
        pairs = [
            _pair("notFound", "badRequest", "storage-error.ts", "storage-error.ts"),
            _pair("deleteClient", "deleteTemplate"),
        ]
        result = suppress_noise_patterns(pairs, rules=["storage_error_factories"])
        assert len(result) == 1
        assert result[0]["func_a"]["name"] == "deleteClient"

    def test_suppresses_both_rules(self):
        pairs = [
            _pair("getAllTablesSelfContained", "getEquipmentSelfContained"),
            _pair("notFound", "gone", "storage-error.ts", "storage-error.ts"),
            _pair("deleteClient", "deleteTemplate"),
        ]
        result = suppress_noise_patterns(
            pairs, rules=["selfcontained_wrappers", "storage_error_factories"]
        )
        assert len(result) == 1

    def test_no_rules_returns_all(self):
        pairs = [_pair("foo", "bar"), _pair("baz", "qux")]
        result = suppress_noise_patterns(pairs, rules=[])
        assert len(result) == 2

    def test_actionable_only_filters_to_type1_high(self):
        pairs = [
            _pair("deleteClient", "deleteTemplate", clone_type="Type 1 (exact clone)", confidence="HIGH"),
            _pair("foo", "bar", clone_type="Type 4 (semantic clone)", confidence="HIGH"),
            _pair("baz", "qux", clone_type="Type 1 (exact clone)", confidence="MEDIUM"),
            _pair("a", "b", clone_type="Type 2 (renamed clone)", confidence="HIGH"),
        ]
        result = suppress_noise_patterns(pairs, rules=[], actionable_only=True)
        assert len(result) == 2  # Type 1 HIGH + Type 2 HIGH
        names = {r["func_a"]["name"] for r in result}
        assert "deleteClient" in names
        assert "a" in names

    def test_suppression_metadata_returned(self):
        pairs = [
            _pair("getAllTablesSelfContained", "getEquipmentSelfContained"),
            _pair("deleteClient", "deleteTemplate"),
        ]
        result, meta = suppress_noise_patterns(
            pairs, rules=["selfcontained_wrappers"], return_meta=True
        )
        assert len(result) == 1
        assert meta["suppressed_count"] == 1
        assert meta["rules_applied"] == ["selfcontained_wrappers"]
