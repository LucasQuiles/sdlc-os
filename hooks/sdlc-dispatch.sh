#!/bin/bash
# SDLC-OS PostToolUse dispatcher.
# Replaces 15 separate hook entries with one predicate-routed entry point.
# Reads stdin once, classifies the file, runs only matching validators.
#
# Blocking contract:
#   exit 0 = pass
#   exit 2 = block (validator stderr preserved)
#   exit 1 or other = non-blocking hook error (stderr preserved, execution continues)
#
# Internal validator order (explicit policy — matches original settings.json array order):
#   1. validate-aqs-artifact        (BLOCK)
#   2. guard-bead-status             (BLOCK)
#   3. lint-domain-vocabulary        (BLOCK)
#   4. validate-consistency          (WARN)
#   5. validate-hardening-report     (BLOCK)
#   6. validate-decision-trace       (BLOCK)
#   7. validate-safety-constraints   (WARN)
#   8. ast-checks                    (WARN, structured JSON)
#   9. check-eslint-disable          (BLOCK)
#  10. validate-quality-budget       (BLOCK)
#  11. validate-hazard-ledger        (BLOCK)
#  12. validate-stress-session       (BLOCK)
#  13. validate-decision-noise       (BLOCK)
#  14. validate-mode-convergence     (BLOCK)
#  15. warn-phase-transition         (WARN)

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"
_SDLC_COMMON_LOADED=1
source "$SCRIPT_DIR/lib/predicates.sh"

# --- Read stdin once ---
load_hook_input_or_exit INPUT || exit 0

FILE_PATH=$(read_hook_file_path "$INPUT")

# --- Compute predicates ---
CONTENT=""
compute_predicates "$FILE_PATH" ""

# Fast path: vendor or no file
if [[ "$P_VENDOR_PATH" == "true" ]]; then
  exit 0
fi

# Check if any validator will fire at all
if [[ "$P_JS_TS_SOURCE" == "false" ]] && \
   [[ "$P_GENERIC_SOURCE" == "false" ]] && \
   [[ "$P_SDLC_ACTIVE" == "false" ]] && \
   [[ "$P_BEAD" == "false" ]] && \
   [[ "$P_AQS_ARTIFACT" == "false" ]] && \
   [[ "$P_HARDENING_REPORT" == "false" ]] && \
   [[ "$P_STATE_MD" == "false" ]] && \
   [[ "$P_FEATURE_MATRIX" == "false" ]] && \
   [[ "$P_CONVENTION_REPORT" == "false" ]] && \
   [[ "$P_QUALITY_BUDGET" == "false" ]] && \
   [[ "$P_HAZARD_LEDGER" == "false" ]] && \
   [[ "$P_STRESS_SESSION" == "false" ]] && \
   [[ "$P_DECISION_NOISE" == "false" ]] && \
   [[ "$P_MODE_CONVERGENCE" == "false" ]]; then
  exit 0
fi

# --- Lazy content load ---
if [[ "$P_AQS_ARTIFACT" == "true" ]] || \
   [[ "$P_BEAD" == "true" ]] || \
   [[ "$P_SDLC_ACTIVE" == "true" ]] || \
   [[ "$P_HARDENING_REPORT" == "true" ]] || \
   [[ "$P_GENERIC_SOURCE" == "true" ]] || \
   [[ "$P_JS_TS_SOURCE" == "true" ]] || \
   [[ "$P_FEATURE_MATRIX" == "true" ]] || \
   [[ "$P_CONVENTION_REPORT" == "true" ]]; then
  CONTENT=$(read_tool_content "$INPUT" "$FILE_PATH")
  # Recompute convention_report predicate with content
  if [[ "$P_CONVENTION_REPORT" == "false" ]] && [[ "$CONTENT" == *"## Convention Enforcement Report"* ]]; then
    P_CONVENTION_REPORT=true
  fi
fi

VALIDATORS_DIR="$SCRIPT_DIR/validators"

# --- Validator runner functions ---
# CONTRACT: Validator files MUST define only functions (no top-level side effects).
# Each file is source'd into this shell; top-level exits/failures would abort the
# dispatcher. The function name is the validator's entry point (passed to run_blocking
# or run_advisory). Known false-positive class: P_GENERIC_SOURCE matches .bak/.swp/.tmp
# extensions — these hit safety-constraints advisory validation, which is benign.
run_blocking() {
  local validator_file="$1"
  shift
  if [[ ! -f "$validator_file" ]]; then
    echo "HOOK_WARNING: missing validator file: $validator_file" >&2
    return 1
  fi
  source "$validator_file" || { echo "HOOK_WARNING: failed to source $validator_file" >&2; return 1; }
  local rc=0
  "$@" || rc=$?
  if [[ "$rc" -eq 2 ]]; then
    exit 2
  fi
}

