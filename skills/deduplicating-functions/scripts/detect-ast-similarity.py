#!/usr/bin/env python3
from __future__ import annotations
# ABOUTME: AST structural similarity detection for Type 3 near-miss clones.
# Uses n-gram Jaccard similarity and longest common subsequence (LCS) on token
# sequences to find functions that share substantial structure but differ in
# some statements or expressions.
# Input: enriched catalog JSON with ast_fingerprint and token_sequence fields.
# Output: JSON array of candidate pairs with detailed similarity scores.

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from lib.common import (
    func_key,
    func_ref,
    jaccard,
    should_compare,
    tokenize_to_strings as tokenize_code,
)
from lib.prefilter import should_prefilter_pair


# ---------------------------------------------------------------------------
# Token sequence extraction
# ---------------------------------------------------------------------------

def get_token_values(func: dict[str, Any]) -> list[str] | None:
    """Extract a flat list of token value strings for a function entry.

    Prefers the AST-provided `token_sequence`; falls back to tokenizing the
    `context` field.  Returns None if neither is available.
    """
    token_seq = func.get("token_sequence")
    if token_seq and isinstance(token_seq, list) and len(token_seq) > 0:
        result: list[str] = []
        for tok in token_seq:
            if isinstance(tok, str):
                result.append(tok)
            elif isinstance(tok, dict):
                result.append(tok.get("value", str(tok)))
            else:
                result.append(str(tok))
        return result

    context = func.get("context")
    if context and isinstance(context, str):
        tokens = tokenize_code(context)
        return tokens if tokens else None

    return None


# ---------------------------------------------------------------------------
# N-gram and similarity helpers
# ---------------------------------------------------------------------------

def ngrams(seq: list[str], n: int) -> set[tuple[str, ...]]:
    """Generate the set of n-grams from a sequence."""
    if len(seq) < n:
        return set()
    return {tuple(seq[i:i + n]) for i in range(len(seq) - n + 1)}


def lcs_length(seq_a: list[str], seq_b: list[str]) -> int:
    """Compute length of the longest common subsequence using O(min(m,n)) space.

    Uses the standard two-row DP approach for memory efficiency.
    """
    # Ensure seq_a is the shorter one for space optimization
    if len(seq_a) > len(seq_b):
        seq_a, seq_b = seq_b, seq_a

    m = len(seq_a)
    n = len(seq_b)

    if m == 0:
        return 0

    # Two rows: previous and current
    prev: list[int] = [0] * (m + 1)
    curr: list[int] = [0] * (m + 1)

    for j in range(1, n + 1):
        for i in range(1, m + 1):
            if seq_a[i - 1] == seq_b[j - 1]:
                curr[i] = prev[i - 1] + 1
            else:
                curr[i] = max(prev[i], curr[i - 1])
        prev, curr = curr, [0] * (m + 1)

    return prev[m]


def lcs_similarity(seq_a: list[str], seq_b: list[str]) -> float:
    """Normalized LCS similarity: 2 * LCS / (len_a + len_b)."""
    total = len(seq_a) + len(seq_b)
    if total == 0:
        return 0.0
    return 2 * lcs_length(seq_a, seq_b) / total


# ---------------------------------------------------------------------------
# Core detection
# ---------------------------------------------------------------------------

