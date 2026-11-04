#!/usr/bin/env python3
"""Fail-closed size ratchets and syntax evidence; clone candidates are advisory."""
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time

BASE = Path(__file__).resolve().parent
ENGINE_FILES = ("run_quality.py", "scripts/extract-functions-ast-py.py", "scripts/quality-swift.swift")
METRICS = ("files", "bytes", "lines", "nodes", "functions", "max_line", "max_function_lines")


def digest(value):
    return hashlib.sha256(value).hexdigest()


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def analyzer_sources():
    return {name: digest((BASE / name).read_bytes()) for name in ENGINE_FILES}


def command(argv, cwd=None, timeout=30):
    process = subprocess.Popen(argv, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               start_new_session=True)
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except BaseException:
        # A timed-out compiler can still own frontend children and open pipes.
        # This fresh process group belongs only to this invocation.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.communicate(timeout=5)
        raise
    if process.returncode:
        raise ValueError(f"{argv[0]} failed ({process.returncode}): {stderr[-1000:].decode(errors='replace')}")
    if len(stdout) > 16 * 1024 * 1024:
        raise ValueError("parser output exceeds 16 MiB")
    return stdout.decode()


def inventory(root, extensions):
    names = command(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], root)
    paths = sorted({p for p in names.split("\0") if Path(p).suffix in extensions})
    if not paths or len(paths) > 2000:
        raise ValueError("source inventory must contain 1..2000 files")
    result = {}
    total_bytes = 0
    for name in paths:
        path = root / name
        if path.is_symlink() or not path.resolve().is_relative_to(root) or not path.is_file():
            raise ValueError(f"source is missing, linked, or outside root: {name}")
        raw = path.read_bytes()
        total_bytes += len(raw)
        if len(raw) > 1024 * 1024 or total_bytes > 32 * 1024 * 1024:
            raise ValueError(f"source exceeds 1 MiB/file or 32 MiB total: {name}")
        result[name] = digest(raw)
    return result


def python_functions(source, name, root):
    tree = ast.parse(source, filename=name)
    compile(tree, name, "exec", dont_inherit=True)
    # Reuse the established signature and complexity collector, but do not use its
    # name-erasing fingerprint as evidence of identical behavior.
    spec = importlib.util.spec_from_file_location("quality_extractor", BASE / "scripts/extract-functions-ast-py.py")
    extractor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(extractor)
    collector = extractor._FunctionCollector(str(root / name), str(root))
    collector.visit(tree)
    fingerprints = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            exact = copy.deepcopy(node)
            exact.name = "_function"
            fingerprints[node.lineno] = digest(ast.dump(exact, include_attributes=False).encode())
    functions = [{"name": item["qualified_name"], "line": item["line"],
                  "end_line": item["end_line"], "signature": item["signature"],
                  "complexity": item["cyclomatic_complexity"],
                  "syntax_sha256": fingerprints[item["line"]]}
                 for item in collector.results]
    return sum(1 for _ in ast.walk(tree)), functions


def swift_files(root, names):
    compiler = Path(command(["xcrun", "--find", "swiftc"]).strip())
    libraries = compiler.parent.parent / "lib/swift/host"
    target = json.loads(command([str(compiler), "-print-target-info"]))
    sdk = command(["xcrun", "--show-sdk-path"]).strip()
    with tempfile.TemporaryDirectory(prefix="quality-swift-") as scratch:
        executable = Path(scratch) / "extract"
        command([str(compiler), "-I", str(libraries), "-L", str(libraries),
                 "-sdk", sdk, "-target", target["target"]["triple"],
                 "-resource-dir", target["paths"]["runtimeResourcePath"],
                 "-module-cache-path", str(Path(scratch) / "modules"),
                 "-lSwiftParser", "-lSwiftSyntax", "-Xlinker", "-rpath", "-Xlinker", str(libraries),
                 str(BASE / "scripts/quality-swift.swift"), "-o", str(executable)])
        result = json.loads(command([str(executable), *(str(root / name) for name in names)]))
    if set(result) != {str(root / name) for name in names}:
        raise ValueError("incomplete Swift source coverage")
    for name in names:
        item = result[str(root / name)]
        raw = (root / name).read_bytes()
        if type(item["nodes"]) is not int or item["nodes"] <= 0:
            raise ValueError(f"invalid Swift node count: {name}")
        for function in item["functions"]:
            start, end = function.pop("start_utf8"), function.pop("end_utf8")
            if not 0 <= start < end <= len(raw):
                raise ValueError(f"invalid Swift source range: {name}")
            # Decode the exact byte slice as a second check on UTF-8 boundaries.
            raw[start:end].decode("utf-8")
            if digest(raw[start:end]) != function.pop("source_sha256"):
                raise ValueError(f"Swift source range does not round-trip: {name}")
            function["complexity"] = None
    return result


