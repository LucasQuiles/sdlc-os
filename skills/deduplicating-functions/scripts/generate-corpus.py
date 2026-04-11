#!/usr/bin/env python3
# ABOUTME: Synthetic corpus generator for duplicate function detection evaluation.
# Produces ground truth clone pairs at each type using template-based generation.

"""
Synthetic Corpus Generator

Creates N function pairs per clone type for evaluation harness testing.
Uses template-based generation to produce realistic token sequences
without requiring actual source code.

Usage:
  ./generate-corpus.py -o corpus.json
  ./generate-corpus.py -o corpus.json --num-per-type 10 --seed 42
"""

import argparse
import json
import random
from pathlib import Path
from typing import Any

# Base token sequence templates representing common function patterns
# Group A: Computation patterns (loops, accumulation)
BASE_TEMPLATES: list[list[str]] = [
    ["FunctionDef", "arguments", "arg", "For", "AugAssign", "Return"],
    ["FunctionDef", "arguments", "arg", "While", "AugAssign", "If", "Break", "Return"],
    ["FunctionDef", "arguments", "arg", "ListComp", "Return"],
    ["FunctionDef", "arguments", "arg", "arg", "BinOp", "Return"],
]

# Group B: Validation/branching patterns
VALIDATION_TEMPLATES: list[list[str]] = [
    ["FunctionDef", "arguments", "arg", "If", "Return", "Return"],
    ["FunctionDef", "arguments", "arg", "If", "Raise", "If", "Raise", "Return"],
    ["FunctionDef", "arguments", "arg", "Try", "Call", "Except", "Return"],
    ["FunctionDef", "arguments", "arg", "If", "Compare", "BoolOp", "Return", "Raise"],
]

# Group C: I/O and side-effect patterns
IO_TEMPLATES: list[list[str]] = [
    ["FunctionDef", "arguments", "arg", "Assign", "Call", "Return"],
    ["FunctionDef", "arguments", "arg", "arg", "Assign", "Call", "Return"],
    ["FunctionDef", "arguments", "arg", "Return", "Call", "Attribute"],
    ["FunctionDef", "arguments", "arg", "arg", "arg", "For", "If", "Call", "Return"],
]

# Group D: Complex multi-statement patterns (ONLY for non-clone diversity)
DIVERSE_TEMPLATES: list[list[str]] = [
    ["FunctionDef", "arguments", "arg", "With", "Assign", "Call", "For", "Assign", "Call", "Return"],
    ["FunctionDef", "arguments", "arg", "arg", "Assign", "DictComp", "For", "If", "Assign", "Return"],
    ["FunctionDef", "arguments", "arg", "Assign", "While", "Call", "Assign", "If", "Break", "AugAssign", "Return"],
    ["FunctionDef", "arguments", "arg", "arg", "arg", "Try", "For", "Assign", "Call", "AugAssign", "Except", "Call", "Return"],
    ["FunctionDef", "arguments", "Assign", "Assign", "Call", "Attribute", "Call", "Attribute", "Return"],
    ["FunctionDef", "arguments", "arg", "arg", "For", "For", "If", "Assign", "Call", "Return"],
    ["FunctionDef", "arguments", "arg", "Assign", "SetComp", "If", "Return", "Return"],
    ["FunctionDef", "arguments", "arg", "arg", "arg", "arg", "Assign", "Assign", "Call", "Call", "Call", "Return"],
    ["FunctionDef", "arguments", "arg", "Global", "If", "Assign", "Call", "Return"],
    ["FunctionDef", "arguments", "Assign", "For", "Yield"],
]

# All templates combined for clone generation; diverse templates only for non-clone padding
ALL_CLONE_TEMPLATES = BASE_TEMPLATES + VALIDATION_TEMPLATES + IO_TEMPLATES

# Name fragments for synthetic function names
NAME_PREFIXES = ["calc", "compute", "get", "fetch", "process", "validate", "check", "format", "parse", "build"]
NAME_SUFFIXES = ["value", "result", "data", "item", "record", "total", "count", "sum", "list", "output"]
NAME_VERBS_V2 = ["calculate", "determine", "retrieve", "obtain", "handle", "verify", "convert", "generate", "extract", "create"]

# Argument name pools
ARG_NAMES_A = ["items", "data", "value", "input", "src", "x", "record", "payload", "config", "opts"]
ARG_NAMES_B = ["elements", "values", "val", "arg", "source", "num", "entry", "body", "settings", "params"]


