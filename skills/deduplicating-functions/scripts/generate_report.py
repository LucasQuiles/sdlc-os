#!/usr/bin/env python3
"""Streaming markdown report generator for merged duplicate-detection results.

Replaces the jq-based generate-report-enhanced.sh, which re-parsed the whole
merged document once per section (a 2.05 GB input produced a 22.7 GB jq
footprint on 2026-08-22). This generator reads pairs exactly once with a
bounded buffer, keeps at most --max-rows-per-section rows per section, states
omissions explicitly, takes totals from the summary, and writes atomically.

Input forms (first positional argument):
  <dir>                 new layout: <dir>/pairs.jsonl + <dir>/summary.json
  <file>.jsonl          pairs only (summary.json beside it if present)
  merged-results.json   legacy {"pairs": [...], "summary": {...}} or bare array
Output: markdown at the second positional argument (default duplicates-report.md).
Exit: 0 ok; 1 missing/malformed input or write failure; 2 usage.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Any, Iterator

_LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib")
if _LIB not in sys.path:
    sys.path.insert(0, _LIB)
import jsonstream  # noqa: E402

DEFAULT_MAX_ROWS = 500
ARROW = "↔"

SECTIONS = ("ACTIONABLE", "HIGH", "MEDIUM", "LOW")


def _s(v: Any) -> str:
    """jq-style string interpolation: null → 'null', numbers as JSON, strings raw."""
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return json.dumps(v)
    if isinstance(v, str):
        return v
    return json.dumps(v)


def _get(d: Any, *keys: str) -> Any:
    for k in keys:
        if not isinstance(d, dict):
            return None
        d = d.get(k)
    return d


def _num_or_zero(v: Any) -> str:
    return "0" if v is None else _s(v)


def _is_actionable(p: dict) -> bool:
    return p.get("confidence") == "HIGH" and p.get("clone_type") in (
        "Type 1 (exact clone)", "Type 2 (renamed clone)")


# ---------------------------------------------------------------------------
# Section renderers (byte-compatible with the legacy jq templates)
# ---------------------------------------------------------------------------

def _summary_block(summary: dict) -> str:
    strategies = summary.get("strategies_used")
    if strategies is None:
        raise ValueError("summary.strategies_used is missing (cannot iterate over null)")
    return (
        "## Summary\n\n"
        "| Metric | Value |\n"
        "|--------|-------|\n"
        f"| Total duplicate pairs | {_s(summary.get('total_pairs'))} |\n"
        f"| HIGH confidence | {_num_or_zero(_get(summary, 'by_confidence', 'HIGH'))} |\n"
        f"| MEDIUM confidence | {_num_or_zero(_get(summary, 'by_confidence', 'MEDIUM'))} |\n"
        f"| LOW confidence | {_num_or_zero(_get(summary, 'by_confidence', 'LOW'))} |\n"
        f"| Multi-signal pairs (2+) | {_s(summary.get('multi_signal_pairs'))} |\n"
        f"| Defense depth pairs (3+) | {_s(summary.get('defense_depth_pairs'))} |\n"
        f"| Detection strategies used | {', '.join(str(x) for x in strategies)} |\n"
    )


def _count_table(mapping: Any, header: str, dashes: str) -> str:
    if not isinstance(mapping, dict):
        raise ValueError(f"summary.{header} is not an object")
    rows = sorted(mapping.items(), key=lambda kv: -(kv[1] if isinstance(kv[1], (int, float)) else 0))
    out = f"| {header} | Count |\n|{dashes}|-------|\n"
    out += "\n".join(f"| {k} | {_s(v)} |" for k, v in rows)
    return out


def _actionable_row(p: dict) -> str:
    return (f"| `{_s(_get(p, 'func_a', 'name'))}` / `{_s(_get(p, 'func_b', 'name'))}` | "
            f"{_s(p.get('composite_score'))} | {_s(p.get('num_strategies'))} | "
            f"`{_s(_get(p, 'func_a', 'file'))}:{_s(_get(p, 'func_a', 'line'))}` | "
            f"`{_s(_get(p, 'func_b', 'file'))}:{_s(_get(p, 'func_b', 'line'))}` |")


def _signals_lines(p: dict, fmt: str, sep: str) -> str:
    strategies = p.get("strategies")
    if not isinstance(strategies, dict):
        raise ValueError("pair.strategies is not an object (cannot iterate over null)")
    return sep.join(fmt.format(k=_s(k), v=_s(v)) for k, v in strategies.items())


def _high_entry(p: dict) -> str:
    a, b = p.get("func_a"), p.get("func_b")
    rec = p.get("recommendation")
    return (
        f"### {_s(_get(a, 'name'))} {ARROW} {_s(_get(b, 'name'))}\n\n"
        "| | Function A | Function B |\n"
        "|---|-----------|------------|\n"
        f"| **Name** | `{_s(_get(a, 'name'))}` | `{_s(_get(b, 'name'))}` |\n"
        f"| **File** | `{_s(_get(a, 'file'))}:{_s(_get(a, 'line'))}` | `{_s(_get(b, 'file'))}:{_s(_get(b, 'line'))}` |\n"
        "\n"
        f"**Clone Type:** {_s(p.get('clone_type'))}\n\n"
        f"**Composite Score:** {_s(p.get('composite_score'))} from {_s(p.get('num_strategies'))} strategies\n\n"
        "**Detection Signals:**\n\n"
        + _signals_lines(p, "- {k}: {v}", "\n")
        + "\n\n"
        f"**Recommendation:** {_s(_get(rec, 'action'))} ({_s(_get(rec, 'urgency'))}) — {_s(_get(rec, 'reason'))}\n\n"
        "---\n"
    )


def _medium_entry(p: dict) -> str:
    a, b = p.get("func_a"), p.get("func_b")
    rec = p.get("recommendation")
    return (
        f"### {_s(_get(a, 'name'))} {ARROW} {_s(_get(b, 'name'))}\n\n"
        f"- **A:** `{_s(_get(a, 'name'))}` in `{_s(_get(a, 'file'))}:{_s(_get(a, 'line'))}`\n"
        f"- **B:** `{_s(_get(b, 'name'))}` in `{_s(_get(b, 'file'))}:{_s(_get(b, 'line'))}`\n"
        f"- **Score:** {_s(p.get('composite_score'))} from {_s(p.get('num_strategies'))} strategy(ies)\n"
        f"- **Clone Type:** {_s(p.get('clone_type'))}\n"
        "- **Signals:** " + _signals_lines(p, "{k}={v}", ", ") + "\n"
        f"- **Action:** {_s(_get(rec, 'action'))} — {_s(_get(rec, 'reason'))}\n\n"
        "---\n"
    )


def _low_entry(p: dict) -> str:
    a, b = p.get("func_a"), p.get("func_b")
    return (
        f"- `{_s(_get(a, 'name'))}` ({_s(_get(a, 'file'))}:{_s(_get(a, 'line'))}) {ARROW} "
        f"`{_s(_get(b, 'name'))}` ({_s(_get(b, 'file'))}:{_s(_get(b, 'line'))}) — score "
        f"{_s(p.get('composite_score'))}, signals: " + _signals_lines(p, "{k}", ", ")
    )


# ---------------------------------------------------------------------------
# Input resolution
# ---------------------------------------------------------------------------

def _resolve_input(path: str, max_buffer_bytes: int) -> tuple[Iterator[dict], dict | None, str]:
    """Return (pairs iterator, summary-or-None, description)."""
    chunk = max(4096, min(jsonstream.DEFAULT_CHUNK_SIZE, max_buffer_bytes // 4))
    max_elem = max(4096, max_buffer_bytes)
    if os.path.isdir(path):
        pairs_path = os.path.join(path, "pairs.jsonl")
        summary_path = os.path.join(path, "summary.json")
        if not os.path.isfile(pairs_path):
            raise FileNotFoundError(f"{pairs_path} not found")
        summary = json.loads(open(summary_path, encoding="utf-8").read()) if os.path.isfile(summary_path) else None
        return jsonstream.iter_jsonl(pairs_path), summary, pairs_path
    if not os.path.isfile(path):
        raise FileNotFoundError(f"file not found: {path}")
    fmt = jsonstream.detect_format(path)
    if fmt == "jsonl":
        summary_path = os.path.join(os.path.dirname(path) or ".", "summary.json")
        summary = json.loads(open(summary_path, encoding="utf-8").read()) if os.path.isfile(summary_path) else None
        return jsonstream.iter_jsonl(path), summary, path
    if fmt == "array":
        return jsonstream.iter_json_array(path, chunk_size=chunk, max_element_bytes=max_elem), None, path
    if fmt == "object":
        try:
            summary = jsonstream.load_object_member(path, "summary", chunk_size=chunk, max_bytes=max_elem)
        except jsonstream.JSONStreamError as exc:
            if "has no member" in str(exc):
                summary = None
            else:
                raise
        return jsonstream.iter_object_member_array(path, "pairs", chunk_size=chunk,
                                                   max_element_bytes=max_elem), summary, path
    raise jsonstream.JSONStreamError(f"{path}: empty input")


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def render(pairs: Iterator[dict], summary: dict | None, max_rows: int, now: str | None = None) -> tuple[str, dict]:
    has_summary = isinstance(summary, dict)
    kept: dict[str, list[str]] = {s: [] for s in SECTIONS}
    seen: dict[str, int] = {s: 0 for s in SECTIONS}
    for p in pairs:
        if not isinstance(p, dict):
            raise ValueError("pair record is not an object")
        conf = p.get("confidence")
        if _is_actionable(p):
            seen["ACTIONABLE"] += 1
            if len(kept["ACTIONABLE"]) < max_rows:
                kept["ACTIONABLE"].append(_actionable_row(p))
        if conf in ("HIGH", "MEDIUM", "LOW"):
            seen[conf] += 1
            if len(kept[conf]) < max_rows:
                kept[conf].append({"HIGH": _high_entry, "MEDIUM": _medium_entry, "LOW": _low_entry}[conf](p))

    def omitted(section: str, label: str) -> str:
        extra = seen[section] - len(kept[section])
        return f"\n_{extra} additional {label} pair(s) omitted (cap {max_rows})_\n" if extra > 0 else ""

    out: list[str] = []
    w = out.append
    w("# Duplicate Functions Report\n")
    w("\n")
    w("_Multi-Signal Detection with Defense in Depth_\n")
    w("\n")
    w(f"Generated: {now or time.strftime('%Y-%m-%d %H:%M')}\n")
    w("\n")
    if has_summary:
        w(_summary_block(summary) + "\n")
    w("\n")
    w("### Clone Type Distribution\n")
    w("\n")
    if has_summary:
        w(_count_table(summary.get("by_clone_type", {}), "Clone Type", "-----------") + "\n")
    w("\n")
    w("### Action Summary\n")
    w("\n")
    if has_summary:
        w(_count_table(summary.get("by_action", {}), "Action", "--------") + "\n")
    w("\n")
    w("---\n")
    w("\n")
    w("## Actionable Tier\n")
    w("\n")
    w("> Type 1 (exact clone) and Type 2 (renamed clone) pairs at HIGH confidence.\n")
    w("> These are the highest-priority consolidation targets.\n")
    w("\n")
    if not kept["ACTIONABLE"]:
        w("> No actionable pairs found.\n\n")
    else:
        w("| Pair | Score | Strategies | File A | File B |\n"
          "|------|-------|------------|--------|--------|\n"
          + "\n".join(kept["ACTIONABLE"]) + "\n\n")
        w(omitted("ACTIONABLE", "actionable"))
    w("\n")
    w("---\n")
    w("\n")
    w("## HIGH Confidence Duplicates\n")
    w("\n")
    w("> These pairs were flagged by multiple independent detection strategies.\n")
    w("> Consolidate them — the evidence is strong.\n")
    w("\n")
    if not kept["HIGH"]:
        w("_No HIGH confidence duplicates found._\n\n")
    else:
        w("\n".join(kept["HIGH"]) + "\n")
        w(omitted("HIGH", "HIGH"))
    w("\n")
    w("## MEDIUM Confidence Duplicates\n")
    w("\n")
    w("> These pairs show moderate duplicate signals. Investigate before consolidating.\n")
    w("\n")
    if not kept["MEDIUM"]:
        w("_No MEDIUM confidence duplicates found._\n\n")
    else:
        w("\n".join(kept["MEDIUM"]) + "\n")
        w(omitted("MEDIUM", "MEDIUM"))
    w("\n")
    w("## LOW Confidence (Review)\n")
    w("\n")
    w("> Weak signals — review if time permits.\n")
    w("\n")
    if not kept["LOW"]:
        w("_No LOW confidence duplicates found._\n\n")
    else:
        w("\n".join(kept["LOW"]) + "\n")
        w(omitted("LOW", "LOW"))
    w("\n")
    w("\n")
    w("---\n")
    w("\n")
    w("_Report generated by multi-signal duplicate detection pipeline._\n")
    w("_Clone types follow the standard taxonomy: Type 1 (exact), Type 2 (renamed), Type 3 (near-miss), Type 4 (semantic)._\n")
    stats = {"seen": seen, "kept": {k: len(v) for k, v in kept.items()}, "has_summary": has_summary}
    return "".join(out), stats


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="generate-report-enhanced",
        description="Generate the enhanced markdown report from merged duplicate results (streaming).")
    ap.add_argument("input", help="merge dir, pairs.jsonl, or legacy merged-results.json")
    ap.add_argument("output", nargs="?", default="duplicates-report.md", help="markdown output path")
    ap.add_argument("--max-rows-per-section", type=int, default=DEFAULT_MAX_ROWS,
                    help="rows kept per section; omissions are stated explicitly (default: %(default)s)")
    ap.add_argument("--max-buffer-bytes", type=int, default=jsonstream.DEFAULT_MAX_ELEMENT_BYTES,
                    help="bound on the parse buffer / one element (default: %(default)s)")
    args = ap.parse_args(argv)
    if args.max_rows_per_section <= 0 or args.max_buffer_bytes <= 0:
        print("Error: --max-rows-per-section and --max-buffer-bytes must be finite positive integers",
              file=sys.stderr)
        return 2
    try:
        pairs, summary, desc = _resolve_input(args.input, args.max_buffer_bytes)
    except FileNotFoundError as exc:
        print(f"Error: file not found: {exc}", file=sys.stderr)
        return 1
    except (jsonstream.JSONStreamError, OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    try:
        text, stats = render(pairs, summary, args.max_rows_per_section)
    except (jsonstream.JSONStreamError, OSError, ValueError, TypeError, KeyError) as exc:
        print(f"Error: {desc}: {exc}", file=sys.stderr)
        return 1
    try:
        jsonstream.atomic_write_text(args.output, lambda fh: fh.write(text))
    except OSError as exc:
        print(f"Error: cannot write {args.output}: {exc}", file=sys.stderr)
        return 1
    print(f"Report generated: {args.output}", file=sys.stderr)
    if stats["has_summary"]:
        bc = summary.get("by_confidence", {}) if isinstance(summary, dict) else {}
        print(f"  HIGH: {bc.get('HIGH', 0)} | MEDIUM: {bc.get('MEDIUM', 0)} | LOW: {bc.get('LOW', 0)} | "
              f"Multi-signal: {_s(summary.get('multi_signal_pairs'))}", file=sys.stderr)
    omitted_total = sum(stats["seen"][s] - stats["kept"][s] for s in SECTIONS)
    if omitted_total:
        print(f"  {omitted_total} row(s) omitted across sections (cap {args.max_rows_per_section})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
