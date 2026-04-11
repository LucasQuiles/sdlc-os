# Gap Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close 4 feature-sweep gaps: shell eval parity, decision records for manual workflows, and a pure-Python report generator.

**Architecture:** Add `--eval-corpus` to orchestrate.sh (mirrors run_pipeline.py), write two ADR decision records, and create generate-report.py to eliminate the bash+jq dependency.

**Tech Stack:** Bash (orchestrate.sh), Python 3.10+ (report generator), pytest (tests)

**Working directory:** `/Users/q/.claude/plugins/sdlc-os/skills/deduplicating-functions`

---

## Task 1: Add `--eval-corpus` to orchestrate.sh (GC-001)

**Files:**
- Modify: `scripts/orchestrate.sh` (arg parsing + new phase_evaluate function)

- [ ] **Step 1: Add --eval-corpus to arg parsing**

In `scripts/orchestrate.sh`, add after the `--threshold` case (around line 70):

```bash
        --eval-corpus) EVAL_CORPUS="$2"; shift 2 ;;
```

Add default at top with other defaults (around line 55):

```bash
EVAL_CORPUS=""
```

Add to help text (around line 23):

```
    --eval-corpus FILE      Evaluate results against ground truth corpus (runs Phase 4)
```

- [ ] **Step 2: Add phase_evaluate function**

Add before the `main()` function:

```bash
# ═══════════════════════════════════════════════════════════════════
# PHASE 4: EVALUATE (optional)
# ═══════════════════════════════════════════════════════════════════

phase_evaluate() {
    [[ -z "$EVAL_CORPUS" ]] && return

    log "═══ Phase 4: EVALUATE ═══"

    local merged="$OUTPUT_DIR/merge/merged-results.json"
    local eval_out="$OUTPUT_DIR/evaluation.json"

    if [[ ! -f "$merged" ]]; then
        log "  WARNING: merged results not found at $merged"
        return
    fi

    if [[ ! -f "$EVAL_CORPUS" ]]; then
        log "  ERROR: corpus file not found at $EVAL_CORPUS"
        return 1
    fi

    "$PYTHON" "$SCRIPT_DIR/evaluate.py" \
        --results "$merged" \
        --corpus "$EVAL_CORPUS" \
        -o "$eval_out" 2>>"$OUTPUT_DIR/pipeline.log"

    if [[ -f "$eval_out" ]]; then
        local summary
        summary=$(jq -r '.summary // "no summary"' "$eval_out" 2>/dev/null || echo "parse error")
        log "  Evaluation: $summary"
        log "  Results: $eval_out"
    else
        log "  WARNING: evaluation produced no output"
    fi
}
```

- [ ] **Step 3: Wire phase_evaluate into main()**

In the `main()` function, add after `phase_report`:

```bash
    phase_report
    echo "" >&2
    phase_evaluate
```

- [ ] **Step 4: Test manually**

```bash
# Test with adversarial corpus
bash scripts/orchestrate.sh scripts/ -o /tmp/orch-eval --eval-corpus tests/fixtures/adversarial-corpus.json --skip-llm 2>&1 | tail -10

# Verify evaluation.json exists
cat /tmp/orch-eval/evaluation.json | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['summary'])"

# Test without --eval-corpus (should skip Phase 4)
bash scripts/orchestrate.sh scripts/ -o /tmp/orch-noeval --skip-llm 2>&1 | grep -c "Phase 4"
# Expected: 0

rm -rf /tmp/orch-eval /tmp/orch-noeval
```

- [ ] **Step 5: Commit**

```bash
git add scripts/orchestrate.sh
git commit -m "feat: add --eval-corpus to orchestrate.sh (GC-001 shell eval parity)"
```

---

## Task 2: Write ADR for manual semantic follow-up (GC-003)

**Files:**
- Create: `docs/decisions/2026-04-10-adr-semantic-follow-up.md`

- [ ] **Step 1: Write the decision record**

Create `docs/decisions/2026-04-10-adr-semantic-follow-up.md`:

