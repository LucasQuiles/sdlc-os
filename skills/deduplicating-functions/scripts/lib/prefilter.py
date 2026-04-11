#!/usr/bin/env python3
from __future__ import annotations
# ABOUTME: Constraint-based pre-filter for candidate pair elimination.
# Applies cheap necessary conditions to skip pairs that cannot be duplicates.
# Based on CCFinderX/Oreo pre-filtering — reduces false positives 30-50%.

from typing import Any

LENGTH_RATIO_MAX = 3.0
ARITY_DIFF_MAX = 2
COMPLEXITY_RATIO_MAX = 3.0
MIN_BODY_LINES = 3


def should_prefilter_pair(
    a: dict[str, Any],
    b: dict[str, Any],
    length_ratio_max: float = LENGTH_RATIO_MAX,
    arity_diff_max: int = ARITY_DIFF_MAX,
    complexity_ratio_max: float = COMPLEXITY_RATIO_MAX,
    min_body_lines: int = MIN_BODY_LINES,
) -> bool:
    """Return True if this pair should be SKIPPED (cannot be duplicates).

    Conservative: if a metric is missing, that check is skipped.
    """
    bl_a = a.get("body_lines")
    bl_b = b.get("body_lines")

    # Both trivial
    if bl_a is not None and bl_b is not None:
        if bl_a < min_body_lines and bl_b < min_body_lines:
            return True

    # Length ratio — only apply when both functions are non-trivial
    if bl_a is not None and bl_b is not None and bl_a > 0 and bl_b > 0:
        if bl_a >= min_body_lines and bl_b >= min_body_lines:
            ratio = max(bl_a, bl_b) / min(bl_a, bl_b)
            if ratio > length_ratio_max:
                return True

    # Arity difference
    params_a = a.get("params")
    params_b = b.get("params")
    if params_a is not None and params_b is not None:
        arity_a = len(params_a) if isinstance(params_a, list) else 0
        arity_b = len(params_b) if isinstance(params_b, list) else 0
        if abs(arity_a - arity_b) > arity_diff_max:
            return True

    # Complexity ratio
    cc_a = a.get("cyclomatic_complexity")
    cc_b = b.get("cyclomatic_complexity")
    if cc_a is not None and cc_b is not None and cc_a > 0 and cc_b > 0:
        ratio = max(cc_a, cc_b) / min(cc_a, cc_b)
        if ratio > complexity_ratio_max:
            return True

    return False
