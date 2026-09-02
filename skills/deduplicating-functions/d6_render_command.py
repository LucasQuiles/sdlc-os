#!/usr/bin/env python3
"""Render (or exec) the reviewed D6 admission launch from the launched tree's
own d6_admitted_command.json.

The record file is the reviewed artifact (round9 events 57/58); this renderer
is the only sanctioned way to turn it into a runnable command. Guarantees
(review rounds 1-3):

- The record and every required file are realpath-CONFINED to the launched
  tree: a symlink pointing outside {TREE} refuses (round 3, BLOCKING).
- The renderer itself verifies `git -C {TREE} rev-parse HEAD` equals
  --head-pin BEFORE any chain is emitted, so record content is bound to the
  owner-named head at render time, not just at wrapper time (round 3,
  consolidating fix: a drifted record cannot select its own judge).
- The rendered OUTER chain is structurally pinned in code — wrapper path,
  tree, pin, admission dir, both '--' separators, the monitor invocation —
  so a record cannot point at a wrapper or monitor outside the gated tree.
- Placeholder multiplicities are pinned exactly ({PYTHON} 3 including the
  env pin, {TREE} 3, {ADMISSION_DIR} 3, {HEAD_PIN} 1); unknown or malformed
  {...} tokens refuse before substitution, and nothing brace-like survives
  after it.
- env pins: ADMISSION_MAX_LOAD1=8.0 and ADMISSION_PYTHON={PYTHON} — the
  interpreter that runs the wrapper's canonical preflight is pinned to the
  same python the chain uses. DEDUP_DETECTOR_TIMEOUT_S is inherited
  (env-only knob, bounded by MAX_DETECTOR_TIMEOUT_S in run_pipeline.py).

Sanctioned consumption:
  --exec        replaces this process with the rendered chain via execvpe,
                applying the env pins OVER the caller's environment and
                preserving the wrapper's exit-code contract (70-75)
                natively. Recommended.
  (stream mode) NUL-TERMINATED records on stdout (every argument ends with
                NUL) for `while IFS= read -r -d '' a`. Do NOT use xargs -0
                (collapses the wrapper's exit codes) or $(...) (strips
                NULs). Stream mode refuses if the caller's environment
                conflicts with a pinned value it cannot enforce.

Both modes print `expected_command_sha256 <hex>` to stderr — sha256 of the
NUL-joined os.fsencode'd pipeline argv, the monitor receipt's exact
command_sha256 formula (post-hoc provenance).

Usage:
  d6_render_command.py --python P --tree T --admission-dir D --head-pin H [--exec]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys

PLACEHOLDER_ANY = re.compile(r"\{[^{}]*\}")
EXPECTED_MULTIPLICITY = {
    "{PYTHON}": 3, "{TREE}": 3, "{ADMISSION_DIR}": 3, "{HEAD_PIN}": 1,
}
TREE_REQUIRED_FILES = (
    "run_pipeline.py", "safety.py", "d6_pressure_monitor.py",
    "admission_wrapper.sh", "d6_admitted_command.json",
)
RECORD_BASENAME = "d6_admitted_command.json"


class RenderError(ValueError):
    pass


def _confined(tree_real: str, name: str) -> str:
    """The file's realpath must live directly inside the tree's realpath."""
    rp = os.path.realpath(os.path.join(tree_real, name))
    if os.path.dirname(rp) != tree_real:
        raise RenderError(
            f"{name} resolves outside the launched tree ({rp}); "
            "symlinked launch inputs are refused")
    if not os.path.isfile(rp):
        raise RenderError(f"--tree is not the skill directory; missing {name}")
    return rp


def load_record(tree_real: str) -> dict:
    with open(_confined(tree_real, RECORD_BASENAME), encoding="utf-8") as f:
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


def _head_of(tree: str) -> str:
    try:
        proc = subprocess.run(
            ["git", "-C", tree, "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise RenderError(f"cannot determine the tree's HEAD: {error!r}")
    if proc.returncode != 0:
        raise RenderError(
            "cannot determine the tree's HEAD: " + proc.stderr.strip())
    return proc.stdout.strip()


def render(python: str, tree: str, admission_dir: str, head_pin: str,
           ) -> tuple[list[str], dict[str, str], str]:
    """Return (full outer argv, rendered env pins, expected pipeline sha256)."""
    for name, value in (("--python", python), ("--tree", tree),
                        ("--admission-dir", admission_dir),
                        ("--head-pin", head_pin)):
        if not value or any(c in value for c in "\0{}"):
            raise RenderError(
                f"{name} must be a non-empty string without NUL or braces")
    if not os.path.isabs(tree) or not os.path.isabs(admission_dir):
        raise RenderError("--tree and --admission-dir must be absolute paths")
    real_tree = os.path.realpath(tree)
    for required in TREE_REQUIRED_FILES:
        _confined(real_tree, required)
    if os.path.realpath(admission_dir).startswith(real_tree + os.sep):
        raise RenderError("--admission-dir must not live inside --tree "
                          "(run artifacts would dirty the head-pinned tree)")
    head = _head_of(tree)
    if head != head_pin:
        raise RenderError(
            f"--head-pin {head_pin} does not match the tree's HEAD {head}; "
            "the record can only be rendered at the owner-named head")

    doc = load_record(real_tree)
    chain = doc["launch_template"]["outer_argv"] + doc["argv"]
    env_items = sorted(doc["env"].items())
    tokens_scope = chain + [v for _, v in env_items]
    for text in tokens_scope:
        for token in PLACEHOLDER_ANY.findall(text):
            if token not in EXPECTED_MULTIPLICITY:
                raise RenderError(f"unknown placeholder {token} in {text!r}")
    joined = "\0".join(tokens_scope)
    for ph, expected in EXPECTED_MULTIPLICITY.items():
        got = joined.count(ph)
        if got != expected:
            raise RenderError(
                f"placeholder {ph} appears {got}x, record requires {expected}x")

    subs = {"{PYTHON}": python, "{TREE}": tree,
            "{ADMISSION_DIR}": admission_dir, "{HEAD_PIN}": head_pin}

    def _sub(text: str) -> str:
        for ph, value in subs.items():
            text = text.replace(ph, value)
        if PLACEHOLDER_ANY.search(text):
            raise RenderError(f"unsubstituted placeholder survives in {text!r}")
        return text

    rendered = [_sub(a) for a in chain]
    env = {k: _sub(v) for k, v in doc["env"].items()}

    expected_outer = [
        "/bin/bash", os.path.join(tree, "admission_wrapper.sh"), tree,
        head_pin, admission_dir, "--", python, "d6_pressure_monitor.py",
        "--receipt", os.path.join(admission_dir, "monitor.json"), "--",
    ]
    if rendered[:len(expected_outer)] != expected_outer:
        raise RenderError(
            "rendered outer chain deviates from the reviewed structure "
            f"(got {rendered[:len(expected_outer)]!r}); a record cannot "
            "select a wrapper or monitor outside the gated tree")

    pipeline_argv = rendered[len(expected_outer):]
    digest = hashlib.sha256(
        b"\0".join(os.fsencode(a) for a in pipeline_argv)).hexdigest()
    return rendered, env, digest


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
    try:
        raise SystemExit(main(sys.argv[1:]))
    except RenderError as error:
        sys.stderr.write(f"d6-render: {error}\n")
        raise SystemExit(1)
