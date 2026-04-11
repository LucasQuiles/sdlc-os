#!/usr/bin/env python3
"""Multi-language regex-based function extractor.

Portable replacement for extract-functions-regex.sh, which uses grep -P
(PCRE) and fails silently on macOS BSD grep. This Python version uses the
stdlib re module and works on any platform with Python 3.

Supports: TypeScript/JavaScript, Python, Go, Rust, Java, Kotlin.

Output format matches the AST extractors: a JSON array of enriched
function metadata ready for the detection pipeline.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass
class LanguageConfig:
    name: str              # canonical name
    patterns: list[str]    # PCRE patterns for matching function definition lines
    globs: list[str]       # file globs
    test_exclude_names: list[str]  # test file name patterns to exclude
    test_exclude_paths: list[str]  # test directory path fragments to exclude
    name_extractors: list[str]     # patterns to extract the function name from a matched line
    comment_prefix: str = "//"


LANGS: dict[str, LanguageConfig] = {
    "typescript": LanguageConfig(
        name="typescript",
        patterns=[
            r"^\s*export\s+(async\s+)?function\s+\w+",
            r"^\s*(export\s+)?(const|let|var)\s+\w+\s*=\s*(async\s+)?\(",
            r"^\s*(public|private|protected)\s+(static\s+)?(async\s+)?\w+\s*\(",
            r"^(async\s+)?function\s+\w+",
            r"^\s*(async\s+)?\w+\s*=\s*\(.*\)\s*=>",
        ],
        globs=["*.ts", "*.tsx", "*.js", "*.jsx", "*.mjs", "*.cjs"],
        test_exclude_names=["*.test.*", "*.spec.*"],
        test_exclude_paths=["__tests__", "/test/", "/tests/"],
        name_extractors=[
            r"function\s+(\w+)",
            r"(?:export\s+)?(?:const|let|var)\s+(\w+)",
            r"(?:public|private|protected)\s+(?:static\s+)?(?:async\s+)?(\w+)\s*\(",
            r"^\s*(?:async\s+)?(\w+)\s*=",
        ],
    ),
    "python": LanguageConfig(
        name="python",
        patterns=[
            r"^\s*(async\s+)?def\s+\w+",
        ],
        globs=["*.py"],
        test_exclude_names=["test_*.py", "*_test.py"],
        test_exclude_paths=["/tests/", "/test/"],
        name_extractors=[
            r"(?:async\s+)?def\s+(\w+)",
        ],
        comment_prefix="#",
    ),
    "go": LanguageConfig(
        name="go",
        patterns=[
            r"^func\s+\w+\s*\(",
            r"^func\s+\([^)]+\)\s+\w+\s*\(",
        ],
        globs=["*.go"],
        test_exclude_names=["*_test.go"],
        test_exclude_paths=[],
        name_extractors=[
            r"func\s+(?:\([^)]+\)\s+)?(\w+)",
        ],
    ),
    "rust": LanguageConfig(
        name="rust",
        patterns=[
            r"^\s*(pub\s+)?(async\s+)?fn\s+\w+",
        ],
        globs=["*.rs"],
        test_exclude_names=[],
        test_exclude_paths=["/tests/"],
        name_extractors=[
            r"(?:pub\s+)?(?:async\s+)?fn\s+(\w+)",
        ],
    ),
    "java": LanguageConfig(
        name="java",
        patterns=[
            # Java method: visibility + return type + name + (
            r"^\s*(public|private|protected)\s+(static\s+)?(final\s+)?[\w<>\[\],\s]+\s+\w+\s*\(",
        ],
        globs=["*.java"],
        test_exclude_names=["*Test.java", "*Spec.java"],
        test_exclude_paths=["/test/", "/tests/"],
        name_extractors=[
            # Last word before ( is the method name in Java
            r"(\w+)\s*\(",
        ],
    ),
    "kotlin": LanguageConfig(
        name="kotlin",
        patterns=[
            r"^\s*(public\s+|private\s+|protected\s+|internal\s+)?(inline\s+)?fun\s+\w+",
        ],
        globs=["*.kt"],
        test_exclude_names=["*Test.kt", "*Spec.kt"],
        test_exclude_paths=["/test/", "/tests/"],
        name_extractors=[
            r"fun\s+(\w+)",
        ],
    ),
}

# Keywords to reject as method names (Java pattern is greedy)
_KEYWORD_BLOCKLIST = {
    "if", "else", "for", "while", "switch", "case", "return", "throw",
    "try", "catch", "finally", "do", "new", "super", "this",
}


def _resolve_language(lang_hint: str) -> str:
    """Map a user-provided language hint to a canonical key in LANGS."""
    aliases = {
        "ts": "typescript", "js": "typescript", "javascript": "typescript",
        "py": "python",
        "golang": "go",
        "rs": "rust",
        "kt": "kotlin",
    }
    return aliases.get(lang_hint.lower(), lang_hint.lower())


def _should_skip_test_file(path: str, cfg: LanguageConfig, include_tests: bool) -> bool:
    if include_tests:
        return False
    basename = os.path.basename(path)
    if any(fnmatch.fnmatch(basename, pat) for pat in cfg.test_exclude_names):
        return True
    if any(frag in path for frag in cfg.test_exclude_paths):
        return True
    return False


def scan_source_tree(
    source_dir: str,
    lang_hint: str | None,
    type_glob: str | None,
    include_tests: bool,
) -> dict[str, list[str]]:
    """Single-pass directory scan: detect languages AND collect files per language.

    Returns {lang_name: [file_paths]} for every detected language.
    Avoids the prior triple-walk (detect_languages + find_source_files × N).
    """
    # Explicit language → scan only for that language's globs
    if lang_hint:
        target_langs = [_resolve_language(lang_hint)]
    elif type_glob:
        target_langs = []
        for g in type_glob.split(","):
            g = g.strip()
            for lang, cfg in LANGS.items():
                if any(fnmatch.fnmatch(g, pat) or g == pat for pat in cfg.globs):
                    target_langs.append(lang)
        if not target_langs:
            target_langs = list(LANGS.keys())
    else:
        target_langs = list(LANGS.keys())

    # Build extension → language mapping for O(1) lookup
    ext_to_lang: dict[str, str] = {}
    for lang in target_langs:
        cfg = LANGS.get(lang)
        if cfg is None:
            continue
        for g in cfg.globs:
            # Convert glob like "*.py" to extension ".py"
            if g.startswith("*."):
                ext_to_lang[g[1:]] = lang  # ".py" → "python"

    files_by_lang: dict[str, list[str]] = {lang: [] for lang in target_langs if lang in LANGS}

    for root, _, files in os.walk(source_dir):
        for fname in files:
            # O(1) extension lookup
            dot_pos = fname.rfind(".")
            if dot_pos < 0:
                continue
            ext = fname[dot_pos:]
            lang = ext_to_lang.get(ext)
            if lang is None:
                continue
            full = os.path.join(root, fname)
            cfg = LANGS[lang]
            if _should_skip_test_file(full, cfg, include_tests):
                continue
            files_by_lang[lang].append(full)

    # Sort file lists for determinism, drop empty languages
    return {lang: sorted(paths) for lang, paths in files_by_lang.items() if paths}


def extract_function_name(line: str, cfg: LanguageConfig) -> str | None:
    for pat in cfg.name_extractors:
        m = re.search(pat, line)
        if m:
            name = m.group(1)
            if name and name not in _KEYWORD_BLOCKLIST:
                return name
    return None


def classify_export_type(line: str, cfg: LanguageConfig) -> str:
    if cfg.name == "typescript":
        if re.match(r"^\s*export\s+default\b", line):
            return "default"
        if re.match(r"^\s*export\b", line):
            return "named"
        if re.match(r"^\s*(public|private|protected)\b", line):
            return "method"
        return "internal"
    if cfg.name == "python":
        # Indented def => method
        if re.match(r"^\s{4,}(async\s+)?def\b", line):
            return "method"
        if re.match(r"^(async\s+)?def\s+_[^_]", line):
            return "internal"
        return "module_level"
    if cfg.name == "go":
        if re.match(r"^func\s+\(", line):
            return "method"
        m = re.search(r"func\s+(\w+)", line)
        if m and m.group(1)[:1].isupper():
            return "named"
        return "internal"
    if cfg.name == "rust":
        if line.startswith(" ") or line.startswith("\t"):
            return "method"
        if re.match(r"^pub\b", line):
            return "named"
        return "internal"
    if cfg.name == "java":
        if re.search(r"\bpublic\b", line):
            return "named"
        if re.search(r"\b(private|protected)\b", line):
            return "internal"
        return "method"
    return "internal"


def extract_for_language(
    cfg: LanguageConfig,
    source_dir: str,
    file_paths: list[str],
    context_lines: int,
) -> list[dict]:
    """Extract functions from a pre-scanned list of files for one language."""
    results: list[dict] = []
    combined_pattern = re.compile("|".join(f"(?:{p})" for p in cfg.patterns))

    for path in file_paths:
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
        except OSError:
            continue

        rel = os.path.relpath(path, source_dir)
        total = len(lines)

        # Find matching line indices
        match_indices: list[int] = []
        for i, line in enumerate(lines):
            if combined_pattern.search(line):
                match_indices.append(i)

        for idx, line_idx in enumerate(match_indices):
            line = lines[line_idx]
            name = extract_function_name(line, cfg)
            if not name:
                continue

            # end_line = next match line - 1, or end of file
            if idx + 1 < len(match_indices):
                end_line = match_indices[idx + 1]
            else:
                end_line = total
            body_lines = max(1, end_line - line_idx)

            ctx_start = max(0, line_idx - context_lines)
            ctx_end = min(total, line_idx + context_lines + 1)
            context_text = "".join(lines[ctx_start:ctx_end])

            signature = line.strip()

            results.append({
                "file": rel,
                "name": name,
                "qualified_name": name,
                "line": line_idx + 1,
                "end_line": end_line,
                "signature": signature,
                "params": [],
                "return_type": None,
                "decorators": [],
                "docstring": None,
                "body_lines": body_lines,
                "cyclomatic_complexity": None,
                "ast_fingerprint": None,
                "token_sequence": None,
                "export_type": classify_export_type(line, cfg),
                "language": cfg.name,
                "context": context_text,
            })
    return results


def main() -> None:
    p = argparse.ArgumentParser(description="Multi-language regex function extractor")
    p.add_argument("source_dir", help="Source directory to scan")
    p.add_argument("-o", "--output", help="Output file (default: stdout)")
    p.add_argument("-c", "--context", type=int, default=3,
                   help="Lines of context around each match (default: 3)")
    p.add_argument("-t", "--type", dest="type_glob",
                   help="File glob filter (e.g. '*.py')")
    p.add_argument("--lang", help="Language hint: typescript/python/go/rust/java/kotlin")
    p.add_argument("--include-tests", action="store_true",
                   help="Include test files (excluded by default)")
    args = p.parse_args()

    if not os.path.isdir(args.source_dir):
        print(f"Error: directory not found: {args.source_dir}", file=sys.stderr)
        sys.exit(1)

    # Single-pass scan: detect languages AND collect files simultaneously
    files_by_lang = scan_source_tree(
        args.source_dir, args.lang, args.type_glob, args.include_tests,
    )
    all_results: list[dict] = []
    for lang, file_paths in files_by_lang.items():
        cfg = LANGS.get(lang)
        if cfg is None:
            continue
        print(f"Scanning for {cfg.name} functions...", file=sys.stderr)
        results = extract_for_language(cfg, args.source_dir, file_paths, args.context)
        all_results.extend(results)

    # Sort for determinism
    all_results.sort(key=lambda r: (r["file"], r["line"]))

    output_text = json.dumps(all_results, indent=2)
    if args.output:
        Path(args.output).write_text(output_text)
        print(f"Wrote {len(all_results)} function(s) to {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(output_text + "\n")

    print(f"Extracted {len(all_results)} function(s) total.", file=sys.stderr)


if __name__ == "__main__":
    main()
