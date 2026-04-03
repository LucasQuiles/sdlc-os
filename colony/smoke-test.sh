#!/bin/bash
# smoke-test.sh -- Deterministic integration smoke tests for Colony Runtime.
#
# Each test is self-contained with its own temp dirs and cleanup.
# Run: bash smoke-test.sh
# Exit 0 only if all tests pass.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PASS_COUNT=0
FAIL_COUNT=0
TOTAL=6
RESULTS=()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

pass() {
  local name="$1"
  echo "  PASS: ${name}"
  RESULTS+=("PASS: ${name}")
  ((PASS_COUNT++))
}

fail() {
  local name="$1"
  shift
  echo "  FAIL: ${name} -- $*"
  RESULTS+=("FAIL: ${name} -- $*")
  ((FAIL_COUNT++))
}

make_temp_repo() {
  # Create a temp git repo with an initial commit on main.
  # Prints the repo path on stdout.
  local dir
  dir="$(mktemp -d)"
  git -C "$dir" init -b main >/dev/null 2>&1
  git -C "$dir" config user.email "smoke@test" >/dev/null 2>&1
  git -C "$dir" config user.name "Smoke Test" >/dev/null 2>&1
  echo "init" > "$dir/README.md"
  git -C "$dir" add . >/dev/null 2>&1
  git -C "$dir" commit -m "initial commit" >/dev/null 2>&1
  echo "$dir"
}

write_bead_file() {
  # write_bead_file <path> <status> <bead_id> <loop_level>
  local path="$1" status="$2" bead_id="$3" loop_level="$4"
  cat > "$path" <<BEADEOF
# Bead File

**BeadID:** ${bead_id}
**Status:** ${status}
**LoopLevel:** ${loop_level}
**WorkerType:** codex
**Phase:** execute
**CynefinDomain:** complicated
**Description:** Smoke test bead
**AcceptanceCriteria:** Tests pass
**ScopeFiles:** (none)
**Output:** (none)
**CorrectionHistory:** (none)
BEADEOF
}

write_bead_output() {
  # write_bead_output <clone_dir> [with_sentinel]
  local clone_dir="$1"
  local sentinel="${2:-yes}"
  local padding
  # Ensure >100 bytes
  padding="$(printf '%0.s=' {1..120})"
  {
    echo "# Bead Output"
    echo ""
    echo "Result: all tests passed."
    echo "${padding}"
    if [[ "$sentinel" == "yes" ]]; then
      echo "<!-- BEAD_OUTPUT_COMPLETE -->"
    fi
  } > "${clone_dir}/bead-output.md"
}

make_clone_with_commit() {
  # make_clone_with_commit <source_repo>
  # Create a file:// clone and add a commit beyond origin/main.
  # Prints clone dir on stdout.
  local source="$1"
  local clone_dir
  clone_dir="$(mktemp -d)"
  rm -rf "$clone_dir"
  git clone "file://${source}" "$clone_dir" >/dev/null 2>&1
  git -C "$clone_dir" config user.email "smoke@test" >/dev/null 2>&1
  git -C "$clone_dir" config user.name "Smoke Test" >/dev/null 2>&1
  echo "worker output" > "$clone_dir/worker.txt"
  git -C "$clone_dir" add . >/dev/null 2>&1
  git -C "$clone_dir" commit -m "worker commit" >/dev/null 2>&1
  echo "$clone_dir"
}

cleanup_dirs=()
register_cleanup() {
  cleanup_dirs+=("$1")
}

do_cleanup() {
  for d in "${cleanup_dirs[@]}"; do
    rm -rf "$d" 2>/dev/null || true
  done
  cleanup_dirs=()
}

# ---------------------------------------------------------------------------
# ST-01: Bridge CLI round-trip
# ---------------------------------------------------------------------------

