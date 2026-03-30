#!/bin/bash
# compute-convergence-signal.sh — Compute convergence signal from AQS/loop cycle data
# Usage: compute-convergence-signal.sh <new_findings> <repeated_findings> \
#          <prev_severities_json> <curr_severities_json> <curr_categories_json> \
#          <original_budget> <current_cycle>
# Output: JSON convergence signal {cycle, new_findings, repeated_findings, evidence_rate,
#                                   severity_trend, entropy_estimate, convergence_state, recommendation}
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# PyYAML guard
if ! python3 -c "import yaml" 2>/dev/null; then
  echo "ERROR: PyYAML is required. Install with: pip install pyyaml" >&2
  exit 1
fi

NEW_FINDINGS="${1:?Usage: compute-convergence-signal.sh <new_findings> <repeated_findings> <prev_severities_json> <curr_severities_json> <curr_categories_json> <original_budget> <current_cycle>}"
REPEATED_FINDINGS="${2:?missing repeated_findings}"
PREV_SEVERITIES_JSON="${3:?missing prev_severities_json}"
CURR_SEVERITIES_JSON="${4:?missing curr_severities_json}"
CURR_CATEGORIES_JSON="${5:?missing curr_categories_json}"
ORIGINAL_BUDGET="${6:?missing original_budget}"
CURRENT_CYCLE="${7:?missing current_cycle}"

RULES_FILE="$SCRIPT_DIR/../references/mode-convergence-rules.yaml"
[ -f "$RULES_FILE" ] || { echo "ERROR: mode-convergence-rules.yaml not found: $RULES_FILE" >&2; exit 1; }

# Source lib (after PyYAML guard; lib itself also guards but guard here before sourcing)
source "$SCRIPT_DIR/lib/mode-convergence-lib.sh"

# Compute severity_trend — reads ordinal thresholds from rules file (no hardcoded values)
SEVERITY_TREND=$(compute_severity_trend "$PREV_SEVERITIES_JSON" "$CURR_SEVERITIES_JSON" "$RULES_FILE")

# Compute Shannon entropy over current finding categories
ENTROPY=$(compute_entropy "$CURR_CATEGORIES_JSON")

# Compute full convergence signal — reads thresholds/recommendations from rules file
compute_convergence_signal \
  "$NEW_FINDINGS" \
  "$REPEATED_FINDINGS" \
  "$SEVERITY_TREND" \
  "$ENTROPY" \
  "$ORIGINAL_BUDGET" \
  "$CURRENT_CYCLE" \
  "$RULES_FILE"
