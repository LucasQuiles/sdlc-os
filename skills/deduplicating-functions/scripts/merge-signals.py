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
import os
import sqlite3
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterator

_LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib")
if _LIB not in sys.path:
    sys.path.insert(0, _LIB)
import jsonstream  # noqa: E402  (scripts/lib, stdlib-only)
import resource_policy as rpolicy  # noqa: E402


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
            # Actionable = Type 1 exact clones at HIGH confidence with substantial body (>= 15 lines each)
            if conf != "HIGH" or ct != "Type 1 (exact clone)":
                suppressed += 1
                continue
            # Require both functions to have >= 20 body lines (skip trivial wrappers)
            body_a = _body_lines(pair.get("func_a", {}))
            body_b = _body_lines(pair.get("func_b", {}))
            if body_a is not None and body_b is not None and (body_a < 20 or body_b < 20):
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
    catalog_index: dict[tuple, dict] | None = None,
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
        best_per_strategy = _best_per_strategy(signals)
        scored = _score_pair(best_per_strategy, thresholds, min_strats_high, catalog_index)
        if scored is not None:
            merged.append(scored)

    # Sort by composite score descending, then by number of strategies
    merged.sort(key=lambda x: (-x["composite_score"], -x["num_strategies"]))
    return merged


def _best_per_strategy(signals: list[tuple[str, dict]]) -> dict[str, dict]:
    """Highest-scoring result per strategy, keyed in first-seen order."""
    best_per_strategy: dict[str, dict] = {}
    for strategy_name, result in signals:
        strategy = result.get("strategy", strategy_name)
        score = result.get("final_score", 0.0)
        if strategy not in best_per_strategy or score > best_per_strategy[strategy].get("final_score", 0):
            best_per_strategy[strategy] = result
    return best_per_strategy


def _score_pair(
    best_per_strategy: dict[str, dict],
    thresholds: dict[str, float],
    min_strats_high: int,
    catalog_index: dict[tuple, dict] | None,
) -> dict | None:
    """Score one pair from its best-per-strategy signals. Returns None when
    the pair falls below the LOW threshold. Shared by the in-memory API and the
    bounded SQLite path so both produce identical output."""
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
            return None
    elif composite_score >= thresholds["HIGH"]:
        confidence = "HIGH"
    elif composite_score >= thresholds["MEDIUM"]:
        confidence = "MEDIUM"
    elif composite_score >= thresholds["LOW"]:
        confidence = "LOW"
    else:
        return None  # Below minimum threshold, skip

    # Pick representative func_a/func_b from first signal, then harvest
    # size metadata (end_line) from ANY contributing strategy that has it.
    first_result = list(best_per_strategy.values())[0]
    func_a = first_result.get("func_a", {})
    func_b = first_result.get("func_b", {})

    # Harvest end_line: try strategy results first, then catalog lookup
    end_line_a = func_a.get("end_line")
    end_line_b = func_b.get("end_line")
    if end_line_a is None or end_line_b is None:
        for strat_result in best_per_strategy.values():
            if end_line_a is None:
                end_line_a = strat_result.get("func_a", {}).get("end_line")
            if end_line_b is None:
                end_line_b = strat_result.get("func_b", {}).get("end_line")
            if end_line_a is not None and end_line_b is not None:
                break
    # Fall back to catalog lookup when detectors don't carry end_line
    if catalog_index and (end_line_a is None or end_line_b is None):
        key_a = (func_a.get("file", ""), func_a.get("line", 0), func_a.get("name", ""))
        key_b = (func_b.get("file", ""), func_b.get("line", 0), func_b.get("name", ""))
        if end_line_a is None:
            cat_a = catalog_index.get(key_a)
            if cat_a:
                end_line_a = cat_a.get("end_line")
        if end_line_b is None:
            cat_b = catalog_index.get(key_b)
            if cat_b:
                end_line_b = cat_b.get("end_line")

    return {
        "func_a": {
            "name": func_a.get("name", "unknown"),
            "file": func_a.get("file", "unknown"),
            "line": func_a.get("line", 0),
            "qualified_name": func_a.get("qualified_name", func_a.get("name", "unknown")),
            "end_line": end_line_a,
        },
        "func_b": {
            "name": func_b.get("name", "unknown"),
            "file": func_b.get("file", "unknown"),
            "line": func_b.get("line", 0),
            "qualified_name": func_b.get("qualified_name", func_b.get("name", "unknown")),
            "end_line": end_line_b,
        },
        "composite_score": round(composite_score, 3),
        "confidence": confidence,
        "num_strategies": num_strategies,
        "strategies": strategy_details,
        "clone_type": classify_clone_type(best_per_strategy),
        "recommendation": generate_recommendation(confidence, num_strategies, best_per_strategy),
    }



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


