# Telemetry Enforcement — Gate Automation for Thinker Enhancement Artifacts

**Date:** 2026-03-30
**Status:** Draft (rev 2 — addresses 5 review findings)
**Profile:** REPAIR
**Problem:** 41 active tasks, zero telemetry artifacts. Gates are prose instructions, not enforced checkpoints.

---

## Problem Statement

The SDLC-OS has 5 telemetry pipelines (Quality Budget, Hazard/Defense Ledger, Stressor Harvesting, Decision-Noise Controls, Mode/Convergence Signals) with working derivation scripts, validation hooks, and system ledgers. But zero data flows because:

1. **Gates are prose.** The orchestrate SKILL.md says "run derive-quality-budget.sh before Synthesize" but nothing enforces this.
2. **No hook blocks phase transitions.** Existing hooks validate artifact FORMAT on Write/Edit, but nothing checks artifact EXISTENCE at phase boundaries.
3. **The Conductor must remember 21 manual steps.** No checklist, no automation, no accountability.
4. **Bead turbulence is never populated.** Beads carry `{L0: 0, L1: 0, ...}` placeholders that are never incremented during execution.

---

## Task Classification Rules

The automation scripts need deterministic rules to decide which telemetry lanes apply. Classification uses a two-layer approach: **artifact presence first** (most reliable), **bead metadata grep as fallback** (handles tasks that predate the telemetry system).

### STPA-required

**Primary:** `hazard-defense-ledger.yaml` exists in the task directory (created by safety-analyst during Architect).

**Fallback:** Any bead file in `beads/*.md` matches `grep -rl "\*\*Cynefin domain:\*\*.*complex\|\*\*Security sensitive:\*\*.*true"` (handles bold markdown formatting used in bead files).

### Stress-sampled

**Primary:** `stress-session.yaml` exists in the task directory (created by FFT-15 evaluation during Execute).

No fallback needed — the artifact IS the decision record.

### AQS-engaged

**Primary:** `decision-noise-summary.yaml` exists in the task directory, OR the system-level `review-passes.jsonl` contains entries for this task_id.

**Fallback:** Any bead file matches `grep -rl "\*\*Cynefin domain:\*\*.*complicated\|\*\*Cynefin domain:\*\*.*complex\|\*\*Cynefin domain:\*\*.*chaotic"`. Note: this is a superset of the orchestrate skip-condition (Clear beads under healthy budget skip AQS). A complicated bead classified here may have had AQS skipped by FFT — the primary check (artifact/ledger presence) is authoritative.

### No beads

If `beads/` is empty or absent, the task has no derivable telemetry. The gate checker reports this as a warning (not failure) — the task may be an INVESTIGATE or early-stage task.

### Classification in scripts

This function is added to `scripts/lib/sdlc-common.sh` and used by BOTH `run-synthesize-gates.sh` and `run-complete-gates.sh` to ensure phase-stable classification. The gate checker also uses it.

```bash
# classify_task_lanes <task-dir> <task-id> <project-dir>
# Sets global variables: HAS_BEADS, IS_STPA, IS_AQS, IS_STRESSED
classify_task_lanes() {
  local task_dir="$1" task_id="$2" project_dir="$3"

  HAS_BEADS=false; IS_STPA=false; IS_AQS=false; IS_STRESSED=false

  # Artifact-first classification (most reliable)
  [ -f "$task_dir/hazard-defense-ledger.yaml" ] && IS_STPA=true
  [ -f "$task_dir/stress-session.yaml" ] && IS_STRESSED=true
  [ -f "$task_dir/decision-noise-summary.yaml" ] && IS_AQS=true
  grep -qF "\"$task_id\"" "$project_dir/docs/sdlc/decision-noise/review-passes.jsonl" 2>/dev/null && IS_AQS=true

  # Bead metadata fallback (handles bold markdown formatting)
  if [ -d "$task_dir/beads" ] && ls "$task_dir/beads/"*.md &>/dev/null; then
    HAS_BEADS=true
    if [ "$IS_STPA" = false ]; then
      grep -rlq "\*\*Cynefin domain:\*\*.*complex\|\*\*Security sensitive:\*\*.*true" "$task_dir/beads/" 2>/dev/null && IS_STPA=true
    fi
    # NOTE: Implementation uses artifact-only IS_AQS (no bead fallback).
    # See scripts/lib/sdlc-common.sh classify_task_lanes() for current logic.
  fi
}
```

