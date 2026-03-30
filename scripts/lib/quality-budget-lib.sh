#!/bin/bash
# quality-budget-lib.sh — Shared helpers for quality budget derivation
# Sourced by derive-quality-budget.sh and append-system-budget.sh

set -euo pipefail

# Parse YAML frontmatter from a bead file, extract a field value
# Usage: bead_field "beads/B01.md" "Turbulence"
bead_field() {
  local file="$1" field="$2"
  grep "^\*\*${field}:\*\*" "$file" | sed "s/\*\*${field}:\*\* *//" | sed 's/^"\(.*\)"$/\1/'
}

# Parse turbulence from bead format: {L0: N, L1: N, L2: N, L2.5: N, L2.75: N}
# Returns space-separated: L0 L1 L2 L2_5 L2_75
parse_turbulence() {
  local raw="$1"
  echo "$raw" | sed 's/[{}]//g' | sed 's/L0: *//; s/L1: *//; s/L2: *//; s/L2\.5: *//; s/L2\.75: *//' | tr ',' ' '
}

# Count beads by status from state.md bead table
# Usage: count_beads_by_status "state.md" "completed"
count_beads_by_status() {
  local state_file="$1" status="$2"
  grep -c "| *${status} *|" "$state_file" 2>/dev/null || echo 0
}

# Compute complexity_weight from cynefin_mix
# Usage: complexity_weight clear complicated complex chaotic
complexity_weight() {
  local clear="${1:-0}" complicated="${2:-0}" complex="${3:-0}" chaotic="${4:-0}"
  local total=$((clear + complicated + complex + chaotic))
  if [ "$total" -eq 0 ]; then echo "0.0"; return; fi
  # weight = (clear*0 + complicated*0.5 + complex*1.0 + chaotic*1.5) / total
  echo "scale=2; ($complicated * 0.5 + $complex * 1.0 + $chaotic * 1.5) / $total" | bc
}

# Lookup threshold from rules file given complexity_weight
# Usage: lookup_threshold "rules.yaml" "0.42" "healthy_floor"
lookup_threshold() {
  local rules_file="$1" weight="$2" field="$3"
  # Parse YAML thresholds (simple grep-based for shell compatibility)
  local prev_max="0" result=""
  while IFS= read -r line; do
    if echo "$line" | grep -q "max_weight:"; then
      local max_w
      max_w=$(echo "$line" | sed 's/.*max_weight: *//')
      if [ "$(echo "$weight <= $max_w" | bc)" -eq 1 ] && [ -z "$result" ]; then
        result=$(grep -A2 "max_weight: *${max_w}" "$rules_file" | grep "${field}:" | sed "s/.*${field}: *//")
      fi
    fi
  done < <(grep -A3 "max_weight:" "$rules_file")
  echo "${result:-0.50}"
}

# Compute budget_state from metrics + rules
# Usage: compute_budget_state zero_turb_rate escapes_at_close turb_sum completed healthy_floor depleted_floor
compute_budget_state() {
  local ztr="$1" escapes="$2" turb_sum="$3" completed="$4" healthy_floor="$5" depleted_floor="$6"

  # Depleted conditions
  if [ "$(echo "$ztr < $depleted_floor" | bc)" -eq 1 ]; then echo "depleted"; return; fi
  if [ "$escapes" -gt 1 ]; then echo "depleted"; return; fi
  if [ "$completed" -gt 0 ] && [ "$(echo "$turb_sum > 6 * $completed" | bc)" -eq 1 ]; then echo "depleted"; return; fi

  # Healthy conditions
  if [ "$(echo "$ztr >= $healthy_floor" | bc)" -eq 1 ] && [ "$escapes" -eq 0 ]; then echo "healthy"; return; fi

  # Default
  echo "warning"
}

# Check hard-stop invariants. Returns "true" if any hard-stop is triggered.
# Usage: check_hard_stops lint_clean types_clean critical_findings stuck blocked wip_age_max_s
check_hard_stops() {
  local lint="$1" types="$2" critical="$3" stuck="$4" blocked="$5" wip_age="$6"
  if [ "$lint" = "false" ]; then echo "true"; return; fi
  if [ "$types" = "false" ]; then echo "true"; return; fi
  if [ "$critical" -gt 0 ] 2>/dev/null; then echo "true"; return; fi
  if [ "$stuck" -gt 0 ] 2>/dev/null; then echo "true"; return; fi
  if [ "$blocked" -gt 0 ] 2>/dev/null && [ "$wip_age" -gt 3600 ] 2>/dev/null; then echo "true"; return; fi
  echo "false"
}

# Format current UTC timestamp as ISO 8601
now_utc() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}
