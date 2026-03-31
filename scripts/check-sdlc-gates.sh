#!/bin/bash
# check-sdlc-gates.sh — Validate SDLC telemetry gates for a task
# Usage: check-sdlc-gates.sh <task-dir> <target-phase> --project-dir <dir>
#
# <target-phase>: synthesize | complete
#
# Exit codes:
#   0 — all applicable gates pass
#   1 — one or more gate failures
#   2 — usage error
#
# Checks are printed to stderr as PASS/FAIL/WARN lines.
# No beads = WARN (not fail).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/sdlc-common.sh"

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
if [ $# -lt 2 ]; then
  echo "Usage: check-sdlc-gates.sh <task-dir> <target-phase> --project-dir <dir>" >&2
  exit 2
fi

TASK_DIR="$1"
TARGET_PHASE="$2"
shift 2

PROJECT_DIR=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --project-dir) PROJECT_DIR="${2:?--project-dir requires a value}"; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
done

if [ -z "$PROJECT_DIR" ]; then
  echo "ERROR: --project-dir is required" >&2
  exit 2
fi

if [[ "$TARGET_PHASE" != "synthesize" && "$TARGET_PHASE" != "complete" ]]; then
  echo "ERROR: <target-phase> must be 'synthesize' or 'complete', got: $TARGET_PHASE" >&2
  exit 2
fi

[ -d "$TASK_DIR" ] || { echo "ERROR: Task directory not found: $TASK_DIR" >&2; exit 2; }

TASK_ID="$(basename "$TASK_DIR")"

# ---------------------------------------------------------------------------
# Lane classification
# ---------------------------------------------------------------------------
classify_task_lanes "$TASK_DIR" "$TASK_ID" "$PROJECT_DIR"

# ---------------------------------------------------------------------------
# Gate tracking
# ---------------------------------------------------------------------------
FAILURES=0
WARNINGS=0

pass() { echo "PASS: $*" >&2; }
fail() { echo "FAIL: $*" >&2; FAILURES=$((FAILURES + 1)); }
warn() { echo "WARN: $*" >&2; WARNINGS=$((WARNINGS + 1)); }

# ---------------------------------------------------------------------------
# Helper: check artifact_status meets minimum threshold
#
# Status ordering: partial < ready < active < final
# We treat 'active' as >= 'ready' for HDL/stress (which use active/final).
# For summary artifacts that use partial/ready/final, partial < ready < final.
# ---------------------------------------------------------------------------
STATUS_RANK() {
  case "$1" in
    partial) echo 1 ;;
    ready)   echo 2 ;;
    active)  echo 2 ;;
    final)   echo 3 ;;
    *)       echo 0 ;;
  esac
}

yaml_artifact_status() {
  local file="$1"
  python3 - "$file" <<'PY'
import sys, yaml
with open(sys.argv[1]) as f:
    d = yaml.safe_load(f)
print(d.get("artifact_status", "") if d else "")
PY
}

check_artifact_status() {
  # check_artifact_status <file> <field-label> <min-status>
  local file="$1" label="$2" min_status="$3"
  if [ ! -f "$file" ]; then
    fail "$label: file not found ($file)"
    return
  fi
  local actual
  actual="$(yaml_artifact_status "$file" 2>/dev/null || echo "")"
  local actual_rank min_rank
  actual_rank="$(STATUS_RANK "$actual")"
  min_rank="$(STATUS_RANK "$min_status")"
  if [ "$actual_rank" -lt "$min_rank" ] || [ "$actual_rank" -eq 0 ]; then
    fail "$label: artifact_status '$actual' does not meet minimum '$min_status'"
  else
    pass "$label: artifact_status=$actual (>= $min_status)"
  fi
}

yaml_field_nonnull() {
  # Returns 0 if field is non-null/non-empty, 1 otherwise
  python3 - "$1" "$2" <<'PY'
import sys, yaml
with open(sys.argv[1]) as f:
    d = yaml.safe_load(f)
key = sys.argv[2]
val = d.get(key) if d else None
sys.exit(0 if val is not None else 1)
PY
}

# ---------------------------------------------------------------------------
# PyYAML guard
# ---------------------------------------------------------------------------
if ! check_pyyaml; then
  echo "ERROR: python3 with PyYAML is required. Install: pip3 install pyyaml" >&2
  exit 2
