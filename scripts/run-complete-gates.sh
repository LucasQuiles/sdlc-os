#!/bin/bash
# run-complete-gates.sh — Finalize all applicable artifacts, append system ledgers, validate complete gates
# Usage: run-complete-gates.sh <task-dir> <project-dir>
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/sdlc-common.sh"

TASK_DIR="${1:?Usage: run-complete-gates.sh <task-dir> <project-dir>}"
PROJECT_DIR="${2:?Usage: run-complete-gates.sh <task-dir> <project-dir>}"

[ -d "$TASK_DIR" ] || { echo "ERROR: Task directory not found: $TASK_DIR" >&2; exit 1; }

TASK_ID="$(basename "$TASK_DIR")"

# ---------------------------------------------------------------------------
# Lane classification
# ---------------------------------------------------------------------------
classify_task_lanes "$TASK_DIR" "$TASK_ID" "$PROJECT_DIR"
echo "--- run-complete-gates: $TASK_ID ---" >&2
echo "  HAS_BEADS=$HAS_BEADS  IS_STPA=$IS_STPA  IS_AQS=$IS_AQS  IS_STRESSED=$IS_STRESSED" >&2

# ---------------------------------------------------------------------------
# 1. Finalize quality budget (if HAS_BEADS)
# ---------------------------------------------------------------------------
if [ "$HAS_BEADS" = true ]; then
  echo "[complete] Finalizing quality budget (--status final)..." >&2
  "$SCRIPT_DIR/derive-quality-budget.sh" "$TASK_DIR" --status final
fi

# ---------------------------------------------------------------------------
# 2. Finalize hazard-defense summary (if IS_STPA + HDL exists)
# ---------------------------------------------------------------------------
if [ "$IS_STPA" = true ] && [ -f "$TASK_DIR/hazard-defense-ledger.yaml" ]; then
  echo "[complete] Finalizing hazard-defense summary (--status final)..." >&2
  "$SCRIPT_DIR/derive-hazard-defense-summary.sh" "$TASK_DIR" --status final
fi

# ---------------------------------------------------------------------------
# 3. Finalize decision-noise summary (if IS_AQS, advisory — || warn)
# ---------------------------------------------------------------------------
if [ "$IS_AQS" = true ]; then
  echo "[complete] Finalizing decision-noise summary (--status final)..." >&2
  "$SCRIPT_DIR/derive-decision-noise-summary.sh" "$TASK_ID" "$PROJECT_DIR" --status final \
    || echo "WARN: derive-decision-noise-summary.sh failed (advisory, continuing)" >&2
fi

# ---------------------------------------------------------------------------
# 4. Finalize stress session (if IS_STRESSED)
#    Write artifact_status: final via python3, then update stressor library
# ---------------------------------------------------------------------------
if [ "$IS_STRESSED" = true ]; then
  echo "[complete] Finalizing stress session (artifact_status: final)..." >&2
  python3 - "$TASK_DIR/stress-session.yaml" <<'PY'
import sys, yaml

session_path = sys.argv[1]
with open(session_path) as f:
    data = yaml.safe_load(f)

data['artifact_status'] = 'final'

with open(session_path, 'w') as f:
    yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

print(f"Set artifact_status=final in {session_path}")
PY

  echo "[complete] Updating stressor library..." >&2
  "$SCRIPT_DIR/update-stressor-library.sh" \
    "$TASK_DIR" \
    "$SCRIPT_DIR/../references/stressor-library.yaml" \
    "$PROJECT_DIR"
fi

# ---------------------------------------------------------------------------
# 5. Finalize mode-convergence summary (if HAS_BEADS)
# ---------------------------------------------------------------------------
if [ "$HAS_BEADS" = true ]; then
  echo "[complete] Finalizing mode-convergence summary (--status final)..." >&2
  "$SCRIPT_DIR/derive-mode-convergence-summary.sh" "$TASK_DIR" --status final
fi

# ---------------------------------------------------------------------------
# 6. Validate task-local artifacts BEFORE appending to system ledgers
# ---------------------------------------------------------------------------
# If task-local artifacts are incomplete, abort before appending to prevent
# permanent stale entries that idempotent appenders refuse to refresh.
echo "[complete] Pre-append validation (task-local only)..." >&2