run_advisory() {
  local validator_file="$1"
  shift
  if [[ ! -f "$validator_file" ]]; then
    echo "HOOK_WARNING: missing validator file: $validator_file" >&2
    return 1
  fi
  source "$validator_file" || { echo "HOOK_WARNING: failed to source $validator_file" >&2; return 1; }
  "$@" || true
}

# --- Run validators in order ---

# 1. validate-aqs-artifact (BLOCK)
if [[ "$P_AQS_ARTIFACT" == "true" ]]; then
  run_blocking "$VALIDATORS_DIR/aqs-artifact.sh" validate_aqs_artifact "$FILE_PATH" "$CONTENT"
fi

# 2. guard-bead-status (BLOCK)
if [[ "$P_BEAD" == "true" ]] && [[ "$P_AQS_ARTIFACT" == "false" ]]; then
  run_blocking "$VALIDATORS_DIR/bead-status.sh" validate_bead_status "$FILE_PATH" "$CONTENT"
fi

# 3. lint-domain-vocabulary (BLOCK)
if [[ "$P_SDLC_ACTIVE" == "true" ]]; then
  run_blocking "$VALIDATORS_DIR/domain-vocabulary.sh" validate_domain_vocabulary "$CONTENT"
fi

# 4. validate-consistency (WARN)
if [[ "$P_FEATURE_MATRIX" == "true" ]] || [[ "$P_CONVENTION_REPORT" == "true" ]]; then
  run_advisory "$VALIDATORS_DIR/consistency.sh" validate_consistency "$FILE_PATH" "$CONTENT"
fi

# 5. validate-hardening-report (BLOCK)
if [[ "$P_HARDENING_REPORT" == "true" ]]; then
  run_blocking "$VALIDATORS_DIR/hardening-report.sh" validate_hardening_report "$CONTENT"
fi

# 6. validate-decision-trace (BLOCK)
if [[ "$P_BEAD" == "true" ]] && [[ "$P_DECISION_TRACE_FILE" == "false" ]] && \
   [[ "$P_AQS_ARTIFACT" == "false" ]] && [[ "$P_HARDENING_REPORT" == "false" ]]; then
  run_blocking "$VALIDATORS_DIR/decision-trace.sh" validate_decision_trace "$FILE_PATH" "$CONTENT"
fi

# 7. validate-safety-constraints (WARN)
if [[ "$P_GENERIC_SOURCE" == "true" ]]; then
  run_advisory "$VALIDATORS_DIR/safety-constraints.sh" validate_safety_constraints "$FILE_PATH" "$CONTENT"
fi

# 8. ast-checks (WARN, structured JSON)
if [[ "$P_JS_TS_SOURCE" == "true" ]]; then
  run_advisory "$VALIDATORS_DIR/ast-checks-adapter.sh" validate_ast_checks "$FILE_PATH"
fi

# 9. check-eslint-disable (BLOCK)
if [[ "$P_JS_TS_SOURCE" == "true" ]]; then
  run_blocking "$VALIDATORS_DIR/eslint-disable.sh" validate_eslint_disable "$FILE_PATH" "$CONTENT"
fi

# 10. validate-quality-budget (BLOCK)
if [[ "$P_QUALITY_BUDGET" == "true" ]]; then
  run_blocking "$VALIDATORS_DIR/quality-budget.sh" validate_quality_budget "$FILE_PATH"
fi

# 11. validate-hazard-ledger (BLOCK)
if [[ "$P_HAZARD_LEDGER" == "true" ]]; then
  run_blocking "$VALIDATORS_DIR/hazard-ledger.sh" validate_hazard_ledger "$FILE_PATH"
fi

# 12. validate-stress-session (BLOCK)
if [[ "$P_STRESS_SESSION" == "true" ]]; then
  run_blocking "$VALIDATORS_DIR/stress-session.sh" validate_stress_session "$FILE_PATH"
fi

# 13. validate-decision-noise (BLOCK)
if [[ "$P_DECISION_NOISE" == "true" ]]; then
  run_blocking "$VALIDATORS_DIR/decision-noise.sh" validate_decision_noise "$FILE_PATH"
fi

# 14. validate-mode-convergence (BLOCK)
if [[ "$P_MODE_CONVERGENCE" == "true" ]]; then
  run_blocking "$VALIDATORS_DIR/mode-convergence.sh" validate_mode_convergence "$FILE_PATH"
fi

# 15. warn-phase-transition (WARN)
if [[ "$P_STATE_MD" == "true" ]]; then
  run_advisory "$VALIDATORS_DIR/phase-transition.sh" validate_phase_transition "$FILE_PATH" "$CONTENT"
fi

exit 0