```markdown
# ADR: Semantic Follow-Up Remains Manual By Design

**Status:** Accepted
**Date:** 2026-04-10
**Context:** The 11-detector classical pipeline is fully automated and deterministic. The LLM-based semantic follow-up (categorize -> split -> per-category opus analysis) requires subagent dispatch, which introduces nondeterminism and cost. The feature sweep (FF-002) flagged the --skip-llm flag as a no-op stub.

**Decision:** Semantic follow-up stays manual. The automated pipeline produces deterministic, reproducible results. Manual semantic review is a follow-up step that users invoke when the classical pipeline's output warrants deeper analysis.

**Consequences:**
- --skip-llm in orchestrate.sh controls whether the manual follow-up reminder is printed, not whether automation runs.
- SKILL.md documents the three-step manual workflow (categorize-prompt.md -> prepare-category-analysis.sh -> find-duplicates-prompt.md).
- No subagent dispatch is added to the pipeline runners.
- If future demand justifies automation, it should be a separate --auto-semantic flag with explicit cost/nondeterminism warnings.
```

- [ ] **Step 2: Commit**

```bash
mkdir -p docs/decisions
git add docs/decisions/2026-04-10-adr-semantic-follow-up.md
git commit -m "docs: ADR — semantic follow-up remains manual by design (GC-003)"
```

---

## Task 3: Write ADR for threshold semantics (GC-004)

**Files:**
- Create: `docs/decisions/2026-04-10-adr-threshold-merge-only.md`

- [ ] **Step 1: Write the decision record**

Create `docs/decisions/2026-04-10-adr-threshold-merge-only.md`:

```markdown
# ADR: --threshold Affects Merge Phase Only

**Status:** Accepted
**Date:** 2026-04-10
**Context:** The --threshold flag in orchestrate.sh and --high-threshold in merge-signals.py control the HIGH confidence cutoff during the merge phase. Individual detectors have their own internal thresholds (e.g., detect-fuzzy-names.py defaults to 0.35, detect-lsh-ast.py defaults to 0.75). The feature sweep (FF-007) noted this is potentially misleading.

**Decision:** --threshold remains merge-only. Detector thresholds are internal calibration that should not be exposed via a single global flag because:
1. Each detector's threshold has different semantics (similarity score, Jaccard index, etc.)
2. A single value would either be too aggressive for some detectors or too permissive for others
3. The merge phase is where multi-signal confidence is computed — that's the right place for user-facing threshold control

**Consequences:**
- Help text explicitly says "Merge-phase HIGH confidence cutoff only"
- Individual detector thresholds are set via their hardcoded defaults (tuned during the experiment branch)
- If per-detector tuning is needed, add --detect-threshold-<name> flags rather than overloading the global flag
```

- [ ] **Step 2: Commit**

```bash
git add docs/decisions/2026-04-10-adr-threshold-merge-only.md
git commit -m "docs: ADR — threshold is merge-only by design (GC-004)"
```

---

## Task 4: Create pure-Python report generator (GC-002)

**Files:**
- Create: `scripts/generate-report.py`
- Create: `tests/test_report_generator.py`
- Modify: `run_pipeline.py` (prefer Python generator)

### Step 1: Write failing tests

- [ ] **Step 1a: Create test file with basic contract tests**

Create `tests/test_report_generator.py`:

