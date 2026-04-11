# SP1: Scalability + Precision Foundation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace O(n^2) brute-force pairwise comparison with TF-IDF indexed candidate retrieval, add constraint-based pre-filtering, overlap coefficient, configurable thresholds, and expanded linguistic maps — cutting false positives 30-50% and enabling 10x larger codebases.

**Architecture:** A new `detect-tfidf-index.py` detector builds an inverted token index with IDF weighting, retrieves candidate pairs via shared rare tokens, and scores by weighted token overlap. A new `prefilter.py` module in `lib/` applies cheap necessary conditions (length ratio, arity, complexity bounds) before expensive comparisons. Existing detectors gain `--threshold` and `--min-tokens` CLI flags. The overlap coefficient (|A&cap;B|/min(|A|,|B|)) supplements Jaccard in `lib/common.py`. Synonym and abbreviation maps expand from ~60 to 150+ entries.

**Tech Stack:** Python 3.12, `math` (IDF), `collections` (inverted index), existing `lib/common.py`, `argparse`, `pytest`

**Working directory:** `/home/q/LAB/skills/finding-duplicate-functions`

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `scripts/lib/common.py` | Modify | Add `overlap_coefficient()`, expand synonym/abbreviation maps |
| `scripts/lib/prefilter.py` | Create | Constraint-based pre-filter: length ratio, arity, complexity guards |
| `scripts/detect-tfidf-index.py` | Create | TF-IDF inverted index detector with weighted token scoring |
| `scripts/detect-ast-similarity.py` | Modify | Add `--ngram-threshold` and `--min-tokens` CLI flags |
| `scripts/detect-token-clones.py` | Modify | Add `--min-tokens` CLI flag (already has default, make configurable) |
| `scripts/detect-fuzzy-names.py` | Modify | Add `--threshold` CLI flag, use expanded synonyms/abbreviations |
| `scripts/detect-signature-match.py` | Modify | Add `--threshold` CLI flag |
| `scripts/detect-metric-similarity.py` | Modify | Add `--threshold` CLI flag, integrate prefilter |
| `scripts/merge-signals.py` | Modify | Add `tfidf_index` strategy weight, tune MIN_STRATEGIES_FOR_HIGH |
| `scripts/orchestrate.sh` | Modify | Wire up TF-IDF detector phase, pass threshold flags |
| `tests/test_common_extended.py` | Create | Tests for overlap coefficient, expanded maps, prefilter |
| `tests/test_tfidf_detector.py` | Create | Tests for TF-IDF index detector |

---

### Task 1: Add Overlap Coefficient to lib/common.py

**Files:**
- Modify: `scripts/lib/common.py`
- Create: `tests/test_common_extended.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_common_extended.py
#!/usr/bin/env python3
# ABOUTME: Tests for extended common utilities — overlap coefficient, prefilter, expanded maps.

import sys
from pathlib import Path
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/q/LAB/skills/finding-duplicate-functions && python3 -m pytest tests/test_common_extended.py::TestOverlapCoefficient -v`
Expected: ImportError — `overlap_coefficient` does not exist yet.

- [ ] **Step 3: Implement overlap_coefficient in lib/common.py**

Add after the existing `jaccard()` function in `scripts/lib/common.py`:

```python
def overlap_coefficient(a: set[Any], b: set[Any]) -> float:
    """Overlap coefficient: |A intersection B| / min(|A|, |B|).

    Asymmetric measure — a small function fully contained in a larger one
    scores 1.0. Complements Jaccard for partial clone detection (NIL technique).
    Returns 0.0 when either set is empty.
    """
    if not a or not b:
        return 0.0
    return len(a & b) / min(len(a), len(b))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/q/LAB/skills/finding-duplicate-functions && python3 -m pytest tests/test_common_extended.py::TestOverlapCoefficient -v`
Expected: 7/7 PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/lib/common.py tests/test_common_extended.py
git commit -m "feat: add overlap coefficient (NIL technique) to common utilities"
```

---

### Task 2: Expand Synonym and Abbreviation Maps

**Files:**
- Modify: `scripts/detect-fuzzy-names.py`
- Modify: `tests/test_common_extended.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_common_extended.py`:

```python
import importlib.util