fi

# ---------------------------------------------------------------------------
# No-beads advisory
# ---------------------------------------------------------------------------
if [ "$HAS_BEADS" = false ]; then
  warn "No beads found in $TASK_DIR/beads/ — telemetry gates may be incomplete"
fi

# ---------------------------------------------------------------------------
# SYNTHESIZE gates
# ---------------------------------------------------------------------------

run_synthesize_checks() {
  # quality-budget.yaml: exists with artifact_status >= ready (if HAS_BEADS)
  if [ "$HAS_BEADS" = true ]; then
    local qb="$TASK_DIR/quality-budget.yaml"
    check_artifact_status "$qb" "quality-budget artifact_status" "ready"

    # All derived fields non-null except estimate_s and sli_readings
    if [ -f "$qb" ]; then
      # Top-level derived fields
      for field in task_id complexity_weight turbulence_sum budget_state; do
        if yaml_field_nonnull "$qb" "$field" 2>/dev/null; then
          pass "quality-budget.$field is non-null"
        else
          fail "quality-budget.$field is null (required derived field)"
        fi
      done

      # Required nested sections (must exist as non-empty dicts/lists)
      local _qb_sections_ok
      _qb_sections_ok="$(python3 - "$qb" <<'PY'
import sys, yaml
with open(sys.argv[1]) as f:
    d = yaml.safe_load(f) or {}
required = ["cynefin_mix", "beads", "corrections", "metrics", "timing", "escapes"]
missing = [s for s in required if not d.get(s)]
print(" ".join(missing) if missing else "OK")
PY
2>/dev/null || echo "ERROR")"
      if [ "$_qb_sections_ok" = "OK" ]; then
        pass "quality-budget: all required sections present (cynefin_mix, beads, corrections, metrics, timing, escapes)"
      elif [ "$_qb_sections_ok" = "ERROR" ]; then
        fail "quality-budget: failed to validate nested sections"
      else
        fail "quality-budget: missing required sections: $_qb_sections_ok"
      fi

      # sli_readings: WARN if inner values are all null, not fail
      local sli_null_count
      sli_null_count="$(python3 - "$qb" <<'PY'
import sys, yaml
with open(sys.argv[1]) as f:
    d = yaml.safe_load(f)
sli = d.get("sli_readings", {}) if d else {}
if not sli:
    print("ALL")
else:
    nulls = sum(1 for v in sli.values() if v is None)
    print("ALL" if nulls == len(sli) else str(nulls))
PY
2>/dev/null || echo "ERROR")"
      if [ "$sli_null_count" = "ALL" ]; then
        warn "quality-budget.sli_readings: all values null (deferred — project-specific enforcement)"
      elif [ "$sli_null_count" = "0" ]; then
        pass "quality-budget.sli_readings: all values populated"
      else
        warn "quality-budget.sli_readings: $sli_null_count value(s) null"
      fi
    fi

    # mode-convergence-summary.yaml: exists with artifact_status >= partial (if HAS_BEADS)
    check_artifact_status "$TASK_DIR/mode-convergence-summary.yaml" "mode-convergence-summary artifact_status" "partial"
  fi

  # hazard-defense-ledger.yaml: exists with artifact_status >= active (if IS_STPA)
  if [ "$IS_STPA" = true ]; then
    check_artifact_status "$TASK_DIR/hazard-defense-ledger.yaml" "hazard-defense-ledger artifact_status" "active"
  fi

  # stress-session.yaml: exists with artifact_status >= active (if IS_STRESSED)
  if [ "$IS_STRESSED" = true ]; then
    check_artifact_status "$TASK_DIR/stress-session.yaml" "stress-session artifact_status" "active"
  fi

  # decision-noise-summary.yaml: exists with artifact_status >= partial (if IS_AQS)
  if [ "$IS_AQS" = true ]; then
    check_artifact_status "$TASK_DIR/decision-noise-summary.yaml" "decision-noise-summary artifact_status" "partial"
  fi
}

# ---------------------------------------------------------------------------
# COMPLETE gates (task-local)
# ---------------------------------------------------------------------------

