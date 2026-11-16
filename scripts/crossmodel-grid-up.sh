#!/bin/bash
# Cross-Model Adversarial Review — Grid Up
# Creates a tmux grid for cross-model worker panes.
# Args: --session-name NAME --panes N
# Exit 0 + JSON = grid ready. Exit 2 = failed.

set -euo pipefail

command -v jq >/dev/null 2>&1 || { printf 'jq is required\n' >&2; exit 2; }
fail() { jq -cn --arg code "$1" '{ready:false,code:$code}'; exit 2; }

bounded_capture() (
  local limit="$1" output pid watchdog rc
  shift
  output=$(mktemp "${TMPDIR:-/tmp}/crossmodel-viewer.XXXXXX") || return 1
  trap 'rm -f "$output"' EXIT
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
  return "$rc"
)

# --- Arg parsing ---

SESSION_NAME=""
PANE_COUNT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --session-name)
      [[ $# -ge 2 ]] || fail INVALID_ARGUMENT
      SESSION_NAME="${2:-}"
      shift 2
      ;;
    --panes)
      [[ $# -ge 2 ]] || fail INVALID_ARGUMENT
      PANE_COUNT="${2:-}"
      shift 2
      ;;
    *)
      printf 'Unknown argument: %s\n' "$1" >&2
      fail INVALID_ARGUMENT
      ;;
  esac
done

if [[ -z "$SESSION_NAME" ]]; then
  printf 'Missing required argument: --session-name\n' >&2
  fail INVALID_ARGUMENT
fi

# Validate session name (alphanumeric, hyphens, underscores only — prevent injection)
if [[ "$SESSION_NAME" =~ [^a-zA-Z0-9_-] ]]; then
  printf 'GRID_UP_FAIL: session name contains invalid characters: %s\n' "$SESSION_NAME" >&2
  fail INVALID_ARGUMENT
fi

if [[ -z "$PANE_COUNT" ]]; then
  printf 'Missing required argument: --panes\n' >&2
  fail INVALID_ARGUMENT
fi

if ! [[ "$PANE_COUNT" =~ ^[1-9][0-9]*$ ]]; then
  printf 'Invalid --panes value: %s (must be a positive integer)\n' "$PANE_COUNT" >&2
  fail INVALID_ARGUMENT
fi

# sdlc-os opens and proves the viewer; keep tmup's launcher disabled.

VIEWER_TIMEOUT="${XM_VIEWER_TIMEOUT_SECONDS:-15}"
[[ "$VIEWER_TIMEOUT" =~ ^[1-9][0-9]*$ ]] || { jq -cn '{ready:false,code:"INVALID_TIMEOUT"}'; exit 2; }
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
  fail SYNC_UNAVAILABLE
fi

if ! bash "$TMUP_SYNC_SCRIPT" >/dev/null; then
  printf 'Failed to sync tmup custom Codex agents via %s\n' "$TMUP_SYNC_SCRIPT" >&2
  fail SYNC_FAILED
fi

# --- Check for existing session ---

if bounded_capture "$VIEWER_TIMEOUT" tmux has-session -t "=$SESSION_NAME" >/dev/null; then
  jq -cn --arg session "$SESSION_NAME" '{ready:false,code:"SESSION_EXISTS",session_name:$session}'
  exit 2
else
  has_rc=$?
  if [[ "$has_rc" != 1 ]]; then
    jq -cn --arg session "$SESSION_NAME" '{ready:false,code:"SESSION_CHECK_FAILED",session_name:$session}'
    exit 2
  fi
fi

# --- Calculate grid geometry ---
# rows = ceil(sqrt(N)), cols = ceil(N / rows)

ROWS=$(awk -v n="$PANE_COUNT" 'BEGIN { r=int(sqrt(n)); if(r*r<n) r++; print r }')
COLS=$(awk -v n="$PANE_COUNT" -v r="$ROWS" 'BEGIN { c=int(n/r); if(c*r<n) c++; print c }')

# --- Create tmux session (detached, no terminal) ---

SESSION_CREATED=false
OWNER_TOKEN="${RANDOM}${RANDOM}$$-$(date +%s)"
VIEWER_PANE_ID=""
FAILURE_CODE="GRID_UP_FAIL"
cleanup_grid() {
  if [[ "$SESSION_CREATED" == true ]]; then
    local owner skipped=false
    owner=$(bounded_capture "$VIEWER_TIMEOUT" tmux show-options -v -t "=$SESSION_NAME:" @xm_owner) || owner=""
    if [[ "$owner" == "$OWNER_TOKEN" ]]; then
      [[ -z "$VIEWER_PANE_ID" ]] || tmux kill-pane -t "$VIEWER_PANE_ID" 2>/dev/null || true
      tmux kill-session -t "=$SESSION_NAME" 2>/dev/null || true
    else
      skipped=true
    fi
    jq -cn --arg session "$SESSION_NAME" --arg code "$FAILURE_CODE" --argjson skipped "$skipped" \
      '{ready:false,code:$code,session_name:$session,cleanup_skipped_unowned:$skipped}'
  else
    jq -cn --arg session "$SESSION_NAME" --arg code "$FAILURE_CODE" '{ready:false,code:$code,session_name:$session}'
  fi
}
trap cleanup_grid EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
SESSION_CREATED=true
if bounded_capture "$VIEWER_TIMEOUT" tmux new-session -d -s "$SESSION_NAME" -x 220 -y 50 >/dev/null; then
  :
else
  create_rc=$?
  [[ "$create_rc" == 137 ]] || SESSION_CREATED=false
  printf 'Failed to create tmux session: %s\n' "$SESSION_NAME" >&2
  exit 2
fi
if ! bounded_capture "$VIEWER_TIMEOUT" tmux set-option -t "=$SESSION_NAME:" @xm_owner "$OWNER_TOKEN" >/dev/null; then
  printf 'Failed to mark tmux session ownership: %s\n' "$SESSION_NAME" >&2
  exit 2
fi

# --- Split panes to reach requested count ---
# Start with 1 pane, split until we have PANE_COUNT panes.

CURRENT_PANES=1
NEEDED=$(( PANE_COUNT - 1 ))

i=0
while [[ $i -lt $NEEDED ]]; do
  if ! bounded_capture "$VIEWER_TIMEOUT" tmux split-window -t "=$SESSION_NAME:" >/dev/null; then
    printf 'Failed to split pane %d in session %s\n' "$((i+2))" "$SESSION_NAME" >&2
    exit 2
  fi
  CURRENT_PANES=$(( CURRENT_PANES + 1 ))
  i=$(( i + 1 ))
done

# --- Apply tiled layout ---

if ! bounded_capture "$VIEWER_TIMEOUT" tmux select-layout -t "=$SESSION_NAME:" tiled >/dev/null; then
  printf 'Warning: could not apply tiled layout to session %s\n' "$SESSION_NAME" >&2
  # Non-fatal — continue
fi

# --- Set minimal prompt in each pane ---

PANE_LIST=$(bounded_capture "$VIEWER_TIMEOUT" tmux list-panes -t "=$SESSION_NAME:") || exit 2
ACTUAL_PANES=$(printf '%s\n' "$PANE_LIST" | wc -l | tr -d ' ')

pane_idx=0
while [[ $pane_idx -lt $ACTUAL_PANES ]]; do
  bounded_capture "$VIEWER_TIMEOUT" tmux send-keys -t "=$SESSION_NAME:.${pane_idx}" "export PS1='xm \$ '" Enter >/dev/null || true
  pane_idx=$(( pane_idx + 1 ))
done

# --- Verify pane readiness — wait for shell prompt in each pane ---

for ((i=0; i<ACTUAL_PANES; i++)); do
  retries=10
  while ((retries > 0)); do
    # Check if pane has rendered the prompt
    pane_content=$(bounded_capture "$VIEWER_TIMEOUT" tmux capture-pane -t "=$SESSION_NAME:.${i}" -p | tail -1)
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
  exit 2
fi

# --- Open a read-only viewer and prove that it attached ---

VIEWER_MODE=""
CLIENT_TTYS=""

visibility_failure() {
  FAILURE_CODE="VISIBILITY_UNAVAILABLE"
  exit 2
}

show_grid() {
  local caller_state=""
  if [[ -n "${TMUX:-}" && -n "${TMUX_PANE:-}" ]]; then
    caller_state=$(bounded_capture "$VIEWER_TIMEOUT" tmux display-message -p -t "$TMUX_PANE" '#{session_attached} #{window_active}') || caller_state=""
  fi
  if [[ "$caller_state" =~ ^[1-9][0-9]*\ 1$ ]]; then
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

BEFORE_CLIENTS=$(bounded_capture "$VIEWER_TIMEOUT" tmux list-clients -t "=$SESSION_NAME" -F '#{client_tty} #{client_readonly}') || visibility_failure
show_grid || visibility_failure
deadline=$((SECONDS + VIEWER_TIMEOUT))
while ((SECONDS < deadline)); do
  CLIENTS=$(bounded_capture "$((deadline - SECONDS))" tmux list-clients -t "=$SESSION_NAME" -F '#{client_tty} #{client_readonly}') || CLIENTS=""
  CLIENT_TTYS=$(jq -nr --arg before "$BEFORE_CLIENTS" --arg after "$CLIENTS" '($before | split("\n") | map(split(" ")[0])) as $old | $after | split("\n")[] | split(" ") | select(length == 2 and .[0] != "" and .[1] == "1" and (.[0] as $tty | $old | index($tty) | not)) | .[0]')
  [[ -n "$CLIENT_TTYS" ]] && break
  if ((SECONDS < deadline)); then sleep 1; fi
done
[[ -n "$CLIENT_TTYS" ]] || visibility_failure
CLIENTS_JSON=$(printf '%s\n' "$CLIENT_TTYS" | jq -Rsc 'split("\n") | map(select(length > 0))')
OBSERVED_AT=$(date -u '+%Y-%m-%dT%H:%M:%SZ')

trap - EXIT INT TERM
jq -cn --arg session "$SESSION_NAME" --arg mode "$VIEWER_MODE" \
  --arg viewer "$VIEWER_PANE_ID" --arg observed "$OBSERVED_AT" --argjson clients "$CLIENTS_JSON" \
  --argjson panes "$ACTUAL_PANES" --argjson rows "$ROWS" --argjson cols "$COLS" \
  '{ready:true,session_name:$session,panes:$panes,rows:$rows,cols:$cols,layout:"tiled",
    visibility:{mode:$mode,session_name:$session,attached_clients:($clients|length),client_ttys:$clients,
      viewer_pane_id:$viewer,observed_at:$observed,observation_source:"tmux list-clients",read_only:true}}'