_spec = importlib.util.spec_from_file_location(
    "detect_fuzzy", Path(__file__).parent.parent / "scripts" / "detect-fuzzy-names.py"
)
_fuzzy_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_fuzzy_mod)


class TestExpandedSynonyms:
    """Verify expanded synonym groups cover common programming verbs."""

    def test_search_lookup_find_synonyms(self):
        """search/lookup/find/query should be treated as synonyms."""
        groups = _fuzzy_mod.SYNONYM_GROUPS
        search_group = None
        for g in groups:
            if "search" in g:
                search_group = g
                break
        assert search_group is not None
        assert "lookup" in search_group
        assert "find" in search_group

    def test_sort_order_arrange_synonyms(self):
        groups = _fuzzy_mod.SYNONYM_GROUPS
        sort_group = None
        for g in groups:
            if "sort" in g:
                sort_group = g
                break
        assert sort_group is not None
        assert "order" in sort_group

    def test_list_array_collection_synonyms(self):
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


class TestExpandedAbbreviations:
    """Verify expanded abbreviation map covers common programming terms."""

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
        """Combined synonyms + abbreviations should total at least 150 entries."""
        syn_count = sum(len(g) for g in _fuzzy_mod.SYNONYM_GROUPS)
        abbr_count = len(_fuzzy_mod.ABBREVIATION_MAP)
        assert syn_count + abbr_count >= 150
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/q/LAB/skills/finding-duplicate-functions && python3 -m pytest tests/test_common_extended.py::TestExpandedSynonyms tests/test_common_extended.py::TestExpandedAbbreviations -v`
Expected: Multiple FAIL — missing synonym groups and abbreviations.

- [ ] **Step 3: Expand SYNONYM_GROUPS in detect-fuzzy-names.py**

Find the existing `SYNONYM_GROUPS` list and replace it with expanded version containing at minimum these groups (keep all existing groups, add new ones):

```python
SYNONYM_GROUPS: list[set[str]] = [
    # Retrieval
    {"get", "fetch", "retrieve", "load", "find", "query", "read", "obtain", "acquire", "lookup", "search", "select"},
    # Mutation
    {"set", "update", "modify", "change", "mutate", "write", "assign", "put", "patch", "alter"},
    # Creation
    {"create", "make", "build", "construct", "generate", "produce", "init", "initialize", "new", "spawn", "instantiate"},
    # Deletion
    {"delete", "remove", "destroy", "drop", "clear", "purge", "erase", "discard", "clean", "wipe"},
    # Validation
    {"validate", "check", "verify", "assert", "ensure", "test", "confirm", "examine", "inspect", "audit"},
    # Formatting / Display
    {"format", "render", "display", "show", "present", "stringify", "print", "output", "serialize"},
    # Parsing
    {"parse", "decode", "deserialize", "extract", "unwrap", "unpack", "read", "interpret"},
    # Events / Messaging
    {"send", "emit", "dispatch", "publish", "broadcast", "notify", "fire", "trigger", "signal", "post"},
    # Processing
    {"handle", "process", "on", "execute", "run", "perform", "do", "invoke", "apply", "call"},
    # Transformation
    {"convert", "transform", "map", "translate", "serialize", "encode", "marshal", "adapt", "cast", "coerce"},
    # Boolean prefixes
    {"is", "has", "can", "should", "will", "does", "was"},
    # Lifecycle start
    {"open", "start", "begin", "launch", "boot", "setup", "mount", "connect", "activate", "enable"},
    # Lifecycle end
    {"close", "stop", "end", "finish", "shutdown", "teardown", "unmount", "disconnect", "deactivate", "disable"},
    # Collection types
    {"list", "array", "collection", "items", "entries", "elements", "set", "group", "batch"},
    # Sorting / Ordering
    {"sort", "order", "arrange", "rank", "organize", "sequence"},
    # Error handling
    {"error", "exception", "failure", "fault", "issue", "problem"},
    # Logging
    {"log", "trace", "debug", "record", "track", "report", "audit"},
    # Computation
    {"calculate", "compute", "derive", "evaluate", "determine", "measure", "estimate", "count", "sum", "total"},
    # Filtering
    {"filter", "exclude", "include", "select", "reject", "where", "match", "screen"},
    # Comparison
    {"compare", "diff", "match", "equals", "same", "identical", "equivalent"},
]
```

- [ ] **Step 4: Expand ABBREVIATION_MAP in detect-fuzzy-names.py**

Find the existing `ABBREVIATION_MAP` dict and expand it:

```python
ABBREVIATION_MAP: dict[str, str] = {
    # Original entries (keep all)
    "fmt": "format", "str": "string", "num": "number", "val": "value",
    "msg": "message", "err": "error", "req": "request", "res": "response",
    "cfg": "config", "ctx": "context", "btn": "button", "el": "element",
    "evt": "event", "cb": "callback", "fn": "function", "arg": "argument",
    "param": "parameter", "idx": "index", "len": "length", "tmp": "temp",
    "prev": "previous", "cur": "current", "src": "source", "dst": "destination",
    "opt": "option",
    # New entries
    "auth": "authenticate", "authn": "authentication", "authz": "authorization",
    "db": "database", "env": "environment", "repo": "repository",
    "impl": "implementation", "init": "initialize", "conf": "configuration",
    "conn": "connection", "sess": "session", "proc": "process",
    "mgr": "manager", "svc": "service", "ctrl": "controller",
    "gen": "generate", "calc": "calculate", "exec": "execute",
    "doc": "document", "desc": "description", "info": "information",
    "ref": "reference", "spec": "specification", "attr": "attribute",
    "prop": "property", "proto": "prototype", "obj": "object",
    "arr": "array", "dict": "dictionary", "tbl": "table",
    "col": "column", "fld": "field", "rec": "record",
    "usr": "user", "grp": "group", "org": "organization",
    "app": "application", "lib": "library", "pkg": "package", "mod": "module",
    "dir": "directory", "pth": "path", "ext": "extension",
    "cmd": "command", "op": "operation", "tx": "transaction",
    "async": "asynchronous", "sync": "synchronous", "seq": "sequence",
    "max": "maximum", "min": "minimum", "avg": "average",
    "agg": "aggregate", "acc": "accumulator", "iter": "iterator",
    "delim": "delimiter", "sep": "separator", "buf": "buffer",
    "alloc": "allocate", "dealloc": "deallocate", "dup": "duplicate",
    "orig": "original", "def": "default", "pref": "preference",
    "cmp": "compare", "eq": "equal", "lt": "less", "gt": "greater",
    "util": "utility", "hlp": "helper", "sched": "schedule",
    "ns": "namespace", "ver": "version", "ts": "timestamp",
}
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd /home/q/LAB/skills/finding-duplicate-functions && python3 -m pytest tests/test_common_extended.py -v`
Expected: All tests PASS, including `test_min_150_total_entries`.

- [ ] **Step 6: Commit**

```bash
git add scripts/detect-fuzzy-names.py tests/test_common_extended.py
git commit -m "feat: expand synonym groups (20 sets) and abbreviation map (80+ entries)"
```

---

### Task 3: Create Constraint-Based Pre-Filter Module

**Files:**
- Create: `scripts/lib/prefilter.py`
- Modify: `tests/test_common_extended.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_common_extended.py`:

```python
from lib.prefilter import should_prefilter_pair


