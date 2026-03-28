#!/bin/bash
# Cross-Model Adversarial Review — Grid Down
# Tears down a tmux cross-model review grid.
# Args: --session-name NAME [--force]
# --force: also deregisters from tmup registry, removes session state dir,
#          and clears current-session pointer. Required for clean retry path.
# Exit 0 = clean. Exit 1 = warning (residue remained).

set -euo pipefail

# --- Arg parsing ---

SESSION_NAME=""
FORCE=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --session-name)
      SESSION_NAME="${2:-}"
      shift 2
      ;;
    --force)
      FORCE=true
      shift
      ;;
    *)
      printf 'Unknown argument: %s\n' "$1" >&2
      exit 1
      ;;
  esac
done

if [[ -z "$SESSION_NAME" ]]; then
  printf 'Missing required argument: --session-name\n' >&2
  exit 1
fi

WARNINGS=0

# --- Step 1: Kill tmux session ---

if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
  if ! tmux kill-session -t "$SESSION_NAME" 2>/dev/null; then
    printf 'Warning: failed to kill tmux session: %s\n' "$SESSION_NAME" >&2
    WARNINGS=$(( WARNINGS + 1 ))
  fi
else
  printf 'Note: tmux session %s was not running\n' "$SESSION_NAME" >&2
fi

# --- Step 2: Force deregistration (--force only) ---

if [[ "$FORCE" == "true" ]]; then
  TMUP_STATE_DIR="${HOME}/.local/state/tmup"
  REGISTRY_FILE="${TMUP_STATE_DIR}/registry.json"
  CURRENT_SESSION_FILE="${TMUP_STATE_DIR}/current-session"

  # 2a. Remove entry from registry.json whose value matches SESSION_NAME
  if [[ -f "$REGISTRY_FILE" ]]; then
    if command -v jq &> /dev/null; then
      # Remove any key whose value equals SESSION_NAME
      UPDATED=$(jq --arg sname "$SESSION_NAME" \
        'to_entries | map(select(.value != $sname)) | from_entries' \
        "$REGISTRY_FILE" 2>/dev/null) || {
          printf 'Warning: jq failed to parse registry.json — skipping registry deregistration\n' >&2
          WARNINGS=$(( WARNINGS + 1 ))
          UPDATED=""
        }
      if [[ -n "$UPDATED" ]]; then
        printf '%s\n' "$UPDATED" > "$REGISTRY_FILE"
      fi
    else
      # Fallback: grep-based removal — remove lines containing the session name
      # Registry format is assumed to be one JSON object; we do line-level surgery
      TMP_REGISTRY="${REGISTRY_FILE}.tmp.$$"
      if grep -v "\"${SESSION_NAME}\"" "$REGISTRY_FILE" > "$TMP_REGISTRY" 2>/dev/null; then
        mv "$TMP_REGISTRY" "$REGISTRY_FILE"
      else
        rm -f "$TMP_REGISTRY"
        printf 'Warning: grep fallback found no entry for %s in registry.json\n' "$SESSION_NAME" >&2
      fi
    fi
  fi

  # 2b. Remove session state directory (xm-* dir matching session name)
  SESSION_STATE_DIR="${TMUP_STATE_DIR}/${SESSION_NAME}"
  if [[ -d "$SESSION_STATE_DIR" ]]; then
    if ! rm -rf "$SESSION_STATE_DIR" 2>/dev/null; then
      printf 'Warning: failed to remove session state directory: %s\n' "$SESSION_STATE_DIR" >&2
      WARNINGS=$(( WARNINGS + 1 ))
    fi
  fi

  # Also check for generic xm-prefixed state dirs matching the session
  for state_dir in "${TMUP_STATE_DIR}"/xm-*; do
    [[ -d "$state_dir" ]] || continue
    if [[ "$(basename "$state_dir")" == "$SESSION_NAME" ]]; then
      rm -rf "$state_dir" 2>/dev/null || {
        printf 'Warning: failed to remove xm state dir: %s\n' "$state_dir" >&2
        WARNINGS=$(( WARNINGS + 1 ))
      }
    fi
  done

  # 2c. Clear current-session pointer if it points to this session
  if [[ -f "$CURRENT_SESSION_FILE" ]]; then
    CURRENT_VAL=$(cat "$CURRENT_SESSION_FILE" 2>/dev/null || echo "")
    if [[ "$CURRENT_VAL" == "$SESSION_NAME" ]]; then
      if ! rm -f "$CURRENT_SESSION_FILE" 2>/dev/null; then
        printf 'Warning: failed to remove current-session pointer\n' >&2
        WARNINGS=$(( WARNINGS + 1 ))
      fi
    fi
  fi
fi

# --- Done ---

if [[ $WARNINGS -gt 0 ]]; then
  printf '{"clean":false,"session_name":"%s","force":%s,"warnings":%d}\n' \
    "$SESSION_NAME" "$( [[ "$FORCE" == "true" ]] && echo "true" || echo "false" )" "$WARNINGS"
  exit 1
fi

printf '{"clean":true,"session_name":"%s","force":%s}\n' \
  "$SESSION_NAME" "$( [[ "$FORCE" == "true" ]] && echo "true" || echo "false" )"
