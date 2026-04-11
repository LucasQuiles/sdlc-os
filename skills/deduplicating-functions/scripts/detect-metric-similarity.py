#!/usr/bin/env python3
from __future__ import annotations
# ABOUTME: Metric-based clone detection -- flags function pairs with suspiciously similar code metrics.
# ABOUTME: Computes 7 normalized metrics per function and outputs candidate duplicate pairs above a similarity threshold.

"""
detect-metric-similarity.py -- Metric-based duplicate function detection.

Functions with very similar code metrics (line count, complexity, parameter
count, token count, nesting depth, Halstead vocabulary, Halstead length) are
flagged as candidate duplicates.  This is a fast, structural pre-filter that
does NOT compare code text -- only numeric profiles.

Input:  Enriched catalog JSON (from extract-functions-ast-py.py or similar)
        with fields: body_lines, cyclomatic_complexity, params, token_sequence.

Output: JSON array of candidate pairs with per-metric and aggregate similarity.

Usage:
    ./detect-metric-similarity.py catalog.json
    ./detect-metric-similarity.py catalog.json -o metric-results.json
    ./detect-metric-similarity.py catalog.json --threshold 0.85
"""


import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from lib.common import func_key, func_ref, should_compare
from lib.prefilter import should_prefilter_pair


# ---------------------------------------------------------------------------
# Nesting depth estimation
# ---------------------------------------------------------------------------

# AST node type names that open a new nesting level.
_BLOCK_TOKENS = frozenset({
    "If", "For", "AsyncFor", "While", "Try", "TryStar", "With", "AsyncWith",
    # TypeScript / generic equivalents
    "IfStatement", "ForStatement", "ForInStatement", "ForOfStatement",
    "WhileStatement", "DoStatement", "TryStatement", "WithStatement",
})

# Closing-bracket tokens mark the end of a block for depth tracking.
_OPEN_TOKENS = _BLOCK_TOKENS
_CLOSE_HINT = frozenset({"EndOfFileToken"})  # not really used -- depth via stack


def _estimate_nesting_depth(token_sequence: list[str] | None, context: str | None = None) -> int:
    """Estimate the maximum nesting depth of block structures.

    Primary method: scan token_sequence for block-opening node types and track
    the max depth seen via a stack-like counter.  Each block token increments
    depth; non-block tokens between block tokens leave depth unchanged; when we
    see a token that is NOT a child of the current block, depth decreases.

    Because the token sequence is a flat DFS walk, we approximate nesting by
    counting consecutive block openers.  A more precise approach would require
    the full tree, but for metric similarity this approximation is sufficient.

    Fallback: if token_sequence is unavailable but context (source lines) is
    provided, estimate from maximum indentation.
    """
    if token_sequence:
        max_depth = 0
        current_depth = 0
        prev_was_block = False

        for token in token_sequence:
            if token in _BLOCK_TOKENS:
                if prev_was_block:
                    # Consecutive block openers -> deeper nesting
                    current_depth += 1
                else:
                    # First block opener at this level
                    current_depth += 1
                prev_was_block = True
                max_depth = max(max_depth, current_depth)
            else:
                prev_was_block = False
                # Heuristic: non-block tokens gradually reduce depth
                # (very rough -- but we only need relative comparison)

        return max_depth

    # Fallback: estimate from indentation in context string
    if context:
        max_indent = 0
        for line in context.split("\n"):
            stripped = line.lstrip()
            if stripped:
                indent = len(line) - len(stripped)
                max_indent = max(max_indent, indent)
        # Convert indent chars to approximate nesting levels (4 spaces per level)
        return max_indent // 4

    return 0


# ---------------------------------------------------------------------------
# Metric extraction
# ---------------------------------------------------------------------------

def _extract_metrics(func: dict[str, Any]) -> dict[str, float | None]:
    """Compute the 7 metric values for a single function entry.

    Returns a dict with keys matching the metric names.  A value of None means
    the metric could not be computed (missing data).
    """
    # 1. body_lines -- prefer explicit field, else derive from line/end_line
    body_lines: float | None = func.get("body_lines")
    if body_lines is None:
        line = func.get("line")
        end_line = func.get("end_line")
        if line is not None and end_line is not None:
            body_lines = float(end_line - line + 1)

    # 2. cyclomatic_complexity
    complexity: float | None = func.get("cyclomatic_complexity")
    if complexity is not None:
        complexity = float(complexity)

    # 3. param_count
    params = func.get("params")
    param_count: float | None = None
    if params is not None:
        param_count = float(len(params))

    # 4. token_count
    token_seq = func.get("token_sequence")
    token_count: float | None = None
    if token_seq is not None:
        token_count = float(len(token_seq))

    # 5. nesting_depth
    nesting_depth: float | None = None
    nesting_raw = _estimate_nesting_depth(token_seq, func.get("context"))
    if nesting_raw is not None:
        nesting_depth = float(nesting_raw)

    # 6. halstead_vocabulary -- count of unique tokens (approx eta)
    halstead_vocab: float | None = None
    if token_seq is not None:
        halstead_vocab = float(len(set(token_seq)))

    # halstead_length removed: identical to token_count, inflated similarity scores

    return {
        "body_lines": body_lines,
        "cyclomatic_complexity": complexity,
        "param_count": param_count,
        "token_count": token_count,
        "nesting_depth": nesting_depth,
        "halstead_vocabulary": halstead_vocab,
    }


