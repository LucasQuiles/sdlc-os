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
  local receipt_schema="${4:-present}"
  local requested_model="${5:-auto}"
  mkdir -p "$tmup_root/.claude-plugin" "$tmup_root/scripts" "$tmup_root/config"
  printf '{"mcpServers":{"tmup":{"command":"node","args":["%s"]}}}\n' \
    "$declared_entry" >"$tmup_root/.claude-plugin/plugin.json"
  printf '#!/bin/bash\nexit 0\n' >"$tmup_root/scripts/sync-codex-agents.sh"
  printf 'codex:\n  model: "%s"\n' "$requested_model" >"$tmup_root/config/policy.yaml"
  chmod +x "$tmup_root/scripts/sync-codex-agents.sh"
  if [[ -n "$created_entry" ]]; then
    mkdir -p "$(dirname "$created_entry")"
    case "$receipt_schema" in
      present)
        cat >"$created_entry" <<'JS'
process.stdin.resume();
process.stdin.on("end", () => {
  const taskPolicy = {
    subject: {type: "string"}, role_required: {type: "boolean"},
    evidence_required: {type: "boolean"},
    model_requirement: {type: "string", enum: ["none", "observed", "cross_model"]},
    reference_model: {type: "string"}
  };
  const tools = [
    {name: "tmup_task_batch", inputSchema: {type: "object", required: ["tasks"], properties: {tasks: {type: "array", items: {type: "object", required: ["subject"], properties: taskPolicy}}}}},
    {name: "tmup_dispatch", inputSchema: {type: "object", required: ["task_id", "role"], properties: {task_id: {type: "string"}, role: {type: "string"}}}},
    {name: "tmup_attempt_attest", inputSchema: {type: "object", required: ["attempt_id", "observed_model", "observation_source", "fallback_used"], properties: {attempt_id: {type: "string"}, observed_model: {type: "string"}, observation_source: {type: "string"}, fallback_used: {type: "boolean"}, fallback_model: {type: "string"}, fallback_reason: {type: "string"}}}},
    {name: "tmup_evidence_add", inputSchema: {type: "object", required: ["attempt_id", "type", "payload"], properties: {attempt_id: {type: "string"}, type: {type: "string", enum: ["diff", "artifact_checksum"]}, payload: {type: "string"}, hash: {type: "string"}}}},
    {name: "tmup_evidence_review", inputSchema: {type: "object", required: ["evidence_id", "disposition"], properties: {evidence_id: {type: "string"}, disposition: {type: "string", enum: ["approved", "challenged", "rejected"]}}}},
    {name: "tmup_complete", inputSchema: {type: "object", required: ["task_id", "result_summary"], properties: {task_id: {type: "string"}, result_summary: {type: "string"}, artifacts: {type: "array", items: {type: "object", required: ["name", "path"], properties: {name: {type: "string"}, path: {type: "string"}}}}}}},
    {name: "tmup_status", inputSchema: {type: "object", properties: {verbose: {type: "boolean"}}}}
  ];
  process.stdout.write(JSON.stringify({jsonrpc: "2.0", id: 1, result: {protocolVersion: "2024-11-05", capabilities: {}, serverInfo: {name: "fixture", version: "1"}}}) + "\n");
  process.stdout.write(JSON.stringify({jsonrpc: "2.0", id: 2, result: {tools}}) + "\n");
});
JS
        ;;
      weak)
        printf '%s\n' 'process.stdin.resume(); process.stdin.on("end", () => { const tools=[{name:"tmup_task_batch",inputSchema:{properties:{tasks:{items:{properties:{role_required:{},evidence_required:{},model_requirement:{},reference_model:{}}}}}}},{name:"tmup_dispatch",inputSchema:{properties:{task_id:{},role:{}}}},{name:"tmup_attempt_attest",inputSchema:{properties:{observed_model:{},fallback_used:{},fallback_model:{},fallback_reason:{}}}},{name:"tmup_evidence_add",inputSchema:{properties:{attempt_id:{},hash:{}}}},{name:"tmup_evidence_review",inputSchema:{properties:{disposition:{enum:["approved"]}}}},{name:"tmup_complete",inputSchema:{properties:{task_id:{},artifacts:{}}}},{name:"tmup_status",inputSchema:{properties:{verbose:{}}}}]; process.stdout.write(JSON.stringify({jsonrpc:"2.0",id:2,result:{tools}})+"\n"); });' >"$created_entry"
        ;;
      *)
        printf '%s\n' 'process.stdin.resume(); process.stdin.on("end", () => { process.stdout.write(JSON.stringify({jsonrpc:"2.0",id:2,result:{tools:[{name:"tmup_status"}]}})+"\n"); });' >"$created_entry"
        ;;
    esac
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
assert payload["requested_model"] == "auto"
assert payload["catalog_status"] == "not_applicable_auto"
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

