"""Contract tests for scripts/generate_report.py and the generate-report-enhanced.sh shim.

The report generator must read pairs incrementally (pairs.jsonl or a legacy
merged-results.json array via the stream reader), bound rows per section,
state omissions explicitly, write atomically, and reproduce the legacy
markdown exactly for uncapped small inputs (golden parity against the
jq-based script at the reviewed base commit).
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).parent.parent
SCRIPTS = BASE / "scripts"
SHIM = SCRIPTS / "generate-report-enhanced.sh"
GEN = SCRIPTS / "generate_report.py"
PY = sys.executable
LEGACY_REF = "8c6f82fbc9a3066f523de7b0cc65713fe26a688a"


def _pair(a, b, clone_type, confidence, score=0.9, n=3, strategies=None, action="CONSOLIDATE"):
    return {
        "func_a": {"name": a, "file": "a.ts", "line": 1, "qualified_name": a, "end_line": 10},
        "func_b": {"name": b, "file": "b.ts", "line": 2, "qualified_name": b, "end_line": 12},
        "composite_score": score,
        "confidence": confidence,
        "num_strategies": n,
        "strategies": strategies or {"token_clone": score, "tfidf_index": 0.8},
        "clone_type": clone_type,
        "recommendation": {"action": action, "urgency": "immediate", "reason": "test pair"},
    }


def _summary(pairs):
    s = {"total_pairs": len(pairs), "by_confidence": {}, "by_clone_type": {}, "by_action": {},
         "strategies_used": ["tfidf_index", "token_clone"], "multi_signal_pairs": len(pairs),
         "defense_depth_pairs": len(pairs)}
    for p in pairs:
        s["by_confidence"][p["confidence"]] = s["by_confidence"].get(p["confidence"], 0) + 1
        s["by_clone_type"][p["clone_type"]] = s["by_clone_type"].get(p["clone_type"], 0) + 1
        a = p["recommendation"]["action"]
        s["by_action"][a] = s["by_action"].get(a, 0) + 1
    return s


def _mixed_pairs():
    return [
        _pair("alpha", "beta", "Type 1 (exact clone)", "HIGH", 1.0),
        _pair("gamma", "delta", "Type 2 (renamed clone)", "HIGH", 0.95),
        _pair("eps", "zeta", "Type 3 (near-miss clone)", "HIGH", 0.85),
        _pair("eta", "theta", "Type 3 (near-miss clone)", "MEDIUM", 0.7, 2, action="INVESTIGATE"),
        _pair("iota", "kappa", "Type 4 (semantic clone)", "MEDIUM", 0.6, 1, {"fuzzy_name": 0.6}, "INVESTIGATE"),
        _pair("lam", "mu", "Type 4 (semantic clone)", "LOW", 0.4, 1, {"metric_similarity": 0.4}, "REVIEW"),
    ]


def _write_legacy(tmp_path, pairs, name="merged-results.json"):
    p = tmp_path / name
    p.write_text(json.dumps({"pairs": pairs, "summary": _summary(pairs)}, indent=2))
    return p


def _write_new_layout(tmp_path, pairs):
    d = tmp_path / "merge"
    d.mkdir()
    (d / "pairs.jsonl").write_text("".join(json.dumps(p) + "\n" for p in pairs))
    (d / "summary.json").write_text(json.dumps(_summary(pairs)))
    return d


def _legacy_script(tmp_path) -> Path:
    """Materialize the jq-based generator from the reviewed base commit."""
    out = tmp_path / "legacy-generate-report.sh"
    r = subprocess.run(
        ["git", "-C", str(BASE), "show",
         f"{LEGACY_REF}:skills/deduplicating-functions/scripts/generate-report-enhanced.sh"],
        capture_output=True, text=True, timeout=30,
    )
    assert r.returncode == 0, f"legacy script unavailable from git: {r.stderr[:200]}"
    out.write_text(r.stdout)
    return out


def _normalize(md: str) -> str:
    return re.sub(r"Generated: \d{4}-\d{2}-\d{2} \d{2}:\d{2}", "Generated: <ts>", md)


def test_generator_exists_and_shim_execs_it():
    assert GEN.exists(), "scripts/generate_report.py missing"
    text = SHIM.read_text()
    assert "generate_report.py" in text
    invocations = [
        line for line in text.splitlines()
        if re.search(r"(^|[\s;|&(])jq(\s|$)", line.split("#", 1)[0])
    ]
    assert invocations == [], f"shim must not invoke jq: {invocations}"


def test_golden_parity_with_legacy_jq_script_on_legacy_input(tmp_path):
    jq_probe = subprocess.run(["which", "jq"], capture_output=True, text=True)
    assert jq_probe.returncode == 0, "jq is required for the legacy parity reference"
    legacy_script = _legacy_script(tmp_path)
    merged = _write_legacy(tmp_path, _mixed_pairs())
    ref_out = tmp_path / "ref.md"
    new_out = tmp_path / "new.md"
    r1 = subprocess.run(["bash", str(legacy_script), str(merged), str(ref_out)],
                        capture_output=True, text=True, timeout=60)
    r2 = subprocess.run(["bash", str(SHIM), str(merged), str(new_out)],
                        capture_output=True, text=True, timeout=60)
    assert r1.returncode == 0, r1.stderr
    assert r2.returncode == 0, r2.stderr
    assert _normalize(new_out.read_text()) == _normalize(ref_out.read_text())


def test_new_layout_input_matches_legacy_input(tmp_path):
    pairs = _mixed_pairs()
    merged = _write_legacy(tmp_path, pairs)
    d = _write_new_layout(tmp_path, pairs)
    o1, o2 = tmp_path / "a.md", tmp_path / "b.md"
    assert subprocess.run(["bash", str(SHIM), str(merged), str(o1)], capture_output=True, text=True).returncode == 0
    assert subprocess.run(["bash", str(SHIM), str(d), str(o2)], capture_output=True, text=True).returncode == 0
    assert _normalize(o1.read_text()) == _normalize(o2.read_text())


def test_row_cap_is_explicit_and_counts_come_from_summary(tmp_path):
    pairs = [_pair(f"h{i}", f"k{i}", "Type 1 (exact clone)", "HIGH", 0.99 - i / 1000) for i in range(40)]
    d = _write_new_layout(tmp_path, pairs)
    out = tmp_path / "r.md"
    r = subprocess.run([PY, str(GEN), str(d), str(out), "--max-rows-per-section", "5"],
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    md = out.read_text()
    assert "| HIGH confidence | 40 |" in md, "summary counts must be the full totals"
    assert md.count("### h") == 5, "HIGH section must be capped at 5 entries"
    assert "35 additional HIGH pair(s) omitted (cap 5)" in md


def test_default_cap_is_finite():
    r = subprocess.run([PY, str(GEN), "--help"], capture_output=True, text=True, timeout=30)
    assert r.returncode == 0
    m = re.search(r"--max-rows-per-section.*?default:\s*(\d+)", r.stdout, re.S)
    assert m and int(m.group(1)) > 0


def test_malformed_input_fails_closed_and_leaves_no_output(tmp_path):
    bad = tmp_path / "merged-results.json"
    bad.write_text('{"pairs": [{"func_a": ')
    out = tmp_path / "r.md"
    out.write_text("previous")
    r = subprocess.run(["bash", str(SHIM), str(bad), str(out)], capture_output=True, text=True, timeout=60)
    assert r.returncode != 0
    assert "merged-results.json" in r.stderr
    assert out.read_text() == "previous", "a failed run must not clobber the previous report"


def test_missing_input_is_error_exit_1():
    r = subprocess.run(["bash", str(SHIM), "/nonexistent/merged.json", "/tmp/x.md"],
                       capture_output=True, text=True, timeout=30)
    assert r.returncode == 1


def test_streams_large_legacy_array_without_loading(tmp_path, monkeypatch):
    """A 20k-pair legacy document must be processed with a bounded buffer."""
    pairs = [_pair(f"h{i}", f"k{i}", "Type 1 (exact clone)", "LOW", 0.4, 1, {"fuzzy_name": 0.4}, "REVIEW")
             for i in range(20000)]
    merged = _write_legacy(tmp_path, pairs)
    out = tmp_path / "r.md"
    r = subprocess.run([PY, str(GEN), str(merged), str(out), "--max-rows-per-section", "3",
                        "--max-buffer-bytes", "262144"],
                       capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr
    assert "19997 additional LOW pair(s) omitted (cap 3)" in out.read_text()
