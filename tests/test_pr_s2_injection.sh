#!/bin/bash
# PR-S2 regression: quote-bearing paths must be data, not Python code.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

assert_not_created() {
  local path="$1"
  [ ! -e "$path" ] || fail "injection created sentinel: $path"
}

if [ -x /opt/homebrew/opt/python@3.12/libexec/bin/python3 ]; then
  export PATH="/opt/homebrew/opt/python@3.12/libexec/bin:$PATH"
fi

if ! command -v python3 >/dev/null; then
  echo "SKIP: python3 is required"
  exit 0
fi

if ! python3 - <<'PY'
import yaml
PY
then
  echo "SKIP: python3 with PyYAML is required"
  exit 0
fi

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

# SITE 1: scripts/append-system-hazard-defense.sh reads TASK_DIR/.../ledger.
# The prefix file lets the pre-fix injected open('/.../site1-prefix') succeed
# before running the injected os.system call.
site1_prefix="$tmpdir/site1-prefix"
cat > "$site1_prefix" <<'YAML'
task_id: decoy
YAML

site1_task_dir="$tmpdir/site1-prefix'))); import os; os.system('touch SITE1_PWNED'); #"
mkdir -p "$site1_task_dir"
cat > "$site1_task_dir/hazard-defense-ledger.yaml" <<'YAML'
task_id: site1-task
artifact_status: final
derived_at: "2026-06-15T00:00:00Z"
summary:
  qualifying_beads: 0
  records_total: 0
  records_with_defense: 0
  records_without_defense: 0
  escapes_known_at_close: 0
  residual_high_risk: 0
  coverage_state: complete
records: []
YAML

site1_project="$tmpdir/project"
site1_output="$(
  cd "$tmpdir"
  bash "$REPO_ROOT/scripts/append-system-hazard-defense.sh" \
    "$site1_task_dir" "$site1_project"
)" || fail "append-system-hazard-defense.sh failed: $site1_output"

assert_not_created "$tmpdir/SITE1_PWNED"
grep -q '"task_id":"site1-task"' \
  "$site1_project/docs/sdlc/system-hazard-defense.jsonl" || \
  fail "site 1 did not append the literal task_id"

# SITE 4: scripts/lib/stressor-lib.sh uses a multiline python3 -c program.
# The newline payload is legal in a Unix path and makes the pre-fix code execute
# os.system while the post-fix code reads the YAML file literally.
site4_prefix="$tmpdir/site4-prefix"
touch "$site4_prefix"
site4_rules_file="$tmpdir/site4-prefix') as f:
    r = {'fft15_sampling': {}}
import os; os.system('touch SITE4_PWNED')
if False:
    #"
cat > "$site4_rules_file" <<'YAML'
fft15_sampling:
  sampled_rate: 0.90
  anti_turkey_rate: 0.30
  hormetic_rate: 0.10
  clean_streak_threshold: 5
YAML

site4_result="$(
  cd "$tmpdir"
  source "$REPO_ROOT/scripts/lib/stressor-lib.sh"
  evaluate_fft15 "warning" 0 "false" "BUILD" "0.75" "$site4_rules_file"
)" || fail "evaluate_fft15 failed"

assert_not_created "$tmpdir/SITE4_PWNED"
[ "$site4_result" = "SAMPLED" ] || fail "site 4 returned $site4_result, expected SAMPLED"

echo "PASS: PR-S2 injection paths treated as data"
