#!/bin/bash
# eslint-disable Justification Enforcer
# Runs as PostToolUse hook on Write|Edit targeting source files.
# Blocks bare eslint-disable comments (score 0) in new code.
# Pre-existing bare suppressions pass if fingerprinted in the task's allowlist.
# Exit 0 = clean, Exit 2 = bare suppression detected (BLOCKING)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

INPUT=$(cat)
FILE_PATH=$(read_hook_file_path "$INPUT")

# Only check source files
if [[ -z "$FILE_PATH" ]]; then
  exit 0
fi

case "$FILE_PATH" in
  *.ts|*.tsx|*.js|*.jsx) ;;
  *) exit 0 ;;
esac

# Skip vendor/generated paths
if is_vendor_path "$FILE_PATH"; then
  exit 0
fi

CONTENT=$(read_tool_content "$INPUT" "$FILE_PATH")

if [[ -z "$CONTENT" ]]; then
  exit 0
fi

# Find all eslint-disable lines
DISABLE_LINES=$(echo "$CONTENT" | grep -n "eslint-disable" 2>/dev/null || true)

if [[ -z "$DISABLE_LINES" ]]; then
  exit 0
fi

# Load allowlist if it exists (for pre-existing bare suppressions)
# Deterministic task-scoped resolution: use SDLC_TASK_ID env var if set,
# otherwise find the single active task directory. Multi-task ambiguity
# is resolved by requiring exactly one match — if multiple active tasks
# exist, skip allowlist (conservative: blocks bare suppressions).
ALLOWLIST_FILE=""
REPO_ROOT=$(get_repo_root)
if [[ -n "$REPO_ROOT" ]]; then
  ACTIVE_DIR="$REPO_ROOT/docs/sdlc/active"
  if [[ -n "${SDLC_TASK_ID:-}" ]]; then
    # Explicit task ID — deterministic
    ALLOWLIST_FILE="$ACTIVE_DIR/$SDLC_TASK_ID/suppression-allowlist.md"
    [[ -f "$ALLOWLIST_FILE" ]] || ALLOWLIST_FILE=""
  else
    # Infer: exactly one active task directory with an allowlist
    CANDIDATES=$(find "$ACTIVE_DIR" -name "suppression-allowlist.md" -type f 2>/dev/null || true)
    CANDIDATE_COUNT=$(echo "$CANDIDATES" | grep -c . 2>/dev/null || echo 0)
    if [[ "$CANDIDATE_COUNT" -eq 1 ]]; then
      ALLOWLIST_FILE="$CANDIDATES"
    fi
    # 0 or 2+ candidates: skip allowlist (conservative — blocks bare suppressions)
  fi
fi

ERRORS=""

while IFS= read -r line; do
  # Extract line number and content
  LINE_NUM=$(echo "$line" | cut -d: -f1)
  LINE_CONTENT=$(echo "$line" | cut -d: -f2-)

  # Skip eslint-enable lines
  if echo "$LINE_CONTENT" | grep -q "eslint-enable"; then
    continue
  fi

  # Check for structured justification: must have -- separator with substantive text
  # Valid: // eslint-disable-next-line no-foo -- reason text here; tracked in DEBT-001
  # Valid: // eslint-disable-next-line no-foo -- reason text here; expires 2026-06-01
  # Invalid: // eslint-disable-next-line no-foo
  # Invalid: // eslint-disable-next-line no-foo -- ok
  # Invalid: // eslint-disable-next-line no-foo -- needed

  if echo "$LINE_CONTENT" | grep -qE "eslint-disable.*--\s*.{10,};\s*(tracked in |expires )"; then
    # Score 2-3: Has structured format with tracking/expiry
    continue
  fi

  if echo "$LINE_CONTENT" | grep -qE "eslint-disable.*--\s*.{10,}"; then
    # Score 1: Has -- separator and reason but missing tracking/expiry
    # Weak but not bare — allow (Scout census will flag)
    continue
  fi

  # This is a bare suppression (score 0). Check allowlist.
  if [[ -n "$ALLOWLIST_FILE" ]] && [[ -f "$ALLOWLIST_FILE" ]]; then
    # Compute fingerprint: sha256(file_path + normalized_disable_text + context)
    NORMALIZED=$(echo "$LINE_CONTENT" | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//')

    # Get surrounding 3 lines for context hash
    CONTEXT_START=$((LINE_NUM > 1 ? LINE_NUM - 1 : 1))
    CONTEXT_END=$((LINE_NUM + 1))
    CONTEXT_LINES=$(echo "$CONTENT" | sed -n "${CONTEXT_START},${CONTEXT_END}p" 2>/dev/null || true)
    CONTEXT_HASH=$(echo "$CONTEXT_LINES" | shasum -a 256 | cut -d' ' -f1)

    FINGERPRINT=$(echo "${FILE_PATH}${NORMALIZED}${CONTEXT_HASH}" | shasum -a 256 | cut -d' ' -f1)

    if grep -q "$FINGERPRINT" "$ALLOWLIST_FILE" 2>/dev/null; then
      # Pre-existing bare suppression — allowlisted
      continue
    fi
  fi

  # Bare suppression not in allowlist — BLOCK
  ERRORS="${ERRORS}Line ${LINE_NUM}: Bare eslint-disable without justification. Required format:\n"
  ERRORS="${ERRORS}  // eslint-disable-next-line <rule> -- <reason (10+ chars)>; tracked in <DEBT-ID>\n"
  ERRORS="${ERRORS}  // eslint-disable-next-line <rule> -- <reason (10+ chars)>; expires <YYYY-MM-DD>\n\n"

done <<< "$DISABLE_LINES"

if [[ -n "$ERRORS" ]]; then
  echo "HOOK_ERROR: eslint-disable justification required" >&2
  echo -e "$ERRORS" >&2
  exit 2
fi

exit 0
