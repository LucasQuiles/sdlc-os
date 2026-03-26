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
echo "=== Bead Status Guard Integration Tests (git history) ==="

# These tests create a real git repo to verify transition blocking works
# with actual git history, including symlinked path forms.
run_integration_guard_test() {
  local TMPDIR_BASE
  TMPDIR_BASE=$(mktemp -d)
  trap "rm -rf '$TMPDIR_BASE'" RETURN

  local REPO="$TMPDIR_BASE/repo"
  mkdir -p "$REPO/docs/sdlc/active/test/beads"

  # Initialize git repo and commit a bead with status "verified"
  (cd "$REPO" && git init -q && git config user.email "test@test" && git config user.name "test")
  cat > "$REPO/docs/sdlc/active/test/beads/b1.md" <<'BEAD'
# Bead: b1

**Status:** verified

## Description
Test bead in verified state.
BEAD
  (cd "$REPO" && git add -A && git commit -q -m "initial bead")

  # Test 1: illegal verified->merged with physical path (should block)
  local PHYSICAL_ROOT
  PHYSICAL_ROOT=$(cd "$REPO" && pwd -P)
  local FIXTURE_BLOCK
  FIXTURE_BLOCK=$(cat <<JSON
{
  "session_id": "test",
  "hook_event_name": "PostToolUse",
  "tool_name": "Write",
  "tool_input": {
    "file_path": "${PHYSICAL_ROOT}/docs/sdlc/active/test/beads/b1.md",
    "content": "# Bead: b1\n\n**Status:** merged\n\n## Description\n\nAttempting illegal verified->merged.\n"
  }
}
JSON
  )

  local exit_code=0
  echo "$FIXTURE_BLOCK" | (cd "$REPO" && bash "$HOOKS_DIR/guard-bead-status.sh") > /dev/null 2>&1 || exit_code=$?
  if [[ "$exit_code" -eq 2 ]]; then
    echo "  PASS: BLOCK: verified->merged via physical path (exit $exit_code)"
    PASS=$((PASS + 1))
  else
    echo "  FAIL: BLOCK: verified->merged via physical path (expected exit 2, got $exit_code)"
    FAIL=$((FAIL + 1))
  fi

  # Test 2: On macOS, /var is a symlink to /private/var.
  # Create a symlink to the repo and test with the symlinked path.
  local SYMLINK_DIR="$TMPDIR_BASE/symlink_root"
  mkdir -p "$SYMLINK_DIR"
  ln -s "$PHYSICAL_ROOT" "$SYMLINK_DIR/repo"
  local SYMLINKED_ROOT="$SYMLINK_DIR/repo"

  local FIXTURE_SYMLINK
  FIXTURE_SYMLINK=$(cat <<JSON
{
  "session_id": "test",
  "hook_event_name": "PostToolUse",
  "tool_name": "Write",
  "tool_input": {
    "file_path": "${SYMLINKED_ROOT}/docs/sdlc/active/test/beads/b1.md",
    "content": "# Bead: b1\n\n**Status:** merged\n\n## Description\n\nAttempting illegal verified->merged via symlink.\n"
  }
}
JSON
  )

  exit_code=0
  echo "$FIXTURE_SYMLINK" | (cd "$REPO" && bash "$HOOKS_DIR/guard-bead-status.sh") > /dev/null 2>&1 || exit_code=$?
  if [[ "$exit_code" -eq 2 ]]; then
    echo "  PASS: BLOCK: verified->merged via symlinked path (exit $exit_code)"
    PASS=$((PASS + 1))
  else
    echo "  FAIL: BLOCK: verified->merged via symlinked path (expected exit 2, got $exit_code)"
    FAIL=$((FAIL + 1))
  fi

  # Test 3: valid transition proven->merged should still pass
  (cd "$REPO" && git checkout -q -- docs/sdlc/active/test/beads/b1.md)
  # Update bead to proven and commit
  cat > "$REPO/docs/sdlc/active/test/beads/b1.md" <<'BEAD'
# Bead: b1

**Status:** proven

## Description
Test bead advanced to proven.
BEAD
  (cd "$REPO" && git add -A && git commit -q -m "advance to proven")

  local FIXTURE_VALID
  FIXTURE_VALID=$(cat <<JSON
{
  "session_id": "test",
  "hook_event_name": "PostToolUse",
  "tool_name": "Write",
  "tool_input": {
    "file_path": "${SYMLINKED_ROOT}/docs/sdlc/active/test/beads/b1.md",
    "content": "# Bead: b1\n\n**Status:** merged\n\n## Description\n\nValid proven->merged via symlink.\n"
  }
}
JSON
  )

  exit_code=0
  echo "$FIXTURE_VALID" | (cd "$REPO" && bash "$HOOKS_DIR/guard-bead-status.sh") > /dev/null 2>&1 || exit_code=$?
  if [[ "$exit_code" -eq 0 ]]; then
    echo "  PASS: valid: proven->merged via symlinked path (exit $exit_code)"
    PASS=$((PASS + 1))
  else
    echo "  FAIL: valid: proven->merged via symlinked path (expected exit 0, got $exit_code)"
    FAIL=$((FAIL + 1))
  fi
}

run_integration_guard_test

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
