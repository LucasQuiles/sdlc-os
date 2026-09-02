"""The D6 admitted command is a REVIEWED, IN-REPO artifact (round9 events
57/58; review rounds 1-4 closed).

Why it exists: admission windows 4 and 5 bracketed the pipeline's own
--jobs 4 detector fan-out (ambient ~5-7 -> breach 8.43; ambient 2.70 ->
breach 8.19, events 44/57) — the reviewed 8.0 monitor ceiling is unreachable
at --jobs 4 on this host. The owner's chosen path is a reviewed variant that
halves the fan-out. The record codifies the FULL launch chain and
d6_render_command.py is the only sanctioned renderer.

Review lineage: round 1 (BLOCKING) — partial argv pins left the index-5
window open. Round 2 (2 BLOCKING) — renderer-local record source; missing
trailing NUL dropped --suppress at the bash reader. Round 3 (BLOCKING) — a
symlinked record defeated the tree binding. Round 4 (2 BLOCKING) — the
head-pin check bound a LABEL, not content: `assume-unchanged` suppressed
drift from the cleanliness gate while the renderer read disk bytes, and
GIT_DIR/GIT_WORK_TREE redirected every git oracle at once. Closed by
reading the record from the head-pinned BLOB via GIT_*-sanitized git,
refusing disk/blob divergence, stripping GIT_* from the exec environment,
and pinning the reviewed templates IN CODE so a drifted record refuses
with no external oracle at all.
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


# ── triple agreement: record file == renderer templates == this file ──

def test_pipeline_argv_is_byte_exact():
    assert _doc()["argv"] == EXPECTED_ARGV


def test_outer_argv_is_byte_exact():
    assert _doc()["launch_template"]["outer_argv"] == EXPECTED_OUTER


def test_env_pins_are_byte_exact():
    assert _doc()["env"] == EXPECTED_ENV


def test_renderer_enforcement_templates_agree_with_the_record():
    # The renderer pins the chain IN CODE (no external oracle); the JSON is
    # the grant-facing artifact. They must never diverge.
    assert d6_render_command.EXPECTED_PIPELINE_TEMPLATE == EXPECTED_ARGV
    assert d6_render_command.EXPECTED_OUTER_TEMPLATE == EXPECTED_OUTER
    assert d6_render_command.EXPECTED_ENV_TEMPLATE == EXPECTED_ENV


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

def _commit(tree_path):
    subprocess.run(["git", "-C", str(tree_path), "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", str(tree_path), "-c", "user.email=t@t", "-c",
         "user.name=t", "-c", "commit.gpgsign=false", "commit", "-q", "-m",
         "s"], check=True)
    return subprocess.run(["git", "-C", str(tree_path), "rev-parse", "HEAD"],
                          capture_output=True, text=True,
                          check=True).stdout.strip()


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
    return str(tmp_path), _commit(tmp_path)


def _render(tree, head, admission_dir="/adm/dir", python=PY):
    return d6_render_command.render(python, tree, admission_dir, head)


# ── renderer: substitution and provenance ────────────────────────────

def test_render_substitutes_and_nothing_survives(tmp_path):
    tree, head = _tree(tmp_path)
    argv, env, digest = _render(tree, head)
    assert len(argv) == CHAIN_LEN
    assert argv[0] == "/bin/bash"
    assert argv[1] == f"{tree}/admission_wrapper.sh"
    assert argv[2:6] == [tree, head, "/adm/dir", "--"]
    assert argv[6:11] == [PY, "d6_pressure_monitor.py",
                          "--receipt", "/adm/dir/monitor.json", "--"]
    assert argv[11] == PY and argv[12] == "run_pipeline.py"
    assert argv[13] == tree
    assert argv[argv.index("--jobs") + 1] == "2"
    assert not any(d6_render_command.PLACEHOLDER_ANY.search(a) for a in argv)
    assert env == {"ADMISSION_MAX_LOAD1": "8.0", "ADMISSION_PYTHON": PY}
    pipeline = argv[len(EXPECTED_OUTER):]
    assert digest == hashlib.sha256(
        b"\0".join(os.fsencode(a) for a in pipeline)).hexdigest()


def test_render_accepts_a_trailing_slash_on_tree(tmp_path):
    tree, head = _tree(tmp_path)
    argv, _, _ = _render(tree + os.sep, head)
    assert argv[1] == f"{tree}/admission_wrapper.sh"


# ── content binding (round 4) ────────────────────────────────────────

def test_render_verifies_the_head_pin_itself(tmp_path):
    tree, _ = _tree(tmp_path)
    with pytest.raises(d6_render_command.RenderError, match="owner-named head"):
        _render(tree, "0" * 40)


def test_assume_unchanged_drift_refuses(tmp_path):
    # Round-4 BLOCKING 1: with the drifted edit suppressed from the index,
    # status is clean and rev-parse matches — but the disk bytes differ from
    # the head-pinned blob, and content is what must bind.
    tree, head = _tree(tmp_path)
    record_path = os.path.join(tree, d6_render_command.RECORD_BASENAME)
    subprocess.run(["git", "-C", tree, "update-index", "--assume-unchanged",
                    d6_render_command.RECORD_BASENAME], check=True)
    doc = _doc()
    doc["argv"] = [a if a != "2" else "4" for a in doc["argv"]]
    with open(record_path, "w") as f:
        json.dump(doc, f)
    porcelain = subprocess.run(["git", "-C", tree, "status", "--porcelain"],
                               capture_output=True, text=True).stdout
    assert porcelain == "", "precondition: the drift is index-suppressed"
    with pytest.raises(d6_render_command.RenderError,
                       match="head-pinned blob"):
        _render(tree, head)


def test_ambient_git_dir_cannot_redirect_the_oracle(tmp_path, monkeypatch):
    # Round-4 BLOCKING 2: GIT_DIR/GIT_WORK_TREE must not reach any git the
    # renderer runs. With them pointing at garbage, a sanitized call still
    # answers from the real tree.
    tree, head = _tree(tmp_path)
    monkeypatch.setenv("GIT_DIR", "/nonexistent/decoy")
    monkeypatch.setenv("GIT_WORK_TREE", "/nonexistent/worktree")
    argv, _, _ = _render(tree, head)
    assert argv[2] == tree


def test_exec_environment_is_stripped_of_git_vars(tmp_path, monkeypatch):
    tree, head = _tree(tmp_path)
    captured = {}

    def fake_execvpe(file, args, env):
        captured.update(file=file, args=args, env=env)
        raise SystemExit(0)

    monkeypatch.setenv("GIT_DIR", "/nonexistent/decoy")
    monkeypatch.setenv("ADMISSION_MAX_LOAD1", "99.0")
    monkeypatch.setenv("ADMISSION_PYTHON", "/attacker/python")
    monkeypatch.setattr(os, "execvpe", fake_execvpe)
    with pytest.raises(SystemExit):
        d6_render_command.main(["--python", PY, "--tree", tree,
                                "--admission-dir", "/adm/dir",
                                "--head-pin", head, "--exec"])
    assert captured["file"] == "/bin/bash"
    assert len(captured["args"]) == CHAIN_LEN
    assert "GIT_DIR" not in captured["env"], (
        "the wrapper's gates must not inherit a redirected git oracle")
    assert captured["env"]["ADMISSION_MAX_LOAD1"] == "8.0"
    assert captured["env"]["ADMISSION_PYTHON"] == PY


@pytest.mark.parametrize("mutate", [
    lambda d: d["argv"].__setitem__(d["argv"].index("2"), "4"),
    lambda d: d["argv"].insert(5, "--permissive"),
    lambda d: d["argv"].insert(5, "{TREE2}"),
    lambda d: d["launch_template"]["outer_argv"].__setitem__(
        1, "/rogue/admission_wrapper.sh"),
    lambda d: d["env"].__setitem__("ADMISSION_MAX_LOAD1", "12.0"),
    lambda d: d["env"].pop("ADMISSION_PYTHON"),
])
def test_a_committed_drifted_record_refuses_on_the_code_pin(tmp_path, mutate):
    # Defense-in-depth: even COMMITTED drift (clean tree, true head pin)
    # refuses, because the reviewed templates are pinned in renderer code —
    # no git mechanism is load-bearing for this check.
    doc = _doc()
    mutate(doc)
    tree, head = _tree(tmp_path, record=doc)
    with pytest.raises(d6_render_command.RenderError,
                       match="reviewed launch templates"):
        _render(tree, head)


@pytest.mark.parametrize("missing_key", ["argv", "launch_template", "env"])
def test_render_raises_render_error_on_missing_sections(tmp_path, missing_key):
    doc = _doc()
    del doc[missing_key]
    tree, head = _tree(tmp_path, record=doc)
    with pytest.raises(d6_render_command.RenderError, match="missing"):
        _render(tree, head)


# ── input validation and confinement ─────────────────────────────────

def test_render_refuses_a_symlinked_record(tmp_path):
    rogue = tmp_path / "rogue"
    rogue.mkdir()
    (rogue / "drifted.json").write_text(json.dumps(_doc()))
    victim = tmp_path / "victim"
    victim.mkdir()
    for name in d6_render_command.TREE_REQUIRED_FILES:
        if name != d6_render_command.RECORD_BASENAME:
            (victim / name).write_text("")
    (victim / d6_render_command.RECORD_BASENAME).symlink_to(
        rogue / "drifted.json")
    subprocess.run(["git", "init", "-q", str(victim)], check=True)
    head = _commit(victim)
    with pytest.raises(d6_render_command.RenderError, match="symlink"):
        _render(str(victim), head)


def test_render_refuses_a_symlinked_required_file(tmp_path):
    outside = tmp_path / "outside.sh"
    outside.write_text("")
    sub = tmp_path / "t"
    sub.mkdir()
    tree, _ = _tree(sub)
    os.remove(os.path.join(tree, "admission_wrapper.sh"))
    os.symlink(outside, os.path.join(tree, "admission_wrapper.sh"))
    head = _commit(sub)
    with pytest.raises(d6_render_command.RenderError, match="symlink"):
        _render(tree, head)


def test_render_refuses_a_tree_that_is_not_the_skill_dir(tmp_path):
    with pytest.raises(d6_render_command.RenderError, match="missing"):
        d6_render_command.render(PY, str(tmp_path), "/adm", "pin")


def test_render_refuses_relative_paths(tmp_path):
    tree, head = _tree(tmp_path)
    with pytest.raises(d6_render_command.RenderError, match="absolute"):
        d6_render_command.render(PY, tree, "adm/dir", head)


@pytest.mark.parametrize("python", ["python3", "/nope/python"])
def test_render_refuses_a_non_executable_python(tmp_path, python):
    tree, head = _tree(tmp_path)
    with pytest.raises(d6_render_command.RenderError, match="interpreter"):
        _render(tree, head, python=python)


def test_render_refuses_braces_in_inputs(tmp_path):
    tree, head = _tree(tmp_path)
    with pytest.raises(d6_render_command.RenderError, match="braces"):
        d6_render_command.render(PY, tree, "/adm/{X}", head)


def test_render_refuses_admission_dir_inside_tree(tmp_path):
    tree, head = _tree(tmp_path)
    with pytest.raises(d6_render_command.RenderError, match="inside"):
        _render(tree, head, admission_dir=os.path.join(tree, "adm-inside"))


def test_digest_uses_the_monitor_fsencode_formula(tmp_path):
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
        [PY, "-P", "-B", RENDERER, "--python", PY, "--tree", tree,
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
        [PY, "-P", "-B", RENDERER, "--python", PY, "--tree", tree,
         "--admission-dir", "/adm/dir", "--head-pin", head],
        capture_output=True, env=env)
    assert proc.returncode != 0
    assert b"cannot enforce the env pin" in proc.stderr
    assert b"Traceback" not in proc.stderr, (
        "refusals are operator-facing messages, not tracebacks")
