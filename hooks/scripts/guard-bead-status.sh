#!/bin/bash
# Bead Status Transition Guard
# Runs as PostToolUse hook on Write|Edit targeting docs/sdlc/active/*/beads/*.md
# Validates that bead status transitions follow the canonical flow
# Exit 0 = valid, Exit 2 = invalid (feeds correction to Claude)

set -euo pipefail

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# Only validate bead files (not AQS reports)
if [[ -z "$FILE_PATH" ]]; then
  exit 0
fi

if [[ ! "$FILE_PATH" =~ docs/sdlc/active/.*/beads/.*\.md$ ]] || [[ "$FILE_PATH" =~ -aqs\.md$ ]]; then
  exit 0
fi

# Get the content (from Write tool_input or read the file for Edit)
CONTENT=$(echo "$INPUT" | jq -r '.tool_input.content // empty')
if [[ -z "$CONTENT" ]] && [[ -f "$FILE_PATH" ]]; then
  CONTENT=$(cat "$FILE_PATH")
fi

if [[ -z "$CONTENT" ]]; then
  exit 0
fi

# Extract current status — portable (no grep -P)
CURRENT_STATUS=$(echo "$CONTENT" | sed -n 's/^\*\*Status:\*\*[[:space:]]*\([a-z_]*\).*/\1/p' | head -1 || true)

if [[ -z "$CURRENT_STATUS" ]]; then
  exit 0
fi

# Canonical status flow:
# pending -> running -> submitted -> verified -> proven -> hardened -> merged
# Also valid: blocked, stuck, escalated (from any state)
#
# Trivial beads may skip: proven -> merged (skipping hardened)
# But verified -> merged is NEVER valid (must go through proven)
# And verified -> hardened is NEVER valid (must go through proven)

# Normalize FILE_PATH to repo-relative for git show
# Both paths must be canonicalized to physical paths to handle symlinks
# (e.g., /var/folders/... vs /private/var/folders/... on macOS)
REPO_ROOT=""
REL_PATH=""
if command -v git &> /dev/null && git rev-parse --git-dir &> /dev/null 2>&1; then
  REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || true)
fi

if [[ -n "$REPO_ROOT" ]]; then
  # Canonicalize both paths to resolve symlinks before stripping
  CANON_ROOT=""
  CANON_FILE=""
  if command -v realpath &> /dev/null; then
    CANON_ROOT=$(realpath "$REPO_ROOT" 2>/dev/null || true)
    if [[ "$FILE_PATH" == /* ]]; then
      CANON_FILE=$(realpath "$FILE_PATH" 2>/dev/null || true)
    fi
  fi
  # Fall back to pwd -P based resolution if realpath unavailable or failed
  if [[ -z "$CANON_ROOT" ]]; then
    CANON_ROOT=$(cd "$REPO_ROOT" 2>/dev/null && pwd -P || echo "$REPO_ROOT")
  fi
  if [[ -z "$CANON_FILE" ]] && [[ "$FILE_PATH" == /* ]]; then
    # Resolve the directory part, keep the filename
    FILE_DIR=$(dirname "$FILE_PATH")
    FILE_BASE=$(basename "$FILE_PATH")
    CANON_FILE=$(cd "$FILE_DIR" 2>/dev/null && pwd -P || echo "$FILE_DIR")/"$FILE_BASE"
  fi

  if [[ -n "$CANON_FILE" ]]; then
    REL_PATH="${CANON_FILE#"$CANON_ROOT"/}"
    # If stripping failed (path doesn't start with root), fall back to original
    if [[ "$REL_PATH" == "$CANON_FILE" ]]; then
      REL_PATH="${FILE_PATH#"$REPO_ROOT"/}"
    fi
  elif [[ "$FILE_PATH" == /* ]]; then
    REL_PATH="${FILE_PATH#"$REPO_ROOT"/}"
  else
    REL_PATH="$FILE_PATH"
  fi
fi

# Check for the previous status in git to detect the transition
PREVIOUS_STATUS=""
if [[ -n "$REL_PATH" ]]; then
  PREVIOUS_CONTENT=$(git show HEAD:"$REL_PATH" 2>/dev/null || true)
  if [[ -n "$PREVIOUS_CONTENT" ]]; then
    PREVIOUS_STATUS=$(echo "$PREVIOUS_CONTENT" | sed -n 's/^\*\*Status:\*\*[[:space:]]*\([a-z_]*\).*/\1/p' | head -1 || true)
  fi
fi

# If we can't determine previous status, allow the transition
if [[ -z "$PREVIOUS_STATUS" ]]; then
  exit 0
fi

# If status didn't change, allow
if [[ "$PREVIOUS_STATUS" == "$CURRENT_STATUS" ]]; then
  exit 0
fi

# Define valid transitions
VALID=false
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
    [[ "$CURRENT_STATUS" =~ ^(proven|blocked|stuck|escalated)$ ]] && VALID=true
    ;;
  proven)
    # proven -> hardened (normal) or proven -> merged (trivial bead skip)
    [[ "$CURRENT_STATUS" =~ ^(hardened|merged|blocked|stuck|escalated)$ ]] && VALID=true
    ;;
  hardened)
    [[ "$CURRENT_STATUS" =~ ^(merged|blocked|stuck|escalated)$ ]] && VALID=true
    ;;
  blocked|stuck|escalated)
    # Recovery: can go back to pending or running
    [[ "$CURRENT_STATUS" =~ ^(pending|running)$ ]] && VALID=true
    ;;
esac

if [[ "$VALID" == "false" ]]; then
  echo "Illegal bead status transition: ${PREVIOUS_STATUS} -> ${CURRENT_STATUS}" >&2
  echo "" >&2
  echo "Canonical flow: pending -> running -> submitted -> verified -> proven -> hardened -> merged" >&2
  echo "Trivial beads may skip AQS: proven -> merged" >&2
  echo "But verified -> merged and verified -> hardened are NEVER valid (must pass through proven first)" >&2
  echo "" >&2
  echo "Fix the status to follow the canonical flow." >&2
  exit 2
fi

exit 0