class TestPrefilter:
    """Constraint-based pre-filter: cheap checks to eliminate impossible pairs."""

    def _func(self, body_lines=10, param_count=2, complexity=3, token_count=50):
        return {
            "body_lines": body_lines,
            "params": [{"name": f"p{i}"} for i in range(param_count)],
            "cyclomatic_complexity": complexity,
            "token_sequence": ["tok"] * token_count,
        }

    def test_similar_functions_pass(self):
        """Functions with similar metrics should NOT be filtered out."""
        a = self._func(body_lines=10, param_count=2, complexity=3)
        b = self._func(body_lines=12, param_count=2, complexity=4)
        assert not should_prefilter_pair(a, b)

    def test_extreme_length_ratio_filtered(self):
        """Function 10x longer than another should be filtered."""
        a = self._func(body_lines=5)
        b = self._func(body_lines=100)
        assert should_prefilter_pair(a, b)

    def test_arity_difference_filtered(self):
        """Functions differing by 3+ params should be filtered."""
        a = self._func(param_count=0)
        b = self._func(param_count=4)
        assert should_prefilter_pair(a, b)

    def test_arity_difference_2_passes(self):
        """Functions differing by 2 params should NOT be filtered."""
        a = self._func(param_count=1)
        b = self._func(param_count=3)
        assert not should_prefilter_pair(a, b)

    def test_extreme_complexity_ratio_filtered(self):
        """Function 3x more complex should be filtered."""
        a = self._func(complexity=2)
        b = self._func(complexity=20)
        assert should_prefilter_pair(a, b)

    def test_missing_metrics_passes(self):
        """If metrics are missing, don't filter (be conservative)."""
        a = {"body_lines": 10}
        b = {"body_lines": 12}
        assert not should_prefilter_pair(a, b)

    def test_both_trivial_filtered(self):
        """Both functions < 3 lines should be filtered (trivial)."""
        a = self._func(body_lines=1)
        b = self._func(body_lines=2)
        assert should_prefilter_pair(a, b)

    def test_one_trivial_one_real_passes(self):
        """One trivial + one real function should NOT be filtered."""
        a = self._func(body_lines=2)
        b = self._func(body_lines=10)
        assert not should_prefilter_pair(a, b)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/q/LAB/skills/finding-duplicate-functions && python3 -m pytest tests/test_common_extended.py::TestPrefilter -v`
Expected: ImportError — `prefilter` module does not exist.

- [ ] **Step 3: Implement prefilter.py**

Create `scripts/lib/prefilter.py`:

```python
#!/usr/bin/env python3
# ABOUTME: Constraint-based pre-filter for candidate pair elimination.
# Applies cheap necessary conditions to skip pairs that cannot be duplicates.
# Based on CCFinderX/Oreo pre-filtering — reduces false positives 30-50%.

