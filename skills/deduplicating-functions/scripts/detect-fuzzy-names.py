#!/usr/bin/env python3
from __future__ import annotations
# ABOUTME: Detects potential duplicate functions by fuzzy matching on function names.
# Uses Levenshtein distance, token decomposition, synonym matching, and abbreviation
# expansion to score pairs of functions from a catalog JSON file.

import argparse
import json
import sys
from itertools import combinations
from pathlib import Path
from typing import Any

from rapidfuzz import fuzz

sys.path.insert(0, str(Path(__file__).parent))

from lib.common import jaccard, should_compare, tokenize
from lib.prefilter import should_prefilter_pair

# ---------------------------------------------------------------------------
# Synonym groups: functions whose name tokens fall into the same group get a
# boost because they likely express the same intent with different vocabulary.
# ---------------------------------------------------------------------------
SYNONYM_GROUPS: list[set[str]] = [
    # get / fetch / retrieve
    {"get", "fetch", "retrieve", "load", "read"},
    # search / lookup / find / query
    {"search", "lookup", "find", "query", "seek", "locate"},
    # set / update / modify
    {"set", "update", "modify", "change", "mutate", "write", "put", "patch"},
    # create / make / build
    {"create", "make", "build", "construct", "generate", "produce", "init", "new"},
    # delete / remove / destroy
    {"delete", "remove", "destroy", "drop", "clear", "purge", "erase", "wipe"},
    # validate / check / verify
    {"validate", "check", "verify", "assert", "ensure", "test", "confirm"},
    # format / render / display / show
    {"format", "render", "display", "show", "present", "stringify", "print"},
    # parse / decode / deserialize
    {"parse", "decode", "deserialize", "extract", "unwrap", "unpack"},
    # send / emit / dispatch
    {"send", "emit", "dispatch", "publish", "broadcast", "notify", "post"},
    # handle / process / execute / run
    {"handle", "process", "on", "execute", "run", "perform", "invoke", "call"},
    # convert / transform / map
    {"convert", "transform", "map", "translate", "serialize", "encode"},
    # boolean predicates
    {"is", "has", "can", "should", "contains", "exists"},
    # sort / order / arrange
    {"sort", "order", "arrange", "rank", "organize", "prioritize"},
    # list / array / collection
    {"list", "array", "collection", "items", "entries", "elements", "records"},
    # open / start / begin / initialize
    {"open", "start", "begin", "initialize", "launch", "boot", "activate"},
    # close / stop / end / finish / terminate
    {"close", "stop", "end", "finish", "terminate", "shutdown", "complete", "finalize"},
    # calculate / compute / evaluate
    {"calculate", "compute", "evaluate", "measure", "count", "sum", "total", "aggregate"},
    # filter / exclude / reject
    {"filter", "exclude", "reject", "prune", "omit", "skip"},
    # compare / diff / match
    {"compare", "diff", "match", "equals", "contrast"},
    # error / exception / fault
    {"error", "exception", "fault", "failure", "problem", "issue"},
    # log / trace / debug
    {"log", "trace", "debug", "record", "audit", "track"},
]

# Pre-compute a lookup: token -> group index (for O(1) synonym checks)
_TOKEN_TO_GROUP: dict[str, int] = {}
for _idx, _group in enumerate(SYNONYM_GROUPS):
    for _tok in _group:
        _TOKEN_TO_GROUP[_tok] = _idx

# ---------------------------------------------------------------------------
# Abbreviation map: short form -> expanded form
# ---------------------------------------------------------------------------
ABBREVIATIONS: dict[str, str] = {
    # original entries
    "fmt": "format",
    "str": "string",
    "num": "number",
    "val": "value",
    "msg": "message",
    "err": "error",
    "req": "request",
    "res": "response",
    "cfg": "config",
    "ctx": "context",
    "btn": "button",
    "el": "element",
    "evt": "event",
    "cb": "callback",
    "fn": "function",
    "arg": "argument",
    "param": "parameter",
    "idx": "index",
    "len": "length",
    "tmp": "temp",
    "prev": "previous",
    "cur": "current",
    "src": "source",
    "dst": "destination",
    "opt": "option",
    # expanded entries
    "auth": "authenticate",
    "db": "database",
    "env": "environment",
    "repo": "repository",
    "impl": "implementation",
    "init": "initialize",
    "conf": "configuration",
    "conn": "connection",
    "sess": "session",
    "proc": "process",
    "mgr": "manager",
    "svc": "service",
    "ctrl": "controller",
    "gen": "generate",
    "calc": "calculate",
    "exec": "execute",
    "doc": "document",
    "desc": "description",
    "info": "information",
    "ref": "reference",
    "spec": "specification",
    "attr": "attribute",
    "prop": "property",
    "obj": "object",
    "arr": "array",
    "dict": "dictionary",
    "tbl": "table",
    "col": "column",
    "fld": "field",
    "rec": "record",
    "usr": "user",
    "grp": "group",
    "org": "organization",
    "app": "application",
    "lib": "library",
    "pkg": "package",
    "mod": "module",
    "dir": "directory",
    "cmd": "command",
    "op": "operation",
    "tx": "transaction",
    "async": "asynchronous",
    "sync": "synchronous",
    "seq": "sequence",
    "max": "maximum",
    "min": "minimum",
    "avg": "average",
    "agg": "aggregate",
    "acc": "accumulate",
    "iter": "iterate",
    "delim": "delimiter",
    "sep": "separator",
    "buf": "buffer",
    "alloc": "allocate",
    "dup": "duplicate",
    "orig": "original",
    "def": "default",
    "pref": "preference",
    "cmp": "compare",
    "eq": "equals",
    "util": "utility",
    "hlp": "helper",
    "sched": "schedule",
    "ns": "namespace",
    "ver": "version",
    "ts": "timestamp",
}

