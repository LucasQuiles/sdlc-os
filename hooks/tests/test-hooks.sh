#!/bin/bash
# Hook Regression Test Suite
# Run: bash hooks/tests/test-hooks.sh
# Tests all three hooks with fixture inputs and expected exit codes.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOKS_DIR="$(cd "$SCRIPT_DIR/../scripts" && pwd)"
HOOK_LIB="$(cd "$SCRIPT_DIR/../lib" && pwd)/common.sh"
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

run_test_advisory() {
  local test_name="$1"
  local hook_script="$2"
  local fixture_file="$3"
  local expect_warning="$4"  # "yes" or "no"

  local actual_exit=0
  local stderr_output
  stderr_output=$(cat "$fixture_file" | bash "$hook_script" 2>&1 1>/dev/null) || actual_exit=$?

  if [[ "$actual_exit" -ne 0 ]]; then
    echo "  FAIL: $test_name (advisory hook exited $actual_exit, must be 0)"
    FAIL=$((FAIL + 1))
    return
  fi

  if [[ "$expect_warning" == "yes" ]]; then
    if echo "$stderr_output" | grep -q "HOOK_WARNING:"; then
      echo "  PASS: $test_name (exit 0, warning emitted)"
      PASS=$((PASS + 1))
    else
      echo "  FAIL: $test_name (exit 0, but expected HOOK_WARNING not found)"
      FAIL=$((FAIL + 1))
    fi
  else
    if echo "$stderr_output" | grep -q "HOOK_WARNING:"; then
      echo "  FAIL: $test_name (exit 0, but unexpected HOOK_WARNING: $stderr_output)"
      FAIL=$((FAIL + 1))
    else
      echo "  PASS: $test_name (exit 0, no warning)"
      PASS=$((PASS + 1))
    fi
  fi
}

run_hook_input_helper_regression_test() {
  local tmpdir path_dir helper_script output exit_code=0
  tmpdir=$(mktemp -d)
  path_dir=$(mktemp -d)
  helper_script="$tmpdir/probe-hook-stdin.sh"
  trap "rm -rf '$tmpdir' '$path_dir'" RETURN

  cat > "$helper_script" <<EOF
#!/bin/bash
set -euo pipefail
source "$HOOK_LIB"
load_hook_input_or_exit INPUT || exit 0
printf '%s' "\$INPUT"
EOF
  chmod +x "$helper_script"
  ln -s "$(command -v perl)" "$path_dir/perl"

  output=$(printf '{"tool_name":"Write"}' | PATH="$path_dir" /bin/bash "$helper_script" 2>&1) || exit_code=$?
  if [[ "$exit_code" -eq 0 ]] && [[ "$output" == '{"tool_name":"Write"}' ]]; then
    echo "  PASS: helper reads stdin without timeout on PATH"
    PASS=$((PASS + 1))
  else
    echo "  FAIL: helper reads stdin without timeout on PATH (exit $exit_code, output: $output)"
    FAIL=$((FAIL + 1))
  fi
}

echo "=== Hook Stdin Compatibility Tests ==="

run_hook_input_helper_regression_test

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
  (cd "$REPO" && git add -A && git commit -q --no-verify -m "initial bead")

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
  (cd "$REPO" && git add -A && git commit -q --no-verify -m "advance to proven")

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
echo "=== Naming Convention Hook Tests (advisory) ==="

# Naming tests need a Convention Map in a git repo to produce warnings.
# Tests without a map correctly produce no warnings (by design).
run_test_advisory "skip: no convention map (no warning)" \
  "$HOOKS_DIR/check-naming-convention.sh" \
  "$FIXTURES_DIR/naming-violation-create.json" "no"

run_test_advisory "skip: vendor path (node_modules)" \
  "$HOOKS_DIR/check-naming-convention.sh" \
  "$FIXTURES_DIR/naming-vendor-skip.json" "no"

