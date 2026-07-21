#!/bin/bash
set -euo pipefail

TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
PLUGIN_ROOT="$(cd "$TEST_DIR/.." && pwd -P)"
TMPROOT="$(mktemp -d "${TMPDIR:-/tmp}/sdlc-runtime-policy.XXXXXX")"
trap 'rm -rf "$TMPROOT"' EXIT HUP INT TERM

candidate_list="$TMPROOT/candidates"
missing_list="$TMPROOT/missing"

rg -l -i --glob '*.md' \
  'model:[[:space:]]*(haiku|sonnet|opus|<catalog-validated-model>|live-catalog selection)|\((haiku|sonnet|opus)\)|agent tool|haiku-|sonnet-|opus-' \
  "$PLUGIN_ROOT/skills" | sort >"$candidate_list"

: >"$missing_list"
while IFS= read -r path; do
  if ! rg -q 'RUNTIME_DISPATCH_POLICY_V1' "$path"; then
    printf '%s\n' "$path" >>"$missing_list"
  fi
done <"$candidate_list"

if [[ -s "$missing_list" ]]; then
  printf 'FAIL: static role/model dispatch guidance lacks the runtime policy marker:\n' >&2
  sed 's/^/  - /' "$missing_list" >&2
  exit 1
fi

count="$(wc -l <"$candidate_list" | tr -d ' ')"
[[ "$count" -gt 0 ]] || { echo 'FAIL: detector found no dispatch-bearing files' >&2; exit 1; }
printf 'PASS: runtime dispatch policy covers %s dispatch-bearing files\n' "$count"
