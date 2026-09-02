"""The D6 admitted command is a REVIEWED, IN-REPO artifact (round9 events
57/58; review round 1 closed the argv-window escape).

Why it exists: admission windows 4 and 5 bracketed the pipeline's own
--jobs 4 detector fan-out (ambient ~5-7 -> breach 8.43; ambient 2.70 ->
breach 8.19, events 44/57) — the reviewed 8.0 monitor ceiling is unreachable
at --jobs 4 on this host. The owner's chosen path is a reviewed variant that
halves the fan-out. The record codifies the FULL launch chain (wrapper argv,
monitor argv, pipeline argv, env allowlist) and d6_render_command.py is the
only sanctioned renderer; the 2026-09-01 window lost an attempt to the
monitor's '--' separator, which ledger prose never showed.

Review round 1 (BLOCKING): pinning argv[0:5] + the tail after --strict left
the index-5 window open — an inserted --permissive passed every test and
would have silently disarmed strict mode (run_pipeline.py computes
strict_mode = not permissive). The pin is now whole-argv equality; the
granular tests remain for readable failure messages.
"""
from __future__ import annotations

import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMMAND_FILE = os.path.join(HERE, "d6_admitted_command.json")

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
    # admission_wrapper.sh:29 requires argv[4] == "--"; the monitor requires
    # a literal "--" before the wrapped command (the 2026-09-01 lost attempt).
    outer = _doc()["launch_template"]["outer_argv"]
    assert outer[5] == "--"
    assert outer[-1] == "--"


def test_derivation_carries_lineage_and_estimate_marking():
    d = _doc()["derivation"]
    for needle in ("event 44", "event 57", "ESTIMATES", "UNMEASURED"):
        assert needle in d, f"derivation must state {needle!r}"


# ── renderer: substitution, validation, fail-closed ──────────────────

def _tree(tmp_path):
    for name in d6_render_command.TREE_REQUIRED_FILES:
        (tmp_path / name).write_text("")
    return str(tmp_path)


def test_render_substitutes_each_placeholder_and_nothing_survives(tmp_path):
    tree = _tree(tmp_path)
    argv, env = d6_render_command.render(
        "/opt/py", tree, "/adm/dir", "abc123")
    assert argv[0] == "/bin/bash"
    assert argv[1] == f"{tree}/admission_wrapper.sh"
    assert argv[2:6] == [tree, "abc123", "/adm/dir", "--"]
    assert argv[6:11] == ["/opt/py", "d6_pressure_monitor.py",
                          "--receipt", "/adm/dir/monitor.json", "--"]
    assert argv[11] == "/opt/py" and argv[12] == "run_pipeline.py"
    assert argv[13] == tree
    assert "--jobs" in argv and argv[argv.index("--jobs") + 1] == "2"
    assert not any("{" in a and "}" in a for a in argv)
    assert env == {"ADMISSION_MAX_LOAD1": "8.0"}


def test_render_refuses_a_tree_that_is_not_the_skill_dir(tmp_path):
    with pytest.raises(d6_render_command.RenderError, match="skill directory"):
        d6_render_command.render("/opt/py", str(tmp_path), "/adm", "pin")


def test_render_refuses_relative_paths(tmp_path):
    tree = _tree(tmp_path)
    with pytest.raises(d6_render_command.RenderError, match="absolute"):
        d6_render_command.render("/opt/py", tree, "adm/dir", "pin")


def test_render_fails_closed_on_malformed_record(tmp_path):
    tree = _tree(tmp_path)
    bad = tmp_path / "cmd.json"
    bad.write_text(json.dumps({"record": "d6-admitted-command",
                               "env": {},
                               "launch_template": {"outer_argv": ["{HEAD_PIN}",
                                                                  "{HEAD_PIN}"]},
                               "argv": ["{PYTHON}", "{ADMISSION_DIR}"]}))
    with pytest.raises(d6_render_command.RenderError, match="HEAD_PIN"):
        d6_render_command.render("/opt/py", tree, "/adm", "pin", path=str(bad))
