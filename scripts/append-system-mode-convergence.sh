#!/bin/bash
# append-system-mode-convergence.sh — Append completed task to system-mode-convergence.jsonl
# Usage: append-system-mode-convergence.sh <task-dir> <project-dir>
#
# Reads:  <task-dir>/mode-convergence-summary.yaml  (must have artifact_status: final)
# Writes: <project-dir>/docs/sdlc/system-mode-convergence.jsonl
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/mode-convergence-lib.sh"

# PyYAML guard
if ! python3 -c "import yaml" 2>/dev/null; then
  echo "ERROR: python3 with PyYAML is required. Install: pip3 install pyyaml" >&2
  exit 1
fi

TASK_DIR="${1:?Usage: append-system-mode-convergence.sh <task-dir> <project-dir>}"
PROJECT_DIR="${2:?Usage: append-system-mode-convergence.sh <task-dir> <project-dir>}"
SUMMARY="$TASK_DIR/mode-convergence-summary.yaml"
LEDGER="$PROJECT_DIR/docs/sdlc/system-mode-convergence.jsonl"

[ -f "$SUMMARY" ] || { echo "ERROR: mode-convergence-summary.yaml not found: $SUMMARY" >&2; exit 1; }

_MC_TASK_ID=$(python3 -c "import yaml; print(yaml.safe_load(open('$SUMMARY'))['task_id'])")
if [ -f "$LEDGER" ] && grep -qF "\"$_MC_TASK_ID\"" "$LEDGER" 2>/dev/null; then
  echo "SKIP: $_MC_TASK_ID already in $(basename "$LEDGER") (idempotent)" >&2
  exit 0
fi

mkdir -p "$(dirname "$LEDGER")"

python3 -c "
import yaml, sys, json, os, glob
from collections import Counter

with open(sys.argv[1]) as f:
    data = yaml.safe_load(f)

# Validate artifact_status
status = data.get('artifact_status')
if status != 'final':
    print(f'ERROR: artifact_status is \"{status}\", must be \"final\" to append to system ledger', file=sys.stderr)
    sys.exit(1)

task_id   = data['task_id']
derived_at = data.get('derived_at', '')
# Date portion only (YYYY-MM-DD)
date = derived_at[:10] if derived_at else ''

exec_mode = data.get('execution_mode', {})
classification = exec_mode.get('classification', '')
confidence     = exec_mode.get('confidence', '')

summary = data.get('summary', {})
total_escalations  = int(summary.get('total_escalations', 0))
reason_distribution = summary.get('reason_distribution') or {}
dominant_reason    = summary.get('dominant_reason')
early_stops        = int(summary.get('early_stops', 0))
budget_extensions  = int(summary.get('budget_extensions', 0))
approach_changes   = int(summary.get('approach_changes', 0))

# convergence_yield = early_stops / total_loop_iterations
# Count ALL cycles from convergence_history (not just terminal recommendations)
convergence_history = data.get('convergence_history', [])
total_loop_iterations = 0
for bead_entry in convergence_history:
    total_loop_iterations += len(bead_entry.get('cycles', []))
# Fallback: if no convergence_history, use terminal outcomes as lower bound
if total_loop_iterations == 0:
    total_loop_iterations = early_stops + budget_extensions + approach_changes
convergence_yield = round(early_stops / total_loop_iterations, 3) if total_loop_iterations > 0 else 0.0

# bead count from quality-budget beads.total (NOT wip_beads which is a different concept)
# Bead count resolution: prefer explicit _beads_total, then count bead files, then wip_beads
_beads_total = data.get('_beads_total')
if _beads_total is not None:
    beads = int(_beads_total)
else:
    # Count bead files in task directory as fallback
    task_dir = os.path.dirname(sys.argv[1])
    bead_files = glob.glob(os.path.join(task_dir, 'beads', '*.md'))
    if bead_files:
        beads = len(bead_files)
    else:
        beads = int(exec_mode.get('signals', {}).get('wip_beads', 0))

entry = {
    'task_id':            task_id,
    'date':               date,
    'execution_mode':     classification,
    'mode_confidence':    confidence,
    'total_escalations':  total_escalations,
    'reason_distribution': reason_distribution,
    'dominant_reason':    dominant_reason,
    'early_stops':        early_stops,
    'convergence_yield':  convergence_yield,
    'beads':              beads,
}

print(json.dumps(entry, separators=(',', ':')))
" "$SUMMARY" >> "$LEDGER"

TASK_ID=$(basename "$TASK_DIR")
echo "Appended $TASK_ID to system-mode-convergence.jsonl"
