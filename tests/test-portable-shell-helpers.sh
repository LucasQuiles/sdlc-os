#!/bin/bash
set -euo pipefail

TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
PLUGIN_ROOT="$(cd "$TEST_DIR/.." && pwd -P)"
HELPER="$PLUGIN_ROOT/colony/lib/portable-shell.sh"
CLONE_MANAGER="$PLUGIN_ROOT/colony/clone-manager.sh"
SMOKE_TEST="$PLUGIN_ROOT/colony/smoke-test.sh"

PASS=0
FAIL=0

pass() {
  printf '  PASS: %s\n' "$1"
  PASS=$((PASS + 1))
}

fail() {
  printf '  FAIL: %s\n' "$1"
  FAIL=$((FAIL + 1))
}

TEST_ROOT_RAW="$(mktemp -d "${TMPDIR:-/tmp}/sdlc-portable-shell.XXXXXX")"
TEST_ROOT="$(cd "$TEST_ROOT_RAW" && pwd -P)"
cleanup() {
  local rc=$?
  trap - EXIT
  rm -rf "$TEST_ROOT"
  exit "$rc"
}
trap cleanup EXIT

mkdir "$TEST_ROOT/runtime space"
export TMPDIR="$TEST_ROOT/runtime space"

if [[ -f "$HELPER" && ! -L "$HELPER" ]]; then
  # shellcheck source=/dev/null
  source "$HELPER"
  pass "portable helper exists"

  SIZE_DIR="$TEST_ROOT/nonempty"
  mkdir "$SIZE_DIR"
  printf 'portable-size\n' > "$SIZE_DIR/input.txt"
  if size="$(path_size_bytes "$SIZE_DIR")" &&
      [[ "$size" =~ ^[1-9][0-9]*$ ]] &&
      [[ $((size % 1024)) -eq 0 ]]; then
    pass "path_size_bytes returns positive byte telemetry"
  else
    fail "path_size_bytes did not return positive kibibyte-derived bytes"
  fi

  if temp_one="$(make_temp_file sdlc-colony-db)" &&
      temp_two="$(make_temp_file sdlc-colony-db)" &&
      [[ -f "$temp_one" && ! -L "$temp_one" ]] &&
      [[ -f "$temp_two" && ! -L "$temp_two" ]] &&
      [[ "$temp_one" != "$temp_two" ]] &&
      [[ "$(cd "$(dirname "$temp_one")" && pwd -P)" == "$TMPDIR" ]] &&
      [[ "$(cd "$(dirname "$temp_two")" && pwd -P)" == "$TMPDIR" ]]; then
    pass "make_temp_file creates unique files inside TMPDIR"
  else
    fail "make_temp_file did not create unique contained files"
  fi
else
  fail "portable helper exists"
fi

du_gnu_count="$(awk '/du -sb/ { count += 1 } END { print count + 0 }' "$CLONE_MANAGER")"
if [[ "$du_gnu_count" -eq 0 ]]; then
  pass "clone manager has no GNU-only du -sb"
else
  fail "clone manager still has $du_gnu_count GNU-only du -sb call(s)"
fi

size_helper_count="$(awk '/path_size_bytes/ { count += 1 } END { print count + 0 }' "$CLONE_MANAGER")"
if [[ "$size_helper_count" -eq 2 ]]; then
  pass "clone manager uses path_size_bytes at both telemetry sites"
else
  fail "clone manager uses path_size_bytes at $size_helper_count of 2 telemetry sites"
fi

mktemp_gnu_count="$(awk '/mktemp --suffix/ { count += 1 } END { print count + 0 }' "$SMOKE_TEST")"
if [[ "$mktemp_gnu_count" -eq 0 ]]; then
  pass "smoke test has no GNU-only mktemp --suffix"
else
  fail "smoke test still has $mktemp_gnu_count GNU-only mktemp --suffix call(s)"
fi

temp_helper_count="$(awk '/make_temp_file sdlc-colony-db/ { count += 1 } END { print count + 0 }' "$SMOKE_TEST")"
if [[ "$temp_helper_count" -eq 3 ]]; then
  pass "smoke test uses make_temp_file at all database sites"
else
  fail "smoke test uses make_temp_file at $temp_helper_count of 3 database sites"
fi

printf '\nPassed: %s\nFailed: %s\n' "$PASS" "$FAIL"
if [[ "$FAIL" -gt 0 ]]; then
  exit 1
fi

printf 'All portable shell helper tests passed\n'