st01_bridge_cli_roundtrip() {
  echo "ST-01: Bridge CLI round-trip"
  local repo clone bead_file
  repo="$(make_temp_repo)"
  register_cleanup "$repo"

  bead_file="${repo}/smoke-001.md"
  write_bead_file "$bead_file" "running" "smoke-001" "L0"
  git -C "$repo" add . >/dev/null 2>&1
  git -C "$repo" commit -m "add bead" >/dev/null 2>&1

  clone="$(make_clone_with_commit "$repo")"
  register_cleanup "$clone"

  write_bead_output "$clone" "yes"

  local output exit_code
  output="$(npx tsx "${SCRIPT_DIR}/bridge-cli.ts" \
    --bead-file "$bead_file" \
    --clone-dir "$clone" \
    --loop-level L0 \
    --completed \
    --project-dir "$repo" \
    --expected-branch main 2>&1)"
  exit_code=$?

  if [[ "$exit_code" -ne 0 ]]; then
    fail "ST-01" "bridge-cli exited with code ${exit_code}: ${output}"
    do_cleanup; return
  fi

  # Check bead status.
  local bead_status
  bead_status="$(grep '^\*\*Status:\*\*' "$bead_file" | head -1 | sed 's/\*\*Status:\*\*\s*//')"

  if [[ "$bead_status" != "submitted" ]]; then
    fail "ST-01" "Expected Status: submitted, got: ${bead_status}"
    do_cleanup; return
  fi

  # Check git log for bridge commit
  local log_output
  log_output="$(git -C "$repo" log --oneline -5 2>&1)"
  if ! echo "$log_output" | grep -q "bridge update bead smoke-001"; then
    fail "ST-01" "No bridge commit found in git log"
    do_cleanup; return
  fi

  pass "ST-01"
  do_cleanup
}

# ---------------------------------------------------------------------------
# ST-02: Bridge rejects missing sentinel
# ---------------------------------------------------------------------------

st02_bridge_rejects_missing_sentinel() {
  echo "ST-02: Bridge rejects missing sentinel"
  local repo clone bead_file
  repo="$(make_temp_repo)"
  register_cleanup "$repo"

  bead_file="${repo}/smoke-002.md"
  write_bead_file "$bead_file" "running" "smoke-002" "L0"
  git -C "$repo" add . >/dev/null 2>&1
  git -C "$repo" commit -m "add bead" >/dev/null 2>&1

  clone="$(make_clone_with_commit "$repo")"
  register_cleanup "$clone"

  # Write output WITHOUT sentinel
  write_bead_output "$clone" "no"

  local output exit_code
  output="$(npx tsx "${SCRIPT_DIR}/bridge-cli.ts" \
    --bead-file "$bead_file" \
    --clone-dir "$clone" \
    --loop-level L0 \
    --completed \
    --project-dir "$repo" \
    --expected-branch main 2>&1)"
  exit_code=$?

  if [[ "$exit_code" -eq 0 ]]; then
    fail "ST-02" "Expected exit 1, got exit 0"
    do_cleanup; return
  fi

  if ! echo "$output" | grep -qi "sentinel"; then
    fail "ST-02" "Error output does not mention 'sentinel'"
    do_cleanup; return
  fi

  pass "ST-02"
  do_cleanup
}

# ---------------------------------------------------------------------------
# ST-03: Bridge CAS rejection
# ---------------------------------------------------------------------------

st03_bridge_cas_rejection() {
  echo "ST-03: Bridge CAS rejection"
  local repo clone bead_file
  repo="$(make_temp_repo)"
  register_cleanup "$repo"

  # Bead with Status: verified (not running)
  bead_file="${repo}/smoke-003.md"
  write_bead_file "$bead_file" "verified" "smoke-003" "L0"
  git -C "$repo" add . >/dev/null 2>&1
  git -C "$repo" commit -m "add bead" >/dev/null 2>&1

  clone="$(make_clone_with_commit "$repo")"
  register_cleanup "$clone"
  write_bead_output "$clone" "yes"

  local output exit_code
  output="$(npx tsx "${SCRIPT_DIR}/bridge-cli.ts" \
    --bead-file "$bead_file" \
    --clone-dir "$clone" \
    --loop-level L0 \
    --completed \
    --project-dir "$repo" \
    --expected-branch main \
    --expected-status running 2>&1)"
  exit_code=$?

  if [[ "$exit_code" -eq 0 ]]; then
    fail "ST-03" "Expected exit 1, got exit 0"
    do_cleanup; return
  fi

  if ! echo "$output" | grep -qi "mismatch\|status"; then
    fail "ST-03" "Error output does not mention status mismatch"
    do_cleanup; return
  fi

  pass "ST-03"
  do_cleanup
}

