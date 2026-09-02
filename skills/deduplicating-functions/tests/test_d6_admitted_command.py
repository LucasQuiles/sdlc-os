"""The D6 admitted command is a REVIEWED, IN-REPO artifact (round9 event 58).

Why it exists: admission windows 4 and 5 bracketed the pipeline's own
--jobs 4 detector fan-out at ~5.5 load1 units (ambient ~5-7 -> breach 8.43;
ambient 2.70 -> breach 8.19, events 44/57) — the reviewed 8.0 monitor ceiling
is unreachable at --jobs 4 on this host. The owner's chosen path is a reviewed
variant that halves the fan-out. Codifying the argv here means a future launch
can only drift from the reviewed form by failing these pins, and the driver
reconstructs the command from a committed file instead of ledger prose (the
2026-09-01 launch lost its first window attempt to an argv separator that
prose never showed).
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMMAND_FILE = os.path.join(HERE, "d6_admitted_command.json")

# The event-28 owner-named flag set, --jobs value excepted (that is the one
# parameter this reviewed variant changes, events 57/58).
EVENT_28_FLAGS_AFTER_JOBS = [
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


def _argv():
    with open(COMMAND_FILE) as f:
        doc = json.load(f)
    assert doc["record"] == "d6-admitted-command"
    return doc["argv"]


def test_command_file_exists_and_parses():
    argv = _argv()
    assert isinstance(argv, list) and len(argv) > 5
    assert all(isinstance(a, str) for a in argv)


def test_jobs_is_exactly_two():
    argv = _argv()
    assert "--jobs" in argv, "the fan-out width must be pinned explicitly"
    jobs = argv[argv.index("--jobs") + 1]
    # Mutant pin: the un-launchable 4 (and anything above 2) must fail here.
    assert jobs == "2", f"reviewed variant pins --jobs 2, found {jobs}"


def test_flags_match_event_28_except_jobs():
    argv = _argv()
    tail = argv[argv.index("--jobs") + 2:]
    assert tail == EVENT_28_FLAGS_AFTER_JOBS, (
        "every flag except --jobs is an owner-named event-28 parameter and "
        "must be byte-identical; changing any of them needs its own grant")
    assert argv[argv.index("--strict"):argv.index("--jobs")] == ["--strict"]


def test_substitution_placeholders_present():
    argv = _argv()
    assert argv[0] == "{PYTHON}"
    assert argv[1] == "run_pipeline.py"
    assert argv[2] == "{TREE}"
    assert argv[3:5] == ["-o", "{ADMISSION_DIR}/pipeline-output"]
    joined = "\0".join(argv)
    for ph in ("{PYTHON}", "{TREE}", "{ADMISSION_DIR}"):
        assert joined.count(ph) == 1, f"{ph} must appear exactly once"


def test_suppress_stays_terminal():
    argv = _argv()
    # --suppress is nargs='*' in run_pipeline: anything after it would be
    # swallowed as suppress patterns, so the reviewed form keeps it last.
    assert argv[-1] == "--suppress"