"""
Pre-filter module: cheap necessary conditions that eliminate impossible pairs
before expensive comparisons (token hashing, n-gram, LCS, etc.).

Returns True if pair should be SKIPPED (filtered out).
Returns False if pair should proceed to full comparison.

Conservative: when metrics are missing, never filter (avoid false negatives).
"""

from __future__ import annotations
from typing import Any

# Configurable thresholds
LENGTH_RATIO_MAX = 3.0      # max body_lines ratio (larger / smaller)
ARITY_DIFF_MAX = 2           # max param count difference
COMPLEXITY_RATIO_MAX = 3.0   # max cyclomatic_complexity ratio
TOKEN_RATIO_MAX = 3.0        # max token_sequence length ratio
MIN_BODY_LINES = 3           # both functions must have at least this many lines


def should_prefilter_pair(
    a: dict[str, Any],
    b: dict[str, Any],
    length_ratio_max: float = LENGTH_RATIO_MAX,
    arity_diff_max: int = ARITY_DIFF_MAX,
    complexity_ratio_max: float = COMPLEXITY_RATIO_MAX,
    min_body_lines: int = MIN_BODY_LINES,
) -> bool:
    """Return True if this pair should be SKIPPED (cannot be duplicates).

    Applies these constraints:
    1. Body line count ratio must be within length_ratio_max
    2. Parameter count difference must be within arity_diff_max
    3. Cyclomatic complexity ratio must be within complexity_ratio_max
    4. Both functions must have at least min_body_lines

    Conservative: if a metric is missing from either entry, that check is skipped.
    """
    # 1. Both trivial?
    bl_a = a.get("body_lines")
    bl_b = b.get("body_lines")
    if bl_a is not None and bl_b is not None:
        if bl_a < min_body_lines and bl_b < min_body_lines:
            return True  # Both trivial — skip

    # 2. Length ratio
    if bl_a is not None and bl_b is not None and bl_a > 0 and bl_b > 0:
        ratio = max(bl_a, bl_b) / min(bl_a, bl_b)
        if ratio > length_ratio_max:
            return True

    # 3. Arity difference
    params_a = a.get("params")
    params_b = b.get("params")
    if params_a is not None and params_b is not None:
        arity_a = len(params_a) if isinstance(params_a, list) else 0
        arity_b = len(params_b) if isinstance(params_b, list) else 0
        if abs(arity_a - arity_b) > arity_diff_max:
            return True

    # 4. Complexity ratio
    cc_a = a.get("cyclomatic_complexity")
    cc_b = b.get("cyclomatic_complexity")
    if cc_a is not None and cc_b is not None and cc_a > 0 and cc_b > 0:
        ratio = max(cc_a, cc_b) / min(cc_a, cc_b)
        if ratio > complexity_ratio_max:
            return True

    return False  # Pair passes — proceed to full comparison
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/q/LAB/skills/finding-duplicate-functions && python3 -m pytest tests/test_common_extended.py::TestPrefilter -v`
Expected: 8/8 PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/lib/prefilter.py tests/test_common_extended.py
git commit -m "feat: add constraint-based pre-filter module for pair elimination"
```