def _make_func(
    name: str,
    file: str,
    line: int,
    token_seq: list[str],
    body_lines: int,
    param_names: list[str],
) -> dict[str, Any]:
    return {
        "name": name,
        "file": file,
        "line": line,
        "token_sequence": token_seq,
        "body_lines": body_lines,
        "params": [{"name": p} for p in param_names],
    }


def _param_names_from_template(template: list[str], arg_pool: list[str]) -> list[str]:
    """Count 'arg' tokens in template to determine param count, pick names from pool."""
    count = template.count("arg")
    return arg_pool[:count] if count <= len(arg_pool) else arg_pool + [f"p{i}" for i in range(count - len(arg_pool))]


def generate_type1_pair(idx: int, template: list[str], rng: random.Random) -> tuple[dict, dict, dict]:
    """Type 1: Exact clone — identical token sequence, different file/name."""
    name_a = f"{NAME_PREFIXES[idx % len(NAME_PREFIXES)]}_{NAME_SUFFIXES[idx % len(NAME_SUFFIXES)]}_v1"
    name_b = f"{NAME_PREFIXES[idx % len(NAME_PREFIXES)]}_{NAME_SUFFIXES[idx % len(NAME_SUFFIXES)]}_v2"
    file_a = f"type1_{idx}_a.py"
    file_b = f"type1_{idx}_b.py"
    body = rng.randint(4, 10)
    params = _param_names_from_template(template, ARG_NAMES_A)

    func_a = _make_func(name_a, file_a, 1, list(template), body, params)
    func_b = _make_func(name_b, file_b, 1, list(template), body, params)
    pair = {
        "func_a": f"{file_a}:{name_a}:1",
        "func_b": f"{file_b}:{name_b}:1",
        "clone_type": 1,
        "is_clone": True,
    }
    return func_a, func_b, pair


def generate_type2_pair(idx: int, template: list[str], rng: random.Random) -> tuple[dict, dict, dict]:
    """Type 2: Renamed clone — same structure, different parameter names."""
    name_a = f"{NAME_PREFIXES[idx % len(NAME_PREFIXES)]}_{NAME_SUFFIXES[idx % len(NAME_SUFFIXES)]}"
    name_b = f"{NAME_VERBS_V2[idx % len(NAME_VERBS_V2)]}_{NAME_SUFFIXES[(idx + 1) % len(NAME_SUFFIXES)]}"
    file_a = f"type2_{idx}_a.py"
    file_b = f"type2_{idx}_b.py"
    body = rng.randint(4, 10)
    params_a = _param_names_from_template(template, ARG_NAMES_A)
    params_b = _param_names_from_template(template, ARG_NAMES_B)

    func_a = _make_func(name_a, file_a, 1, list(template), body, params_a)
    func_b = _make_func(name_b, file_b, 1, list(template), body, params_b)
    pair = {
        "func_a": f"{file_a}:{name_a}:1",
        "func_b": f"{file_b}:{name_b}:1",
        "clone_type": 2,
        "is_clone": True,
    }
    return func_a, func_b, pair


def generate_type3_pair(idx: int, template: list[str], rng: random.Random) -> tuple[dict, dict, dict]:
    """Type 3: Near-miss clone — add or remove 1-2 tokens from sequence."""
    name_a = f"near_{NAME_PREFIXES[idx % len(NAME_PREFIXES)]}_{idx}"
    name_b = f"close_{NAME_PREFIXES[idx % len(NAME_PREFIXES)]}_{idx}"
    file_a = f"type3_{idx}_a.py"
    file_b = f"type3_{idx}_b.py"

    # Mutate: add or remove 1-2 tokens
    mutated = list(template)
    extra_tokens = ["Assign", "Call", "If", "Pass", "AugAssign"]
    ops = rng.randint(1, 2)
    for _ in range(ops):
        if rng.random() < 0.5 and len(mutated) > 4:
            # Remove a non-structural token (not FunctionDef/Return)
            removable = [i for i, t in enumerate(mutated) if t not in ("FunctionDef", "Return")]
            if removable:
                mutated.pop(rng.choice(removable))
        else:
            insert_pos = rng.randint(2, len(mutated) - 1)
            mutated.insert(insert_pos, rng.choice(extra_tokens))

    body_a = len(template) - 2
    body_b = len(mutated) - 2
    params_a = _param_names_from_template(template, ARG_NAMES_A)
    params_b = _param_names_from_template(mutated, ARG_NAMES_A)

    func_a = _make_func(name_a, file_a, 1, list(template), max(3, body_a), params_a)
    func_b = _make_func(name_b, file_b, 1, mutated, max(3, body_b), params_b)
    pair = {
        "func_a": f"{file_a}:{name_a}:1",
        "func_b": f"{file_b}:{name_b}:1",
        "clone_type": 3,
        "is_clone": True,
    }
    return func_a, func_b, pair