def detect_ast_similarity(
    catalog: list[dict[str, Any]],
    threshold: float = 0.6,
    min_tokens: int = 10,
    ngram_threshold: float = 0.4,
) -> list[dict[str, Any]]:
    """Detect Type 3 near-miss clones via n-gram screening + LCS verification.

    Algorithm:
    1. Group by ast_fingerprint for exact structural matches (fast path).
    2. For all pairs: compute n-gram (n=3, n=5) Jaccard similarity as a screen.
    3. For pairs passing the screen (avg n-gram > 0.4): compute LCS similarity.
    4. Combine scores and keep pairs above the threshold.
    """
    # ---------------------------------------------------------------
    # Step 0: Prepare — extract token sequences and filter short ones
    # ---------------------------------------------------------------
    prepared: list[tuple[dict[str, Any], list[str]]] = []
    for func in catalog:
        tokens = get_token_values(func)
        if tokens is None or len(tokens) < min_tokens:
            continue
        prepared.append((func, tokens))

    results: list[dict[str, Any]] = []
    seen_pairs: set[tuple[str, str]] = set()

    def pair_id(fa: dict[str, Any], fb: dict[str, Any]) -> tuple[str, str]:
        ka, kb = func_key(fa), func_key(fb)
        return (min(ka, kb), max(ka, kb))

    # ---------------------------------------------------------------
    # Step 1: Fingerprint grouping (fast path)
    # ---------------------------------------------------------------
    fp_groups: dict[str, list[tuple[dict[str, Any], list[str]]]] = defaultdict(list)
    for func, tokens in prepared:
        fp = func.get("ast_fingerprint")
        if fp:
            fp_groups[fp].append((func, tokens))

    for _fp, members in fp_groups.items():
        if len(members) < 2:
            continue
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                fa, tok_a = members[i]
                fb, tok_b = members[j]
                if not should_compare(fa, fb):
                    continue
                pid = pair_id(fa, fb)
                if pid in seen_pairs:
                    continue
                if should_prefilter_pair(fa, fb):
                    continue
                seen_pairs.add(pid)

                # Fingerprint match — skip expensive LCS/n-gram computation
                results.append({
                    "func_a": func_ref(fa),
                    "func_b": func_ref(fb),
                    "scores": {"fingerprint_match": True},
                    "final_score": 1.0,
                    "strategy": "ast_similarity",
                })

    # ---------------------------------------------------------------
    # Step 2: Pre-compute n-gram sets for all functions
    # ---------------------------------------------------------------
    ngram_cache: list[tuple[dict[str, Any], list[str], set[tuple[str, ...]], set[tuple[str, ...]]]] = []
    for func, tokens in prepared:
        ng3 = ngrams(tokens, 3)
        ng5 = ngrams(tokens, 5)
        ngram_cache.append((func, tokens, ng3, ng5))

    # ---------------------------------------------------------------
    # Step 3: Pairwise n-gram screening + LCS for passing pairs
    # ---------------------------------------------------------------
    n = len(ngram_cache)

    for i in range(n):
        fa, tok_a, ng3_a, ng5_a = ngram_cache[i]
        for j in range(i + 1, n):
            fb, tok_b, ng3_b, ng5_b = ngram_cache[j]

            if not should_compare(fa, fb):
                continue
            pid = pair_id(fa, fb)
            if pid in seen_pairs:
                continue
            if should_prefilter_pair(fa, fb):
                continue

            # Quick n-gram screen
            ng3_score = jaccard(ng3_a, ng3_b)
            ng5_score = jaccard(ng5_a, ng5_b)
            avg_ngram = (ng3_score + ng5_score) / 2

            if avg_ngram < ngram_threshold:
                continue

            # Passes screen — compute LCS
            lcs_sim = lcs_similarity(tok_a, tok_b)
            combined = 0.3 * ng3_score + 0.3 * ng5_score + 0.4 * lcs_sim

            if combined < threshold:
                continue

            seen_pairs.add(pid)
            results.append({
                "func_a": func_ref(fa),
                "func_b": func_ref(fb),
                "scores": {
                    "fingerprint_match": False,
                    "ngram_3_jaccard": round(ng3_score, 4),
                    "ngram_5_jaccard": round(ng5_score, 4),
                    "lcs_similarity": round(lcs_sim, 4),
                },
                "final_score": round(combined, 4),
                "strategy": "ast_similarity",
            })

    # Sort: highest score first, then by file/line for determinism
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
        description="AST structural similarity detection (Type 3 near-miss clones)."
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
        default=0.6,
        help="Minimum final_score to include a pair (default: 0.6)",
    )
    parser.add_argument(
        "--min-tokens",
        type=int,
        default=10,
        help="Minimum token sequence length to consider (default: 10)",
    )
    parser.add_argument(
        "--ngram-threshold",
        type=float,
        default=0.4,
        help="N-gram Jaccard pre-screening threshold; pairs below skip LCS (default: 0.4)",
    )

    args = parser.parse_args()

    # Load catalog
    try:
        with open(args.catalog, "r", encoding="utf-8") as f:
            catalog = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Error loading catalog: {exc}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(catalog, list):
        print("Error: catalog must be a JSON array", file=sys.stderr)
        sys.exit(1)

    # Detect similarity
    results = detect_ast_similarity(
        catalog,
        threshold=args.threshold,
        min_tokens=args.min_tokens,
        ngram_threshold=args.ngram_threshold,
    )

    # Output
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