# ============================================================================
# Bounded (SQLite-backed, streamed) merge — the production path
# ============================================================================

EXIT_INPUT = 1
EXIT_USAGE = 2
EXIT_RESOURCE = rpolicy.EXIT_RESOURCE

LEGACY_SUMMARY_KEYS = (
    "total_pairs", "by_confidence", "by_clone_type", "by_action",
    "strategies_used", "multi_signal_pairs", "defense_depth_pairs",
)


class MergeRefused(Exception):
    """A finite ceiling was exceeded under --resource-policy refuse."""

    def __init__(self, reason: str, detail: str) -> None:
        super().__init__(f"{reason}: {detail}")
        self.reason = reason
        self.detail = detail


def _strategy_name_from_path(path: Path) -> str:
    stem = path.name
    for suffix in (".jsonl", ".json"):
        if stem.endswith(suffix):
            stem = stem[: -len(suffix)]
            break
    return stem.replace("-results", "")


def _discover_inputs(input_dir: Path, strategy_files: list[str] | None) -> list[tuple[str, Path, str]]:
    """Return [(strategy_name, path, kind)] in the legacy iteration order:
    ``*-results.json[l]`` sorted by name, then ``duplicates/*.json`` (LLM groups)."""
    items: list[tuple[str, Path, str]] = []
    if strategy_files:
        for fp in strategy_files:
            path = Path(fp)
            name = _strategy_name_from_path(path).replace("detect-", "").replace("_", "-")
            items.append((name, path, "strategy"))
        return items
    seen: set[str] = set()
    for path in sorted(list(input_dir.glob("*-results.json")) + list(input_dir.glob("*-results.jsonl")),
                       key=lambda q: (_strategy_name_from_path(q), q.suffix)):
        name = _strategy_name_from_path(path)
        if name in seen:
            continue  # .json wins over .jsonl for the same strategy
        seen.add(name)
        items.append((name, path, "strategy"))
    for path in sorted(input_dir.glob("duplicates/*.json")):
        items.append(("llm_semantic", path, "llm"))
    return items


def _iter_records(path: Path) -> Iterator[Any]:
    fmt = jsonstream.detect_format(str(path))
    if fmt == "array":
        yield from jsonstream.iter_json_array(str(path))
    elif fmt == "jsonl":
        yield from jsonstream.iter_jsonl(str(path))
    elif fmt == "empty":
        raise jsonstream.JSONStreamError(f"{path}: empty detector output (expected a JSON array)")
    else:
        raise jsonstream.JSONStreamError(f"{path}: detector output is a JSON object, expected an array")


def _load_catalog_index(catalog_path: str | None) -> dict[tuple[str, int, str], dict]:
    index: dict[tuple[str, int, str], dict] = {}
    if not catalog_path:
        return index
    cp = Path(catalog_path)
    if not cp.exists() or cp.stat().st_size <= 2:
        return index
    try:
        for fn in jsonstream.iter_json_array(str(cp)):
            if isinstance(fn, dict):
                index[(fn.get("file", ""), fn.get("line", 0), fn.get("name", ""))] = fn
    except (jsonstream.JSONStreamError, OSError):
        return {}  # catalog enrichment is optional; a bad catalog never blocks the merge
    if index:
        print(f"  Catalog loaded: {len(index)} functions (size metadata available)", file=sys.stderr)
    return index