run_complete_local_checks() {
  # All synthesize checks apply first (with 'final' status requirement)
  if [ "$HAS_BEADS" = true ]; then
    local qb="$TASK_DIR/quality-budget.yaml"
    check_artifact_status "$qb" "quality-budget artifact_status" "final"

    if [ -f "$qb" ]; then
      # budget_state must be computed (non-null)
      if yaml_field_nonnull "$qb" "budget_state" 2>/dev/null; then
        pass "quality-budget.budget_state is computed"
      else
        fail "quality-budget.budget_state is null (must be computed for complete)"
      fi

      # Required nested sections
      local _qb_sections_ok
      _qb_sections_ok="$(python3 - "$qb" <<'PY'
import sys, yaml
with open(sys.argv[1]) as f:
    d = yaml.safe_load(f) or {}
required = ["cynefin_mix", "beads", "corrections", "metrics", "timing", "escapes"]
missing = [s for s in required if not d.get(s)]
print(" ".join(missing) if missing else "OK")
PY
2>/dev/null || echo "ERROR")"
      if [ "$_qb_sections_ok" = "OK" ]; then
        pass "quality-budget: all required sections present"
      elif [ "$_qb_sections_ok" = "ERROR" ]; then
        fail "quality-budget: failed to validate nested sections"
      else
        fail "quality-budget: missing required sections: $_qb_sections_ok"
      fi

      # All required derived fields non-null
      for field in task_id complexity_weight turbulence_sum budget_state; do
        if yaml_field_nonnull "$qb" "$field" 2>/dev/null; then
          pass "quality-budget.$field is non-null"
        else
          fail "quality-budget.$field is null (required derived field)"
        fi
      done

      # sli_readings: WARN if inner values are all null, not fail (same as synthesize)
      local sli_null_count
      sli_null_count="$(python3 - "$qb" <<'PY'
import sys, yaml
with open(sys.argv[1]) as f:
    d = yaml.safe_load(f)
sli = d.get("sli_readings", {}) if d else {}
if not sli:
    print("ALL")
else:
    nulls = sum(1 for v in sli.values() if v is None)
    print("ALL" if nulls == len(sli) else str(nulls))
PY
2>/dev/null || echo "ERROR")"
      if [ "$sli_null_count" = "ALL" ]; then
        warn "quality-budget.sli_readings: all values null (deferred — project-specific enforcement)"
      elif [ "$sli_null_count" = "0" ]; then
        pass "quality-budget.sli_readings: all values populated"
      else
        warn "quality-budget.sli_readings: $sli_null_count value(s) null"
      fi
    fi

    check_artifact_status "$TASK_DIR/mode-convergence-summary.yaml" "mode-convergence-summary artifact_status" "final"
  fi

  # HDL complete checks
  if [ "$IS_STPA" = true ]; then
    local hdl="$TASK_DIR/hazard-defense-ledger.yaml"
    check_artifact_status "$hdl" "hazard-defense-ledger artifact_status" "final"

    if [ -f "$hdl" ]; then
      # No open records — all records must have status in {caught, escaped, accepted_residual}
      local open_count
      open_count="$(python3 - "$hdl" <<'PY'
import sys, yaml
with open(sys.argv[1]) as f:
    d = yaml.safe_load(f)
records = d.get("records", []) if d else []
open_records = [r for r in records if r.get("status", "") == "open"]
print(len(open_records))
PY
2>/dev/null || echo "ERROR")"
      if [ "$open_count" = "ERROR" ]; then
        fail "hazard-defense-ledger: failed to parse records"
      elif [ "$open_count" -gt 0 ]; then
        fail "hazard-defense-ledger: $open_count open record(s) remain (must be caught/escaped/accepted_residual)"
      else
        pass "hazard-defense-ledger: no open records remain"
      fi

      # summary.coverage_state must be computed
      local cov_state
      cov_state="$(python3 - "$hdl" <<'PY'
import sys, yaml
with open(sys.argv[1]) as f:
    d = yaml.safe_load(f)