Both automation scripts call `classify_task_lanes "$TASK_DIR" "$TASK_ID" "$PROJECT_DIR"` and get identical results.

---

## Design

### 1. Gate Checker Script (`scripts/check-sdlc-gates.sh`)

Deterministic validator for phase transitions. Checks BOTH task-local artifacts AND system ledger append success.

```
Usage: check-sdlc-gates.sh <task-dir> <target-phase> --project-dir <dir>

Target phases: synthesize | complete

Exit codes:
  0 = all gates pass
  1 = gate failures (details on stderr)
  2 = usage error
```

**Synthesize gate checks:**
- `quality-budget.yaml` exists with `artifact_status: ready`
- All derived fields non-null (except `estimate_s`, `sli_readings`)
- If STPA-required: `hazard-defense-ledger.yaml` exists with `artifact_status: active`+
- If stress-sampled: `stress-session.yaml` exists with `artifact_status: active`+
- If AQS-engaged: `decision-noise-summary.yaml` exists with `artifact_status: partial`+
- `mode-convergence-summary.yaml` exists with `artifact_status: partial`+

**Complete gate checks (task-local):**
- `quality-budget.yaml` exists with `artifact_status: final`
- `sli_readings`: WARN on null (not fail). SLI population requires project-specific deterministic checks (lint, tsc, test coverage) that the automation scripts cannot run generically. Full enforcement deferred until Conductor or project hook populates them before calling run-complete-gates.sh.
- `budget_state` computed
- If STPA-required: HDL `artifact_status: final`, all records resolved
- If stress-sampled: `stress-session.yaml` `artifact_status: final`
- If AQS-engaged: `decision-noise-summary.yaml` `artifact_status: final`
- `mode-convergence-summary.yaml` `artifact_status: final`

**Complete gate checks (system ledger verification):**
- `system-budget.jsonl` contains an entry with this `task_id`
- If STPA-required: `system-hazard-defense.jsonl` contains an entry with this `task_id`
- If stress-sampled: `system-stress.jsonl` contains an entry with this `task_id`
- `system-mode-convergence.jsonl` contains an entry with this `task_id`

Ledger verification: `grep -qF "\"$TASK_ID\"" "$LEDGER_PATH"`. If the ledger file doesn't exist, that's also a failure.

### 2. Synthesize Automation Script (`scripts/run-synthesize-gates.sh`)

Runs all applicable derivation scripts, then validates. Uses the deterministic classification rules above — no prose decisions.

```bash
#!/bin/bash
# Usage: run-synthesize-gates.sh <task-dir> <project-dir>
set -euo pipefail

TASK_DIR="$1"
PROJECT_DIR="$2"
TASK_ID=$(basename "$TASK_DIR")

# --- Classification: shared function from sdlc-common.sh ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/sdlc-common.sh"
classify_task_lanes "$TASK_DIR" "$TASK_ID" "$PROJECT_DIR"
# Sets: HAS_BEADS, IS_STPA, IS_AQS, IS_STRESSED

echo "=== Synthesize Gates: $TASK_ID ==="
echo "Beads: $HAS_BEADS | STPA: $IS_STPA | AQS: $IS_AQS | Stressed: $IS_STRESSED"

# --- 1. Quality budget (always, if beads exist) ---
if [ "$HAS_BEADS" = true ]; then
  echo "[1/5] Deriving quality budget..."
  "$SCRIPT_DIR/derive-quality-budget.sh" "$TASK_DIR" --status ready
fi

# --- 2. HDL summary (if STPA-required) ---
if [ "$IS_STPA" = true ] && [ -f "$TASK_DIR/hazard-defense-ledger.yaml" ]; then
  echo "[2/5] Deriving HDL summary..."
  "$SCRIPT_DIR/derive-hazard-defense-summary.sh" "$TASK_DIR" --status active
fi

# --- 3. Decision-noise summary (if AQS-engaged) ---
if [ "$IS_AQS" = true ]; then
  echo "[3/5] Deriving decision-noise summary..."
  "$SCRIPT_DIR/derive-decision-noise-summary.sh" "$TASK_ID" "$PROJECT_DIR" --status partial || echo "WARN: decision-noise derivation skipped (no review passes)" >&2
fi

# --- 4. Mode-convergence summary (always, if beads exist) ---
if [ "$HAS_BEADS" = true ]; then
  echo "[4/5] Deriving mode-convergence summary..."
  "$SCRIPT_DIR/derive-mode-convergence-summary.sh" "$TASK_DIR" --status partial
fi

# --- 5. Validate all synthesize gates ---
echo "[5/5] Checking synthesize gates..."
"$SCRIPT_DIR/check-sdlc-gates.sh" "$TASK_DIR" synthesize --project-dir "$PROJECT_DIR"
```