# Integration test: create a repo with a Convention Map and test naming enforcement
run_naming_integration_test() {
  local TMPDIR_BASE
  TMPDIR_BASE=$(mktemp -d)
  trap "rm -rf '$TMPDIR_BASE'" RETURN

  local REPO="$TMPDIR_BASE/repo"
  mkdir -p "$REPO/lib/storage" "$REPO/docs/sdlc"

  (cd "$REPO" && git init -q && git config user.email "test@test" && git config user.name "test")

  # Create a Convention Map with lib/storage/ -> kebab-case
  cat > "$REPO/docs/sdlc/convention-map.md" <<'MAP'
# Convention Map

## Scanned Dimensions

### File Naming
- **Convention:** kebab-case
- **Scope:** lib/storage/, lib/utils/
- **Confidence:** Verified 5/5
MAP
  (cd "$REPO" && git add -A && git commit -q --no-verify -m "add convention map")

  # Test: valid kebab-case file in mapped dir — no warning
  local FIXTURE_VALID
  FIXTURE_VALID=$(cat <<JSON
{
  "session_id": "test",
  "hook_event_name": "PreToolUse",
  "tool_name": "Write",
  "tool_input": {
    "file_path": "${REPO}/lib/storage/payments-storage.ts",
    "content": "export function getPayments() { return []; }"
  }
}
JSON
  )

  local exit_code=0
  local stderr_output
  stderr_output=$(echo "$FIXTURE_VALID" | (cd "$REPO" && bash "$HOOKS_DIR/check-naming-convention.sh") 2>&1 1>/dev/null) || exit_code=$?
  if [[ "$exit_code" -eq 0 ]] && ! echo "$stderr_output" | grep -q "HOOK_WARNING:"; then
    echo "  PASS: valid: kebab-case in mapped dir (exit 0, no warning)"
    PASS=$((PASS + 1))
  else
    echo "  FAIL: valid: kebab-case in mapped dir (exit $exit_code, stderr: $stderr_output)"
    FAIL=$((FAIL + 1))
  fi

  # Test: camelCase violation in mapped dir — should warn
  local FIXTURE_VIOLATION
  FIXTURE_VIOLATION=$(cat <<JSON
{
  "session_id": "test",
  "hook_event_name": "PreToolUse",
  "tool_name": "Write",
  "tool_input": {
    "file_path": "${REPO}/lib/storage/userPayments.ts",
    "content": "export function getPayments() { return []; }"
  }
}
JSON
  )

  exit_code=0
  stderr_output=$(echo "$FIXTURE_VIOLATION" | (cd "$REPO" && bash "$HOOKS_DIR/check-naming-convention.sh") 2>&1 1>/dev/null) || exit_code=$?
  if [[ "$exit_code" -eq 0 ]] && echo "$stderr_output" | grep -q "HOOK_WARNING:.*naming violation"; then
    echo "  PASS: warning: camelCase in kebab-case dir (exit 0, warning emitted)"
    PASS=$((PASS + 1))
  else
    echo "  FAIL: warning: camelCase in kebab-case dir (exit $exit_code, stderr: $stderr_output)"
    FAIL=$((FAIL + 1))
  fi
}

run_naming_integration_test

echo ""
echo "=== Consistency Artifact Validation Tests (advisory) ==="

run_test_advisory "valid: feature matrix with correct row" \
  "$HOOKS_DIR/validate-consistency-artifacts.sh" \
  "$FIXTURES_DIR/artifact-valid-matrix.json" "no"

run_test_advisory "warning: feature matrix with invalid ID/severity/status" \
  "$HOOKS_DIR/validate-consistency-artifacts.sh" \
  "$FIXTURES_DIR/artifact-invalid-matrix.json" "yes"

run_test_advisory "valid: convention report with required sections" \
  "$HOOKS_DIR/validate-consistency-artifacts.sh" \
  "$FIXTURES_DIR/artifact-valid-convention-report.json" "no"

run_test_advisory "warning: convention report missing sections" \
  "$HOOKS_DIR/validate-consistency-artifacts.sh" \
  "$FIXTURES_DIR/artifact-invalid-convention-report.json" "yes"

echo ""
echo "=== Runner Output Validation Tests (advisory) ==="

run_test_advisory "valid: runner output with all sections" \
  "$HOOKS_DIR/validate-runner-output.sh" \
  "$FIXTURES_DIR/runner-output-valid.json" "no"

run_test_advisory "warning: runner output missing sections" \
  "$HOOKS_DIR/validate-runner-output.sh" \
  "$FIXTURES_DIR/runner-output-missing-sections.json" "yes"

run_test_advisory "warning: runner output with convention signal" \
  "$HOOKS_DIR/validate-runner-output.sh" \
  "$FIXTURES_DIR/runner-output-convention-signal.json" "yes"

echo ""
echo "=== Safety Constraints Tests (advisory) ==="