# ---------------------------------------------------------------------------
# ST-04: Clone manager lifecycle
# ---------------------------------------------------------------------------

st04_clone_manager_lifecycle() {
  echo "ST-04: Clone manager lifecycle"

  # Source clone-manager.sh in a subshell context
  local repo clone_dir
  repo="$(make_temp_repo)"
  register_cleanup "$repo"

  # We run clone-manager functions via bash -c to keep source isolation
  export COLONY_BASE
  COLONY_BASE="$(mktemp -d)/sdlc-colony"
  mkdir -p "$COLONY_BASE"
  register_cleanup "$COLONY_BASE"

  # colony_clone_create
  clone_dir="$(bash -c "
    set -euo pipefail
    source '${SCRIPT_DIR}/clone-manager.sh'
    colony_clone_create '${repo}' 'smoke-session' 'agent1'
  " 2>/dev/null)"

  if [[ ! -d "${clone_dir}/.git" ]]; then
    fail "ST-04" "clone_create: .git does not exist at ${clone_dir}"
    do_cleanup; return
  fi

  if [[ "${clone_dir}" != *"/sdlc-colony/"* ]]; then
    fail "ST-04" "clone_create: path not under expected colony base"
    do_cleanup; return
  fi

  # colony_clone_verify
  if ! bash -c "
    set -euo pipefail
    export COLONY_BASE='${COLONY_BASE}'
    source '${SCRIPT_DIR}/clone-manager.sh'
    colony_clone_verify '${clone_dir}'
  " 2>/dev/null; then
    fail "ST-04" "clone_verify: returned non-zero"
    do_cleanup; return
  fi

  # colony_clone_has_commits -- should be 1 (no commits beyond origin/main yet)
  if bash -c "
    set -euo pipefail
    export COLONY_BASE='${COLONY_BASE}'
    source '${SCRIPT_DIR}/clone-manager.sh'
    colony_clone_has_commits '${clone_dir}'
  " 2>/dev/null; then
    fail "ST-04" "clone_has_commits: should return 1 (no extra commits)"
    do_cleanup; return
  fi

  # Add a commit to the clone
  git -C "$clone_dir" config user.email "smoke@test" >/dev/null 2>&1
  git -C "$clone_dir" config user.name "Smoke Test" >/dev/null 2>&1
  echo "new work" > "${clone_dir}/work.txt"
  git -C "$clone_dir" add . >/dev/null 2>&1
  git -C "$clone_dir" commit -m "worker commit" >/dev/null 2>&1

  # colony_clone_has_commits -- should now be 0
  if ! bash -c "
    set -euo pipefail
    export COLONY_BASE='${COLONY_BASE}'
    source '${SCRIPT_DIR}/clone-manager.sh'
    colony_clone_has_commits '${clone_dir}'
  " 2>/dev/null; then
    fail "ST-04" "clone_has_commits: should return 0 after adding commit"
    do_cleanup; return
  fi

  # colony_clone_prune with bridge_synced=0 -- should fail
  if bash -c "
    set -euo pipefail
    export COLONY_BASE='${COLONY_BASE}'
    source '${SCRIPT_DIR}/clone-manager.sh'
    colony_clone_prune '${clone_dir}' 0
  " 2>/dev/null; then
    fail "ST-04" "clone_prune(0): should return 1 (not synced)"
    do_cleanup; return
  fi

  # colony_clone_prune with bridge_synced=1 -- should succeed
  if ! bash -c "
    set -euo pipefail
    export COLONY_BASE='${COLONY_BASE}'
    source '${SCRIPT_DIR}/clone-manager.sh'
    colony_clone_prune '${clone_dir}' 1
  " 2>/dev/null; then
    fail "ST-04" "clone_prune(1): should return 0"
    do_cleanup; return
  fi

  if [[ -d "$clone_dir" ]]; then
    fail "ST-04" "clone_prune(1): directory still exists after prune"
    do_cleanup; return
  fi

  pass "ST-04"
  do_cleanup
}

# ---------------------------------------------------------------------------
# ST-05: Deacon lock behavior
# ---------------------------------------------------------------------------

