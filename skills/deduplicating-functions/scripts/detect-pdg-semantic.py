#!/usr/bin/env python3
from __future__ import annotations
# ABOUTME: PDG-inspired semantic clone detector for Type 4 (behavioral) clones.
# Segments token_sequence into statement blocks, hashes (block_shape, context)
# neighborhood tuples, then compares functions by Jaccard on fingerprint sets.
# Functions that do the same thing with different variable names get similar
# fingerprints because statement shapes match even when identifiers differ.
# Input: enriched catalog JSON with token_sequence field (list of AST node type names).
# Output: JSON array of candidate pairs with pdg_jaccard scores.


import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from lib.common import func_key, func_ref, jaccard, should_compare, stable_hash
from lib.prefilter import should_prefilter_pair


# ---------------------------------------------------------------------------
# Statement boundary tokens — these start a new "statement block"
# ---------------------------------------------------------------------------

STATEMENT_BOUNDARIES: frozenset[str] = frozenset({
    "FunctionDef",
    "AsyncFunctionDef",
    "If",
    "For",
    "While",
    "Try",
    "With",
    "Return",
    "Assign",
    "AugAssign",
    "Expr",
    "Raise",
    "Assert",
    "Delete",
    "Import",
    "ClassDef",
})


# ---------------------------------------------------------------------------
# Block segmentation
# ---------------------------------------------------------------------------

def segment_into_blocks(token_sequence: list[str]) -> list[list[str]]:
    """Segment a flat token_sequence into statement blocks.

    A new block starts whenever a STATEMENT_BOUNDARIES token is encountered.
    The boundary token becomes the first token of the new block.

    Returns a list of non-empty blocks.  An empty token_sequence produces [].
    """
    if not token_sequence:
        return []

    blocks: list[list[str]] = []
    current: list[str] = []

    for tok in token_sequence:
        if tok in STATEMENT_BOUNDARIES:
            if current:
                blocks.append(current)
            current = [tok]
        else:
            current.append(tok)

    if current:
        blocks.append(current)

    return blocks


# ---------------------------------------------------------------------------
# PDG fingerprint
# ---------------------------------------------------------------------------

def compute_pdg_fingerprint(func: dict[str, Any]) -> set[int]:
    """Compute a PDG-inspired fingerprint for a function.

    Algorithm:
    1. Extract token_sequence (list of AST node type name strings).
    2. Segment into statement blocks at boundary tokens.
    3. For each block b[i]:
        - block_type  = b[i][0]  (first token)
        - block_shape = tuple(b[i])  (all tokens)
        - context     = (prev_type, block_type, next_type)
          where prev/next are "_START"/"_END" at boundaries.
    4. Hash (block_shape, context) → int (neighborhood hash).
    5. Return the set of all neighborhood hashes.

    An empty or very short token_sequence yields an empty set.
    """
    token_seq = func.get("token_sequence")
    if not token_seq or not isinstance(token_seq, list):
        return set()

    # Normalise: accept bare strings (AST node names) or typed dicts
    str_tokens: list[str] = []
    for tok in token_seq:
        if isinstance(tok, str):
            str_tokens.append(tok)
        elif isinstance(tok, dict):
            # Prefer "type" (AST node type) over "value"
            str_tokens.append(tok.get("type", tok.get("value", "")))

    blocks = segment_into_blocks(str_tokens)
    if not blocks:
        return set()

    fingerprint: set[int] = set()
    n = len(blocks)

    for i, block in enumerate(blocks):
        block_type = block[0]
        block_shape = tuple(block)

        prev_type = blocks[i - 1][0] if i > 0 else "_START"
        next_type = blocks[i + 1][0] if i < n - 1 else "_END"

        context = (prev_type, block_type, next_type)
        neighborhood_hash = stable_hash((block_shape, context))
        fingerprint.add(neighborhood_hash)

    return fingerprint


# ---------------------------------------------------------------------------
# Core detection
# ---------------------------------------------------------------------------

def detect_pdg_duplicates(
    catalog: list[dict[str, Any]],
    threshold: float = 0.4,
) -> list[dict[str, Any]]:
    """Detect Type 4 semantic clones via PDG neighborhood-hash Jaccard similarity.

    Algorithm:
    1. Compute PDG fingerprint for every function in the catalog.
    2. Skip functions with empty fingerprints.
    3. For each pair passing should_compare + should_prefilter_pair: compute Jaccard.
    4. Emit pairs where Jaccard >= threshold.
    """
    # Build fingerprints, skip empties
    prepared: list[tuple[dict[str, Any], set[int]]] = []
    for func in catalog:
        fp = compute_pdg_fingerprint(func)
        if fp:
            prepared.append((func, fp))

    results: list[dict[str, Any]] = []
    seen_pairs: set[tuple[str, str]] = set()
    n = len(prepared)

    for i in range(n):
        fa, fp_a = prepared[i]
        for j in range(i + 1, n):
            fb, fp_b = prepared[j]

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

            score = jaccard(fp_a, fp_b)
            if score < threshold:
                continue

            results.append({
                "func_a": func_ref(fa),
                "func_b": func_ref(fb),
                "scores": {"pdg_jaccard": round(score, 4)},
                "final_score": round(score, 4),
                "strategy": "pdg_semantic",
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
            "PDG-inspired semantic clone detector (Type 4 clones). "
            "Uses statement-block neighborhood hashes for Jaccard comparison."
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
        help="Minimum Jaccard similarity to include a pair (default: 0.4)",
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

    results = detect_pdg_duplicates(catalog, threshold=args.threshold)

    output_json = json.dumps(results, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json + "\n")
        print(
            f"Found {len(results)} semantic clone pair(s), written to {args.output}",
            file=sys.stderr,
        )
    else:
        print(output_json)
        print(
            f"Found {len(results)} semantic clone pair(s)",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
