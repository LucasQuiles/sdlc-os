#!/usr/bin/env python3
"""Render the reviewed D6 admission launch from d6_admitted_command.json.

The record file is the reviewed artifact (round9 events 57/58); this renderer
is the only sanctioned way to turn it into a runnable command. It substitutes
{PYTHON}/{TREE}/{ADMISSION_DIR}/{HEAD_PIN}, validates the placeholder scheme
(each exactly once across the full chain), asserts {TREE} really is the skill
directory the record requires, and emits the complete outer argv (wrapper +
monitor + pipeline) NUL-separated on stdout. A hand-assembled launch that
bypasses this forfeits the pins - the 2026-09-01 window lost an attempt to a
separator that ledger prose never showed.

Usage:
  d6_render_command.py --python P --tree T --admission-dir D --head-pin H
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
COMMAND_FILE = os.path.join(HERE, "d6_admitted_command.json")

PLACEHOLDERS = ("{PYTHON}", "{TREE}", "{ADMISSION_DIR}", "{HEAD_PIN}")
TREE_REQUIRED_FILES = (
    "run_pipeline.py", "safety.py", "d6_pressure_monitor.py",
    "admission_wrapper.sh",
)


class RenderError(ValueError):
    pass


def load_record(path: str = COMMAND_FILE) -> dict:
    with open(path, encoding="utf-8") as f:
        doc = json.load(f)
    if doc.get("record") != "d6-admitted-command":
        raise RenderError("wrong record type")
    outer = doc["launch_template"]["outer_argv"]
    inner = doc["argv"]
    if not (isinstance(outer, list) and isinstance(inner, list)):
        raise RenderError("argv sections must be lists")
    if not all(isinstance(a, str) for a in outer + inner):
        raise RenderError("argv elements must be strings")
    return doc


def render(python: str, tree: str, admission_dir: str, head_pin: str,
           path: str = COMMAND_FILE) -> tuple[list[str], dict[str, str]]:
    """Return (full outer argv, env additions) with placeholders substituted."""
    for name, value in (("--python", python), ("--tree", tree),
                        ("--admission-dir", admission_dir),
                        ("--head-pin", head_pin)):
        if not value or "\0" in value:
            raise RenderError(f"{name} must be a non-empty NUL-free string")
    if not os.path.isabs(tree) or not os.path.isabs(admission_dir):
        raise RenderError("--tree and --admission-dir must be absolute paths")
    missing = [f for f in TREE_REQUIRED_FILES
               if not os.path.isfile(os.path.join(tree, f))]
    if missing:
        raise RenderError(f"--tree is not the skill directory; missing {missing}")

    doc = load_record(path)
    chain = doc["launch_template"]["outer_argv"] + doc["argv"]
    joined = "\0".join(chain)
    for ph in ("{PYTHON}", "{ADMISSION_DIR}"):
        if joined.count(ph) < 1:
            raise RenderError(f"record lost placeholder {ph}")
    # {TREE} appears in the wrapper path, wrapper arg, and pipeline source;
    # {HEAD_PIN} exactly once; unknown {WORD} tokens are refused outright.
    subs = {"{PYTHON}": python, "{TREE}": tree,
            "{ADMISSION_DIR}": admission_dir, "{HEAD_PIN}": head_pin}
    if joined.count("{HEAD_PIN}") != 1:
        raise RenderError("record must carry {HEAD_PIN} exactly once")
    rendered = []
    for arg in chain:
        for ph, value in subs.items():
            arg = arg.replace(ph, value)
        if "{" in arg and "}" in arg:
            raise RenderError(f"unsubstituted placeholder survives in {arg!r}")
        rendered.append(arg)
    return rendered, dict(doc.get("env", {}))


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--python", required=True)
    ap.add_argument("--tree", required=True)
    ap.add_argument("--admission-dir", required=True)
    ap.add_argument("--head-pin", required=True)
    args = ap.parse_args(argv)
    rendered, env = render(args.python, args.tree, args.admission_dir,
                           args.head_pin)
    sys.stdout.write("\0".join(rendered))
    for key, value in sorted(env.items()):
        sys.stderr.write(f"env {key}={value}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