Note: `classify-execution-mode.sh` is removed — mode classification is already done inside `derive-mode-convergence-summary.sh`.

Stress-session.yaml is NOT created here. It was created during Execute by FFT-15 evaluation. If FFT-15 didn't trigger, there's no session to derive. The gate checker handles this: if `stress-session.yaml` doesn't exist, the stressed-task gates don't apply.

### 3. Complete Automation Script (`scripts/run-complete-gates.sh`)

Finalizes all artifacts, appends to system ledgers, verifies ledger entries exist.

```bash
#!/bin/bash
# Usage: run-complete-gates.sh <task-dir> <project-dir>
set -euo pipefail

TASK_DIR="$1"
PROJECT_DIR="$2"
TASK_ID=$(basename "$TASK_DIR")
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# --- Classification: SAME shared function as synthesize ---
source "$SCRIPT_DIR/lib/sdlc-common.sh"
classify_task_lanes "$TASK_DIR" "$TASK_ID" "$PROJECT_DIR"
# Sets: HAS_BEADS, IS_STPA, IS_AQS, IS_STRESSED

echo "=== Complete Gates: $TASK_ID ==="

# --- 1. Finalize quality budget ---
if [ "$HAS_BEADS" = true ]; then
  echo "[1/6] Finalizing quality budget..."
  "$SCRIPT_DIR/derive-quality-budget.sh" "$TASK_DIR" --status final
fi

# --- 2. Finalize HDL (if STPA) ---
if [ "$IS_STPA" = true ] && [ -f "$TASK_DIR/hazard-defense-ledger.yaml" ]; then
  echo "[2/6] Finalizing HDL..."
  "$SCRIPT_DIR/derive-hazard-defense-summary.sh" "$TASK_DIR" --status final
fi

# --- 3. Finalize decision-noise summary (if AQS-engaged) ---
if [ "$IS_AQS" = true ]; then
  echo "[3/8] Finalizing decision-noise summary..."
  "$SCRIPT_DIR/derive-decision-noise-summary.sh" "$TASK_ID" "$PROJECT_DIR" --status final || echo "WARN: decision-noise finalization skipped" >&2
fi

# --- 4. Finalize stress session (if stressed) ---
if [ "$IS_STRESSED" = true ]; then
  echo "[4/8] Finalizing stress session..."
  # Write artifact_status: final to stress-session.yaml, then update stressor library
  python3 -c "
import yaml
with open('$TASK_DIR/stress-session.yaml') as f:
    data = yaml.safe_load(f)
data['artifact_status'] = 'final'
with open('$TASK_DIR/stress-session.yaml', 'w') as f:
    yaml.dump(data, f, default_flow_style=False, sort_keys=False)
"
  "$SCRIPT_DIR/update-stressor-library.sh" "$TASK_DIR" "$SCRIPT_DIR/../references/stressor-library.yaml" "$PROJECT_DIR"
fi

# --- 5. Finalize mode-convergence ---
if [ "$HAS_BEADS" = true ]; then
  echo "[5/8] Finalizing mode-convergence summary..."
  "$SCRIPT_DIR/derive-mode-convergence-summary.sh" "$TASK_DIR" --status final
fi

# --- 6. Append to ALL applicable system ledgers ---
echo "[6/8] Appending to system ledgers..."
if [ "$HAS_BEADS" = true ]; then
  "$SCRIPT_DIR/append-system-budget.sh" "$TASK_DIR" "$PROJECT_DIR"
fi
if [ "$IS_STPA" = true ] && [ -f "$TASK_DIR/hazard-defense-ledger.yaml" ]; then
  "$SCRIPT_DIR/append-system-hazard-defense.sh" "$TASK_DIR" "$PROJECT_DIR"
fi
if [ "$IS_STRESSED" = true ]; then
  "$SCRIPT_DIR/append-system-stress.sh" "$TASK_DIR" "$PROJECT_DIR"
fi
if [ "$HAS_BEADS" = true ]; then
  "$SCRIPT_DIR/append-system-mode-convergence.sh" "$TASK_DIR" "$PROJECT_DIR"
fi

# --- 7. Validate ALL complete gates (task-local + system ledger) ---
echo "[7/8] Checking complete gates..."
"$SCRIPT_DIR/check-sdlc-gates.sh" "$TASK_DIR" complete --project-dir "$PROJECT_DIR"
```

