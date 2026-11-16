#!/bin/bash
# Cross-Model Adversarial Review — Grid Up
# Creates a tmux grid for cross-model worker panes.
# Args: --session-name NAME --panes N
# Exit 0 + JSON = grid ready. Exit 2 = failed.

set -euo pipefail

# --- Arg parsing ---

SESSION_NAME=""
PANE_COUNT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --session-name)
      SESSION_NAME="${2:-}"
      shift 2
      ;;
    --panes)
      PANE_COUNT="${2:-}"
      shift 2
      ;;
    *)
      printf 'Unknown argument: %s\n' "$1" >&2
      exit 2
      ;;
  esac
done

if [[ -z "$SESSION_NAME" ]]; then
  printf 'Missing required argument: --session-name\n' >&2
  exit 2
fi

# Validate session name (alphanumeric, hyphens, underscores only — prevent injection)
if [[ "$SESSION_NAME" =~ [^a-zA-Z0-9_-] ]]; then
  printf 'GRID_UP_FAIL: session name contains invalid characters: %s\n' "$SESSION_NAME" >&2
  exit 2
fi

if [[ -z "$PANE_COUNT" ]]; then
  printf 'Missing required argument: --panes\n' >&2
  exit 2
fi

if ! [[ "$PANE_COUNT" =~ ^[1-9][0-9]*$ ]]; then
  printf 'Invalid --panes value: %s (must be a positive integer)\n' "$PANE_COUNT" >&2
  exit 2
fi

# sdlc-os opens and proves the viewer; keep tmup's launcher disabled.

export TMUP_NO_TERMINAL=1

# --- Sync tmup tiered custom agents into ~/.codex/agents ---

TMUP_SYNC_SCRIPT=""
if [[ -n "${TMUP_PLUGIN_ROOT:-}" ]]; then
  TMUP_CANDIDATES=("$TMUP_PLUGIN_ROOT/scripts/sync-codex-agents.sh")
else
  TMUP_CANDIDATES=(
  "$(cd "$(dirname "$0")/../.." && pwd)/tmup/scripts/sync-codex-agents.sh" \
  "${HOME}/.claude/plugins/tmup/scripts/sync-codex-agents.sh" \
  "${HOME}/.local/share/tmup/scripts/sync-codex-agents.sh")
fi
for candidate in "${TMUP_CANDIDATES[@]}"; do
  if [[ -f "$candidate" ]]; then
    TMUP_SYNC_SCRIPT="$candidate"
    break
  fi
done

if [[ -z "$TMUP_SYNC_SCRIPT" ]]; then
  printf 'TMUP sync script not found — expected tmup/scripts/sync-codex-agents.sh alongside sdlc-os\n' >&2
  exit 2
fi

if ! bash "$TMUP_SYNC_SCRIPT" >/dev/null; then
  printf 'Failed to sync tmup custom Codex agents via %s\n' "$TMUP_SYNC_SCRIPT" >&2
  exit 2
fi

# --- Check for existing session ---

if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
  printf 'Session already exists: %s — kill it first with crossmodel-grid-down.sh\n' "$SESSION_NAME" >&2
  exit 2
fi

# --- Calculate grid geometry ---
# rows = ceil(sqrt(N)), cols = ceil(N / rows)

ROWS=$(awk -v n="$PANE_COUNT" 'BEGIN { r=int(sqrt(n)); if(r*r<n) r++; print r }')
COLS=$(awk -v n="$PANE_COUNT" -v r="$ROWS" 'BEGIN { c=int(n/r); if(c*r<n) c++; print c }')

# --- Create tmux session (detached, no terminal) ---

if ! tmux new-session -d -s "$SESSION_NAME" -x 220 -y 50 2>/dev/null; then
  printf 'Failed to create tmux session: %s\n' "$SESSION_NAME" >&2
  exit 2
fi

# --- Split panes to reach requested count ---
# Start with 1 pane, split until we have PANE_COUNT panes.

CURRENT_PANES=1
NEEDED=$(( PANE_COUNT - 1 ))

i=0
while [[ $i -lt $NEEDED ]]; do
  if ! tmux split-window -t "${SESSION_NAME}" 2>/dev/null; then
    printf 'Failed to split pane %d in session %s\n' "$((i+2))" "$SESSION_NAME" >&2
    tmux kill-session -t "$SESSION_NAME" 2>/dev/null || true
    exit 2
  fi
  CURRENT_PANES=$(( CURRENT_PANES + 1 ))
  i=$(( i + 1 ))
done

# --- Apply tiled layout ---

if ! tmux select-layout -t "$SESSION_NAME" tiled 2>/dev/null; then
  printf 'Warning: could not apply tiled layout to session %s\n' "$SESSION_NAME" >&2
  # Non-fatal — continue
fi

# --- Set minimal prompt in each pane ---

ACTUAL_PANES=$(tmux list-panes -t "$SESSION_NAME" 2>/dev/null | wc -l | tr -d ' ')

pane_idx=0
while [[ $pane_idx -lt $ACTUAL_PANES ]]; do
  tmux send-keys -t "${SESSION_NAME}.${pane_idx}" "export PS1='xm \$ '" Enter 2>/dev/null || true
  pane_idx=$(( pane_idx + 1 ))
done

# --- Verify pane readiness — wait for shell prompt in each pane ---

