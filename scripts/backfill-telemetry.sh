#!/bin/bash
# backfill-telemetry.sh — Idempotent telemetry backfill for tasks with bead data
# Usage: backfill-telemetry.sh <sdlc-active-dir> <project-dir>
#
# For each task with beads/*.md files:
#   - Derives quality-budget.yaml (--status final) if not already present
#   - Derives mode-convergence-summary.yaml (--status final) if not already present
#   - Appends to system-budget.jsonl if task_id not already in ledger
#   - Appends to system-mode-convergence.jsonl if task_id not already in ledger
#
# Each artifact and each ledger entry are checked independently (no short-circuit).
# Safe to rerun after partial failures.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/sdlc-common.sh"

ACTIVE_DIR="${1:?Usage: backfill-telemetry.sh <sdlc-active-dir> <project-dir>}"
PROJECT_DIR="${2:?Usage: backfill-telemetry.sh <sdlc-active-dir> <project-dir>}"

[ -d "$ACTIVE_DIR" ] || { echo "ERROR: Active directory not found: $ACTIVE_DIR" >&2; exit 1; }
[ -d "$PROJECT_DIR" ] || { echo "ERROR: Project directory not found: $PROJECT_DIR" >&2; exit 1; }

# PyYAML guard (required for mode-convergence derivation)
if ! python3 -c "import yaml" 2>/dev/null; then
  echo "ERROR: python3 with PyYAML is required. Install: pip3 install pyyaml" >&2
  exit 1
fi

