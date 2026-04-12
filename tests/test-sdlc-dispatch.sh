#!/bin/bash
set -euo pipefail

DISPATCH="$HOME/LAB/sdlc-os/hooks/sdlc-dispatch.sh"
PASS=0
FAIL=0

test_dispatch() {
  local payload="$1" expected_exit="$2" desc="$3"
  local check_stderr="${4:-}"
  local actual_exit=0 stderr_out=""
  stderr_out=$(echo "$payload" | bash "$DISPATCH" 2>&1 >/dev/null) || actual_exit=$?
  if [[ "$actual_exit" -ne "$expected_exit" ]]; then
    echo "FAIL: $desc — expected exit $expected_exit, got $actual_exit (stderr: $stderr_out)" >&2
    FAIL=$((FAIL + 1))
    return
  fi
  if [[ -n "$check_stderr" ]] && [[ "$stderr_out" != *"$check_stderr"* ]]; then
    echo "FAIL: $desc — stderr missing '$check_stderr' (got: $stderr_out)" >&2
    FAIL=$((FAIL + 1))
    return
  fi
  PASS=$((PASS + 1))
}

# Create real temp files for realistic tests
TMPROOT="$(mktemp -d)"
trap 'rm -rf "$TMPROOT"' EXIT
mkdir -p "$TMPROOT/node_modules"
printf 'const x = 1;\n' > "$TMPROOT/test.ts"
printf 'x = 1\n' > "$TMPROOT/test.py"

# --- Fast path: vendor ---
test_dispatch \
  '{"tool_name":"Write","tool_input":{"file_path":"'"$TMPROOT"'/node_modules/foo.ts","content":"x"}}' \
  0 "vendor path exits 0"

# --- Fast path: .md outside SDLC ---
test_dispatch \
  '{"tool_name":"Write","tool_input":{"file_path":"'"$TMPROOT"'/README.md","content":"# hello"}}' \
  0 ".md outside SDLC exits 0 (no validators match)"

# --- Fast path: empty file_path ---
test_dispatch \
  '{"tool_name":"Write","tool_input":{"content":"x"}}' \
  0 "empty file_path exits 0"

# --- Source file: .ts runs safety-constraints (advisory) ---
test_dispatch \
  '{"tool_name":"Write","tool_input":{"file_path":"'"$TMPROOT"'/test.ts","content":"const x = 1;"}}' \
  0 ".ts file runs validators but passes"

# --- Source file: .py runs safety-constraints only ---
test_dispatch \
  '{"tool_name":"Write","tool_input":{"file_path":"'"$TMPROOT"'/test.py","content":"x = 1"}}' \
  0 ".py file runs safety-constraints only"

# --- Empty stdin ---
test_dispatch \
  '' \
  0 "empty stdin exits 0"

# --- .json file: no validators match ---
test_dispatch \
  '{"tool_name":"Write","tool_input":{"file_path":"'"$TMPROOT"'/package.json","content":"{}"}}' \
  0 ".json file exits 0 (no validators)"

# --- Blocking test: quality-budget with missing fields ---
printf 'schema_version: 1\n' > "$TMPROOT/quality-budget.yaml"
test_dispatch \
  '{"tool_name":"Write","tool_input":{"file_path":"'"$TMPROOT"'/quality-budget.yaml","content":"schema_version: 1"}}' \
  2 "quality-budget with missing fields blocks" \
  "missing"

echo "Results: $PASS passed, $FAIL failed"
[[ "$FAIL" -eq 0 ]]