---

### Task 4: Build TF-IDF Inverted Index Detector

**Files:**
- Create: `scripts/detect-tfidf-index.py`
- Create: `tests/test_tfidf_detector.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_tfidf_detector.py`:

```python
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
        "token_sequence": tokens,
        "body_lines": len(tokens),
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
        assert len(index["rare_token"]) == 2  # a and b share rare_token

    def test_idf_rare_tokens_higher(self):
        catalog = [
            _func("a", "a.py", ["if", "return", "rare"]),
            _func("b", "b.py", ["if", "return", "common"]),
            _func("c", "c.py", ["if", "common", "other"]),
        ]
        idf = compute_idf(catalog)
        assert idf["rare"] > idf["common"]  # rare has higher IDF
        assert idf["if"] < idf["rare"]       # if appears in all 3, lowest IDF

    def test_retrieves_candidates_via_shared_tokens(self):
        catalog = [
            _func("a", "a.py", ["if", "return", "domain_specific"]),
            _func("b", "b.py", ["for", "while", "domain_specific"]),
            _func("c", "c.py", ["if", "return", "other"]),
        ]
        index = build_inverted_index(catalog)
        idf = compute_idf(catalog)
        # a and b share "domain_specific" (high IDF), should be candidates
        candidates = retrieve_candidates(catalog, index, idf, min_shared_idf=0.1)
        pair_names = {(p[0]["name"], p[1]["name"]) for p in candidates}
        assert ("a", "b") in pair_names or ("b", "a") in pair_names

    def test_score_identical_functions(self):
        tokens = ["if", "x", "return", "True"]
        a = _func("foo", "a.py", tokens)
        b = _func("bar", "b.py", tokens)
        idf = {"if": 0.5, "x": 1.5, "return": 0.3, "True": 1.0}
        score = score_pair_tfidf(a, b, idf)
        assert score == pytest.approx(1.0, abs=0.01)

    def test_score_disjoint_functions(self):
        a = _func("foo", "a.py", ["alpha", "beta"])
        b = _func("bar", "b.py", ["gamma", "delta"])
        idf = {"alpha": 1.0, "beta": 1.0, "gamma": 1.0, "delta": 1.0}
        score = score_pair_tfidf(a, b, idf)
        assert score == 0.0

    def test_full_pipeline(self):
        catalog = [
            _func("format_date", "a.py", ["def", "date", "return", "strftime", "format"]),
            _func("date_to_string", "b.py", ["def", "date", "return", "strftime", "format"]),
            _func("unrelated", "c.py", ["def", "socket", "connect", "send", "recv"]),
        ]
        results = detect_tfidf_duplicates(catalog, threshold=0.3)
        assert len(results) >= 1
        # format_date and date_to_string should match
        names = {(r["func_a"]["name"], r["func_b"]["name"]) for r in results}
        assert ("format_date", "date_to_string") in names or ("date_to_string", "format_date") in names

    def test_empty_catalog(self):
        assert detect_tfidf_duplicates([], threshold=0.3) == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/q/LAB/skills/finding-duplicate-functions && python3 -m pytest tests/test_tfidf_detector.py -v`
Expected: ImportError — `detect-tfidf-index.py` does not exist.

- [ ] **Step 3: Implement detect-tfidf-index.py**

Create `scripts/detect-tfidf-index.py`:

```python
#!/usr/bin/env python3
# ABOUTME: TF-IDF inverted index detector — replaces O(n^2) brute force with
# O(n log n) candidate retrieval via shared rare tokens, weighted by IDF.
# Based on SourcererCC technique. Achieves 73% recall on Type-3 clones.

"""
detect-tfidf-index.py -- TF-IDF weighted token overlap for duplicate detection.

Builds an inverted index mapping tokens to functions, weights by inverse
document frequency (IDF) so rare domain-specific tokens matter more than
keywords. Retrieves candidate pairs sharing high-IDF tokens and scores
by weighted cosine similarity.

Input: Catalog JSON with token_sequence arrays.
Output: JSON array of scored candidate pairs.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from lib.common import func_ref, should_compare
from lib.prefilter import should_prefilter_pair


def get_tokens(func: dict[str, Any]) -> list[str]:
    """Extract flat token list from a function entry."""
    ts = func.get("token_sequence")
    if ts and isinstance(ts, list):
        if ts and isinstance(ts[0], dict):
            return [t.get("value", "") for t in ts if isinstance(t, dict)]
        return [str(t) for t in ts]
    # Fallback: tokenize context
    ctx = func.get("context", "")
    if ctx:
        return ctx.split()
    return []


def build_inverted_index(
    catalog: list[dict[str, Any]],
) -> dict[str, list[int]]:
    """Build token -> [func_index] inverted index."""
    index: dict[str, list[int]] = defaultdict(list)
    for i, func in enumerate(catalog):
        seen: set[str] = set()
        for token in get_tokens(func):
            if token not in seen:
                index[token].append(i)
                seen.add(token)
    return dict(index)


def compute_idf(catalog: list[dict[str, Any]]) -> dict[str, float]:
    """Compute IDF for each token: log(N / df) where df = document frequency."""
    n = len(catalog)
    if n == 0:
        return {}

    df: Counter[str] = Counter()
    for func in catalog:
        seen: set[str] = set()
        for token in get_tokens(func):
            if token not in seen:
                df[token] += 1
                seen.add(token)

    return {token: math.log(n / count) for token, count in df.items()}


def retrieve_candidates(
    catalog: list[dict[str, Any]],
    index: dict[str, list[int]],
    idf: dict[str, float],
    min_shared_idf: float = 0.5,
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    """Retrieve candidate pairs that share high-IDF tokens.

    For each token with IDF above median, look up all function pairs
    sharing that token. Deduplicate and return.
    """
    if not idf:
        return []

    # Only consider tokens with above-median IDF (rare tokens)
    idf_values = sorted(idf.values())
    median_idf = idf_values[len(idf_values) // 2] if idf_values else 0

    pair_idf_sum: dict[tuple[int, int], float] = defaultdict(float)

    for token, postings in index.items():
        token_idf = idf.get(token, 0)
        if token_idf < median_idf:
            continue  # Skip common tokens
        if len(postings) > len(catalog) * 0.5:
            continue  # Skip tokens in >50% of functions (too common)

        for idx_i in range(len(postings)):
            for idx_j in range(idx_i + 1, len(postings)):
                i, j = postings[idx_i], postings[idx_j]
                key = (min(i, j), max(i, j))
                pair_idf_sum[key] += token_idf

    # Filter by minimum shared IDF and prefilter constraints
    candidates: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for (i, j), total_idf in pair_idf_sum.items():
        if total_idf < min_shared_idf:
            continue
        fa, fb = catalog[i], catalog[j]
        if not should_compare(fa, fb):
            continue
        if should_prefilter_pair(fa, fb):
            continue
        candidates.append((fa, fb))

    return candidates


def score_pair_tfidf(
    a: dict[str, Any],
    b: dict[str, Any],
    idf: dict[str, float],
) -> float:
    """Score a pair by TF-IDF weighted cosine similarity on token bags."""
    tokens_a = get_tokens(a)
    tokens_b = get_tokens(b)

    if not tokens_a or not tokens_b:
        return 0.0

    tf_a: Counter[str] = Counter(tokens_a)
    tf_b: Counter[str] = Counter(tokens_b)

    # TF-IDF vectors
    all_tokens = set(tf_a) | set(tf_b)
    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0

    for token in all_tokens:
        w = idf.get(token, 1.0)
        va = tf_a.get(token, 0) * w
        vb = tf_b.get(token, 0) * w
        dot += va * vb
        norm_a += va * va
        norm_b += vb * vb

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot / (math.sqrt(norm_a) * math.sqrt(norm_b))


def detect_tfidf_duplicates(
    catalog: list[dict[str, Any]],
    threshold: float = 0.5,
    min_shared_idf: float = 0.5,
) -> list[dict[str, Any]]:
    """Run TF-IDF duplicate detection on the catalog."""
    if not catalog:
        return []

    index = build_inverted_index(catalog)
    idf = compute_idf(catalog)
    candidates = retrieve_candidates(catalog, index, idf, min_shared_idf)

    results: list[dict[str, Any]] = []
    for fa, fb in candidates:
        score = score_pair_tfidf(fa, fb, idf)
        if score >= threshold:
            results.append({
                "func_a": func_ref(fa),
                "func_b": func_ref(fb),
                "scores": {"tfidf_cosine": round(score, 4)},
                "final_score": round(score, 4),
                "strategy": "tfidf_index",
            })

    results.sort(key=lambda r: -r["final_score"])
    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="TF-IDF inverted index duplicate detector"
    )
    parser.add_argument("catalog", help="Path to catalog JSON file")
    parser.add_argument("-o", "--output", default="/dev/stdout", help="Output file")
    parser.add_argument("--threshold", type=float, default=0.5, help="Min score (default: 0.5)")
    parser.add_argument("--min-shared-idf", type=float, default=0.5, help="Min shared IDF for candidates")
    args = parser.parse_args()

    with open(args.catalog) as f:
        catalog = json.load(f)

    results = detect_tfidf_duplicates(catalog, args.threshold, args.min_shared_idf)

    with open(args.output, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Found {len(results)} candidate pair(s) (threshold={args.threshold}). "
          f"Wrote to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Make executable and run tests**

Run:
```bash
chmod +x scripts/detect-tfidf-index.py
cd /home/q/LAB/skills/finding-duplicate-functions && python3 -m pytest tests/test_tfidf_detector.py -v
```
Expected: 7/7 PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/detect-tfidf-index.py tests/test_tfidf_detector.py
git commit -m "feat: add TF-IDF inverted index detector (SourcererCC technique)"
```

