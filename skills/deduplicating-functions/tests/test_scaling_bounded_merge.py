"""Scaling tests for the bounded merge (plan P1 §6.5).

Tier is selected with DEDUP_SCALE_TIER = 10k (default, always runs) | 100k | 1m.
The merge runs as a subprocess; its peak RSS is read from getrusage(RUSAGE_CHILDREN)
(ru_maxrss is bytes on macOS, KiB on Linux). The assertion is on the *merge
process*, the component that reached 5.25 GB + 22.7 GB on 2026-08-22.

Synthetic candidates are generated on the fly (never checked in): three
detectors flag the same N pairs so every pair is a 3-signal HIGH candidate —
the densest case for the pair index.
"""
from __future__ import annotations

import json
import os
import resource
import subprocess
import sys
import time
from pathlib import Path


BASE = Path(__file__).parent.parent
MERGE = BASE / "scripts" / "merge-signals.py"
PY = sys.executable

TIERS = {"10k": 10_000, "100k": 100_000, "1m": 1_000_000}
TIER = os.environ.get("DEDUP_SCALE_TIER", "10k").lower()
N = TIERS.get(TIER, TIERS["10k"])
# Peak-RSS ceiling for the merge subprocess (plan: < 1.5 GiB at 1M candidates).
RSS_CEILING = {"10k": 400 << 20, "100k": 900 << 20, "1m": 1536 << 20}[TIER if TIER in TIERS else "10k"]


def _gen(detect_dir: Path, n: int) -> None:
    detect_dir.mkdir(parents=True, exist_ok=True)
    strategies = (("token-clone", "token_clone", {"scores": {"clone_type": 1}}),
                  ("ast-similarity", "ast_similarity", {}),
                  ("tfidf-index", "tfidf_index", {}))
    for fname, strat, extra in strategies:
        with open(detect_dir / f"{fname}-results.jsonl", "w") as fh:
            for i in range(n):
                rec = {
                    "func_a": {"name": f"fa{i}", "file": f"src/m{i % 977}.ts", "line": i + 1,
                               "qualified_name": f"fa{i}"},
                    "func_b": {"name": f"fb{i}", "file": f"src/n{i % 983}.ts", "line": i + 7,
                               "qualified_name": f"fb{i}"},
                    "final_score": round(0.80 + (i % 199) / 1000.0, 3),
                    "strategy": strat,
                }
                rec.update(extra)
                fh.write(json.dumps(rec) + "\n")


def _children_maxrss_bytes() -> int:
    ru = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    return ru if sys.platform == "darwin" else ru * 1024


def test_merge_peak_rss_is_bounded(tmp_path):
    detect = tmp_path / "detect"
    _gen(detect, N)
    out = tmp_path / "merge"
    out.mkdir()
    before = _children_maxrss_bytes()
    t0 = time.monotonic()
    r = subprocess.run(
        [PY, str(MERGE), str(detect), "-o", str(out / "merged-results.json"), "--include-summary",
         "--resource-policy", "truncate", "--max-pairs", str(N), "--max-legacy-json-bytes", "1"],
        capture_output=True, text=True, timeout=1700,
    )
    elapsed = time.monotonic() - t0
    after = _children_maxrss_bytes()
    assert r.returncode == 0, r.stderr[-1500:]
    peak = after  # ru_maxrss is the max over all children so far; the merge is the largest
    summary = json.loads((out / "summary.json").read_text())
    run = json.loads((out / "run.json").read_text())
    report = {"tier": TIER, "n": N, "peak_children_rss_bytes": peak, "before_rss_bytes": before,
              "elapsed_s": round(elapsed, 2), "pairs": summary["total_pairs"],
              "legacy_written": run["legacy_export"]["written"],
              "scratch_bytes_pairs_jsonl": (out / "pairs.jsonl").stat().st_size}
    (tmp_path / "scaling-report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report))
    assert summary["total_pairs"] == N
    assert summary["complete"] is True
    assert run["legacy_export"]["written"] is False, "legacy export must stay under its ceiling"
    assert peak < RSS_CEILING, f"merge peak RSS {peak/2**20:.0f} MiB >= ceiling {RSS_CEILING/2**20:.0f} MiB"
    assert not list(out.glob(".merge-scratch-*")), "scratch database must be removed"
