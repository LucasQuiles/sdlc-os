#!/usr/bin/env python3
# ABOUTME: Extracts function/method definitions from Python files using the ast module.
# ABOUTME: Produces a JSON array of function metadata including signatures, complexity, AST fingerprints, and token sequences.

"""
extract-functions-ast-py.py -- Python function extraction via AST analysis.

Walks a source directory, parses every matching Python file with ast.parse(),
and emits a JSON array of function/method descriptors suitable for duplicate
detection.

Usage:
    python extract-functions-ast-py.py /path/to/src
    python extract-functions-ast-py.py /path/to/src -o functions.json
    python extract-functions-ast-py.py /path/to/src -t "*.py" --include-tests
"""

from __future__ import annotations

import argparse
import ast
import copy
import fnmatch
import hashlib
import json
import os
import sys
from typing import Any


# ---------------------------------------------------------------------------
# AST normalization helpers
# ---------------------------------------------------------------------------

class _NameNormalizer(ast.NodeTransformer):
    """Replace all identifier names with positional placeholders.

    Within a single function body, each unique identifier (variable, parameter,
    function name) is replaced with _VAR_0, _VAR_1, ... in order of first
    appearance.  This lets us compare structural shape while ignoring naming.
    """

    def __init__(self) -> None:
        super().__init__()
        self._mapping: dict[str, str] = {}
        self._counter: int = 0

    def _placeholder(self, original: str) -> str:
        if original not in self._mapping:
            self._mapping[original] = f"_VAR_{self._counter}"
            self._counter += 1
        return self._mapping[original]

    def visit_Name(self, node: ast.Name) -> ast.Name:  # noqa: N802
        node.id = self._placeholder(node.id)
        self.generic_visit(node)
        return node

    def visit_arg(self, node: ast.arg) -> ast.arg:
        node.arg = self._placeholder(node.arg)
        # Erase annotation for structural comparison
        node.annotation = None
        self.generic_visit(node)
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:  # noqa: N802
        node.name = self._placeholder(node.name)
        # Strip decorators and return annotation for structural comparison
        node.decorator_list = []
        node.returns = None
        self.generic_visit(node)
        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AsyncFunctionDef:  # noqa: N802
        node.name = self._placeholder(node.name)
        node.decorator_list = []
        node.returns = None
        self.generic_visit(node)
        return node

    def visit_Attribute(self, node: ast.Attribute) -> ast.Attribute:
        node.attr = self._placeholder(node.attr)
        self.generic_visit(node)
        return node

    def visit_alias(self, node: ast.alias) -> ast.alias:
        node.name = self._placeholder(node.name)
        if node.asname:
            node.asname = self._placeholder(node.asname)
        self.generic_visit(node)
        return node