def _open_scratch_db(out_dir: Path) -> tuple[sqlite3.Connection, Path]:
    db_path = out_dir / f".merge-scratch-{os.getpid()}.sqlite"
    for stale in (db_path, Path(str(db_path) + "-journal")):
        if stale.exists():
            stale.unlink()
    conn = sqlite3.connect(str(db_path), isolation_level=None)
    # Bounded scratch database: 64 MiB page cache, temp tables on disk, no journal
    # (the file is discarded on any failure), no fsync (durability is irrelevant).
    conn.execute("PRAGMA journal_mode=OFF")
    conn.execute("PRAGMA synchronous=OFF")
    conn.execute("PRAGMA temp_store=FILE")
    conn.execute("PRAGMA cache_size=-65536")
    conn.execute(
        "CREATE TABLE pairs (pair_seq INTEGER PRIMARY KEY, pair_key TEXT NOT NULL UNIQUE)"
    )
    conn.execute(
        "CREATE TABLE signals (pair_seq INTEGER NOT NULL, strategy TEXT NOT NULL, "
        "score REAL NOT NULL, result_json TEXT NOT NULL, seen_seq INTEGER NOT NULL, "
        "PRIMARY KEY (pair_seq, strategy))"
    )
    conn.execute(
        "CREATE TABLE scored (pair_seq INTEGER PRIMARY KEY, composite REAL NOT NULL, "
        "num_strategies INTEGER NOT NULL, pair_json TEXT NOT NULL)"
    )
    conn.execute("CREATE INDEX scored_order ON scored (composite DESC, num_strategies DESC, pair_seq ASC)")
    return conn, db_path


def _ingest(conn: sqlite3.Connection, inputs: list[tuple[str, Path, str]]) -> dict[str, Any]:
    """Stream every detector record into the scratch tables.

    Ordering contract (matches the in-memory implementation exactly): pairs are
    numbered in first-seen order; per (pair, strategy) the highest score wins
    but keeps the seen_seq of its first occurrence.
    """
    seen_seq = 0
    per_strategy: dict[str, int] = {}
    conn.execute("BEGIN")
    upsert_pair = "INSERT OR IGNORE INTO pairs (pair_key) VALUES (?)"
    get_seq = "SELECT pair_seq FROM pairs WHERE pair_key = ?"
    get_sig = "SELECT score FROM signals WHERE pair_seq = ? AND strategy = ?"
    ins_sig = "INSERT INTO signals (pair_seq, strategy, score, result_json, seen_seq) VALUES (?, ?, ?, ?, ?)"
    upd_sig = "UPDATE signals SET score = ?, result_json = ? WHERE pair_seq = ? AND strategy = ?"
    for strategy_name, path, kind in inputs:
        count = 0
        records: Iterator[Any]
        if kind == "llm":
            groups = [g for g in _iter_records(path)]
            records = iter(convert_llm_results(groups))
        else:
            records = _iter_records(path)
        for idx, result in enumerate(records):
            if not isinstance(result, dict):
                raise jsonstream.JSONStreamError(
                    f"{path}: element {idx} is a JSON {type(result).__name__}, expected an object"
                )
            func_a = result.get("func_a", {})
            func_b = result.get("func_b", {})
            if not func_a or not func_b:
                continue
            key = make_pair_key(func_a, func_b)
            conn.execute(upsert_pair, (key,))
            pair_seq = conn.execute(get_seq, (key,)).fetchone()[0]
            strategy = result.get("strategy", strategy_name)
            score = float(result.get("final_score", 0.0) or 0.0)
            row = conn.execute(get_sig, (pair_seq, strategy)).fetchone()
            seen_seq += 1
            if row is None:
                conn.execute(ins_sig, (pair_seq, strategy, score, json.dumps(result), seen_seq))
            elif score > float(row[0]):
                conn.execute(upd_sig, (score, json.dumps(result), pair_seq, strategy))
            count += 1
            if count % 50000 == 0:
                conn.execute("COMMIT")
                conn.execute("BEGIN")
        per_strategy[strategy_name] = per_strategy.get(strategy_name, 0) + count
    conn.execute("COMMIT")
    unique_pairs = conn.execute("SELECT COUNT(*) FROM pairs").fetchone()[0]
    return {"candidates_seen": seen_seq, "per_strategy": per_strategy, "pairs_unique": unique_pairs}