_sc_tmp=$(mktemp -d)
cat > "$_sc_tmp/comment-only-catch.json" <<'JSON'
{
  "tool_name": "Write",
  "tool_input": {
    "file_path": "/tmp/example.js",
    "content": "try { work(); } catch (err) { /* intentional noop */ }"
  }
}
JSON

_sc_exit=0
_sc_stderr=$(cat "$_sc_tmp/comment-only-catch.json" | bash "$HOOKS_DIR/validate-safety-constraints.sh" 2>&1 1>/dev/null) || _sc_exit=$?
if [[ "$_sc_exit" -eq 0 ]] && echo "$_sc_stderr" | grep -q "SC-004"; then
  echo "  PASS: warning: comment-only catch block (exit 0, advisory emitted)"
  PASS=$((PASS + 1))
else
  echo "  FAIL: warning: comment-only catch block (exit $_sc_exit, stderr: $_sc_stderr)"
  FAIL=$((FAIL + 1))
fi

rm -rf "$_sc_tmp"

echo ""
echo "=== eslint-disable Justification Tests ==="

# Setup: create test source file for Edit-tier test
mkdir -p /tmp/test-project/lib/storage
echo '// eslint-disable-next-line no-raw-soft-delete
const old = true;' > /tmp/test-project/lib/storage/access-requests.ts

run_test "BLOCK: bare eslint-disable (no justification)" \
  "$HOOKS_DIR/check-eslint-disable-justification.sh" \
  "$FIXTURES_DIR/justification-bare-suppression.json" 2

run_test "valid: structured justification with tracking ID" \
  "$HOOKS_DIR/check-eslint-disable-justification.sh" \
  "$FIXTURES_DIR/justification-structured-valid.json" 0

run_test "valid: weak justification (score 1, not blocked)" \
  "$HOOKS_DIR/check-eslint-disable-justification.sh" \
  "$FIXTURES_DIR/justification-weak-reason.json" 0

run_test "valid: non-source file (skip)" \
  "$HOOKS_DIR/check-eslint-disable-justification.sh" \
  "$FIXTURES_DIR/justification-non-source-file.json" 0

run_test "BLOCK: Edit-tier bare suppression (no allowlist)" \
  "$HOOKS_DIR/check-eslint-disable-justification.sh" \
  "$FIXTURES_DIR/justification-edit-bare-no-allowlist.json" 2

