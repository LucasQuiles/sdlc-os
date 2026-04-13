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

    def test_actionable_only_filters_to_type1_high_substantial(self):
        # _pair uses line=1 by default; add end_line for substantial body
        substantial = _pair("deleteClient", "deleteTemplate", clone_type="Type 1 (exact clone)", confidence="HIGH")
        substantial["func_a"]["end_line"] = 30  # 30 body lines (>= 20 threshold)
        substantial["func_b"]["end_line"] = 30
        tiny = _pair("foo", "bar", clone_type="Type 1 (exact clone)", confidence="HIGH")
        tiny["func_a"]["end_line"] = 10  # too small (< 20 threshold)
        tiny["func_b"]["end_line"] = 10
        pairs = [
            substantial,
            tiny,
            _pair("x", "y", clone_type="Type 4 (semantic clone)", confidence="HIGH"),
            _pair("baz", "qux", clone_type="Type 1 (exact clone)", confidence="MEDIUM"),
            _pair("a", "b", clone_type="Type 2 (renamed clone)", confidence="HIGH"),
        ]
        result = suppress_noise_patterns(pairs, rules=[], actionable_only=True)
        assert len(result) == 1  # Only substantial Type 1 HIGH
        assert result[0]["func_a"]["name"] == "deleteClient"

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


class TestSuppressionNegativeControls:
    def test_one_sided_selfcontained_not_suppressed(self):
        """Only one function ends in SelfContained — should NOT be suppressed."""
        pairs = [_pair("getAllTablesSelfContained", "deleteClient")]
        result = suppress_noise_patterns(pairs, rules=["selfcontained_wrappers"])
        assert len(result) == 1  # pair survives

    def test_factory_names_outside_storage_error_not_suppressed(self):
        """notFound in a different file should NOT be suppressed."""
        pairs = [_pair("notFound", "badRequest", "other-file.ts", "other-file.ts")]
        result = suppress_noise_patterns(pairs, rules=["storage_error_factories"])
        assert len(result) == 1

    def test_same_name_crud_not_suppressed(self):
        """Two functions with the same name should NOT be suppressed by crud_boilerplate."""
        pairs = [_pair("deleteClient", "deleteClient", "file1.ts", "file2.ts", score=0.8)]
        result = suppress_noise_patterns(pairs, rules=["crud_boilerplate"])
        assert len(result) == 1  # same name = not cross-entity, survives

    def test_high_score_crud_survives(self):
        """Score >= 0.95 survives crud_boilerplate rule."""
        pairs = [_pair("deleteClient", "deleteTemplate", score=0.95)]
        result = suppress_noise_patterns(pairs, rules=["crud_boilerplate"])
        assert len(result) == 1  # score at threshold, survives

    def test_combined_suppression_preserves_real_finding(self):
        """The deleteClient/deleteTemplate exact clone must survive all rules."""
        real_finding = _pair("deleteClient", "deleteTemplate",
            "client-storage-manager.ts", "client-storage-manager.ts",
            score=1.0, clone_type="Type 1 (exact clone)", confidence="HIGH")
        real_finding["func_a"]["end_line"] = 30  # substantial body
        real_finding["func_b"]["end_line"] = 30
        noise = _pair("getAllTablesSelfContained", "getEquipmentSelfContained")
        pairs = [noise, real_finding]
        result = suppress_noise_patterns(
            pairs,
            rules=["selfcontained_wrappers", "storage_error_factories", "crud_boilerplate"],
            actionable_only=True,
        )
        assert len(result) == 1
        assert result[0]["func_a"]["name"] == "deleteClient"


class TestSizeAwareSuppression:
    def _sized_pair(self, name_a, name_b, end_line_a=None, end_line_b=None, **kwargs):
        p = _pair(name_a, name_b, **kwargs)
        if end_line_a is not None:
            p["func_a"]["end_line"] = end_line_a
        if end_line_b is not None:
            p["func_b"]["end_line"] = end_line_b
        return p

    def test_tiny_crud_pair_suppressed(self):
        """Two 5-line CRUD functions with different names and low score: suppressed."""
        pairs = [self._sized_pair("deleteClient", "deleteTemplate",
            end_line_a=5, end_line_b=5, score=0.8)]
        # Both start at line 1, end at line 5 = 5 body lines <= 10 threshold
        result = suppress_noise_patterns(pairs, rules=["crud_boilerplate"])
        assert len(result) == 0

    def test_large_exact_clone_survives(self):
        """A 50-line clone pair must survive even with crud_boilerplate rule."""
        pairs = [self._sized_pair("deleteClient", "deleteTemplate",
            end_line_a=50, end_line_b=50, score=0.8)]
        result = suppress_noise_patterns(pairs, rules=["crud_boilerplate"])
        assert len(result) == 1  # too large to suppress

    def test_missing_size_fails_open(self):
        """When end_line is missing, pair should NOT be suppressed (fail open)."""
        pairs = [_pair("deleteClient", "deleteTemplate", score=0.8)]
        # No end_line set — _both_small returns False — pair survives
        result = suppress_noise_patterns(pairs, rules=["crud_boilerplate"])
        assert len(result) == 1

    def test_one_small_one_large_survives(self):
        """Mixed sizes: one 5-line, one 50-line. Should NOT suppress."""
        pairs = [self._sized_pair("deleteClient", "deleteTemplate",
            end_line_a=5, end_line_b=50, score=0.8)]
        result = suppress_noise_patterns(pairs, rules=["crud_boilerplate"])
        assert len(result) == 1

    def test_at_threshold_not_suppressed(self):
        """Exactly at the boundary (11 lines when threshold is 10): survives."""
        pairs = [self._sized_pair("deleteClient", "deleteTemplate",
            end_line_a=11, end_line_b=11, score=0.8)]
        result = suppress_noise_patterns(pairs, rules=["crud_boilerplate"])
        assert len(result) == 1  # 11 body lines > 10 threshold
