#!/usr/bin/env python3
from __future__ import annotations
# ABOUTME: Detects potential duplicate functions by comparing function signatures.
# Analyzes arity, parameter type patterns, return types, and parameter name
# similarity to find functions that share the same shape even if named differently.

import argparse
import json
import re
import sys
from itertools import combinations
from pathlib import Path
from typing import Any

from rapidfuzz import fuzz

sys.path.insert(0, str(Path(__file__).parent))

from lib.common import jaccard, should_compare, tokenize
from lib.prefilter import should_prefilter_pair

# ---------------------------------------------------------------------------
# Type normalization map: collapse complex/generic types to base forms
# ---------------------------------------------------------------------------
TYPE_NORMALIZATIONS: dict[str, str] = {
    # JavaScript/TypeScript generics
    "array": "array",
    "promise": "promise",
    "observable": "observable",
    "readonly": "",
    "partial": "",
    # Python typing
    "optional": "",
    "union": "",
    "list": "array",
    "dict": "object",
    "tuple": "array",
    "set": "array",
    "frozenset": "array",
    "sequence": "array",
    "mapping": "object",
    "iterable": "array",
    "iterator": "array",
    "generator": "iterator",
    "callable": "function",
    "coroutine": "promise",
    "awaitable": "promise",
    # Common equivalences
    "string": "string",
    "str": "string",
    "int": "number",
    "float": "number",
    "double": "number",
    "integer": "number",
    "boolean": "boolean",
    "bool": "boolean",
    "void": "void",
    "none": "void",
    "null": "void",
    "undefined": "void",
    "any": "any",
    "object": "object",
    "record": "object",
    "map": "object",
}


# ---------------------------------------------------------------------------
# Type normalization
# ---------------------------------------------------------------------------
def normalize_type(raw: str) -> str:
    """Normalize a type string to a canonical base form.

    Examples:
        "Array<string>"    -> "array"
        "Promise<number>"  -> "promise"
        "Optional[int]"    -> "number"
        "string | null"    -> "string"
        "List[Dict[str, Any]]" -> "array"
    """
    if not raw:
        return "any"

    # Lowercase and strip whitespace
    t = raw.strip().lower()

    # Strip generic parameters:  Array<...> -> Array,  List[...] -> List
    t = re.sub(r"[<\[].*?[>\]]", "", t)

    # Strip union components to keep the first non-null/none/undefined type
    if "|" in t:
        parts = [p.strip() for p in t.split("|")]
        parts = [p for p in parts if p not in ("null", "none", "undefined", "void", "")]
        t = parts[0] if parts else "void"

    # Strip remaining non-alpha chars
    t = re.sub(r"[^a-z]", "", t)

    return TYPE_NORMALIZATIONS.get(t, t) if t else "any"