def _compute_ast_fingerprint(func_node: ast.AST) -> str:
    """SHA-256 hex digest of the normalized AST dump for a function node."""

    tree = copy.deepcopy(func_node)
    normalizer = _NameNormalizer()
    tree = normalizer.visit(tree)
    ast.fix_missing_locations(tree)
    dump = ast.dump(tree, annotate_fields=False)
    return hashlib.sha256(dump.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Token sequence extraction (DFS node type names)
# ---------------------------------------------------------------------------

def _extract_token_sequence(func_node: ast.AST) -> list[str]:
    """Return a list of AST node type names in depth-first order."""
    tokens: list[str] = []

    class _Visitor(ast.NodeVisitor):
        def generic_visit(self, node: ast.AST) -> None:
            tokens.append(type(node).__name__)
            super().generic_visit(node)

    _Visitor().visit(func_node)
    return tokens


# ---------------------------------------------------------------------------
# Cyclomatic complexity
# ---------------------------------------------------------------------------

# Node types that each add 1 to cyclomatic complexity.
_COMPLEXITY_NODE_TYPES: tuple[type, ...] = (
    ast.If,
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.ExceptHandler,
    ast.Assert,
    ast.With,
    ast.AsyncWith,
    ast.ListComp,
    ast.SetComp,
    ast.DictComp,
    ast.GeneratorExp,
)


def _cyclomatic_complexity(func_node: ast.AST) -> int:
    """Count complexity-contributing nodes inside a function body.

    Starts at 1 (the function itself is one path), then adds 1 for each
    branching / looping / exception-handling construct and each boolean
    operator (and / or).
    """
    complexity = 1

    for node in ast.walk(func_node):
        if isinstance(node, _COMPLEXITY_NODE_TYPES):
            complexity += 1
        elif isinstance(node, ast.BoolOp):
            # `a and b and c` has 2 ops, `a or b` has 1 op
            complexity += len(node.values) - 1
        # elif nodes are represented as nested ast.If inside orelse,
        # so they are already counted by the ast.If check above.

    return complexity


# ---------------------------------------------------------------------------
# Signature reconstruction
# ---------------------------------------------------------------------------

def _unparse_annotation(node: ast.expr | None) -> str | None:
    """Render a type annotation back to source text, or None."""
    if node is None:
        return None
    try:
        return ast.unparse(node)
    except Exception:
        return None


def _unparse_default(node: ast.expr | None) -> str | None:
    """Render a default value back to source text, or None."""
    if node is None:
        return None
    try:
        return ast.unparse(node)
    except Exception:
        return None


def _build_params(func_node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[dict[str, Any]]:
    """Extract the parameter list with type hints and defaults."""
    args = func_node.args
    params: list[dict[str, Any]] = []

    # Pair up arguments with their defaults.
    # positional defaults are right-aligned: if there are 3 args and 1 default,
    # the default belongs to the last arg.
    posonlyargs = getattr(args, "posonlyargs", [])
    all_positional = posonlyargs + args.args
    n_positional = len(all_positional)
    n_defaults = len(args.defaults)
    default_offset = n_positional - n_defaults

    for i, arg in enumerate(all_positional):
        default_idx = i - default_offset
        default = args.defaults[default_idx] if default_idx >= 0 else None
        params.append({
            "name": arg.arg,
            "type": _unparse_annotation(arg.annotation),
            "default": _unparse_default(default),
        })

    # *args
    if args.vararg:
        params.append({
            "name": f"*{args.vararg.arg}",
            "type": _unparse_annotation(args.vararg.annotation),
            "default": None,
        })
    elif args.kwonlyargs:
        # bare * separator (kwonly args exist but no *args)
        params.append({
            "name": "*",
            "type": None,
            "default": None,
        })

    # keyword-only
    for i, arg in enumerate(args.kwonlyargs):
        default = args.kw_defaults[i]  # may be None
        params.append({
            "name": arg.arg,
            "type": _unparse_annotation(arg.annotation),
            "default": _unparse_default(default),
        })

    # **kwargs
    if args.kwarg:
        params.append({
            "name": f"**{args.kwarg.arg}",
            "type": _unparse_annotation(args.kwarg.annotation),
            "default": None,
        })

    return params


def _build_signature(
    func_node: ast.FunctionDef | ast.AsyncFunctionDef,
    params: list[dict[str, Any]],
) -> str:
    """Reconstruct a human-readable signature string."""
    parts: list[str] = []
    for p in params:
        s = p["name"]
        if p["type"]:
            s += f": {p['type']}"
        if p["default"]:
            s += f" = {p['default']}"
        parts.append(s)

    prefix = "async def" if isinstance(func_node, ast.AsyncFunctionDef) else "def"
    ret = _unparse_annotation(func_node.returns)
    ret_str = f" -> {ret}" if ret else ""
    return f"{prefix} {func_node.name}({', '.join(parts)}){ret_str}"


# ---------------------------------------------------------------------------
# Decorator helpers
# ---------------------------------------------------------------------------

def _decorator_name(node: ast.expr) -> str:
    """Best-effort name string for a decorator expression."""
    try:
        return ast.unparse(node)
    except Exception:
        return "<unknown>"


def _decorator_names(func_node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    return [_decorator_name(d) for d in func_node.decorator_list]


# ---------------------------------------------------------------------------
# Export type classification
# ---------------------------------------------------------------------------

def _classify_export_type(
    func_node: ast.FunctionDef | ast.AsyncFunctionDef,
    class_name: str | None,
    is_nested: bool,
) -> str:
    """Classify the function's export type.

    Categories:
      - "module_level"   : top-level function (not inside a class)
      - "method"         : regular instance method inside a class
      - "classmethod"    : decorated with @classmethod
      - "staticmethod"   : decorated with @staticmethod
      - "property"       : decorated with @property (or @*.setter / @*.deleter)
      - "internal"       : nested function OR underscore-prefixed name
    """
    if is_nested:
        return "internal"

    dec_names = _decorator_names(func_node)

    if func_node.name.startswith("_") and not func_node.name.startswith("__"):
        # Single-underscore prefix => internal, but allow dunder methods to
        # remain classified by their decorator / position.
        if class_name is None:
            return "internal"

    if class_name is not None:
        # Check decorators for classmethod / staticmethod / property
        for d in dec_names:
            if d == "classmethod":
                return "classmethod"
            if d == "staticmethod":
                return "staticmethod"
            if d == "property" or d.endswith(".setter") or d.endswith(".deleter"):
                return "property"
        return "method"

    if func_node.name.startswith("_") and not func_node.name.startswith("__"):
        return "internal"

    return "module_level"


# ---------------------------------------------------------------------------
# Docstring extraction
# ---------------------------------------------------------------------------

def _first_line_docstring(func_node: ast.FunctionDef | ast.AsyncFunctionDef) -> str | None:
    """Return the first line of the docstring, or None."""
    if (
        func_node.body
        and isinstance(func_node.body[0], ast.Expr)
        and isinstance(func_node.body[0].value, (ast.Constant,))
        and isinstance(func_node.body[0].value.value, str)
    ):
        raw = func_node.body[0].value.value
        first = raw.strip().split("\n")[0].strip()
        return first if first else None
    return None


# ---------------------------------------------------------------------------
# Core extraction visitor
# ---------------------------------------------------------------------------

class _FunctionCollector(ast.NodeVisitor):
    """Walk an AST tree and collect function/method descriptors."""

    def __init__(self, filepath: str, base_dir: str) -> None:
        super().__init__()
        self.filepath = filepath
        self.rel_path = os.path.relpath(filepath, base_dir)
        self.results: list[dict[str, Any]] = []
        # Stack tracks (class_name | None, is_nested)
        self._scope_stack: list[tuple[str | None, bool]] = []

    @property
    def _class_name(self) -> str | None:
        for class_name, _ in reversed(self._scope_stack):
            if class_name is not None:
                return class_name
        return None

    @property
    def _is_nested(self) -> bool:
        # A function is nested if there is already a function scope above it.
        # The _scope_stack entries with class_name=None mark function scopes.
        func_depth = sum(1 for cn, _ in self._scope_stack if cn is None)
        return func_depth > 0

    def _process_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        class_name = self._class_name
        is_nested = self._is_nested

        qualified_name = f"{class_name}.{node.name}" if class_name else node.name
        params = _build_params(node)
        signature = _build_signature(node, params)
        decorators = _decorator_names(node)
        docstring = _first_line_docstring(node)
        body_lines = (node.end_lineno or node.lineno) - node.lineno + 1
        complexity = _cyclomatic_complexity(node)
        fingerprint = _compute_ast_fingerprint(node)
        token_seq = _extract_token_sequence(node)
        export_type = _classify_export_type(node, class_name, is_nested)

        self.results.append({
            "file": self.rel_path,
            "name": node.name,
            "qualified_name": qualified_name,
            "line": node.lineno,
            "end_line": node.end_lineno or node.lineno,
            "signature": signature,
            "params": params,
            "return_type": _unparse_annotation(node.returns),
            "decorators": decorators,
            "docstring": docstring,
            "body_lines": body_lines,
            "cyclomatic_complexity": complexity,
            "ast_fingerprint": fingerprint,
            "token_sequence": token_seq,
            "export_type": export_type,
            "language": "python",
        })

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        self._process_function(node)
        # Descend into body to find nested functions
        self._scope_stack.append((None, True))
        self.generic_visit(node)
        self._scope_stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: N802
        self._process_function(node)
        self._scope_stack.append((None, True))
        self.generic_visit(node)
        self._scope_stack.pop()

    def visit_ClassDef(self, node: ast.ClassDef) -> None:  # noqa: N802
        self._scope_stack.append((node.name, False))
        self.generic_visit(node)
        self._scope_stack.pop()


# ---------------------------------------------------------------------------
# File walking
# ---------------------------------------------------------------------------

_TEST_INDICATORS = (
    "test_",
    "_test.py",
    "tests/",
    "tests\\",
    "test/",
    "test\\",
    "conftest.py",
)


def _is_test_file(relpath: str) -> bool:
    """Heuristic: does this relative path look like a test file?"""
    basename = os.path.basename(relpath)
    lower = relpath.lower().replace("\\", "/")
    if basename.startswith("test_") or basename.endswith("_test.py"):
        return True
    if basename == "conftest.py":
        return True
    # Any segment in the path named "tests" or "test"
    parts = lower.split("/")
    if "tests" in parts or "test" in parts:
        return True
    return False


def walk_and_extract(
    source_dir: str,
    file_pattern: str = "*.py",
    include_tests: bool = False,
) -> list[dict[str, Any]]:
    """Walk source_dir, parse matching files, return function descriptors."""
    all_results: list[dict[str, Any]] = []

    for dirpath, _dirnames, filenames in os.walk(source_dir):
        for filename in sorted(filenames):
            if not fnmatch.fnmatch(filename, file_pattern):
                continue

            filepath = os.path.join(dirpath, filename)
            relpath = os.path.relpath(filepath, source_dir)

            if not include_tests and _is_test_file(relpath):
                continue

            try:
                with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                    source = f.read()
            except OSError as exc:
                print(f"[WARN] Cannot read {filepath}: {exc}", file=sys.stderr)
                continue

            try:
                tree = ast.parse(source, filename=filepath)
            except SyntaxError as exc:
                print(
                    f"[WARN] Syntax error in {filepath}: {exc}",
                    file=sys.stderr,
                )
                continue

            collector = _FunctionCollector(filepath, source_dir)
            collector.visit(tree)
            all_results.extend(collector.results)

    return all_results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Extract function/method definitions from Python source files "
            "and emit a JSON array of metadata for duplicate detection."
        ),
    )
    parser.add_argument(
        "source_dir",
        help="Root directory to scan for Python files.",
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        metavar="FILE",
        help="Write JSON output to FILE instead of stdout.",
    )
    parser.add_argument(
        "-t", "--pattern",
        default="*.py",
        metavar="GLOB",
        help="File glob pattern to match (default: '*.py').",
    )
    parser.add_argument(
        "--include-tests",
        action="store_true",
        default=False,
        help="Include test files (excluded by default).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    source_dir = os.path.abspath(args.source_dir)
    if not os.path.isdir(source_dir):
        print(f"Error: '{source_dir}' is not a directory.", file=sys.stderr)
        return 1

    results = walk_and_extract(
        source_dir=source_dir,
        file_pattern=args.pattern,
        include_tests=args.include_tests,
    )

    output_json = json.dumps(results, indent=2, ensure_ascii=False)

    if args.output:
        output_path = os.path.abspath(args.output)
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(output_json)
                f.write("\n")
            print(
                f"Wrote {len(results)} function(s) to {output_path}",
                file=sys.stderr,
            )
        except OSError as exc:
            print(f"Error writing to {output_path}: {exc}", file=sys.stderr)
            return 1
    else:
        sys.stdout.write(output_json)
        sys.stdout.write("\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
