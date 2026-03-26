#!/bin/bash
# Hook Regression Test Suite
# Run: bash hooks/tests/test-hooks.sh
# Tests all three hooks with fixture inputs and expected exit codes.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOKS_DIR="$(cd "$SCRIPT_DIR/../scripts" && pwd)"
FIXTURES_DIR="$SCRIPT_DIR/fixtures"
PASS=0
FAIL=0

run_test() {
  local test_name="$1"
  local hook_script="$2"
  local fixture_file="$3"
  local expected_exit="$4"

  local actual_exit=0
  cat "$fixture_file" | bash "$hook_script" > /dev/null 2>&1 || actual_exit=$?

  if [[ "$actual_exit" -eq "$expected_exit" ]]; then
    echo "  PASS: $test_name (exit $actual_exit)"
    PASS=$((PASS + 1))
  else
    echo "  FAIL: $test_name (expected exit $expected_exit, got $actual_exit)"
    FAIL=$((FAIL + 1))
  fi
}

echo "=== Bead Status Guard Tests ==="

run_test "valid: pending->running" \
  "$HOOKS_DIR/guard-bead-status.sh" \
  "$FIXTURES_DIR/status-valid-pending-running.json" 0

run_test "valid: proven->merged (trivial skip)" \
  "$HOOKS_DIR/guard-bead-status.sh" \
  "$FIXTURES_DIR/status-valid-proven-merged.json" 0

run_test "design-intent: verified->merged (no git history in test env)" \
  "$HOOKS_DIR/guard-bead-status.sh" \
  "$FIXTURES_DIR/status-illegal-verified-merged.json" 0

run_test "design-intent: verified->hardened (no git history in test env)" \
  "$HOOKS_DIR/guard-bead-status.sh" \
  "$FIXTURES_DIR/status-illegal-verified-hardened.json" 0

run_test "valid: non-bead file (skip)" \
  "$HOOKS_DIR/guard-bead-status.sh" \
  "$FIXTURES_DIR/status-non-bead-file.json" 0

echo ""
echo "=== AQS Artifact Validator Tests ==="

run_test "valid: complete finding" \
  "$HOOKS_DIR/validate-aqs-artifact.sh" \
  "$FIXTURES_DIR/finding-valid.json" 0

run_test "BLOCK: finding missing fields" \
  "$HOOKS_DIR/validate-aqs-artifact.sh" \
  "$FIXTURES_DIR/finding-missing-fields.json" 2

run_test "BLOCK: finding with bad domain" \
  "$HOOKS_DIR/validate-aqs-artifact.sh" \
  "$FIXTURES_DIR/finding-bad-domain.json" 2

run_test "BLOCK: second finding missing fields (per-block)" \
  "$HOOKS_DIR/validate-aqs-artifact.sh" \
  "$FIXTURES_DIR/finding-second-malformed.json" 2

run_test "valid: complete accepted response" \
  "$HOOKS_DIR/validate-aqs-artifact.sh" \
  "$FIXTURES_DIR/response-valid-accepted.json" 0

run_test "BLOCK: accepted response missing defensive iteration" \
  "$HOOKS_DIR/validate-aqs-artifact.sh" \
  "$FIXTURES_DIR/response-missing-iteration.json" 2

run_test "BLOCK: second accepted response missing iteration (per-block)" \
  "$HOOKS_DIR/validate-aqs-artifact.sh" \
  "$FIXTURES_DIR/response-second-missing-iteration.json" 2

run_test "valid: complete verdict" \
  "$HOOKS_DIR/validate-aqs-artifact.sh" \
  "$FIXTURES_DIR/verdict-valid.json" 0

run_test "BLOCK: verdict missing pre-commitment" \
  "$HOOKS_DIR/validate-aqs-artifact.sh" \
  "$FIXTURES_DIR/verdict-missing-precommit.json" 2

run_test "valid: non-AQS file (skip)" \
  "$HOOKS_DIR/validate-aqs-artifact.sh" \
  "$FIXTURES_DIR/non-aqs-file.json" 0

echo ""
echo "=== Domain Vocabulary Linter Tests ==="

run_test "valid: canonical domains" \
  "$HOOKS_DIR/lint-domain-vocabulary.sh" \
  "$FIXTURES_DIR/vocab-valid.json" 0

run_test "BLOCK: non-canonical domain" \
  "$HOOKS_DIR/lint-domain-vocabulary.sh" \
  "$FIXTURES_DIR/vocab-bad-domain.json" 2

run_test "valid: non-SDLC file (skip)" \
  "$HOOKS_DIR/lint-domain-vocabulary.sh" \
  "$FIXTURES_DIR/vocab-non-sdlc.json" 0

echo ""
echo "=== Results ==="
echo "PASS: $PASS  FAIL: $FAIL  TOTAL: $((PASS + FAIL))"

if [[ "$FAIL" -gt 0 ]]; then
  echo "REGRESSION DETECTED"
  exit 1
else
  echo "ALL TESTS PASSED"
  exit 0
fi