# ---------------------------------------------------------------------------
# Parameter extraction helpers
# ---------------------------------------------------------------------------
def extract_params(entry: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract parameter list from a catalog entry, handling various formats.

    Supports:
      - entry["params"] as list of {"name": ..., "type": ..., "optional": ...}
      - entry["params"] as list of strings (names only)
      - Derives param_count if not present
    """
    params = entry.get("params", [])
    if not isinstance(params, list):
        return []

    result: list[dict[str, Any]] = []
    for p in params:
        if isinstance(p, dict):
            result.append(
                {
                    "name": p.get("name", ""),
                    "type": p.get("type", ""),
                    "optional": p.get("optional", False),
                }
            )
        elif isinstance(p, str):
            result.append({"name": p, "type": "", "optional": False})
    return result


def get_param_count(entry: dict[str, Any]) -> tuple[int, int]:
    """Return (required_count, optional_count) for a function entry."""
    # Use explicit param_count if present
    if "param_count" in entry and isinstance(entry["param_count"], int):
        params = extract_params(entry)
        optional = sum(1 for p in params if p.get("optional", False))
        required = entry["param_count"] - optional
        return (max(0, required), optional)

    params = extract_params(entry)
    required = sum(1 for p in params if not p.get("optional", False))
    optional = sum(1 for p in params if p.get("optional", False))
    return (required, optional)


def get_return_type(entry: dict[str, Any]) -> str:
    """Extract and normalize the return type."""
    rt = entry.get("return_type", "")
    if not rt or not isinstance(rt, str):
        return ""
    return normalize_type(rt)


# ---------------------------------------------------------------------------
# Scoring components
# ---------------------------------------------------------------------------
def arity_match_score(entry_a: dict[str, Any], entry_b: dict[str, Any]) -> float:
    """Score based on parameter count matching.

    - 1.0 if exact same required+optional counts
    - 0.5 if total differs by exactly 1 (likely an optional param difference)
    - 0.0 otherwise
    """
    req_a, opt_a = get_param_count(entry_a)
    req_b, opt_b = get_param_count(entry_b)

    total_a = req_a + opt_a
    total_b = req_b + opt_b

    if req_a == req_b and opt_a == opt_b:
        return 1.0

    # Off by one total — could be an optional param difference
    if abs(total_a - total_b) == 1:
        return 0.5

    # Same total but different required/optional split
    if total_a == total_b:
        return 0.75

    return 0.0


def type_pattern_score(entry_a: dict[str, Any], entry_b: dict[str, Any]) -> float:
    """Score based on parameter type sequence alignment.

    Compares normalized types positionally. Uses a simple alignment:
    for each position, score 1.0 for exact match, 0.5 if one is "any",
    0.0 otherwise. Average across positions.
    """
    params_a = extract_params(entry_a)
    params_b = extract_params(entry_b)

    types_a = [normalize_type(p.get("type", "")) for p in params_a]
    types_b = [normalize_type(p.get("type", "")) for p in params_b]

    # If both have no type info, we can't compare — return neutral score
    if all(t == "any" for t in types_a) and all(t == "any" for t in types_b):
        # No type info available — this is NOT evidence of a match
        return 0.4

    # If one is empty and the other isn't, score based on length difference
    if not types_a or not types_b:
        if not types_a and not types_b:
            return 1.0
        return 0.0

    # Align by position up to the shorter list
    max_len = max(len(types_a), len(types_b))
    if max_len == 0:
        return 1.0

    score_sum = 0.0
    for i in range(max_len):
        ta = types_a[i] if i < len(types_a) else ""
        tb = types_b[i] if i < len(types_b) else ""

        if ta == tb:
            score_sum += 1.0
        elif ta == "any" or tb == "any":
            # One side has no type info — partial credit
            score_sum += 0.5
        elif ta == "" or tb == "":
            # Missing type on one side — small credit
            score_sum += 0.3
        else:
            score_sum += 0.0

    return score_sum / max_len


def return_type_match_score(entry_a: dict[str, Any], entry_b: dict[str, Any]) -> float:
    """Score based on return type comparison.

    - 1.0 if same normalized return type
    - 0.5 if one is "any" or both are missing
    - 0.0 if different
    """
    rt_a = get_return_type(entry_a)
    rt_b = get_return_type(entry_b)

    # Both missing — no signal, give moderate score
    if not rt_a and not rt_b:
        return 0.5

    # One missing
    if not rt_a or not rt_b:
        return 0.3

    if rt_a == rt_b:
        return 1.0

    # One is "any" — compatible
    if rt_a == "any" or rt_b == "any":
        return 0.5

    return 0.0


def param_name_similarity_score(
    entry_a: dict[str, Any], entry_b: dict[str, Any]
) -> float:
    """Score based on parameter name token overlap.

    For each positional pair of parameters, compute Jaccard similarity on
    their name tokens. Average across all positional pairs.
    """
    params_a = extract_params(entry_a)
    params_b = extract_params(entry_b)

    if not params_a and not params_b:
        return 1.0
    if not params_a or not params_b:
        return 0.0

    max_len = max(len(params_a), len(params_b))
    score_sum = 0.0

    for i in range(max_len):
        name_a = params_a[i]["name"] if i < len(params_a) else ""
        name_b = params_b[i]["name"] if i < len(params_b) else ""

        if not name_a and not name_b:
            score_sum += 0.5
            continue
        if not name_a or not name_b:
            score_sum += 0.0
            continue

        tokens_a = set(tokenize(name_a))
        tokens_b = set(tokenize(name_b))
        score_sum += jaccard(tokens_a, tokens_b)

    return score_sum / max_len


def compute_final_score(scores: dict[str, float]) -> float:
    """Weighted average of all component scores, penalized for missing type info.

    When neither function has type annotations, the signature "match" is
    vacuous — both have shape () -> unknown.  Apply a penalty so these
    pairs don't drown out real signal.
    """
    raw = (
        0.3 * scores["arity_match"]
        + 0.3 * scores["type_pattern"]
        + 0.2 * scores["return_type_match"]
        + 0.2 * scores["param_name_similarity"]
    )

    # Penalize vacuous matches: when all type-dependent scores used
    # fallback/neutral values (0.5), the match is uninformative.
    type_info_score = scores.get("type_pattern", 0.5)
    return_info_score = scores.get("return_type_match", 0.5)

    # Both type_pattern and return_type at their "unknown" defaults (0.3-0.5)
    # means no type information was available — apply penalty
    if type_info_score <= 0.5 and return_info_score <= 0.5:
        # Scale down: a fully untyped match gets at most 50% of raw score
        raw *= 0.5

    return raw


# ---------------------------------------------------------------------------
# Main detection
# ---------------------------------------------------------------------------
def detect_signature_duplicates(
    catalog: list[dict[str, Any]], threshold: float = 0.7
) -> list[dict[str, Any]]:
    """Find candidate duplicate pairs by signature matching."""
    results: list[dict[str, Any]] = []

    for (i, a), (j, b) in combinations(enumerate(catalog), 2):
        if not should_compare(a, b):
            continue
        if should_prefilter_pair(a, b):
            continue

        scores = {
            "arity_match": arity_match_score(a, b),
            "type_pattern": type_pattern_score(a, b),
            "return_type_match": return_type_match_score(a, b),
            "param_name_similarity": param_name_similarity_score(a, b),
        }

        final = compute_final_score(scores)

        if final >= threshold:
            name_a = a.get("name", "")
            name_b = b.get("name", "")
            results.append(
                {
                    "func_a": {
                        "name": name_a,
                        "file": a.get("file", ""),
                        "line": a.get("line", 0),
                    },
                    "func_b": {
                        "name": name_b,
                        "file": b.get("file", ""),
                        "line": b.get("line", 0),
                    },
                    "scores": {k: round(v, 4) for k, v in scores.items()},
                    "final_score": round(final, 4),
                    "strategy": "signature_match",
                }
            )

    results.sort(key=lambda r: r["final_score"], reverse=True)
    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Detect potential duplicate functions via signature matching."
    )
    parser.add_argument(
        "catalog",
        help="Path to enriched catalog JSON file (array of function entries with params/return_type)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output file path (default: stdout)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.7,
        help="Minimum final_score to include a pair (default: 0.7)",
    )

    args = parser.parse_args()

    try:
        with open(args.catalog, "r") as f:
            catalog = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading catalog: {e}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(catalog, list):
        print("Error: catalog must be a JSON array", file=sys.stderr)
        sys.exit(1)

    results = detect_signature_duplicates(catalog, threshold=args.threshold)

    output_json = json.dumps(results, indent=2)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output_json)
            f.write("\n")
        print(
            f"Wrote {len(results)} candidate pairs to {args.output}",
            file=sys.stderr,
        )
    else:
        print(output_json)


if __name__ == "__main__":
    main()
