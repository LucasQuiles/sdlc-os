#!/bin/bash
# Cross-Model Adversarial Review — Preflight Check
# Verifies all prerequisites before launching a cross-model review session.
# Exit 0 + JSON = ready. Exit 2 + stderr = not ready with specific failure reason.

set -euo pipefail

TASK_ID="${1:-}"
PLUGIN_DIR="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"

# --- Helpers ---

fail() {
  local code="$1"
  local reason="$2"
  printf '{"ready":false,"code":"%s","reason":"%s"}\n' "$code" "$reason"
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
for candidate in \
  "${PLUGIN_DIR}/../tmup/index.js" \
  "${HOME}/.claude/plugins/tmup/index.js" \
  "${HOME}/.local/share/tmup/index.js"; do
  if [[ -f "$candidate" ]]; then
    TMUP_ENTRY="$candidate"
    break
  fi
done

if [[ -z "$TMUP_ENTRY" ]]; then
  fail "TMUP_MISSING" "tmup MCP entry point not found — expected tmup plugin alongside sdlc-os"
fi

TMUP_PLUGIN_DIR="$(cd "$(dirname "$TMUP_ENTRY")" && pwd)"
TMUP_SYNC_SCRIPT="${TMUP_PLUGIN_DIR}/scripts/sync-codex-agents.sh"

if [[ ! -f "$TMUP_SYNC_SCRIPT" ]]; then
  fail "TMUP_SYNC_MISSING" "tmup sync-codex-agents.sh not found — cross-model review requires tmup tiered agent sync support"
fi

# --- Check 4: Artifact path writable ---

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

# --- Check 5: No conflicting active cross-model session ---

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

# --- Check 6: registry.json project-dir conflict ---

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

printf '{"ready":true,"tmux_version":"%s","codex_version":"%s","tmup_entry":"%s","tmup_sync":"%s","artifact_base":"%s"}\n' \
  "$TMUX_VERSION" \
  "$CODEX_VERSION" \
  "$TMUP_ENTRY" \
  "$TMUP_SYNC_SCRIPT" \
  "${ARTIFACT_BASE:-n/a}"
