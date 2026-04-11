#!/usr/bin/env python3
from __future__ import annotations
# ABOUTME: Bag-of-AST-nodes cosine similarity detector for Type 3 near-miss clones.
# Represents each function as a Counter of AST node type names from token_sequence,
# then compares pairs via cosine similarity on the count vectors.
# Based on Oreo paper technique — achieves 86% precision on Type 3 clones.
# Input: enriched catalog JSON with token_sequence field (list of AST node type names).
# Output: JSON array of candidate pairs with cosine similarity scores.


import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from lib.common import func_key, func_ref, should_compare
from lib.prefilter import should_prefilter_pair


# ---------------------------------------------------------------------------
# Vector construction
# ---------------------------------------------------------------------------

def ast_node_vector(func: dict[str, Any]) -> Counter[str]:
    """Build a Counter of AST node type names from a function's token_sequence.

    The token_sequence field is expected to be a list of AST node type name
    strings (e.g. ["FunctionDef", "If", "Return", "Call", ...]).

    Returns an empty Counter if token_sequence is absent or empty.
    """
    token_seq = func.get("token_sequence")
    if not token_seq or not isinstance(token_seq, list):
        return Counter()

    result: Counter[str] = Counter()
    for tok in token_seq:
        if isinstance(tok, str):
            result[tok] += 1
        elif isinstance(tok, dict):
            # Handle typed token dicts from tokenize_to_typed()
            node_type = tok.get("type", tok.get("value", ""))
            if node_type:
                result[node_type] += 1
    return result


# ---------------------------------------------------------------------------
# Cosine similarity on Counter vectors
# ---------------------------------------------------------------------------

def cosine_similarity(a: Counter[str], b: Counter[str]) -> float:
    """Compute cosine similarity between two Counter vectors.

    Returns 1.0 for identical non-empty vectors, 0.0 for disjoint or empty.
    """
    if not a or not b:
        return 0.0

    # Dot product: only iterate keys in the smaller counter
    dot = 0.0
    for key, count_a in a.items():
        count_b = b.get(key, 0)
        dot += count_a * count_b

    if dot == 0.0:
        return 0.0

    norm_a = math.sqrt(sum(v * v for v in a.values()))
    norm_b = math.sqrt(sum(v * v for v in b.values()))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return dot / (norm_a * norm_b)


# ---------------------------------------------------------------------------
# Core detection
# ---------------------------------------------------------------------------

def detect_bag_of_ast_duplicates(
    catalog: list[dict[str, Any]],
    threshold: float = 0.85,
) -> list[dict[str, Any]]:
    """Detect Type 3 near-miss clones via bag-of-AST-nodes cosine similarity.

    Algorithm:
    1. For each function build a Counter of AST node type names from token_sequence.
    2. Skip functions with empty vectors.
    3. For each pair passing should_compare + should_prefilter_pair: compute cosine.
    4. Emit pairs where cosine >= threshold.
    """
    # Build vectors, skip empties
    prepared: list[tuple[dict[str, Any], Counter[str]]] = []
    for func in catalog:
        vec = ast_node_vector(func)
        if vec:
            prepared.append((func, vec))

    results: list[dict[str, Any]] = []
    seen_pairs: set[tuple[str, str]] = set()
    n = len(prepared)

    for i in range(n):
        fa, vec_a = prepared[i]
        for j in range(i + 1, n):
            fb, vec_b = prepared[j]

            if not should_compare(fa, fb):
                continue
            if should_prefilter_pair(fa, fb):
                continue

            pair_key = (min(func_key(fa), func_key(fb)), max(func_key(fa), func_key(fb)))
            if pair_key in seen_pairs:
                continue
            seen_pairs.add(pair_key)

            score = cosine_similarity(vec_a, vec_b)
            if score < threshold:
                continue

            results.append({
                "func_a": func_ref(fa),
                "func_b": func_ref(fb),
                "scores": {"cosine": round(score, 4)},
                "final_score": round(score, 4),
                "strategy": "bag_of_ast",
            })

    results.sort(key=lambda r: (
        -r["final_score"],
        r["func_a"]["file"],
        r["func_a"]["line"],
    ))
    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bag-of-AST-nodes cosine similarity duplicate detector (Type 3 clones)."
    )
    parser.add_argument(
        "catalog",
        help="Path to enriched catalog JSON file",
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Output file path (default: stdout)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.85,
        help="Minimum cosine similarity to include a pair (default: 0.85)",
    )

    args = parser.parse_args()

    try:
        with open(args.catalog, "r", encoding="utf-8") as f:
            catalog = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Error loading catalog: {exc}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(catalog, list):
        print("Error: catalog must be a JSON array", file=sys.stderr)
        sys.exit(1)

    results = detect_bag_of_ast_duplicates(catalog, threshold=args.threshold)

    output_json = json.dumps(results, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json + "\n")
        print(
            f"Found {len(results)} similar pair(s), written to {args.output}",
            file=sys.stderr,
        )
    else:
        print(output_json)
        print(
            f"Found {len(results)} similar pair(s)",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
