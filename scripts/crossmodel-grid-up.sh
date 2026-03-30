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

# --- Suppress GUI terminal auto-launch ---

export TMUP_NO_TERMINAL=1

# --- Sync tmup tiered custom agents into ~/.codex/agents ---

TMUP_SYNC_SCRIPT=""
for candidate in \
  "$(cd "$(dirname "$0")/../.." && pwd)/tmup/scripts/sync-codex-agents.sh" \
  "${HOME}/.claude/plugins/tmup/scripts/sync-codex-agents.sh" \
  "${HOME}/.local/share/tmup/scripts/sync-codex-agents.sh"; do
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

# --- Success ---

printf '{"ready":true,"session_name":"%s","panes":%d,"rows":%d,"cols":%d,"layout":"tiled"}\n' \
  "$SESSION_NAME" \
  "$ACTUAL_PANES" \
  "$ROWS" \
  "$COLS"
