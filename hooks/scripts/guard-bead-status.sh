#!/bin/bash
# Bead Status Transition Guard
# Runs as PostToolUse hook on Write|Edit targeting docs/sdlc/active/*/beads/*.md
# Validates that bead status transitions follow the canonical flow
# Exit 0 = valid, Exit 2 = invalid (feeds correction to Claude)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

if ! command -v jq &>/dev/null; then
  echo '{"error": "jq is required but not found"}' >&2
  exit 2
fi

INPUT=$(read_hook_stdin) || exit 0
FILE_PATH=$(read_hook_file_path "$INPUT")

# Only validate bead files (not AQS reports)
if [[ -z "$FILE_PATH" ]]; then
  exit 0
fi

if [[ ! "$FILE_PATH" =~ docs/sdlc/active/.*/beads/.*\.md$ ]] || [[ "$FILE_PATH" =~ -aqs\.md$ ]]; then
  exit 0
fi

# Get the content (from Write tool_input or read the file for Edit)
CONTENT=$(read_tool_content "$INPUT" "$FILE_PATH")

if [[ -z "$CONTENT" ]]; then
  exit 0
fi

# Extract current status — portable (no grep -P)
CURRENT_STATUS=$(echo "$CONTENT" | sed -n 's/^\*\*Status:\*\*[[:space:]]*\([a-z_]*\).*/\1/p' | head -1 || true)

if [[ -z "$CURRENT_STATUS" ]]; then
  exit 0
fi

# Canonical status flow:
# pending -> running -> submitted -> verified -> proven -> hardened -> reliability-proven -> merged
# Also valid: blocked, stuck, escalated (from any state)
#
# Trivial beads may skip: proven -> merged (skipping hardened and reliability-proven)
# Beads may skip reliability: hardened -> merged (when Phase 4.5 is not active)
# Evolve beads: verified -> merged (no code to prove/harden)
# But verified -> merged is NEVER valid for non-evolve beads (must go through proven)
# And verified -> hardened is NEVER valid (must go through proven)

# Normalize FILE_PATH to repo-relative for git show
REPO_ROOT=""
REL_PATH=""
if command -v git &> /dev/null && git rev-parse --git-dir &> /dev/null 2>&1; then
  REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || true)
fi

if [[ -n "$REPO_ROOT" ]]; then
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
    # Check if this is an evolve bead (verified -> merged is valid for evolve beads)
    BEAD_TYPE=$(echo "$CONTENT" | sed -n 's/^\*\*Type:\*\*[[:space:]]*\([a-z]*\).*/\1/p' | head -1 || true)
    if [[ "$BEAD_TYPE" == "evolve" ]]; then
      [[ "$CURRENT_STATUS" =~ ^(proven|merged|blocked|stuck|escalated)$ ]] && VALID=true
    else
      [[ "$CURRENT_STATUS" =~ ^(proven|blocked|stuck|escalated)$ ]] && VALID=true
    fi
    ;;
  proven)
    # proven -> hardened (normal) or proven -> merged (trivial bead skip)
    [[ "$CURRENT_STATUS" =~ ^(hardened|merged|blocked|stuck|escalated)$ ]] && VALID=true
    ;;
  hardened)
    # hardened -> reliability-proven (normal with Phase 4.5) or hardened -> merged (skip Phase 4.5)
    [[ "$CURRENT_STATUS" =~ ^(reliability-proven|merged|blocked|stuck|escalated)$ ]] && VALID=true
    ;;
  reliability-proven)
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
  echo "Canonical flow: pending -> running -> submitted -> verified -> proven -> hardened -> reliability-proven -> merged" >&2
  echo "Trivial beads may skip AQS: proven -> merged" >&2
  echo "But verified -> merged and verified -> hardened are NEVER valid (must pass through proven first)" >&2
  echo "" >&2
  echo "Fix the status to follow the canonical flow." >&2
  exit 2
fi

exit 0