# ---------------------------------------------------------------------------
# Similarity computation
# ---------------------------------------------------------------------------

# Mapping from metric key to output score key
_METRIC_TO_SCORE_KEY = {
    "body_lines": "body_lines_sim",
    "cyclomatic_complexity": "complexity_sim",
    "param_count": "param_count_sim",
    "token_count": "token_count_sim",
    "nesting_depth": "nesting_depth_sim",
    "halstead_vocabulary": "halstead_vocab_sim",
}


def _normalized_distance(a: float, b: float) -> float:
    """Compute |a - b| / max(a, b, 1).  Returns 0 when both are equal."""
    return abs(a - b) / max(a, b, 1.0)


def _compute_pair_similarity(
    metrics_a: dict[str, float | None],
    metrics_b: dict[str, float | None],
) -> tuple[dict[str, float], float, int]:
    """Compute per-metric and aggregate similarity for a pair.

    Returns:
        (scores_dict, final_score, num_metrics_used)
    """
    scores: dict[str, float] = {}
    distances: list[float] = []

    for metric_key, score_key in _METRIC_TO_SCORE_KEY.items():
        va = metrics_a[metric_key]
        vb = metrics_b[metric_key]
        if va is not None and vb is not None:
            dist = _normalized_distance(va, vb)
            sim = 1.0 - dist
            scores[score_key] = round(sim, 4)
            distances.append(dist)

    num_metrics = len(distances)
    if num_metrics == 0:
        return scores, 0.0, 0

    avg_distance = sum(distances) / num_metrics
    final_score = round(1.0 - avg_distance, 4)
    return scores, final_score, num_metrics


# ---------------------------------------------------------------------------
# Pair generation and filtering
# ---------------------------------------------------------------------------

# _func_id replaced by func_key from lib.common


def detect_metric_clones(
    catalog: list[dict[str, Any]],
    threshold: float = 0.9,
    min_body_lines: int = 3,
    min_metrics: int = 3,
) -> list[dict[str, Any]]:
    """Run pairwise metric similarity over the catalog.

    Args:
        catalog: List of function descriptors (enriched JSON).
        threshold: Minimum similarity score to include a pair (0-1).
        min_body_lines: Skip functions with fewer body lines than this.
        min_metrics: Skip pairs where fewer than this many metrics are available.

    Returns:
        List of candidate pair dicts in the specified output format.
    """
    # Pre-compute metrics for each function
    entries: list[tuple[dict[str, Any], dict[str, float | None]]] = []
    for func in catalog:
        metrics = _extract_metrics(func)
        body = metrics["body_lines"]
        if body is not None and body < min_body_lines:
            continue
        entries.append((func, metrics))

    results: list[dict[str, Any]] = []
    n = len(entries)

    for i in range(n):
        func_a, metrics_a = entries[i]
        id_a = func_key(func_a)

        for j in range(i + 1, n):
            func_b, metrics_b = entries[j]
            id_b = func_key(func_b)

            if id_a == id_b:
                continue
            if not should_compare(func_a, func_b):
                continue
            if should_prefilter_pair(func_a, func_b):
                continue

            scores, final_score, num_metrics = _compute_pair_similarity(metrics_a, metrics_b)

            if num_metrics < min_metrics:
                continue

            if final_score < threshold:
                continue

            results.append({
                "func_a": func_ref(func_a),
                "func_b": func_ref(func_b),
                "scores": scores,
                "final_score": final_score,
                "strategy": "metric_similarity",
            })

    # Sort by descending similarity
    results.sort(key=lambda r: r["final_score"], reverse=True)
    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Detect candidate duplicate functions by comparing numeric code "
            "metrics (body lines, complexity, param count, token count, nesting "
            "depth, Halstead vocabulary, Halstead length)."
        ),
    )
    parser.add_argument(
        "catalog",
        help="Path to enriched function catalog JSON file.",
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        metavar="FILE",
        help="Write results JSON to FILE instead of stdout.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.9,
        metavar="N",
        help="Minimum similarity score to report (default: 0.9).",
    )
    parser.add_argument(
        "--min-body-lines",
        type=int,
        default=3,
        metavar="N",
        help="Skip functions with fewer body lines (default: 3).",
    )
    parser.add_argument(
        "--min-metrics",
        type=int,
        default=3,
        metavar="N",
        help="Skip pairs with fewer available metrics (default: 3).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # Load catalog
    try:
        with open(args.catalog, "r", encoding="utf-8") as f:
            catalog = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Error reading catalog: {exc}", file=sys.stderr)
        return 1

    if not isinstance(catalog, list):
        print("Error: catalog must be a JSON array of function descriptors.", file=sys.stderr)
        return 1

    # Run detection
    results = detect_metric_clones(
        catalog=catalog,
        threshold=args.threshold,
        min_body_lines=args.min_body_lines,
        min_metrics=args.min_metrics,
    )

    # Output
    output_json = json.dumps(results, indent=2, ensure_ascii=False)

    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output_json)
                f.write("\n")
            print(
                f"Found {len(results)} candidate pair(s) (threshold={args.threshold}). "
                f"Wrote to {args.output}",
                file=sys.stderr,
            )
        except OSError as exc:
            print(f"Error writing to {args.output}: {exc}", file=sys.stderr)
            return 1
    else:
        sys.stdout.write(output_json)
        sys.stdout.write("\n")
        print(
            f"Found {len(results)} candidate pair(s) (threshold={args.threshold}).",
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