### 4. Advisory Hook (`hooks/scripts/warn-phase-transition.sh`)

Simplified contract: the hook re-runs `check-sdlc-gates.sh` against current filesystem state. No gate-run marker or stamp file — the check is idempotent and deterministic.

```bash
#!/bin/bash
# Triggers on state.md Write/Edit. Warns if gate check fails.
set -euo pipefail

input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // .tool_input.path // empty')

# Only trigger on state.md writes
[[ "$file_path" == */state.md ]] || exit 0

TASK_DIR=$(dirname "$file_path")
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"

# Detect phase transition by parsing current-phase from YAML frontmatter
CURRENT_PHASE=$(sed -n '/^---$/,/^---$/{ s/^current-phase: *//p; }' "$file_path" 2>/dev/null | head -1)

# Check gates for synthesize or complete transitions
case "$CURRENT_PHASE" in
  synthesize|complete)
    TARGET="$CURRENT_PHASE"
    if ! bash "${CLAUDE_PLUGIN_ROOT}/scripts/check-sdlc-gates.sh" "$TASK_DIR" "$TARGET" --project-dir "$PROJECT_DIR" 2>/dev/null; then
      echo "HOOK_WARNING: current-phase set to '$TARGET' but gate check failed. Run: bash scripts/run-${TARGET}-gates.sh $TASK_DIR $PROJECT_DIR" >&2
    fi
    ;;
esac

exit 0
```

### 5. Backfill Script (`scripts/backfill-telemetry.sh`)

```bash
#!/bin/bash
# Usage: backfill-telemetry.sh <sdlc-active-dir> <project-dir>
# Retroactively derives telemetry for tasks that have bead data.
# IDEMPOTENT: checks each artifact and ledger entry independently.
# Safe to re-run after partial failures.
set -euo pipefail

ACTIVE_DIR="$1"
PROJECT_DIR="$2"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKFILLED=0

# Helper: check if task_id already in a JSONL ledger (duplicate guard)
task_in_ledger() {
  local ledger="$1" task_id="$2"
  [ -f "$ledger" ] && grep -qF "\"$task_id\"" "$ledger" 2>/dev/null
}

for task_dir in "$ACTIVE_DIR"/*/; do
  TASK_ID=$(basename "$task_dir")

  # Skip tasks without beads
  [ -d "$task_dir/beads" ] && ls "$task_dir/beads/"*.md &>/dev/null || continue

  echo "=== Backfilling: $TASK_ID ==="

  # --- Per-artifact checks (each independent, not short-circuit) ---

  # Quality budget
  if [ ! -f "$task_dir/quality-budget.yaml" ]; then
    bash "$SCRIPT_DIR/derive-quality-budget.sh" "$task_dir" --status final 2>/dev/null \
      && echo "  quality-budget.yaml created" \
      || echo "  WARN: quality-budget derivation failed" >&2
  else
    echo "  quality-budget.yaml already exists (skip derivation)"
  fi

  # Mode-convergence
  if [ ! -f "$task_dir/mode-convergence-summary.yaml" ]; then
    bash "$SCRIPT_DIR/derive-mode-convergence-summary.sh" "$task_dir" --status final 2>/dev/null \
      && echo "  mode-convergence-summary.yaml created" \
      || echo "  WARN: mode-convergence derivation failed" >&2
  else
    echo "  mode-convergence-summary.yaml already exists (skip derivation)"
  fi

  # --- Per-ledger checks (duplicate guard before append) ---

  BUDGET_LEDGER="$PROJECT_DIR/docs/sdlc/system-budget.jsonl"
  if ! task_in_ledger "$BUDGET_LEDGER" "$TASK_ID"; then
    bash "$SCRIPT_DIR/append-system-budget.sh" "$task_dir" "$PROJECT_DIR" 2>/dev/null \
      && echo "  system-budget.jsonl appended" \
      || echo "  WARN: system-budget append failed" >&2
  else
    echo "  system-budget.jsonl already has $TASK_ID (skip append)"
  fi

  MC_LEDGER="$PROJECT_DIR/docs/sdlc/system-mode-convergence.jsonl"
  if ! task_in_ledger "$MC_LEDGER" "$TASK_ID"; then
    bash "$SCRIPT_DIR/append-system-mode-convergence.sh" "$task_dir" "$PROJECT_DIR" 2>/dev/null \
      && echo "  system-mode-convergence.jsonl appended" \
      || echo "  WARN: system-mode-convergence append failed" >&2
  else
    echo "  system-mode-convergence.jsonl already has $TASK_ID (skip append)"
  fi

  BACKFILLED=$((BACKFILLED + 1))
done

echo "=== Backfilled $BACKFILLED tasks ==="
```

