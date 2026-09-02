#!/usr/bin/env python3
"""Render (or exec) the reviewed D6 admission launch from the launched tree's
own d6_admitted_command.json.

The record file is the reviewed artifact (round9 events 57/58); this renderer
is the only sanctioned way to turn it into a runnable command. The record is
ALWAYS read from {TREE}/d6_admitted_command.json — the same tree the wrapper
head-pins and cleanliness-checks — so record content cannot come from an
ungated checkout (review round 2, finding 1). Placeholder multiplicities in
the record are pinned exactly: {PYTHON} 2, {TREE} 3, {ADMISSION_DIR} 3,
{HEAD_PIN} 1.

Sanctioned consumption (review round 2, findings 2-4):
  --exec        replaces this process with the rendered chain via execvpe,
                applying the record's env pin OVER the caller's environment
                and preserving the wrapper's exit-code contract (70-75)
                natively. This is the recommended path.
  (stream mode) without --exec, the chain is written to stdout as
                NUL-TERMINATED records (every argument ends with NUL,
                find -print0 convention) for
                `while IFS= read -r -d '' a; do argv+=("$a"); done`.
                Do NOT use xargs -0 (it collapses the wrapper's exit codes)
                or $(...) (it strips NULs). Stream mode REFUSES to render if
                the caller's environment already carries a conflicting value
                for a pinned env var, since stdout cannot enforce the pin.

Both modes print `expected_command_sha256 <hex>` to stderr — the sha256 of
the NUL-joined pipeline argv, which must equal the monitor receipt's
command_sha256 after the run (post-hoc provenance).

Usage:
  d6_render_command.py --python P --tree T --admission-dir D --head-pin H [--exec]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys

PLACEHOLDER_RE = re.compile(r"\{[A-Z_]+\}")
EXPECTED_MULTIPLICITY = {
    "{PYTHON}": 2, "{TREE}": 3, "{ADMISSION_DIR}": 3, "{HEAD_PIN}": 1,
}
TREE_REQUIRED_FILES = (
    "run_pipeline.py", "safety.py", "d6_pressure_monitor.py",
    "admission_wrapper.sh", "d6_admitted_command.json",
)
RECORD_BASENAME = "d6_admitted_command.json"


class RenderError(ValueError):
    pass


def load_record(tree: str) -> dict:
    path = os.path.join(tree, RECORD_BASENAME)
    with open(path, encoding="utf-8") as f:
        doc = json.load(f)
    if doc.get("record") != "d6-admitted-command":
        raise RenderError("wrong record type")
    try:
        outer = doc["launch_template"]["outer_argv"]
        inner = doc["argv"]
        env = doc["env"]
    except KeyError as missing:
        raise RenderError(f"record is missing required key {missing}") from None
    if not (isinstance(outer, list) and isinstance(inner, list)
            and isinstance(env, dict)):
        raise RenderError("record sections have wrong types")
    if not all(isinstance(a, str) for a in outer + inner):
        raise RenderError("argv elements must be strings")
    if not all(isinstance(k, str) and isinstance(v, str)
               for k, v in env.items()):
        raise RenderError("env entries must be strings")
    return doc


def render(python: str, tree: str, admission_dir: str, head_pin: str,
           ) -> tuple[list[str], dict[str, str], str]:
    """Return (full outer argv, env pins, expected pipeline-argv sha256).

    The record is read from tree/d6_admitted_command.json, binding record
    content to the same tree the wrapper gates.
    """
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
    real_tree = os.path.realpath(tree)
    if os.path.realpath(admission_dir).startswith(real_tree + os.sep):
        raise RenderError("--admission-dir must not live inside --tree "
                          "(run artifacts would dirty the head-pinned tree)")

    doc = load_record(tree)
    chain = doc["launch_template"]["outer_argv"] + doc["argv"]
    for arg in chain:
        for token in PLACEHOLDER_RE.findall(arg):
            if token not in EXPECTED_MULTIPLICITY:
                raise RenderError(f"unknown placeholder {token} in {arg!r}")
    joined = "\0".join(chain)
    for ph, expected in EXPECTED_MULTIPLICITY.items():
        got = joined.count(ph)
        if got != expected:
            raise RenderError(
                f"placeholder {ph} appears {got}x, record requires {expected}x")

    subs = {"{PYTHON}": python, "{TREE}": tree,
            "{ADMISSION_DIR}": admission_dir, "{HEAD_PIN}": head_pin}
    rendered = []
    for arg in chain:
        for ph, value in subs.items():
            arg = arg.replace(ph, value)
        rendered.append(arg)

    inner_start = len(doc["launch_template"]["outer_argv"])
    pipeline_argv = rendered[inner_start:]
    digest = hashlib.sha256(
        b"\0".join(a.encode() for a in pipeline_argv)).hexdigest()
    return rendered, dict(doc["env"]), digest


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--python", required=True)
    ap.add_argument("--tree", required=True)
    ap.add_argument("--admission-dir", required=True)
    ap.add_argument("--head-pin", required=True)
    ap.add_argument("--exec", dest="exec_mode", action="store_true")
    args = ap.parse_args(argv)
    rendered, env, digest = render(args.python, args.tree,
                                   args.admission_dir, args.head_pin)
    sys.stderr.write(f"expected_command_sha256 {digest}\n")
    if args.exec_mode:
        sys.stderr.flush()
        os.execvpe(rendered[0], rendered, {**os.environ, **env})
        raise AssertionError("unreachable")  # pragma: no cover
    for key, value in env.items():
        held = os.environ.get(key)
        if held is not None and held != value:
            raise RenderError(
                f"stream mode cannot enforce the env pin: {key} is already "
                f"{held!r} in the environment, record pins {value!r}; "
                "use --exec or clear the variable")
        sys.stderr.write(f"env {key}={value}\n")
    sys.stdout.write("".join(a + "\0" for a in rendered))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
