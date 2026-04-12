#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/../hooks/lib/predicates.sh"

PASS=0
FAIL=0

assert_predicate() {
  local pred="$1" expected="$2" desc="$3"
  local actual="${!pred}"
  if [[ "$actual" == "$expected" ]]; then
    PASS=$((PASS + 1))
  else
    echo "FAIL: $desc — expected $pred=$expected, got $actual" >&2
    FAIL=$((FAIL + 1))
  fi
}

# --- vendor_path ---
reset_predicates
compute_predicates "" ""
assert_predicate "P_VENDOR_PATH" "true" "empty path is vendor"

reset_predicates
compute_predicates "/home/q/LAB/project/node_modules/foo/bar.ts" ""
assert_predicate "P_VENDOR_PATH" "true" "node_modules is vendor"

reset_predicates
compute_predicates "/home/q/LAB/project/dist/bundle.js" ""
assert_predicate "P_VENDOR_PATH" "true" "dist is vendor"

reset_predicates
compute_predicates "/home/q/LAB/project/vendor/lib.js" ""
assert_predicate "P_VENDOR_PATH" "true" "vendor/ is vendor"

reset_predicates
compute_predicates "/home/q/LAB/project/src/app.ts" ""
assert_predicate "P_VENDOR_PATH" "false" "src/app.ts is not vendor"

# --- js_ts_source ---
reset_predicates
compute_predicates "/home/q/LAB/project/src/app.ts" ""
assert_predicate "P_JS_TS_SOURCE" "true" ".ts is js_ts_source"

reset_predicates
compute_predicates "/home/q/LAB/project/src/app.tsx" ""
assert_predicate "P_JS_TS_SOURCE" "true" ".tsx is js_ts_source"

reset_predicates
compute_predicates "/home/q/LAB/project/src/app.py" ""
assert_predicate "P_JS_TS_SOURCE" "false" ".py is not js_ts_source"

reset_predicates
compute_predicates "/home/q/LAB/project/node_modules/foo.ts" ""
assert_predicate "P_JS_TS_SOURCE" "false" "vendor .ts is not js_ts_source"

# --- generic_source ---
reset_predicates
compute_predicates "/home/q/LAB/project/src/app.py" ""
assert_predicate "P_GENERIC_SOURCE" "true" ".py is generic_source"

reset_predicates
compute_predicates "/home/q/LAB/project/src/app.ts" ""
assert_predicate "P_GENERIC_SOURCE" "true" ".ts is also generic_source"

reset_predicates
compute_predicates "/home/q/LAB/project/README.md" ""
assert_predicate "P_GENERIC_SOURCE" "false" ".md is not generic_source"

reset_predicates
compute_predicates "/home/q/LAB/project/config.json" ""
assert_predicate "P_GENERIC_SOURCE" "false" ".json is not generic_source"

reset_predicates
compute_predicates "/home/q/LAB/project/data.yaml" ""
assert_predicate "P_GENERIC_SOURCE" "false" ".yaml is not generic_source"

reset_predicates
compute_predicates "/home/q/LAB/project/data.yml" ""
assert_predicate "P_GENERIC_SOURCE" "false" ".yml is not generic_source"

reset_predicates
compute_predicates "/home/q/LAB/project/go.sum" ""
assert_predicate "P_GENERIC_SOURCE" "false" ".sum is not generic_source"

# --- sdlc_active ---
reset_predicates
compute_predicates "/home/q/LAB/project/docs/sdlc/active/task-1/beads/bead-001.md" ""
assert_predicate "P_SDLC_ACTIVE" "true" "SDLC bead path"

reset_predicates
compute_predicates "/home/q/LAB/project/src/app.ts" ""
assert_predicate "P_SDLC_ACTIVE" "false" "non-SDLC path"

# --- bead ---
reset_predicates
compute_predicates "/home/q/LAB/project/docs/sdlc/active/task-1/beads/bead-001.md" ""
assert_predicate "P_BEAD" "true" "bead path"

reset_predicates
compute_predicates "/home/q/LAB/project/docs/sdlc/active/task-1/state.md" ""
assert_predicate "P_BEAD" "false" "state.md is not a bead"

