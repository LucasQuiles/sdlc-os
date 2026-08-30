"""admission_wrapper.sh contract tests (remediation WP2, round9 event 51).

The wrapper is the repo-reviewed replacement for session-scratch admission
scripts. Contract: it may launch the wrapped command ONLY after (1) the target
tree's HEAD equals the pinned commit, (2) the tree is clean, (3) the TREE'S OWN
canonical safety.check_preflight admits AND load1 is under the ceiling, and
(4) the admission directory did not previously exist (created 0700). The
wrapped command's stderr (combined stream) is captured into the admission dir
so refusal REASONS are artifact-bound (round9 event 37 rule). Exit codes:
71 head-pin mismatch, 72 dirty tree, 73 dir occupied, 75 preflight refusal;
otherwise the wrapped command's own exit code passes through.

The wrapper resolves `safety` from the TARGET TREE, which is the seam these
tests use: a fixture repo carries a stub safety.py steered by STUB_PREFLIGHT_OK.
"""
from __future__ import annotations

import os
import stat
import subprocess
import sys

import pytest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WRAPPER = os.path.join(BASE, "admission_wrapper.sh")

STUB_SAFETY = """\
import os

def check_preflight():
    if os.environ.get("STUB_PREFLIGHT_OK") == "1":
        return True, "ok: stub preflight"
    return False, "refused: stub preflight"
"""


def _git(repo, *args):
    subprocess.run(
        ["git", "-C", str(repo), "-c", "user.email=t@test", "-c", "user.name=t",
         "-c", "commit.gpgsign=false", *args],
        check=True, capture_output=True)


@pytest.fixture()
def tree(tmp_path):
    repo = tmp_path / "tree"
    repo.mkdir()
    (repo / "safety.py").write_text(STUB_SAFETY)
    _git(repo, "init", "-q")
    _git(repo, "add", "safety.py")
    env_hookless = {"core.hooksPath": os.devnull}
    subprocess.run(
        ["git", "-C", str(repo), "-c", "user.email=t@test", "-c", "user.name=t",
         "-c", f"core.hooksPath={tmp_path / 'nohooks'}",
         "commit", "-q", "-m", "fixture tree"],
        check=True, capture_output=True)
    return repo


def _head(repo):
    return subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                          check=True, capture_output=True, text=True).stdout.strip()


def _run(tree_path, head, admission_dir, *cmd, ok="1", max_load1="100000"):
    env = dict(os.environ)
    env["STUB_PREFLIGHT_OK"] = ok
    env["ADMISSION_MAX_LOAD1"] = max_load1
    return subprocess.run(
        ["bash", WRAPPER, str(tree_path), head, str(admission_dir), "--", *cmd],
        capture_output=True, text=True, env=env, timeout=60)


def test_wrapper_exists_and_is_syntactically_valid():
    assert os.path.isfile(WRAPPER), "admission_wrapper.sh missing from the repo"
    check = subprocess.run(["bash", "-n", WRAPPER], capture_output=True)
    assert check.returncode == 0, check.stderr


def test_head_pin_mismatch_refuses_71(tree, tmp_path):
    res = _run(tree, "0" * 40, tmp_path / "adm", "true")
    assert res.returncode == 71, res.stdout + res.stderr
    assert not (tmp_path / "adm").exists()


def test_dirty_tree_refuses_72(tree, tmp_path):
    (tree / "dirt.txt").write_text("x")
    res = _run(tree, _head(tree), tmp_path / "adm", "true")
    assert res.returncode == 72, res.stdout + res.stderr
    assert not (tmp_path / "adm").exists()


def test_canonical_preflight_refusal_is_75(tree, tmp_path):
    res = _run(tree, _head(tree), tmp_path / "adm", "true", ok="0")
    assert res.returncode == 75, res.stdout + res.stderr
    assert "refused: stub preflight" in res.stdout
    assert not (tmp_path / "adm").exists()


def test_load_ceiling_refusal_is_75(tree, tmp_path):
    res = _run(tree, _head(tree), tmp_path / "adm", "true", max_load1="0")
    assert res.returncode == 75, res.stdout + res.stderr
    assert not (tmp_path / "adm").exists()


def test_occupied_admission_dir_refuses_73(tree, tmp_path):
    adm = tmp_path / "adm"
    adm.mkdir()
    res = _run(tree, _head(tree), adm, "true")
    assert res.returncode == 73, res.stdout + res.stderr


def test_happy_path_passes_exit_through_and_captures_stderr(tree, tmp_path):
    adm = tmp_path / "adm"
    res = _run(tree, _head(tree), adm,
               "sh", "-c", "echo visible; echo hidden 1>&2; exit 7")
    assert res.returncode == 7, res.stdout + res.stderr
    assert adm.is_dir()
    mode = stat.S_IMODE(adm.stat().st_mode)
    assert mode == 0o700, oct(mode)
    captured = (adm / "wrapped.stderr").read_text()
    assert "hidden" in captured
    assert "visible" in res.stdout


def test_refusal_never_creates_the_admission_dir(tree, tmp_path):
    adm = tmp_path / "adm2"
    _run(tree, _head(tree), adm, "true", ok="0")
    assert not adm.exists()