def generate_type4_pair(idx: int, templates: list[list[str]], rng: random.Random) -> tuple[dict, dict, dict]:
    """Type 4: Semantic clone — same param count/return structure, different token sequence."""
    name_a = f"impl_{NAME_SUFFIXES[idx % len(NAME_SUFFIXES)]}_v1"
    name_b = f"impl_{NAME_SUFFIXES[idx % len(NAME_SUFFIXES)]}_v2"
    file_a = f"type4_{idx}_a.py"
    file_b = f"type4_{idx}_b.py"

    # Pick two structurally different templates with same param count
    t_a = templates[idx % len(templates)]
    # Find another template with same arg count
    arg_count_a = t_a.count("arg")
    candidates = [t for t in templates if t.count("arg") == arg_count_a and t != t_a]
    t_b = candidates[idx % len(candidates)] if candidates else templates[(idx + 1) % len(templates)]

    params_a = _param_names_from_template(t_a, ARG_NAMES_A)
    params_b = _param_names_from_template(t_b, ARG_NAMES_B)
    body_a = max(3, len(t_a) - 2)
    body_b = max(3, len(t_b) - 2)

    func_a = _make_func(name_a, file_a, 1, list(t_a), body_a, params_a)
    func_b = _make_func(name_b, file_b, 1, list(t_b), body_b, params_b)
    pair = {
        "func_a": f"{file_a}:{name_a}:1",
        "func_b": f"{file_b}:{name_b}:1",
        "clone_type": 4,
        "is_clone": True,
    }
    return func_a, func_b, pair


def generate_non_clone_pair(
    func_pool: list[dict],
    used_pairs: set[str],
    rng: random.Random,
) -> dict | None:
    """Pick two clearly different functions from the pool as a non-clone pair."""
    attempts = 0
    while attempts < 50:
        fa = rng.choice(func_pool)
        fb = rng.choice(func_pool)
        if fa is fb:
            attempts += 1
            continue
        key = "|".join(sorted([f"{fa['file']}:{fa['name']}:1", f"{fb['file']}:{fb['name']}:1"]))
        if key in used_pairs:
            attempts += 1
            continue
        # Prefer structurally different pairs (different token sequences)
        if fa["token_sequence"] != fb["token_sequence"]:
            used_pairs.add(key)
            return {
                "func_a": f"{fa['file']}:{fa['name']}:1",
                "func_b": f"{fb['file']}:{fb['name']}:1",
                "clone_type": None,
                "is_clone": False,
            }
        attempts += 1
    return None


