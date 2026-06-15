"""PR-S1c fail-closed regressions for dedup pipeline hardening."""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


def _load_script_module(name: str, script: str):
    spec = importlib.util.spec_from_file_location(name, BASE / "scripts" / script)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_tfidf_main_rejects_non_list_catalog(tmp_path: Path, monkeypatch, capsys) -> None:
    tfidf = _load_script_module("detect_tfidf_s1c", "detect-tfidf-index.py")
    catalog = tmp_path / "catalog.json"
    output = tmp_path / "tfidf.json"
    catalog.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        ["detect-tfidf-index.py", str(catalog), "-o", str(output)],
    )

    with pytest.raises(SystemExit) as exc:
        tfidf.main()

    assert exc.value.code == 1
    assert "must be a JSON array" in capsys.readouterr().err
    assert not output.exists()


def test_detector_timeout_counts_as_strict_failure(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    shutil.copytree(BASE / "scripts", repo / "scripts")
    shutil.copy(BASE / "run_pipeline.py", repo / "run_pipeline.py")
    shutil.copy(BASE / "safety.py", repo / "safety.py")

    sleeper = repo / "scripts" / "detect-tfidf-index.py"
    sleeper.write_text(
        "#!/usr/bin/env python3\n"
        "import sys\n"
        "import time\n"
        "time.sleep(2)\n"
        "sys.exit(0)\n",
        encoding="utf-8",
    )

    corpus = tmp_path / "corpus.json"
    corpus.write_text(json.dumps({"functions": []}), encoding="utf-8")
    out_dir = tmp_path / "out"
    env = os.environ.copy()
    env["DEDUP_DETECTOR_TIMEOUT_S"] = "1"

    result = subprocess.run(
        [
            PYTHON,
            str(repo / "run_pipeline.py"),
            "--from-corpus",
            str(corpus),
            "-o",
            str(out_dir),
            "--lock-file",
            str(tmp_path / "run_pipeline.lock"),
            "--ignore-preflight",
        ],
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
    )

    assert result.returncode == 2
    assert "tfidf-index failed (exit 124)" in result.stdout
    assert "strict mode: 1 detector(s) failed, 0 skipped" in result.stdout
    assert "TIMEOUT after 1s" in (out_dir / "pipeline.log").read_text(encoding="utf-8")


def test_regex_extractor_warns_on_unreadable_path(tmp_path: Path, capsys) -> None:
    regex = _load_script_module("extract_functions_regex_s1c", "extract-functions-regex.py")
    source_dir = tmp_path / "src"
    source_dir.mkdir()
    unreadable_path = source_dir / "package.py"
    unreadable_path.mkdir()

    results = regex.extract_for_language(
        regex.LANGS["python"],
        str(source_dir),
        [str(unreadable_path)],
        context_lines=2,
    )

    captured = capsys.readouterr()
    assert results == []
    assert "Warning: skipping unreadable file" in captured.err
    assert str(unreadable_path) in captured.err
