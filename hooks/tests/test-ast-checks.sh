#!/bin/bash
# ast-checks.sh hook-mode regression matrix
# Run: bash hooks/tests/test-ast-checks.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SOURCE_AST_CHECKS="$PLUGIN_ROOT/scripts/ast-checks.sh"
SOURCE_AST_COMMON="$PLUGIN_ROOT/scripts/lib/ast-common.sh"
SOURCE_HOOK_COMMON="$PLUGIN_ROOT/hooks/lib/common.sh"

PASS=0
FAIL=0

CASE_STDOUT=""
CASE_EXIT=0

pass() {
  echo "  PASS: $1"
  PASS=$((PASS + 1))
}

fail() {
  echo "  FAIL: $1"
  FAIL=$((FAIL + 1))
}

make_sandbox() {
  local sandbox
  sandbox=$(mktemp -d)
  mkdir -p "$sandbox/scripts/lib" "$sandbox/hooks/lib"
  cp "$SOURCE_AST_CHECKS" "$sandbox/scripts/ast-checks.sh"
  cp "$SOURCE_AST_COMMON" "$sandbox/scripts/lib/ast-common.sh"
  cp "$SOURCE_HOOK_COMMON" "$sandbox/hooks/lib/common.sh"
  chmod +x "$sandbox/scripts/ast-checks.sh"
  echo "$sandbox"
}

make_bin_dir() {
  local dir
  dir=$(mktemp -d)
  local name
  for name in "$@"; do
    local src
    src=$(command -v "$name" || true)
    if [[ -n "$src" ]]; then
      ln -s "$src" "$dir/$name"
    fi
  done
  echo "$dir"
}

run_with_stdin() {
  local sandbox="$1"
  local path_env="$2"
  local input="$3"
  shift 3

  CASE_EXIT=0
  CASE_STDOUT=$(
    printf '%s' "$input" | PATH="$path_env" /bin/bash "$sandbox/scripts/ast-checks.sh" "$@" 2>/dev/null
  ) || CASE_EXIT=$?
}

run_with_empty_stdin() {
  local sandbox="$1"
  local path_env="$2"
  shift 2

  CASE_EXIT=0
  CASE_STDOUT=$(
    PATH="$path_env" /bin/bash "$sandbox/scripts/ast-checks.sh" "$@" </dev/null 2>/dev/null
  ) || CASE_EXIT=$?
}

run_cli() {
  local sandbox="$1"
  local path_env="$2"
  shift 2

  CASE_EXIT=0
  CASE_STDOUT=$(
    PATH="$path_env" /bin/bash "$sandbox/scripts/ast-checks.sh" "$@" 2>/dev/null
  ) || CASE_EXIT=$?
}

assert_case() {
  local name="$1"
  local expected_status="$2"
  local expected_reason="${3:-}"

  if [[ "$CASE_EXIT" -ne 0 ]]; then
    fail "$name (expected exit 0, got $CASE_EXIT)"
    echo "    stdout: $CASE_STDOUT"
    return
  fi

  if ! printf '%s\n' "$CASE_STDOUT" | grep -Eq "\"status\"[[:space:]]*:[[:space:]]*\"$expected_status\""; then
    fail "$name (expected status $expected_status, got: $CASE_STDOUT)"
    return
  fi

  if [[ -n "$expected_reason" ]] && ! printf '%s\n' "$CASE_STDOUT" | grep -Fq "$expected_reason"; then
    fail "$name (missing reason substring: $expected_reason; got: $CASE_STDOUT)"
    return
  fi

  pass "$name"
}

make_fixture_file() {
  local dir="$1"
  local relpath="$2"
  local content="$3"
  mkdir -p "$(dirname "$dir/$relpath")"
  printf '%s\n' "$content" > "$dir/$relpath"
}

echo "=== ast-checks Hook Matrix ==="

STANDARD_BIN="$(make_bin_dir dirname cat jq timeout tail)"
NO_JQ_BIN="$(make_bin_dir dirname cat timeout tail)"
NO_TIMEOUT_BIN="$(make_bin_dir dirname cat jq tail)"

trap 'rm -rf "$STANDARD_BIN" "$NO_JQ_BIN" "$NO_TIMEOUT_BIN"' EXIT

