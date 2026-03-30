#!/bin/bash
# append-system-budget.sh — Append completed task to system-budget.jsonl
# Usage: append-system-budget.sh <task-dir> <project-dir>
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/quality-budget-lib.sh"

TASK_DIR="${1:?Usage: append-system-budget.sh <task-dir> <project-dir>}"
PROJECT_DIR="${2:?Usage: append-system-budget.sh <task-dir> <project-dir>}"
BUDGET_FILE="$TASK_DIR/quality-budget.yaml"
LEDGER="$PROJECT_DIR/docs/sdlc/system-budget.jsonl"

[ -f "$BUDGET_FILE" ] || { echo "ERROR: quality-budget.yaml not found" >&2; exit 1; }

# Simple YAML field extractor (works for flat fields)
yf() { grep "^${1}:" "$BUDGET_FILE" | sed "s/^${1}: *//" | sed 's/"//g'; }
yf_nested() { grep "^  ${1}:" "$BUDGET_FILE" | sed "s/^  ${1}: *//" | sed 's/"//g'; }

TASK_ID=$(yf "task_id")
STATUS=$(yf "artifact_status")

if [ "$STATUS" != "final" ]; then
  echo "ERROR: artifact_status is '$STATUS', must be 'final' to append to system ledger" >&2
  exit 1
fi

# Build JSONL entry
ENTRY=$(cat <<JSON
{"task_id":"$TASK_ID","date":"$(yf "derived_at")","beads":$(yf_nested "total"),"cynefin_mix":{"clear":$(yf_nested "clear"),"complicated":$(yf_nested "complicated"),"complex":$(yf_nested "complex"),"chaotic":$(yf_nested "chaotic")},"complexity_weight":$(yf "complexity_weight"),"turbulence_sum":$(yf "turbulence_sum"),"zero_turbulence_rate":$(yf_nested "zero_turbulence_rate"),"review_pass_rate":$(yf_nested "review_pass_rate"),"L0":$(yf_nested "L0"),"L1":$(yf_nested "L1"),"L2":$(yf_nested "L2"),"L2_5":$(yf_nested "L2_5"),"L2_75":$(yf_nested "L2_75"),"escapes_at_close":$(yf_nested "known_at_close"),"estimate_s":$(yf_nested "estimate_s"),"actual_s":$(yf_nested "actual_s"),"latency_avg_s":$(yf_nested "review_latency_avg_s"),"latency_p95_s":$(yf_nested "review_latency_p95_s"),"queue_peak":$(yf_nested "queue_depth_peak"),"buffer_hits":$(yf_nested "buffer_hits"),"budget_state":"$(yf "budget_state")"}
JSON
)

mkdir -p "$(dirname "$LEDGER")"
echo "$ENTRY" >> "$LEDGER"
echo "Appended $TASK_ID to system-budget.jsonl"
