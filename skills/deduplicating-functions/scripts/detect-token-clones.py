#!/usr/bin/env python3
from __future__ import annotations
# ABOUTME: Token-based clone detection for Type 1 (exact) and Type 2 (renamed) clones.
# Hashes raw and normalized token sequences to find identical or structurally identical functions.
# Input: enriched catalog JSON with optional token_sequence arrays per function.
# Output: JSON array of candidate clone pairs with scores.

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from lib.common import KEYWORDS, func_key, func_ref, should_compare, tokenize_to_typed as tokenize_code
from lib.prefilter import should_prefilter_pair


# ---------------------------------------------------------------------------
# Hashing helpers
# ---------------------------------------------------------------------------

def hash_sequence(seq: list[str]) -> int:
    """Fast non-crypto hash of a token sequence for bucketing."""
    return hash(tuple(seq))


def normalize_ast_tokens(token_sequence: list[dict[str, str]]) -> list[str]:
    """Normalize an AST-provided token_sequence for Type 2 detection.

    Replaces identifiers with _ID, string literals with _STR, number literals
    with _NUM. Preserves keywords, operators, punctuation verbatim.

    token_sequence entries are expected to have at minimum a "type" and "value"
    field.  We also accept bare strings (treated as raw values needing
    classification).
    """
    normalized: list[str] = []
    for tok in token_sequence:
        if isinstance(tok, str):
            # Bare string — classify on the fly
            if tok in KEYWORDS:
                normalized.append(tok)
            else:
                normalized.append("_ID")
            continue

        tok_type = tok.get("type", "").lower()
        tok_value = tok.get("value", "")

        if tok_type in ("identifier", "name", "id"):
            normalized.append("_ID")
        elif tok_type in ("string", "stringliteral", "str"):
            normalized.append("_STR")
        elif tok_type in ("number", "numberliteral", "num", "numeric", "int", "float"):
            normalized.append("_NUM")
        elif tok_type in ("keyword",):
            normalized.append(tok_value)
        else:
            # Operators, punctuation, etc. — keep as-is
            normalized.append(tok_value)
    return normalized


def raw_token_values(token_sequence: list[dict[str, str] | str]) -> list[str]:
    """Extract raw string values from a token_sequence."""
    result: list[str] = []
    for tok in token_sequence:
        if isinstance(tok, str):
            result.append(tok)
        else:
            result.append(tok.get("value", str(tok)))
    return result


def normalize_simple_tokens(tokens: list[dict[str, str]]) -> list[str]:
    """Normalize tokens produced by our simple tokenizer for Type 2 detection."""
    normalized: list[str] = []
    for tok in tokens:
        tok_type = tok["type"]
        if tok_type == "identifier":
            normalized.append("_ID")
        elif tok_type == "string":
            normalized.append("_STR")
        elif tok_type == "number":
            normalized.append("_NUM")
        else:
            normalized.append(tok["value"])
    return normalized


# ---------------------------------------------------------------------------
# Core detection
# ---------------------------------------------------------------------------

def build_pair_result(
    fa: dict[str, Any],
    fb: dict[str, Any],
    clone_type: int,
    seq_length: int,
) -> dict[str, Any]:
    """Build a candidate pair result dict."""
    final_score = 1.0 if clone_type == 1 else 0.9
    return {
        "func_a": func_ref(fa),
        "func_b": func_ref(fb),
        "scores": {
            "token_hash_match": True,
            "clone_type": clone_type,
            "sequence_length": seq_length,
        },
        "final_score": final_score,
        "strategy": "token_clone",
    }


def detect_clones(
    catalog: list[dict[str, Any]],
    min_tokens: int = 10,
) -> list[dict[str, Any]]:
    """Run Type 1 and Type 2 clone detection on the catalog.

    Returns a deduplicated list of candidate pairs.
    """
    # We track two hash maps: one for raw (Type 1), one for normalized (Type 2).
    # Each maps hash -> list of (func_entry, sequence_length).
    raw_groups: dict[str, list[tuple[dict[str, Any], int]]] = defaultdict(list)
    norm_groups: dict[str, list[tuple[dict[str, Any], int]]] = defaultdict(list)

    for func in catalog:
        token_seq = func.get("token_sequence")

        if token_seq and isinstance(token_seq, list) and len(token_seq) > 0:
            # --- AST-provided token_sequence ---
            raw_vals = raw_token_values(token_seq)
            if len(raw_vals) < min_tokens:
                continue

            raw_hash = hash_sequence(raw_vals)
            raw_groups[raw_hash].append((func, len(raw_vals)))

            norm_vals = normalize_ast_tokens(token_seq)
            norm_hash = hash_sequence(norm_vals)
            norm_groups[norm_hash].append((func, len(norm_vals)))

        elif func.get("context"):
            # --- Fallback: tokenize the context field ---
            tokens = tokenize_code(func["context"])
            if len(tokens) < min_tokens:
                continue

            raw_vals = [t["value"] for t in tokens]
            raw_hash = hash_sequence(raw_vals)
            raw_groups[raw_hash].append((func, len(raw_vals)))

            norm_vals = normalize_simple_tokens(tokens)
            norm_hash = hash_sequence(norm_vals)
            norm_groups[norm_hash].append((func, len(norm_vals)))

        # Functions with neither token_sequence nor context are skipped.

    # Collect results, avoiding duplicate pairs.
    seen_pairs: set[tuple[str, str]] = set()
    results: list[dict[str, Any]] = []

    def add_pairs(
        groups: dict[str, list[tuple[dict[str, Any], int]]],
        clone_type: int,
    ) -> None:
        for _hash, members in groups.items():
            if len(members) < 2:
                continue
            for i in range(len(members)):
                for j in range(i + 1, len(members)):
                    fa, len_a = members[i]
                    fb, len_b = members[j]
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
                    seq_len = max(len_a, len_b)
                    results.append(build_pair_result(fa, fb, clone_type, seq_len))

    # Type 1 first (higher confidence), then Type 2.
    # Type 1 pairs won't be duplicated in Type 2 because of seen_pairs.
    add_pairs(raw_groups, clone_type=1)
    add_pairs(norm_groups, clone_type=2)

    # Sort by score descending, then by func_a file/line for deterministic output.
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
        description="Token-based clone detection (Type 1 exact and Type 2 renamed clones)."
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
        "--min-tokens",
        type=int,
        default=10,
        help="Minimum token sequence length to consider (default: 10)",
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

    # Detect clones
    results = detect_clones(catalog, min_tokens=args.min_tokens)

    # Output
    output_json = json.dumps(results, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json + "\n")
        print(
            f"Found {len(results)} token clone pair(s), written to {args.output}",
            file=sys.stderr,
        )
    else:
        print(output_json)
        print(
            f"Found {len(results)} token clone pair(s)",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
