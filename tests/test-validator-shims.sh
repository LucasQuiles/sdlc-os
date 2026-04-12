#!/bin/bash
set -euo pipefail

PASS=0
FAIL=0

test_shim() {
  local script="$1" payload="$2" expected_exit="$3" desc="$4"
  local actual_exit=0
  echo "$payload" | bash "$script" > /dev/null 2>&1 || actual_exit=$?
  if [[ "$actual_exit" -eq "$expected_exit" ]]; then
    PASS=$((PASS + 1))
  else
    echo "FAIL: $desc — expected exit $expected_exit, got $actual_exit" >&2
    FAIL=$((FAIL + 1))
  fi
}

HOOKS_DIR="$HOME/LAB/sdlc-os/hooks/scripts"

test_shim "$HOOKS_DIR/validate-quality-budget.sh" \
  '{"tool_name":"Write","tool_input":{"file_path":"/tmp/foo.py","content":"x"}}' \
  0 "quality-budget shim exits 0 for non-matching path"

test_shim "$HOOKS_DIR/validate-hardening-report.sh" \
  '{"tool_name":"Write","tool_input":{"file_path":"/tmp/foo.py","content":"x"}}' \
  0 "hardening-report shim exits 0 for non-matching path"

test_shim "$HOOKS_DIR/guard-bead-status.sh" \
  '{"tool_name":"Write","tool_input":{"file_path":"/tmp/foo.py","content":"x"}}' \
  0 "bead-status shim exits 0 for non-matching path"

test_shim "$HOOKS_DIR/lint-domain-vocabulary.sh" \
  '{"tool_name":"Write","tool_input":{"file_path":"/tmp/foo.py","content":"x"}}' \
  0 "domain-vocabulary shim exits 0 for non-matching path"

test_shim "$HOOKS_DIR/validate-safety-constraints.sh" \
  '{"tool_name":"Write","tool_input":{"file_path":"/tmp/foo.md","content":"x"}}' \
  0 "safety-constraints shim exits 0 for .md extension"

test_shim "$HOOKS_DIR/check-eslint-disable-justification.sh" \
  '{"tool_name":"Write","tool_input":{"file_path":"/tmp/foo.py","content":"x"}}' \
  0 "eslint-disable shim exits 0 for .py extension"

test_shim "$HOOKS_DIR/warn-phase-transition.sh" \
  '{"tool_name":"Write","tool_input":{"file_path":"/tmp/foo.py","content":"x"}}' \
  0 "phase-transition shim exits 0 for non-state.md"

test_shim "$HOOKS_DIR/validate-aqs-artifact.sh" \
  '{"tool_name":"Write","tool_input":{"file_path":"/tmp/foo.py","content":"x"}}' \
  0 "aqs-artifact shim exits 0 for non-matching path"

test_shim "$HOOKS_DIR/validate-decision-trace.sh" \
  '{"tool_name":"Write","tool_input":{"file_path":"/tmp/foo.py","content":"x"}}' \
  0 "decision-trace shim exits 0 for non-matching path"

test_shim "$HOOKS_DIR/validate-consistency-artifacts.sh" \
  '{"tool_name":"Write","tool_input":{"file_path":"/tmp/foo.py","content":"x"}}' \
  0 "consistency shim exits 0 for non-matching path"

test_shim "$HOOKS_DIR/validate-hazard-defense-ledger.sh" \
  '{"tool_name":"Write","tool_input":{"file_path":"/tmp/foo.py","content":"x"}}' \
  0 "hazard-ledger shim exits 0 for non-matching path"

test_shim "$HOOKS_DIR/validate-stress-session.sh" \
  '{"tool_name":"Write","tool_input":{"file_path":"/tmp/foo.py","content":"x"}}' \
  0 "stress-session shim exits 0 for non-matching path"

test_shim "$HOOKS_DIR/validate-decision-noise-summary.sh" \
  '{"tool_name":"Write","tool_input":{"file_path":"/tmp/foo.py","content":"x"}}' \
  0 "decision-noise shim exits 0 for non-matching path"

test_shim "$HOOKS_DIR/validate-mode-convergence-summary.sh" \
  '{"tool_name":"Write","tool_input":{"file_path":"/tmp/foo.py","content":"x"}}' \
  0 "mode-convergence shim exits 0 for non-matching path"

echo "Results: $PASS passed, $FAIL failed"
[[ "$FAIL" -eq 0 ]]
