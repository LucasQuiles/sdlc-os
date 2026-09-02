"""The D6 admitted command is a REVIEWED, IN-REPO artifact (round9 events
57/58; review rounds 1-2 closed).

Why it exists: admission windows 4 and 5 bracketed the pipeline's own
--jobs 4 detector fan-out (ambient ~5-7 -> breach 8.43; ambient 2.70 ->
breach 8.19, events 44/57) — the reviewed 8.0 monitor ceiling is unreachable
at --jobs 4 on this host. The owner's chosen path is a reviewed variant that
halves the fan-out. The record codifies the FULL launch chain and
d6_render_command.py is the only sanctioned renderer.

Review lineage: round 1 (BLOCKING) — partial argv pins left the index-5
window open (--permissive passed and would have disarmed strict mode); now
whole-argv equality. Round 2 (2 BLOCKING) — the renderer read the record
from ITS OWN directory, so a rogue checkout could render drifted content
into a gated tree (now the record is ALWAYS read from {TREE}, the same path
the wrapper head-pins); and stream output was NUL-separated, not
NUL-terminated, so the canonical bash reader silently dropped --suppress,
flipping merge suppression ON (now every record ends with NUL, and --exec
is the sanctioned mode: execvpe applies the env pin over the caller's
environment and preserves the wrapper's 70-75 exit contract).
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMMAND_FILE = os.path.join(HERE, "d6_admitted_command.json")
RENDERER = os.path.join(HERE, "d6_render_command.py")
PY = "/opt/homebrew/bin/python3.12"

sys.path.insert(0, HERE)
import d6_render_command  # noqa: E402
sys.path.pop(0)

EXPECTED_ARGV = [
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

EXPECTED_OUTER = [
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

CHAIN_LEN = len(EXPECTED_OUTER) + len(EXPECTED_ARGV)


def _doc():
    with open(COMMAND_FILE, encoding="utf-8") as f:
        return json.load(f)


# ── whole-chain equality: the only pin an insertion cannot slip past ──

def test_pipeline_argv_is_byte_exact():
    assert _doc()["argv"] == EXPECTED_ARGV


def test_outer_argv_is_byte_exact():
    assert _doc()["launch_template"]["outer_argv"] == EXPECTED_OUTER


def test_env_allowlist_is_exactly_the_load_ceiling():
    assert _doc()["env"] == {"ADMISSION_MAX_LOAD1": "8.0"}


# ── granular pins kept for readable failures ─────────────────────────

def test_jobs_is_exactly_two():
    argv = _doc()["argv"]
    jobs = argv[argv.index("--jobs") + 1]
    assert jobs == "2", f"reviewed variant pins --jobs 2, found {jobs}"


def test_suppress_stays_terminal():
    # --suppress is nargs='*' in run_pipeline: anything after it would be
    # swallowed as suppress patterns, so the reviewed form keeps it last.
    assert _doc()["argv"][-1] == "--suppress"


def test_wrapper_and_monitor_separators_present():
    outer = _doc()["launch_template"]["outer_argv"]
    assert outer[5] == "--"
    assert outer[-1] == "--"


def test_derivation_carries_lineage_and_estimate_marking():
    d = _doc()["derivation"]
    for needle in ("event 44", "event 57", "ESTIMATES", "UNMEASURED"):
        assert needle in d, f"derivation must state {needle!r}"


# ── renderer fixtures ────────────────────────────────────────────────

def _tree(tmp_path, record=None):
    """A stub skill tree carrying the real (or a supplied) record."""
    for name in d6_render_command.TREE_REQUIRED_FILES:
        if name != d6_render_command.RECORD_BASENAME:
            (tmp_path / name).write_text("")
    if record is None:
        shutil.copy(COMMAND_FILE, tmp_path / d6_render_command.RECORD_BASENAME)
    else:
        (tmp_path / d6_render_command.RECORD_BASENAME).write_text(
            json.dumps(record))
    return str(tmp_path)


def _render(tree, admission_dir="/adm/dir"):
    return d6_render_command.render("/opt/py", tree, admission_dir, "abc123")


# ── renderer: substitution, provenance, source binding ───────────────

def test_render_substitutes_and_nothing_survives(tmp_path):
    tree = _tree(tmp_path)
    argv, env, digest = _render(tree)
    assert len(argv) == CHAIN_LEN
    assert argv[0] == "/bin/bash"
    assert argv[1] == f"{tree}/admission_wrapper.sh"
    assert argv[2:6] == [tree, "abc123", "/adm/dir", "--"]
    assert argv[6:11] == ["/opt/py", "d6_pressure_monitor.py",
                          "--receipt", "/adm/dir/monitor.json", "--"]
    assert argv[11] == "/opt/py" and argv[12] == "run_pipeline.py"
    assert argv[13] == tree
    assert argv[argv.index("--jobs") + 1] == "2"
    assert not any(d6_render_command.PLACEHOLDER_RE.search(a) for a in argv)
    assert env == {"ADMISSION_MAX_LOAD1": "8.0"}
    # provenance: the digest is the monitor's command_sha256 formula applied
    # to the pipeline leg of the rendered chain.
    pipeline = argv[len(EXPECTED_OUTER):]
    assert digest == hashlib.sha256(
        b"\0".join(a.encode() for a in pipeline)).hexdigest()


def test_record_content_comes_from_the_launched_tree(tmp_path):
    # Round-2 BLOCKING 1: whatever checkout the renderer script belongs to,
    # the CONTENT rendered is the launched tree's own record — the same path
    # the wrapper head-pins. A drifted record only ever launches its own
    # (head-pin-gated) tree.
    doc = _doc()
    doc["argv"] = [a if a != "2" else "3" for a in doc["argv"]]
    tree = _tree(tmp_path, record=doc)
    argv, _, _ = _render(tree)
    assert argv[argv.index("--jobs") + 1] == "3", (
        "render() must read the launched tree's record, not the renderer's")


def test_render_refuses_a_tree_that_is_not_the_skill_dir(tmp_path):
    with pytest.raises(d6_render_command.RenderError, match="skill directory"):
        d6_render_command.render("/opt/py", str(tmp_path), "/adm", "pin")


def test_render_refuses_relative_paths(tmp_path):
    tree = _tree(tmp_path)
    with pytest.raises(d6_render_command.RenderError, match="absolute"):
        d6_render_command.render("/opt/py", tree, "adm/dir", "pin")


def test_render_refuses_admission_dir_inside_tree(tmp_path):
    tree = _tree(tmp_path)
    with pytest.raises(d6_render_command.RenderError, match="inside"):
        _render(tree, admission_dir=os.path.join(tree, "adm-inside"))


def test_render_pins_placeholder_multiplicities(tmp_path):
    doc = _doc()
    doc["launch_template"]["outer_argv"][3] = "{HEAD_PIN}{HEAD_PIN}"
    tree = _tree(tmp_path, record=doc)
    with pytest.raises(d6_render_command.RenderError, match="HEAD_PIN"):
        _render(tree)


def test_render_refuses_unknown_placeholders(tmp_path):
    doc = _doc()
    doc["argv"].insert(5, "{EXTRA_KNOB}")
    tree = _tree(tmp_path, record=doc)
    with pytest.raises(d6_render_command.RenderError, match="EXTRA_KNOB"):
        _render(tree)


@pytest.mark.parametrize("missing_key", ["argv", "launch_template", "env"])
def test_render_raises_render_error_on_missing_sections(tmp_path, missing_key):
    doc = _doc()
    del doc[missing_key]
    tree = _tree(tmp_path, record=doc)
    with pytest.raises(d6_render_command.RenderError, match="missing"):
        _render(tree)


# ── consumption contract (round-2 BLOCKING 2 + findings 3/4) ─────────

def test_stream_output_is_nul_terminated_and_bash_reader_gets_all(tmp_path):
    tree = _tree(tmp_path)
    env = {k: v for k, v in os.environ.items() if k != "ADMISSION_MAX_LOAD1"}
    proc = subprocess.run(
        [PY, "-P", "-B", RENDERER, "--python", "/opt/py", "--tree", tree,
         "--admission-dir", "/adm/dir", "--head-pin", "abc123"],
        capture_output=True, env=env)
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.endswith(b"\0"), "every record must be NUL-terminated"
    args = proc.stdout.split(b"\0")[:-1]
    assert len(args) == CHAIN_LEN
    assert args[-1] == b"--suppress"
    assert b"expected_command_sha256 " in proc.stderr
    reader = subprocess.run(
        ["/bin/bash", "-c",
         'n=0; while IFS= read -r -d "" a; do n=$((n+1)); last="$a"; done; '
         'printf "%s %s" "$n" "$last"'],
        input=proc.stdout, capture_output=True)
    assert reader.stdout.decode() == f"{CHAIN_LEN} --suppress"


def test_stream_mode_refuses_a_conflicting_env_pin(tmp_path):
    tree = _tree(tmp_path)
    env = dict(os.environ, ADMISSION_MAX_LOAD1="99.0")
    proc = subprocess.run(
        [PY, "-P", "-B", RENDERER, "--python", "/opt/py", "--tree", tree,
         "--admission-dir", "/adm/dir", "--head-pin", "abc123"],
        capture_output=True, env=env)
    assert proc.returncode != 0
    assert b"cannot enforce the env pin" in proc.stderr


def test_exec_mode_applies_the_env_pin_over_the_caller(tmp_path, monkeypatch):
    tree = _tree(tmp_path)
    captured = {}

    def fake_execvpe(file, args, env):
        captured.update(file=file, args=args, env=env)
        raise SystemExit(0)

    monkeypatch.setenv("ADMISSION_MAX_LOAD1", "99.0")
    monkeypatch.setattr(os, "execvpe", fake_execvpe)
    with pytest.raises(SystemExit):
        d6_render_command.main(["--python", "/opt/py", "--tree", tree,
                                "--admission-dir", "/adm/dir",
                                "--head-pin", "abc123", "--exec"])
    assert captured["file"] == "/bin/bash"
    assert captured["args"][0] == "/bin/bash"
    assert len(captured["args"]) == CHAIN_LEN
    assert captured["env"]["ADMISSION_MAX_LOAD1"] == "8.0", (
        "the record's pin must override the caller's export")