def _score_all(
    conn: sqlite3.Connection,
    thresholds: dict[str, float],
    min_strats_high: int,
    catalog_index: dict[tuple, dict] | None,
    suppress_rules: list[str],
    actionable_only: bool,
) -> dict[str, Any]:
    """Score every unique pair (first-seen order) and stage survivors in ``scored``."""
    scored = 0
    suppressed = 0
    below = 0
    conn.execute("BEGIN")
    read = conn.cursor()
    for (pair_seq,) in read.execute("SELECT pair_seq FROM pairs ORDER BY pair_seq"):
        signals = [
            (strategy, json.loads(result_json))
            for strategy, result_json in conn.execute(
                "SELECT strategy, result_json FROM signals WHERE pair_seq = ? ORDER BY seen_seq",
                (pair_seq,),
            )
        ]
        best = _best_per_strategy(signals)
        pair = _score_pair(best, thresholds, min_strats_high, catalog_index)
        if pair is None:
            below += 1
            continue
        if suppress_rules or actionable_only:
            kept, meta = suppress_noise_patterns([pair], rules=suppress_rules,
                                                 actionable_only=actionable_only, return_meta=True)
            if not kept:
                suppressed += 1
                continue
            pair = kept[0]
        conn.execute(
            "INSERT INTO scored (pair_seq, composite, num_strategies, pair_json) VALUES (?, ?, ?, ?)",
            (pair_seq, pair["composite_score"], pair["num_strategies"], json.dumps(pair)),
        )
        scored += 1
        if scored % 50000 == 0:
            conn.execute("COMMIT")
            conn.execute("BEGIN")
    conn.execute("COMMIT")
    return {"pairs_scored": scored, "suppressed": suppressed, "below_threshold": below}


def _iter_scored(conn: sqlite3.Connection, limit: int | None) -> Iterator[dict]:
    sql = "SELECT pair_json FROM scored ORDER BY composite DESC, num_strategies DESC, pair_seq ASC"
    if limit is not None:
        sql += f" LIMIT {int(limit)}"
    for (pair_json,) in conn.execute(sql):
        yield json.loads(pair_json)


def _empty_summary() -> dict[str, Any]:
    return generate_summary([])


class _SummaryAccumulator:
    """Streaming equivalent of generate_summary()."""

    def __init__(self) -> None:
        self.by_confidence: dict[str, int] = defaultdict(int)
        self.by_clone_type: dict[str, int] = defaultdict(int)
        self.by_action: dict[str, int] = defaultdict(int)
        self.strategies: set[str] = set()
        self.total = 0
        self.multi = 0
        self.depth = 0

    def add(self, item: dict) -> None:
        self.total += 1
        self.by_confidence[item["confidence"]] += 1
        self.by_clone_type[item["clone_type"]] += 1
        self.by_action[item["recommendation"]["action"]] += 1
        self.strategies.update(item["strategies"].keys())
        if item["num_strategies"] >= 2:
            self.multi += 1
        if item["num_strategies"] >= 3:
            self.depth += 1

    def legacy(self) -> dict[str, Any]:
        return {
            "total_pairs": self.total,
            "by_confidence": dict(self.by_confidence),
            "by_clone_type": dict(self.by_clone_type),
            "by_action": dict(self.by_action),
            "strategies_used": sorted(self.strategies),
            "multi_signal_pairs": self.multi,
            "defense_depth_pairs": self.depth,
        }


