#!/bin/bash
set -euo pipefail

umask 077

TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
PLUGIN_ROOT="$(cd "$TEST_DIR/.." && pwd -P)"
PREFLIGHT="$PLUGIN_ROOT/scripts/crossmodel-preflight.sh"
PYTHON_BIN="$(command -v python3.12)"
CHILD_PATH="$(dirname "$PYTHON_BIN"):/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"
TMPROOT=""
PASS=0
FAIL=0

cleanup() {
  local rc=$?
  trap - EXIT HUP INT TERM
  if [[ -n "$TMPROOT" ]]; then
    rm -rf "$TMPROOT"
  fi
  exit "$rc"
}

record_pass() {
  PASS=$((PASS + 1))
  printf 'PASS: %s\n' "$1"
}

record_fail() {
  FAIL=$((FAIL + 1))
  printf 'FAIL: %s\n' "$1" >&2
}

make_tool_fixtures() {
  local bin_dir="$1"
  mkdir -p "$bin_dir"
  cat >"$bin_dir/tmux" <<'EOF'
#!/bin/bash
if [[ "${1:-}" == "-V" ]]; then
  printf 'tmux 3.4\n'
  exit 0
fi
if [[ "${1:-}" == "has-session" ]]; then
  exit 1
fi
exit 64
EOF
  cat >"$bin_dir/codex" <<'EOF'
#!/bin/bash
if [[ "${1:-}" == "--version" ]]; then
  printf 'codex 1.0.0\n'
  exit 0
fi
exit 64
EOF
  chmod +x "$bin_dir/tmux" "$bin_dir/codex"
}

make_tmup_fixture() {
  local tmup_root="$1"
  local declared_entry="$2"
  local created_entry="${3:-}"
  mkdir -p "$tmup_root/.claude-plugin" "$tmup_root/scripts"
  printf '{"mcpServers":{"tmup":{"command":"node","args":["%s"]}}}\n' \
    "$declared_entry" >"$tmup_root/.claude-plugin/plugin.json"
  printf '#!/bin/bash\nexit 0\n' >"$tmup_root/scripts/sync-codex-agents.sh"
  chmod +x "$tmup_root/scripts/sync-codex-agents.sh"
  if [[ -n "$created_entry" ]]; then
    mkdir -p "$(dirname "$created_entry")"
    printf 'export {};\n' >"$created_entry"
  fi
}

run_preflight() {
  local case_root="$1"
  local use_override="${2:-yes}"
  local sdlc_root="$case_root/plugins/sdlc-os"
  local tmup_root="$case_root/plugins/tmup"
  local home_root="$case_root/home"
  local work_root="$case_root/work"
  local output_root="$case_root/output"
  mkdir -p "$sdlc_root" "$home_root" "$work_root" "$output_root"

  set +e
  if [[ "$use_override" == "yes" ]]; then
    (
      cd "$work_root" || exit 125
      env -i \
        LC_ALL=C \
        PATH="$case_root/bin:$CHILD_PATH" \
        HOME="$home_root" \
        CLAUDE_PLUGIN_ROOT="$sdlc_root" \
        TMUP_PLUGIN_ROOT="$tmup_root" \
        /bin/bash "$PREFLIGHT"
    ) >"$output_root/stdout" 2>"$output_root/stderr"
  else
    (
      cd "$work_root" || exit 125
      env -i \
        LC_ALL=C \
        PATH="$case_root/bin:$CHILD_PATH" \
        HOME="$home_root" \
        CLAUDE_PLUGIN_ROOT="$sdlc_root" \
        /bin/bash "$PREFLIGHT"
    ) >"$output_root/stdout" 2>"$output_root/stderr"
  fi
  PREFLIGHT_RC=$?
  set -e
}

assert_ready() {
  local label="$1"
  local case_root="$2"
  local expected_entry="$3"
  local use_override="${4:-yes}"
  local expected_sync="$case_root/plugins/tmup/scripts/sync-codex-agents.sh"
  run_preflight "$case_root" "$use_override"
  if [[ "$PREFLIGHT_RC" -ne 0 ]]; then
    record_fail "$label (exit $PREFLIGHT_RC; $(tr '\n' ' ' <"$case_root/output/stderr"))"
    return
  fi
  if "$PYTHON_BIN" - "$case_root/output/stdout" "$expected_entry" "$expected_sync" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as stream:
    payload = json.load(stream)

assert payload["ready"] is True
assert payload["tmup_entry"] == sys.argv[2]
assert payload["tmup_sync"] == sys.argv[3]
PY
  then
    record_pass "$label"
  else
    record_fail "$label (ready payload mismatch)"
  fi
}

assert_missing() {
  local label="$1"
  local case_root="$2"
  run_preflight "$case_root"
  if [[ "$PREFLIGHT_RC" -ne 2 ]]; then
    record_fail "$label (expected exit 2, got $PREFLIGHT_RC)"
    return
  fi
  if "$PYTHON_BIN" - "$case_root/output/stdout" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as stream:
    payload = json.load(stream)

assert payload == {
    "ready": False,
    "code": "TMUP_MISSING",
    "reason": "tmup MCP entry point not found — expected tmup plugin alongside sdlc-os",
}
PY
  then
    record_pass "$label"
  else
    record_fail "$label (TMUP_MISSING payload mismatch)"
  fi
}

TMPROOT="$(mktemp -d "${TMPDIR:-/tmp}/sdlc-crossmodel-preflight.XXXXXX")"
TMPROOT="$(cd "$TMPROOT" && pwd -P)"
trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

CURRENT_ROOT="$TMPROOT/current"
make_tool_fixtures "$CURRENT_ROOT/bin"
make_tmup_fixture \
  "$CURRENT_ROOT/plugins/tmup" \
  "\${CLAUDE_PLUGIN_ROOT}/mcp-server/dist/index.js" \
  "$CURRENT_ROOT/plugins/tmup/mcp-server/dist/index.js"
assert_ready \
  "manifest-declared nested entry" \
  "$CURRENT_ROOT" \
  "$CURRENT_ROOT/plugins/tmup/mcp-server/dist/index.js" \
  no

FUTURE_ROOT="$TMPROOT/future"
make_tool_fixtures "$FUTURE_ROOT/bin"
make_tmup_fixture \
  "$FUTURE_ROOT/plugins/tmup" \
  "\${CLAUDE_PLUGIN_ROOT}/server/main.js" \
  "$FUTURE_ROOT/plugins/tmup/server/main.js"
assert_ready \
  "future manifest entry" \
  "$FUTURE_ROOT" \
  "$FUTURE_ROOT/plugins/tmup/server/main.js"

MISSING_ROOT="$TMPROOT/missing"
make_tool_fixtures "$MISSING_ROOT/bin"
make_tmup_fixture \
  "$MISSING_ROOT/plugins/tmup" \
  "\${CLAUDE_PLUGIN_ROOT}/mcp-server/dist/index.js"
assert_missing "missing declared entry" "$MISSING_ROOT"

ESCAPE_ROOT="$TMPROOT/escape"
make_tool_fixtures "$ESCAPE_ROOT/bin"
make_tmup_fixture \
  "$ESCAPE_ROOT/plugins/tmup" \
  "\${CLAUDE_PLUGIN_ROOT}/../outside.js" \
  "$ESCAPE_ROOT/plugins/outside.js"
assert_missing "escaping declared entry" "$ESCAPE_ROOT"

printf '\nResults: %d passed, %d failed\n' "$PASS" "$FAIL"
if [[ "$FAIL" -ne 0 ]]; then
  exit 1
fi
printf 'CROSSMODEL_PREFLIGHT_TESTS_PASS\n'