assert_receipt_schema_missing() {
  local label="$1"
  local case_root="$2"
  run_preflight "$case_root"
  if [[ "$PREFLIGHT_RC" -ne 2 ]]; then
    record_fail "$label (expected exit 2, got $PREFLIGHT_RC)"
    return
  fi
  if jq -e '
    .ready == false
    and .code == "TMUP_RECEIPT_SCHEMA_MISSING"
    and (.reason | contains("receipt-aware tmup MCP tools"))
  ' "$case_root/output/stdout" >/dev/null; then
    record_pass "$label"
  else
    record_fail "$label (receipt-schema payload mismatch)"
  fi
}

assert_explicit_model_rejected() {
  local label="$1"
  local case_root="$2"
  run_preflight "$case_root"
  if [[ "$PREFLIGHT_RC" -ne 2 ]]; then
    record_fail "$label (expected exit 2, got $PREFLIGHT_RC)"
    return
  fi
  if jq -e '.ready == false and .code == "TMUP_EXPLICIT_MODEL_UNSUPPORTED"' "$case_root/output/stdout" >/dev/null; then
    record_pass "$label"
  else
    record_fail "$label (explicit-model payload mismatch)"
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

QUOTED_ROOT="$TMPROOT/quoted\"path"
make_tool_fixtures "$QUOTED_ROOT/bin"
make_tmup_fixture \
  "$QUOTED_ROOT/plugins/tmup" \
  "\${CLAUDE_PLUGIN_ROOT}/mcp-server/dist/index.js" \
  "$QUOTED_ROOT/plugins/tmup/mcp-server/dist/index.js"
assert_ready \
  "JSON output escapes filesystem paths" \
  "$QUOTED_ROOT" \
  "$QUOTED_ROOT/plugins/tmup/mcp-server/dist/index.js"

MISSING_ROOT="$TMPROOT/missing"
make_tool_fixtures "$MISSING_ROOT/bin"
make_tmup_fixture \
  "$MISSING_ROOT/plugins/tmup" \
  "\${CLAUDE_PLUGIN_ROOT}/mcp-server/dist/index.js"
assert_missing "missing declared entry" "$MISSING_ROOT"

SCHEMA_ROOT="$TMPROOT/schema-missing"
make_tool_fixtures "$SCHEMA_ROOT/bin"
make_tmup_fixture \
  "$SCHEMA_ROOT/plugins/tmup" \
  "\${CLAUDE_PLUGIN_ROOT}/mcp-server/dist/index.js" \
  "$SCHEMA_ROOT/plugins/tmup/mcp-server/dist/index.js" \
  missing
assert_receipt_schema_missing "missing receipt schema" "$SCHEMA_ROOT"

WEAK_SCHEMA_ROOT="$TMPROOT/weak-schema"
make_tool_fixtures "$WEAK_SCHEMA_ROOT/bin"
make_tmup_fixture \
  "$WEAK_SCHEMA_ROOT/plugins/tmup" \
  "\${CLAUDE_PLUGIN_ROOT}/mcp-server/dist/index.js" \
  "$WEAK_SCHEMA_ROOT/plugins/tmup/mcp-server/dist/index.js" \
  weak
assert_receipt_schema_missing "insufficient receipt schema" "$WEAK_SCHEMA_ROOT"

EXPLICIT_ROOT="$TMPROOT/explicit-model"
make_tool_fixtures "$EXPLICIT_ROOT/bin"
make_tmup_fixture \
  "$EXPLICIT_ROOT/plugins/tmup" \
  "\${CLAUDE_PLUGIN_ROOT}/mcp-server/dist/index.js" \
  "$EXPLICIT_ROOT/plugins/tmup/mcp-server/dist/index.js" \
  present \
  pinned-model
assert_explicit_model_rejected "MCP path rejects unreceipted explicit model" "$EXPLICIT_ROOT"

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