def _write_legacy_json(fh, pairs: Iterator[dict], summary: dict | None) -> None:
    """Stream ``{"pairs": [...], "summary": {...}}`` (or a bare array when
    summary is None) in json.dump(indent=2) layout without holding the list."""
    if summary is None:
        fh.write("[")
        first = True
        for pair in pairs:
            fh.write("\n  " if first else ",\n  ")
            fh.write(json.dumps(pair, indent=2).replace("\n", "\n  "))
            first = False
        fh.write("\n]" if not first else "]")
        return
    fh.write('{\n  "pairs": [')
    first = True
    for pair in pairs:
        fh.write("\n    " if first else ",\n    ")
        fh.write(json.dumps(pair, indent=2).replace("\n", "\n    "))
        first = False
    fh.write("\n  ],\n" if not first else "],\n")
    fh.write('  "summary": ')
    fh.write(json.dumps(summary, indent=2).replace("\n", "\n  "))
    fh.write("\n}")


def _positive_int(value: str) -> int:
    try:
        n = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{value!r} is not an integer") from None
    if n <= 0:
        raise argparse.ArgumentTypeError(f"{value!r}: ceilings must be finite positive integers")
    return n


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Merge multi-signal duplicate detection results into unified report"
    )
    parser.add_argument("input_dir", help="Directory containing strategy output JSON/JSONL files")
    parser.add_argument("-o", "--output", default="/dev/stdout",
                        help="Legacy merged-results.json path (default: stdout). When a file path "
                             "is given, pairs.jsonl, summary.json and run.json are written beside it "
                             "and the legacy file only if it stays under --max-legacy-json-bytes.")
    parser.add_argument("--strategy-files", nargs="*",
                        help="Specific strategy files to merge (overrides input_dir scan)")
    parser.add_argument("--high-threshold", type=float, default=CONFIDENCE_THRESHOLDS["HIGH"],
                        help=f"Score threshold for HIGH confidence (default: {CONFIDENCE_THRESHOLDS['HIGH']})")
    parser.add_argument("--min-strategies-high", type=int, default=MIN_STRATEGIES_FOR_HIGH,
                        help=f"Min strategies for auto-HIGH (default: {MIN_STRATEGIES_FOR_HIGH})")
    parser.add_argument("--include-summary", action="store_true",
                        help="Include summary statistics in the legacy output")
    parser.add_argument("--suppress", nargs="*", default=[], choices=list(SUPPRESSION_RULES.keys()),
                        help="Noise suppression rules to apply after merge")
    parser.add_argument("--actionable-only", action="store_true",
                        help="Emit only Type 1/2 exact clones at HIGH confidence after suppression")
    parser.add_argument("--catalog",
                        help="Path to unified catalog JSON for size metadata enrichment "
                             "(auto-detected from input_dir)")
    # Finite resource policy (plan P1 §6.2). Every ceiling is a positive integer.
    defaults = rpolicy.ResourcePolicy.defaults()
    parser.add_argument("--resource-policy", choices=("refuse", "truncate"), default=defaults.mode,
                        help="What to do when a ceiling is exceeded (default: %(default)s)")
    parser.add_argument("--max-pairs", type=_positive_int, default=defaults.max_pairs,
                        help="Maximum pairs emitted (default: %(default)s)")
    parser.add_argument("--max-input-bytes", type=_positive_int, default=defaults.max_input_bytes,
                        help="Maximum total detector-output bytes accepted (default: %(default)s)")
    parser.add_argument("--max-output-bytes", type=_positive_int, default=defaults.max_output_bytes,
                        help="Maximum pairs.jsonl bytes (default: %(default)s)")
    parser.add_argument("--max-legacy-json-bytes", type=_positive_int, default=defaults.max_legacy_json_bytes,
                        help="Write the legacy merged-results.json only if its estimated size is "
                             "at or below this ceiling (default: %(default)s)")
    parser.add_argument("--no-legacy-json", action="store_true",
                        help="Never write the legacy merged-results.json (pairs.jsonl + summary.json only)")
    return parser