summary = d.get("summary", {}) if d else {}
val = summary.get("coverage_state")
print(val if val is not None else "")
PY
2>/dev/null || echo "")"
      if [ -n "$cov_state" ]; then
        pass "hazard-defense-ledger.summary.coverage_state=$cov_state"
      else
        fail "hazard-defense-ledger.summary.coverage_state is null/missing"
      fi
    fi
  fi

  # Stress session complete checks
  if [ "$IS_STRESSED" = true ]; then
    local ss="$TASK_DIR/stress-session.yaml"
    check_artifact_status "$ss" "stress-session artifact_status" "final"

    if [ -f "$ss" ]; then
      local pending_count
      pending_count="$(python3 - "$ss" <<'PY'
import sys, yaml
with open(sys.argv[1]) as f:
    d = yaml.safe_load(f)
applications = d.get("stressors_applied", []) if d else []
pending = [a for a in applications if a.get("result") is None or a.get("result", "") == "pending"]
print(len(pending))
PY
2>/dev/null || echo "ERROR")"
      if [ "$pending_count" = "ERROR" ]; then
        fail "stress-session: failed to parse stressors_applied"
      elif [ "$pending_count" -gt 0 ]; then
        fail "stress-session: $pending_count stressor application(s) still pending (unresolved)"
      else
        pass "stress-session: all stressor applications resolved"
      fi
    fi
  fi

  # AQS complete checks
  if [ "$IS_AQS" = true ]; then
    check_artifact_status "$TASK_DIR/decision-noise-summary.yaml" "decision-noise-summary artifact_status" "final"
  fi
}

# ---------------------------------------------------------------------------
# COMPLETE gates (system ledger)
# ---------------------------------------------------------------------------

run_complete_system_checks() {
  local sdlc_dir="$PROJECT_DIR/docs/sdlc"

  # system-budget.jsonl (if HAS_BEADS)
  if [ "$HAS_BEADS" = true ]; then
    local sb="$sdlc_dir/system-budget.jsonl"
    if grep -qF "\"$TASK_ID\"" "$sb" 2>/dev/null; then
      pass "system-budget.jsonl: task_id '$TASK_ID' found"
    else
      fail "system-budget.jsonl: task_id '$TASK_ID' not found in $sb"
    fi

    # system-mode-convergence.jsonl (if HAS_BEADS)
    local smc="$sdlc_dir/system-mode-convergence.jsonl"
    if grep -qF "\"$TASK_ID\"" "$smc" 2>/dev/null; then
      pass "system-mode-convergence.jsonl: task_id '$TASK_ID' found"
    else
      fail "system-mode-convergence.jsonl: task_id '$TASK_ID' not found in $smc"
    fi
  fi

  # system-hazard-defense.jsonl (if IS_STPA)
  if [ "$IS_STPA" = true ]; then
    local shd="$sdlc_dir/system-hazard-defense.jsonl"
    if grep -qF "\"$TASK_ID\"" "$shd" 2>/dev/null; then
      pass "system-hazard-defense.jsonl: task_id '$TASK_ID' found"
    else
      fail "system-hazard-defense.jsonl: task_id '$TASK_ID' not found in $shd"
    fi
  fi

  # system-stress.jsonl (if IS_STRESSED)
  if [ "$IS_STRESSED" = true ]; then
    local ss_ledger="$sdlc_dir/system-stress.jsonl"
    if grep -qF "\"$TASK_ID\"" "$ss_ledger" 2>/dev/null; then
      pass "system-stress.jsonl: task_id '$TASK_ID' found"
    else
      fail "system-stress.jsonl: task_id '$TASK_ID' not found in $ss_ledger"
    fi
  fi
}

# ---------------------------------------------------------------------------
# Dispatch by phase
# ---------------------------------------------------------------------------
echo "--- check-sdlc-gates: $TASK_ID / $TARGET_PHASE ---" >&2
echo "  HAS_BEADS=$HAS_BEADS  IS_STPA=$IS_STPA  IS_AQS=$IS_AQS  IS_STRESSED=$IS_STRESSED" >&2

case "$TARGET_PHASE" in
  synthesize)
    run_synthesize_checks
    ;;
  complete)
    run_complete_local_checks
    run_complete_system_checks
    ;;
esac

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo "--- gate summary: $FAILURES failure(s), $WARNINGS warning(s) ---" >&2

if [ "$FAILURES" -gt 0 ]; then
  exit 1
fi
exit 0
