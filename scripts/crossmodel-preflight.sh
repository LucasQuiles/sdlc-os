#!/bin/bash
# Cross-Model Adversarial Review — Preflight Check
# Verifies all prerequisites before launching a cross-model review session.
# Exit 0 + JSON = ready. Exit 2 + stderr = not ready with specific failure reason.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=scripts/lib/tmup-discovery.sh
source "$SCRIPT_DIR/lib/tmup-discovery.sh"

TASK_ID="${1:-}"
PLUGIN_DIR="${CLAUDE_PLUGIN_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd -P)}"

# --- Helpers ---

fail() {
  local code="$1"
  local reason="$2"
  if command -v jq >/dev/null 2>&1; then
    jq -cn --arg code "$code" --arg reason "$reason" \
      '{ready:false,code:$code,reason:$reason}'
  else
    printf '{"ready":false,"code":"%s","reason":"structured failure details unavailable because jq is missing; see stderr"}\n' "$code"
  fi
  printf 'Preflight failed [%s]: %s\n' "$code" "$reason" >&2
  exit 2
}

# --- Check 1: tmux available ---

if ! command -v tmux &> /dev/null; then
  fail "TMUX_MISSING" "tmux not found on PATH — install tmux to enable cross-model grid sessions"
fi

TMUX_VERSION=$(tmux -V 2>/dev/null | awk '{print $2}' || echo "unknown")

# --- Check 2: codex CLI available ---

if ! command -v codex &> /dev/null; then
  fail "CODEX_MISSING" "codex CLI not found on PATH — install codex to enable cross-model workers"
fi

CODEX_VERSION=$(codex --version 2>/dev/null | head -1 | tr -d '\n' || echo "unknown")

# --- Check 3: tmup MCP reachable ---

TMUP_ENTRY=""
TMUP_PLUGIN_DIR=""
if [[ -n "${TMUP_PLUGIN_ROOT:-}" ]]; then
  TMUP_CANDIDATE_ROOTS=("$TMUP_PLUGIN_ROOT")
else
  TMUP_CANDIDATE_ROOTS=(
    "${PLUGIN_DIR}/../tmup"
    "${HOME}/.claude/plugins/tmup"
    "${HOME}/.local/share/tmup"
  )
fi

for candidate_root in "${TMUP_CANDIDATE_ROOTS[@]}"; do
  [[ -n "$candidate_root" && -d "$candidate_root" ]] || continue
  if TMUP_ENTRY="$(discover_tmup_entry "$candidate_root" 2>/dev/null)"; then
    TMUP_PLUGIN_DIR="$(cd "$candidate_root" && pwd -P)"
    break
  fi
done

if [[ -z "$TMUP_ENTRY" ]]; then
  fail "TMUP_MISSING" "tmup MCP entry point not found — expected tmup plugin alongside sdlc-os"
fi

TMUP_SYNC_SCRIPT="${TMUP_PLUGIN_DIR}/scripts/sync-codex-agents.sh"
TMUP_POLICY_FILE="${TMUP_PLUGIN_DIR}/config/policy.yaml"

if [[ ! -f "$TMUP_SYNC_SCRIPT" ]]; then
  fail "TMUP_SYNC_MISSING" "tmup sync-codex-agents.sh not found — cross-model review requires tmup tiered agent sync support"
fi

if [[ ! -f "$TMUP_POLICY_FILE" ]]; then
  fail "TMUP_POLICY_MISSING" "tmup config/policy.yaml not found"
fi