def _refusal(run: rpolicy.RunRecord, run_json: Path | None, reason: str, detail: str, counts: dict) -> int:
    print(f"REFUSED_RESOURCE: {reason}: {detail}", file=sys.stderr)
    run.note_error(f"{reason}: {detail}")
    run.finish(outcome="refused_resource", counts=counts, extra={"refusal": {"reason": reason, "detail": detail}})
    if run_json is not None:
        run.write(str(run_json))
    return EXIT_RESOURCE


def main() -> None:
    parser = _build_parser()
    try:
        args = parser.parse_args()
    except SystemExit as exc:  # argparse already printed; make the 'finite' contract visible
        if exc.code not in (0, None):
            print("merge-signals: resource ceilings must be finite positive integers", file=sys.stderr)
        raise
    try:
        policy = rpolicy.ResourcePolicy.defaults().with_overrides(
            mode=args.resource_policy, max_pairs=args.max_pairs,
            max_input_bytes=args.max_input_bytes, max_output_bytes=args.max_output_bytes,
            max_legacy_json_bytes=args.max_legacy_json_bytes,
        )
    except rpolicy.PolicyError as exc:
        print(f"merge-signals: {exc} (ceilings must be finite)", file=sys.stderr)
        sys.exit(EXIT_USAGE)

    user_thresholds = dict(CONFIDENCE_THRESHOLDS)
    user_thresholds["HIGH"] = args.high_threshold

    to_stdout = args.output in ("/dev/stdout", "-")
    out_path = None if to_stdout else Path(args.output)
    out_dir = out_path.parent if out_path is not None else None
    run_json = (out_dir / "run.json") if out_dir is not None else None
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
    run = rpolicy.RunRecord.start(policy=policy, base_dir=os.path.dirname(os.path.abspath(__file__)),
                                  extra={"tool": "merge-signals", "output": args.output})

    # Catalog (optional enrichment)
    catalog_path = args.catalog
    if not catalog_path:
        input_p = Path(args.input_dir) if not args.strategy_files else Path(args.strategy_files[0]).parent
        candidate = input_p.parent / "extract" / "catalog-unified.json"
        if candidate.exists():
            catalog_path = str(candidate)
    catalog_index = _load_catalog_index(catalog_path)

    # Inputs + input-bytes ceiling (checked before any expensive work)
    if not args.strategy_files:
        input_dir = Path(args.input_dir)
        if not input_dir.is_dir():
            print(f"Error: {args.input_dir} is not a directory", file=sys.stderr)
            sys.exit(EXIT_INPUT)
    inputs = _discover_inputs(Path(args.input_dir), args.strategy_files)
    input_bytes = 0
    for _, path, _ in inputs:
        try:
            input_bytes += path.stat().st_size
        except OSError as exc:
            print(f"Warning: Could not stat {path}: {exc}", file=sys.stderr)
    run.note_phase("inputs", {"files": len(inputs), "bytes": input_bytes})
    if input_bytes > policy.max_input_bytes:
        sys.exit(_refusal(run, run_json, "max_input_bytes",
                          f"detector outputs total {input_bytes} bytes > {policy.max_input_bytes}",
                          {"input_bytes": input_bytes}))

    if not inputs:
        print("Warning: No strategy results found", file=sys.stderr)
        summary = _empty_summary()
        if to_stdout:
            _write_legacy_json(sys.stdout, iter(()), summary if args.include_summary else None)
            return
        jsonstream.atomic_write_text(str(out_dir / "pairs.jsonl"), lambda fh: None)
        full_summary = dict(summary, complete=True, pairs_dropped=0, candidates_total=0)
        jsonstream.atomic_write_text(str(out_dir / "summary.json"),
                                     lambda fh: fh.write(json.dumps(full_summary, indent=2) + "\n"))
        legacy_written = not args.no_legacy_json
        if legacy_written:
            jsonstream.atomic_write_text(str(out_path), lambda fh: _write_legacy_json(
                fh, iter(()), summary if args.include_summary else None))
        run.finish(outcome="complete",
                   counts={"candidates_seen": 0, "pairs_unique": 0, "pairs_candidates": 0,
                           "pairs_emitted": 0, "pairs_dropped": 0, "suppressed": 0},
                   artifacts={"pairs.jsonl": str(out_dir / "pairs.jsonl"),
                              "summary.json": str(out_dir / "summary.json"),
                              "merged-results.json": str(out_path) if legacy_written else None},
                   extra={"legacy_export": {"written": legacy_written,
                                            "reason": "disabled by --no-legacy-json" if not legacy_written else "ok"}})
        run.write(str(run_json))
        return

    scratch_dir = out_dir if out_dir is not None else Path(os.getcwd())
    conn, db_path = _open_scratch_db(scratch_dir)
    pairs_tmp = None
    try:
        t0 = time.monotonic()
        try:
            ingest = _ingest(conn, inputs)
        except (jsonstream.JSONStreamError, OSError, ValueError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            run.note_error(str(exc))
            run.finish(outcome="input_error")
            if run_json is not None:
                run.write(str(run_json))
            sys.exit(EXIT_INPUT)
        run.note_phase("ingest", dict(ingest, seconds=round(time.monotonic() - t0, 3)))
        print(f"Merging results from {len(ingest['per_strategy'])} strategies: "
              f"{', '.join(ingest['per_strategy'].keys())}", file=sys.stderr)
        for name, n in ingest["per_strategy"].items():
            print(f"  {name}: {n} candidate pairs", file=sys.stderr)

        t1 = time.monotonic()
        score = _score_all(conn, user_thresholds, args.min_strategies_high, catalog_index or None,
                           args.suppress, args.actionable_only)
        run.note_phase("score", dict(score, seconds=round(time.monotonic() - t1, 3)))
        candidates = score["pairs_scored"]
        if args.suppress or args.actionable_only:
            print(f"\n  Suppressed {score['suppressed']} noise pairs ({candidates} remaining)", file=sys.stderr)

        counts = {
            "candidates_seen": ingest["candidates_seen"],
            "pairs_unique": ingest["pairs_unique"],
            "pairs_candidates": candidates,
            "suppressed": score["suppressed"],
        }

        # --max-pairs ceiling
        truncated = False
        truncation_reason = None
        limit: int | None = None
        if candidates > policy.max_pairs:
            if policy.mode == "refuse":
                sys.exit(_refusal(run, run_json, "max_pairs",
                                  f"{candidates} pairs > {policy.max_pairs}", counts))
            limit = policy.max_pairs
            truncated = True
            truncation_reason = f"max_pairs={policy.max_pairs} (top-ranked kept, {candidates - limit} dropped)"

        acc = _SummaryAccumulator()
        emitted = 0
        out_bytes = 0

        if to_stdout:
            # No sidecars on stdout; still honour the ceilings.
            def _stdout_pairs():
                nonlocal emitted
                for pair in _iter_scored(conn, limit):
                    acc.add(pair)
                    emitted += 1
                    yield pair
            _write_legacy_json(sys.stdout, _stdout_pairs(), None)
            sys.stdout.write("\n")
            if args.include_summary:
                pass  # legacy stdout mode with summary is rebuilt below
            return

        # pairs.jsonl (atomic)
        def _write_pairs(fh) -> None:
            nonlocal emitted, out_bytes, truncated, truncation_reason
            for pair in _iter_scored(conn, limit):
                line = json.dumps(pair) + "\n"
                if out_bytes + len(line) > policy.max_output_bytes:
                    if policy.mode == "refuse":
                        raise MergeRefused("max_output_bytes",
                                           f"pairs.jsonl would exceed {policy.max_output_bytes} bytes")
                    truncated = True
                    truncation_reason = f"max_output_bytes={policy.max_output_bytes}"
                    break
                fh.write(line)
                out_bytes += len(line)
                acc.add(pair)
                emitted += 1

        pairs_path = out_dir / "pairs.jsonl"
        try:
            jsonstream.atomic_write_text(str(pairs_path), _write_pairs)
        except MergeRefused as exc:
            sys.exit(_refusal(run, run_json, exc.reason, exc.detail, counts))

        dropped = candidates - emitted
        legacy_summary = acc.legacy()
        full_summary = dict(legacy_summary, complete=not truncated, pairs_dropped=dropped,
                            candidates_total=candidates, truncation_reason=truncation_reason)
        summary_path = out_dir / "summary.json"
        jsonstream.atomic_write_text(str(summary_path),
                                     lambda fh: fh.write(json.dumps(full_summary, indent=2) + "\n"))

        # Legacy compatibility export (finite ceiling; absence is explicit)
        legacy_info: dict[str, Any]
        if args.no_legacy_json:
            legacy_info = {"written": False, "reason": "disabled by --no-legacy-json"}
        else:
            estimate = int(out_bytes * 1.7) + len(json.dumps(legacy_summary)) + 64
            if estimate > policy.max_legacy_json_bytes:
                legacy_info = {"written": False,
                               "reason": f"estimated {estimate} bytes exceeds ceiling "
                                         f"max_legacy_json_bytes={policy.max_legacy_json_bytes}",
                               "estimated_bytes": estimate}
                if out_path.exists():
                    out_path.unlink()
            else:
                jsonstream.atomic_write_text(str(out_path), lambda fh: _write_legacy_json(
                    fh, jsonstream.iter_jsonl(str(pairs_path)),
                    legacy_summary if args.include_summary else None))
                legacy_info = {"written": True, "reason": "ok", "bytes": out_path.stat().st_size,
                               "estimated_bytes": estimate}

        counts.update({"pairs_emitted": emitted, "pairs_dropped": dropped, "output_bytes": out_bytes})
        print("\nMerge complete:", file=sys.stderr)
        print(f"  Total unique pairs: {legacy_summary['total_pairs']}", file=sys.stderr)
        print(f"  HIGH confidence: {legacy_summary['by_confidence'].get('HIGH', 0)}", file=sys.stderr)
        print(f"  MEDIUM confidence: {legacy_summary['by_confidence'].get('MEDIUM', 0)}", file=sys.stderr)
        print(f"  LOW confidence: {legacy_summary['by_confidence'].get('LOW', 0)}", file=sys.stderr)
        print(f"  Multi-signal (2+): {legacy_summary['multi_signal_pairs']}", file=sys.stderr)
        print(f"  Defense depth (3+): {legacy_summary['defense_depth_pairs']}", file=sys.stderr)
        if truncated:
            print(f"  TRUNCATED: {truncation_reason}; {dropped} pair(s) dropped", file=sys.stderr)
        if not legacy_info["written"]:
            print(f"  Legacy merged-results.json NOT written: {legacy_info['reason']}", file=sys.stderr)

        run.finish(outcome="complete", counts=counts, truncated=truncated,
                   truncation_reason=truncation_reason,
                   artifacts={"pairs.jsonl": str(pairs_path), "summary.json": str(summary_path),
                              "merged-results.json": str(out_path) if legacy_info["written"] else None},
                   extra={"legacy_export": legacy_info})
        run.write(str(run_json))
    except sqlite3.Error as exc:
        print(f"ERROR: scratch database failure: {exc}", file=sys.stderr)
        run.note_error(str(exc))
        run.finish(outcome="error")
        if run_json is not None:
            run.write(str(run_json))
        sys.exit(EXIT_INPUT)
    finally:
        try:
            conn.close()
        finally:
            for stale in (db_path, Path(str(db_path) + "-journal")):
                try:
                    if stale.exists():
                        stale.unlink()
                except OSError:
                    pass


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
