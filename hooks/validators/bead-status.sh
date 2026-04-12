#!/bin/bash
# validate_bead_status — sourceable validator function
# Args: $1 = file_path, $2 = content
# Returns 0 for pass, 2 for block.
# Requires common.sh to be already sourced (for canonicalize_path).

validate_bead_status() {
  local FILE_PATH="$1"
  local CONTENT="$2"

  if [[ -z "$CONTENT" ]]; then
    return 0
  fi

  if ! command -v jq &>/dev/null; then
    echo '{"error": "jq is required but not found"}' >&2
    return 2
  fi

  # Extract current status
  local CURRENT_STATUS
  CURRENT_STATUS=$(echo "$CONTENT" | sed -n 's/^\*\*Status:\*\*[[:space:]]*\([a-z_]*\).*/\1/p' | head -1 || true)

  if [[ -z "$CURRENT_STATUS" ]]; then
    return 0
  fi

  # Normalize FILE_PATH to repo-relative for git show
  local REPO_ROOT=""
  local REL_PATH=""
  if command -v git &> /dev/null && git rev-parse --git-dir &> /dev/null 2>&1; then
    REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || true)
  fi

  if [[ -n "$REPO_ROOT" ]]; then
    local CANON_ROOT CANON_FILE
    CANON_ROOT=$(canonicalize_path "$REPO_ROOT")
    CANON_FILE=""
    if [[ "$FILE_PATH" == /* ]]; then
      CANON_FILE=$(canonicalize_path "$FILE_PATH")
    fi

    if [[ -n "$CANON_FILE" ]]; then
      REL_PATH="${CANON_FILE#"$CANON_ROOT"/}"
      if [[ "$REL_PATH" == "$CANON_FILE" ]]; then
        REL_PATH="${FILE_PATH#"$REPO_ROOT"/}"
      fi
    elif [[ "$FILE_PATH" == /* ]]; then
      REL_PATH="${FILE_PATH#"$REPO_ROOT"/}"
    else
      REL_PATH="$FILE_PATH"
    fi
  fi

  # Check for the previous status in git
  local PREVIOUS_STATUS=""
  if [[ -n "$REL_PATH" ]]; then
    local PREVIOUS_CONTENT
    PREVIOUS_CONTENT=$(git show HEAD:"$REL_PATH" 2>/dev/null || true)
    if [[ -n "$PREVIOUS_CONTENT" ]]; then
      PREVIOUS_STATUS=$(echo "$PREVIOUS_CONTENT" | sed -n 's/^\*\*Status:\*\*[[:space:]]*\([a-z_]*\).*/\1/p' | head -1 || true)
    fi
  fi

  # If we can't determine previous status, allow the transition
  if [[ -z "$PREVIOUS_STATUS" ]]; then
    return 0
  fi

  # If status didn't change, allow
  if [[ "$PREVIOUS_STATUS" == "$CURRENT_STATUS" ]]; then
    return 0
  fi

  # Define valid transitions
  local VALID=false
  case "$PREVIOUS_STATUS" in
    pending)
      [[ "$CURRENT_STATUS" =~ ^(running|blocked)$ ]] && VALID=true
      ;;
    running)
      [[ "$CURRENT_STATUS" =~ ^(submitted|blocked|stuck)$ ]] && VALID=true
      ;;
    submitted)
      [[ "$CURRENT_STATUS" =~ ^(verified|blocked|stuck|escalated)$ ]] && VALID=true
      ;;
    verified)
      local BEAD_TYPE
      BEAD_TYPE=$(echo "$CONTENT" | sed -n 's/^\*\*Type:\*\*[[:space:]]*\([a-z]*\).*/\1/p' | head -1 || true)
      if [[ "$BEAD_TYPE" == "evolve" ]]; then
        [[ "$CURRENT_STATUS" =~ ^(proven|merged|blocked|stuck|escalated)$ ]] && VALID=true
      else
        [[ "$CURRENT_STATUS" =~ ^(proven|blocked|stuck|escalated)$ ]] && VALID=true
      fi
      ;;
    proven)
      [[ "$CURRENT_STATUS" =~ ^(hardened|merged|blocked|stuck|escalated)$ ]] && VALID=true
      ;;
    hardened)
      [[ "$CURRENT_STATUS" =~ ^(reliability-proven|merged|blocked|stuck|escalated)$ ]] && VALID=true
      ;;
    reliability-proven)
      [[ "$CURRENT_STATUS" =~ ^(merged|blocked|stuck|escalated)$ ]] && VALID=true
      ;;
    blocked|stuck|escalated)
      [[ "$CURRENT_STATUS" =~ ^(pending|running)$ ]] && VALID=true
      ;;
  esac

  if [[ "$VALID" == "false" ]]; then
    echo "Illegal bead status transition: ${PREVIOUS_STATUS} -> ${CURRENT_STATUS}" >&2
    echo "" >&2
    echo "Canonical flow: pending -> running -> submitted -> verified -> proven -> hardened -> reliability-proven -> merged" >&2
    echo "Trivial beads may skip AQS: proven -> merged" >&2
    echo "But verified -> merged and verified -> hardened are NEVER valid (must pass through proven first)" >&2
    echo "" >&2
    echo "Fix the status to follow the canonical flow." >&2
    return 2
  fi

  return 0
}