# Setup: create allowlist with matching fingerprint for the bare suppression fixture.
# (1) init git repo so get_repo_root() works, (2) compute fingerprint by running
# the same hashing logic the hook uses on the actual fixture content.
cd /tmp/test-project && git init -q && cd - > /dev/null
ALLOWLIST_DIR="/tmp/test-project/docs/sdlc/active/test-task"
mkdir -p "$ALLOWLIST_DIR"
# Compute fingerprint from fixture content using the exact same method as the hook:
# parse JSON content, grep for eslint-disable, extract context lines via sed -n, hash with echo.
FIXTURE_CONTENT=$(cat "$FIXTURES_DIR/justification-allowlisted-bare.json" | jq -r '.tool_input.content')
FIXTURE_FILE_PATH=$(cat "$FIXTURES_DIR/justification-allowlisted-bare.json" | jq -r '.tool_input.file_path')
FIXTURE_LINE=$(echo "$FIXTURE_CONTENT" | grep -n "eslint-disable" | head -1)
FIXTURE_LINE_NUM=$(echo "$FIXTURE_LINE" | cut -d: -f1)
FIXTURE_LINE_CONTENT=$(echo "$FIXTURE_LINE" | cut -d: -f2-)
FIXTURE_NORMALIZED=$(echo "$FIXTURE_LINE_CONTENT" | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//')
FIXTURE_CTX_START=$((FIXTURE_LINE_NUM > 1 ? FIXTURE_LINE_NUM - 1 : 1))
FIXTURE_CTX_END=$((FIXTURE_LINE_NUM + 1))
FIXTURE_CTX_LINES=$(echo "$FIXTURE_CONTENT" | sed -n "${FIXTURE_CTX_START},${FIXTURE_CTX_END}p")
FIXTURE_CTX_HASH=$(echo "$FIXTURE_CTX_LINES" | shasum -a 256 | cut -d' ' -f1)
FINGERPRINT=$(echo "${FIXTURE_FILE_PATH}${FIXTURE_NORMALIZED}${FIXTURE_CTX_HASH}" | shasum -a 256 | cut -d' ' -f1)
echo "- fingerprint: $FINGERPRINT | file: $FIXTURE_FILE_PATH | rule: no-raw-soft-delete" > "$ALLOWLIST_DIR/suppression-allowlist.md"
export SDLC_TASK_ID="test-task"
# cd to the test project so get_repo_root() resolves to /tmp/test-project
SAVED_DIR="$(pwd)"
cd /tmp/test-project

run_test "valid: allowlisted bare suppression (fingerprint match)" \
  "$HOOKS_DIR/check-eslint-disable-justification.sh" \
  "$FIXTURES_DIR/justification-allowlisted-bare.json" 0

# Cleanup
cd "$SAVED_DIR"
unset SDLC_TASK_ID
rm -rf /tmp/test-project

echo ""
echo "=== Quality Budget Validation Tests ==="

# Generate temp fixture files with inline JSON pointing at real YAML fixture paths.
# We write to temp files and use run_test (not a pipe) so PASS/FAIL counters
# update in the current shell — piping into a function runs a subshell.
_qb_tmp=$(mktemp -d)
_qb_json() { echo "{\"tool_name\":\"Write\",\"tool_input\":{\"file_path\":\"$1\"}}" > "$2"; }

_qb_json "$FIXTURES_DIR/qb-valid/quality-budget.yaml" "$_qb_tmp/qb-valid.json"
_qb_json "$FIXTURES_DIR/qb-missing/quality-budget.yaml" "$_qb_tmp/qb-missing.json"
_qb_json "$FIXTURES_DIR/qb-malformed/quality-budget.yaml" "$_qb_tmp/qb-malformed.json"
_qb_json "/tmp/not-quality-budget.txt" "$_qb_tmp/qb-non-budget.json"

run_test "valid: complete quality-budget.yaml passes" \
  "$HOOKS_DIR/validate-quality-budget.sh" "$_qb_tmp/qb-valid.json" 0

run_test "reject: missing required fields" \
  "$HOOKS_DIR/validate-quality-budget.sh" "$_qb_tmp/qb-missing.json" 2

run_test "reject: malformed YAML" \
  "$HOOKS_DIR/validate-quality-budget.sh" "$_qb_tmp/qb-malformed.json" 2

run_test "skip: non-budget file ignored" \
  "$HOOKS_DIR/validate-quality-budget.sh" "$_qb_tmp/qb-non-budget.json" 0

rm -rf "$_qb_tmp"

echo ""
echo "=== Hazard-Defense Ledger Validation Tests ==="

# Generate temp fixture files with inline JSON pointing at real YAML fixture paths.
# We write to temp files and use run_test (not a pipe) so PASS/FAIL counters
# update in the current shell — piping into a function runs a subshell.
_hdl_tmp=$(mktemp -d)
_hdl_json() { echo "{\"tool_name\":\"Write\",\"tool_input\":{\"file_path\":\"$1\"}}" > "$2"; }

_hdl_json "$FIXTURES_DIR/hdl-valid/hazard-defense-ledger.yaml" "$_hdl_tmp/hdl-valid.json"
_hdl_json "$FIXTURES_DIR/hdl-missing/hazard-defense-ledger.yaml" "$_hdl_tmp/hdl-missing.json"
_hdl_json "$FIXTURES_DIR/hdl-malformed/hazard-defense-ledger.yaml" "$_hdl_tmp/hdl-malformed.json"
_hdl_json "/tmp/not-hazard-defense-ledger.txt" "$_hdl_tmp/hdl-non-ledger.json"

run_test "valid: complete hazard-defense-ledger.yaml passes" \
  "$HOOKS_DIR/validate-hazard-defense-ledger.sh" "$_hdl_tmp/hdl-valid.json" 0

run_test "reject: missing required fields" \
  "$HOOKS_DIR/validate-hazard-defense-ledger.sh" "$_hdl_tmp/hdl-missing.json" 2

run_test "reject: malformed YAML" \
  "$HOOKS_DIR/validate-hazard-defense-ledger.sh" "$_hdl_tmp/hdl-malformed.json" 2

run_test "skip: non-ledger file ignored" \
  "$HOOKS_DIR/validate-hazard-defense-ledger.sh" "$_hdl_tmp/hdl-non-ledger.json" 0

rm -rf "$_hdl_tmp"

echo ""
echo "=== Stress Session Validation Tests ==="

# Generate temp fixture files with inline JSON pointing at real YAML fixture paths.
# We write to temp files and use run_test (not a pipe) so PASS/FAIL counters
# update in the current shell — piping into a function runs a subshell.
_ss_tmp=$(mktemp -d)
_ss_json() { echo "{\"tool_name\":\"Write\",\"tool_input\":{\"file_path\":\"$1\"}}" > "$2"; }

_ss_json "$FIXTURES_DIR/stress-valid/stress-session.yaml" "$_ss_tmp/ss-valid.json"
_ss_json "$FIXTURES_DIR/stress-missing/stress-session.yaml" "$_ss_tmp/ss-missing.json"
_ss_json "$FIXTURES_DIR/stress-malformed/stress-session.yaml" "$_ss_tmp/ss-malformed.json"
_ss_json "/tmp/not-stress-session.txt" "$_ss_tmp/ss-non-session.json"

run_test "valid: complete stress-session.yaml passes" \
  "$HOOKS_DIR/validate-stress-session.sh" "$_ss_tmp/ss-valid.json" 0

run_test "reject: missing required fields" \
  "$HOOKS_DIR/validate-stress-session.sh" "$_ss_tmp/ss-missing.json" 2

run_test "reject: malformed YAML" \
  "$HOOKS_DIR/validate-stress-session.sh" "$_ss_tmp/ss-malformed.json" 2

run_test "skip: non-session file ignored" \
  "$HOOKS_DIR/validate-stress-session.sh" "$_ss_tmp/ss-non-session.json" 0

rm -rf "$_ss_tmp"

echo ""
echo "=== Decision-Noise Summary Validation Tests ==="

# Generate temp fixture files with inline JSON pointing at real YAML fixture paths.
# We write to temp files and use run_test (not a pipe) so PASS/FAIL counters
# update in the current shell — piping into a function runs a subshell.
_dn_tmp=$(mktemp -d)
_dn_json() { echo "{\"tool_name\":\"Write\",\"tool_input\":{\"file_path\":\"$1\"}}" > "$2"; }

_dn_json "$FIXTURES_DIR/dn-valid/decision-noise-summary.yaml" "$_dn_tmp/dn-valid.json"
_dn_json "$FIXTURES_DIR/dn-missing/decision-noise-summary.yaml" "$_dn_tmp/dn-missing.json"
_dn_json "$FIXTURES_DIR/dn-malformed/decision-noise-summary.yaml" "$_dn_tmp/dn-malformed.json"
_dn_json "/tmp/not-decision-noise-summary.txt" "$_dn_tmp/dn-non-summary.json"

run_test "valid: complete decision-noise-summary.yaml passes" \
  "$HOOKS_DIR/validate-decision-noise-summary.sh" "$_dn_tmp/dn-valid.json" 0

run_test "reject: missing required fields" \
  "$HOOKS_DIR/validate-decision-noise-summary.sh" "$_dn_tmp/dn-missing.json" 2

run_test "reject: malformed YAML" \
  "$HOOKS_DIR/validate-decision-noise-summary.sh" "$_dn_tmp/dn-malformed.json" 2

run_test "skip: non-summary file ignored" \
  "$HOOKS_DIR/validate-decision-noise-summary.sh" "$_dn_tmp/dn-non-summary.json" 0

rm -rf "$_dn_tmp"

echo ""
echo "=== Mode-Convergence Summary Validation Tests ==="

# Generate temp fixture files with inline JSON pointing at real YAML fixture paths.
# We write to temp files and use run_test (not a pipe) so PASS/FAIL counters
# update in the current shell — piping into a function runs a subshell.
_mc_tmp=$(mktemp -d)
_mc_json() { echo "{\"tool_name\":\"Write\",\"tool_input\":{\"file_path\":\"$1\"}}" > "$2"; }

_mc_json "$FIXTURES_DIR/mc-valid/mode-convergence-summary.yaml" "$_mc_tmp/mc-valid.json"
_mc_json "$FIXTURES_DIR/mc-missing/mode-convergence-summary.yaml" "$_mc_tmp/mc-missing.json"
_mc_json "$FIXTURES_DIR/mc-malformed/mode-convergence-summary.yaml" "$_mc_tmp/mc-malformed.json"
_mc_json "/tmp/not-mode-convergence-summary.txt" "$_mc_tmp/mc-non-summary.json"

run_test "valid: complete mode-convergence-summary.yaml passes" \
  "$HOOKS_DIR/validate-mode-convergence-summary.sh" "$_mc_tmp/mc-valid.json" 0

run_test "reject: missing required fields" \
  "$HOOKS_DIR/validate-mode-convergence-summary.sh" "$_mc_tmp/mc-missing.json" 2

run_test "reject: malformed YAML" \
  "$HOOKS_DIR/validate-mode-convergence-summary.sh" "$_mc_tmp/mc-malformed.json" 2

run_test "skip: non-summary file ignored" \
  "$HOOKS_DIR/validate-mode-convergence-summary.sh" "$_mc_tmp/mc-non-summary.json" 0

rm -rf "$_mc_tmp"

echo ""
echo "=== Phase-Transition Warning Tests ==="

_pt_tmp=$(mktemp -d)
mkdir -p "$_pt_tmp/beads"

# Add a bead file so HAS_BEADS=true — gates will fail without artifacts
cat > "$_pt_tmp/beads/B01.md" << 'BEAD'
**Status:** merged
**Cynefin domain:** complicated
BEAD

# Helper to create JSON fixture pointing at a real file
_pt_json() { echo "{\"tool_name\":\"Write\",\"tool_input\":{\"file_path\":\"$1\"}}" > "$2"; }

# 1. complete transition with no artifacts → advisory warning
cat > "$_pt_tmp/state.md" << 'YAML'
---
task-id: test-gate-task
current-phase: complete
---
YAML
_pt_json "$_pt_tmp/state.md" "$_pt_tmp/pt-complete.json"
run_test_advisory "warn: complete without artifacts" "$HOOKS_DIR/warn-phase-transition.sh" "$_pt_tmp/pt-complete.json" "yes"

# 2. synthesize transition → also advisory warning
cat > "$_pt_tmp/state.md" << 'YAML'
---
task-id: test-gate-task
current-phase: synthesize
---
YAML
_pt_json "$_pt_tmp/state.md" "$_pt_tmp/pt-synthesize.json"
run_test_advisory "warn: synthesize without artifacts" "$HOOKS_DIR/warn-phase-transition.sh" "$_pt_tmp/pt-synthesize.json" "yes"

# 3. execute transition → no warning
cat > "$_pt_tmp/state.md" << 'YAML'
---
task-id: test-gate-task
current-phase: execute
---
YAML
_pt_json "$_pt_tmp/state.md" "$_pt_tmp/pt-execute.json"
run_test_advisory "skip: execute phase (no warning)" "$HOOKS_DIR/warn-phase-transition.sh" "$_pt_tmp/pt-execute.json" "no"

# 4. non-state file → skip
_pt_json "/tmp/not-state.txt" "$_pt_tmp/pt-nonstate.json"
run_test "skip: non-state file" "$HOOKS_DIR/warn-phase-transition.sh" "$_pt_tmp/pt-nonstate.json" 0

rm -rf "$_pt_tmp"

echo ""
echo "=== AST Checks Hook Suite ==="
# Run the standalone ast-checks.sh test matrix as a sub-suite and roll its
# PASS/FAIL counts into the main totals. The sub-suite uses its own scratch
# env (temp ast-checks.sh copy, synthetic PATHs) so it is safe to invoke here.

AST_SUITE="$SCRIPT_DIR/test-ast-checks.sh"
if [[ ! -f "$AST_SUITE" ]]; then
  echo "  FAIL: test-ast-checks.sh missing at $AST_SUITE"
  FAIL=$((FAIL + 1))
else
  # Capture output, surface per-test lines, extract PASS/FAIL counts from summary.
  AST_OUTPUT=$(bash "$AST_SUITE" 2>&1) || true
  # Forward each PASS:/FAIL: line so granularity is visible in aggregated output
  echo "$AST_OUTPUT" | grep -E '^\s*(PASS|FAIL):' || true

  AST_PASS=$(echo "$AST_OUTPUT" | sed -n 's/.*PASS: \([0-9]*\).*FAIL:.*/\1/p' | tail -1)
  AST_FAIL=$(echo "$AST_OUTPUT" | sed -n 's/.*PASS: [0-9]*  FAIL: \([0-9]*\).*/\1/p' | tail -1)

  if [[ -z "$AST_PASS" || -z "$AST_FAIL" ]]; then
    echo "  FAIL: could not parse test-ast-checks.sh summary"
    FAIL=$((FAIL + 1))
  else
    PASS=$((PASS + AST_PASS))
    FAIL=$((FAIL + AST_FAIL))
  fi
fi

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
