#!/usr/bin/env python3
# ABOUTME: Tests for extended common utilities — overlap coefficient, prefilter, expanded maps.

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from lib.common import overlap_coefficient


class TestOverlapCoefficient:
    def test_identical_sets(self):
        assert overlap_coefficient({"a", "b", "c"}, {"a", "b", "c"}) == 1.0

    def test_subset(self):
        """Small set fully contained in large set = 1.0 (asymmetric)."""
        assert overlap_coefficient({"a", "b"}, {"a", "b", "c", "d"}) == 1.0

    def test_partial_overlap(self):
        assert overlap_coefficient({"a", "b", "c"}, {"b", "c", "d"}) == pytest.approx(2/3)

    def test_no_overlap(self):
        assert overlap_coefficient({"a"}, {"b"}) == 0.0

    def test_both_empty(self):
        assert overlap_coefficient(set(), set()) == 0.0

    def test_one_empty(self):
        assert overlap_coefficient(set(), {"a"}) == 0.0

    def test_single_element_match(self):
        assert overlap_coefficient({"x"}, {"x"}) == 1.0


import importlib.util

_spec_fuzzy = importlib.util.spec_from_file_location(
    "detect_fuzzy", Path(__file__).parent.parent / "scripts" / "detect-fuzzy-names.py"
)
_fuzzy_mod = importlib.util.module_from_spec(_spec_fuzzy)
_spec_fuzzy.loader.exec_module(_fuzzy_mod)


class TestExpandedSynonyms:
    def test_search_lookup_find_synonyms(self):
        groups = _fuzzy_mod.SYNONYM_GROUPS
        found = any("search" in g and "lookup" in g and "find" in g for g in groups)
        assert found, "search/lookup/find should be synonyms"

    def test_sort_order_synonyms(self):
        groups = _fuzzy_mod.SYNONYM_GROUPS
        found = any("sort" in g and "order" in g for g in groups)
        assert found

    def test_list_array_synonyms(self):
        groups = _fuzzy_mod.SYNONYM_GROUPS
        found = any("list" in g and "array" in g for g in groups)
        assert found

    def test_open_start_begin_synonyms(self):
        groups = _fuzzy_mod.SYNONYM_GROUPS
        found = any("open" in g and "start" in g and "begin" in g for g in groups)
        assert found

    def test_close_stop_end_finish_synonyms(self):
        groups = _fuzzy_mod.SYNONYM_GROUPS
        found = any("close" in g and "stop" in g and "end" in g for g in groups)
        assert found

    def test_calculate_compute_synonyms(self):
        groups = _fuzzy_mod.SYNONYM_GROUPS
        found = any("calculate" in g and "compute" in g for g in groups)
        assert found


class TestExpandedAbbreviations:
    def test_auth_abbreviation(self):
        assert _fuzzy_mod.ABBREVIATION_MAP.get("auth") == "authenticate"

    def test_db_abbreviation(self):
        assert _fuzzy_mod.ABBREVIATION_MAP.get("db") == "database"

    def test_env_abbreviation(self):
        assert _fuzzy_mod.ABBREVIATION_MAP.get("env") == "environment"

    def test_repo_abbreviation(self):
        assert _fuzzy_mod.ABBREVIATION_MAP.get("repo") == "repository"

    def test_impl_abbreviation(self):
        assert _fuzzy_mod.ABBREVIATION_MAP.get("impl") == "implementation"

    def test_min_150_total_entries(self):
        syn_count = sum(len(g) for g in _fuzzy_mod.SYNONYM_GROUPS)
        abbr_count = len(_fuzzy_mod.ABBREVIATION_MAP)
        assert syn_count + abbr_count >= 150, f"Only {syn_count + abbr_count} entries, need 150+"


from lib.prefilter import should_prefilter_pair


class TestPrefilter:
    def _func(self, body_lines=10, param_count=2, complexity=3, token_count=50):
        return {
            "body_lines": body_lines,
            "params": [{"name": f"p{i}"} for i in range(param_count)],
            "cyclomatic_complexity": complexity,
            "token_sequence": ["tok"] * token_count,
        }

    def test_similar_functions_pass(self):
        a = self._func(body_lines=10, param_count=2, complexity=3)
        b = self._func(body_lines=12, param_count=2, complexity=4)
        assert not should_prefilter_pair(a, b)

    def test_extreme_length_ratio_filtered(self):
        a = self._func(body_lines=5)
        b = self._func(body_lines=100)
        assert should_prefilter_pair(a, b)

    def test_arity_difference_filtered(self):
        a = self._func(param_count=0)
        b = self._func(param_count=4)
        assert should_prefilter_pair(a, b)

    def test_arity_difference_2_passes(self):
        a = self._func(param_count=1)
        b = self._func(param_count=3)
        assert not should_prefilter_pair(a, b)

    def test_extreme_complexity_ratio_filtered(self):
        a = self._func(complexity=2)
        b = self._func(complexity=20)
        assert should_prefilter_pair(a, b)

    def test_missing_metrics_passes(self):
        a = {"body_lines": 10}
        b = {"body_lines": 12}
        assert not should_prefilter_pair(a, b)

    def test_both_trivial_filtered(self):
        a = self._func(body_lines=1)
        b = self._func(body_lines=2)
        assert should_prefilter_pair(a, b)

    def test_one_trivial_one_real_passes(self):
        a = self._func(body_lines=2)
        b = self._func(body_lines=10)
        assert not should_prefilter_pair(a, b)