```python
"""Tests for the pure-Python report generator."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys

import pytest

PYTHON = sys.executable
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GENERATOR = os.path.join(BASE, "scripts", "generate-report.py")
MERGED_SAMPLE = os.path.join(BASE, "output", "merge", "merged-results.json")


def test_generator_runs_without_error(tmp_path):
    """The generator should exit 0 on valid merged input."""
    out = tmp_path / "report.md"
    result = subprocess.run(
        [PYTHON, GENERATOR, MERGED_SAMPLE, str(out)],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, f"Failed: {result.stderr[:500]}"
    assert out.exists()


def test_generator_produces_markdown_with_headers(tmp_path):
    """Report should have standard section headers."""
    out = tmp_path / "report.md"
    subprocess.run(
        [PYTHON, GENERATOR, MERGED_SAMPLE, str(out)],
        capture_output=True, text=True, timeout=30,
    )
    content = out.read_text()
    assert "# Duplicate Function Detection Report" in content
    assert "## HIGH Confidence" in content
    assert "## Summary" in content


def test_generator_includes_pair_details(tmp_path):
    """Report should include function names and scores from merged input."""
    out = tmp_path / "report.md"
    subprocess.run(
        [PYTHON, GENERATOR, MERGED_SAMPLE, str(out)],
        capture_output=True, text=True, timeout=30,
    )
    content = out.read_text()
    with open(MERGED_SAMPLE) as f:
        data = json.load(f)
    if data["pairs"]:
        first_name = data["pairs"][0]["func_a"]["name"]
        assert first_name in content, f"Expected {first_name} in report"


def test_generator_handles_empty_input(tmp_path):
    """Empty merged results should produce a valid report."""
    empty_input = tmp_path / "empty.json"
    empty_input.write_text(json.dumps({"pairs": [], "summary": {
        "total_pairs": 0, "by_confidence": {},
        "by_clone_type": {}, "by_action": {},
        "strategies_used": [], "multi_signal_pairs": 0,
        "defense_depth_pairs": 0,
    }}))
    out = tmp_path / "report.md"
    result = subprocess.run(
        [PYTHON, GENERATOR, str(empty_input), str(out)],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0
    content = out.read_text()
    assert "No duplicate pairs detected" in content or "0 pairs" in content.lower()


def test_generator_is_deterministic(tmp_path):
    """Two runs on same input should produce identical output."""
    out1 = tmp_path / "r1.md"
    out2 = tmp_path / "r2.md"
    for out in [out1, out2]:
        subprocess.run(
            [PYTHON, GENERATOR, MERGED_SAMPLE, str(out)],
            capture_output=True, text=True, timeout=30,
        )
    ts_re = re.compile(
        r"\b\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(?::\d{2})?\b"
        r"|\b\d{2}:\d{2}(?::\d{2})?\b"
    )
    c1 = ts_re.sub("<TS>", out1.read_text())
    c2 = ts_re.sub("<TS>", out2.read_text())
    assert c1 == c2, "Report generator is nondeterministic"
```

- [ ] **Step 1b: Run tests to verify they fail**

```bash
python3 -m pytest tests/test_report_generator.py -v --tb=short 2>&1 | tail -10
# Expected: FAILED (generate-report.py does not exist yet)
```

### Step 2: Implement the generator

- [ ] **Step 2a: Create `scripts/generate-report.py`**

```python
#!/usr/bin/env python3
"""Pure-Python report generator for duplicate function detection.

Replaces generate-report-enhanced.sh to eliminate the bash+jq dependency.
Reads merged-results.json (with --include-summary) and produces a
Markdown report grouped by confidence level.

Usage:
    python3 generate-report.py merged-results.json report.md
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path


def generate_report(merged_path: str, output_path: str) -> None:
    with open(merged_path) as f:
        data = json.load(f)

    pairs = data.get("pairs", [])
    summary = data.get("summary", {})
    lines: list[str] = []

    # Header
    lines.append("# Duplicate Function Detection Report")
    lines.append("")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")

    # Summary
    total = summary.get("total_pairs", len(pairs))
    by_conf = summary.get("by_confidence", {})
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Total pairs:** {total}")
    for level in ["HIGH", "MEDIUM", "LOW"]:
        count = by_conf.get(level, 0)
        if count > 0:
            lines.append(f"- **{level}:** {count}")
    lines.append(f"- **Multi-signal (2+):** {summary.get('multi_signal_pairs', 0)}")
    lines.append(f"- **Defense depth (3+):** {summary.get('defense_depth_pairs', 0)}")
    strategies = summary.get("strategies_used", [])
    if strategies:
        lines.append(f"- **Strategies:** {', '.join(strategies)}")
    lines.append("")

    if not pairs:
        lines.append("No duplicate pairs detected.")
        lines.append("")
        Path(output_path).write_text("\n".join(lines))
        return

    # Group by confidence
    by_level: dict[str, list[dict]] = {"HIGH": [], "MEDIUM": [], "LOW": []}
    for pair in pairs:
        level = pair.get("confidence", "LOW")
        by_level.setdefault(level, []).append(pair)

    for level in ["HIGH", "MEDIUM", "LOW"]:
        level_pairs = by_level.get(level, [])
        if not level_pairs:
            continue

        lines.append(f"## {level} Confidence ({len(level_pairs)} pairs)")
        lines.append("")

        for pair in level_pairs:
            fa = pair["func_a"]
            fb = pair["func_b"]
            score = pair.get("composite_score", 0)
            clone_type = pair.get("clone_type", "unknown")
            num_strats = pair.get("num_strategies", 0)
            strats = pair.get("strategies", {})
            rec = pair.get("recommendation", {})

            lines.append(
                f"### `{fa['name']}` ({fa['file']}:{fa['line']}) "
                f"<-> `{fb['name']}` ({fb['file']}:{fb['line']})"
            )
            lines.append("")
            lines.append(
                f"- **Score:** {score:.3f} | **Type:** {clone_type} "
                f"| **Strategies:** {num_strats}"
            )

            if strats:
                strat_details = ", ".join(
                    f"{k}={v:.2f}" for k, v in sorted(strats.items())
                )
                lines.append(f"- **Details:** {strat_details}")

            action = rec.get("action", "REVIEW")
            reason = rec.get("reason", "")
            if action:
                lines.append(f"- **Action:** {action}")
            if reason:
                lines.append(f"  > {reason}")
            lines.append("")

    Path(output_path).write_text("\n".join(lines))


def main() -> None:
    if len(sys.argv) < 3:
        print(
            "Usage: generate-report.py <merged-results.json> <output.md>",
            file=sys.stderr,
        )
        sys.exit(1)
    generate_report(sys.argv[1], sys.argv[2])


if __name__ == "__main__":
    main()
```