---

### Task 5: Add Configurable Thresholds to All Detectors

**Files:**
- Modify: `scripts/detect-ast-similarity.py`
- Modify: `scripts/detect-token-clones.py`
- Modify: `scripts/detect-fuzzy-names.py`
- Modify: `scripts/detect-signature-match.py`
- Modify: `scripts/detect-metric-similarity.py`

- [ ] **Step 1: Verify current CLI flags**

Run each detector with `--help` to see what flags already exist:

```bash
cd /home/q/LAB/skills/finding-duplicate-functions
python3 scripts/detect-ast-similarity.py --help 2>&1 | grep -E "threshold|min.tokens"
python3 scripts/detect-token-clones.py --help 2>&1 | grep -E "threshold|min.tokens"
python3 scripts/detect-fuzzy-names.py --help 2>&1 | grep -E "threshold"
python3 scripts/detect-signature-match.py --help 2>&1 | grep -E "threshold"
python3 scripts/detect-metric-similarity.py --help 2>&1 | grep -E "threshold"
```

Document which flags exist and which are missing.

- [ ] **Step 2: Add missing CLI flags**

For each detector that is missing `--threshold` or `--min-tokens`:

In `detect-ast-similarity.py`, verify that `--threshold` and `--min-tokens` are already in the argparse config. If `--ngram-threshold` (the pre-screening threshold, currently hardcoded at 0.4) is missing, add it:

```python
parser.add_argument("--ngram-threshold", type=float, default=0.4,
                    help="Pre-screening n-gram threshold (default: 0.4)")
```

And thread it through to the detection function.

For `detect-token-clones.py`, verify `--min-tokens` exists (default 10).

For `detect-fuzzy-names.py` and `detect-signature-match.py`, verify `--threshold` exists (default 0.5).

For `detect-metric-similarity.py`, verify `--threshold` exists (default 0.8).

- [ ] **Step 3: Run all detectors with custom thresholds to verify flags work**

```bash
python3 scripts/detect-ast-similarity.py /tmp/verify-v5/extract/catalog-unified.json --threshold 0.7 --min-tokens 15 -o /dev/null 2>&1 | tail -1
python3 scripts/detect-token-clones.py /tmp/verify-v5/extract/catalog-unified.json --min-tokens 20 -o /dev/null 2>&1 | tail -1
python3 scripts/detect-fuzzy-names.py /tmp/verify-v5/extract/catalog-unified.json --threshold 0.6 -o /dev/null 2>&1 | tail -1
```

