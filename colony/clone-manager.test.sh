#!/bin/bash
# clone-manager.test.sh — Tests for clone-manager.sh
# Creates temporary git repos, exercises all 5 functions, verifies behavior.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/clone-manager.sh"

# Use a unique test-scoped COLONY_BASE to avoid interfering with real data
TEST_BASE="/tmp/sdlc-colony-test-$$"
export COLONY_BASE="${TEST_BASE}"

PASS=0
FAIL=0

pass() { echo "  PASS: $1"; PASS=$((PASS + 1)); }
fail() { echo "  FAIL: $1"; FAIL=$((FAIL + 1)); }

cleanup() {
  rm -rf "${TEST_BASE}" "${SOURCE_REPO:-}" 2>/dev/null || true
}
trap cleanup EXIT

# --- Setup: create a source git repo ---
SOURCE_REPO="$(mktemp -d)"
git -C "${SOURCE_REPO}" init -b main >/dev/null 2>&1
git -C "${SOURCE_REPO}" config user.email "test@test.com"
git -C "${SOURCE_REPO}" config user.name "Test"
echo "initial" > "${SOURCE_REPO}/README.md"
git -C "${SOURCE_REPO}" add README.md
git -C "${SOURCE_REPO}" commit -m "initial commit" >/dev/null 2>&1

echo "=== Test: colony_clone_create ==="

# T1: Clone is created with .git directory
CLONE_DIR="$(colony_clone_create "${SOURCE_REPO}" "test-session" "agent-1")"
if [[ -d "${CLONE_DIR}/.git" ]]; then
  pass "clone created with .git directory"
else
  fail "clone missing .git directory"
fi

