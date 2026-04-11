"""Property-based testing for pipeline invariants using Hypothesis.

These tests generate random function catalogs and verify that core
pipeline invariants hold regardless of input. They complement the
hand-crafted unit tests by exploring the input space automatically.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import given, settings, assume, HealthCheck
from hypothesis import strategies as st

# Import modules under test via importlib (scripts/ is not a package)
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

from lib.common import jaccard, overlap_coefficient, should_compare, tokenize
from lib.prefilter import should_prefilter_pair


# ── Strategies for generating test data ──────────────────────────────

def _func_entry(
    name: str = "func",
    file: str = "a.py",
    line: int = 1,
    body_lines: int = 10,
    params: int = 2,
    complexity: int = 3,
    tokens: list[str] | None = None,
) -> dict:
    return {
        "name": name,
        "file": file,
        "line": line,
        "qualified_name": f"{file}:{name}",
        "body_lines": body_lines,
        "params": [{"name": f"p{i}", "type": "int"} for i in range(params)],
        "cyclomatic_complexity": complexity,
        "token_sequence": tokens or ["FunctionDef", "arg", "Return"],
        "return_type": "int",
        "language": "python",
    }


st_name = st.text(
    alphabet=st.characters(whitelist_categories=("Ll", "Lu")),
    min_size=1, max_size=20,
)
st_filename = st.text(
    alphabet=st.characters(whitelist_categories=("Ll",)),
    min_size=1, max_size=10,
).map(lambda s: f"{s}.py")
st_line = st.integers(min_value=1, max_value=10000)
st_body_lines = st.integers(min_value=1, max_value=500)
st_params = st.integers(min_value=0, max_value=10)
st_complexity = st.integers(min_value=1, max_value=20)

st_func = st.builds(
    _func_entry,
    name=st_name,
    file=st_filename,
    line=st_line,
    body_lines=st_body_lines,
    params=st_params,
    complexity=st_complexity,
)


# ── Set similarity invariants ────────────────────────────────────────

@given(
    a=st.frozensets(st.integers(min_value=0, max_value=100), min_size=0, max_size=50),
    b=st.frozensets(st.integers(min_value=0, max_value=100), min_size=0, max_size=50),
)
@settings(max_examples=200)
def test_jaccard_is_symmetric(a, b):
    """Jaccard similarity must be symmetric: J(A,B) == J(B,A)."""
    assert jaccard(set(a), set(b)) == jaccard(set(b), set(a))


@given(
    a=st.frozensets(st.integers(min_value=0, max_value=100), min_size=0, max_size=50),
    b=st.frozensets(st.integers(min_value=0, max_value=100), min_size=0, max_size=50),
)
@settings(max_examples=200)
def test_jaccard_bounded_zero_to_one(a, b):
    """Jaccard similarity must be in [0, 1]."""
    j = jaccard(set(a), set(b))
    assert 0.0 <= j <= 1.0


@given(
    a=st.frozensets(st.integers(min_value=0, max_value=100), min_size=1, max_size=50),
)
@settings(max_examples=100)
def test_jaccard_self_similarity_is_one(a):
    """Jaccard of a set with itself must be 1.0."""
    assert jaccard(set(a), set(a)) == 1.0


@given(
    a=st.frozensets(st.integers(min_value=0, max_value=50), min_size=1, max_size=25),
    b=st.frozensets(st.integers(min_value=51, max_value=100), min_size=1, max_size=25),
)
@settings(max_examples=100)
def test_jaccard_disjoint_is_zero(a, b):
    """Jaccard of fully disjoint non-empty sets must be 0.0."""
    assert jaccard(set(a), set(b)) == 0.0


@given(
    a=st.frozensets(st.integers(min_value=0, max_value=100), min_size=0, max_size=50),
    b=st.frozensets(st.integers(min_value=0, max_value=100), min_size=0, max_size=50),
)
@settings(max_examples=200)
def test_overlap_coefficient_is_symmetric(a, b):
    """Overlap coefficient must be symmetric."""
    assert overlap_coefficient(set(a), set(b)) == overlap_coefficient(set(b), set(a))


@given(
    a=st.frozensets(st.integers(min_value=0, max_value=100), min_size=0, max_size=50),
    b=st.frozensets(st.integers(min_value=0, max_value=100), min_size=0, max_size=50),
)
@settings(max_examples=200)
def test_overlap_coefficient_bounded_zero_to_one(a, b):
    """Overlap coefficient must be in [0, 1]."""
    oc = overlap_coefficient(set(a), set(b))
    assert 0.0 <= oc <= 1.0


# ── Prefilter invariants ─────────────────────────────────────────────

@given(f=st_func.filter(lambda f: f["body_lines"] >= 3))
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
def test_prefilter_never_rejects_nontrivial_identical_pair(f):
    """A non-trivial function (body >= 3 lines) paired with itself must not be prefiltered.

    Trivial functions (body < MIN_BODY_LINES=3) are correctly rejected
    by the prefilter — they're too small to be meaningful consolidation
    candidates regardless of duplication.
    """
    assert not should_prefilter_pair(f, f), (
        f"Prefilter rejected non-trivial identical pair: {f['name']} "
        f"(body_lines={f['body_lines']})"
    )


@given(
    bl=st.integers(min_value=1, max_value=2),
)
@settings(max_examples=20)
def test_prefilter_rejects_trivial_pairs(bl):
    """Both functions < MIN_BODY_LINES should be prefiltered."""
    a = _func_entry(body_lines=bl)
    b = _func_entry(name="other", file="b.py", body_lines=bl)
    assert should_prefilter_pair(a, b), (
        f"Prefilter should reject trivial pair (body_lines={bl})"
    )


@given(f=st_func)
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
def test_prefilter_is_symmetric(f):
    """should_prefilter_pair(a, b) must equal should_prefilter_pair(b, a)."""
    other = _func_entry(
        name="other", file="b.py", line=1,
        body_lines=f["body_lines"] * 2,
        params=f.get("params", 0) if isinstance(f.get("params"), int) else len(f.get("params", [])),
        complexity=f["cyclomatic_complexity"],
    )
    assert should_prefilter_pair(f, other) == should_prefilter_pair(other, f)


# ── Tokenizer invariants ─────────────────────────────────────────────

@given(name=st_name)
@settings(max_examples=100)
def test_tokenize_produces_lowercase(name):
    """tokenize() must produce all-lowercase tokens."""
    tokens = tokenize(name)
    for t in tokens:
        assert t == t.lower(), f"Token '{t}' from '{name}' is not lowercase"


@given(name=st_name)
@settings(max_examples=100)
def test_tokenize_is_deterministic(name):
    """tokenize() must produce the same result on repeated calls."""
    assert tokenize(name) == tokenize(name)


# ── should_compare invariants ────────────────────────────────────────

@given(f=st_func)
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
def test_should_compare_rejects_same_file_same_line(f):
    """should_compare must reject a pair from the same file and line."""
    assert not should_compare(f, f), (
        f"should_compare accepted a function compared with itself"
    )
