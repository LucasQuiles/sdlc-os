"""The D6 admitted command is a REVIEWED, IN-REPO artifact (round9 events
57/58; review rounds 1-3 closed).

Why it exists: admission windows 4 and 5 bracketed the pipeline's own
--jobs 4 detector fan-out (ambient ~5-7 -> breach 8.43; ambient 2.70 ->
breach 8.19, events 44/57) — the reviewed 8.0 monitor ceiling is unreachable
at --jobs 4 on this host. The owner's chosen path is a reviewed variant that
halves the fan-out. The record codifies the FULL launch chain and
d6_render_command.py is the only sanctioned renderer.

Review lineage: round 1 (BLOCKING) — partial argv pins left the index-5
window open. Round 2 (2 BLOCKING) — renderer-local record source; missing
trailing NUL dropped --suppress at the bash reader. Round 3 (BLOCKING) — a
symlinked record defeated the tree binding (git tracks the link, not the
target); closed by realpath confinement of every launch input, plus the
consolidating fix: the renderer verifies the tree's HEAD against --head-pin
itself, and pins the rendered outer chain structurally so a record cannot
name a wrapper or monitor outside the gated tree.
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

EXPECTED_ENV = {"ADMISSION_MAX_LOAD1": "8.0", "ADMISSION_PYTHON": "{PYTHON}"}

CHAIN_LEN = len(EXPECTED_OUTER) + len(EXPECTED_ARGV)


def _doc():
    with open(COMMAND_FILE, encoding="utf-8") as f:
        return json.load(f)


# ── whole-chain equality: the only pin an insertion cannot slip past ──

def test_pipeline_argv_is_byte_exact():
    assert _doc()["argv"] == EXPECTED_ARGV


def test_outer_argv_is_byte_exact():
    assert _doc()["launch_template"]["outer_argv"] == EXPECTED_OUTER


def test_env_pins_are_byte_exact():
    # ADMISSION_PYTHON pins the interpreter that runs the wrapper's canonical
    # preflight to the same python the chain uses (round 3, finding 3).
    assert _doc()["env"] == EXPECTED_ENV


# ── granular pins kept for readable failures ─────────────────────────

def test_jobs_is_exactly_two():
    argv = _doc()["argv"]
    jobs = argv[argv.index("--jobs") + 1]
    assert jobs == "2", f"reviewed variant pins --jobs 2, found {jobs}"


def test_suppress_stays_terminal():
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
    """A stub skill tree that is a real git checkout carrying the record."""
    for name in d6_render_command.TREE_REQUIRED_FILES:
        if name != d6_render_command.RECORD_BASENAME:
            (tmp_path / name).write_text("")
    if record is None:
        shutil.copy(COMMAND_FILE, tmp_path / d6_render_command.RECORD_BASENAME)
    else:
        (tmp_path / d6_render_command.RECORD_BASENAME).write_text(
            json.dumps(record))
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "-c", "user.email=t@t", "-c",
         "user.name=t", "-c", "commit.gpgsign=false", "commit", "-q", "-m", "s"],
        check=True)
    head = subprocess.run(["git", "-C", str(tmp_path), "rev-parse", "HEAD"],
                          capture_output=True, text=True,
                          check=True).stdout.strip()
    return str(tmp_path), head


def _render(tree, head, admission_dir="/adm/dir", python="/opt/py"):
    return d6_render_command.render(python, tree, admission_dir, head)


# ── renderer: substitution, provenance, source binding ───────────────

def test_render_substitutes_and_nothing_survives(tmp_path):
    tree, head = _tree(tmp_path)
    argv, env, digest = _render(tree, head)
    assert len(argv) == CHAIN_LEN
    assert argv[0] == "/bin/bash"
    assert argv[1] == f"{tree}/admission_wrapper.sh"
    assert argv[2:6] == [tree, head, "/adm/dir", "--"]
    assert argv[6:11] == ["/opt/py", "d6_pressure_monitor.py",
                          "--receipt", "/adm/dir/monitor.json", "--"]
    assert argv[11] == "/opt/py" and argv[12] == "run_pipeline.py"
    assert argv[13] == tree
    assert argv[argv.index("--jobs") + 1] == "2"
    assert not any(d6_render_command.PLACEHOLDER_ANY.search(a) for a in argv)
    assert env == {"ADMISSION_MAX_LOAD1": "8.0", "ADMISSION_PYTHON": "/opt/py"}
    pipeline = argv[len(EXPECTED_OUTER):]
    assert digest == hashlib.sha256(
        b"\0".join(os.fsencode(a) for a in pipeline)).hexdigest()


def test_render_verifies_the_head_pin_itself(tmp_path):
    tree, _ = _tree(tmp_path)
    with pytest.raises(d6_render_command.RenderError, match="owner-named head"):
        _render(tree, "0" * 40)


def test_render_refuses_a_symlinked_record(tmp_path):
    # Round-3 BLOCKING: git tracks the link, not the target — a symlinked
    # record would pass head-pin and cleanliness while the argv comes from
    # an ungated path.
    rogue = tmp_path / "rogue"
    rogue.mkdir()
    doc = _doc()
    doc["argv"] = [a if a != "2" else "4" for a in doc["argv"]]
    (rogue / "drifted.json").write_text(json.dumps(doc))
    victim = tmp_path / "victim"
    victim.mkdir()
    for name in d6_render_command.TREE_REQUIRED_FILES:
        if name != d6_render_command.RECORD_BASENAME:
            (victim / name).write_text("")
    (victim / d6_render_command.RECORD_BASENAME).symlink_to(
        rogue / "drifted.json")
    subprocess.run(["git", "init", "-q", str(victim)], check=True)
    subprocess.run(["git", "-C", str(victim), "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", str(victim), "-c", "user.email=t@t", "-c", "user.name=t",
         "-c", "commit.gpgsign=false", "commit", "-q", "-m", "s"], check=True)
    head = subprocess.run(["git", "-C", str(victim), "rev-parse", "HEAD"],
                          capture_output=True, text=True,
                          check=True).stdout.strip()
    with pytest.raises(d6_render_command.RenderError, match="symlink"):
        _render(str(victim), head)


def test_render_refuses_a_symlinked_required_file(tmp_path):
    outside = tmp_path / "outside.sh"
    outside.write_text("")
    sub = tmp_path / "t"
    sub.mkdir()
    tree, head = _tree(sub)
    os.remove(os.path.join(tree, "admission_wrapper.sh"))
    os.symlink(outside, os.path.join(tree, "admission_wrapper.sh"))
    with pytest.raises(d6_render_command.RenderError, match="symlink"):
        _render(tree, head)


def test_record_content_comes_from_the_launched_tree(tmp_path):
    doc = _doc()
    doc["argv"] = [a if a != "2" else "3" for a in doc["argv"]]
    tree, head = _tree(tmp_path, record=doc)
    argv, _, _ = _render(tree, head)
    assert argv[argv.index("--jobs") + 1] == "3", (
        "render() must read the launched tree's record, not the renderer's")


def test_render_refuses_a_record_naming_a_foreign_wrapper(tmp_path):
    # Round-3 finding 2: counts alone let a record point outer_argv[1] at a
    # wrapper outside the gated tree while keeping {TREE} multiplicity legal.
    doc = _doc()
    doc["launch_template"]["outer_argv"][1] = "/rogue/admission_wrapper.sh"
    doc["launch_template"]["outer_argv"][7] = "{TREE}/d6_pressure_monitor.py"
    doc["launch_template"]["outer_argv"][2] = "{TREE}"
    doc["argv"][2] = "{TREE}"
    tree, head = _tree(tmp_path, record=doc)
    with pytest.raises(d6_render_command.RenderError):
        _render(tree, head)


def test_render_refuses_a_tree_that_is_not_the_skill_dir(tmp_path):
    with pytest.raises(d6_render_command.RenderError, match="missing"):
        d6_render_command.render("/opt/py", str(tmp_path), "/adm", "pin")


def test_render_refuses_relative_paths(tmp_path):
    tree, head = _tree(tmp_path)
    with pytest.raises(d6_render_command.RenderError, match="absolute"):
        d6_render_command.render("/opt/py", tree, "adm/dir", head)


def test_render_refuses_braces_in_inputs(tmp_path):
    tree, head = _tree(tmp_path)
    with pytest.raises(d6_render_command.RenderError, match="braces"):
        d6_render_command.render("/opt/{p}", tree, "/adm", head)


def test_render_refuses_admission_dir_inside_tree(tmp_path):
    tree, head = _tree(tmp_path)
    with pytest.raises(d6_render_command.RenderError, match="inside"):
        _render(tree, head, admission_dir=os.path.join(tree, "adm-inside"))


def test_render_pins_placeholder_multiplicities(tmp_path):
    doc = _doc()
    doc["launch_template"]["outer_argv"][3] = "{HEAD_PIN}{HEAD_PIN}"
    tree, head = _tree(tmp_path, record=doc)
    with pytest.raises(d6_render_command.RenderError, match="HEAD_PIN"):
        _render(tree, head)


@pytest.mark.parametrize("token", ["{EXTRA_KNOB}", "{TREE2}", "{tree}", "{X1}"])
def test_render_refuses_unknown_or_malformed_placeholders(tmp_path, token):
    doc = _doc()
    doc["argv"].insert(5, token)
    tree, head = _tree(tmp_path, record=doc)
    with pytest.raises(d6_render_command.RenderError,
                       match="unknown placeholder"):
        _render(tree, head)


@pytest.mark.parametrize("missing_key", ["argv", "launch_template", "env"])
def test_render_raises_render_error_on_missing_sections(tmp_path, missing_key):
    doc = _doc()
    del doc[missing_key]
    tree, head = _tree(tmp_path, record=doc)
    with pytest.raises(d6_render_command.RenderError, match="missing"):
        _render(tree, head)


def test_digest_uses_the_monitor_fsencode_formula(tmp_path):
    # An undecodable byte in a path must still digest (os.fsencode), not
    # crash — the monitor's command_sha256 uses fsencode (round 3, F5).
    tree, head = _tree(tmp_path)
    weird = "/adm/" + os.fsdecode(b"d\xff")
    argv, _, digest = _render(tree, head, admission_dir=weird)
    pipeline = argv[len(EXPECTED_OUTER):]
    assert digest == hashlib.sha256(
        b"\0".join(os.fsencode(a) for a in pipeline)).hexdigest()


# ── consumption contract ─────────────────────────────────────────────

def test_stream_output_is_nul_terminated_and_bash_reader_gets_all(tmp_path):
    tree, head = _tree(tmp_path)
    env = {k: v for k, v in os.environ.items()
           if k not in ("ADMISSION_MAX_LOAD1", "ADMISSION_PYTHON")}
    proc = subprocess.run(
        [PY, "-P", "-B", RENDERER, "--python", "/opt/py", "--tree", tree,
         "--admission-dir", "/adm/dir", "--head-pin", head],
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


def test_stream_mode_refuses_a_conflicting_env_pin_cleanly(tmp_path):
    tree, head = _tree(tmp_path)
    env = dict(os.environ, ADMISSION_MAX_LOAD1="99.0")
    proc = subprocess.run(
        [PY, "-P", "-B", RENDERER, "--python", "/opt/py", "--tree", tree,
         "--admission-dir", "/adm/dir", "--head-pin", head],
        capture_output=True, env=env)
    assert proc.returncode != 0
    assert b"cannot enforce the env pin" in proc.stderr
    assert b"Traceback" not in proc.stderr, (
        "refusals are operator-facing messages, not tracebacks")


def test_exec_mode_applies_the_env_pins_over_the_caller(tmp_path, monkeypatch):
    tree, head = _tree(tmp_path)
    captured = {}

    def fake_execvpe(file, args, env):
        captured.update(file=file, args=args, env=env)
        raise SystemExit(0)

    monkeypatch.setenv("ADMISSION_MAX_LOAD1", "99.0")
    monkeypatch.setenv("ADMISSION_PYTHON", "/attacker/python")
    monkeypatch.setattr(os, "execvpe", fake_execvpe)
    with pytest.raises(SystemExit):
        d6_render_command.main(["--python", "/opt/py", "--tree", tree,
                                "--admission-dir", "/adm/dir",
                                "--head-pin", head, "--exec"])
    assert captured["file"] == "/bin/bash"
    assert len(captured["args"]) == CHAIN_LEN
    assert captured["env"]["ADMISSION_MAX_LOAD1"] == "8.0"
    assert captured["env"]["ADMISSION_PYTHON"] == "/opt/py", (
        "the preflight interpreter pin must override the caller's export")