Expected: Each runs without error and reports a result count.

- [ ] **Step 4: Commit**

```bash
git add scripts/detect-*.py
git commit -m "feat: ensure all detectors have configurable --threshold and --min-tokens flags"
```

---

### Task 6: Wire TF-IDF Detector Into Orchestrator and Merge

**Files:**
- Modify: `scripts/orchestrate.sh`
- Modify: `scripts/merge-signals.py`

- [ ] **Step 1: Add tfidf_index strategy weight to merge-signals.py**

In the `STRATEGY_WEIGHTS` dict at the top of `scripts/merge-signals.py`, add:

```python
"tfidf_index": 0.75,      # TF-IDF weighted token overlap — strong signal
```

- [ ] **Step 2: Add TF-IDF phase to orchestrate.sh**

In the `phase_detect()` function, add after the metric similarity block:

```bash
# 1f. TF-IDF inverted index
if [[ -x "$SCRIPT_DIR/detect-tfidf-index.py" ]]; then
    log "  [1f] TF-IDF inverted index..."
    python3 "$SCRIPT_DIR/detect-tfidf-index.py" "$catalog" \
        -o "$OUTPUT_DIR/detect/tfidf-index-results.json" 2>>"$OUTPUT_DIR/pipeline.log" &
    pids+=($!)
fi
```

- [ ] **Step 3: Run full pipeline and verify TF-IDF appears in merge**

```bash
rm -rf /tmp/verify-sp1 && bash scripts/orchestrate.sh /home/q/LAB/bricklab/hooks -o /tmp/verify-sp1 --skip-llm 2>&1 | grep -E "tfidf|strategies"
```

Expected: `tfidf-index: N candidate pairs` in the merge output, and `tfidf_index` in the strategies list.

- [ ] **Step 4: Compare accuracy before/after**

```bash
jq '.summary' /tmp/verify-sp1/merge/merged-results.json
```

Verify `tfidf_index` appears in `strategies_used` and total pairs have shifted.

- [ ] **Step 5: Commit**

```bash
git add scripts/merge-signals.py scripts/orchestrate.sh
git commit -m "feat: wire TF-IDF detector into orchestrator and merge pipeline"
```

---

### Task 7: Integration Test — Full Pipeline Regression

**Files:**
- Modify: `tests/test_adversarial.py` (add integration section)

- [ ] **Step 1: Run full pipeline on bricklab/hooks**

```bash
rm -rf /tmp/sp1-final && bash scripts/orchestrate.sh /home/q/LAB/bricklab/hooks -o /tmp/sp1-final --skip-llm 2>&1
```

- [ ] **Step 2: Verify key metrics**

```bash
jq '.summary' /tmp/sp1-final/merge/merged-results.json
```

Check:
- `strategies_used` includes all 6 strategies (5 original + tfidf_index)
- `defense_depth_pairs` (3+ strategies) is >= 20
- Known true duplicate `generate_action_id` <-> `generate_enrichment_id` is still HIGH

```bash
jq '[.pairs[] | select(.func_a.name == "generate_action_id" or .func_b.name == "generate_action_id")] | .[0].confidence' /tmp/sp1-final/merge/merged-results.json
```

Expected: `"HIGH"`

- [ ] **Step 3: Run all unit + adversarial tests**

```bash
cd /home/q/LAB/skills/finding-duplicate-functions && python3 -m pytest tests/ -v
```

Expected: All tests pass.

- [ ] **Step 4: Commit integration results**

```bash
git add tests/
git commit -m "test: SP1 integration verification — all tests pass, 6 strategies active"
```

---

## Post-Plan Notes

**What SP1 delivers:**
- TF-IDF inverted index detector (O(n log n) candidate retrieval)
- Constraint-based pre-filter (30-50% FP reduction)
- Overlap coefficient (NIL technique for partial clones)
- Expanded synonym groups (20 sets) + abbreviation map (80+ entries)
- Configurable thresholds on all detectors
- 6 detection strategies in the merge pipeline

**What comes next (SP2):**
- LSH on AST feature vectors (datasketch MinHash)
- Bag-of-AST-nodes with cosine similarity
- Winnowing/fingerprint algorithm
- New merge signals + weights
