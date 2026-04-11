#!/usr/bin/env python3
# ABOUTME: Precision/recall/F1 evaluation harness for duplicate function detection.
# Measures detection accuracy by comparing pipeline output against a ground truth corpus.

"""
Evaluation Harness for Duplicate Function Detection

Loads merged pipeline results and ground truth corpus, then computes
precision, recall, and F1 per clone type and overall.

Usage:
  ./evaluate.py --results merged-results.json --corpus eval-corpus.json
  ./evaluate.py --results merged-results.json --corpus eval-corpus.json --min-confidence HIGH -o eval-out.json
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Confidence levels and their numeric ordering for threshold filtering
CONFIDENCE_ORDER = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}


def make_pair_key(func_spec_a: str, func_spec_b: str) -> str:
    """Create canonical, order-independent key from two 'file:name:line' specs."""
    return "|".join(sorted([func_spec_a, func_spec_b]))


def _func_to_spec(func: dict) -> str:
    """Convert a func dict with file/name/line to a 'file:name:line' spec string."""
    return f"{func.get('file', '')}:{func.get('name', '')}:{func.get('line', 0)}"


def load_ground_truth(corpus_path: str) -> dict[str, dict]:
    """
    Load corpus JSON and index ground truth pairs by canonical pair key.

    Returns dict mapping pair_key -> ground truth entry with fields:
      - is_clone: bool
      - clone_type: int | None
      - func_a: str (file:name:line)
      - func_b: str (file:name:line)
    """
    with open(corpus_path) as f:
        corpus = json.load(f)

    index: dict[str, dict] = {}
    for entry in corpus.get("ground_truth", []):
        key = make_pair_key(entry["func_a"], entry["func_b"])
        index[key] = {
            "is_clone": entry["is_clone"],
            "clone_type": entry.get("clone_type"),
            "func_a": entry["func_a"],
            "func_b": entry["func_b"],
        }
    return index


def load_detected_pairs(
    results_path: str,
    min_confidence: str = "LOW",
    min_strategies: int = 1,
    min_score: float = 0.0,
) -> set[str]:
    """
    Load merged pipeline results and return canonical pair keys for all pairs
    at or above the given confidence threshold, strategy count, and score.

    Accepts results as either:
      - A list of pair dicts (bare array format)
      - An object with a "pairs" key (include-summary format)
    """
    with open(results_path) as f:
        data = json.load(f)

    if isinstance(data, dict) and "pairs" in data:
        pairs = data["pairs"]
    elif isinstance(data, list):
        pairs = data
    else:
        return set()

    min_level = CONFIDENCE_ORDER.get(min_confidence, 1)
    detected: set[str] = set()

    for pair in pairs:
        confidence = pair.get("confidence", "LOW")
        level = CONFIDENCE_ORDER.get(confidence, 0)
        num_strats = pair.get("num_strategies", 1)
        score = pair.get("composite_score", 0.0)
        if level >= min_level and num_strats >= min_strategies and score >= min_score:
            func_a = pair.get("func_a", {})
            func_b = pair.get("func_b", {})
            spec_a = _func_to_spec(func_a)
            spec_b = _func_to_spec(func_b)
            key = make_pair_key(spec_a, spec_b)
            detected.add(key)

    return detected


def _safe_divide(numerator: float, denominator: float) -> float:
    """Return numerator/denominator, or 0.0 if denominator is zero."""
    return numerator / denominator if denominator > 0 else 0.0


def _compute_metrics(tp: int, fp: int, fn: int) -> dict[str, Any]:
    """Compute precision, recall, F1 from raw counts."""
    precision = _safe_divide(tp, tp + fp)
    recall = _safe_divide(tp, tp + fn)
    f1 = _safe_divide(2 * precision * recall, precision + recall)
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }


def evaluate(
    detected: set[str],
    ground_truth: dict[str, dict],
) -> dict[str, Any]:
    """
    Compute precision/recall/F1 overall and per clone type.

    Args:
        detected: set of canonical pair keys that the pipeline flagged
        ground_truth: dict of pair_key -> ground truth entry (from load_ground_truth)

    Returns:
        {
            "overall": {"tp", "fp", "fn", "precision", "recall", "f1"},
            "by_type": {"1": {...}, "2": {...}, "3": {...}, "4": {...}},
            "summary": "P=... R=... F1=..."
        }
    """
    # Separate actual clones from non-clones
    actual_clones: set[str] = set()
    type_map: dict[str, set[str]] = {}  # clone_type str -> set of pair keys

    for key, entry in ground_truth.items():
        if entry["is_clone"]:
            actual_clones.add(key)
            ct = str(entry["clone_type"]) if entry["clone_type"] is not None else "unknown"
            type_map.setdefault(ct, set()).add(key)

    # Overall counts
    tp_keys = detected & actual_clones
    fp_keys = detected - actual_clones
    fn_keys = actual_clones - detected

    overall = _compute_metrics(len(tp_keys), len(fp_keys), len(fn_keys))

    # Per-type breakdown — only for types that appear in ground truth
    by_type: dict[str, dict] = {}
    for ct, gt_keys_for_type in sorted(type_map.items()):
        tp = len(detected & gt_keys_for_type)
        fp_for_type = len(detected & (set(ground_truth.keys()) - gt_keys_for_type) - actual_clones)
        fn = len(gt_keys_for_type - detected)
        # FP for per-type: detected pairs that are NOT this clone type
        # (i.e., we over-counted or wrongly assigned — use global FP for overall, but
        #  for per-type we track misses within type and global FP is shared)
        # Standard per-type: TP = hit this type, FN = missed this type, FP = global FP
        by_type[ct] = _compute_metrics(tp, len(fp_keys), fn)

    summary_p = overall["precision"]
    summary_r = overall["recall"]
    summary_f1 = overall["f1"]
    summary = f"P={summary_p:.2f} R={summary_r:.2f} F1={summary_f1:.2f}"

    return {
        "overall": overall,
        "by_type": by_type,
        "summary": summary,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate duplicate detection precision/recall/F1 against ground truth"
    )
    parser.add_argument(
        "--results",
        required=True,
        help="Path to merged pipeline results JSON",
    )
    parser.add_argument(
        "--corpus",
        required=True,
        help="Path to ground truth corpus JSON",
    )
    parser.add_argument(
        "--min-confidence",
        default="LOW",
        choices=["LOW", "MEDIUM", "HIGH"],
        help="Minimum confidence level to count as detected (default: LOW)",
    )
    parser.add_argument(
        "--min-strategies",
        type=int,
        default=1,
        help="Minimum number of agreeing strategies (default: 1)",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.0,
        help="Minimum composite score (default: 0.0)",
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Output file path (default: stdout)",
    )

    args = parser.parse_args()

    # Load inputs
    try:
        ground_truth = load_ground_truth(args.corpus)
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        print(f"Error loading corpus: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        detected = load_detected_pairs(
            args.results, args.min_confidence,
            min_strategies=args.min_strategies,
            min_score=args.min_score,
        )
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading results: {e}", file=sys.stderr)
        sys.exit(1)

    result = evaluate(detected, ground_truth)

    print(f"Evaluation complete:", file=sys.stderr)
    print(f"  Ground truth pairs: {len(ground_truth)}", file=sys.stderr)
    actual_count = sum(1 for e in ground_truth.values() if e["is_clone"])
    print(f"  Actual clones: {actual_count}", file=sys.stderr)
    print(f"  Detected pairs (>={args.min_confidence}): {len(detected)}", file=sys.stderr)
    print(f"  {result['summary']}", file=sys.stderr)

    output_text = json.dumps(result, indent=2)
    if args.output:
        Path(args.output).write_text(output_text)
        print(f"Results written to {args.output}", file=sys.stderr)
    else:
        print(output_text)


if __name__ == "__main__":
    main()