def analyze(root, policy):
    root = root.resolve()
    if Path(command(["git", "rev-parse", "--show-toplevel"], root).strip()).resolve() != root:
        raise ValueError("root must be the repository root")
    groups = policy.get("groups", {})
    extensions = policy.get("extensions", [])
    if (policy.get("schema") != 1 or not groups or "total" in groups or not extensions
            or not set(extensions) <= {".py", ".swift", ".sh"}):
        raise ValueError("invalid quality policy")
    for prefixes in groups.values():
        if not isinstance(prefixes, list) or not prefixes:
            raise ValueError("each group requires explicit paths")
        for prefix in prefixes:
            if not isinstance(prefix, str) or not prefix or prefix.startswith("/") or ".." in Path(prefix).parts:
                raise ValueError("group paths must be relative and nonempty")
            if not (root / prefix).exists():
                raise ValueError(f"missing policy path: {prefix}")
    analyzer = analyzer_sources()
    before = inventory(root, extensions)
    parsers = {"python": f"ast-{sys.version_info.major}.{sys.version_info.minor}"}
    swift_names = [name for name in before if name.endswith(".swift")]
    swift = {}
    if swift_names:
        libraries = Path(command(["xcrun", "--find", "swiftc"]).strip()).parent.parent / "lib/swift/host"
        parsers["swift"] = {
            "compiler": command(["xcrun", "swiftc", "--version"]).splitlines()[0],
            "libraries": {name: digest((libraries / name).read_bytes())
                          for name in ("libSwiftParser.dylib", "libSwiftSyntax.dylib")},
        }
        swift = swift_files(root, swift_names)
    if any(name.endswith(".sh") for name in before):
        parsers["shell"] = command(["bash", "--version"]).splitlines()[0]
    totals = {group: dict.fromkeys(METRICS, 0) for group in groups}
    files, candidates = [], {}
    for name, sha in before.items():
        owners = [group for group, prefixes in groups.items()
                  if any(name.startswith(p) if p.endswith("/") else name == p for p in prefixes)]
        if len(owners) != 1:
            raise ValueError(f"source needs exactly one group: {name}")
        raw = (root / name).read_bytes()
        source = raw.decode("utf-8")
        suffix = Path(name).suffix
        if suffix == ".py":
            nodes, functions = python_functions(source, name, root)
        elif suffix == ".swift":
            item = swift[str(root / name)]
            nodes, functions = item["nodes"], item["functions"]
        else:
            command(["bash", "-n", str(root / name)])
            nodes, functions = 0, []
        metrics = {"files": 1, "bytes": len(raw), "lines": len(source.splitlines()), "nodes": nodes,
                   "functions": len(functions), "max_line": max(map(len, source.splitlines()), default=0),
                   "max_function_lines": max((f["end_line"] - f["line"] + 1 for f in functions), default=0)}
        target = totals[owners[0]]
        for metric, value in metrics.items():
            target[metric] = max(target[metric], value) if metric.startswith("max_") else target[metric] + value
        files.append({"path": name, "group": owners[0], "sha256": sha,
                      "metrics": metrics, "functions": functions})
        for function in functions:
            if function["end_line"] > function["line"]:
                candidates.setdefault((suffix, function["syntax_sha256"]), []).append(
                    {"path": name, "line": function["line"], "name": function["name"]})
    if any(not metrics["files"] for metrics in totals.values()):
        raise ValueError("empty policy group")
    if inventory(root, extensions) != before or analyzer_sources() != analyzer:
        raise ValueError("sources or analyzer changed during analysis")
    totals["total"] = {key: (max(values[key] for values in totals.values()) if key.startswith("max_")
                              else sum(values[key] for values in totals.values())) for key in METRICS}
    return {"schema": 1, "policy_sha256": digest(encoded(policy)), "parsers": parsers,
            "analyzer_files": analyzer, "python_runtime": sys.version,
            "source_sha256": digest(encoded(before)), "totals": totals, "files": files,
            "duplicate_candidates": [items for items in candidates.values() if len(items) > 1],
            "semantic_equivalence": "unknown; syntax matches require behavioral review",
            "lsp_coverage": "unknown; no reference or rename proof",
            "shell_coverage": "syntax and physical size only; no AST or function analysis"}


