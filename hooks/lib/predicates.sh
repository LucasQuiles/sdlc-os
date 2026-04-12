#!/bin/bash
# Predicate computation for sdlc-dispatch.sh.
# Source this file, then call compute_predicates "$file_path" "$content".
# All predicates are set as P_* variables (true/false).

# shellcheck source=common.sh
[[ -n "${_SDLC_COMMON_LOADED:-}" ]] || source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

reset_predicates() {
  P_VENDOR_PATH=false
  P_JS_TS_SOURCE=false
  P_GENERIC_SOURCE=false
  P_SDLC_ACTIVE=false
  P_BEAD=false
  P_AQS_ARTIFACT=false
  P_DECISION_TRACE_FILE=false
  P_HARDENING_REPORT=false
  P_STATE_MD=false
  P_FEATURE_MATRIX=false
  P_CONVENTION_REPORT=false
  P_QUALITY_BUDGET=false
  P_HAZARD_LEDGER=false
  P_STRESS_SESSION=false
  P_DECISION_NOISE=false
  P_MODE_CONVERGENCE=false
}

compute_predicates() {
  local file_path="$1"
  local content="$2"

  reset_predicates

  # --- vendor_path ---
  if [[ -z "$file_path" ]] || is_vendor_path "$file_path"; then
    P_VENDOR_PATH=true
    return 0
  fi

  local basename
  basename=$(basename "$file_path")
  local ext="${basename##*.}"

  # --- js_ts_source ---
  case "$ext" in
    ts|tsx|js|jsx) P_JS_TS_SOURCE=true ;;
  esac

  # --- generic_source (not doc/config/data extensions) ---
  case "$ext" in
    md|json|yaml|yml|txt|toml|ini|cfg|conf|lock|sum) ;;
    *) P_GENERIC_SOURCE=true ;;
  esac

  # --- sdlc_active ---
  [[ "$file_path" == *"docs/sdlc/active/"* ]] && P_SDLC_ACTIVE=true

  # --- bead ---
  [[ "$file_path" =~ docs/sdlc/active/.*/beads/.*\.md$ ]] && P_BEAD=true

  # --- aqs_artifact ---
  if [[ "$file_path" =~ docs/sdlc/active/.*/adversarial/ ]] || [[ "$basename" == *-aqs.md ]]; then
    P_AQS_ARTIFACT=true
  fi

  # --- decision_trace_file ---
  [[ "$basename" == *-decision-trace.md ]] && P_DECISION_TRACE_FILE=true

  # --- hardening_report ---
  [[ "$basename" == "hardening-report.md" ]] && P_HARDENING_REPORT=true

  # --- state_md ---
  [[ "$basename" == "state.md" ]] && P_STATE_MD=true

  # --- feature_matrix ---
  [[ "$basename" == "feature-matrix.md" ]] && P_FEATURE_MATRIX=true

  # --- convention_report ---
  if [[ "$basename" == *convention-report* ]] || [[ "$basename" == *-convention-report.md ]]; then
    P_CONVENTION_REPORT=true
  elif [[ "$content" == *"## Convention Enforcement Report"* ]]; then
    P_CONVENTION_REPORT=true
  fi

  # --- named YAML artifacts ---
  [[ "$basename" == *quality-budget.yaml ]] && P_QUALITY_BUDGET=true
  [[ "$basename" == *hazard-defense-ledger.yaml ]] && P_HAZARD_LEDGER=true
  [[ "$basename" == *stress-session.yaml ]] && P_STRESS_SESSION=true
  [[ "$basename" == *decision-noise-summary.yaml ]] && P_DECISION_NOISE=true
  [[ "$basename" == *mode-convergence-summary.yaml ]] && P_MODE_CONVERGENCE=true
  return 0
}