# --- aqs_artifact ---
reset_predicates
compute_predicates "/home/q/LAB/project/docs/sdlc/active/task-1/adversarial/report.md" ""
assert_predicate "P_AQS_ARTIFACT" "true" "adversarial dir"

reset_predicates
compute_predicates "/home/q/LAB/project/docs/sdlc/active/task-1/beads/bead-001-aqs.md" ""
assert_predicate "P_AQS_ARTIFACT" "true" "-aqs.md basename"

reset_predicates
compute_predicates "/home/q/LAB/project/docs/sdlc/active/task-1/beads/bead-001.md" ""
assert_predicate "P_AQS_ARTIFACT" "false" "regular bead is not AQS"

# --- decision_trace_file ---
reset_predicates
compute_predicates "/home/q/LAB/project/docs/sdlc/active/task-1/beads/bead-001-decision-trace.md" ""
assert_predicate "P_DECISION_TRACE_FILE" "true" "decision trace file"

reset_predicates
compute_predicates "/home/q/LAB/project/docs/sdlc/active/task-1/beads/bead-001.md" ""
assert_predicate "P_DECISION_TRACE_FILE" "false" "regular bead is not trace"

# --- hardening_report ---
reset_predicates
compute_predicates "/home/q/LAB/project/docs/sdlc/active/task-1/hardening-report.md" ""
assert_predicate "P_HARDENING_REPORT" "true" "hardening report"

reset_predicates
compute_predicates "/home/q/LAB/project/hardening-report.md" ""
assert_predicate "P_HARDENING_REPORT" "true" "hardening report outside SDLC"

# --- state_md ---
reset_predicates
compute_predicates "/home/q/LAB/project/docs/sdlc/active/task-1/state.md" ""
assert_predicate "P_STATE_MD" "true" "state.md under SDLC"

reset_predicates
compute_predicates "/home/q/LAB/project/state.md" ""
assert_predicate "P_STATE_MD" "true" "state.md anywhere"

# --- named YAML artifacts ---
reset_predicates
compute_predicates "/home/q/LAB/project/docs/sdlc/active/task-1/quality-budget.yaml" ""
assert_predicate "P_QUALITY_BUDGET" "true" "quality-budget.yaml"

reset_predicates
compute_predicates "/home/q/LAB/project/docs/sdlc/active/task-1/hazard-defense-ledger.yaml" ""
assert_predicate "P_HAZARD_LEDGER" "true" "hazard-defense-ledger.yaml"

reset_predicates
compute_predicates "/home/q/LAB/project/docs/sdlc/active/task-1/stress-session.yaml" ""
assert_predicate "P_STRESS_SESSION" "true" "stress-session.yaml"

reset_predicates
compute_predicates "/home/q/LAB/project/docs/sdlc/active/task-1/decision-noise-summary.yaml" ""
assert_predicate "P_DECISION_NOISE" "true" "decision-noise-summary.yaml"

reset_predicates
compute_predicates "/home/q/LAB/project/docs/sdlc/active/task-1/mode-convergence-summary.yaml" ""
assert_predicate "P_MODE_CONVERGENCE" "true" "mode-convergence-summary.yaml"

# --- feature_matrix ---
reset_predicates
compute_predicates "/home/q/LAB/project/docs/sdlc/feature-matrix.md" ""
assert_predicate "P_FEATURE_MATRIX" "true" "feature-matrix.md"

# --- convention_report (path-based) ---
reset_predicates
compute_predicates "/home/q/LAB/project/docs/sdlc/active/task-1/convention-report.md" ""
assert_predicate "P_CONVENTION_REPORT" "true" "convention-report.md"

# --- convention_report (content-based) ---
reset_predicates
compute_predicates "/home/q/LAB/project/docs/sdlc/active/task-1/report.md" "## Convention Enforcement Report"
assert_predicate "P_CONVENTION_REPORT" "true" "content-based convention report"

# --- overlapping predicates ---
reset_predicates
compute_predicates "/home/q/LAB/project/docs/sdlc/active/task-1/quality-budget.yaml" ""
assert_predicate "P_SDLC_ACTIVE" "true" "quality-budget under SDLC is also sdlc_active"
assert_predicate "P_QUALITY_BUDGET" "true" "quality-budget under SDLC is also quality_budget"

echo "Results: $PASS passed, $FAIL failed"
[[ "$FAIL" -eq 0 ]]
