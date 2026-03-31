#!/bin/bash
# run-synthesize-gates.sh — Derive all applicable artifacts then validate synthesize gates
# Usage: run-synthesize-gates.sh <task-dir> <project-dir>
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/sdlc-common.sh"

TASK_DIR="${1:?Usage: run-synthesize-gates.sh <task-dir> <project-dir>}"
PROJECT_DIR="${2:?Usage: run-synthesize-gates.sh <task-dir> <project-dir>}"

[ -d "$TASK_DIR" ] || { echo "ERROR: Task directory not found: $TASK_DIR" >&2; exit 1; }

TASK_ID="$(basename "$TASK_DIR")"

# ---------------------------------------------------------------------------
# Lane classification
# ---------------------------------------------------------------------------
classify_task_lanes "$TASK_DIR" "$TASK_ID" "$PROJECT_DIR"
echo "--- run-synthesize-gates: $TASK_ID ---" >&2
echo "  HAS_BEADS=$HAS_BEADS  IS_STPA=$IS_STPA  IS_AQS=$IS_AQS  IS_STRESSED=$IS_STRESSED" >&2

# ---------------------------------------------------------------------------
# 1. Derive quality budget (if HAS_BEADS)
# ---------------------------------------------------------------------------
if [ "$HAS_BEADS" = true ]; then
  echo "[synthesize] Deriving quality budget (--status ready)..." >&2
  "$SCRIPT_DIR/derive-quality-budget.sh" "$TASK_DIR" --status ready
fi

# ---------------------------------------------------------------------------
# 2. Derive hazard-defense summary (if IS_STPA + HDL exists)
# ---------------------------------------------------------------------------
if [ "$IS_STPA" = true ] && [ -f "$TASK_DIR/hazard-defense-ledger.yaml" ]; then
  echo "[synthesize] Deriving hazard-defense summary (--status active)..." >&2
  "$SCRIPT_DIR/derive-hazard-defense-summary.sh" "$TASK_DIR" --status active
fi

# ---------------------------------------------------------------------------
# 3. Derive decision-noise summary (if IS_AQS, advisory — || warn)
# ---------------------------------------------------------------------------
if [ "$IS_AQS" = true ]; then
  echo "[synthesize] Deriving decision-noise summary (--status partial)..." >&2
  "$SCRIPT_DIR/derive-decision-noise-summary.sh" "$TASK_ID" "$PROJECT_DIR" --status partial \
    || echo "WARN: derive-decision-noise-summary.sh failed (advisory, continuing)" >&2
fi

# ---------------------------------------------------------------------------
# 4. Derive mode-convergence summary (if HAS_BEADS)
# ---------------------------------------------------------------------------
if [ "$HAS_BEADS" = true ]; then
  echo "[synthesize] Deriving mode-convergence summary (--status partial)..." >&2
  "$SCRIPT_DIR/derive-mode-convergence-summary.sh" "$TASK_DIR" --status partial
fi

# ---------------------------------------------------------------------------
# 5. Validate synthesize gates
# ---------------------------------------------------------------------------
echo "[synthesize] Checking gates..." >&2
"$SCRIPT_DIR/check-sdlc-gates.sh" "$TASK_DIR" synthesize --project-dir "$PROJECT_DIR"
