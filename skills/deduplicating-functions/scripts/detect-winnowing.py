#!/usr/bin/env python3
from __future__ import annotations
# ABOUTME: Winnowing fingerprint detector for partial clone detection (Type 3/4 clones).
# Implements Moss/Winnowing algorithm: k-gram hashing + sliding window minimum selection.
# Detects partial clones where one function contains a copied fragment of another.
# Guarantee: any shared substring >= k+w-1 tokens will be detected.
# Input: enriched catalog JSON with optional token_sequence arrays per function.
# Output: JSON array of scored candidate pairs with strategy: "winnowing".

"""
detect-winnowing.py -- Winnowing positional substring fingerprinting.

Algorithm:
  1. Tokenize function body (token_sequence or context fallback).
  2. Generate k-grams (k=5): consecutive k-token tuples.
  3. Hash each k-gram with a stable hash (SHA-256 truncated to 64 bits).
     Python's built-in hash() is NOT used because it is salted per process
     under PYTHONHASHSEED=random, making winnowing nondeterministic.
  4. Slide a window of size w=4 across hashes; select the minimum from each
     window position, tracking hash positions to avoid duplicate selections.
  5. The resulting set of selected hashes = the function's fingerprint.
  6. Score pairs: max(jaccard(fp_a, fp_b), overlap_coefficient(fp_a, fp_b)).
     Jaccard catches symmetric overlap; overlap_coefficient catches containment.

References:
  Schleimer, Wilkerson, Aiken — "Winnowing: Local Algorithms for Document
  Fingerprinting", SIGMOD 2003.
"""


import argparse
import json
import sys
from itertools import combinations
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from lib.common import func_ref, func_key, should_compare, jaccard, overlap_coefficient, stable_hash, tokenize_to_strings
from lib.prefilter import should_prefilter_pair


# ---------------------------------------------------------------------------
# Core Winnowing primitives
# ---------------------------------------------------------------------------

def kgrams(seq: list[str], k: int) -> list[tuple[str, ...]]:
    """Generate all k-grams (consecutive k-tuples) from token sequence.

    Returns an empty list when len(seq) < k or k < 1 (RES-002).

    Examples::

        >>> kgrams(["a", "b", "c", "d"], 2)
        [('a', 'b'), ('b', 'c'), ('c', 'd')]
        >>> kgrams(["x"], 3)
        []
    """
    if k < 1 or len(seq) < k:
        return []
    return [tuple(seq[i:i + k]) for i in range(len(seq) - k + 1)]


def winnow(hashes: list[int], window: int) -> set[int]:
    """Select fingerprint hashes using the Winnowing algorithm.

    Slides a window of size `window` across `hashes`. For each window
    position, the minimum hash is selected. A hash is only added to the
    fingerprint when it is newly selected (i.e., the minimum changes or
    the previous minimum drops out of the window).

    This guarantees that any sequence of `window` consecutive hashes
    contributes at least one hash to the fingerprint.

    Returns an empty set for empty, too-short input, or window < 1 (RES-001).
    """
    if window < 1 or not hashes:
        return set()
    if len(hashes) < window:
        # Window larger than input — just return all hashes as fingerprint
        return set(hashes)

    fingerprint: set[int] = set()
    # Track (hash, position) of current minimum so we know when it leaves window
    current_min_hash: int | None = None
    current_min_pos: int = -1

    for i in range(len(hashes) - window + 1):
        window_slice = hashes[i:i + window]

        # If current minimum is still in this window, check if there's a smaller one
        if current_min_pos >= i:
            # Current min still valid — find if there's a strictly smaller value
            w_min = min(window_slice)
            if w_min < current_min_hash:  # type: ignore[operator]
                # New smaller minimum found
                current_min_pos = i + window_slice.index(w_min)
                current_min_hash = w_min
                fingerprint.add(current_min_hash)
        else:
            # Previous minimum has slid out — recompute minimum for this window
            w_min = min(window_slice)
            # Prefer rightmost occurrence for stability (as per original paper)
            # Find last occurrence of minimum in window
            last_pos = len(window_slice) - 1 - window_slice[::-1].index(w_min)
            current_min_pos = i + last_pos
            current_min_hash = w_min
            fingerprint.add(current_min_hash)

    return fingerprint


