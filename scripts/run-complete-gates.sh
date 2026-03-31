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
# 6. Run FULL task-local complete gate BEFORE appending to system ledgers
# ---------------------------------------------------------------------------
# This is the complete-local phase of check-sdlc-gates.sh — it runs ALL
# task-local checks including artifact_status: final, budget_state, HDL
# open-record resolution, stress pending-result resolution, and AQS finality.
# If ANY check fails, we abort before touching system ledgers.
echo "[complete] Pre-append gate check (complete-local)..." >&2
if ! "$SCRIPT_DIR/check-sdlc-gates.sh" "$TASK_DIR" complete-local --project-dir "$PROJECT_DIR"; then
  echo "ERROR: Task-local complete gate failed. System ledgers NOT modified." >&2
  echo "Fix the failing checks above, then re-run run-complete-gates.sh." >&2
  exit 1
fi
echo "[complete] Pre-append gate check passed." >&2

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
