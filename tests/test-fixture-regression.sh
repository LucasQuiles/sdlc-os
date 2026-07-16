#!/bin/bash
# Golden fixture regression test for sdlc-dispatch.sh.
# Replays each *.payload.json through the dispatcher and compares
# exit code + stderr against saved golden outputs.
set -euo pipefail

TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=tests/lib/plugin-root.sh
source "$TEST_DIR/lib/plugin-root.sh"
PLUGIN_ROOT="$(resolve_plugin_root "${BASH_SOURCE[0]}")"
DISPATCH="$PLUGIN_ROOT/hooks/sdlc-dispatch.sh"
FIXTURES="$TEST_DIR/fixtures/validator-baseline"

PASS=0
FAIL=0

for payload in "$FIXTURES"/*.payload.json; do
  base=$(basename "$payload" .payload.json)

  expected_exit=$(cat "$FIXTURES/${base}.exit")
  expected_stderr=$(cat "$FIXTURES/${base}.stderr")

  actual_exit=0
  actual_stderr=$(bash "$DISPATCH" < "$payload" 2>&1 >/dev/null) || actual_exit=$?

  if [[ "$actual_exit" -ne "$expected_exit" ]]; then
    echo "FAIL: $base — expected exit $expected_exit, got $actual_exit" >&2
    FAIL=$((FAIL + 1))
    continue
  fi

  # Compare stderr (normalize whitespace for robustness)
  norm_expected=$(echo "$expected_stderr" | sed 's/[[:space:]]*$//')
  norm_actual=$(echo "$actual_stderr" | sed 's/[[:space:]]*$//')

  if [[ "$norm_expected" != "$norm_actual" ]]; then
    echo "FAIL: $base -- stderr mismatch" >&2
    diff <(echo "$norm_expected") <(echo "$norm_actual") >&2 || true
    FAIL=$((FAIL + 1))
    continue
  fi

  PASS=$((PASS + 1))
done

echo "Fixture regression: $PASS passed, $FAIL failed ($(( PASS + FAIL )) total)"
[[ "$FAIL" -eq 0 ]]
