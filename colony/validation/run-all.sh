#!/usr/bin/env bash
set -euo pipefail

# Colony Validation Runner — T0.1
# Runs all 6 validation scripts, reports PASS/FAIL per script.
# Exits 0 only if 6/6 pass.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PASS_COUNT=0
FAIL_COUNT=0
RESULTS=()

run_test() {
  local name="$1"
  local cmd="$2"
  echo ""
  echo "========================================"
  echo "Running: $name"
  echo "========================================"

  if eval "$cmd"; then
    RESULTS+=("PASS  $name")
    PASS_COUNT=$((PASS_COUNT + 1))
  else
    RESULTS+=("FAIL  $name")
    FAIL_COUNT=$((FAIL_COUNT + 1))
  fi
}

run_test "V-01 plugin-loading"     "bash '$SCRIPT_DIR/v01-plugin-loading.sh'"
run_test "V-02 worker-roundtrip"   "bash '$SCRIPT_DIR/v02-worker-roundtrip.sh'"
run_test "V-03 git-clone"          "bash '$SCRIPT_DIR/v03-git-clone.sh'"
run_test "V-04 sqlite-concurrency" "python3 '$SCRIPT_DIR/v04-sqlite-concurrency.py'"
run_test "V-05 inotifywait"        "bash '$SCRIPT_DIR/v05-inotifywait.sh'"
run_test "V-06 shared-db"          "bash '$SCRIPT_DIR/v06-shared-db.sh'"

echo ""
echo "========================================"
echo "SUMMARY"
echo "========================================"
for r in "${RESULTS[@]}"; do
  echo "  $r"
done
echo ""
echo "Result: $PASS_COUNT/6 passed, $FAIL_COUNT/6 failed"

if [ "$FAIL_COUNT" -eq 0 ]; then
  echo "ALL PASS"
  exit 0
else
  echo "SOME FAILED"
  exit 1
fi