def generate_corpus(num_per_type: int = 10, seed: int = 42) -> dict[str, Any]:
    """
    Generate a synthetic corpus with num_per_type pairs for each clone type
    plus an equal number of non-clone pairs.

    Returns corpus dict with 'functions' and 'ground_truth' arrays.
    """
    rng = random.Random(seed)
    functions: list[dict] = []
    ground_truth: list[dict] = []
    used_clone_keys: set[str] = set()

    for i in range(num_per_type):
        template = ALL_CLONE_TEMPLATES[i % len(ALL_CLONE_TEMPLATES)]

        # Type 1
        fa, fb, pair = generate_type1_pair(i, template, rng)
        functions.extend([fa, fb])
        ground_truth.append(pair)
        used_clone_keys.add("|".join(sorted([pair["func_a"], pair["func_b"]])))

        # Type 2
        fa, fb, pair = generate_type2_pair(i, template, rng)
        functions.extend([fa, fb])
        ground_truth.append(pair)
        used_clone_keys.add("|".join(sorted([pair["func_a"], pair["func_b"]])))

        # Type 3
        fa, fb, pair = generate_type3_pair(i, template, rng)
        functions.extend([fa, fb])
        ground_truth.append(pair)
        used_clone_keys.add("|".join(sorted([pair["func_a"], pair["func_b"]])))

        # Type 4
        fa, fb, pair = generate_type4_pair(i, ALL_CLONE_TEMPLATES, rng)
        functions.extend([fa, fb])
        ground_truth.append(pair)
        used_clone_keys.add("|".join(sorted([pair["func_a"], pair["func_b"]])))

    # Add diverse non-clone "decoy" functions from DIVERSE_TEMPLATES
    # These are structurally VERY different from clone templates, reducing FP
    decoy_names = [
        "open_connection", "write_log", "compress_archive", "render_template",
        "migrate_schema", "schedule_task", "encrypt_payload", "parse_config",
        "stream_events", "generate_report",
    ]
    for j, dt in enumerate(DIVERSE_TEMPLATES):
        name = decoy_names[j % len(decoy_names)]
        func = _make_func(
            name=f"{name}_{j}",
            file=f"diverse_{j}.py",
            line=1,
            token_seq=list(dt),
            body_lines=max(5, len(dt)),
            param_names=_param_names_from_template(dt, ARG_NAMES_A),
        )
        functions.append(func)

    # Generate non-clone pairs (same count as clone pairs total)
    num_non_clones = num_per_type * 4
    for _ in range(num_non_clones):
        pair = generate_non_clone_pair(functions, used_clone_keys, rng)
        if pair:
            ground_truth.append(pair)

    return {
        "functions": functions,
        "ground_truth": ground_truth,
        "metadata": {
            "num_per_type": num_per_type,
            "seed": seed,
            "total_functions": len(functions),
            "total_pairs": len(ground_truth),
            "clone_pairs": sum(1 for p in ground_truth if p["is_clone"]),
            "non_clone_pairs": sum(1 for p in ground_truth if not p["is_clone"]),
        },
    }


def validate_corpus(corpus: dict) -> list[str]:
    """Validate corpus structure. Returns list of error messages (empty = valid)."""
    errors: list[str] = []
    funcs = corpus.get("functions", [])
    gt = corpus.get("ground_truth", [])

    if not funcs:
        errors.append("No functions in corpus")
    if not gt:
        errors.append("No ground truth entries")

    # Check required fields
    for i, f in enumerate(funcs):
        for field in ("name", "file", "line", "token_sequence", "body_lines", "params"):
            if field not in f:
                errors.append(f"Function[{i}] missing field: {field}")

    for i, entry in enumerate(gt):
        for field in ("func_a", "func_b", "is_clone"):
            if field not in entry:
                errors.append(f"ground_truth[{i}] missing field: {field}")
        if "clone_type" not in entry:
            errors.append(f"ground_truth[{i}] missing clone_type")

    # Check for duplicate pair keys
    seen_keys: set[str] = set()
    for i, entry in enumerate(gt):
        key = "|".join(sorted([entry.get("func_a", ""), entry.get("func_b", "")]))
        if key in seen_keys:
            errors.append(f"ground_truth[{i}] duplicate pair key: {key}")
        seen_keys.add(key)

    return errors


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate synthetic evaluation corpus for duplicate function detection"
    )
    parser.add_argument(
        "-o", "--output",
        default="corpus.json",
        help="Output file path (default: corpus.json)",
    )
    parser.add_argument(
        "--num-per-type",
        type=int,
        default=10,
        help="Number of pairs per clone type (default: 10)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate the generated corpus and report issues",
    )

    args = parser.parse_args()

    corpus = generate_corpus(num_per_type=args.num_per_type, seed=args.seed)

    if args.validate:
        errors = validate_corpus(corpus)
        if errors:
            for e in errors:
                print(f"ERROR: {e}", flush=True)
            import sys
            sys.exit(1)
        print("Corpus validation: OK")

    meta = corpus.get("metadata", {})
    print(f"Generated corpus: {meta.get('total_functions', '?')} functions, "
          f"{meta.get('total_pairs', '?')} pairs "
          f"({meta.get('clone_pairs', '?')} clones, {meta.get('non_clone_pairs', '?')} non-clones)")

    output_path = Path(args.output)
    output_path.write_text(json.dumps(corpus, indent=2))
    print(f"Written to: {output_path}")


if __name__ == "__main__":
    main()