def _get_token_strings(func: dict[str, Any]) -> list[str]:
    """Extract flat string token list from a function entry.

    Prefers the pre-computed token_sequence field; falls back to tokenizing
    the context field via tokenize_to_strings.
    """
    ts = func.get("token_sequence")
    if ts and isinstance(ts, list) and len(ts) > 0:
        if isinstance(ts[0], dict):
            return [t.get("value", "") for t in ts if isinstance(t, dict)]
        return [str(t) for t in ts]

    ctx = func.get("context", "")
    if ctx:
        return tokenize_to_strings(ctx)

    return []


def compute_fingerprint(func: dict[str, Any], k: int = 5, window: int = 4) -> set[int]:
    """Compute the Winnowing fingerprint for a function entry.

    Steps:
      1. Extract token strings.
      2. Generate k-grams.
      3. Hash each k-gram.
      4. Winnow the hash sequence.

    Returns an empty set if the function has insufficient tokens.
    """
    tokens = _get_token_strings(func)
    grams = kgrams(tokens, k)
    if not grams:
        return set()
    hashes = [stable_hash(g) for g in grams]
    return winnow(hashes, window)


def fingerprint_similarity(fp_a: set[int], fp_b: set[int]) -> float:
    """Compute similarity between two fingerprints.

    Returns max(jaccard, overlap_coefficient).
    - Jaccard handles symmetric similarity (both functions share content).
    - Overlap coefficient handles containment (one function is a subset clone).

    Returns 0.0 when either fingerprint is empty.
    """
    if not fp_a or not fp_b:
        return 0.0
    j = jaccard(fp_a, fp_b)
    oc = overlap_coefficient(fp_a, fp_b)
    return max(j, oc)


# ---------------------------------------------------------------------------
# Full pipeline
# ---------------------------------------------------------------------------

def detect_winnowing_duplicates(
    catalog: list[dict[str, Any]],
    threshold: float = 0.4,
    k: int = 5,
    window: int = 4,
) -> list[dict[str, Any]]:
    """Run Winnowing duplicate detection over an entire function catalog.

    For each function, computes a Winnowing fingerprint. Then compares all
    eligible pairs (using should_compare and should_prefilter_pair guards),
    scoring by fingerprint_similarity. Returns pairs whose score >= threshold.

    Output records have the form::

        {
            "func_a": func_ref(...),
            "func_b": func_ref(...),
            "scores": {"jaccard": float, "overlap": float},
            "final_score": float,
            "strategy": "winnowing",
        }
    """
    if not catalog:
        return []

    # Precompute fingerprints for all functions
    fingerprints: dict[str, set[int]] = {}
    for func in catalog:
        key = func_key(func)
        fingerprints[key] = compute_fingerprint(func, k=k, window=window)

    seen_pairs: set[tuple[str, str]] = set()
    results: list[dict[str, Any]] = []

    for i in range(len(catalog)):
        for j in range(i + 1, len(catalog)):
            fa = catalog[i]
            fb = catalog[j]

            if not should_compare(fa, fb):
                continue
            if should_prefilter_pair(fa, fb):
                continue

            key_a = func_key(fa)
            key_b = func_key(fb)
            pair = (min(key_a, key_b), max(key_a, key_b))
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)

            fp_a = fingerprints[key_a]
            fp_b = fingerprints[key_b]

            if not fp_a or not fp_b:
                continue

            j_score = jaccard(fp_a, fp_b)
            oc_score = overlap_coefficient(fp_a, fp_b)
            final_score = max(j_score, oc_score)

            if final_score < threshold:
                continue

            results.append({
                "func_a": func_ref(fa),
                "func_b": func_ref(fb),
                "scores": {
                    "jaccard": round(j_score, 4),
                    "overlap": round(oc_score, 4),
                },
                "final_score": round(final_score, 4),
                "strategy": "winnowing",
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
            "Winnowing fingerprint detector for partial clone detection. "
            "Implements the Moss/Winnowing algorithm (Schleimer et al., SIGMOD 2003)."
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
        default=0.4,
        help="Minimum similarity score to report (default: 0.4)",
    )
    parser.add_argument(
        "--k",
        type=int,
        default=5,
        help="k-gram size (default: 5)",
    )
    parser.add_argument(
        "--window",
        type=int,
        default=4,
        help="Winnowing window size (default: 4). Guarantees detection of shared "
             "substrings >= k+window-1 tokens.",
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

    results = detect_winnowing_duplicates(
        catalog,
        threshold=args.threshold,
        k=args.k,
        window=args.window,
    )

    output_json = json.dumps(results, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json + "\n")
        print(
            f"Found {len(results)} winnowing clone pair(s), written to {args.output}",
            file=sys.stderr,
        )
    else:
        print(output_json)
        print(
            f"Found {len(results)} winnowing clone pair(s)",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
