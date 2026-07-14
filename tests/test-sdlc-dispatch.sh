#!/bin/bash
set -euo pipefail

umask 077

TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=tests/lib/plugin-root.sh
source "$TEST_DIR/lib/plugin-root.sh"
SOURCE_ROOT="$(resolve_plugin_root "${BASH_SOURCE[0]}")"
SOURCE_VALIDATOR="$SOURCE_ROOT/hooks/validators/safety-constraints.sh"
TEMP_TREE_HELPER="$SOURCE_ROOT/tests/lib/f01-temp-tree.py"
CHILD_PATH="/opt/homebrew/opt/node@20/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"
PYTHON_BIN="${PYTHON_BIN:-}"

resolve_python_bin() {
  local candidate probe version executable
  candidate="$PYTHON_BIN"
  if [[ -z "$candidate" ]]; then
    if ! candidate="$(command -v python3.12 2>/dev/null)"; then
      return 1
    fi
  fi
  [[ "$candidate" == /* && -x "$candidate" ]] || return 1
  if ! probe="$("$candidate" -c '
import os
import sys

print(f"{sys.version_info.major}.{sys.version_info.minor}")
print(os.path.realpath(sys.executable))
' 2>/dev/null)"; then
    return 1
  fi
  case "$probe" in *$'\n'*) ;; *) return 1 ;; esac
  version="${probe%%$'\n'*}"
  executable="${probe#*$'\n'}"
  [[ "$version" == "3.12" &&
      "$executable" == /* &&
      "$executable" != *$'\n'* &&
      -f "$executable" &&
      ! -L "$executable" &&
      -x "$executable" ]] || return 1
  printf '%s\n' "$executable"
}

if ! PYTHON_BIN="$(resolve_python_bin)"; then
  printf 'F01_FIXTURE_ESCAPE: canonical Python 3.12 is unavailable\n' >&2
  exit 1
fi
if [[ ! -f "$TEMP_TREE_HELPER" || -L "$TEMP_TREE_HELPER" ]]; then
  printf 'F01_TEMP_TREE_HELPER_MISSING:%s\n' "$TEMP_TREE_HELPER" >&2
  exit 1
fi

TMP_BASE="${TMPDIR:-/tmp}"
[[ -d "$TMP_BASE" ]] || {
  printf 'F01_FIXTURE_ESCAPE:TMPDIR does not exist: %s\n' "$TMP_BASE" >&2
  exit 1
}
TMPROOT="$(mktemp -d "$TMP_BASE/sdlc-dispatch-test.XXXXXX")"
TMPROOT="$(cd "$TMPROOT" && pwd -P)"
TMPROOT_TOKEN="$("$PYTHON_BIN" "$TEMP_TREE_HELPER" capture \
  "$TMPROOT" sdlc-dispatch-test.)" || {
  printf 'F01_INNER_RETAINED:%s\n' "$TMPROOT" >&2
  exit 125
}
FIXTURE_ROOT="$TMPROOT/fixture"
ISOLATED_HOME="$TMPROOT/home"
WORK_ROOT="$TMPROOT/work"
RUNTIME_ROOT="$TMPROOT/runtime"
EVIDENCE_ROOT="$TMPROOT/evidence"
BACKUP_ROOT="$TMPROOT/backups"
REPLACEMENT_ROOT="$TMPROOT/replacements"
FIXTURE_VALIDATOR=""
FIXTURE_BASELINE=""
BACKUP_VALIDATOR=""
RESTORE_FAILED=0
PRESERVE_TMPROOT=0

record_restore_failure() {
  if [[ "$RESTORE_FAILED" -eq 0 ]]; then
    RESTORE_FAILED=1
    PRESERVE_TMPROOT=1
    printf 'F01_RESTORE_FAILED:%s\n' "$FIXTURE_ROOT" >&2
  fi
}

cleanup() {
  local rc=$?
  trap - EXIT HUP INT TERM
  if [[ "$RESTORE_FAILED" -eq 0 && -n "$BACKUP_VALIDATOR" ]]; then
    if [[ ! -f "$BACKUP_VALIDATOR" || -L "$BACKUP_VALIDATOR" ]] ||
        ! rm -f "$FIXTURE_VALIDATOR" ||
        ! mv "$BACKUP_VALIDATOR" "$FIXTURE_VALIDATOR" ||
        ! cmp -s "$FIXTURE_BASELINE" "$FIXTURE_VALIDATOR"; then
      record_restore_failure
    fi
  fi
  if [[ "$PRESERVE_TMPROOT" -ne 0 ]]; then
    exit 125
  fi
  if ! "$PYTHON_BIN" "$TEMP_TREE_HELPER" remove \
      "$TMPROOT" sdlc-dispatch-test. "$TMPROOT_TOKEN"; then
    printf 'CLEANUP_FAILED:%s\n' "$TMPROOT" >&2
    printf 'F01_INNER_RETAINED:%s\n' "$TMPROOT" >&2
    exit 125
  fi
  exit "$rc"
}

trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

fail_fixture() {
  printf 'F01_FIXTURE_ESCAPE:%s\n' "$1" >&2
  exit 1
}

require_contained_dir() {
  local path="$1" physical
  physical="$(cd "$path" 2>/dev/null && pwd -P)" || fail_fixture "cannot resolve directory $path"
  case "$physical/" in
    "$TMPROOT"/*) ;;
    *) fail_fixture "directory escaped fixture root: $path" ;;
  esac
  printf '%s\n' "$physical"
}

require_regular_file() {
  local path="$1"
  [[ -f "$path" && ! -L "$path" ]] || fail_fixture "regular non-symlink file required: $path"
}

restore_validator() {
  if ! rm -f "$FIXTURE_VALIDATOR" ||
      ! mv "$BACKUP_VALIDATOR" "$FIXTURE_VALIDATOR" ||
      ! cmp -s "$FIXTURE_BASELINE" "$FIXTURE_VALIDATOR"; then
    record_restore_failure
    exit 125
  fi
  BACKUP_VALIDATOR=""
}

mkdir -p \
  "$FIXTURE_ROOT" \
  "$ISOLATED_HOME" \
  "$WORK_ROOT" \
  "$RUNTIME_ROOT" \
  "$EVIDENCE_ROOT" \
  "$BACKUP_ROOT" \
  "$REPLACEMENT_ROOT"
FIXTURE_ROOT="$(require_contained_dir "$FIXTURE_ROOT")"
ISOLATED_HOME="$(require_contained_dir "$ISOLATED_HOME")"
WORK_ROOT="$(require_contained_dir "$WORK_ROOT")"
RUNTIME_ROOT="$(require_contained_dir "$RUNTIME_ROOT")"
EVIDENCE_ROOT="$(require_contained_dir "$EVIDENCE_ROOT")"
BACKUP_ROOT="$(require_contained_dir "$BACKUP_ROOT")"
REPLACEMENT_ROOT="$(require_contained_dir "$REPLACEMENT_ROOT")"

require_regular_file "$SOURCE_VALIDATOR"
require_regular_file "$TEMP_TREE_HELPER"
cp -R "$SOURCE_ROOT/hooks" "$FIXTURE_ROOT/hooks"
cp -R "$SOURCE_ROOT/scripts" "$FIXTURE_ROOT/scripts"
first_link="$(find "$FIXTURE_ROOT/hooks" "$FIXTURE_ROOT/scripts" -type l -print -quit)"
[[ -z "$first_link" ]] || fail_fixture "copied dependency symlink: $first_link"
DISPATCH="$FIXTURE_ROOT/hooks/sdlc-dispatch.sh"
FIXTURE_VALIDATOR="$FIXTURE_ROOT/hooks/validators/safety-constraints.sh"
require_regular_file "$DISPATCH"
require_regular_file "$FIXTURE_VALIDATOR"
[[ "$FIXTURE_VALIDATOR" != "$SOURCE_VALIDATOR" ]] || fail_fixture "source and fixture paths alias"
[[ ! "$FIXTURE_VALIDATOR" -ef "$SOURCE_VALIDATOR" ]] || fail_fixture "source and fixture inodes alias"
case "$FIXTURE_VALIDATOR" in
  "$TMPROOT"/*) ;;
  *) fail_fixture "fixture validator escaped temporary root" ;;
esac
FIXTURE_BASELINE="$EVIDENCE_ROOT/safety-constraints.bytes"
cp "$FIXTURE_VALIDATOR" "$FIXTURE_BASELINE"

PASS=0
FAIL=0
CASE_INDEX=0

test_dispatch() {
  local payload="$1" expected_exit="$2" desc="$3"
  local check_stderr="${4:-}"
  local actual_exit stderr_out payload_file stderr_file
  CASE_INDEX=$((CASE_INDEX + 1))
  payload_file="$EVIDENCE_ROOT/case-$CASE_INDEX.stdin"
  stderr_file="$EVIDENCE_ROOT/case-$CASE_INDEX.stderr"
  printf '%s\n' "$payload" >"$payload_file"
  set +e
  (
    cd "$WORK_ROOT"
    exec env -i \
      LC_ALL=C \
      PATH="$CHILD_PATH" \
      HOME="$ISOLATED_HOME" \
      TMPDIR="$RUNTIME_ROOT" \
      CLAUDE_PLUGIN_ROOT="$FIXTURE_ROOT" \
      CLAUDE_PROJECT_DIR="$WORK_ROOT" \
      /bin/bash "$DISPATCH" <"$payload_file" >/dev/null 2>"$stderr_file"
  )
  actual_exit=$?
  set -e
  stderr_out="$(<"$stderr_file")"
  if [[ "$actual_exit" -ne "$expected_exit" ]]; then
    printf 'FAIL: %s — expected exit %s, got %s (stderr: %s)\n' \
      "$desc" "$expected_exit" "$actual_exit" "$stderr_out" >&2
    FAIL=$((FAIL + 1))
    return
  fi
  if [[ -n "$check_stderr" && "$stderr_out" != *"$check_stderr"* ]]; then
    printf 'FAIL: %s — stderr missing %s (got: %s)\n' \
      "$desc" "$check_stderr" "$stderr_out" >&2
    FAIL=$((FAIL + 1))
    return
  fi
  PASS=$((PASS + 1))
}

mkdir -p "$WORK_ROOT/node_modules"
printf 'const x = 1;\n' >"$WORK_ROOT/test.ts"
printf 'x = 1\n' >"$WORK_ROOT/test.py"

test_dispatch \
  '{"tool_name":"Write","tool_input":{"file_path":"'"$WORK_ROOT"'/node_modules/foo.ts","content":"x"}}' \
  0 "vendor path exits 0"

test_dispatch \
  '{"tool_name":"Write","tool_input":{"file_path":"'"$WORK_ROOT"'/README.md","content":"# hello"}}' \
  0 ".md outside SDLC exits 0 (no validators match)"

test_dispatch \
  '{"tool_name":"Write","tool_input":{"content":"x"}}' \
  0 "empty file_path exits 0"

test_dispatch \
  '{"tool_name":"Write","tool_input":{"file_path":"'"$WORK_ROOT"'/test.ts","content":"const x = 1;"}}' \
  0 ".ts file runs validators but passes"

test_dispatch \
  '{"tool_name":"Write","tool_input":{"file_path":"'"$WORK_ROOT"'/test.py","content":"x = 1"}}' \
  0 ".py file runs safety-constraints only"

test_dispatch \
  '' \
  0 "empty stdin exits 0"

test_dispatch \
  '{"tool_name":"Write","tool_input":{"file_path":"'"$WORK_ROOT"'/package.json","content":"{}"}}' \
  0 ".json file exits 0 (no validators)"

printf 'schema_version: 1\n' >"$WORK_ROOT/quality-budget.yaml"
test_dispatch \
  '{"tool_name":"Write","tool_input":{"file_path":"'"$WORK_ROOT"'/quality-budget.yaml","content":"schema_version: 1"}}' \
  2 "quality-budget with missing fields blocks" \
  "missing"

if [[ -n "${SDLC_TEST_PRE_FAILPOINT_FAILURE:-}" ]]; then
  if [[ "${SDLC_TEST_FAILPOINT:-}" != "after-validator-swap" ]]; then
    exit 64
  fi
  case "$SDLC_TEST_PRE_FAILPOINT_FAILURE" in
    synthetic)
      printf 'FAIL: synthetic pre-failpoint failure\n' >&2
      FAIL=$((FAIL + 1))
      ;;
    *) exit 64 ;;
  esac
fi
if [[ "$PASS" -ne 8 || "$FAIL" -ne 0 ]]; then
  printf 'F01_PRE_FAILPOINT_CASES_FAILED:pass=%s fail=%s\n' "$PASS" "$FAIL" >&2
  exit 1
fi

BACKUP_VALIDATOR="$BACKUP_ROOT/safety-constraints.original"
mv "$FIXTURE_VALIDATOR" "$BACKUP_VALIDATOR"
if [[ -n "${SDLC_TEST_RESTORE_FAILURE:-}" ]]; then
  if [[ "${SDLC_TEST_FAILPOINT:-}" != "after-validator-swap" ]]; then
    exit 64
  fi
  case "$SDLC_TEST_RESTORE_FAILURE" in
    after-backup-move)
      printf 'restore failure falsifier\n' >>"$FIXTURE_BASELINE"
      ;;
    remove-backup)
      rm -f "$BACKUP_VALIDATOR"
      ;;
    *) exit 64 ;;
  esac
fi
if [[ "${SDLC_TEST_FAILPOINT:-}" == "after-validator-swap" ]]; then
  printf 'F01_FORCED_ASSERTION_AFTER_VALIDATOR_SWAP:%s\n' \
    "$FIXTURE_VALIDATOR" >&2
  case "${SDLC_TEST_FAILPOINT_STDERR_SUFFIX:-}" in
    "") ;;
    blank-line) printf '\n' >&2 ;;
    *) exit 64 ;;
  esac
  if [[ -n "${SDLC_TEST_SIGNAL:-}" ]]; then
    case "$SDLC_TEST_SIGNAL" in
      HUP|INT|TERM) ;;
      *) exit 64 ;;
    esac
    kill -s "$SDLC_TEST_SIGNAL" "$$"
    exit 125
  fi
  /usr/bin/false
  exit 125
fi
test_dispatch \
  '{"tool_name":"Write","tool_input":{"file_path":"'"$WORK_ROOT"'/test.py","content":"x = 1"}}' \
  0 "missing validator file stays non-blocking (exit 0)" \
  "HOOK_WARNING"
restore_validator

BROKEN_VALIDATOR="$REPLACEMENT_ROOT/safety-constraints.broken"
printf 'validate_safety_constraints() {\n  if [[\n}\n' >"$BROKEN_VALIDATOR"
BACKUP_VALIDATOR="$BACKUP_ROOT/safety-constraints.original"
mv "$FIXTURE_VALIDATOR" "$BACKUP_VALIDATOR"
mv "$BROKEN_VALIDATOR" "$FIXTURE_VALIDATOR"
test_dispatch \
  '{"tool_name":"Write","tool_input":{"file_path":"'"$WORK_ROOT"'/test.py","content":"x = 1"}}' \
  0 "broken validator source stays non-blocking (exit 0)" \
  "HOOK_WARNING"
restore_validator

EXIT1_VALIDATOR="$REPLACEMENT_ROOT/safety-constraints.exit1"
printf 'validate_safety_constraints() { echo "SC-ERR" >&2; return 1; }\n' >"$EXIT1_VALIDATOR"
BACKUP_VALIDATOR="$BACKUP_ROOT/safety-constraints.original"
mv "$FIXTURE_VALIDATOR" "$BACKUP_VALIDATOR"
mv "$EXIT1_VALIDATOR" "$FIXTURE_VALIDATOR"
test_dispatch \
  '{"tool_name":"Write","tool_input":{"file_path":"'"$WORK_ROOT"'/test.py","content":"x = 1"}}' \
  0 "validator exit 1 stays non-blocking (exit 0)"
restore_validator

printf 'Results: %s passed, %s failed\n' "$PASS" "$FAIL"
[[ "$PASS" -eq 11 && "$FAIL" -eq 0 ]]
