#!/usr/bin/env python3
from __future__ import annotations
# ABOUTME: Code2Vec-lite AST path embedding detector for structural duplicate detection.
# Builds bag-of-AST-path vectors from contiguous n-gram subsequences of token_sequence,
# then compares pairs via cosine similarity on the count vectors.
# Captures local structural patterns (not just unigram counts) — catches Type 3 near-miss
# clones where the bag-of-AST unigrams diverge but structural paths remain shared.
# Input: enriched catalog JSON with token_sequence field (list of AST node type names).
# Output: JSON array of candidate pairs with path_cosine similarity scores.


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
# Path extraction — contiguous n-gram subsequences
# ---------------------------------------------------------------------------

def extract_ast_paths(
    token_sequence: list[str],
    min_len: int = 3,
    max_len: int = 5,
) -> list[tuple[str, ...]]:
    """Extract all contiguous subsequences of AST node types as path tuples.

    For a token_sequence like ["If", "Compare", "Call", "Return", "Name"] with
    min_len=3, max_len=5 this yields:
      3-grams: ("If","Compare","Call"), ("Compare","Call","Return"), ("Call","Return","Name")
      4-grams: ("If","Compare","Call","Return"), ("Compare","Call","Return","Name")
      5-grams: ("If","Compare","Call","Return","Name")

    Returns an empty list for sequences shorter than min_len or non-list input.
    """
    if not token_sequence or not isinstance(token_sequence, list):
        return []

    # Normalise: accept plain strings or typed dicts
    strs: list[str] = []
    for tok in token_sequence:
        if isinstance(tok, str):
            strs.append(tok)
        elif isinstance(tok, dict):
            node_type = tok.get("type", tok.get("value", ""))
            if node_type:
                strs.append(node_type)

    n = len(strs)
    paths: list[tuple[str, ...]] = []
    for length in range(min_len, min(max_len, n) + 1):
        for i in range(n - length + 1):
            paths.append(tuple(strs[i : i + length]))
    return paths


# ---------------------------------------------------------------------------
# Embedding construction
# ---------------------------------------------------------------------------

def build_embedding(
    func: dict[str, Any],
    min_len: int = 3,
    max_len: int = 5,
) -> Counter[tuple[str, ...]]:
    """Build a Counter of AST path tuples from a function's token_sequence.

    Returns an empty Counter if token_sequence is absent, empty, or too short
    to produce any paths of length >= min_len.
    """
    token_seq = func.get("token_sequence")
    if not token_seq or not isinstance(token_seq, list):
        return Counter()
    paths = extract_ast_paths(token_seq, min_len=min_len, max_len=max_len)
    return Counter(paths)


# ---------------------------------------------------------------------------
# Cosine similarity on Counter[tuple] vectors
# ---------------------------------------------------------------------------

def embedding_cosine(
    a: Counter[tuple[str, ...]],
    b: Counter[tuple[str, ...]],
) -> float:
    """Compute cosine similarity between two path-embedding Counters.

    Returns 1.0 for identical non-empty embeddings, 0.0 for disjoint or empty.

    dot(a, b) / (||a|| * ||b||) computed on the sparse count vectors.
    """
    if not a or not b:
        return 0.0

    # Dot product over shared keys only
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
# Core detection pipeline
# ---------------------------------------------------------------------------

def detect_embedding_duplicates(
    catalog: list[dict[str, Any]],
    threshold: float = 0.5,
    min_path_len: int = 3,
    max_path_len: int = 5,
) -> list[dict[str, Any]]:
    """Detect structural duplicates via Code2Vec-lite AST path embeddings.

    Algorithm:
    1. For each function build a Counter of AST path n-grams from token_sequence.
    2. Skip functions whose embedding is empty (too short or missing token_sequence).
    3. For each pair passing should_compare + should_prefilter_pair: compute cosine.
    4. Emit pairs where cosine >= threshold.

    Returns results sorted by final_score descending, then by file/line for stability.
    """
    # Build embeddings, skip empties
    prepared: list[tuple[dict[str, Any], Counter[tuple[str, ...]]]] = []
    for func in catalog:
        emb = build_embedding(func, min_len=min_path_len, max_len=max_path_len)
        if emb:
            prepared.append((func, emb))

    results: list[dict[str, Any]] = []
    seen_pairs: set[tuple[str, str]] = set()
    n = len(prepared)

    for i in range(n):
        fa, emb_a = prepared[i]
        for j in range(i + 1, n):
            fb, emb_b = prepared[j]

            if not should_compare(fa, fb):
                continue
            if should_prefilter_pair(fa, fb):
                continue

            pair_key = (
                min(func_key(fa), func_key(fb)),
                max(func_key(fa), func_key(fb)),
            )
            if pair_key in seen_pairs:
                continue
            seen_pairs.add(pair_key)

            score = embedding_cosine(emb_a, emb_b)
            if score < threshold:
                continue

            results.append({
                "func_a": func_ref(fa),
                "func_b": func_ref(fb),
                "scores": {"path_cosine": round(score, 4)},
                "final_score": round(score, 4),
                "strategy": "code_embedding",
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
        description=(
            "Code2Vec-lite AST path embedding duplicate detector. "
            "Builds bag-of-AST-path vectors (contiguous n-grams of token_sequence) "
            "and compares function pairs via cosine similarity."
        )
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
        default=0.5,
        help="Minimum path_cosine similarity to include a pair (default: 0.5)",
    )
    parser.add_argument(
        "--min-path-len",
        type=int,
        default=3,
        help="Minimum AST path length (n-gram size) (default: 3)",
    )
    parser.add_argument(
        "--max-path-len",
        type=int,
        default=5,
        help="Maximum AST path length (n-gram size) (default: 5)",
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

    results = detect_embedding_duplicates(
        catalog,
        threshold=args.threshold,
        min_path_len=args.min_path_len,
        max_path_len=args.max_path_len,
    )

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
