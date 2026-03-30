#!/bin/bash
# classify-execution-mode.sh — Classify task execution mode (Rasmussen SRK) from quality-budget.yaml
# Usage: classify-execution-mode.sh <task-dir>
# Output: JSON {classification, confidence, signals}
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# PyYAML guard
if ! python3 -c "import yaml" 2>/dev/null; then
  echo "ERROR: PyYAML is required. Install with: pip install pyyaml" >&2
  exit 1
fi

TASK_DIR="${1:?Usage: classify-execution-mode.sh <task-dir>}"
[ -d "$TASK_DIR" ] || { echo "ERROR: Task directory not found: $TASK_DIR" >&2; exit 1; }

QB="$TASK_DIR/quality-budget.yaml"
[ -f "$QB" ] || { echo "ERROR: quality-budget.yaml not found in $TASK_DIR" >&2; exit 1; }

RULES_FILE="$SCRIPT_DIR/../references/mode-convergence-rules.yaml"
[ -f "$RULES_FILE" ] || { echo "ERROR: mode-convergence-rules.yaml not found: $RULES_FILE" >&2; exit 1; }

# Source lib (after PyYAML guard)
source "$SCRIPT_DIR/lib/mode-convergence-lib.sh"

# Extract the 4 SRK signals from quality-budget.yaml via Python
read -r TPB ZTR LAT ESC < <(python3 -c "
import yaml, sys
with open(sys.argv[1]) as f:
    qb = yaml.safe_load(f)
metrics = qb.get('metrics', {})
corrections = qb.get('corrections', {})

tpb = float(metrics.get('turbulence_sum_per_bead', 0))
ztr = float(metrics.get('zero_turbulence_rate', 0))
lat = float(metrics.get('review_latency_p95_s', 0))

# escalation_count = sum of L2+ corrections (L2, L2_5, L2_75)
esc = int(corrections.get('L2', 0)) + int(corrections.get('L2_5', 0)) + int(corrections.get('L2_75', 0))

print(tpb, ztr, lat, esc)
" "$QB")

# Classify using shared lib (reads thresholds from rules file — no hardcoded values)
RESULT=$(classify_execution_mode "$TPB" "$ZTR" "$LAT" "$ESC" "$RULES_FILE")

# Enrich with the raw signal values for observability
python3 -c "
import json, sys
result = json.loads(sys.argv[1])
result['signals'] = {
    'turbulence_sum_per_bead': float(sys.argv[2]),
    'zero_turbulence_rate': float(sys.argv[3]),
    'review_latency_p95_s': float(sys.argv[4]),
    'escalation_count': int(sys.argv[5]),
}
print(json.dumps(result))
" "$RESULT" "$TPB" "$ZTR" "$LAT" "$ESC"