test_empty_stdin() {
  local sandbox
  sandbox=$(make_sandbox)

  run_with_empty_stdin "$sandbox" "$STANDARD_BIN" --check ALL
  assert_case "empty stdin -> SKIP" "SKIP" "no analyzable files"
  rm -rf "$sandbox"
}

test_bash_event_without_file_path() {
  local sandbox
  sandbox=$(make_sandbox)

  run_with_stdin "$sandbox" "$STANDARD_BIN" '{"tool_name":"Bash","tool_input":{"command":"true"}}' --check ALL
  assert_case "Bash event without file_path -> SKIP" "SKIP" "no analyzable files"
  rm -rf "$sandbox"
}

test_non_code_file_path() {
  local sandbox work
  sandbox=$(make_sandbox)
  work=$(mktemp -d)

  make_fixture_file "$work" "docs/readme.md" "# readme"
  run_with_stdin "$sandbox" "$STANDARD_BIN" "{\"tool_name\":\"Write\",\"tool_input\":{\"file_path\":\"$work/docs/readme.md\"}}" --check ALL
  assert_case ".md hook input -> SKIP" "SKIP" "no analyzable files"
  rm -rf "$sandbox" "$work"
}

test_ts_without_eslint_hook_mode() {
  local sandbox work
  sandbox=$(make_sandbox)
  work=$(mktemp -d)

  make_fixture_file "$work" "src/example.ts" "const x = 1;"
  run_with_stdin "$sandbox" "$STANDARD_BIN" "{\"tool_name\":\"Write\",\"tool_input\":{\"file_path\":\"$work/src/example.ts\"}}" --check ALL
  assert_case ".ts via hook stdin without eslint -> UNAVAILABLE" "UNAVAILABLE" "eslint not found"
  rm -rf "$sandbox" "$work"
}

test_missing_jq() {
  local sandbox work
  sandbox=$(make_sandbox)
  work=$(mktemp -d)

  make_fixture_file "$work" "src/example.ts" "const x = 1;"
  run_with_stdin "$sandbox" "$NO_JQ_BIN" "{\"tool_name\":\"Write\",\"tool_input\":{\"file_path\":\"$work/src/example.ts\"}}" --check ALL
  assert_case "jq missing -> UNAVAILABLE" "UNAVAILABLE" "jq not in PATH"
  rm -rf "$sandbox" "$work"
}

test_missing_timeout() {
  local sandbox work
  sandbox=$(make_sandbox)
  work=$(mktemp -d)

  make_fixture_file "$work" "src/example.ts" "const x = 1;"
  run_with_stdin "$sandbox" "$NO_TIMEOUT_BIN" "{\"tool_name\":\"Write\",\"tool_input\":{\"file_path\":\"$work/src/example.ts\"}}" --check ALL
  assert_case "timeout missing -> UNAVAILABLE" "UNAVAILABLE" "timeout(1) not in PATH"
  rm -rf "$sandbox" "$work"
}

test_missing_common_sh() {
  local sandbox work
  sandbox=$(make_sandbox)
  work=$(mktemp -d)

  rm -f "$sandbox/hooks/lib/common.sh"
  make_fixture_file "$work" "src/example.ts" "const x = 1;"
  run_with_stdin "$sandbox" "$STANDARD_BIN" "{\"tool_name\":\"Write\",\"tool_input\":{\"file_path\":\"$work/src/example.ts\"}}" --check ALL
  assert_case "common.sh missing -> UNAVAILABLE" "UNAVAILABLE" "hooks/lib/common.sh not found"
  rm -rf "$sandbox" "$work"
}

test_cli_without_eslint() {
  local sandbox work
  sandbox=$(make_sandbox)
  work=$(mktemp -d)

  make_fixture_file "$work" "src/example.tsx" "export const x = 1;"
  run_cli "$sandbox" "$STANDARD_BIN" --check ALL "$work/src/example.tsx"
  assert_case "CLI .tsx without eslint -> UNAVAILABLE" "UNAVAILABLE" "eslint not found"
  rm -rf "$sandbox" "$work"
}

test_empty_stdin
test_bash_event_without_file_path
test_non_code_file_path
test_ts_without_eslint_hook_mode
test_missing_jq
test_missing_timeout
test_missing_common_sh
test_cli_without_eslint

echo
echo "PASS: $PASS  FAIL: $FAIL  TOTAL: $((PASS + FAIL))"

if [[ "$FAIL" -ne 0 ]]; then
  exit 1
fi
