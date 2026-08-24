"""Contract tests for the bounded merge-signals.py (SQLite-backed, streamed output).

Requirements (plan P1 §6.2): finite caps, deterministic truncation, summary.json +
pairs.jsonl + run.json artifacts, legacy merged-results.json only under a finite
ceiling, fail-closed on malformed input, semantic parity with the previous
in-memory implementation.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).parent.parent
SCRIPTS = BASE / "scripts"
MERGE = SCRIPTS / "merge-signals.py"
PY = sys.executable

_spec = importlib.util.spec_from_file_location("merge_signals_bounded", MERGE)
merge_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(merge_mod)


def _func(name, file="a.py", line=1):
    return {"name": name, "file": file, "line": line}


def _pair(a, b, strategy, score, extra=None):
    d = {"func_a": a, "func_b": b, "final_score": score, "strategy": strategy}
    if extra:
        d.update(extra)
    return d


def _write_detect_dir(tmp_path: Path, results: dict[str, list[dict]], jsonl: bool = False) -> Path:
    d = tmp_path / "detect"
    d.mkdir(parents=True, exist_ok=True)
    for strat, rows in results.items():
        name = strat.replace("_", "-")
        if jsonl:
            (d / f"{name}-results.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
        else:
            (d / f"{name}-results.json").write_text(json.dumps(rows, indent=2))
    return d


def _run_merge(detect_dir: Path, out_dir: Path, *args: str) -> subprocess.CompletedProcess:
    out_dir.mkdir(exist_ok=True)
    return subprocess.run(
        [PY, str(MERGE), str(detect_dir), "-o", str(out_dir / "merged-results.json"),
         "--include-summary", *args],
        capture_output=True, text=True, timeout=120,
    )


def _three_signal_corpus(n_pairs: int) -> dict[str, list[dict]]:
    """n_pairs distinct pairs, each flagged by token_clone+ast_similarity+tfidf (→ HIGH)."""
    res: dict[str, list[dict]] = {"token_clone": [], "ast_similarity": [], "tfidf_index": []}
    for i in range(n_pairs):
        a = _func(f"fa{i}", "a.py", i + 1)
        b = _func(f"fb{i}", "b.py", i + 1)
        score = round(1.0 - (i % 97) / 1000.0, 3)
        res["token_clone"].append(_pair(a, b, "token_clone", score, {"scores": {"clone_type": 1}}))
        res["ast_similarity"].append(_pair(a, b, "ast_similarity", score))
        res["tfidf_index"].append(_pair(a, b, "tfidf_index", score))
    return res


# ---------------------------------------------------------------------------
# Artifacts
# ---------------------------------------------------------------------------

def test_writes_summary_pairs_jsonl_run_json_and_legacy(tmp_path):
    d = _write_detect_dir(tmp_path, _three_signal_corpus(12))
    out = tmp_path / "merge"
    r = _run_merge(d, out)
    assert r.returncode == 0, r.stderr
    assert (out / "summary.json").exists()
    assert (out / "pairs.jsonl").exists()
    assert (out / "run.json").exists()
    assert (out / "merged-results.json").exists(), "small run must still emit the legacy file"
    summary = json.loads((out / "summary.json").read_text())
    pairs = [json.loads(line) for line in (out / "pairs.jsonl").read_text().splitlines()]
    legacy = json.loads((out / "merged-results.json").read_text())
    assert summary["total_pairs"] == 12 == len(pairs)
    assert legacy["pairs"] == pairs
    assert legacy["summary"] == {k: v for k, v in summary.items() if k in legacy["summary"]}
    run = json.loads((out / "run.json").read_text())
    assert run["schema_version"] >= 1
    assert run["outcome"] == "complete"
    assert run["counts"]["candidates_seen"] == 36
    assert run["counts"]["pairs_emitted"] == 12
    assert run["counts"]["pairs_dropped"] == 0
    assert run["truncated"] is False
    assert run["legacy_export"]["written"] is True
    assert "sha256" in run["artifacts"]["pairs.jsonl"]


def test_pairs_jsonl_ordering_is_score_then_strategies_then_first_seen(tmp_path):
    res = {
        "token_clone": [
            _pair(_func("a"), _func("b"), "token_clone", 0.9, {"scores": {"clone_type": 1}}),
            _pair(_func("c"), _func("d"), "token_clone", 0.9, {"scores": {"clone_type": 1}}),
            _pair(_func("e"), _func("f"), "token_clone", 0.95, {"scores": {"clone_type": 1}}),
        ],
        "ast_similarity": [
            _pair(_func("c"), _func("d"), "ast_similarity", 0.9),
        ],
    }
    d = _write_detect_dir(tmp_path, res)
    out = tmp_path / "merge"
    r = _run_merge(d, out)
    assert r.returncode == 0, r.stderr
    names = [(p["func_a"]["name"], p["func_b"]["name"]) for p in
             (json.loads(line) for line in (out / "pairs.jsonl").read_text().splitlines())]
    # e/f highest score; c/d has 2 strategies; a/b last (same score as c/d, fewer strategies)
    assert names == [("e", "f"), ("c", "d"), ("a", "b")]


def test_jsonl_detector_input_accepted_and_equal_to_array_input(tmp_path):
    res = _three_signal_corpus(9)
    d1 = _write_detect_dir(tmp_path / "arr", res)
    d2 = _write_detect_dir(tmp_path / "jl", res, jsonl=True)
    r1 = _run_merge(d1, tmp_path / "arr" / "merge")
    r2 = _run_merge(d2, tmp_path / "jl" / "merge")
    assert r1.returncode == 0 and r2.returncode == 0, (r1.stderr, r2.stderr)
    p1 = (tmp_path / "arr" / "merge" / "pairs.jsonl").read_text()
    p2 = (tmp_path / "jl" / "merge" / "pairs.jsonl").read_text()
    assert p1 == p2


# ---------------------------------------------------------------------------
# Caps and resource policy
# ---------------------------------------------------------------------------

def test_refuse_policy_exits_3_and_writes_nothing_partial(tmp_path):
    d = _write_detect_dir(tmp_path, _three_signal_corpus(30))
    out = tmp_path / "merge"
    r = _run_merge(d, out, "--max-pairs", "10", "--resource-policy", "refuse")
    assert r.returncode == 3, (r.returncode, r.stderr)
    assert "REFUSED_RESOURCE" in r.stderr
    assert not (out / "pairs.jsonl").exists()
    assert not (out / "merged-results.json").exists()
    run = json.loads((out / "run.json").read_text())
    assert run["outcome"] == "refused_resource"
    assert run["counts"]["pairs_candidates"] == 30


def test_truncate_policy_keeps_top_n_deterministically_and_records_drop(tmp_path):
    d = _write_detect_dir(tmp_path, _three_signal_corpus(30))
    out_full = tmp_path / "full"
    out_cap = tmp_path / "cap"
    assert _run_merge(d, out_full).returncode == 0
    r = _run_merge(d, out_cap, "--max-pairs", "10", "--resource-policy", "truncate")
    assert r.returncode == 0, r.stderr
    full = (out_full / "pairs.jsonl").read_text().splitlines()
    cap = (out_cap / "pairs.jsonl").read_text().splitlines()
    assert cap == full[:10]
    summary = json.loads((out_cap / "summary.json").read_text())
    run = json.loads((out_cap / "run.json").read_text())
    assert summary["total_pairs"] == 10
    assert summary["complete"] is False
    assert summary["pairs_dropped"] == 20
    assert run["truncated"] is True and run["truncation_reason"].startswith("max_pairs")
    assert run["counts"]["pairs_dropped"] == 20


def test_legacy_json_skipped_above_ceiling_is_explicit(tmp_path):
    d = _write_detect_dir(tmp_path, _three_signal_corpus(20))
    out = tmp_path / "merge"
    r = _run_merge(d, out, "--max-legacy-json-bytes", "512")
    assert r.returncode == 0, r.stderr
    assert not (out / "merged-results.json").exists()
    run = json.loads((out / "run.json").read_text())
    assert run["legacy_export"]["written"] is False
    assert "ceiling" in run["legacy_export"]["reason"]
    assert (out / "pairs.jsonl").exists()


def test_no_legacy_json_flag(tmp_path):
    d = _write_detect_dir(tmp_path, _three_signal_corpus(3))
    out = tmp_path / "merge"
    r = _run_merge(d, out, "--no-legacy-json")
    assert r.returncode == 0, r.stderr
    assert not (out / "merged-results.json").exists()
    assert json.loads((out / "run.json").read_text())["legacy_export"]["written"] is False


def test_input_bytes_cap_refuses_before_merge(tmp_path):
    d = _write_detect_dir(tmp_path, _three_signal_corpus(50))
    out = tmp_path / "merge"
    r = _run_merge(d, out, "--max-input-bytes", "100")
    assert r.returncode == 3
    assert "REFUSED_RESOURCE" in r.stderr and "max_input_bytes" in r.stderr
    assert not (out / "pairs.jsonl").exists()


def test_non_finite_cap_rejected():
    r = subprocess.run([PY, str(MERGE), "/nonexistent", "--max-pairs", "0"],
                       capture_output=True, text=True, timeout=30)
    assert r.returncode == 2
    assert "finite" in r.stderr.lower()


# ---------------------------------------------------------------------------
# Fail-closed input handling
# ---------------------------------------------------------------------------

def test_malformed_detector_file_is_nonzero_with_named_file(tmp_path):
    d = _write_detect_dir(tmp_path, _three_signal_corpus(3))
    (d / "winnowing-results.json").write_text('[{"func_a": {"name": "x"}, ')
    out = tmp_path / "merge"
    r = _run_merge(d, out)
    assert r.returncode == 1, (r.returncode, r.stderr)
    assert "winnowing-results.json" in r.stderr
    assert not (out / "pairs.jsonl").exists()
    run = json.loads((out / "run.json").read_text())
    assert run["outcome"] == "input_error"


def test_no_results_still_writes_complete_artifacts(tmp_path):
    d = tmp_path / "detect"
    d.mkdir()
    out = tmp_path / "merge"
    r = _run_merge(d, out)
    assert r.returncode == 0, r.stderr
    assert json.loads((out / "summary.json").read_text())["total_pairs"] == 0
    assert (out / "pairs.jsonl").read_text() == ""
    legacy = json.loads((out / "merged-results.json").read_text())
    assert legacy == {"pairs": [], "summary": legacy["summary"]}


# ---------------------------------------------------------------------------
# Semantic parity with the previous in-memory implementation
# ---------------------------------------------------------------------------

def test_parity_with_in_memory_merge_on_small_checked_in_fixture(tmp_path):
    """The streamed CLI preserves merge score and ordering on the bounded fixture."""
    fixture = BASE / "tests" / "fixtures" / "baseline-corpus"
    detect_dir = tmp_path / "detect"
    detect_dir.mkdir()
    detector_rows = json.loads((fixture / "detector-output.json").read_text())
    (detect_dir / "fuzzy-name-results.json").write_text(json.dumps(detector_rows))
    all_results = {"fuzzy-name": detector_rows}
    catalog_index = {}
    for fn in json.loads((fixture / "catalog.json").read_text()):
        catalog_index[(fn.get("file", ""), fn.get("line", 0), fn.get("name", ""))] = fn
    expected = merge_mod.merge_pair_signals(all_results, catalog_index=catalog_index)
    out = tmp_path / "merge"
    r = _run_merge(detect_dir, out, "--max-pairs", str(max(10, len(expected) * 2)))
    assert r.returncode == 0, r.stderr
    got = [json.loads(line) for line in (out / "pairs.jsonl").read_text().splitlines()]
    assert len(got) == len(expected)
    assert got == expected