# ---------------------------------------------------------------------------
# task_in_ledger <ledger> <task_id>
# Returns 0 if task_id is already present in the ledger, 1 otherwise
# ---------------------------------------------------------------------------
task_in_ledger() {
  local ledger="$1" task_id="$2"
  [ -f "$ledger" ] && grep -qF "\"$task_id\"" "$ledger" 2>/dev/null
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
BUDGET_LEDGER="$PROJECT_DIR/docs/sdlc/system-budget.jsonl"
CONVERGENCE_LEDGER="$PROJECT_DIR/docs/sdlc/system-mode-convergence.jsonl"

TASKS_FOUND=0
TASKS_WITH_BEADS=0
TASKS_SKIPPED=0
TASKS_PROCESSED=0
TOTAL_ERRORS=0

echo "=== backfill-telemetry: scanning $ACTIVE_DIR ===" >&2

for task_dir in "$ACTIVE_DIR"/*/; do
  [ -d "$task_dir" ] || continue
  task_id="$(basename "$task_dir")"
  TASKS_FOUND=$((TASKS_FOUND + 1))

  # Only process tasks with bead files
  if ! ls "$task_dir/beads/"*.md &>/dev/null 2>&1; then
    echo "  [$task_id] SKIP: no beads/*.md files" >&2
    TASKS_SKIPPED=$((TASKS_SKIPPED + 1))
    continue
  fi

  TASKS_WITH_BEADS=$((TASKS_WITH_BEADS + 1))
  echo "" >&2
  echo "--- [$task_id] ---" >&2

  task_errors=0
  budget_derived=false
  budget_skipped=false
  convergence_derived=false
  convergence_skipped=false
  budget_appended=false
  budget_ledger_skip=false
  convergence_appended=false
  convergence_ledger_skip=false

  # -------------------------------------------------------------------------
  # Artifact 1: quality-budget.yaml
  # -------------------------------------------------------------------------
  if [ -f "$task_dir/quality-budget.yaml" ]; then
    echo "  [quality-budget.yaml] already exists — skipping derivation" >&2
    budget_skipped=true
  else
    echo "  [quality-budget.yaml] deriving (--status final)..." >&2
    if "$SCRIPT_DIR/derive-quality-budget.sh" "$task_dir" --status final 2>&1 | sed 's/^/    /'; then
      budget_derived=true
      echo "  [quality-budget.yaml] derived OK" >&2
    else
      echo "  [quality-budget.yaml] ERROR: derivation failed" >&2
      task_errors=$((task_errors + 1))
    fi
  fi

  # -------------------------------------------------------------------------
  # Artifact 2: mode-convergence-summary.yaml
  # Depends on quality-budget.yaml being present (already existing or just derived)
  # -------------------------------------------------------------------------
  if [ -f "$task_dir/mode-convergence-summary.yaml" ]; then
    echo "  [mode-convergence-summary.yaml] already exists — skipping derivation" >&2
    convergence_skipped=true
  elif [ ! -f "$task_dir/quality-budget.yaml" ]; then
    echo "  [mode-convergence-summary.yaml] SKIP: quality-budget.yaml missing (derivation prerequisite)" >&2
    task_errors=$((task_errors + 1))
  else
    echo "  [mode-convergence-summary.yaml] deriving (--status final)..." >&2
    if "$SCRIPT_DIR/derive-mode-convergence-summary.sh" "$task_dir" --status final 2>&1 | sed 's/^/    /'; then
      convergence_derived=true
      echo "  [mode-convergence-summary.yaml] derived OK" >&2
    else
      echo "  [mode-convergence-summary.yaml] ERROR: derivation failed" >&2
      task_errors=$((task_errors + 1))
    fi
  fi

  # -------------------------------------------------------------------------
  # Ledger 1: system-budget.jsonl (independent of ledger 2)
  # -------------------------------------------------------------------------
  if task_in_ledger "$BUDGET_LEDGER" "$task_id"; then
    echo "  [system-budget.jsonl] already has $task_id — skipping append" >&2
    budget_ledger_skip=true
  elif [ ! -f "$task_dir/quality-budget.yaml" ]; then
    echo "  [system-budget.jsonl] SKIP: quality-budget.yaml missing (cannot append)" >&2
    task_errors=$((task_errors + 1))
  else
    echo "  [system-budget.jsonl] appending $task_id..." >&2
    if "$SCRIPT_DIR/append-system-budget.sh" "$task_dir" "$PROJECT_DIR" 2>&1 | sed 's/^/    /'; then
      budget_appended=true
      echo "  [system-budget.jsonl] appended OK" >&2
    else
      echo "  [system-budget.jsonl] ERROR: append failed" >&2
      task_errors=$((task_errors + 1))
    fi
  fi

  # -------------------------------------------------------------------------
  # Ledger 2: system-mode-convergence.jsonl (independent of ledger 1)
  # -------------------------------------------------------------------------
  if task_in_ledger "$CONVERGENCE_LEDGER" "$task_id"; then
    echo "  [system-mode-convergence.jsonl] already has $task_id — skipping append" >&2
    convergence_ledger_skip=true
  elif [ ! -f "$task_dir/mode-convergence-summary.yaml" ]; then
    echo "  [system-mode-convergence.jsonl] SKIP: mode-convergence-summary.yaml missing (cannot append)" >&2
    task_errors=$((task_errors + 1))
  else
    echo "  [system-mode-convergence.jsonl] appending $task_id..." >&2
    if "$SCRIPT_DIR/append-system-mode-convergence.sh" "$task_dir" "$PROJECT_DIR" 2>&1 | sed 's/^/    /'; then
      convergence_appended=true
      echo "  [system-mode-convergence.jsonl] appended OK" >&2
    else
      echo "  [system-mode-convergence.jsonl] ERROR: append failed" >&2
      task_errors=$((task_errors + 1))
    fi
  fi

  # -------------------------------------------------------------------------
  # Per-task summary
  # -------------------------------------------------------------------------
  if [ "$task_errors" -gt 0 ]; then
    echo "  RESULT: $task_id — $task_errors error(s)" >&2
    TOTAL_ERRORS=$((TOTAL_ERRORS + task_errors))
  else
    echo "  RESULT: $task_id — OK" >&2
    TASKS_PROCESSED=$((TASKS_PROCESSED + 1))
  fi
done

# ---------------------------------------------------------------------------
# Final summary
# ---------------------------------------------------------------------------
echo "" >&2
echo "=== backfill-telemetry: done ===" >&2
echo "  Tasks found:       $TASKS_FOUND" >&2
echo "  Tasks with beads:  $TASKS_WITH_BEADS" >&2
echo "  Tasks skipped:     $TASKS_SKIPPED (no beads)" >&2
echo "  Tasks OK:          $TASKS_PROCESSED" >&2
echo "  Total errors:      $TOTAL_ERRORS" >&2

if [ "$TOTAL_ERRORS" -gt 0 ]; then
  echo "" >&2
  echo "WARNING: $TOTAL_ERRORS error(s) encountered. Rerun after fixing to complete backfill." >&2
  exit 1
fi
exit 0