PRE_APPEND_FAIL=0

if [ "$HAS_BEADS" = true ]; then
  # quality-budget.yaml must exist with artifact_status: final and budget_state non-null
  if [ ! -f "$TASK_DIR/quality-budget.yaml" ]; then
    echo "FAIL: quality-budget.yaml not found — aborting ledger append" >&2
    PRE_APPEND_FAIL=1
  else
    _qb_status=$(python3 -c "import yaml; d=yaml.safe_load(open('$TASK_DIR/quality-budget.yaml')); print(d.get('artifact_status',''))" 2>/dev/null || echo "")
    _qb_budget=$(python3 -c "import yaml; d=yaml.safe_load(open('$TASK_DIR/quality-budget.yaml')); print(d.get('budget_state',''))" 2>/dev/null || echo "")
    if [ "$_qb_status" != "final" ]; then
      echo "FAIL: quality-budget.yaml artifact_status='$_qb_status' (need 'final') — aborting" >&2
      PRE_APPEND_FAIL=1
    fi
    if [ -z "$_qb_budget" ] || [ "$_qb_budget" = "null" ]; then
      echo "FAIL: quality-budget.yaml budget_state is null — aborting" >&2
      PRE_APPEND_FAIL=1
    fi
  fi
fi

if [ "$IS_STPA" = true ] && [ -f "$TASK_DIR/hazard-defense-ledger.yaml" ]; then
  _hdl_status=$(python3 -c "import yaml; d=yaml.safe_load(open('$TASK_DIR/hazard-defense-ledger.yaml')); print(d.get('artifact_status',''))" 2>/dev/null || echo "")
  if [ "$_hdl_status" != "final" ]; then
    echo "FAIL: hazard-defense-ledger.yaml artifact_status='$_hdl_status' (need 'final') — aborting" >&2
    PRE_APPEND_FAIL=1
  fi
fi

if [ "$IS_STRESSED" = true ] && [ -f "$TASK_DIR/stress-session.yaml" ]; then
  _ss_status=$(python3 -c "import yaml; d=yaml.safe_load(open('$TASK_DIR/stress-session.yaml')); print(d.get('artifact_status',''))" 2>/dev/null || echo "")
  if [ "$_ss_status" != "final" ]; then
    echo "FAIL: stress-session.yaml artifact_status='$_ss_status' (need 'final') — aborting" >&2
    PRE_APPEND_FAIL=1
  fi
fi

if [ "$PRE_APPEND_FAIL" -ne 0 ]; then
  echo "ERROR: Pre-append validation failed. System ledgers NOT modified." >&2
  exit 1
fi

echo "[complete] Pre-append validation passed." >&2

# ---------------------------------------------------------------------------
# 7. Append to all applicable system ledgers
# ---------------------------------------------------------------------------
if [ "$HAS_BEADS" = true ]; then
  echo "[complete] Appending to system-budget.jsonl..." >&2
  "$SCRIPT_DIR/append-system-budget.sh" "$TASK_DIR" "$PROJECT_DIR"

  echo "[complete] Appending to system-mode-convergence.jsonl..." >&2
  "$SCRIPT_DIR/append-system-mode-convergence.sh" "$TASK_DIR" "$PROJECT_DIR"
fi

if [ "$IS_STPA" = true ]; then
  echo "[complete] Appending to system-hazard-defense.jsonl..." >&2
  "$SCRIPT_DIR/append-system-hazard-defense.sh" "$TASK_DIR" "$PROJECT_DIR"
fi

if [ "$IS_STRESSED" = true ]; then
  echo "[complete] Appending to system-stress.jsonl..." >&2
  "$SCRIPT_DIR/append-system-stress.sh" "$TASK_DIR" "$PROJECT_DIR"
fi

# ---------------------------------------------------------------------------
# 8. Validate ALL complete gates (task-local + system ledger)
# ---------------------------------------------------------------------------
echo "[complete] Final gate check (task-local + system ledger)..." >&2
"$SCRIPT_DIR/check-sdlc-gates.sh" "$TASK_DIR" complete --project-dir "$PROJECT_DIR"