def compare(current, baseline):
    if baseline.get("schema") != 1:
        raise ValueError("unsupported baseline")
    errors = []
    for key in ("policy_sha256", "parsers", "analyzer_files"):
        if current[key] != baseline.get(key):
            errors.append(f"{key} changed; explicit baseline review required")
    if set(current["totals"]) != set(baseline.get("totals", {})):
        errors.append("baseline groups changed")
    for group, metrics in current["totals"].items():
        for metric, value in metrics.items():
            limit = baseline.get("totals", {}).get(group, {}).get(metric)
            if type(limit) is not int or limit < 0:
                errors.append(f"invalid baseline {group}.{metric}")
            elif value > limit:
                errors.append(f"{group}.{metric}: {value} exceeds {limit}")
    return errors


def write_json(path, value, exclusive=False):
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        try:
            json.dump(value, stream, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
            if exclusive:
                os.link(temporary, path)
            else:
                os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--capture-baseline", action="store_true", help="create a new baseline; never overwrite")
    args = parser.parse_args()
    report = {"status": "incomplete", "checked_at_unix": time.time()}
    try:
        if args.report.resolve() in {args.policy.resolve(), args.baseline.resolve()}:
            raise ValueError("report must not overwrite inputs")
        policy_bytes = args.policy.read_bytes()
        baseline_bytes = None if args.capture_baseline else args.baseline.read_bytes()
        report["policy_file_sha256"] = digest(policy_bytes)
        report["baseline_file_sha256"] = digest(baseline_bytes) if baseline_bytes else None
        report["analysis"] = analyze(args.root, json.loads(policy_bytes))
        if args.policy.read_bytes() != policy_bytes or (baseline_bytes is not None and args.baseline.read_bytes() != baseline_bytes):
            raise ValueError("policy or baseline changed during analysis")
        if args.capture_baseline:
            write_json(args.baseline, {key: report["analysis"][key] for key in
                       ("schema", "policy_sha256", "parsers", "analyzer_files", "source_sha256", "totals")}, exclusive=True)
            errors = []
        else:
            errors = compare(report["analysis"], json.loads(baseline_bytes))
        report.update(status="fail" if errors else "pass", errors=errors)
    except (OSError, ValueError, SyntaxError, KeyError, TypeError, AttributeError,
            IndexError, StopIteration, RecursionError, subprocess.TimeoutExpired) as error:
        report["errors"] = [f"{type(error).__name__}: {error}"]
    if args.report.resolve() in {args.policy.resolve(), args.baseline.resolve()}:
        print(json.dumps({"status": "incomplete", "errors": report["errors"]}))
        return 2
    write_json(args.report, report)
    print(json.dumps({key: report[key] for key in ("status", "errors")}))
    return {"pass": 0, "fail": 1, "incomplete": 2}[report["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
