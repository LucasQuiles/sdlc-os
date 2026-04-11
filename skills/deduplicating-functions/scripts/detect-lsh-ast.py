#!/usr/bin/env python3
from __future__ import annotations
# ABOUTME: LSH (Locality-Sensitive Hashing) duplicate detector using MinHash on token sets.
# Replaces O(n^2) comparison with sub-linear ANN retrieval via datasketch MinHashLSH.
# Input: enriched catalog JSON with token_sequence arrays per function.
# Output: JSON array of scored candidate pairs.

"""
detect-lsh-ast.py -- MinHash + LSH approximate nearest neighbor duplicate detection.

Builds a MinHash signature for each function's token set, inserts into a
MinHashLSH index, then queries each function to find similar candidates.
Scales to large catalogs without O(n^2) brute-force comparison.

Input: Catalog JSON with token_sequence arrays.
Output: JSON array of scored candidate pairs.
"""


import argparse
import json
import sys
from pathlib import Path
from typing import Any

from datasketch import MinHash, MinHashLSH

sys.path.insert(0, str(Path(__file__).parent))

from lib.common import func_key, func_ref, should_compare
from lib.prefilter import should_prefilter_pair


# ---------------------------------------------------------------------------
# MinHash helpers
# ---------------------------------------------------------------------------

def get_token_set(func: dict[str, Any]) -> set[str]:
    """Extract a set of unique token strings from a function entry."""
    ts = func.get("token_sequence")
    if ts and isinstance(ts, list):
        tokens: list[str] = []
        for t in ts:
            if isinstance(t, dict):
                val = t.get("value", "")
                if val:
                    tokens.append(val)
            elif isinstance(t, str) and t:
                tokens.append(t)
        return set(tokens)
    # Fallback: split context field
    ctx = func.get("context", "")
    if ctx:
        return set(ctx.split())
    return set()


def build_minhash(token_set: set[str], num_perm: int = 128) -> MinHash:
    """Create a MinHash signature from a set of token strings.

    Each token is encoded to UTF-8 bytes before updating the MinHash,
    as required by datasketch.

    Args:
        token_set: Set of token strings representing the function.
        num_perm: Number of permutations (hash functions). Higher = more accurate.

    Returns:
        A MinHash object with the signature computed from token_set.
    """
    m = MinHash(num_perm=num_perm)
    for token in token_set:
        m.update(token.encode("utf-8"))
    return m


# ---------------------------------------------------------------------------
# Core detection
# ---------------------------------------------------------------------------

def detect_lsh_duplicates(
    catalog: list[dict[str, Any]],
    threshold: float = 0.75,
    num_perm: int = 128,
) -> list[dict[str, Any]]:
    """Run MinHash + LSH duplicate detection on the catalog.

    Algorithm:
    1. Extract token set for each function (skip empty or < 5 unique tokens).
    2. Build MinHash for each function.
    3. Insert all into a MinHashLSH index keyed by func_key().
    4. Query each function against the LSH index.
    5. For each candidate pair, estimate Jaccard from MinHash signatures.
    6. Filter pairs below threshold; deduplicate order-independently.

    Args:
        catalog: List of function entry dicts (enriched catalog format).
        threshold: Minimum estimated Jaccard similarity to report.
        num_perm: Number of MinHash permutations (default 128).

    Returns:
        Sorted list of result dicts with func_a, func_b, scores, final_score,
        and strategy fields.
    """
    if num_perm < 2:
        print("Warning: num_perm must be >= 2, defaulting to 128", file=sys.stderr)
        num_perm = 128

    if not catalog:
        return []

    # --- Phase 1: build MinHash for each eligible function ---
    # Maps func_key -> (func_entry, MinHash)
    key_to_func: dict[str, dict[str, Any]] = {}
    key_to_minhash: dict[str, MinHash] = {}

    for func in catalog:
        token_set = get_token_set(func)
        if not token_set or len(token_set) < 5:
            continue
        key = func_key(func)
        # If duplicate keys exist (shouldn't in a well-formed catalog), last wins
        key_to_func[key] = func
        key_to_minhash[key] = build_minhash(token_set, num_perm=num_perm)

    if len(key_to_func) < 2:
        return []

    # --- Phase 2: insert into LSH index ---
    lsh = MinHashLSH(threshold=threshold, num_perm=num_perm)
    for key, mh in key_to_minhash.items():
        lsh.insert(key, mh)

    # --- Phase 3: query and collect candidate pairs ---
    seen_pairs: set[tuple[str, str]] = set()
    results: list[dict[str, Any]] = []

    for key_a, mh_a in key_to_minhash.items():
        candidates = lsh.query(mh_a)
        fa = key_to_func[key_a]

        for key_b in candidates:
            if key_b == key_a:
                continue  # skip self

            fb = key_to_func[key_b]
            if not should_compare(fa, fb):
                continue
            if should_prefilter_pair(fa, fb):
                continue

            # Canonical ordering for deduplication
            pair = (min(key_a, key_b), max(key_a, key_b))
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)

            # Estimate Jaccard from MinHash signatures
            mh_b = key_to_minhash[key_b]
            estimated_jaccard = mh_a.jaccard(mh_b)

            if estimated_jaccard < threshold:
                continue

            # Canonicalize func_a/func_b order for deterministic output
            # (set/dict iteration order varies across runs)
            if key_a <= key_b:
                fa_out, fb_out = fa, fb
            else:
                fa_out, fb_out = fb, fa

            results.append({
                "func_a": func_ref(fa_out),
                "func_b": func_ref(fb_out),
                "scores": {"estimated_jaccard": round(estimated_jaccard, 4)},
                "final_score": round(estimated_jaccard, 4),
                "strategy": "lsh_ast",
            })

    results.sort(key=lambda r: (
        -r["final_score"],
        r["func_a"]["file"],
        r["func_a"]["line"],
        r["func_b"]["file"],
        r["func_b"]["line"],
    ))
    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="LSH (MinHash) duplicate detector — sub-linear ANN retrieval on token sets."
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
        default=0.75,
        help="Minimum estimated Jaccard similarity to report (default: 0.75)",
    )
    parser.add_argument(
        "--num-perm",
        type=int,
        default=128,
        help="Number of MinHash permutations (default: 128, higher = more accurate)",
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

    results = detect_lsh_duplicates(catalog, threshold=args.threshold, num_perm=args.num_perm)

    output_json = json.dumps(results, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json + "\n")
        print(
            f"Found {len(results)} LSH candidate pair(s), written to {args.output}",
            file=sys.stderr,
        )
    else:
        print(output_json)
        print(
            f"Found {len(results)} LSH candidate pair(s)",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