- [ ] **Step 2b: Run tests**

```bash
python3 -m pytest tests/test_report_generator.py -v --tb=short 2>&1 | tail -10
# Expected: all pass
```

- [ ] **Step 2c: Commit**

```bash
git add scripts/generate-report.py tests/test_report_generator.py
git commit -m "feat: pure-Python report generator (GC-002)"
```

### Step 3: Wire into run_pipeline.py

- [ ] **Step 3a: Update run_pipeline.py to prefer Python generator**

In `run_pipeline.py`, Phase 3 report section, change to try the Python generator first:

```python
    # ── Phase 3: REPORT ──────────────────────────────────────────────
    log("=== Phase 3: REPORT ===")

    py_report_script = os.path.join(SCRIPTS, "generate-report.py")
    sh_report_script = os.path.join(SCRIPTS, "generate-report-enhanced.sh")
    report_out = os.path.join(out, "duplicates-report.md")

    if os.path.exists(py_report_script):
        report_result = run([PYTHON, py_report_script, merged_out, report_out],
                            label="generate-report-py", check=False, log_file=log_file)
    elif os.path.exists(sh_report_script):
        report_result = run(["bash", sh_report_script, merged_out, report_out],
                            label="generate-report-sh", check=False, log_file=log_file)
    else:
        report_result = None
```

Keep the existing strict gate logic after this block.

- [ ] **Step 3b: Run full test suite**

```bash
python3 -m pytest tests/ -q --tb=line 2>&1 | tail -3
# Expected: all pass (415+ with new report tests)
```

- [ ] **Step 3c: Commit**

```bash
git add run_pipeline.py
git commit -m "feat: run_pipeline.py prefers Python report generator over bash+jq"
```

---

## Task 5: Clean remaining dead code (reviewer S-3)

**Files:**
- Modify: `scripts/orchestrate.sh` (remove dead generate-report.sh fallback)

- [ ] **Step 1: Remove dead fallback in phase_report**

In `scripts/orchestrate.sh` phase_report function, remove the `elif` block that references `generate-report.sh` (which does not exist).

- [ ] **Step 2: Commit**

```bash
git add scripts/orchestrate.sh
git commit -m "fix: remove dead generate-report.sh fallback in orchestrate.sh (reviewer S-3)"
```

---

## Verification

After all tasks:

```bash
# Full test suite
python3 -m pytest tests/ -q --tb=line

# Shell eval parity
bash scripts/orchestrate.sh scripts/ -o /tmp/final-eval --eval-corpus tests/fixtures/adversarial-corpus.json --skip-llm 2>&1 | grep "Evaluation"

# Python report from run_pipeline.py
python3 run_pipeline.py scripts/ -o /tmp/final-py --strict 2>&1 | grep "generate-report"

# Decision records exist
ls docs/decisions/

# Clean up
rm -rf /tmp/final-eval /tmp/final-py
```