for ((i=0; i<ACTUAL_PANES; i++)); do
  retries=10
  while ((retries > 0)); do
    # Check if pane has rendered the prompt
    pane_content=$(tmux capture-pane -t "${SESSION_NAME}.${i}" -p 2>/dev/null | tail -1)
    if [[ "$pane_content" == *"xm "* ]]; then
      break
    fi
    sleep 0.5
    retries=$((retries - 1))
  done
  if ((retries == 0)); then
    printf 'Warning: pane %d may not be ready (prompt not detected)\n' "$i" >&2
  fi
done

# --- Verify actual pane count ---

if [[ "$ACTUAL_PANES" -ne "$PANE_COUNT" ]]; then
  printf 'Pane count mismatch: requested %d, got %d\n' "$PANE_COUNT" "$ACTUAL_PANES" >&2
  tmux kill-session -t "$SESSION_NAME" 2>/dev/null || true
  exit 2
fi

# --- Open a read-only viewer and prove that it attached ---

VIEWER_PANE_ID=""
VIEWER_MODE=""
CLIENT_TTYS=""
VIEWER_TIMEOUT="${XM_VIEWER_TIMEOUT_SECONDS:-15}"

bounded_capture() {
  local limit="$1" output pid watchdog rc
  shift
  output=$(mktemp "${TMPDIR:-/tmp}/crossmodel-viewer.XXXXXX") || return 1
  "$@" >"$output" 2>/dev/null &
  pid=$!
  (
    sleep "$limit" &
    timer=$!
    trap 'kill "$timer" 2>/dev/null || true; wait "$timer" 2>/dev/null || true; exit 0' TERM
    wait "$timer"
    kill -KILL "$pid" 2>/dev/null || true
  ) >/dev/null 2>&1 &
  watchdog=$!
  if wait "$pid"; then rc=0; else rc=$?; fi
  kill "$watchdog" 2>/dev/null || true
  wait "$watchdog" 2>/dev/null || true
  cat "$output"
  rm -f "$output"
  return "$rc"
}

visibility_failure() {
  if [[ -n "$VIEWER_PANE_ID" ]]; then
    tmux kill-pane -t "$VIEWER_PANE_ID" 2>/dev/null || true
  fi
  tmux kill-session -t "$SESSION_NAME" 2>/dev/null || true
  jq -cn --arg session "$SESSION_NAME" '{ready:false,code:"VISIBILITY_UNAVAILABLE",session_name:$session}'
  exit 2
}

show_grid() {
  if [[ -n "${TMUX:-}" && -n "${TMUX_PANE:-}" ]]; then
    local socket="${TMUX%%,*}" quoted_socket
    printf -v quoted_socket '%q' "$socket"
    VIEWER_PANE_ID=$(bounded_capture "$VIEWER_TIMEOUT" tmux split-window -h -d -P -F '#{pane_id}' -t "$TMUX_PANE" \
      "env -u TMUX tmux -S $quoted_socket attach-session -r -t '=$SESSION_NAME'") || return 1
    [[ -n "$VIEWER_PANE_ID" ]] || return 1
    VIEWER_MODE="split-pane"
  elif [[ "$(uname -s)" == Darwin && -z "${SSH_CONNECTION:-}" ]] && command -v osascript >/dev/null 2>&1; then
    bounded_capture "$VIEWER_TIMEOUT" osascript -e "tell application \"Terminal\" to do script \"tmux attach-session -r -t =$SESSION_NAME\"" >/dev/null || return 1
    VIEWER_MODE="new-window"
  elif [[ "$(uname -s)" == Linux && ( -n "${DISPLAY:-}" || -n "${WAYLAND_DISPLAY:-}" ) ]] && command -v gnome-terminal >/dev/null 2>&1; then
    bounded_capture "$VIEWER_TIMEOUT" gnome-terminal -- tmux attach-session -r -t "=$SESSION_NAME" >/dev/null || return 1
    VIEWER_MODE="new-window"
  else
    return 1
  fi
}

[[ "$VIEWER_TIMEOUT" =~ ^[1-9][0-9]*$ ]] || visibility_failure
show_grid || visibility_failure
deadline=$((SECONDS + VIEWER_TIMEOUT))
while ((SECONDS < deadline)); do
  CLIENT_TTYS=$(bounded_capture "$((deadline - SECONDS))" tmux list-clients -t "=$SESSION_NAME" -F '#{client_tty}') || CLIENT_TTYS=""
  [[ -n "$CLIENT_TTYS" ]] && break
  if ((SECONDS < deadline)); then sleep 1; fi
done
[[ -n "$CLIENT_TTYS" ]] || visibility_failure
CLIENTS_JSON=$(printf '%s\n' "$CLIENT_TTYS" | jq -Rsc 'split("\n") | map(select(length > 0))')
OBSERVED_AT=$(date -u '+%Y-%m-%dT%H:%M:%SZ')

jq -cn --arg session "$SESSION_NAME" --arg mode "$VIEWER_MODE" \
  --arg viewer "$VIEWER_PANE_ID" --arg observed "$OBSERVED_AT" --argjson clients "$CLIENTS_JSON" \
  --argjson panes "$ACTUAL_PANES" --argjson rows "$ROWS" --argjson cols "$COLS" \
  '{ready:true,session_name:$session,panes:$panes,rows:$rows,cols:$cols,layout:"tiled",
    visibility:{mode:$mode,session_name:$session,attached_clients:($clients|length),client_ttys:$clients,
      viewer_pane_id:$viewer,observed_at:$observed,observation_source:"tmux list-clients"}}'
