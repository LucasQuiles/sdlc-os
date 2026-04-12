#!/usr/bin/env python3
from __future__ import annotations
# ABOUTME: Multi-signal merge pipeline — combines outputs from all detection strategies
# into a unified, deduplicated, weighted-confidence duplicate report.

"""
Merge Pipeline for Duplicate Function Detection

Takes outputs from all detection strategies (fuzzy names, signature matching,
token clones, AST similarity, metric similarity, LLM semantic analysis) and
produces a unified report with multi-signal confidence scoring.

Industry standard: A duplicate pair flagged by 3+ independent strategies
gets HIGH confidence automatically (defense in depth).
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


# ============================================================================
# Noise Suppression
# ============================================================================

STORAGE_ERROR_FACTORY_NAMES = frozenset({
    "notFound", "badRequest", "validationFailed", "noFieldsProvided",
    "conflict", "forbidden", "gone", "internal", "duplicate",
    "concurrentModification", "insufficientStock",
})

def _is_crud_name(func: dict) -> bool:
    name = func.get("name", "")
    return any(name.startswith(p) for p in ("create", "get", "update", "delete"))


def _body_lines(func: dict) -> int | None:
    line = func.get("line")
    end_line = func.get("end_line")
    if line is not None and end_line is not None:
        return end_line - line + 1
    return None


def _both_small(pair: dict, max_body_lines: int = 10) -> bool:
    """Returns True only if both functions have known size <= threshold.
    Fails open (returns False = don't suppress) when size is unknown."""
    a_lines = _body_lines(pair.get("func_a", {}))
    b_lines = _body_lines(pair.get("func_b", {}))
    if a_lines is None or b_lines is None:
        return False  # fail open: missing size = don't suppress
    return a_lines <= max_body_lines and b_lines <= max_body_lines


SUPPRESSION_RULES: dict[str, Any] = {
    "selfcontained_wrappers": lambda pair: (
        pair.get("func_a", {}).get("name", "").endswith("SelfContained")
        and pair.get("func_b", {}).get("name", "").endswith("SelfContained")
    ),
    "storage_error_factories": lambda pair: (
        "storage-error" in pair.get("func_a", {}).get("file", "")
        and "storage-error" in pair.get("func_b", {}).get("file", "")
        and pair.get("func_a", {}).get("name", "") in STORAGE_ERROR_FACTORY_NAMES
        and pair.get("func_b", {}).get("name", "") in STORAGE_ERROR_FACTORY_NAMES
    ),
    "crud_boilerplate": lambda pair: (
        _is_crud_name(pair.get("func_a", {}))
        and _is_crud_name(pair.get("func_b", {}))
        and pair.get("func_a", {}).get("name", "") != pair.get("func_b", {}).get("name", "")
        and pair.get("composite_score", 1.0) < 0.95
        and _both_small(pair, max_body_lines=10)
    ),
}


def suppress_noise_patterns(
    pairs: list[dict[str, Any]],
    rules: list[str] | None = None,
    actionable_only: bool = False,
    return_meta: bool = False,
) -> list[dict[str, Any]] | tuple[list[dict[str, Any]], dict[str, Any]]:
    """Remove pairs matching known noise patterns. Returns filtered list.

    When return_meta=True, returns (filtered_pairs, metadata_dict).
    """
    active_rules = [SUPPRESSION_RULES[r] for r in (rules or []) if r in SUPPRESSION_RULES]
    suppressed = 0

    result = []
    for pair in pairs:
        if any(rule(pair) for rule in active_rules):
            suppressed += 1
            continue
        if actionable_only:
            ct = pair.get("clone_type", "")
            conf = pair.get("confidence", "")
            if conf != "HIGH" or ct not in ("Type 1 (exact clone)", "Type 2 (renamed clone)"):
                suppressed += 1
                continue
        result.append(pair)

    if return_meta:
        meta = {
            "suppressed_count": suppressed,
            "remaining_count": len(result),
            "rules_applied": [r for r in (rules or []) if r in SUPPRESSION_RULES],
            "actionable_only": actionable_only,
        }
        return result, meta
    return result


# Strategy weights — tuned for defense in depth
# Higher weight = more trust in that signal
STRATEGY_WEIGHTS: dict[str, float] = {
    "token_clone": 0.95,       # Type 1/2 clones are near-certain
    "ast_similarity": 0.85,    # Structural similarity is very strong
    "tfidf_index": 0.75,       # TF-IDF weighted token overlap — strong signal
    "signature_match": 0.60,   # Same signature is suggestive but not conclusive
    "fuzzy_name": 0.50,        # Name similarity is a hint
    "metric_similarity": 0.45, # Similar metrics = worth investigating
    "llm_semantic": 0.90,      # LLM semantic analysis is very strong
    "bag_of_ast": 0.70,       # Bag-of-AST-nodes cosine — strong structural signal
    "winnowing": 0.65,        # Winnowing fingerprints — partial clone detection
    "lsh_ast": 0.70,          # LSH on AST features — approximate but fast
    "pdg_semantic": 0.80,     # PDG subgraph similarity — strong Type 4 signal
    "code_embedding": 0.72,   # Code2Vec-lite AST path embeddings
}

# Multi-signal confidence thresholds
CONFIDENCE_THRESHOLDS = {
    "HIGH": 0.80,    # 3+ strong signals or 1 near-certain signal
    "MEDIUM": 0.55,  # 2+ signals agree
    "LOW": 0.35,     # 1 signal with moderate confidence
}

# Minimum number of agreeing strategies for auto-HIGH
MIN_STRATEGIES_FOR_HIGH = 3


def make_pair_key(func_a: dict, func_b: dict) -> str:
    """Create canonical key for a function pair (order-independent).

    Uses NULL byte as delimiter to prevent collision when fields contain
    colons, pipes, or other common characters (F-03).
    """
    key_a = f"{func_a.get('file', '')}\0{func_a.get('name', '')}\0{func_a.get('line', 0)}"
    key_b = f"{func_b.get('file', '')}\0{func_b.get('name', '')}\0{func_b.get('line', 0)}"
    return "\x01".join(sorted([key_a, key_b]))


def load_strategy_results(file_path: str) -> list[dict]:
    """Load results from a single strategy output file."""
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
        if not isinstance(data, list):
            print(f"Warning: {file_path} is not a JSON array, skipping", file=sys.stderr)
            return []
        return data
    except (json.JSONDecodeError, FileNotFoundError, OSError) as e:
        print(f"Warning: Could not load {file_path}: {e}", file=sys.stderr)
        return []


def merge_pair_signals(
    all_results: dict[str, list[dict]],
    confidence_thresholds: dict[str, float] | None = None,
    min_strategies_for_high: int = 3,
) -> list[dict]:
    """
    Merge all strategy results into unified pairs with multi-signal scoring.

    For each unique function pair, collect all strategies that flagged it,
    compute a weighted composite score, and assign confidence level.
    """
    thresholds = confidence_thresholds or CONFIDENCE_THRESHOLDS
    min_strats_high = min_strategies_for_high
    # Index: pair_key -> list of (strategy, result)
    pair_index: dict[str, list[tuple[str, dict]]] = defaultdict(list)

    for strategy_name, results in all_results.items():
        for result in results:
            func_a = result.get("func_a", {})
            func_b = result.get("func_b", {})
            if not func_a or not func_b:
                continue
            key = make_pair_key(func_a, func_b)
            pair_index[key].append((strategy_name, result))

    # Build merged output
    merged: list[dict] = []

    for pair_key, signals in pair_index.items():
        # Deduplicate strategies (take highest score per strategy)
        best_per_strategy: dict[str, dict] = {}
        for strategy_name, result in signals:
            strategy = result.get("strategy", strategy_name)
            score = result.get("final_score", 0.0)
            if strategy not in best_per_strategy or score > best_per_strategy[strategy].get("final_score", 0):
                best_per_strategy[strategy] = result

        # Compute weighted composite score
        total_weight = 0.0
        weighted_sum = 0.0
        strategy_details: dict[str, float] = {}

        for strategy, result in best_per_strategy.items():
            weight = STRATEGY_WEIGHTS.get(strategy, 0.5)
            score = result.get("final_score", 0.0)
            weighted_sum += weight * score
            total_weight += weight
            strategy_details[strategy] = round(score, 3)

        composite_score = weighted_sum / total_weight if total_weight > 0 else 0.0
        composite_score = min(composite_score, 1.0)  # Clamp to [0,1] (F-05)
        num_strategies = len(best_per_strategy)

        # --- Strategy correlation groups (Oracle #1+2) ---
        # Strategies sharing the same primary input are NOT independent.
        # Count "effective independent signals" instead of raw strategy count.
        TOKEN_SEQ_GROUP = {"bag_of_ast", "code_embedding", "pdg_semantic", "lsh_ast", "ast_similarity", "winnowing"}
        present = set(best_per_strategy.keys())
        token_seq_count = len(present & TOKEN_SEQ_GROUP)
        # Count at most 2 from the token_sequence group (they share input)
        effective_strategies = num_strategies - max(0, token_seq_count - 2)

        # Cross-strategy negative correlation: signature-only matches in the
        # absence of name similarity are likely false positives in untyped code
        if (
            num_strategies == 1
            and "signature_match" in best_per_strategy
            and "fuzzy_name" not in best_per_strategy
        ):
            composite_score *= 0.7  # Penalize isolated signature matches

        # Contradiction penalty: if structural strategies (AST, token, PDG)
        # are ABSENT while surface strategies (name, signature, metric) flag
        # the pair, reduce confidence. Structural absence is negative evidence.
        # llm_semantic is treated as structural (it analyzes code, not just names) (F-02)
        structural = {"token_clone", "ast_similarity", "pdg_semantic", "code_embedding",
                      "bag_of_ast", "tfidf_index", "winnowing", "lsh_ast", "llm_semantic"}
        surface = {"fuzzy_name", "signature_match", "metric_similarity"}
        has_structural = bool(structural & present)
        has_surface_only = bool(surface & present) and not has_structural
        if has_surface_only and num_strategies >= 2:
            composite_score *= 0.6  # Surface-only multi-signal = contradicted by structural absence

        # Multi-signal confidence: defense in depth
        # Uses effective_strategies (correlation-aware) instead of raw count (Oracle #2)
        # Also requires minimum composite score to prevent weak-signal inflation (F-04)
        MIN_COMPOSITE_FOR_HIGH = 0.5  # Floor: even 3+ strategies can't make HIGH below this
        is_single_strategy = num_strategies == 1
        solo_strategy = list(best_per_strategy.keys())[0] if is_single_strategy else None

        # Only exact token clones (Type 1, score ~1.0) can solo-HIGH.
        # Renamed clones (Type 2, score <1.0) need corroboration.
        is_near_certain_solo = (
            is_single_strategy
            and solo_strategy == "token_clone"
            and best_per_strategy["token_clone"].get("final_score", 0) >= 0.99
        )

        if effective_strategies >= min_strats_high and composite_score >= MIN_COMPOSITE_FOR_HIGH:
            confidence = "HIGH"
        elif is_single_strategy and not is_near_certain_solo:
            # Single heuristic signal: cap at MEDIUM regardless of score
            if composite_score >= thresholds["MEDIUM"]:
                confidence = "MEDIUM"
            elif composite_score >= thresholds["LOW"]:
                confidence = "LOW"
            else:
                continue
        elif composite_score >= thresholds["HIGH"]:
            confidence = "HIGH"
        elif composite_score >= thresholds["MEDIUM"]:
            confidence = "MEDIUM"
        elif composite_score >= thresholds["LOW"]:
            confidence = "LOW"
        else:
            continue  # Below minimum threshold, skip

        # Pick representative func_a/func_b from first signal
        first_result = list(best_per_strategy.values())[0]
        func_a = first_result.get("func_a", {})
        func_b = first_result.get("func_b", {})

        merged.append({
            "func_a": {
                "name": func_a.get("name", "unknown"),
                "file": func_a.get("file", "unknown"),
                "line": func_a.get("line", 0),
                "qualified_name": func_a.get("qualified_name", func_a.get("name", "unknown")),
                "end_line": func_a.get("end_line"),  # None if upstream didn't provide
            },
            "func_b": {
                "name": func_b.get("name", "unknown"),
                "file": func_b.get("file", "unknown"),
                "line": func_b.get("line", 0),
                "qualified_name": func_b.get("qualified_name", func_b.get("name", "unknown")),
                "end_line": func_b.get("end_line"),  # None if upstream didn't provide
            },
            "composite_score": round(composite_score, 3),
            "confidence": confidence,
            "num_strategies": num_strategies,
            "strategies": strategy_details,
            "clone_type": classify_clone_type(best_per_strategy),
            "recommendation": generate_recommendation(confidence, num_strategies, best_per_strategy),
        })

    # Sort by composite score descending, then by number of strategies
    merged.sort(key=lambda x: (-x["composite_score"], -x["num_strategies"]))
    return merged


def classify_clone_type(strategies: dict[str, dict]) -> str:
    """
    Classify the clone type based on which strategies triggered.

    Clone taxonomy (standard):
    - Type 1: Exact clones (whitespace/comment differences only)
    - Type 2: Renamed clones (identifiers renamed)
    - Type 3: Near-miss clones (statements added/removed)
    - Type 4: Semantic clones (different implementation, same behavior)
    """
    if "token_clone" in strategies:
        clone_info = strategies["token_clone"].get("scores", {})
        ct = clone_info.get("clone_type", 2)
        if ct == 1:
            return "Type 1 (exact clone)"
        return "Type 2 (renamed clone)"

    if "ast_similarity" in strategies:
        score = strategies["ast_similarity"].get("final_score", 0)
        if score >= 0.95:
            return "Type 2 (renamed clone)"
        return "Type 3 (near-miss clone)"

    if "llm_semantic" in strategies:
        return "Type 4 (semantic clone)"

    if "signature_match" in strategies and "fuzzy_name" in strategies:
        return "Type 3 (near-miss clone)"

    return "Type 4 (semantic clone)"


def generate_recommendation(
    confidence: str,
    num_strategies: int,
    strategies: dict[str, dict],
) -> dict[str, str]:
    """Generate actionable recommendation based on confidence and signals."""
    if confidence == "HIGH":
        if "token_clone" in strategies:
            return {
                "action": "CONSOLIDATE",
                "urgency": "immediate",
                "reason": f"Structurally identical code detected by {num_strategies} independent strategies",
            }
        return {
            "action": "CONSOLIDATE",
            "urgency": "high",
            "reason": f"Strong duplicate signal from {num_strategies} independent detection strategies",
        }

    if confidence == "MEDIUM":
        return {
            "action": "INVESTIGATE",
            "urgency": "normal",
            "reason": f"Likely duplicate flagged by {num_strategies} strategy(ies) — review implementations",
        }

    return {
        "action": "REVIEW",
        "urgency": "low",
        "reason": f"Possible duplicate flagged by {num_strategies} strategy — may be intentional",
    }


def generate_summary(merged: list[dict]) -> dict[str, Any]:
    """Generate summary statistics for the merged results."""
    by_confidence = defaultdict(int)
    by_clone_type = defaultdict(int)
    by_action = defaultdict(int)
    strategies_seen: set[str] = set()

    for item in merged:
        by_confidence[item["confidence"]] += 1
        by_clone_type[item["clone_type"]] += 1
        by_action[item["recommendation"]["action"]] += 1
        strategies_seen.update(item["strategies"].keys())

    return {
        "total_pairs": len(merged),
        "by_confidence": dict(by_confidence),
        "by_clone_type": dict(by_clone_type),
        "by_action": dict(by_action),
        "strategies_used": sorted(strategies_seen),
        "multi_signal_pairs": sum(1 for m in merged if m["num_strategies"] >= 2),
        "defense_depth_pairs": sum(1 for m in merged if m["num_strategies"] >= 3),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Merge multi-signal duplicate detection results into unified report"
    )
    parser.add_argument(
        "input_dir",
        help="Directory containing strategy output JSON files",
    )
    parser.add_argument(
        "-o", "--output",
        default="/dev/stdout",
        help="Output file (default: stdout)",
    )
    parser.add_argument(
        "--strategy-files",
        nargs="*",
        help="Specific strategy files to merge (overrides input_dir scan)",
    )
    parser.add_argument(
        "--high-threshold",
        type=float,
        default=CONFIDENCE_THRESHOLDS["HIGH"],
        help=f"Score threshold for HIGH confidence (default: {CONFIDENCE_THRESHOLDS['HIGH']})",
    )
    parser.add_argument(
        "--min-strategies-high",
        type=int,
        default=MIN_STRATEGIES_FOR_HIGH,
        help=f"Min strategies for auto-HIGH (default: {MIN_STRATEGIES_FOR_HIGH})",
    )
    parser.add_argument(
        "--include-summary",
        action="store_true",
        help="Include summary statistics in output",
    )
    parser.add_argument("--suppress", nargs="*", default=[],
        choices=list(SUPPRESSION_RULES.keys()),
        help="Noise suppression rules to apply after merge")
    parser.add_argument("--actionable-only", action="store_true",
        help="Emit only Type 1/2 exact clones at HIGH confidence after suppression")

    args = parser.parse_args()

    # Build config from args (no global mutation)
    user_thresholds = dict(CONFIDENCE_THRESHOLDS)
    user_thresholds["HIGH"] = args.high_threshold
    user_min_strategies = args.min_strategies_high

    # Collect strategy result files
    all_results: dict[str, list[dict]] = {}

    if args.strategy_files:
        for filepath in args.strategy_files:
            strategy_name = Path(filepath).stem.replace("detect-", "").replace("-results", "").replace("_", "-")
            results = load_strategy_results(filepath)
            if results:
                all_results[strategy_name] = results
    else:
        input_dir = Path(args.input_dir)
        if not input_dir.is_dir():
            print(f"Error: {args.input_dir} is not a directory", file=sys.stderr)
            sys.exit(1)

        # Load all JSON files that look like strategy outputs
        for json_file in sorted(input_dir.glob("*-results.json")):
            strategy_name = json_file.stem.replace("-results", "")
            results = load_strategy_results(str(json_file))
            if results:
                all_results[strategy_name] = results

        # Also load LLM semantic results if present
        for json_file in sorted(input_dir.glob("duplicates/*.json")):
            results = load_strategy_results(str(json_file))
            if results:
                # Convert LLM format to our pair format if needed
                converted = convert_llm_results(results)
                all_results.setdefault("llm_semantic", []).extend(converted)

    if not all_results:
        print("Warning: No strategy results found", file=sys.stderr)
        output = {"pairs": [], "summary": generate_summary([])}
        with open(args.output, "w") as f:
            json.dump(output, f, indent=2)
        return

    print(f"Merging results from {len(all_results)} strategies: {', '.join(all_results.keys())}", file=sys.stderr)
    for name, results in all_results.items():
        print(f"  {name}: {len(results)} candidate pairs", file=sys.stderr)

    # Merge
    merged = merge_pair_signals(
        all_results,
        confidence_thresholds=user_thresholds,
        min_strategies_for_high=user_min_strategies,
    )

    # Apply noise suppression if requested
    if args.suppress or args.actionable_only:
        pre_count = len(merged)
        merged, suppression_meta = suppress_noise_patterns(
            merged, rules=args.suppress, actionable_only=args.actionable_only, return_meta=True
        )
        print(f"\n  Suppressed {suppression_meta['suppressed_count']} noise pairs "
              f"({len(merged)} remaining)", file=sys.stderr)

    summary = generate_summary(merged)

    print(f"\nMerge complete:", file=sys.stderr)
    print(f"  Total unique pairs: {summary['total_pairs']}", file=sys.stderr)
    print(f"  HIGH confidence: {summary['by_confidence'].get('HIGH', 0)}", file=sys.stderr)
    print(f"  MEDIUM confidence: {summary['by_confidence'].get('MEDIUM', 0)}", file=sys.stderr)
    print(f"  LOW confidence: {summary['by_confidence'].get('LOW', 0)}", file=sys.stderr)
    print(f"  Multi-signal (2+): {summary['multi_signal_pairs']}", file=sys.stderr)
    print(f"  Defense depth (3+): {summary['defense_depth_pairs']}", file=sys.stderr)

    # Output
    if args.include_summary:
        output = {"pairs": merged, "summary": summary}
    else:
        output = merged

    try:
        with open(args.output, "w") as f:
            json.dump(output, f, indent=2)
    except (IsADirectoryError, PermissionError, OSError) as e:
        print(f"Error writing output to {args.output}: {e}", file=sys.stderr)
        sys.exit(1)


def convert_llm_results(results: list[dict]) -> list[dict]:
    """
    Convert LLM semantic analysis results (from the existing opus phase)
    into the standard pair format used by other strategies.

    LLM results use a group format:
    {
        "intent": "...",
        "confidence": "HIGH|MEDIUM|LOW",
        "functions": [...],
        "recommendation": {...}
    }

    We convert each group into pairwise combinations.
    """
    pairs: list[dict] = []

    for group in results:
        functions = group.get("functions", [])
        confidence = group.get("confidence", "LOW")
        score_map = {"HIGH": 0.95, "MEDIUM": 0.7, "LOW": 0.4}
        score = score_map.get(confidence, 0.5)

        # Generate all pairs within the group (RES-006: skip non-dict entries)
        functions = [f for f in functions if isinstance(f, dict)]
        for i in range(len(functions)):
            for j in range(i + 1, len(functions)):
                fa = functions[i]
                fb = functions[j]
                pairs.append({
                    "func_a": {
                        "name": fa.get("name", "unknown"),
                        "file": fa.get("file", "unknown"),
                        "line": fa.get("line", 0),
                    },
                    "func_b": {
                        "name": fb.get("name", "unknown"),
                        "file": fb.get("file", "unknown"),
                        "line": fb.get("line", 0),
                    },
                    "scores": {"llm_confidence": confidence},
                    "final_score": score,
                    "strategy": "llm_semantic",
                })

    return pairs


if __name__ == "__main__":
    main()