TMUP_REQUESTED_MODEL=$(awk '
  /^codex:[[:space:]]*$/ { in_codex=1; next }
  in_codex && /^[^[:space:]]/ { exit }
  in_codex && /^[[:space:]]+model:[[:space:]]*/ {
    value=$0
    sub(/^[[:space:]]+model:[[:space:]]*/, "", value)
    gsub(/^"|"$/, "", value)
    print value
    exit
  }
' "$TMUP_POLICY_FILE")

if [[ -z "$TMUP_REQUESTED_MODEL" ]]; then
  fail "TMUP_MODEL_POLICY_INVALID" "tmup codex.model is missing from config/policy.yaml"
fi

if [[ "$TMUP_REQUESTED_MODEL" != "auto" ]]; then
  fail "TMUP_EXPLICIT_MODEL_UNSUPPORTED" "cross-model MCP dispatch cannot use an explicit model without a live catalog validation receipt; use a receipt-capable direct lane or restore codex.model auto"
fi

# --- Check 4: live receipt-aware tmup schema and authoritative JSON parser ---

if ! command -v jq >/dev/null 2>&1; then
  fail "JQ_MISSING" "jq is required for fail-closed cross-model journal validation"
fi

PYTHON_BIN="$(command -v python3.12 || command -v python3 || true)"
if [[ -z "$PYTHON_BIN" ]]; then
  fail "PYTHON_MISSING" "python3 is required for the bounded tmup MCP schema probe"
fi

if ! TMUP_MCP_RESPONSE=$("$PYTHON_BIN" - "$TMUP_ENTRY" <<'PY'
import subprocess
import sys

request = "\n".join([
    '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"sdlc-crossmodel-preflight","version":"1"}}}',
    '{"jsonrpc":"2.0","method":"notifications/initialized","params":{}}',
    '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}',
    '',
])
try:
    result = subprocess.run(
        ["node", sys.argv[1]],
        input=request,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        timeout=10,
        check=False,
    )
except (OSError, subprocess.TimeoutExpired):
    raise SystemExit(2)
if result.returncode != 0 or not result.stdout.strip():
    raise SystemExit(2)
sys.stdout.write(result.stdout)
PY
); then
  fail "TMUP_MCP_UNAVAILABLE" "tmup MCP tools/list probe failed or timed out"
fi

if ! printf '%s\n' "$TMUP_MCP_RESPONSE" | jq -se '
  def requires($fields):
    (.inputSchema.required // []) as $required
    | ($fields - $required | length) == 0;
  [.[] | select(.id == 2) | .result.tools[]?] as $tools
  | ($tools | map(.name)) as $names
  | (["tmup_task_batch", "tmup_dispatch", "tmup_attempt_attest", "tmup_evidence_add", "tmup_evidence_review", "tmup_complete", "tmup_status"] - $names | length) == 0
  and any($tools[]; .name == "tmup_task_batch"
    and requires(["tasks"])
    and (.inputSchema.properties.tasks.type == "array")
    and ((.inputSchema.properties.tasks.items.required // []) | index("subject") != null)
    and (.inputSchema.properties.tasks.items.properties
      | .role_required.type == "boolean"
      and .evidence_required.type == "boolean"
      and (.model_requirement.enum | index("cross_model") != null)
      and .reference_model.type == "string"))
  and any($tools[]; .name == "tmup_dispatch"
    and requires(["task_id", "role"])
    and .inputSchema.properties.task_id.type == "string"
    and .inputSchema.properties.role.type == "string")
  and any($tools[]; .name == "tmup_attempt_attest"
    and requires(["attempt_id", "observed_model", "observation_source", "fallback_used"])
    and (.inputSchema.properties
      | .attempt_id.type == "string"
      and .observed_model.type == "string"
      and .observation_source.type == "string"
      and .fallback_used.type == "boolean"
      and .fallback_model.type == "string"
      and .fallback_reason.type == "string"))
  and any($tools[]; .name == "tmup_evidence_add"
    and requires(["attempt_id", "type", "payload"])
    and (.inputSchema.properties.type.enum | index("artifact_checksum") != null)
    and .inputSchema.properties.hash.type == "string")
  and any($tools[]; .name == "tmup_evidence_review"
    and requires(["evidence_id", "disposition"])
    and (.inputSchema.properties.disposition.enum | index("approved") != null))
  and any($tools[]; .name == "tmup_complete"
    and requires(["task_id", "result_summary"])
    and .inputSchema.properties.artifacts.type == "array"
    and ((.inputSchema.properties.artifacts.items.required // []) as $artifact_required
      | (["name", "path"] - $artifact_required | length) == 0))
  and any($tools[]; .name == "tmup_status"
    and .inputSchema.properties.verbose.type == "boolean")
' >/dev/null 2>&1; then
  fail "TMUP_RECEIPT_SCHEMA_MISSING" "live tmup tools/list lacks receipt-aware tmup MCP tools and completion policy fields"
fi

# --- Check 5: Artifact path writable ---

ARTIFACT_BASE=""
if [[ -n "$TASK_ID" ]]; then
  ARTIFACT_BASE="${PLUGIN_DIR}/../../docs/sdlc/active/${TASK_ID}/crossmodel"
  # Normalize
  ARTIFACT_BASE=$(cd "$(dirname "$ARTIFACT_BASE")" 2>/dev/null && pwd)/$(basename "$ARTIFACT_BASE") 2>/dev/null || true
fi

# Use a generic writable check when no task-id provided
CHECK_DIR="${ARTIFACT_BASE:-${PLUGIN_DIR}/../../docs/sdlc/active}"
PARENT_DIR=$(dirname "$CHECK_DIR")

if [[ ! -d "$PARENT_DIR" ]]; then
  # Try to create it
  if ! mkdir -p "$PARENT_DIR" 2>/dev/null; then
    fail "ARTIFACT_NOT_WRITABLE" "Cannot create artifact parent directory: ${PARENT_DIR}"
  fi
fi

if ! touch "${PARENT_DIR}/.preflight-write-test" 2>/dev/null; then
  fail "ARTIFACT_NOT_WRITABLE" "Artifact base path is not writable: ${PARENT_DIR}"
fi
rm -f "${PARENT_DIR}/.preflight-write-test"

# --- Check 6: No conflicting active cross-model session ---

TMUP_STATE_DIR="${HOME}/.local/state/tmup"
CONFLICTING_SESSION=""

if [[ -d "$TMUP_STATE_DIR" ]]; then
  # Look for xm-* directories that have a live tmux session
  for state_entry in "${TMUP_STATE_DIR}"/xm-*; do
    [[ -d "$state_entry" ]] || continue
    session_name=$(basename "$state_entry")
    # Sanitize: skip state entries whose names contain invalid characters
    if [[ "$session_name" =~ [^a-zA-Z0-9_-] ]]; then
      continue
    fi
    # Check if a tmux session with this name is actually running
    if tmux has-session -t "$session_name" 2>/dev/null; then
      CONFLICTING_SESSION="$session_name"
      break
    fi
  done
fi

if [[ -n "$CONFLICTING_SESSION" ]]; then
  fail "CONFLICTING_SESSION" "Active cross-model session detected: ${CONFLICTING_SESSION} — run crossmodel-grid-down.sh --session-name ${CONFLICTING_SESSION} --force first"
fi

# --- Check 7: registry.json project-dir conflict ---

REGISTRY_JSON="${TMUP_STATE_DIR}/registry.json"
CURRENT_PROJECT_DIR=$(pwd)

if [[ -f "$REGISTRY_JSON" ]]; then
  if command -v jq &> /dev/null; then
    # Check if any registry entry's project_dir value matches current directory
    REGISTRY_CONFLICT=$(jq -r --arg pdir "$CURRENT_PROJECT_DIR" 'to_entries[] | select(.value == $pdir) | .key' "$REGISTRY_JSON" 2>/dev/null | head -1 || echo "")
  else
    # grep fallback: look for the current project dir as a value in the JSON
    REGISTRY_CONFLICT=$(grep -oE '"[^"]*"[[:space:]]*:[[:space:]]*"'"$(printf '%s' "$CURRENT_PROJECT_DIR" | sed 's/[\/&]/\\&/g')"'"' "$REGISTRY_JSON" 2>/dev/null | grep -oE '^"[^"]*"' | tr -d '"' | head -1 || echo "")
  fi

  if [[ -n "$REGISTRY_CONFLICT" ]]; then
    fail "CONFLICTING_SESSION" "registry.json entry '${REGISTRY_CONFLICT}' targets current project directory ${CURRENT_PROJECT_DIR} — run crossmodel-grid-down.sh --session-name ${REGISTRY_CONFLICT} --force first"
  fi
fi

# --- All checks passed ---

jq -cn \
  --arg tmux_version "$TMUX_VERSION" \
  --arg codex_version "$CODEX_VERSION" \
  --arg tmup_entry "$TMUP_ENTRY" \
  --arg tmup_sync "$TMUP_SYNC_SCRIPT" \
  --arg requested_model "$TMUP_REQUESTED_MODEL" \
  --arg artifact_base "${ARTIFACT_BASE:-n/a}" \
  '{
    ready:true,
    tmux_version:$tmux_version,
    codex_version:$codex_version,
    tmup_entry:$tmup_entry,
    tmup_sync:$tmup_sync,
    requested_model:$requested_model,
    catalog_status:"not_applicable_auto",
    artifact_base:$artifact_base
  }'