# T2: Clone path is under COLONY_BASE
if [[ "${CLONE_DIR}" == "${TEST_BASE}"/* ]]; then
  pass "clone path under COLONY_BASE"
else
  fail "clone path not under COLONY_BASE: ${CLONE_DIR}"
fi

# T3: Push URL is set to no-push (SC-COL-27)
PUSH_URL="$(git -C "${CLONE_DIR}" remote get-url --push origin)"
if [[ "${PUSH_URL}" == "no-push" ]]; then
  pass "push URL set to no-push"
else
  fail "push URL is '${PUSH_URL}', expected 'no-push'"
fi

echo ""
echo "=== Test: colony_clone_verify ==="

# T4: Valid clone passes verification
if colony_clone_verify "${CLONE_DIR}" >/dev/null 2>&1; then
  pass "valid clone passes verify"
else
  fail "valid clone rejected by verify"
fi

# T5: Directory outside COLONY_BASE fails verification
OUTSIDE_DIR="$(mktemp -d)"
git -C "${OUTSIDE_DIR}" init -b main >/dev/null 2>&1
if colony_clone_verify "${OUTSIDE_DIR}" >/dev/null 2>&1; then
  fail "directory outside COLONY_BASE passed verify"
else
  pass "directory outside COLONY_BASE rejected by verify"
fi
rm -rf "${OUTSIDE_DIR}"

# T6: Directory without .git fails verification
NO_GIT_DIR="${TEST_BASE}/test-session/no-git-dir"
mkdir -p "${NO_GIT_DIR}"
if colony_clone_verify "${NO_GIT_DIR}" >/dev/null 2>&1; then
  fail "directory without .git passed verify"
else
  pass "directory without .git rejected by verify"
fi
rm -rf "${NO_GIT_DIR}"

echo ""
echo "=== Test: colony_clone_has_commits ==="

# T7: Clone with no worker commits returns false
if colony_clone_has_commits "${CLONE_DIR}" 2>/dev/null; then
  fail "clone with no worker commits reported as having commits"
else
  pass "clone with no worker commits correctly returns false"
fi

# T8: Clone with worker commit returns true
echo "worker change" > "${CLONE_DIR}/worker-file.txt"
git -C "${CLONE_DIR}" add worker-file.txt
git -C "${CLONE_DIR}" config user.email "worker@test.com"
git -C "${CLONE_DIR}" config user.name "Worker"
git -C "${CLONE_DIR}" commit -m "worker commit" >/dev/null 2>&1
if colony_clone_has_commits "${CLONE_DIR}" 2>/dev/null; then
  pass "clone with worker commit detected"
else
  fail "clone with worker commit not detected"
fi

echo ""
echo "=== Test: colony_clone_prune ==="

# T9: Prune refuses when bridge_synced != 1 (SC-COL-21)
PRUNE_CLONE="$(colony_clone_create "${SOURCE_REPO}" "test-session" "agent-prune")"
if colony_clone_prune "${PRUNE_CLONE}" "0" >/dev/null 2>&1; then
  fail "prune succeeded with bridge_synced=0"
else
  pass "prune refused with bridge_synced=0"
fi

# T10: Verify clone still exists after refused prune
if [[ -d "${PRUNE_CLONE}/.git" ]]; then
  pass "clone still exists after refused prune"
else
  fail "clone was deleted despite refused prune"
fi

# T11: Prune succeeds when bridge_synced == 1
if colony_clone_prune "${PRUNE_CLONE}" "1" >/dev/null 2>&1; then
  pass "prune succeeded with bridge_synced=1"
else
  fail "prune failed with bridge_synced=1"
fi

# T12: Clone directory is actually removed
if [[ ! -d "${PRUNE_CLONE}" ]]; then
  pass "clone directory removed after prune"
else
  fail "clone directory still exists after prune"
fi

echo ""
echo "=== Test: colony_clone_recover_output ==="

# T13: Recover copies bead-output.md and correction.json
RECOVER_CLONE="$(colony_clone_create "${SOURCE_REPO}" "test-session" "agent-recover")"
echo "# Bead Output" > "${RECOVER_CLONE}/bead-output.md"
echo '{"what_failed": "test"}' > "${RECOVER_CLONE}/correction.json"

TASK_ID="task-recover-001"
if colony_clone_recover_output "${RECOVER_CLONE}" "${TASK_ID}" >/dev/null 2>&1; then
  pass "recover_output succeeded"
else
  fail "recover_output failed"
fi

RECOVER_DIR="${TEST_BASE}/recovered-outputs/${TASK_ID}"
if [[ -f "${RECOVER_DIR}/bead-output.md" ]]; then
  pass "bead-output.md copied to recovery dir"
else
  fail "bead-output.md not found in recovery dir"
fi

if [[ -f "${RECOVER_DIR}/correction.json" ]]; then
  pass "correction.json copied to recovery dir"
else
  fail "correction.json not found in recovery dir"
fi

# T14: Recover fails when no output files exist
EMPTY_CLONE="$(colony_clone_create "${SOURCE_REPO}" "test-session" "agent-empty")"
if colony_clone_recover_output "${EMPTY_CLONE}" "task-empty-001" >/dev/null 2>&1; then
  fail "recover_output succeeded with no output files"
else
  pass "recover_output correctly failed with no output files"
fi

echo ""
echo "=== Test: structured logging ==="

LOG_FILE="${TEST_BASE}/clone-events.log"

# T17: clone-events.log exists after colony_clone_create
if [[ -f "${LOG_FILE}" ]]; then
  pass "clone-events.log created after colony_clone_create"
else
  fail "clone-events.log not found"
fi

# T18: All log entries are valid JSON
INVALID_JSON=0
while IFS= read -r line; do
  if ! echo "${line}" | python3 -m json.tool >/dev/null 2>&1; then
    INVALID_JSON=1
    break
  fi
done < "${LOG_FILE}"
if [[ "${INVALID_JSON}" -eq 0 ]]; then
  pass "all log entries are valid JSON"
else
  fail "found invalid JSON in clone-events.log"
fi

# T19: elapsed_ms > 0 in clone_created entry
CREATE_ELAPSED=$(python3 -c "
import json, sys
for line in open('${LOG_FILE}'):
    obj = json.loads(line)
    if obj.get('event') == 'clone_created':
        print(obj.get('elapsed_ms', -1))
        break
")
if [[ "${CREATE_ELAPSED}" -gt 0 ]]; then
  pass "elapsed_ms > 0 in clone_created entry"
else
  fail "elapsed_ms not > 0 in clone_created entry (got ${CREATE_ELAPSED})"
fi

# T20: clone_bytes > 0 in clone_created entry
CREATE_BYTES=$(python3 -c "
import json, sys
for line in open('${LOG_FILE}'):
    obj = json.loads(line)
    if obj.get('event') == 'clone_created':
        print(obj.get('clone_bytes', -1))
        break
")
if [[ "${CREATE_BYTES}" -gt 0 ]]; then
  pass "clone_bytes > 0 in clone_created entry"
else
  fail "clone_bytes not > 0 (got ${CREATE_BYTES})"
fi

# T21: clone_verified events present with valid field
VERIFIED_COUNT=$(python3 -c "
import json
count = 0
for line in open('${LOG_FILE}'):
    obj = json.loads(line)
    if obj.get('event') == 'clone_verified' and 'valid' in obj:
        count += 1
print(count)
")
if [[ "${VERIFIED_COUNT}" -ge 1 ]]; then
  pass "clone_verified events logged with valid field"
else
  fail "no clone_verified events found"
fi

# T22: clone_commit_check events present with commit_count
COMMIT_CHECK=$(python3 -c "
import json
for line in open('${LOG_FILE}'):
    obj = json.loads(line)
    if obj.get('event') == 'clone_commit_check' and 'commit_count' in obj:
        print('found')
        break
else:
    print('missing')
")
if [[ "${COMMIT_CHECK}" == "found" ]]; then
  pass "clone_commit_check event logged with commit_count"
else
  fail "clone_commit_check event not found"
fi

# T23: clone_pruned event present with elapsed_ms
PRUNED_ELAPSED=$(python3 -c "
import json
for line in open('${LOG_FILE}'):
    obj = json.loads(line)
    if obj.get('event') == 'clone_pruned' and 'elapsed_ms' in obj:
        print(obj['elapsed_ms'])
        break
else:
    print(-1)
")
if [[ "${PRUNED_ELAPSED}" -ge 0 ]]; then
  pass "clone_pruned event logged with elapsed_ms"
else
  fail "clone_pruned event not found"
fi

# T24: clone_output_recovered event present with output_bytes
RECOVER_BYTES=$(python3 -c "
import json
for line in open('${LOG_FILE}'):
    obj = json.loads(line)
    if obj.get('event') == 'clone_output_recovered' and 'output_bytes' in obj:
        print(obj['output_bytes'])
        break
else:
    print(-1)
")
if [[ "${RECOVER_BYTES}" -ge 0 ]]; then
  pass "clone_output_recovered event logged with output_bytes"
else
  fail "clone_output_recovered event not found"
fi

echo ""
echo "=== Results ==="
echo "Passed: ${PASS}"
echo "Failed: ${FAIL}"

if [[ "${FAIL}" -gt 0 ]]; then
  echo "SOME TESTS FAILED"
  exit 1
fi

echo "All clone-manager tests passed"