# Alias used by tests and external code
ABBREVIATION_MAP = ABBREVIATIONS


def expand_abbreviations(tokens: list[str]) -> list[str]:
    """Expand known abbreviations in a token list."""
    return [ABBREVIATIONS.get(t, t) for t in tokens]


# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------
def levenshtein_score(name_a: str, name_b: str) -> float:
    """Normalized Levenshtein similarity (0-1) via rapidfuzz."""
    return fuzz.ratio(name_a, name_b) / 100.0


def token_jaccard_score(tokens_a: list[str], tokens_b: list[str]) -> float:
    """Jaccard similarity on raw token sets."""
    return jaccard(set(tokens_a), set(tokens_b))


def synonym_boost(tokens_a: list[str], tokens_b: list[str]) -> float:
    """Compute synonym boost (0-0.3).

    For each token in A that is NOT in B, check if any token in B is a synonym.
    The boost is proportional to how many such synonym matches exist relative
    to the total unique tokens across both lists.
    """
    set_a = set(tokens_a)
    set_b = set(tokens_b)
    # Tokens unique to each side
    only_a = set_a - set_b
    only_b = set_b - set_a

    if not only_a or not only_b:
        return 0.0

    synonym_matches = 0
    matched_b: set[str] = set()

    for ta in only_a:
        ga = _TOKEN_TO_GROUP.get(ta)
        if ga is None:
            continue
        for tb in only_b:
            if tb in matched_b:
                continue
            gb = _TOKEN_TO_GROUP.get(tb)
            if ga == gb:
                synonym_matches += 1
                matched_b.add(tb)
                break

    # Normalize: max possible matches is min(|only_a|, |only_b|)
    max_possible = min(len(only_a), len(only_b))
    if max_possible == 0:
        return 0.0

    # Scale to 0-0.3 range
    return 0.3 * (synonym_matches / max_possible)


def abbreviation_boost(
    tokens_a: list[str],
    tokens_b: list[str],
    expanded_a: list[str],
    expanded_b: list[str],
) -> float:
    """Compute abbreviation boost (0-0.2).

    Measures how much expanding abbreviations improves the token overlap.
    If expansion doesn't help (tokens were already the same or expansion
    doesn't change anything), boost is 0.
    """
    raw_jaccard = jaccard(set(tokens_a), set(tokens_b))
    expanded_jaccard = jaccard(set(expanded_a), set(expanded_b))

    improvement = expanded_jaccard - raw_jaccard
    if improvement <= 0:
        return 0.0

    # Scale to 0-0.2 range; clamp at 0.2
    return min(0.2, 0.2 * (improvement / 0.5))


def compute_final_score(scores: dict[str, float]) -> float:
    """Weighted average of all component scores."""
    return (
        0.3 * scores["levenshtein"]
        + 0.4 * scores["token_jaccard"]
        + 0.2 * scores["synonym_boost"]
        + 0.1 * scores["abbreviation_boost"]
    )


# ---------------------------------------------------------------------------
# Main detection
# ---------------------------------------------------------------------------
def detect_fuzzy_duplicates(
    catalog: list[dict[str, Any]], threshold: float = 0.5
) -> list[dict[str, Any]]:
    """Find candidate duplicate pairs by fuzzy name matching."""
    results: list[dict[str, Any]] = []

    # Pre-compute tokens and expansions for every entry
    precomputed: list[tuple[list[str], list[str]]] = []
    for entry in catalog:
        name = entry.get("name", "")
        tokens = tokenize(name)
        expanded = expand_abbreviations(tokens)
        precomputed.append((tokens, expanded))

    for (i, a), (j, b) in combinations(enumerate(catalog), 2):
        if not should_compare(a, b):
            continue
        if should_prefilter_pair(a, b):
            continue

        name_a = a.get("name", "")
        name_b = b.get("name", "")

        tokens_a, expanded_a = precomputed[i]
        tokens_b, expanded_b = precomputed[j]

        scores = {
            "levenshtein": levenshtein_score(name_a, name_b),
            "token_jaccard": token_jaccard_score(tokens_a, tokens_b),
            "synonym_boost": synonym_boost(tokens_a, tokens_b),
            "abbreviation_boost": abbreviation_boost(
                tokens_a, tokens_b, expanded_a, expanded_b
            ),
        }

        final = compute_final_score(scores)

        if final >= threshold:
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
                    "strategy": "fuzzy_name",
                }
            )

    # Sort by final_score descending for easy review
    results.sort(key=lambda r: r["final_score"], reverse=True)
    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Detect potential duplicate functions via fuzzy name matching."
    )
    parser.add_argument(
        "catalog",
        help="Path to catalog JSON file (array of function entries)",
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
        default=0.5,
        help="Minimum final_score to include a pair (default: 0.5)",
    )

    args = parser.parse_args()

    # Load catalog
    try:
        with open(args.catalog, "r") as f:
            catalog = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading catalog: {e}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(catalog, list):
        print("Error: catalog must be a JSON array", file=sys.stderr)
        sys.exit(1)

    results = detect_fuzzy_duplicates(catalog, threshold=args.threshold)

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
