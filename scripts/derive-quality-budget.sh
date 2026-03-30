#!/bin/bash
# derive-quality-budget.sh — Derive quality-budget.yaml from bead traces
# Usage: derive-quality-budget.sh <task-dir> [--status partial|ready|final]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/quality-budget-lib.sh"

TASK_DIR="${1:?Usage: derive-quality-budget.sh <task-dir> [--status partial|ready|final]}"
STATUS="${3:-partial}"
RULES_FILE="$SCRIPT_DIR/../references/quality-budget-rules.yaml"
OUTPUT="$TASK_DIR/quality-budget.yaml"
STATE_FILE="$TASK_DIR/state.md"
BEADS_DIR="$TASK_DIR/beads"

[ -d "$TASK_DIR" ] || { echo "ERROR: Task directory not found: $TASK_DIR" >&2; exit 1; }
[ -f "$STATE_FILE" ] || { echo "ERROR: state.md not found in $TASK_DIR" >&2; exit 1; }

TASK_ID=$(basename "$TASK_DIR")

# --- Count beads by status ---
TOTAL=0 COMPLETED=0 WIP=0 STUCK=0 BLOCKED=0
CLEAR=0 COMPLICATED=0 COMPLEX=0 CHAOTIC=0
L0=0 L1=0 L2=0 L2_5=0 L2_75=0
ZERO_TURB=0
LATENCIES=""
WIP_AGES=""

for bead in "$BEADS_DIR"/*.md; do
  [ -f "$bead" ] || continue
  TOTAL=$((TOTAL + 1))

  status=$(bead_field "$bead" "Status")
  case "$status" in
    merged|hardened|reliability-proven|verified|proven) COMPLETED=$((COMPLETED + 1)) ;;
    running|submitted) WIP=$((WIP + 1)) ;;
    stuck) STUCK=$((STUCK + 1)) ;;
    blocked) BLOCKED=$((BLOCKED + 1)) ;;
  esac

  cynefin=$(bead_field "$bead" "Cynefin domain")
  case "$cynefin" in
    clear) CLEAR=$((CLEAR + 1)) ;;
    complicated) COMPLICATED=$((COMPLICATED + 1)) ;;
    complex) COMPLEX=$((COMPLEX + 1)) ;;
    chaotic) CHAOTIC=$((CHAOTIC + 1)) ;;
  esac

  turb_raw=$(bead_field "$bead" "Turbulence")
  if [ -n "$turb_raw" ]; then
    read -r tL0 tL1 tL2 tL2_5 tL2_75 <<< "$(parse_turbulence "$turb_raw")"
    L0=$((L0 + ${tL0:-0}))
    L1=$((L1 + ${tL1:-0}))
    L2=$((L2 + ${tL2:-0}))
    L2_5=$((L2_5 + ${tL2_5:-0}))
    L2_75=$((L2_75 + ${tL2_75:-0}))
    bead_turb=$(( ${tL0:-0} + ${tL1:-0} + ${tL2:-0} + ${tL2_5:-0} + ${tL2_75:-0} ))
    if [ "$bead_turb" -eq 0 ] && echo "$status" | grep -qE "merged|hardened|reliability-proven|verified|proven"; then
      ZERO_TURB=$((ZERO_TURB + 1))
    fi
  fi
done

TURB_SUM=$((L0 + L1 + L2 + L2_5 + L2_75))

# Find max turbulence bead
MAX_TURB=0 MAX_BEAD="null"
for bead in "$BEADS_DIR"/*.md; do
  [ -f "$bead" ] || continue
  turb_raw=$(bead_field "$bead" "Turbulence")
  if [ -n "$turb_raw" ]; then
    read -r tL0 tL1 tL2 tL2_5 tL2_75 <<< "$(parse_turbulence "$turb_raw")"
    bt=$(( ${tL0:-0} + ${tL1:-0} + ${tL2:-0} + ${tL2_5:-0} + ${tL2_75:-0} ))
    if [ "$bt" -gt "$MAX_TURB" ]; then
      MAX_TURB=$bt
      MAX_BEAD=$(basename "$bead" .md)
    fi
  fi
done

# --- Compute metrics ---
if [ "$COMPLETED" -gt 0 ]; then
  ZTR=$(echo "scale=2; $ZERO_TURB / $COMPLETED" | bc)
  TSPR=$(echo "scale=2; $TURB_SUM / $COMPLETED" | bc)
else
  ZTR="0.0"
  TSPR="null"
fi

CW=$(complexity_weight "$CLEAR" "$COMPLICATED" "$COMPLEX" "$CHAOTIC")

# --- Derive budget_state (only if ready or final) ---
if [ "$STATUS" != "partial" ]; then
  HF=$(lookup_threshold "$RULES_FILE" "$CW" "healthy_floor")
  DF=$(lookup_threshold "$RULES_FILE" "$CW" "depleted_floor")
  BUDGET_STATE=$(compute_budget_state "$ZTR" "0" "$TURB_SUM" "$COMPLETED" "$HF" "$DF")
else
  BUDGET_STATE="null"
fi

NOW=$(now_utc)

# --- Write YAML ---
cat > "$OUTPUT" <<YAML
schema_version: 1
task_id: "$TASK_ID"
artifact_status: $STATUS
budget_state: $BUDGET_STATE
derived_at: "$NOW"
last_updated: "$NOW"

cynefin_mix:
  clear: $CLEAR
  complicated: $COMPLICATED
  complex: $COMPLEX
  chaotic: $CHAOTIC
complexity_weight: $CW

beads:
  total: $TOTAL
  completed: $COMPLETED
  wip: $WIP
  stuck: $STUCK
  blocked: $BLOCKED
  wip_age_max_s: 0

corrections:
  L0: $L0
  L1: $L1
  L2: $L2
  L2_5: $L2_5
  L2_75: $L2_75

turbulence_sum: $TURB_SUM
turbulence_max_bead: $MAX_BEAD

metrics:
  zero_turbulence_rate: $ZTR
  turbulence_sum_per_bead: $TSPR
  review_pass_rate: 0.0
  queue_depth_peak: 0
  buffer_hits: 0
  review_latency_avg_s: 0
  review_latency_p95_s: 0

timing:
  estimate_s: null
  actual_s: null

sli_readings:
  lint_clean: null
  types_clean: null
  test_coverage_delta: null
  complexity_delta: null
  critical_findings: null

escapes:
  known_at_close: 0

overrides: []
notes: ""
YAML

echo "Derived quality-budget.yaml for $TASK_ID (status: $STATUS, budget: $BUDGET_STATE)"