### 6. Conductor Checklist Update

Add to `skills/sdlc-orchestrate/SKILL.md`:

```markdown
## REQUIRED: Gate Automation

Before Synthesize: `bash scripts/run-synthesize-gates.sh <task-dir> <project-dir>`
Before Complete: `bash scripts/run-complete-gates.sh <task-dir> <project-dir>`

These scripts automatically:
- Detect which telemetry lanes apply (STPA, AQS, stress) using deterministic rules
- Run all applicable derivation scripts in the correct order
- Append to all applicable system JSONL ledgers
- Validate both task-local artifacts AND system ledger entries
- Report pass/fail with details

Do NOT manually update state.md phase log without running the appropriate gate script first.
```

---

## Implementation Surface

### Files to Create

| File | Purpose |
|------|---------|
| `scripts/check-sdlc-gates.sh` | Deterministic gate validator: task-local artifacts + system ledger entries |
| `scripts/run-synthesize-gates.sh` | Automation: detect lanes → derive → validate |
| `scripts/run-complete-gates.sh` | Automation: finalize → append ledgers → validate (includes stress finalization) |
| `scripts/backfill-telemetry.sh` | Retroactively derive for tasks with bead data |
| `hooks/scripts/warn-phase-transition.sh` | Advisory hook: re-run gate check on state.md writes |

### Files to Modify

| File | Change |
|------|--------|
| `scripts/lib/sdlc-common.sh` | Add `classify_task_lanes()` shared function |
| `scripts/append-system-budget.sh` | Add duplicate-task-id guard (`grep -qF` before append) |
| `scripts/append-system-hazard-defense.sh` | Add duplicate-task-id guard |
| `scripts/append-system-stress.sh` | Add duplicate-task-id guard |
| `scripts/append-system-mode-convergence.sh` | Add duplicate-task-id guard |
| `skills/sdlc-orchestrate/SKILL.md` | Add prominent REQUIRED gate automation callout |
| `skills/sdlc-gate/SKILL.md` | Reference check-sdlc-gates.sh as enforcement mechanism |
| `hooks/hooks.json` | Add warn-phase-transition.sh PostToolUse hook |
| `hooks/tests/test-hooks.sh` | Add tests for the new hook |
| `README.md` | Update with gate automation instructions |

---

## Scope

### In scope
- Gate checker with system ledger verification
- Synthesize/Complete automation with deterministic classification (artifact-first, bead-metadata fallback)
- Stress session finalization (write artifact_status: final) in Complete automation
- Decision-noise finalization in Complete automation
- Backfill for existing tasks with bead data
- Advisory phase-transition hook (re-check against filesystem, no stamp file)
- Orchestrate SKILL.md update
- Testing and verification

### Implementation plan must address (from review findings 4 and 5)
- **Hook detection:** Parse `current-phase:` from state.md YAML frontmatter for transition detection, not grep for same-day date strings. Must detect both synthesize and complete transitions.
- **Backfill idempotency:** Add duplicate-task-id guard to all system ledger append scripts (`grep -qF` before appending, same pattern as `pass_exists` in decision-noise-lib). Make backfill resumable: check each artifact + each ledger entry independently, not short-circuit on first artifact.

### Out of scope
- Blocking (non-advisory) hook enforcement (v2)
- Automatic turbulence population during bead execution (requires runner changes)
- Dashboard/visualization of system ledger data
- Automatic bead file creation for tasks that skip bead tracking
