#!/usr/bin/env python3
"""Render (or exec) the reviewed D6 admission launch.

The record file d6_admitted_command.json is the reviewed artifact (round9
events 57/58) and this renderer is the only sanctioned way to turn it into a
runnable command. Guarantees (review rounds 1-4):

- CONTENT, not a label: after verifying `git rev-parse HEAD` equals
  --head-pin, EVERY launch input — the record, run_pipeline.py, safety.py,
  d6_pressure_monitor.py, admission_wrapper.sh, and this renderer itself —
  is compared byte-for-byte to its head-pinned blob, and any divergence
  refuses (catches update-index --assume-unchanged / --skip-worktree drift
  on the executables as well as the record, rounds 4-5 BLOCKING). The
  self-check catches an accidentally drifted or foreign renderer; a
  deliberately rewritten verifier cannot bootstrap trust in itself — that
  residual is the operator's checkout, owned by the head-pin grant.
- Independent oracle: every git call uses the system git at the absolute
  path /usr/bin/git (a PATH-earlier substitute cannot answer the checks,
  round 5 finding 2) under an environment stripped of GIT_* variables, and
  --exec strips GIT_* from the child environment too, so neither ambient
  variables nor PATH can redirect the renderer's checks or the wrapper's
  own head-pin and cleanliness gates.
- No-oracle structural pin: the blob's outer chain, pipeline argv, and env
  section must equal the reviewed templates in this file byte-for-byte
  BEFORE substitution — drift in the record refuses even if every git
  integrity mechanism has been defeated (defense-in-depth from the round-4
  risk register).
- The record and every required file are realpath-CONFINED to the launched
  tree (symlinked launch inputs refuse; a symlinked TREE itself is fine —
  it normalizes first).
- env pins ADMISSION_MAX_LOAD1=8.0 and ADMISSION_PYTHON={PYTHON}; --python
  must be an absolute path to an existing executable.

Sanctioned consumption:
  --exec        replaces this process with the rendered chain via execvpe,
                applying the env pins over the caller's environment (minus
                GIT_*) and preserving the wrapper's exit-code contract
                (70-75) natively. Recommended.
  (stream mode) NUL-TERMINATED records on stdout for
                `while IFS= read -r -d '' a`. Do NOT use xargs -0
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
GIT_BIN = "/usr/bin/git"
RECORD_BASENAME = "d6_admitted_command.json"
RENDERER_BASENAME = "d6_render_command.py"
TREE_REQUIRED_FILES = (
    "run_pipeline.py", "safety.py", "d6_pressure_monitor.py",
    "admission_wrapper.sh", RECORD_BASENAME, RENDERER_BASENAME,
)

# The reviewed launch chain (round9 events 57/58). The blob record must
# equal these templates byte-for-byte before substitution; the JSON file is
# the grant-facing artifact, this is the enforcement copy, and the tests pin
# their agreement.
EXPECTED_OUTER_TEMPLATE = [
    "/bin/bash",
    "{TREE}/admission_wrapper.sh",
    "{TREE}",
    "{HEAD_PIN}",
    "{ADMISSION_DIR}",
    "--",
    "{PYTHON}",
    "d6_pressure_monitor.py",
    "--receipt",
    "{ADMISSION_DIR}/monitor.json",
    "--",
]
EXPECTED_PIPELINE_TEMPLATE = [
    "{PYTHON}",
    "run_pipeline.py",
    "{TREE}",
    "-o",
    "{ADMISSION_DIR}/pipeline-output",
    "--strict",
    "--jobs", "2",
    "--resource-policy", "refuse",
    "--max-pairs", "200000",
    "--max-input-bytes", "1073741824",
    "--max-output-bytes", "1073741824",
    "--no-legacy-json",
    "--max-report-rows", "500",
    "--max-wall-seconds", "1800",
    "--max-tree-rss-bytes", "6442450944",
    "--suppress",
]
EXPECTED_ENV_TEMPLATE = {
    "ADMISSION_MAX_LOAD1": "8.0",
    "ADMISSION_PYTHON": "{PYTHON}",
}


class RenderError(ValueError):
    pass


def _sanitized_env() -> dict[str, str]:
    """The caller's environment minus every GIT_* variable, so no ambient
    variable can redirect repository discovery for us or the wrapper."""
    return {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}


def _git(tree: str, *args: str) -> bytes:
    try:
        proc = subprocess.run([GIT_BIN, "-C", tree, *args],
                              capture_output=True, timeout=30,
                              env=_sanitized_env())
    except (OSError, subprocess.TimeoutExpired) as error:
        raise RenderError(f"git {' '.join(args)} failed: {error!r}")
    if proc.returncode != 0:
        raise RenderError(f"git {' '.join(args)} failed: "
                          + proc.stderr.decode(errors="replace").strip())
    return proc.stdout


def _confined(tree_real: str, name: str) -> str:
    rp = os.path.realpath(os.path.join(tree_real, name))
    if os.path.dirname(rp) != tree_real:
        raise RenderError(
            f"{name} resolves outside the launched tree ({rp}); "
            "symlinked launch inputs are refused")
    if not os.path.isfile(rp):
        raise RenderError(f"--tree is not the skill directory; missing {name}")
    return rp


def _verify_blob_bound(tree: str, tree_real: str) -> dict[str, bytes]:
    """Every launch input's disk bytes must equal its head-pinned blob —
    the executables as much as the record (round 5 BLOCKING)."""
    blobs: dict[str, bytes] = {}
    for name in TREE_REQUIRED_FILES:
        blob = _git(tree, "cat-file", "blob", f"HEAD:{name}")
        with open(_confined(tree_real, name), "rb") as f:
            disk = f.read()
        if disk != blob:
            raise RenderError(
                f"the working-tree {name} differs from its head-pinned blob "
                "(drifted or index-suppressed edit); refusing to render")
        blobs[name] = blob
    with open(os.path.realpath(__file__), "rb") as f:
        running = f.read()
    if running != blobs[RENDERER_BASENAME]:
        raise RenderError(
            "the executing renderer differs from the launched tree's "
            "reviewed renderer; run the tree's own d6_render_command.py")
    return blobs


def load_record(blob: bytes) -> dict:
    try:
        doc = json.loads(blob.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as error:
        raise RenderError(f"record blob does not parse: {error}")
    if doc.get("record") != "d6-admitted-command":
        raise RenderError("wrong record type")
    try:
        outer, inner, env = (doc["launch_template"]["outer_argv"],
                             doc["argv"], doc["env"])
    except KeyError as missing:
        raise RenderError(f"record is missing required key {missing}") from None
    if outer != EXPECTED_OUTER_TEMPLATE or inner != EXPECTED_PIPELINE_TEMPLATE \
            or env != EXPECTED_ENV_TEMPLATE:
        raise RenderError(
            "record deviates from the reviewed launch templates; a drifted "
            "record refuses regardless of git integrity")
    return doc


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
    if not (os.path.isabs(python) and os.path.isfile(python)
            and os.access(python, os.X_OK)):
        raise RenderError("--python must be an absolute path to an existing "
                          "executable (it becomes the preflight interpreter)")
    tree = tree.rstrip(os.sep) or os.sep
    real_tree = os.path.realpath(tree)
    for required in TREE_REQUIRED_FILES:
        _confined(real_tree, required)
    if os.path.realpath(admission_dir).startswith(real_tree + os.sep):
        raise RenderError("--admission-dir must not live inside --tree "
                          "(run artifacts would dirty the head-pinned tree)")
    head = _git(tree, "rev-parse", "HEAD").decode().strip()
    if head != head_pin:
        raise RenderError(
            f"--head-pin {head_pin} does not match the tree's HEAD {head}; "
            "the record can only be rendered at the owner-named head")

    blobs = _verify_blob_bound(tree, real_tree)
    doc = load_record(blobs[RECORD_BASENAME])
    subs = {"{PYTHON}": python, "{TREE}": tree,
            "{ADMISSION_DIR}": admission_dir, "{HEAD_PIN}": head_pin}

    def _sub(text: str) -> str:
        for ph, value in subs.items():
            text = text.replace(ph, value)
        if PLACEHOLDER_ANY.search(text):
            raise RenderError(f"unsubstituted placeholder survives in {text!r}")
        return text

    chain = doc["launch_template"]["outer_argv"] + doc["argv"]
    rendered = [_sub(a) for a in chain]
    env = {k: _sub(v) for k, v in doc["env"].items()}

    pipeline_argv = rendered[len(EXPECTED_OUTER_TEMPLATE):]
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
        os.execvpe(rendered[0], rendered, {**_sanitized_env(), **env})
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