st05_deacon_lock_behavior() {
  echo "ST-05: Deacon lock behavior"

  local lock_file="/tmp/sdlc-colony-conductor.lock"
  local lock_backup=""

  # Back up existing lock file if present
  if [[ -f "$lock_file" ]]; then
    lock_backup="$(mktemp)"
    cp "$lock_file" "$lock_backup"
  fi

  # Write lock file with dead PID (99999) + stale timestamp
  echo "99999" > "$lock_file"
  echo "1000000000.0" >> "$lock_file"

  local db_path
  db_path="$(mktemp --suffix=.db)"
  register_cleanup "$db_path"

  # Create minimal DB so Deacon can instantiate
  python3 -c "
import sqlite3
conn = sqlite3.connect('${db_path}')
conn.execute('CREATE TABLE IF NOT EXISTS tasks (id TEXT, status TEXT, sdlc_loop_level TEXT, bridge_synced INT, bead_id TEXT, retry_count INT, max_retries INT, clone_dir TEXT, description TEXT, owner TEXT)')
conn.execute('CREATE TABLE IF NOT EXISTS agents (id TEXT, last_heartbeat_at TEXT)')
conn.commit()
conn.close()
" 2>/dev/null

  local output
  output="$(python3 -c "
import sys
sys.path.insert(0, '${SCRIPT_DIR}')
from deacon import Deacon
d = Deacon(db_path='${db_path}', project_dir='/tmp')
print(d.can_spawn_conductor())
" 2>/dev/null)"

  # Restore lock file
  if [[ -n "$lock_backup" ]]; then
    cp "$lock_backup" "$lock_file"
    rm -f "$lock_backup"
  else
    rm -f "$lock_file"
  fi

  if [[ "$output" == "True" ]]; then
    pass "ST-05"
  else
    fail "ST-05" "Expected True (stale lock), got: ${output}"
  fi

  do_cleanup
}

# ---------------------------------------------------------------------------
# ST-06: Deacon check_for_work
# ---------------------------------------------------------------------------

st06_deacon_check_for_work() {
  echo "ST-06: Deacon check_for_work"

  local db_path
  db_path="$(mktemp --suffix=.db)"
  register_cleanup "$db_path"

  # Create schema and insert a pending task with bead_id
  python3 -c "
import sqlite3
conn = sqlite3.connect('${db_path}')
conn.execute('''CREATE TABLE IF NOT EXISTS tasks (
  id TEXT, status TEXT, sdlc_loop_level TEXT,
  bridge_synced INT DEFAULT 0, bead_id TEXT,
  retry_count INT DEFAULT 0, max_retries INT DEFAULT 3,
  clone_dir TEXT, description TEXT, owner TEXT
)''')
conn.execute('''CREATE TABLE IF NOT EXISTS agents (
  id TEXT, last_heartbeat_at TEXT
)''')
conn.execute(\"INSERT INTO tasks (id, status, sdlc_loop_level, bead_id) VALUES ('task-1', 'pending', 'L0', 'bead-001')\")
conn.commit()
conn.close()
" 2>/dev/null

  local output
  output="$(python3 -c "
import sys
sys.path.insert(0, '${SCRIPT_DIR}')
from deacon import Deacon
d = Deacon(db_path='${db_path}', project_dir='/tmp')
print(d.check_for_work())
" 2>/dev/null)"

  if [[ "$output" == "True" ]]; then
    pass "ST-06"
  else
    fail "ST-06" "Expected True, got: ${output}"
  fi

  do_cleanup
}

# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

echo "============================================"
echo "Colony Runtime Smoke Tests"
echo "============================================"
echo ""

st01_bridge_cli_roundtrip
st02_bridge_rejects_missing_sentinel
st03_bridge_cas_rejection
st04_clone_manager_lifecycle
st05_deacon_lock_behavior
st06_deacon_check_for_work

echo ""
echo "============================================"
echo "Results: ${PASS_COUNT}/${TOTAL} PASS"
echo "============================================"
for r in "${RESULTS[@]}"; do
  echo "  ${r}"
done

if [[ "$PASS_COUNT" -eq "$TOTAL" ]]; then
  exit 0
else
  exit 1
fi
